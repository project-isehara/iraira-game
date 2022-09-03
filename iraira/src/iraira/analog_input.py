import sys
import time

import serial

from iraira.player import SignalParam
from iraira.state import AppState, GameState, GuiState, Page, PlayerState

ZERO_VALUE_RANGE = 0.02  # アナログ値の中央から±この範囲の値まで，ゼロとして扱う


def analog_listener(
    app_state: AppState,
    sig_param: SignalParam,
    player_state: PlayerState,
    game_state: GameState,
    gui_state: GuiState,
) -> None:
    try:
        with serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01) as serial_port:
            reading_bytes: bytes = bytes()

            while app_state.is_running:
                read_bytes: bytes = serial_port.read_all()
                if read_bytes is None or len(read_bytes) == 0:
                    continue

                # 文字列の受信とデコードを行う．文字列は0.0~1.0までの浮動小数点数の文字列(小数点以下3桁)および，"p"(ボタン押下時),"r"(ボタン解放時),"l"(ボタン長押し時)
                all_read_bytes = reading_bytes + read_bytes
                all_completed_string: str = None  # その時点で，完全な行として読み込んだ要素からなる文字列

                last_ln_index = all_read_bytes.decode("utf8").rfind("\n")
                if last_ln_index == len(all_read_bytes) - 1:  # 読み込んだタイミングで，行を全受信していた場合
                    reading_bytes = bytes()  # 読みかけの要素なし
                    all_completed_string = all_read_bytes.decode("utf8")
                else:
                    reading_bytes = all_read_bytes[last_ln_index:]
                    all_completed_string = all_read_bytes[:last_ln_index].decode("utf8")

                all_lines = all_completed_string.split("\n")
                analog_value: float = None
                for line in all_lines:
                    if line == "":
                        continue

                    if line[0] == "p":  # 押下
                        button_pressed(game_state, gui_state)
                    elif line[0] == "r":  # 開放
                        # button_released(game_state,gui_state)
                        None
                    elif line[0] == "l":  # 長押し
                        button_longpressed(game_state, gui_state)
                    else:
                        analog_value = float(line) - 0.5

                if analog_value is not None:
                    volume: float = 0
                    if abs(analog_value) < ZERO_VALUE_RANGE:
                        volume = 0
                    elif analog_value < 0:
                        sig_param.traction_down()
                        volume = (-analog_value - ZERO_VALUE_RANGE) / (0.5 - ZERO_VALUE_RANGE)
                    else:
                        sig_param.traction_up()
                        volume = (analog_value - ZERO_VALUE_RANGE) / (0.5 - ZERO_VALUE_RANGE)

                    player_state.volume = volume

                time.sleep(0.2)

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)


def button_pressed(game_state: GameState, gui_state: GuiState) -> None:
    current_page = gui_state.current_page

    if current_page == Page.TITLE:
        gui_state.current_page = Page.GAME

    if current_page == Page.RESULT:
        gui_state.current_page = Page.TITLE
        game_state.clear_game_state()


def button_released(game_state: GameState, gui_state: GuiState) -> None:
    None


def button_longpressed(game_state: GameState, gui_state: GuiState) -> None:
    if gui_state.current_page == Page.GAME:
        gui_state.current_page = Page.TITLE
        game_state.clear_game_state()
