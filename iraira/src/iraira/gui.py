from __future__ import annotations

import csv
import sys
import time
import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from iraira.player import SignalParam
from iraira.state import AppState, GameState, GuiState, Page, PlayerState, TractionDirection
from iraira.util import RepoPath

_result_path = RepoPath().db_dir / "result.csv"


@dataclass(frozen=True)
class Result:
    id: int
    name: str
    start_datetime: datetime
    time_sec: float
    touch_count: int
    touch_time_sec: float

    @property
    def start_datetime_iso(self) -> str:
        return self.start_datetime.isoformat()

    @property
    def score(self) -> float:
        """スコアの算出"""
        s = (200 - self.time_sec) - (self.touch_count * 5)
        return 0 if s < 0 else s


def score(time: float, touch_count: int) -> float:
    """スコアの算出"""
    s = (200 - time) - (touch_count * 5)
    return 0 if s < 0 else s


def read_results(count: int) -> list[Result]:
    with _result_path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        _ = next(reader)

        results_iter = (
            Result(
                id=int(row[0]),
                name=row[1],
                start_datetime=datetime.fromisoformat(row[2]),
                time_sec=float(row[3]),
                touch_count=int(row[4]),
                touch_time_sec=float(row[5]),
            )
            for row in reader
        )
        return sorted(results_iter, key=lambda r: r.score, reverse=True)[:count]


class App(tk.Tk):
    """GUI表示

    画面遷移
    [ゲームタイトル画面] (スタート、設定、スコアハイライト)
    → [ゲーム中] (プレイ中のフィードバック表示)
    → [成功画面] or [失敗画面]
    → [ゲームタイトル画面]に戻る

    常時入力対応キーボードコマンド
    * q: アプリを終了する

    ゲーム中コマンドキーボードコマンド
    * [space]: 牽引力振動の再生/停止
    * 左矢印[←]: 牽引力振動の方向を左にする
    * 右矢印[→]: 牽引力振動の方向を右にする
    """

    def __init__(
        self,
        app_state: AppState,
        sig_param: SignalParam,
        player_param: PlayerState,
        game_state: GameState,
        gui_state: GuiState,
    ) -> None:
        tk.Tk.__init__(self)

        self._app_state = app_state
        self._sig_param = sig_param
        self._player_param = player_param
        self._game_state = game_state
        self._gui_state = gui_state

        # 画面設定
        self.title("")
        self.geometry("1024x768")
        # ウィンドウのグリッドを 1x1 にする この処理をコメントアウトすると配置がズレる
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 終了処理
        self.protocol("WM_DELETE_WINDOW", self._on_close_botton_click)
        self._check_close()

        # キーボード操作
        self.bind("<KeyPress>", self._input_key)
        self.focus_set()
        self._key_event: tk.Event

        # 画面ページ
        self._create_page()
        self._check_game_goal()

        self._previus_page = None
        self._check_current_page()
        self._gui_state.current_page = Page.TITLE

    def _create_page(self) -> None:
        """ページGUIの構築"""

        self._page_title = TitlePage(self, self._gui_state)
        self._page_game = GamePage(
            self, self._app_state, self._sig_param, self._player_param, self._game_state, self._gui_state
        )
        self._page_result = ResultPage(
            self, self._app_state, self._sig_param, self._player_param, self._game_state, self._gui_state
        )

    def _check_close(self) -> None:
        """アプリの起動状態監視と終了処理"""
        if self._app_state.is_running:
            self.after(500, self._check_close)
            return

        self.destroy()

    def _on_close_botton_click(self) -> None:
        """ウィンドウの閉じる[x]ボタンを押したときの処理"""
        self.destroy()
        self._app_state.is_running = False

    def _check_game_goal(self) -> None:
        """ゲーム画面でゴール時の画面遷移処理"""
        if self._gui_state.current_page == Page.GAME and self._game_state.is_goaled:
            self._gui_state.current_page = Page.RESULT
            self._game_state.is_goaled = False

        self.after(1000, self._check_game_goal)

    def _check_current_page(self) -> None:
        """現在の表示すべきページの表示"""
        current_page = self._gui_state.current_page

        if current_page != self._previus_page:
            self.change_page(current_page)
            self._previus_page = current_page

        self.after(200, self._check_current_page)

    def _input_key(self, event: tk.Event) -> None:
        """キーボードイベント処理"""
        self._key_event = event
        print(event, event.keysym_num)

        # アプリイベント
        if event.keysym_num == 113:  # key: q
            self._app_state.is_running = False

        # 画面ごとのイベント
        if self._gui_state.current_page == Page.TITLE:
            if event.keysym_num == 65293:  # key: Return
                self._gui_state.current_page = Page.GAME
                self._game_state.clear_game_state()

        elif self._gui_state.current_page == Page.GAME:
            # 画面遷移
            if event.keysym_num == 65293:  # key: Return
                self._gui_state.current_page = Page.RESULT

            # 操作
            elif event.keysym_num == 32:  # key: space
                self._player_param.change_play_state()

            elif event.keysym_num == 65361:  # key: Left
                self._sig_param.traction_down()

            elif event.keysym_num == 65363:  # key: Right
                self._sig_param.traction_up()

            elif event.keysym_num == 65362:  # key: Up
                self._player_param.volume_up()

            elif event.keysym_num == 65364:  # key: Down
                self._player_param.volume_down()

            # デバッグ用: ゲームゴール
            elif event.keysym_num == 103:  # key: g
                self._game_state.is_goaled = True

            # デバッグ用: ゲーム途中終了
            elif event.keysym_num == 119:  # key: w
                self._gui_state.current_page = Page.TITLE

            # デバッグ用: ゲーム途中終了
            elif event.keysym_num == 114:  # key: r
                self._game_state.increment_touch_count()

        elif self._gui_state.current_page == Page.RESULT:
            if event.keysym_num == 65293:  # key: Return
                self._gui_state.current_page = Page.TITLE

    def change_page(self, page: Page) -> None:
        if page == Page.TITLE:
            self._page_title.update_ranking()
            self._page_title.tkraise()
            self._player_param.play_state = False

        elif page == Page.GAME:
            self._page_game.tkraise()
            self._player_param.play_state = True
            self._game_state.start_time = time.time()

        elif page == Page.RESULT:
            self._page_result.update_app_status()
            self._page_result.tkraise()
            self._player_param.play_state = True


