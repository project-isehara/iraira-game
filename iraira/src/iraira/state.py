from __future__ import annotations

import time
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


@dataclass
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

    @staticmethod
    def get(d: DictProxy) -> SharedAppState:
        return SharedAppState(d)

    @staticmethod
    def get_with_init(d: DictProxy) -> SharedAppState:
        d["is_running"] = True
        return SharedAppState(d)


class PlayerState(Protocol):
    """振動再生のパラメータ"""

    @property
    def fs(self) -> int:
        ...

    @property
    def volume(self) -> float:
        ...

    @volume.setter
    def volume(self, value: float) -> None:
        ...

    @property
    def play_state(self) -> bool:
        ...

    @play_state.setter
    def play_state(self, value: bool) -> None:
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
    def play_state(self) -> bool:
        return self._raw["play_state"]

    @play_state.setter
    def play_state(self, value: bool) -> None:
        self._raw["play_state"] = value

    @property
    def volume(self) -> float:
        return self._raw["volume"]

    @volume.setter
    def volume(self, value: float) -> None:
        if value > 1:
            value = 1
        if value < 0:
            value = 0
        self._raw["volume"] = value

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
        self._raw["play_state"] = not self._raw["play_state"]

    @staticmethod
    def get(d: DictProxy) -> SharedPlayerState:
        return SharedPlayerState(d)

    @staticmethod
    def get_with_init(
        d: DictProxy,
        fs: int = 44_100,
        volume: float = 0.5,
        play_state: bool = False,
    ) -> SharedPlayerState:
        d["fs"] = fs
        d["volume"] = volume
        d["play_state"] = play_state
        return SharedPlayerState(d)


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
    def get(d: DictProxy) -> SharedSignalParam:
        return SharedSignalParam(d)

    @staticmethod
    def get_with_init(
        d: DictProxy,
        frequency: int = 63,
        direction: TractionDirection = TractionDirection.up,
        count_anti_node: int = 4,
    ) -> SharedSignalParam:
        d["frequency"] = frequency
        d["traction_direction"] = direction
        d["count_anti_node"] = count_anti_node
        return SharedSignalParam(d)


class GameState(Protocol):
    """ゲームの状態を管理"""

    @property
    def touch_count(self) -> int:
        ...

    @property
    def touch_time(self) -> float:
        ...

    @property
    def is_goaled(self) -> bool:
        ...

    @is_goaled.setter
    def is_goaled(self, value: bool) -> None:
        ...

    @property
    def start_time(self) -> float:
        ...

    @start_time.setter
    def start_time(self, value: float) -> None:
        ...

    def increment_touch_count(self) -> None:
        ...

    def add_touch_time(self, touching_time: float) -> None:
        ...

    def clear_game_state(self) -> None:
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
    def is_goaled(self) -> bool:
        return self._raw["isGoaled"]

    @is_goaled.setter
    def is_goaled(self, value: bool) -> None:
        self._raw["isGoaled"] = value

    @property
    def start_time(self) -> float:
        return self._raw["start_time"]

    @start_time.setter
    def start_time(self, value: float) -> None:
        self._raw["start_time"] = value

    def increment_touch_count(self) -> None:
        count = self._raw["touch_count"]
        self._raw["touch_count"] = count + 1

    def add_touch_time(self, touching_time: float) -> None:
        current_touching_time = self._raw["touch_time"]
        self._raw["touch_time"] = current_touching_time + touching_time

    def clear_game_state(self) -> None:
        self._raw["touch_count"] = 0
        self._raw["touch_time"] = 0
        self._raw["isGoaled"] = False
        self._raw["start_time"] = time.time()

    @staticmethod
    def get(d: DictProxy) -> SharedGameState:
        return SharedGameState(d)

    @staticmethod
    def get_with_init(
        d: DictProxy,
        touch_count: int = 0,
        touch_time: float = 0.0,
        is_goaled: bool = False,
    ) -> SharedGameState:
        d["touch_count"] = touch_count
        d["touch_time"] = touch_time
        d["isGoaled"] = is_goaled
        d["start_time"] = 0
        return SharedGameState(d)


class GuiState(Protocol):
    """ゲーム画面の管理"""

    @property
    def current_page(self) -> Page:
        ...

    @current_page.setter
    def current_page(self, value: Page) -> None:
        ...


@dataclass
class SharedGuiState:
    """GuiStateの実装"""

    _raw: DictProxy[str, Any]

    @property
    def current_page(self) -> Page:
        return self._raw["current_page"]

    @current_page.setter
    def current_page(self, value: Page) -> None:
        self._raw["current_page"] = value

    @staticmethod
    def get(d: DictProxy) -> SharedGuiState:
        return SharedGuiState(d)

    @staticmethod
    def get_with_init(d: DictProxy) -> SharedGuiState:
        d["current_page"] = Page.TITLE
        return SharedGuiState(d)


class Page(Enum):
    """GUIの大画面項目"""

    TITLE = auto()
    GAME = auto()
    RESULT = auto()
