from __future__ import annotations

import sys
import tkinter as tk

from iraira.player import SignalParam
from iraira.state import AppState, GameState, GuiState, Page, PlayerState
from iraira.util import RepoPath


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

        # 画面設定
        self.title("")
        self.geometry("800x600")
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
        self._gui_state = gui_state
        self._create_page()
        self._check_game_goal()

        self._previus_page = None
        self._check_current_page()
        self._gui_state.current_page = Page.TITLE

    def _create_page(self) -> None:
        """ページGUIの構築"""

        self._page_title = self._create_page_title()
        self._page_game = self._create_page_game()
        self._page_result = self._create_page_result()

    def _create_page_title(self) -> tk.Frame:
        page_title = tk.Frame()
        page_title.grid(row=0, column=0, sticky="nsew")

        def background_image() -> tk.Canvas:
            img_path = RepoPath().assert_dir / "DALL·E 2022-08-29 02.10.00 - maze_trim4x3.png"
            self._background = tk.PhotoImage(file=str(img_path))  # 変数保持しないと表示されない
            bg = tk.Canvas(page_title, width=1024, height=768)
            bg.create_image(0, 0, anchor=tk.NW, image=self._background)
            return bg

        def title_label() -> tk.Label:
            return tk.Label(page_title, text="妨害イライラ棒", font=(None, "80"))

        def start_button() -> tk.Button:
            def go_to_game_page() -> None:
                self._gui_state.current_page = Page.GAME

            return tk.Button(
                page_title,
                text="START",
                font=(None, "60"),
                command=lambda: go_to_game_page(),
            )

        def start_key_label() -> tk.Label:
            return tk.Label(page_title, text="[ENTER]", font=(None, "20"))

        def ranking_label() -> tk.Label:
            return tk.Label(
                page_title,
                text="(本日の結果ランキング的な)\n----------------\n1. ABC\n2. DDD\n----------------",
                font=(None, "20"),
            )

        background_image().place(relx=0, rely=0)
        title_label().pack(anchor=tk.CENTER, pady=30)
        start_button().pack(anchor=tk.CENTER, pady=20)
        start_key_label().pack(anchor=tk.CENTER)
        ranking_label().pack(anchor=tk.CENTER, pady=20)
        return page_title

    def _create_page_game(self) -> tk.Frame:
        page_game = tk.Frame()
        page_game.grid(row=0, column=0, sticky="nsew")

        def title_label() -> tk.Label:
            return tk.Label(page_game, text="妨害イライラ棒", font=(None, "80"))

        def game_status_label() -> tk.Label:
            return tk.Label(
                page_game,
                text="妨害イライラ棒情報？\nライフポイント [#####      ]: \n接触時間: n [sec]\n接触回数: n [回]",
                font=(None, 24),
                justify=tk.LEFT,
            )

        def app_status_label() -> tk.Label:
            return tk.Label(
                page_game,
                font=(None, 24),
                # width="100",
                justify=tk.LEFT,
            )

        def update_app_status(app_status: tk.Label) -> None:
            """アプリ情報を定期更新する"""
            app_status.configure(
                text=(
                    f"volume  : {self._player_param.volume:.1f}\n"
                    f"traction: {self._sig_param.traction_direction:>4}\n"
                    f"play    : {'playing' if self._player_param.play_state else 'stop':>7}\n"
                    f"touch_count: {self._game_state.touch_count:>3}\n"
                    f"touch_time: {self._game_state.touch_time:.2f}\n"
                    f"isGoaled: {self._game_state.is_goaled}"
                )
            )

            self.after(200, lambda: update_app_status(app_status))

        title_label().pack(anchor=tk.CENTER, pady=30)
        game_status_label().pack(anchor=tk.CENTER, pady=10)
        tk.Label(page_game, text="-" * 30).pack()
        app_status = app_status_label()
        app_status.pack(anchor=tk.CENTER, pady=10)
        update_app_status(app_status)

        # フレーム1からmainフレームに戻るボタン
        def go_to_title_page() -> None:
            self._gui_state.current_page = Page.TITLE

        back_button = tk.Button(page_game, text="Back", command=lambda: go_to_title_page())
        back_button.pack()

        return page_game

    def _create_page_result(self) -> tk.Frame:
        page = tk.Frame()
        page.grid(row=0, column=0, sticky="nsew")

        def title_label() -> tk.Label:
            return tk.Label(page, text="妨害イライラ棒", font=(None, "80"))

        def goal_label() -> tk.Label:
            return tk.Label(page, text="ゴール !!", font=(None, 48))

        def result_label() -> tk.Label:
            return tk.Label(page, text="クリア (or 失敗)", font=(None, 30))

        title_label().pack(anchor=tk.CENTER, pady=30)
        goal_label().pack(anchor=tk.CENTER, pady=10)
        result_label().pack(anchor=tk.CENTER, pady=10)
        return page

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
            self._previus_page = current_page
            self.change_page(current_page)

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
                self._sig_param.traction_up()

            elif event.keysym_num == 65363:  # key: Right
                self._sig_param.traction_down()

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

        elif self._gui_state.current_page == Page.RESULT:
            if event.keysym_num == 65293:  # key: Return
                self._gui_state.current_page = Page.TITLE

    def change_page(self, page: Page) -> None:
        if page == Page.TITLE:
            self._page_title.tkraise()

        elif page == Page.GAME:
            self._page_game.tkraise()
            self._player_param.play_state = True

        elif page == Page.RESULT:
            self._page_result.tkraise()
            self._player_param.play_state = False


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
