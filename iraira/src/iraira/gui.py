from __future__ import annotations

import os
import sys

import PySide6
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

from iraira.player import SignalParam
from iraira.state import AppState


class MyWidget(QtWidgets.QWidget):
    def __init__(self, sig_param: SignalParam):
        super().__init__()

        self.setWindowTitle("イライラ棒")
        self.setFont(QFont())

        self.sig_param = sig_param

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel(text=f"牽引力方向: {sig_param.traction_direction:>4}", alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

        # 定期実行
        self.timer = QTimer()
        self.timer.timeout.connect(self.change_traction)
        self.timer.start(500)

    @QtCore.Slot()
    def magic(self):
        self.sig_param.traction_change()

    def change_traction(self):
        self.text.setText(f"牽引力方向: {self.sig_param.traction_direction:>4}")


def show_gui(app_state: AppState, sig_param: SignalParam):
    app = QtWidgets.QApplication()

    widget = MyWidget(sig_param)
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