class TitlePage(tk.Frame):
    """ゲームタイトル画面"""

    def __init__(
        self,
        master: tk.Misc,
        gui_state: GuiState,
    ) -> None:
        super().__init__(master)
        self._gui_state = gui_state
        self._create_title_page()

    def _create_title_page(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")

        self._create_background_image().place(relx=0, rely=0)
        self._create_title_label().pack(anchor=tk.CENTER, pady=20)
        self._create_start_button().pack(anchor=tk.CENTER, pady=10)
        self._ranking = tk.Frame(self)

    def _create_background_image(self) -> tk.Canvas:
        img_path = RepoPath().assert_dir / "DALL·E 2022-08-29 02.10.00 - maze_trim4x3.png"
        self._background = tk.PhotoImage(file=str(img_path))  # 変数保持しないと表示されない
        bg = tk.Canvas(self, width=1024, height=768)
        bg.create_image(0, 0, anchor=tk.NW, image=self._background)
        return bg

    def _create_title_label(self) -> tk.Label:
        return tk.Label(self, text="妨害イライラ棒", font=(None, "70"))

    def _create_start_button(self) -> tk.Button:
        def go_to_game_page() -> None:
            self._gui_state.current_page = Page.GAME

        return tk.Button(
            self,
            text="START",
            font=(None, "60"),
            command=lambda: go_to_game_page(),
        )

    def _create_ranking(self, results: Sequence[Result]) -> tk.Frame:
        f = tk.Frame(self)
        tk.Label(f, text="").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        tk.Label(f, text="NAME", font=(None, "20")).grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)
        tk.Label(f, text="TIME [s]", font=(None, "20")).grid(column=2, row=0, sticky=tk.W, padx=5, pady=5)
        tk.Label(f, text="TOUCH", font=(None, "20")).grid(column=3, row=0, sticky=tk.W, padx=5, pady=5)
        tk.Label(f, text="SCORE", font=(None, "20")).grid(column=4, row=0, sticky=tk.W, padx=5, pady=5)

        for i, r in enumerate(results):
            tk.Label(f, text=f"{i+1}", font=(None, "20")).grid(column=0, row=i + 1, sticky=tk.W, padx=5, pady=5)
            tk.Label(f, text=f"{r.name}", font=(None, "20")).grid(column=1, row=i + 1, sticky=tk.W, padx=5, pady=5)
            tk.Label(f, text=f"{r.time_sec}", font=(None, "20")).grid(column=2, row=i + 1, sticky=tk.W, padx=5, pady=5)
            tk.Label(f, text=f"{r.touch_count}", font=(None, "20")).grid(
                column=3, row=i + 1, sticky=tk.W, padx=5, pady=5
            )
            tk.Label(f, text=f"{r.score}", font=(None, "20")).grid(column=4, row=i + 1, sticky=tk.W, padx=5, pady=5)

        return f

    def update_ranking(self) -> None:
        if isinstance(self._ranking, tk.Frame):
            self._ranking.destroy()

        results = read_results(5)
        self._ranking = self._create_ranking(results)
        self._ranking.pack(anchor=tk.CENTER, pady=20)


