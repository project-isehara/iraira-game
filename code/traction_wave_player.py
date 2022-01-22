from __future__ import annotations

import asyncio
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pyaudio

import readchar


# やりたいこと
# 変更できるパラメータ
# * 音量
# * 牽引力方向
# * 周波数
# 持続時間式ではなくstart/stop式にする


def play_audio():
    # パラメータ
    volume: float = 0.5

    fs = 44_100  # サンプリング周波数[Hz]
    duration_sec = 2
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
    f = 200  # 非対称周期関数の周波数

    sig = asymmetric_signal(2 * np.pi * f * t).astype(np.float32)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

    for _ in range(3):
        stream.write((volume * sig).tobytes())

    stream.stop_stream()
    stream.close()
    p.terminate()


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
    play_audio()


if __name__ == "__main__":
    main()
