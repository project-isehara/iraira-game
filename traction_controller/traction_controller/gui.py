from __future__ import annotations

import tkinter as tk

from traction_controller.player import SignalParam
from traction_controller.state import AppState


class Application(tk.Frame):
    def __init__(self, master, sig_param: SignalParam):
        super().__init__(master)
        self.master = master
        self.pack()

        self.sig_param = sig_param
        self.create_widgets()

    def create_widgets(self):
        self.traction = tk.Label(self, text="")
        self.traction.pack()
        self.update()

    def update(self):
        self.traction.configure(text=str(self.sig_param.traction_direction))
        self.traction.after(500, self.update)


def show_gui(app_state: AppState, sig_param: SignalParam):
    root = tk.Tk()
    app = Application(master=root, sig_param=sig_param)
    app.mainloop()
