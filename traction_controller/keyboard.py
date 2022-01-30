from collections.abc import Callable
from enum import Enum, auto

import readchar
from state import AppState


class AppCommand(Enum):
    """アプリ操作コマンド"""

    app_stop = auto()
    pause = auto()

    volume_up = auto()
    volume_down = auto()

    traction_up = auto()
    traction_down = auto()

    frequency_up = auto()
    frequency_down = auto()


def keyboard_listener(
    callback: Callable[[AppCommand], None],
    app_state: AppState,
):
    """キーボードの入力を読み取り対応するAppCommandでCallableを呼ぶ
    :param callback: AppCommandを処理するコールバック関数
    :param app_state:
    """

    while app_state.is_running:
        key = readchar.readkey()  # ブロッキング
        # print(ord(key))

        if key == "q":
            app_state.is_running = False
            callback(AppCommand.app_stop)
            return

        elif key == readchar.key.SPACE:
            callback(AppCommand.pause)

        elif key in (readchar.key.UP, "s"):
            callback(AppCommand.volume_up)
        elif key in (readchar.key.DOWN, "x"):
            callback(AppCommand.volume_down)

        elif key in (readchar.key.LEFT, "d"):
            callback(AppCommand.traction_up)
        elif key in (readchar.key.RIGHT, "c"):
            callback(AppCommand.traction_down)

        elif key == "a":
            callback(AppCommand.frequency_up)
        elif key == "z":
            callback(AppCommand.frequency_down)
