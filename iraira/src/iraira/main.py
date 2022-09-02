from __future__ import annotations

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from iraira.player import PlayerState, SignalParam, play
from iraira.state import SharedAppState, SharedGameState, SharedGuiState, SharedPlayerState, SharedSignalParam


def print_info(player_param: PlayerState, sig_param: SignalParam) -> None:
    """CLI画面に表示される情報"""
    print(
        f"\rvolume {player_param.volume:.1f} "
        f"f: {sig_param.frequency:>4} "
        f"traction: {sig_param.traction_direction:>4} "
        f"count_anti_node: {sig_param.count_anti_node:>3} "
        f"play: {'playing' if player_param.play_state else 'stop':>7}",
        end="",
    )


def main() -> None:
    loop = asyncio.new_event_loop()

    # キーボードからのコマンド読み取りと音の再生を別プロセスで実行する。
    # マルチプロセス: ProcessPoolExecutor
    # プロセス間通信: multiprocessing#Manager
    with multiprocessing.Manager() as manager, ProcessPoolExecutor(max_workers=10) as pool:
        app_state = SharedAppState.get_with_init(manager.dict())
        player_state = SharedPlayerState.get_with_init(manager.dict())
        signal_param = SharedSignalParam.get_with_init(manager.dict())
        game_state = SharedGameState.get_with_init(manager.dict())
        gui_state = SharedGuiState.get_with_init(manager.dict())

        print_info(player_state, signal_param)

        futures = []

        try:
            future_play = loop.run_in_executor(pool, play, app_state, player_state, signal_param, game_state, gui_state)
            futures.append(future_play)
        except RuntimeError as e:
            print(f"play module: {e}")

        # GUIがある環境でのみ動作する
        try:
            from iraira.gui import show_gui

            future_gui = loop.run_in_executor(
                pool, show_gui, app_state, player_state, signal_param, game_state, gui_state
            )
            futures.append(future_gui)
        except RuntimeError as e:
            print(f"gui module: {e}")

        # RaspberryPi環境でのみ動作する
        try:
            from iraira.gpio_raspi import switch_listener

            future_gpio = loop.run_in_executor(pool, switch_listener, app_state, signal_param)
            futures.append(future_gpio)
        except RuntimeError as e:
            print(f"gpio module: {e}")

        try:
            from iraira.analog_input import analog_listener

            f_analog_input = loop.run_in_executor(
                pool, analog_listener, app_state, signal_param, player_state, game_state, gui_state
            )
            futures.append(f_analog_input)
        except RuntimeError as e:
            print(f"analog_input module: {e}")

        try:
            from iraira.touch_sensing import touch_listener

            f_touch_sensing = loop.run_in_executor(pool, touch_listener, app_state, game_state, gui_state)
            futures.append(f_touch_sensing)
        except RuntimeError as e:
            print(f"touch_sensing module: {e}")

        f = asyncio.gather(*futures, return_exceptions=True)
        try:
            loop.run_until_complete(f)
        except KeyboardInterrupt:
            f.cancel()
        finally:
            loop.close()
