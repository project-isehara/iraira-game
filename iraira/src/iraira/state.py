from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from multiprocessing.managers import DictProxy  # type: ignore
from typing import Any, Protocol


class AppState(Protocol):
    """アプリ動作中の状態"""

    @property
    def is_running(self) -> bool:
        """アプリの動作状態"""
        ...

    @is_running.setter
    def is_running(self, value: bool) -> None:
        """アプリの動作状態をセットする"""
        ...


@dataclass()
class SharedAppState:
    """AppStateの実装

    MultiProcessingのDictProxyのラッパークラスでありマルチプロセスで状態共有できる
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: DictProxy[str, Any]

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

    @is_running.setter
    def is_running(self, value: bool) -> None:
        self._raw["is_running"] = value


class PlayerState(Protocol):
    """振動再生のパラメータ"""

    @property
    def fs(self) -> int:
        ...

    @property
    def volume(self) -> float:
        ...

    @volume.setter
    def volume(self,v:float) -> None:
        ...

    @property
    def is_running(self) -> bool:
        ...

    def volume_up(self) -> None:
        ...

    def volume_down(self) -> None:
        ...

    def change_play_state(self) -> None:
        ...


@dataclass
class SharedPlayerState:
    """PlayerStateの実装クラス

    MultiProcessingのDictProxyのラッパークラスでありマルチプロセスで状態共有できる
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: DictProxy[str, Any]

    @property
    def fs(self) -> int:
        return self._raw["fs"]

    @property
    def is_running(self) -> bool:
        return self._raw["is_running"]

    @property
    def volume(self) -> float:
        return self._raw["volume"]

    @volume.setter
    def volume(self,v:float) -> None:
        if v > 1:
            v = 1
        if v < 0:
            v = 0
        self._raw["volume"] = v

    def volume_up(self) -> None:
        v = self.volume
        v += 0.1
        if v > 1:
            v = 1
        self._raw["volume"] = v

    def volume_down(self) -> None:
        v = self.volume
        v -= 0.1
        if v < 0:
            v = 0
        self._raw["volume"] = v

    def change_play_state(self) -> None:
        self._raw["is_running"] = not self._raw["is_running"]

    @staticmethod
    def setup_dict(d: DictProxy, fs: int = 44_100, volume: float = 0.5, is_running: bool = True) -> DictProxy:
        d["fs"] = fs
        d["volume"] = volume
        d["is_running"] = is_running
        return d


class TractionDirection(Enum):
    """牽引力方向"""

    up = auto()
    down = auto()

    def __str__(self) -> str:
        return self.name


class SignalParam(Protocol):
    """非対称周期信号のパラメータ"""

    @property
    def frequency(self) -> int:
        ...

    @property
    def traction_direction(self) -> TractionDirection:
        ...

    @property
    def count_anti_node(self) -> int:
        ...

    def frequency_up(self) -> None:
        ...

    def frequency_down(self) -> None:
        ...

    def traction_up(self) -> None:
        ...

    def traction_down(self) -> None:
        ...

    def traction_change(self) -> None:
        ...

    def count_anti_node_up(self) -> None:
        ...

    def count_anti_node_down(self) -> None:
        ...


@dataclass
class SharedSignalParam:
    """MultiProcessingで使用できる SignalParam の実装クラス
    状態を扱うプロセスごとにインスタンスを生成しなければいけない
    """

    _raw: DictProxy[str, Any]

    @property
    def frequency(self) -> int:
        return self._raw["frequency"]

    def frequency_up(self) -> None:
        f = self._raw["frequency"]
        assert f <= 1000
        if f == 1000:
            return
        self._raw["frequency"] = f + 1

    def frequency_down(self) -> None:
        f = self._raw["frequency"]
        assert f >= 20
        if f == 20:
            return
        self._raw["frequency"] = f - 1

    @property
    def traction_direction(self) -> TractionDirection:
        return self._raw["traction_direction"]

    def traction_change(self) -> None:
        if self.traction_direction == TractionDirection.up:
            self._raw["traction_direction"] = TractionDirection.down
        else:
            self._raw["traction_direction"] = TractionDirection.up

    def traction_up(self) -> None:
        self._raw["traction_direction"] = TractionDirection.up

    def traction_down(self) -> None:
        self._raw["traction_direction"] = TractionDirection.down

    @property
    def count_anti_node(self) -> int:
        return self._raw["count_anti_node"]

    def count_anti_node_up(self) -> None:
        n = self._raw["count_anti_node"]
        assert n <= 1000
        if n == 1000:
            return
        self._raw["count_anti_node"] = n + 1

    def count_anti_node_down(self) -> None:
        n = self._raw["count_anti_node"]
        assert n >= 3
        if n == 3:
            return
        self._raw["count_anti_node"] = n - 1

    @staticmethod
    def setup_dict(
        d: DictProxy,
        frequency: int = 63,
        direction: TractionDirection = TractionDirection.up,
        count_anti_node: int = 4,
    ) -> DictProxy:
        d["frequency"] = frequency
        d["traction_direction"] = direction
        d["count_anti_node"] = count_anti_node
        return d

class GameState(Protocol):
    """ゲームの状態を管理"""

    @property
    def touch_count(self) -> int:
        ...

    @property
    def touch_time(self) -> float:
        ...

    @property
    def isGoaled(self) -> bool:
        ...

    @isGoaled.setter
    def isGoaled(self,isGoaled) -> None:
        ...

    def increment_touch_count(self) -> None:
        ...

    def add_touch_time(self,touching_time:float) -> None:
        ...

    def clear_game_state(self,touching_time:float) -> None:
        ...

@dataclass
class SharedGameState:
    """GameStateの実装"""

    _raw: DictProxy[str, Any]

    @property
    def touch_count(self) -> int:
        return self._raw["touch_count"]

    @property
    def touch_time(self) -> float:
        return self._raw["touch_time"]

    @property
    def isGoaled(self) -> bool:
        return self._raw["isGoaled"]

    @isGoaled.setter
    def isGoaled(self,isGoaled) -> None:
        self._raw["isGoaled"]=isGoaled

    def increment_touch_count(self) -> None:
        count = self._raw["touch_count"]
        self._raw["touch_count"] = count+1

    def add_touch_time(self,touching_time:float) -> None:
        current_touching_time = self._raw["touch_time"]
        self._raw["touch_time"] = current_touching_time + touching_time

    def clear_game_state(self,touching_time:float) -> None:
        self._raw["touch_count"] = 0 
        self._raw["touch_time"] = 0 

    @staticmethod
    def setup_dict(
        d: DictProxy,
        touch_count: int = 0,
        touch_time: float = 0.0,
        isGoaled: bool = False,
    ) -> DictProxy:
        d["touch_count"] = touch_count 
        d["touch_time"] = touch_time 
        d["isGoaled"] = isGoaled 
        return d