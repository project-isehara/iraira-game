from collections.abc import Callable
from enum import Enum, auto

import readchar

from iraira.state import AppState, PlayerState, SignalParam


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

    anti_node_up = auto()
    anti_node_down = auto()


def execute_command(
    app_key: AppCommand,
    app_state: AppState,
    player_param: PlayerState,
    sig_param: SignalParam,
) -> None:
    """AppCommandに対応するアプリ動作をする"""

    if app_key == AppCommand.app_stop:
        app_state.is_running = False

    elif app_key == AppCommand.pause:
        player_param.change_play_state()

    elif app_key == AppCommand.volume_up:
        player_param.volume_up()
    elif app_key == AppCommand.volume_down:
        player_param.volume_down()

    elif app_key == AppCommand.traction_up:
        sig_param.traction_up()
    elif app_key == AppCommand.traction_down:
        sig_param.traction_down()

    elif app_key == AppCommand.frequency_up:
        sig_param.frequency_up()
    elif app_key == AppCommand.frequency_down:
        sig_param.frequency_down()

    elif app_key == AppCommand.anti_node_up:
        sig_param.count_anti_node_up()
    elif app_key == AppCommand.anti_node_down:
        sig_param.count_anti_node_down()

    # print_info(player_param, sig_param)


def keyboard_listener(
    callback: Callable[[AppCommand], None],
    app_state: AppState,
) -> None:
    """キーボードの入力を読み取り対応するAppCommandでCallableを呼ぶ
    :param callback: AppCommandを処理するコールバック関数
    :param app_state: アプリ動作状態
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

        elif key in (readchar.key.UP, "a"):
            callback(AppCommand.volume_up)
        elif key in (readchar.key.DOWN, "z"):
            callback(AppCommand.volume_down)

        elif key in (readchar.key.LEFT, "d"):
            callback(AppCommand.traction_up)
        elif key in (readchar.key.RIGHT, "c"):
            callback(AppCommand.traction_down)

        elif key == "s":
            callback(AppCommand.frequency_up)
        elif key == "x":
            callback(AppCommand.frequency_down)

        elif key == "f":
            callback(AppCommand.anti_node_up)
        elif key == "v":
            callback(AppCommand.anti_node_down)
