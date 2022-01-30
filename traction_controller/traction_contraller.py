from __future__ import annotations

from enum import Enum, auto
from functools import lru_cache
from typing import Protocol

import numpy as np
import pyaudio
from state import AppState
from traction_wave import traction_wave


class PlayerState(Protocol):
    """音声プレーヤーの状態"""

    fs: int
    volume: bool
    is_running: bool

    def volume_up(self):
        ...

    def volume_down(self):
        ...

    def change_play_state(self):
        ...


class SignalParam(Protocol):
    """非対称周期信号のパラメータ"""

    frequency: int
    traction_direction: TractionDirection
    count_anti_node: int

    def frequency_up(self):
        ...

    def frequency_down(self):
        ...

    def traction_up(self):
        ...

    def traction_down(self):
        ...

    def count_anti_node_up(self):
        ...

    def count_anti_node_down(self):
        ...


class TractionDirection(Enum):
    """牽引力方向"""

    up = auto()
    down = auto()

    def __str__(self):
        return self.name


class Player:
    """音声プレーヤーの制御"""

    def __init__(self, param: PlayerState):
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@lru_cache(maxsize=1)
def create_traction_wave(
    fs: int, frequency: int, traction_direction: TractionDirection, count_anti_node: int = 4
) -> np.ndarray:

    # 生成波形の長さが波形周波数の整数倍になるように調整
    duration_sec = 0.1
    duration_sec = round(duration_sec * frequency) / frequency

    # 波形生成
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
    sig = traction_wave(2 * np.pi * frequency * t, count_anti_node).astype(np.float32)

    # 牽引力方向の調整
    if traction_direction == TractionDirection.down:
        sig = -sig

    return sig


def play(app_state: AppState, player_param: PlayerState, sig_param: SignalParam):
    with Player(player_param) as player:
        player.start()

        while app_state.is_running:
            if not player_param.is_running:
                player.stop()
                continue
            else:
                player.start()

            sig = create_traction_wave(
                player_param.fs,
                sig_param.frequency,
                sig_param.traction_direction,
                sig_param.count_anti_node,
            )
            player.write(sig)
