from __future__ import annotations

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from iraira.gui import show_gui
from iraira.keyboard import AppCommand, keyboard_listener
from iraira.player import PlayerState, SignalParam, play
from iraira.state import AppState, AppStateMultiProcessing, PlayerStateMultiProcessing, SignalParamMultiProcessing
from iraira.switch import switch_listener


def print_info(player_param: PlayerState, sig_param: SignalParam):
    """CLI画面に表示される情報"""
    print(
        f"\rvolume {player_param.volume:.1f} "
        f"f: {sig_param.frequency:>4} "
        f"traction: {sig_param.traction_direction:>4} "
        f"count_anti_node: {sig_param.count_anti_node:>3} "
        f"play: {'playing' if player_param.is_running else 'stop':>7}",
        end="",
    )


def execute_command(
    app_key: AppCommand,
    app_state: AppState,
    player_param: PlayerState,
    sig_param: SignalParam,
):
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

    print_info(player_param, sig_param)


def main():
    loop = asyncio.new_event_loop()

    # キーボードからのコマンド読み取りと音の再生を別プロセスで実行する。
    # マルチプロセス: ProcessPoolExecutor
    # プロセス間通信: multiprocessing#Manager
    with multiprocessing.Manager() as manager, ProcessPoolExecutor() as pool:
        app_state_dict = manager.dict()
        player_state_dict = PlayerStateMultiProcessing.setup_dict(manager.dict())
        signal_param_dict = SignalParamMultiProcessing.setup_dict(manager.dict())

        AppStateMultiProcessing(app_state_dict).is_running = True

        print_info(
            PlayerStateMultiProcessing(player_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        partial_execute_command = partial(
            execute_command,
            app_state=AppStateMultiProcessing(app_state_dict),
            player_param=PlayerStateMultiProcessing(player_state_dict),
            sig_param=SignalParamMultiProcessing(signal_param_dict),
        )

        f1 = loop.run_in_executor(
            pool,
            keyboard_listener,
            partial_execute_command,
            AppStateMultiProcessing(app_state_dict),
        )
        f2 = loop.run_in_executor(
            pool,
            play,
            AppStateMultiProcessing(app_state_dict),
            PlayerStateMultiProcessing(player_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        f3 = loop.run_in_executor(
            pool,
            switch_listener,
            AppStateMultiProcessing(app_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        f4 = loop.run_in_executor(
            pool,
            show_gui,
            AppStateMultiProcessing(app_state_dict),
            SignalParamMultiProcessing(signal_param_dict),
        )

        f = asyncio.gather(f1, f2, f3, f4, return_exceptions=True)
        loop.run_until_complete(f)
