from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from enum import auto, Enum

import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import readchar


class TractionDirection(Enum):
    """牽引力方向"""
    up = auto()
    down = auto()


@dataclass()
class SignalParameter:
    """非対称周期信号のパラメータ"""
    volume: float = 0.5
    frequency: float = 200
    traction_direction: TractionDirection = TractionDirection.up

    def replace(self, **changes) -> SignalParameter:
        return dataclasses.replace(self, **changes)

    def volume_up(self):
        self.volume += 0.1

    def volume_down(self):
        self.volume -= 0.1

    def traction_up(self):
        self.traction_direction = TractionDirection.up

    def traction_down(self):
        self.traction_direction = TractionDirection.down


def listen_keyboard():
    while True:
        key = readchar.readkey()

        if key == "q":
            loop.stop()
            loop.close()
            return
        elif key == readchar.key.UP:
            print("\rinput:: UP", end="")
            signal_parameter.volume_up()
        elif key == readchar.key.DOWN:
            print("\rinput:: DOWN", end="")
            signal_parameter.volume_down()
        elif key == readchar.key.LEFT:
            print("\rinput:: LEFT", end="")
            signal_parameter.traction_up()
        elif key == readchar.key.RIGHT:
            print("\rinput:: RIGHT", end="")
            signal_parameter.traction_down()
        else:
            print(f"\rinput:: {key}", end="")


def play_audio(is_running: Callable[[], bool]):
    fs = 44_100  # サンプリング周波数[Hz]
    duration_sec = 1
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

    while loop.is_running():

        sig = asymmetric_signal(2 * np.pi * signal_parameter.frequency * t).astype(np.float32)
        if signal_parameter.traction_direction == TractionDirection.down:
            sig = -sig

        stream.write((signal_parameter.volume * sig).tobytes())

    stream.stop_stream()
    stream.close()
    p.terminate()


def play_audio2(signal: np.ndarray, is_running: Callable[[], bool], fs: int):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

    while is_running():
        stream.write(signal.tobytes())

    stream.stop_stream()
    stream.close()
    p.terminate()


def aaa():
    fs = 44_100  # サンプリング周波数[Hz]
    sig = create_asymmetric_signal(
        signal_parameter.frequency,
        fs,
        signal_parameter.traction_direction,
        1
    )

    play_audio2(sig, lambda: loop.is_running(), fs)


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


def asymmetric_signal(x, count_anti_node: int = 4) -> np.ndarray:
    """非対称周期信号を生成する
    周期2πでcount_anti_node個の腹を関数。最後の腹のみ下に凸でそれ以外は上に凸となる。

    :param x: 角度[rad], array_likeオブジェクトを受け取れる
    :param count_anti_node: 非対称関数1周期の腹の数, 3以上を指定する
    """
    if not count_anti_node >= 3:
        raise ValueError("count_anti_node expected 3 or more")

    multi_sin_abs = np.abs(np.sin(count_anti_node / 2 * x))

    # 1周期内の最後の腹部分のみ下に凸とする
    x_mod_2pi = x % (2 * np.pi)  # [0 2π]範囲の周波数値
    asymmetric_x = (count_anti_node - 1) / count_anti_node * 2 * np.pi
    multi_sin_abs[asymmetric_x < x_mod_2pi] = -multi_sin_abs[asymmetric_x < x_mod_2pi]

    return multi_sin_abs


def test_asymmetric_signal():
    """asymmetric_signal の動作確認"""
    fs = 1001
    duration_sec = 2.3
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)

    sigs = [
        asymmetric_signal(2 * np.pi * 1 * t),  # f=1,節4つ
        asymmetric_signal(2 * np.pi * (4 / 3) * t, 3),  # f=4/3, 節3つ ==波長はf=1,節4つと同じ
        asymmetric_signal(2 * np.pi * 1 * t, 3),  # f=1, 節3つ
    ]

    fig, axes = plt.subplots(len(sigs), 1)
    for index, sig in enumerate(sigs):
        axes[index].plot(t, sig)
    plt.show()


def main():
    loop.run_in_executor(None, listen_keyboard)
    loop.run_in_executor(None, play_audio)
    loop.run_forever()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    signal_parameter = SignalParameter()
    main()
