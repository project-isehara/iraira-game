from __future__ import annotations

import random
import sys
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pyaudio

from iraira.state import AppState, GameState, GuiState, Page, PlayerState, SignalParam, TractionDirection
from iraira.traction_wave import traction_wave
from iraira.util import RepoPath

_assert_path = RepoPath().assert_dir
_sound_touch_wall_1_path = _assert_path / "効果音ラボ/大砲2.wav"  # 44.1 kHz
_sound_touch_wall_2_path = _assert_path / "効果音ラボ/爆発2.wav"  # 44.1 kHz
# _sound_touch_wall_2_path = _assert_path / "maouaudio/魔王魂  戦闘09.wav"  # 48.0 kHz
_sound_goal_path = _assert_path / "nakano sound/ファンファーレ6（戦闘勝利＋BGM）.wav"  # 44.1 kHz


def read_wav(file: Path) -> npt.NDArray[np.uint8 | np.int16]:
    with wave.open(str(file), "rb") as fr:
        channel = fr.getnchannels()
        sample_width = fr.getsampwidth()
        frame = fr.readframes(fr.getnframes())

    if sample_width == 1:
        d_type = np.uint8
    elif sample_width == 2:
        d_type = np.int16
    else:
        raise NotImplementedError()

    w = np.frombuffer(frame, dtype=d_type)
    if channel == 2:
        return w[::2]
    return w


class GameSoundEffect:
    def __init__(self) -> None:
        self._sound_touch_walls = (
            # (read_wav(_sound_touch_wall_1_path)[:22050] * 2.1).astype(np.int16),  # 0.5 sec & 音量調整
            # (read_wav(_sound_touch_wall_2_path)[:22050] * 2.5).astype(np.int16),  # 0.5 sec & 音量調整
            (read_wav(_sound_touch_wall_1_path)[:22050] * 5).astype(np.int16),  # 0.5 sec & 音量調整
            (read_wav(_sound_touch_wall_2_path)[:22050] * 5).astype(np.int16),  # 0.5 sec & 音量調整
        )
        self._sound_goal = (read_wav(_sound_goal_path)[: int(44100 * 9.3)] * 1.8).astype(np.int16)  # 音源の使用する長さ & 音量調整

    def sound_touch_wall_random(self) -> npt.NDArray[np.int16]:
        return random.choice(self._sound_touch_walls)

    def sound_goal(self) -> npt.NDArray[np.int16]:
        return self._sound_goal


class Player:
    """音声プレーヤーの制御"""

    def __init__(self, param: PlayerState):
        self._py_audio = pyaudio.PyAudio()
        self._stream = self._py_audio.open(format=pyaudio.paInt16, channels=1, rate=param.fs, output=True)
        self.param = param

    def start(self) -> None:
        self._stream.start_stream()

    def stop(self) -> None:
        self._stream.stop_stream()

    def change_play_state(self) -> None:
        if self._stream.is_active():
            self.stop()
        else:
            self.start()

    def close(self) -> None:
        self._stream.close()
        self._py_audio.terminate()

    def write(self, sig: npt.NDArray[np.int16]) -> None:
        self._stream.write(sig.tobytes())

    def __enter__(self) -> Player:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self.close()


@lru_cache(maxsize=1)
def create_traction_wave(
    fs: int,
    frequency: int,
    traction_direction: TractionDirection,
    count_anti_node: int = 4,
) -> npt.NDArray[np.float_]:
    """牽引力信号を生成する

    :param fs: サンプリング周波数[Hz]
    :param frequency: 信号周波数[Hz]
    :param traction_direction: 牽引力方向
    :param count_anti_node: 1周期の腹の数, 3以上を指定する, defaults to 4
    :return: 牽引力信号
    """

    # 生成波形の長さが波形周波数の整数倍になるように調整
    duration_sec = 0.1
    duration_sec = round(duration_sec * frequency) / frequency

    # 波形生成
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
    sig = traction_wave(2 * np.pi * frequency * t, count_anti_node)

    # 牽引力方向の調整
    if traction_direction == TractionDirection.down:
        sig = -sig

    return sig


def play(
    app_state: AppState,
    player_param: PlayerState,
    sig_param: SignalParam,
    game_state: GameState,
    gui_state: GuiState,
) -> None:
    """音声出力

    :param app_state: アプリ状態
    :param player_param: プレイヤー状態
    :param sig_param: 信号状態
    :param game_param: ゲーム状態
    """
    try:
        touch_count = 0
        game_sound = GameSoundEffect()
        previus_page = None

        with Player(player_param) as player:
            player.start()

            while app_state.is_running:
                if not player_param.play_state:
                    player.stop()
                    previus_page = gui_state.current_page
                    continue
                else:
                    player.start()

                if gui_state.current_page == Page.RESULT and previus_page != Page.RESULT:
                    sig = game_sound.sound_goal()

                elif gui_state.current_page == Page.GAME:
                    if touch_count != game_state.touch_count:
                        touch_count = game_state.touch_count
                        sig = game_sound.sound_touch_wall_random()
                    else:
                        traction_wave = create_traction_wave(
                            player_param.fs,
                            sig_param.frequency,
                            sig_param.traction_direction,
                            sig_param.count_anti_node,
                        )
                        # 値域調整 16bit & 音量調整
                        sig = (traction_wave * 32767 * player_param.volume).astype(np.int16)

                else:
                    continue

                previus_page = gui_state.current_page
                player.write(sig)

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)
