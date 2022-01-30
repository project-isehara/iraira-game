from __future__ import annotations

from enum import Enum, auto
from typing import Protocol


class AppState(Protocol):
    """アプリ動作中の状態"""

    is_running: bool


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

    def frequency_up(self):
        ...

    def frequency_down(self):
        ...

    def traction_up(self):
        ...

    def traction_down(self):
        ...


class TractionDirection(Enum):
    """牽引力方向"""

    up = auto()
    down = auto()

    def __str__(self):
        return self.name
