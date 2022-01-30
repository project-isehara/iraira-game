from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pyaudio
from state import PlayerState, TractionDirection


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

    def volume_up(self):
        self.param.volume_up()

    def volume_down(self):
        self.param.volume_down()
