from __future__ import annotations

import tkinter as tk

from iraira.player import SignalParam
from iraira.state import AppState, PlayerState


class Application(tk.Frame):
    """GUI表示

    画面遷移
    [ゲームスタート] → []

    常時入力対応キーボードコマンド
    * q: アプリを終了する

    ゲーム中コマンドキーボードコマンド
    * [space]: 牽引力振動の再生/停止
    * 左矢印[←]: 牽引力振動の方向を左にする
    * 右矢印[→]: 牽引力振動の方向を右にする
    """

    def __init__(self, master: tk.Tk, app_state: AppState, sig_param: SignalParam, player_param: PlayerState):
        super().__init__(master)

        self._app_state = app_state
        self._sig_param = sig_param
        self._player_param = player_param

        self.check_close()

        self.master = master
        self.master.geometry("800x600")
        self.master.title("イライラ棒")
        self.pack()
        self.create_widgets()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close_botton_click)

    def check_close(self) -> None:
        """アプリの起動状態監視と終了処理"""
        if not self._app_state.is_running:
            self.master.destroy()
            return

        self.after(1000, self.check_close)

    def on_close_botton_click(self) -> None:
        """ウィンドウの閉じる[x]ボタンを押したときの処理"""
        self.master.destroy()
        self._app_state.is_running = False

    def create_widgets(self) -> None:
        # アプリ情報
        status_text = (
            f"volume {self._player_param.volume:.1f}\n"
            f"f: {self._sig_param.frequency:>4}\n"
            f"traction: {self._sig_param.traction_direction:>4}\n"
            f"count_anti_node: {self._sig_param.count_anti_node:>3}\n"
            f"play: {'playing' if self._player_param.is_running else 'stop':>7}"
        )
        self.status = tk.Label(self, text=status_text, font=(None, 24), width="100", anchor=tk.W)
        self.status.pack()
        self.show_status()

        # キーボードプレス値
        self.key_value = tk.StringVar()
        self.key = tk.Label(self, textvariable=self.key_value, font=(None, 48), width="100")
        self.key.pack(pady=50)
        self.key.bind("<KeyPress>", self.input_key)
        self.key.focus_set()

    def show_status(self) -> None:
        self.status.configure(
            text=(
                f"volume {self._player_param.volume:.1f}\n"
                f"f: {self._sig_param.frequency:>4}\n"
                f"traction: {self._sig_param.traction_direction:>4}\n"
                f"count_anti_node: {self._sig_param.count_anti_node:>3}\n"
                f"play: {'playing' if self._player_param.is_running else 'stop':>7}"
            )
        )

        self.after(200, self.show_status)

    def input_key(self, event: tk.Event) -> None:
        """キーボードイベント処理"""
        print(event, event.keysym_num)
        key_name = event.keysym
        self.key_value.set(key_name)

        if event.keysym_num == 113:  # key: q
            self._app_state.is_running = False
        elif event.keysym_num == 32:  # key: space
            self._player_param.change_play_state()

        elif event.keysym_num == 65361:  # key: Left
            self._sig_param.traction_up()
        elif event.keysym_num == 65363:  # key: Right
            self._sig_param.traction_down()


def show_gui(app_state: AppState, player_param: PlayerState, sig_param: SignalParam) -> None:
    """アプリGUI画面を表示する"""
    try:
        app = Application(tk.Tk(), app_state, sig_param, player_param)
        app.mainloop()
    except KeyboardInterrupt:
        app.master.destroy()
