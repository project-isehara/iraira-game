from __future__ import annotations

from typing import Protocol


class AppState(Protocol):
    """アプリ動作中の状態"""

    is_running: bool
