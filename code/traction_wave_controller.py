from __future__ import annotations

import asyncio
import dataclasses
import multiprocessing
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from enum import auto, Enum
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

    def __init__(self, param: PlayerParameter):
        self._py_audio = pyaudio.PyAudio()
        self._stream = self._py_audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=param.fs,
            output=True
        )
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


def create_asymmetric_signal(
        frequency: float,
        fs: int,
        traction_direction: TractionDirection,
        duration_sec=1
) -> np.ndarray:
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
    sig = asymmetric_signal(2 * np.pi * frequency * t).astype(np.float32)
    if traction_direction == TractionDirection.down:
        sig = -sig
    return sig


def listen_keyboard_input(callback: Callable[[AppCommand], None],
                          # is_running: Synchronized,
                          d: DictProxy,
                          h: AppStateHelper
                          ):
    """ キーボードの入力を読み取り対応する AppCommand で Callable を呼ぶ
    :param callback: AppCommandを処理するコールバック関数
    :param is_running:
    """

    while h.running:
        key = readchar.readkey()  # ブロッキング
        if key == "q":
            app_state._running = False
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


def play(
        # player_param, sig_param,
        # is_running: Callable[[bool]],
        d: DictProxy,
        h: AppStateHelper

):
    player = Player(player_param)
    player.start()
    # while loop.is_running():
    # while True:
    while h.running:
        sig = create_asymmetric_signal(
            sig_param.frequency,
            player_param.fs,
            sig_param.traction_direction,
            1
        )
        player.write(sig)


# アプリ内グローバル
sig_param = SignalParameter(frequency=200)
player_param = PlayerParameter()


@dataclass
class AppState:
    _running: bool

    @property
    def running(self):
        return self._running


app_state = AppState(True)


def execute_command(app_key: AppCommand):
    """AppCommandに対応するアプリ動作をする"""

    if app_key == AppCommand.app_stop:
        app_state._running = False

        pass

        # player.close()

    elif app_key == AppCommand.change_play_state:
        pass
        # player.change_play_state()

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

    print_info()


def print_info():
    """CLI画面に表示される情報"""
    print(
        f"\rvolume {player_param.volume:.2f} "
        f"f: {sig_param.frequency} "
        f"traction: {sig_param.traction_direction}",
        end=""
    )


@dataclass
class AppStateHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""
    _raw: DictProxy

    @property
    def running(self) -> bool:
        return self._raw["is_running"]

    @running.setter
    def running(self, value: bool):
        self._raw["is_running"] = value

    # def set_runningss(self, value: bool):
    #     self._raw["is_running"] = value


@dataclass
class SignalParameterHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""
    _raw: DictProxy


@dataclass
class PlayerParameterHelper:
    """マルチプロセス時に生で値を触るのがいやなので"""
    _raw: DictProxy

    # volume: float = 0.5  # 0~1
    # fs: ClassVar[int] = 44_100

    @property
    def volume(self) -> float:
        return self._raw["volume"]

    @volume.setter
    def volume(self, value: float):
        self._raw["volume"] = value

    def volume_up(self):
        v = self.volume
        v += 0.1
        if v > 1:
            v = 1
        self.volume = v

    def volume_down(self):
        v = self.volume
        v -= 0.1
        if v < 0:
            v = 0
        self.volume = v


def main():
    # 起動
    # f1 = loop.run_in_executor(None, listen_keyboard_input, execute_command, )
    # f2 = loop.run_in_executor(None, play, player_param, sig_param, )

    print_info()

    # 共有変数を使うためのManager
    with multiprocessing.Manager() as manager:
        # is_running = manager.Value(ctypes.c_bool, True)
        d = manager.dict()
        app_state = AppStateHelper(d)
        app_state.running = True

        with ProcessPoolExecutor() as pool:
            f1 = loop.run_in_executor(pool, listen_keyboard_input, execute_command, d,
                                      AppStateHelper(d))
            f2 = loop.run_in_executor(pool, play, d, AppStateHelper(d))

    # f1 = loop.run_in_executor(pool, listen_keyboard_input, execute_command,
    #                           is_active_listen_keyboards()
    #                           )
    # f2 = loop.run_in_executor(pool, play, player_param, sig_param)
    f = asyncio.gather(f1, f2)
    # loop.create_task(f1)

    loop.run_until_complete(f)
    # loop.run_forever()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    main()
