from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import auto, Enum
from typing import ClassVar

import numpy as np
import pyaudio
import readchar
from pyaudio import Stream

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
class SignalParameter2:
    """非対称周期信号のパラメータ"""

    frequency: float
    traction_direction: TractionDirection = TractionDirection.up

    def _replace(self, **changes) -> SignalParameter2:
        return dataclasses.replace(self, **changes)

    def frequency_up(self) -> SignalParameter2:
        return self._replace(frequency=self.frequency + 1)

    def frequency_down(self) -> SignalParameter2:
        f = self.frequency - 1
        if f < 0:
            f = 0
        return self._replace(frequency=f)

    def traction_up(self) -> SignalParameter2:
        return self._replace(traction_direction=TractionDirection.up)

    def traction_down(self) -> SignalParameter2:
        return self._replace(traction_direction=TractionDirection.down)


@dataclass(frozen=True)
class PlayerParameter:
    """音声プレーヤーのパラメータ"""

    volume: float = 0.5  # 0~1
    fs: ClassVar[int] = 44_100

    def _replace(self, **changes) -> PlayerParameter:
        return dataclasses.replace(self, **changes)

    def volume_up(self) -> PlayerParameter:
        volume = self.volume + 0.1
        if volume > 1:
            volume = 1
        return self._replace(volume=volume)

    def volume_down(self) -> PlayerParameter:
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
        self.param = self.param.volume_up()

    def volume_down(self):
        self.param = self.param.volume_down()


def play_audio2(callback: Callable[[Stream]], is_running: Callable[[], bool], fs: int):
    py_audio = pyaudio.PyAudio()
    stream = py_audio.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

    while is_running():
        callback(stream)
    stream.stop_stream()
    stream.close()
    py_audio.terminate()

    # try:
    #     while True:
    #         if is_running():
    #             stream.start_stream()
    #             callback(stream)
    #         else:
    #             stream.stop_stream()
    # finally:
    #     stream.stop_stream()
    #     stream.close()
    #     py_audio.terminate()
    #


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


def listen_keyboard_input(callback: Callable[[AppCommand], None], is_running: Callable[[bool]]):
    """ キーボードの入力を読み取り対応する AppCommand で Callable を呼ぶ
    :param callback: AppCommandを処理するコールバック関数
    :param is_running:
    """
    while is_running():
        key = readchar.readkey()

        if key == "q":
            callback(AppCommand.app_stop)

        elif key == "z":
            callback(AppCommand.change_play_state)

        elif key == readchar.key.UP:
            callback(AppCommand.volume_up)
        elif key == readchar.key.DOWN:
            callback(AppCommand.volume_down)

        elif key == readchar.key.LEFT:
            callback(AppCommand.traction_up)
        elif key == readchar.key.RIGHT:
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


def main():
    # アプリ内グローバル
    sig_param = SignalParameter(frequency=200)
    player = Player(PlayerParameter())

    # player = Player(PlayerParameter())

    def print_info():
        """CLI画面に表示される情報"""
        print(
            f"\rvolume {player.param.volume:.2f} "
            f"f: {sig_param.frequency} "
            f"traction: {sig_param.traction_direction}",
            end=""
        )

    def execute_command(app_key: AppCommand):
        """AppCommandに対応するアプリ動作をする"""

        if app_key == AppCommand.app_stop:
            is_active_listen_keyboard = False
            player.close()
            loop.stop()
            loop.close()

        elif app_key == AppCommand.change_play_state:
            player.change_play_state()

        elif app_key == AppCommand.volume_up:
            player.volume_up()
        elif app_key == AppCommand.volume_down:
            player.volume_down()

        elif app_key == AppCommand.traction_up:
            sig_param.traction_up()
        elif app_key == AppCommand.traction_down:
            sig_param.traction_down()

        elif app_key == AppCommand.frequency_up:
            sig_param.frequency_up()
        elif app_key == AppCommand.frequency_down:
            sig_param.frequency_down()

        print_info()

    def play():
        player.start()
        while loop.is_running():
            sig = create_asymmetric_signal(
                sig_param.frequency,
                player.param.fs,
                sig_param.traction_direction,
                1
            )
            player.write(sig)

    def is_active_listen_keyboards():
        return is_active_listen_keyboard

    print_info()
    is_active_listen_keyboard = True

    # 起動
    with ThreadPoolExecutor() as pool:
        f1 = loop.run_in_executor(pool, listen_keyboard_input, execute_command,
                                  is_active_listen_keyboards())
        f2 = loop.run_in_executor(pool, play)
        # f = asyncio.gather(f1, f2)
    # loop.run_in_executor(None, play_audio, lambda: loop.is_running())
    # loop.run_in_executor(None, play_audio2, sound, is_playing, player_param.fs)
    # loop.run_forever()
    loop.run_until_complete(f1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    main()
