from collections.abc import Callable
from enum import Enum, auto

import readchar
from state import AppStateHelper


class AppCommand(Enum):
    """アプリ操作コマンド"""

    app_stop = auto()

    volume_up = auto()
    volume_down = auto()

    traction_up = auto()
    traction_down = auto()

    frequency_up = auto()
    frequency_down = auto()

    change_play_state = auto()


def keyboard_listener(
    callback: Callable[[AppCommand], None],
    h: AppStateHelper,
):
    """キーボードの入力を読み取り対応するAppCommandでCallableを呼ぶ
    :param callback: AppCommandを処理するコールバック関数
    :param h:
    """

    while h.running:
        key = readchar.readkey()  # ブロッキング
        if key == "q":
            h.running = False
            callback(AppCommand.app_stop)
            return

        elif key == readchar.key.SPACE:
            callback(AppCommand.change_play_state)

        elif key == readchar.key.UP:
            callback(AppCommand.volume_up)
        elif key == readchar.key.DOWN:
            callback(AppCommand.volume_down)

        elif key == readchar.key.LEFT:
            callback(AppCommand.traction_up)
        elif key == readchar.key.RIGHT:
            callback(AppCommand.traction_down)

        elif key == "a":
            callback(AppCommand.frequency_up)
        elif key == "s":
            callback(AppCommand.frequency_down)
