from __future__ import annotations

import asyncio
import dataclasses
import multiprocessing
from abc import ABC
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import InitVar, dataclass
from enum import Enum, auto
from functools import partial
from multiprocessing.managers import DictProxy
from typing import ClassVar

import numpy as np
import pyaudio
import readchar
from traction_wave import asymmetric_signal


class TractionDirection(Enum):
    """牽引力方向"""

    up = auto()
    down = auto()

    def __str__(self):
        return self.name


@dataclass
class SignalParameter:
    """非対称周期信号のパラメータ"""

    frequency: float
    traction_direction: TractionDirection = TractionDirection.up

    def frequency_up(self):
        self.frequency += 1

    def frequency_down(self):
        self.frequency -= 1
        if self.frequency < 0:
            self.frequency = 0

    def traction_up(self):
        self.traction_direction = TractionDirection.up

    def traction_down(self):
        self.traction_direction = TractionDirection.down


@dataclass(frozen=True)
class SignalParameterImmutable:
    """非対称周期信号のパラメータ"""

    frequency: float
    traction_direction: TractionDirection = TractionDirection.up

    def _replace(self, **changes) -> SignalParameterImmutable:
        return dataclasses.replace(self, **changes)

    def frequency_up(self) -> SignalParameterImmutable:
        return self._replace(frequency=self.frequency + 1)

    def frequency_down(self) -> SignalParameterImmutable:
        f = self.frequency - 1
        if f < 0:
            f = 0
        return self._replace(frequency=f)

    def traction_up(self) -> SignalParameterImmutable:
        return self._replace(traction_direction=TractionDirection.up)

    def traction_down(self) -> SignalParameterImmutable:
        return self._replace(traction_direction=TractionDirection.down)


@dataclass
class PlayerParameter:
    """音声プレーヤーのパラメータ"""

    volume: float = 0.5  # 0~1
    fs: ClassVar[int] = 44_100

    def volume_up(self):
        self.volume += 0.1
        if self.volume > 1:
            self.volume = 1

    def volume_down(self):
        self.volume -= 0.1
        if self.volume < 0:
            self.volume = 0


@dataclass(frozen=True)
class PlayerParameterImmutable:
    """音声プレーヤーのパラメータ"""

    volume: float = 0.5  # 0~1
    fs: ClassVar[int] = 44_100

    def _replace(self, **changes) -> PlayerParameterImmutable:
        return dataclasses.replace(self, **changes)

    def volume_up(self) -> PlayerParameterImmutable:
        volume = self.volume + 0.1
        if volume > 1:
            volume = 1
        return self._replace(volume=volume)

    def volume_down(self) -> PlayerParameterImmutable:
        volume = self.volume - 0.1
        if volume < 0:
            volume = 0
        return self._replace(volume=volume)


class Player:
    """音声プレーヤーの制御"""

    def __init__(self, param: PlayerParameter):
        self._py_audio = pyaudio.PyAudio()
        self._stream = self._py_audio.open(format=pyaudio.paFloat32, channels=1, rate=param.fs, output=True)
        self.param = param

    def start(self):
        self._stream.start_stream()

    def stop(self):
        self._stream.stop_stream()

    def change_play_state(self):
        if self._stream.is_active():
            self.stop()
        else:
            self.start()

    def close(self):
        self._stream.close()
        self._py_audio.terminate()

    def write(self, sig: np.ndarray):
        self._stream.write((sig * self.param.volume).tobytes())

    def volume_up(self):
        self.param.volume_up()

    def volume_down(self):
        self.param.volume_down()


def keyboard_listener(
    callback: Callable[[AppCommand], None],
    h: AppStateHelper,
    sig_param: SignalParameterHelper,
    player_param: PlayerParameterHelper,
):
    """キーボードの入力を読み取り対応するAppCommandでCallableを呼ぶ
    :param callback: AppCommandを処理するコールバック関数
    :param h:
    :param sig_param:
    """

    while h.running:
        key = readchar.readkey()  # ブロッキング
        if key == "q":
            h.running = False
            callback(AppCommand.app_stop)
            return

        elif key == "z":
            callback(AppCommand.change_play_state)

        elif key == "d":
            callback(AppCommand.volume_up)
        elif key == "f":
            callback(AppCommand.volume_down)

        elif key == "x":
            callback(AppCommand.traction_up)
        elif key == "c":
            callback(AppCommand.traction_down)

        elif key == "a":
            callback(AppCommand.frequency_up)
        elif key == "s":
            callback(AppCommand.frequency_down)


class AppCommand(Enum):
    """アプリ操作コマンド"""

    app_stop = auto()

    volume_up = auto()
    volume_down = auto()

    traction_up = auto()
    traction_down = auto()

    frequency_up = auto()
    frequency_down = auto()

    change_play_state = auto()


def play(h: AppStateHelper, sig_param: SignalParameterHelper, player_param: PlayerParameterHelper):
    duration_sec = 1

    player = Player(player_param)
    player.start()

    def create_asymmetric_signal() -> np.ndarray:
        fs = player_param.fs
        frequency = sig_param.frequency
        traction_direction = sig_param.traction_direction

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
class AppStateHelper(AppState):
    """マルチプロセス時に生で値を触るのがいやなので"""

    _raw: DictProxy

    _running: InitVar[bool]

    def __post_init__(self, _running: bool):
        self._raw["is_running"] = _running

    @property
    def running(self) -> bool:
        return self._raw["is_running"]

    @running.setter
    def running(self, value: bool):
        self._raw["is_running"] = value


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
            SignalParameterHelper(d, 200, TractionDirection.up),
            PlayerParameterHelper(d, 0.5, 44_100, 1),
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