class GamePage(tk.Frame):
    """ゲーム中画面"""

    def __init__(
        self,
        master: tk.Misc,
        app_state: AppState,
        sig_param: SignalParam,
        player_param: PlayerState,
        game_state: GameState,
        gui_state: GuiState,
    ) -> None:
        super().__init__(master)

        self._app_state = app_state
        self._sig_param = sig_param
        self._player_param = player_param
        self._game_state = game_state
        self._gui_state = gui_state

        self._create_game_page()

    def _create_game_page(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")

        self._create_title_label().pack(anchor=tk.CENTER, pady=20)
        self._create_traction_status().pack(anchor=tk.N, pady=30, fill=tk.X)

        app_status = self._create_app_status_label()
        app_status.pack(anchor=tk.CENTER, pady=30)
        self.update_app_status()

    def _create_title_label(self) -> tk.Label:
        return tk.Label(self, text="妨害イライラ棒", font=(None, "70"))

    def _create_traction_status(self) -> tk.Frame:
        f = tk.Frame(self, height=200)
        t = tk.Label(f, text="ぼうがいレベル", font=(None, 40))
        t.grid(column=0, row=0, sticky=tk.W + tk.E + tk.N + tk.S, columnspan=2, padx=5)

        text = "-" * 21
        self._ing = tk.Label(f, text=text, font=(None, 60))
        self._ing.grid(column=0, row=1, sticky=tk.W + tk.E + tk.N + tk.S, columnspan=2, padx=5)

        # self._left = tk.Label(f, text="⬅", font=(None, 200), fg="DodgerBlue1")
        # self._left.grid(column=0, row=2, sticky=tk.W + tk.E + tk.N + tk.S, padx=5)

        # self._right = tk.Label(f, text="➡", font=(None, 200), fg="OrangeRed")
        # self._right.grid(column=1, row=2, sticky=tk.W + tk.E + tk.N + tk.S, padx=5)

        f.grid_columnconfigure(0, weight=1)
        # f.grid_columnconfigure(1, weight=1)
        # f.grid_columnconfigure(2, weight=2)
        return f

    def _create_app_status_label(self) -> tk.Frame:
        f = tk.Frame(self)

        self._time = tk.Label(f, text="TIME", font=(None, 60))
        self._time.grid(column=0, row=0, sticky=tk.W + tk.E, padx=5, pady=5)

        t = tk.Label(f, text="壁接触: ", font=(None, 50))
        t.grid(column=0, row=1, sticky=tk.W + tk.E, padx=5, pady=5)

        self._touch_count = tk.Label(f, text="n", font=(None, 60))
        self._touch_count.grid(column=1, row=1, sticky=tk.W + tk.E, padx=5, pady=5)

        return f

    def update_app_status(self) -> None:
        """アプリ情報を定期更新する"""

        # 牽引力方向
        t = list("-" * 21)
        t[10] = "0"
        v = int(self._player_param.volume * 10)
        if self._sig_param.traction_direction == TractionDirection.up:
            t[10 + v] = "★"
        else:
            t[10 - v] = "★"
        self._ing.configure(text=f"←{''.join(t)}→")

        # 経過時間
        t = time.time() - self._game_state.start_time
        self._time.configure(text=f"{t:.1f}")

        # 接触回数
        self._touch_count.configure(text=self._game_state.touch_count)

        self.after(100, lambda: self.update_app_status())


class ResultPage(tk.Frame):
    """ゲーム結果画面"""

    def __init__(
        self,
        master: tk.Misc,
        app_state: AppState,
        sig_param: SignalParam,
        player_param: PlayerState,
        game_state: GameState,
        gui_state: GuiState,
    ) -> None:
        super().__init__(master)

        self._app_state = app_state
        self._sig_param = sig_param
        self._player_param = player_param
        self._game_state = game_state
        self._gui_state = gui_state

        self._create_result_page()

    def _create_result_page(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")

        self._create_title_label().pack(anchor=tk.CENTER, pady=20)
        self._create_goal_label().pack(anchor=tk.CENTER, pady=10)
        self._create_result_label().pack(anchor=tk.CENTER, pady=10)

    def _create_title_label(self) -> tk.Label:
        return tk.Label(self, text="妨害イライラ棒", font=(None, "70"))

    def _create_goal_label(self) -> tk.Label:
        return tk.Label(self, text="RESULT", font=(None, 60))

    def _create_result_label(self) -> tk.Frame:
        f = tk.Frame(self)

        self._time = tk.Label(f, text="クリア時間: ", font=(None, 60))
        self._time.grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)

        self._time = tk.Label(f, text="          ", font=(None, 60))
        self._time.grid(column=1, row=0, sticky=tk.W + tk.E, padx=5, pady=5)

        t = tk.Label(f, text="壁接触回数: ", font=(None, 50))
        t.grid(column=0, row=1, sticky=tk.E, padx=5, pady=5)

        self._touch_count = tk.Label(f, text=0, font=(None, 60))
        self._touch_count.grid(column=1, row=1, sticky=tk.W + tk.E, padx=5, pady=5)

        t = tk.Label(f, text="☆スコア☆: ", font=(None, 60))
        t.grid(column=0, row=2, sticky=tk.E, padx=5, pady=5)

        self._score = tk.Label(f, text=0, font=(None, 100))
        self._score.grid(column=1, row=2, sticky=tk.W + tk.E, padx=5, pady=5)

        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=2)
        return f

    def update_app_status(self) -> None:
        """アプリ情報を定期更新する"""

        # 経過時間
        t = time.time() - self._game_state.start_time
        self._time.configure(text=f"{t:.1f} 秒")

        # 接触回数
        self._touch_count.configure(text=self._game_state.touch_count)

        # スコア
        s = int(score(t, self._game_state.touch_count))
        self._score.configure(text=s)


def show_gui(
    app_state: AppState,
    player_param: PlayerState,
    sig_param: SignalParam,
    game_state: GameState,
    gui_state: GuiState,
) -> None:
    """アプリGUI画面を表示する"""
    try:
        app = App(app_state, sig_param, player_param, game_state, gui_state)
        app.mainloop()

    except KeyboardInterrupt:
        app.destroy()

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)
