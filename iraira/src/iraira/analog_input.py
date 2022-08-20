import sys
import time

import serial

from iraira.player import SignalParam
from iraira.state import AppState, PlayerState

ZERO_VALUE_RANGE = 0.02  # アナログ値の中央から±この範囲の値まで，ゼロとして扱う


def analog_listener(
    app_state: AppState,
    sig_param: SignalParam,
    player_state: PlayerState,
) -> None:
    try:
        with serial.Serial("/dev/ttyUSB0", 115200, timeout=0.01) as serial_port:
            last_read_line: str = ""
            reading_bytes: bytes = bytes()

            while app_state.is_running:
                read_bytes: bytes = serial_port.read_all()
                if read_bytes is None or len(read_bytes) == 0:
                    continue

                # 文字列の受信とデコードを行う．文字列は0.0~1.0までの浮動小数点数の文字列(小数点以下3桁)
                all_read_bytes = reading_bytes + read_bytes
                all_lines = all_read_bytes.decode("utf8").split("\n")

                if all_read_bytes[-1] == "\n":  # 読み込んだタイミングで，行を全受信していた場合
                    last_read_line = all_lines[-2]  # このとき，最後の改行で空要素が入るため，最終行は最後から一つ手前
                    reading_bytes = bytes()

                else:
                    # 読み込んだタイミングで，行を受信途中の場合．ex."0.553\n0.5"
                    reading_bytes = all_lines[-1].encode("utf8")
                    if len(all_lines) > 1:
                        last_read_line = all_lines[-2]

                analog_value = float(last_read_line) - 0.5

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
