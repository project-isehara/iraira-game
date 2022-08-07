from __future__ import annotations

import numpy as np


def traction_wave(x, count_anti_node: int = 4) -> np.ndarray:
    """牽引力波形を生成する
    周期2πでcount_anti_node個の腹を持つ関数。最後の腹のみ下に凸でそれ以外は上に凸となる。

    :param x: 角度[rad], array_likeオブジェクトを受け取れる
    :param count_anti_node: 1周期の腹の数, 3以上を指定する
    """
    if not count_anti_node >= 3:
        raise ValueError("count_anti_node expected 3 or more")

    multi_sin_abs = np.abs(np.sin(count_anti_node / 2 * x))

    # 1周期内の最後の腹部分のみ下に凸とする
    x_mod_2pi = x % (2 * np.pi)  # [0 2π]範囲に正規化した角度 [π, 3π, 2π+0.4]→[π, π, 0.4]
    asymmetric_x = (count_anti_node - 1) / count_anti_node * 2 * np.pi
    multi_sin_abs[asymmetric_x < x_mod_2pi] = -multi_sin_abs[asymmetric_x < x_mod_2pi]

    return multi_sin_abs


def show_traction_wave():
    """traction_wave の動作確認"""
    import matplotlib.pyplot as plt

    fs = 10000
    duration_sec = 2.3
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)

    sigs = [
        traction_wave(2 * np.pi * 1 * t),  # f=1,節4つ
        traction_wave(2 * np.pi * 1 * t, 3),  # f=1, 節3つ
        traction_wave(2 * np.pi * (4 / 3) * t, 3),  # f=4/3, 節3つ ==波長はf=1,節4つと同じ
        traction_wave(2 * np.pi * (4 / 3) * t, 3),  # f=4/3, 節3つ ==波長はf=1,節4つと同じ
    ]

    fig, axes = plt.subplots(len(sigs), 1)
    for index, sig in enumerate(sigs):
        axes[index].plot(t, sig)

    plt.show()


if __name__ == "__main__":
    show_traction_wave()
