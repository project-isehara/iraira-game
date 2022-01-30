from __future__ import annotations

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial

import numpy as np
from keyboard import AppCommand, keyboard_listener
from state import AppState, PlayerState, SignalParam
from traction_contraller import Player, TractionDirection
from traction_wave import traction_wave


def play(app_state: AppState, sig_param: SignalParam, player_param: PlayerState):
    player = Player(player_param)
    player.start()

    def create_asymmetric_signal() -> np.ndarray:
        fs = player_param.fs
        frequency = sig_param.frequency
        traction_direction = sig_param.traction_direction

        duration_sec = 0.2
        duration_sec = round(duration_sec * frequency) / frequency

        t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
        sig = traction_wave(2 * np.pi * frequency * t).astype(np.float32)
        if traction_direction == TractionDirection.down:
            sig = -sig
        return sig

    while app_state.is_running:
        if not player_param.is_running:
            player.stop()
            continue
        else:
            player.start()

        sig = create_asymmetric_signal()
        player.write(sig)


def execute_command(
    app_key: AppCommand, app_state: AppState, sig_param: SignalParameterHelper, player_param: PlayerParameterHelper
):
    """AppCommandに対応するアプリ動作をする"""

    if app_key == AppCommand.app_stop:
        app_state.running = False

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

    print_info(sig_param, player_param)


def print_info(sig_param: SignalParameterHelper, player_param: PlayerParameterHelper):
    """CLI画面に表示される情報"""
    print(
        f"\rvolume {player_param.volume:.1f} "
        f"f: {sig_param.frequency:>4} "
        f"traction: {sig_param.traction_direction:>4}",
        end="",
    )


@dataclass
class AppStateHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""

    _raw: dict

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

    @is_running.setter
    def is_running(self, value: bool):
        self._raw["is_running"] = value


@dataclass
class SignalParameterHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""

    _raw: dict

    @property
    def frequency(self) -> int:
        return self._raw["frequency"]

    def frequency_up(self):
        self._raw["frequency"] += 1

    def frequency_down(self):
        f = self._raw["frequency"]
        assert f >= 20
        if f == 20:
            return
        self._raw["frequency"] = f - 1

    @property
    def traction_direction(self) -> TractionDirection:
        return self._raw["traction_direction"]

    def traction_up(self):
        self._raw["traction_direction"] = TractionDirection.up

    def traction_down(self):
        self._raw["traction_direction"] = TractionDirection.down

    @staticmethod
    def setup_dict(d: dict, frequency: int = 63, direction: TractionDirection = TractionDirection.up) -> dict:
        d["frequency"] = frequency
        d["traction_direction"] = direction
        return d


@dataclass
class PlayerParameterHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""

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


def main():
    loop = asyncio.get_event_loop()

    # 共有変数を使うためのManager
    with multiprocessing.Manager() as manager, ProcessPoolExecutor() as pool:
        app_state_dict = manager.dict()
        player_state_dict = PlayerParameterHelper.setup_dict(manager.dict())
        signal_param_dict = SignalParameterHelper.setup_dict(manager.dict())

        AppStateHelper(app_state_dict).is_running = True

        print_info(
            sig_param=SignalParameterHelper(signal_param_dict),
            player_param=PlayerParameterHelper(player_state_dict),
        )

        partial_execute_command = partial(
            execute_command,
            app_state=AppStateHelper(app_state_dict),
            sig_param=SignalParameterHelper(signal_param_dict),
            player_param=PlayerParameterHelper(player_state_dict),
        )

        f1 = loop.run_in_executor(
            pool,
            keyboard_listener,
            partial_execute_command,
            AppStateHelper(app_state_dict),
        )
        f2 = loop.run_in_executor(
            pool,
            play,
            AppStateHelper(app_state_dict),
            SignalParameterHelper(signal_param_dict),
            PlayerParameterHelper(player_state_dict),
        )

        f = asyncio.gather(f1, f2, loop=loop, return_exceptions=True)
        loop.run_until_complete(f)


if __name__ == "__main__":
    main()
