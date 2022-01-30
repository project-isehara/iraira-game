from __future__ import annotations

import asyncio
import multiprocessing
from abc import ABC
from concurrent.futures import ProcessPoolExecutor
from dataclasses import InitVar, dataclass
from functools import partial
from multiprocessing.managers import DictProxy

import numpy as np
from keyboard import AppCommand, keyboard_listener
from state import AppStateHelper
from traction_contraller import Player, TractionDirection
from traction_wave import asymmetric_signal


def play(h: AppStateHelper, sig_param: SignalParameterHelper, player_param: PlayerParameterHelper):

    player = Player(player_param)
    player.start()

    def create_asymmetric_signal() -> np.ndarray:
        fs = player_param.fs
        frequency = sig_param.frequency
        traction_direction = sig_param.traction_direction

        duration_sec = 0.2
        duration_sec = round(duration_sec * frequency) / frequency

        t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
        sig = asymmetric_signal(2 * np.pi * frequency * t).astype(np.float32)
        if traction_direction == TractionDirection.down:
            sig = -sig
        return sig

    while h.running:
        if player_param.state == 0:
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

    elif app_key == AppCommand.change_play_state:
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
        f"\rvolume {player_param.volume:.2f} " f"f: {sig_param.frequency} " f"traction: {sig_param.traction_direction}",
        end="",
    )


class AppState(ABC):
    running: bool


@dataclass
class SignalParameterHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""

    _raw: DictProxy

    frequency: InitVar[float]
    traction_direction: InitVar[TractionDirection]

    def __post_init__(self, frequency: float, traction_direction: TractionDirection):
        self._raw["frequency"] = frequency
        self._raw["traction_direction"] = traction_direction

    @property
    def frequency(self) -> float:
        return self._raw["frequency"]

    def frequency_up(self):
        self._raw["frequency"] += 1

    def frequency_down(self):
        f = self._raw["frequency"]
        f -= 1
        if f < 0:
            f = 0
        self._raw["frequency"] = f

    @property
    def traction_direction(self) -> TractionDirection:
        return self._raw["traction_direction"]

    def traction_up(self):
        self._raw["traction_direction"] = TractionDirection.up

    def traction_down(self):
        self._raw["traction_direction"] = TractionDirection.down


@dataclass
class PlayerParameterHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""

    _raw: DictProxy

    volume: InitVar[float]  # = 0.5  # 0~1
    fs: InitVar[int]  # = 44_100
    state: InitVar[int]  # 0: stop 1:running

    def __post_init__(self, volume: float, fs: int, state: int):
        self._raw["volume"] = volume
        self._raw["fs"] = fs
        self._raw["state"] = state

    @property
    def fs(self) -> int:
        return self._raw["fs"]

    @property
    def state(self) -> int:
        return self._raw["state"]

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
        self._raw["state"] = not self._raw["state"]


def main():
    # 共有変数を使うためのManager
    with multiprocessing.Manager() as manager, ProcessPoolExecutor() as pool:
        d = manager.dict()

        app_state = AppStateHelper(d, True)

        sig_param = SignalParameterHelper(d, 200, TractionDirection.up)
        player_param = PlayerParameterHelper(d, 0.5, 44_100, 1)
        print_info(sig_param, player_param)

        partial_execute_command = partial(
            execute_command,
            app_state=AppStateHelper(d, True),
            sig_param=SignalParameterHelper(d, 200, TractionDirection.up),
            player_param=PlayerParameterHelper(d, 0.5, 44_100, 1),
        )

        f1 = loop.run_in_executor(
            pool,
            keyboard_listener,
            partial_execute_command,
            AppStateHelper(d, True),
        )
        f2 = loop.run_in_executor(
            pool,
            play,
            AppStateHelper(d, True),
            SignalParameterHelper(d, 200, TractionDirection.up),
            PlayerParameterHelper(d, 0.5, 44_100, 1),
        )

        f = asyncio.gather(f1, f2)
        loop.run_until_complete(f)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    main()
