import sys
import tkinter as tk
import numpy as np
import pyaudio

#参考サイト:http://www.isc.meiji.ac.jp/~ri03037/ICTappli2/step04.html

# メイン関数
def main():
    root = tk.Tk()
    root.option_add('*font', 'ＭＳゴシック 16')
    root.title("任意音再生Ver0.1")
    ww = WidgetsWindow(root)
    root.mainloop()

# 「ウィジェットを並べたウィンドウ」クラス
class WidgetsWindow():
    # 作成
    def __init__(self, root):
        self.tf = tk.Frame(root)    # トップレベルのフレーム
        self.tf.grid(column = 0, row = 0, padx = 15, pady = 15)

        # ボタン
        self.b1 = tk.Button(self.tf, text = '正弦波')
        self.b2 = tk.Button(self.tf, text = '牽引錯覚波(未実装)')
        self.b1.grid(column = 0, row = 1, sticky = 'w')
        self.b2.grid(column = 1, row = 1, sticky = 'w')
        self.b1.bind("<Button-1>", self.sinPlayer)
        self.b2.bind("<Button-1>")

        # 音量スケール
        self.volVar = tk.DoubleVar()        # コントロール変数
        self.volVar.set(0.5)
        self.sc = tk.Scale(self.tf, label = '音量', orient = 'h', from_ = 0.1, to = 1, resolution = 0.1, variable = self.volVar)
        self.sc.grid(column = 0, columnspan = 2, row = 3, sticky = ('e' + 'w'))

        # 周波数スケール
        self.freqVar = tk.DoubleVar()        # コントロール変数
        self.freqVar.set(200)
        self.sc = tk.Scale(self.tf, label = '周波数', orient = 'h', from_ = 100, to = 1000, resolution = 10, variable = self.freqVar)
        self.sc.grid(column = 0, columnspan = 2, row = 4, sticky = ('e' + 'w'))

        # ラベル
        self.label = tk.Label(self.tf, text = '持続時間')
        self.label.grid(column = 0, row = 5, sticky = 'w')

        # # 持続時間スピンボックス
        self.sbVar = tk.IntVar()        # コントロール変数
        self.sbVar.set(1)
        self.sb = tk.Spinbox(self.tf, textvariable = self.sbVar, from_ = 1, to = 10, increment=1, width = 5)
        self.sb.grid(column = 1, row = 5)




    def sinPlayer(self,t):#音声プレーヤー。pyaudioの読み込みにちょっと時間かかる。あらかじめ読み込んでおきたいけどやり方が分からん。
        p = pyaudio.PyAudio()
        volume = 0.5  # range [0.0, 1.0]
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

        stream.stop_stream()
        stream.close()

if __name__ == '__main__':
    main()