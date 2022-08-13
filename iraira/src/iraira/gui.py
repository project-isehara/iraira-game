from __future__ import annotations

import tkinter as tk

from iraira.player import SignalParam
from iraira.state import AppState, PlayerState


class Application(tk.Frame):
    def __init__(self, master: tk.Tk, app_state: AppState, sig_param: SignalParam, player_param: PlayerState):
        super().__init__(master)

        self.app_state = app_state
        self.sig_param = sig_param
        self.player_param = player_param

        self.after(1000, self.check_close)

        self.master = master
        self.master.geometry("500x300")
        self.master.protocol("WM_DELETE_WINDOW", self.delete_window)
        self.pack()
        self.create_widgets()

    def delete_window(self) -> None:
        self.master.destroy()
        self.app_state.is_running = False

    def create_widgets(self) -> None:
        # 牽引力方向
        self.traction = tk.Label(self, text="", font=(None, 24), width="100", anchor=tk.W)
        self.traction.pack()
        self.update_traction()

        # キーボードプレス値
        self.key_value = tk.StringVar()
        self.key = tk.Label(self, textvariable=self.key_value, font=(None, 48), width="100")
        self.key.pack(pady=50)
        self.key.bind("<KeyPress>", self.input_key)
        self.key.focus_set()

    def update_traction(self) -> None:
        self.traction.configure(text=f"牽引力方向: {self.sig_param.traction_direction:>4}")
        self.traction.after(500, self.update_traction)

    def input_key(self, event: tk.Event) -> None:
        """キーボードイベント処理"""
        print(event, event.keysym_num)
        key_name = event.keysym
        self.key_value.set(key_name)

        if event.keysym_num == 32:  # key: space
            self.player_param.change_play_state()

        elif event.keysym_num == 65361:  # key: Left
            self.sig_param.traction_up()
        elif event.keysym_num == 65363:  # key: Right
            self.sig_param.traction_down()

    def check_close(self) -> None:
        """アプリの終了監視"""
        if not self.app_state.is_running:
            self.master.destroy()
        self.after(1000, self.check_close)


def show_gui(app_state: AppState, player_param: PlayerState, sig_param: SignalParam) -> None:
    """アプリGUI画面を表示する

    :param app_state: _description_
    :param player_param: _description_
    :param sig_param: _description_
    """
    root = tk.Tk()
    app = Application(root, app_state, sig_param, player_param)
    app.mainloop()
