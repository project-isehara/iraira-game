import math
import sys
import tkinter as tk

import matplotlib.pyplot as plt
import numpy as np
import pyaudio

# 参考サイト:http://www.isc.meiji.ac.jp/~ri03037/ICTappli2/step04.html

# メイン関数
def main():
    root = tk.Tk()
    root.option_add("*font", "ＭＳゴシック 16")
    root.title("任意音再生Ver0.2")
    ww = WidgetsWindow(root)
    root.mainloop()


# 「ウィジェットを並べたウィンドウ」クラス
class WidgetsWindow:
    # 作成
    def __init__(self, root):
        self.tf = tk.Frame(root)  # トップレベルのフレーム
        self.tf.grid(column=0, row=0, padx=15, pady=15)

        # ボタン
        self.b1 = tk.Button(self.tf, text="正弦波")
        self.b2 = tk.Button(self.tf, text="牽引錯覚波(正方向)")
        self.b3 = tk.Button(self.tf, text="牽引錯覚波(逆方向)")
        self.b1.grid(column=0, row=1, sticky="w")
        self.b2.grid(column=1, row=1, sticky="w")
        self.b3.grid(column=2, row=1, sticky="w")
        self.b1.bind("<Button-1>", self.sinPlayer)
        self.b2.bind("<Button-1>", self.tracPlayer)
        self.b3.bind("<Button-1>", self.invtracPlayer)

        # 音量スケール
        self.volVar = tk.DoubleVar()  # コントロール変数
        self.volVar.set(0.5)
        self.sc = tk.Scale(self.tf, label="音量", orient="h", from_=0.1, to=1, resolution=0.1, variable=self.volVar)
        self.sc.grid(column=0, columnspan=3, row=3, sticky=("e" + "w"))

        # 周波数スケール
        self.freqVar = tk.DoubleVar()  # コントロール変数
        self.freqVar.set(200)
        self.sc = tk.Scale(self.tf, label="周波数", orient="h", from_=10, to=1000, resolution=10, variable=self.freqVar)
        self.sc.grid(column=0, columnspan=3, row=4, sticky=("e" + "w"))

        # ラベル
        self.label = tk.Label(self.tf, text="持続時間")
        self.label.grid(column=0, row=5, sticky="w")

        # # 持続時間スピンボックス
        self.sbVar = tk.DoubleVar()  # コントロールF変数
        self.sbVar.set(1)
        self.sb = tk.Spinbox(self.tf, textvariable=self.sbVar, from_=1, to=10, increment=0.1, width=5)
        self.sb.grid(column=1, row=5)

    def sinPlayer(self, t):  # 音声プレーヤー。pyaudioの読み込みにちょっと時間かかる。あらかじめ読み込んでおきたいけどやり方が分からん。
        p = pyaudio.PyAudio()
        # volume = 0.5  # range [0.0, 1.0]
        fs = 44100  # sampling rate, Hz, must be integer
        # duration = 15.0  # in seconds, may be float
        # f = 15000.0  # sine frequency, Hz, may be float
        volume = self.volVar.get()
        f = self.freqVar.get()
        duration = self.sbVar.get()
        print(str(volume))
        print(str(f))
        print(str(duration))
        # generate samples, note conversion to float32 array
        sinAudio = (np.sin(2 * np.pi * np.arange(fs * duration) * f / fs)).astype(np.float32)

        # for paFloat32 sample values must be in range [-1.0, 1.0]
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

        # play. May repeat with different volume values (if done interactively)
        stream.write((volume * sinAudio).tostring())

        # plt.plot(sinAudio)
        # plt.show()

        stream.stop_stream()
        stream.close()

    def tracPlayer(self, t):
        p = pyaudio.PyAudio()
        fs = 44100
        volume = self.volVar.get()
        f = self.freqVar.get()
        duration = self.sbVar.get()
        unitNum = 2  # ユニット数
        period = unitNum / f
        start = 3 / 4  # 波形を反転させる開始位置(1周期の中で)
        end = 1  # 波形を反転させる終了位置(1周期の中で)
        unitNum = int(duration * f)  # 持続時間中に波形が何個入るか
        t = np.linspace(0, duration, int(fs * duration))
        tracAudio = np.abs(np.sin(2 * math.pi * f * t)).astype(np.float32)
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

        # 範囲(start~end)に相当するデータを反転させる
        for i in range(int(duration / period)):  # 1周期ごとにstart~endの範囲の波形を反転させる
            Indx = np.where((t > start * period + i * period) & (t < end * period + i * period))
            tracAudio[Indx] = -tracAudio[Indx]

        # plt.plot(tracAudio)
        # plt.show()

        # play. May repeat with different volume values (if done interactively)
        stream.write((volume * tracAudio).tostring())  # 波形データに音量を反映させて文字列に変換して再生(文字列変換はモジュールの仕様)

    def invtracPlayer(self, t):
        p = pyaudio.PyAudio()
        fs = 44100
        volume = self.volVar.get()
        f = self.freqVar.get()
        duration = self.sbVar.get()
        unitNum = 2  # ユニット数
        period = unitNum / f
        start = 3 / 4  # 波形を反転させる開始位置(1周期の中で)
        end = 1  # 波形を反転させる終了位置(1周期の中で)
        unitNum = int(duration * f)  # 持続時間中に波形が何個入るか
        t = np.linspace(0, duration, int(fs * duration))
        tracAudio = np.abs(np.sin(2 * math.pi * f * t)).astype(np.float32)
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

        # 範囲(start~end)に相当するデータを反転させる
        for i in range(unitNum):  # 1周期ごとにstart~endの範囲の波形を反転させる
            Indx = np.where((t > i * period) & (t < start * period + i * period))
            tracAudio[Indx] = -tracAudio[Indx]

        # plt.plot(tracAudio)
        # plt.show()

        # play. May repeat with different volume values (if done interactively)
        stream.write((volume * tracAudio).tostring())  # 波形データに音量を反映させて文字列に変換して再生(文字列変換はモジュールの仕様)


if __name__ == "__main__":
    main()
