from __future__ import annotations

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial

from traction_controller.gui import show_gui
from traction_controller.keyboard import AppCommand, keyboard_listener
from traction_controller.player import PlayerState, SignalParam, TractionDirection, play
from traction_controller.state import AppState
from traction_controller.switch import switch_listener


@dataclass
class AppStateMultiProcessing:
    """MultiProcessingで使用できる AppState の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: dict

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

    @is_running.setter
    def is_running(self, value: bool):
        self._raw["is_running"] = value


@dataclass
class PlayerStateMultiProcessing:
    """MultiProcessingで使用できる PlayerState の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: dict

    @property
    def fs(self) -> int:
        return self._raw["fs"]

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

    @property
    def volume(self) -> float:
        return self._raw["volume"]

    def volume_up(self):
        v = self.volume
        v += 0.1
        if v > 1:
            v = 1
        self._raw["volume"] = v

    def volume_down(self):
        v = self.volume
        v -= 0.1
        if v < 0:
            v = 0
        self._raw["volume"] = v

    def change_play_state(self):
        self._raw["is_running"] = not self._raw["is_running"]

    @staticmethod
    def setup_dict(d: dict, fs: int = 44_100, volume: float = 0.5, is_running: bool = True) -> dict:
        d["fs"] = fs
        d["volume"] = volume
        d["is_running"] = is_running
        return d


@dataclass
class SignalParamMultiProcessing:
    """MultiProcessingで使用できる SignalParam の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: dict

    @property
    def frequency(self) -> int:
        return self._raw["frequency"]

    def frequency_up(self):
        f = self._raw["frequency"]
        assert f <= 1000
        if f == 1000:
            return
        self._raw["frequency"] = f + 1

    def frequency_down(self):
        f = self._raw["frequency"]
        assert f >= 20
        if f == 20:
            return
        self._raw["frequency"] = f - 1

    @property
    def traction_direction(self) -> TractionDirection:
        return self._raw["traction_direction"]

    def traction_change(self):
        if self.traction_direction == TractionDirection.up:
            self._raw["traction_direction"] = TractionDirection.down
        else:
            self._raw["traction_direction"] = TractionDirection.up

    def traction_up(self):
        self._raw["traction_direction"] = TractionDirection.up

    def traction_down(self):
        self._raw["traction_direction"] = TractionDirection.down

    @property
    def count_anti_node(self) -> int:
        return self._raw["count_anti_node"]

    def count_anti_node_up(self):
        n = self._raw["count_anti_node"]
        assert n <= 1000
        if n == 1000:
            return
        self._raw["count_anti_node"] = n + 1

    def count_anti_node_down(self):
        n = self._raw["count_anti_node"]
        assert n >= 3
        if n == 3:
            return
        self._raw["count_anti_node"] = n - 1

    @staticmethod
    def setup_dict(
        d: dict,
        frequency: int = 63,
        direction: TractionDirection = TractionDirection.up,
        count_anti_node: int = 4,
    ) -> dict:
        d["frequency"] = frequency
        d["traction_direction"] = direction
        d["count_anti_node"] = count_anti_node
        return d


def print_info(player_param: PlayerState, sig_param: SignalParam):
    """CLI画面に表示される情報"""
    print(
        f"\rvolume {player_param.volume:.1f} "
        f"f: {sig_param.frequency:>4} "
        f"traction: {sig_param.traction_direction:>4} "
        f"count_anti_node: {sig_param.count_anti_node:>3} "
        f"play: {'playing' if player_param.is_running else 'stop':>7}",
        end="",
    )


def execute_command(
    app_key: AppCommand,
    app_state: AppState,
    player_param: PlayerState,
    sig_param: SignalParam,
):
    """AppCommandに対応するアプリ動作をする"""

    if app_key == AppCommand.app_stop:
        app_state.is_running = False

    elif app_key == AppCommand.pause:
        player_param.change_play_state()

    elif app_key == AppCommand.volume_up:
        player_param.volume_up()
    elif app_key == AppCommand.volume_down:
        player_param.volume_down()

    elif app_key == AppCommand.traction_up:
        sig_param.traction_up()
    elif app_key == AppCommand.traction_down:
        sig_param.traction_down()

    elif app_key == AppCommand.frequency_up:
        sig_param.frequency_up()
    elif app_key == AppCommand.frequency_down:
        sig_param.frequency_down()

    elif app_key == AppCommand.anti_node_up:
        sig_param.count_anti_node_up()
    elif app_key == AppCommand.anti_node_down:
        sig_param.count_anti_node_down()

    print_info(player_param, sig_param)


def main():
    loop = asyncio.new_event_loop()

    # キーボードからのコマンド読み取りと音の再生を別プロセスで実行する。
    # マルチプロセス: ProcessPoolExecutor
    # プロセス間通信: multiprocessing#Manager
    with multiprocessing.Manager() as manager, ProcessPoolExecutor() as pool:
        app_state_dict = manager.dict()
        player_state_dict = PlayerStateMultiProcessing.setup_dict(manager.dict())
        signal_param_dict = SignalParamMultiProcessing.setup_dict(manager.dict())

        AppStateMultiProcessing(app_state_dict).is_running = True

        print_info(
            PlayerStateMultiProcessing(player_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        partial_execute_command = partial(
            execute_command,
            app_state=AppStateMultiProcessing(app_state_dict),
            player_param=PlayerStateMultiProcessing(player_state_dict),
            sig_param=SignalParamMultiProcessing(signal_param_dict),
        )

        f1 = loop.run_in_executor(
            pool,
            keyboard_listener,
            partial_execute_command,
            AppStateMultiProcessing(app_state_dict),
        )
        f2 = loop.run_in_executor(
            pool,
            play,
            AppStateMultiProcessing(app_state_dict),
            PlayerStateMultiProcessing(player_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        f3 = loop.run_in_executor(
            pool,
            switch_listener,
            AppStateMultiProcessing(app_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        f4 = loop.run_in_executor(
            pool,
            show_gui,
            AppStateMultiProcessing(app_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        f = asyncio.gather(f1, f2, f3, f4, return_exceptions=True)
        loop.run_until_complete(f)
