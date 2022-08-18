from __future__ import annotations

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from iraira.player import PlayerState, SignalParam, play
from iraira.state import AppState, SharedAppState, SharedPlayerState, SharedSignalParam


def print_info(player_param: PlayerState, sig_param: SignalParam) -> None:
    """CLI画面に表示される情報"""
    print(
        f"\rvolume {player_param.volume:.1f} "
        f"f: {sig_param.frequency:>4} "
        f"traction: {sig_param.traction_direction:>4} "
        f"count_anti_node: {sig_param.count_anti_node:>3} "
        f"play: {'playing' if player_param.is_running else 'stop':>7}",
        end="",
    )


# async def main_process(span: int, app_state: AppState) -> None:
#     idx = 1
#     while app_state.is_running:
#         await asyncio.sleep(span)
#         num_active_tasks = len([task for task in asyncio.all_tasks() if not task.done()])
#         # if num_active_tasks == 1:
#         #     break
#         print(f"[run:{num_active_tasks}]{idx * span}秒経過")
#         idx += 1


def main() -> None:
    loop = asyncio.new_event_loop()

    # キーボードからのコマンド読み取りと音の再生を別プロセスで実行する。
    # マルチプロセス: ProcessPoolExecutor
    # プロセス間通信: multiprocessing#Manager
    with multiprocessing.Manager() as manager, ProcessPoolExecutor() as pool:
        app_state = SharedAppState.get_with_init(manager.dict())
        player_state = SharedPlayerState.get_with_init(manager.dict())
        signal_param = SharedSignalParam.get_with_init(manager.dict())

        print_info(player_state, signal_param)

        futures = []

        # # キーボード入力 GUIで実施するので一旦停止
        # from functools import partial
        # from iraira.keyboard import execute_command, keyboard_listener

        # partial_execute_command = partial(
        #     execute_command,
        #     app_state=app_state,
        #     player_param=player_state,
        #     sig_param=signal_param,
        # )
        # f = loop.run_in_executor(
        #     pool,
        #     keyboard_listener,
        #     partial_execute_command,
        #     app_state,
        # )
        # futures.append(f)

        future_play = loop.run_in_executor(
            pool,
            play,
            app_state,
            player_state,
            signal_param,
        )
        futures.append(future_play)

        # GUIがある環境でのみ動作する
        try:
            from iraira.gui import show_gui

            future_gui = loop.run_in_executor(
                pool,
                show_gui,
                app_state,
                player_state,
                signal_param,
            )
            futures.append(future_gui)
        except RuntimeError as e:
            print(f"tkinter: {e}")

        # RaspberryPi環境でのみ動作する
        try:
            from iraira.gpio_raspi import switch_listener

            future_gpio = loop.run_in_executor(pool, switch_listener, app_state, signal_param)
            futures.append(future_gpio)
        except RuntimeError as e:
            print(f"RPi.GPIO: {e}")

        f = asyncio.gather(*futures, return_exceptions=True)
        try:
            loop.run_until_complete(f)
        except KeyboardInterrupt:
            f.cancel()
        finally:
            loop.close()
