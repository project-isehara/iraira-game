from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class AppState(Protocol):
    """アプリ動作中の状態"""

    is_running: bool


@dataclass
class AppStateMultiProcessing:
    """MultiProcessingで使用できる AppState の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: dict

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

    @is_running.setter
    def is_running(self, value: bool):
        self._raw["is_running"] = value


@dataclass
class PlayerStateMultiProcessing:
    """MultiProcessingで使用できる PlayerState の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: dict

    @property
    def fs(self) -> int:
        return self._raw["fs"]

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

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
        self._raw["is_running"] = not self._raw["is_running"]

    @staticmethod
    def setup_dict(d: dict, fs: int = 44_100, volume: float = 0.5, is_running: bool = True) -> dict:
        d["fs"] = fs
        d["volume"] = volume
        d["is_running"] = is_running
        return d


class TractionDirection(Enum):
    """牽引力方向"""

    up = auto()
    down = auto()

    def __str__(self):
        return self.name


@dataclass
class SignalParamMultiProcessing:
    """MultiProcessingで使用できる SignalParam の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: dict

    @property
    def frequency(self) -> int:
        return self._raw["frequency"]

    def frequency_up(self):
        f = self._raw["frequency"]
        assert f <= 1000
        if f == 1000:
            return
        self._raw["frequency"] = f + 1

    def frequency_down(self):
        f = self._raw["frequency"]
        assert f >= 20
        if f == 20:
            return
        self._raw["frequency"] = f - 1

    @property
    def traction_direction(self) -> TractionDirection:
        return self._raw["traction_direction"]

    def traction_change(self):
        if self.traction_direction == TractionDirection.up:
            self._raw["traction_direction"] = TractionDirection.down
        else:
            self._raw["traction_direction"] = TractionDirection.up

    def traction_up(self):
        self._raw["traction_direction"] = TractionDirection.up

    def traction_down(self):
        self._raw["traction_direction"] = TractionDirection.down

    @property
    def count_anti_node(self) -> int:
        return self._raw["count_anti_node"]

    def count_anti_node_up(self):
        n = self._raw["count_anti_node"]
        assert n <= 1000
        if n == 1000:
            return
        self._raw["count_anti_node"] = n + 1

    def count_anti_node_down(self):
        n = self._raw["count_anti_node"]
        assert n >= 3
        if n == 3:
            return
        self._raw["count_anti_node"] = n - 1

    @staticmethod
    def setup_dict(
        d: dict,
        frequency: int = 63,
        direction: TractionDirection = TractionDirection.up,
        count_anti_node: int = 4,
    ) -> dict:
        d["frequency"] = frequency
        d["traction_direction"] = direction
        d["count_anti_node"] = count_anti_node
        return d


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

    def traction_change(self):
        ...

    def count_anti_node_up(self):
        ...

    def count_anti_node_down(self):
        ...
