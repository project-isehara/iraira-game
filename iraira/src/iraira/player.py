from __future__ import annotations

import random
import sys
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pyaudio

from iraira.state import AppState, GameState, PlayerState, SignalParam, TractionDirection
from iraira.traction_wave import traction_wave
from iraira.util import RepoPath

_assert_path = RepoPath().assert_dir
_sound_touch_wall_1_path = _assert_path / "maouaudio/魔王魂  戦闘09.wav"
_sound_touch_wall_2_path = _assert_path / "効果音ラボ/大砲2.wav"
_sound_touch_wall_3_path = _assert_path / "効果音ラボ/爆発2.wav"
_sound_goal_path = _assert_path / "nakano sound/ファンファーレ6（戦闘勝利＋BGM）.wav"


def read_wav(file: Path) -> npt.NDArray[np.float32]:
    with wave.open(str(file), "rb") as fr:
        frame = fr.readframes(fr.getnframes())

    return np.frombuffer(frame, dtype=np.float32)


class GameSoundEffect:
    def __init__(self) -> None:
        self._sound_touch_walls = (
            read_wav(_sound_touch_wall_1_path),
            read_wav(_sound_touch_wall_2_path),
            read_wav(_sound_touch_wall_3_path),
        )
        self._sound_goal = read_wav(_sound_goal_path)

    def sound_touch_wall_random(self) -> npt.NDArray[np.float32]:
        return random.choice(self._sound_touch_walls)

    def sound_goal(self) -> npt.NDArray[np.float32]:
        return self._sound_goal


class Player:
    """音声プレーヤーの制御"""

    def __init__(self, param: PlayerState):
        self._py_audio = pyaudio.PyAudio()
        self._stream = self._py_audio.open(format=pyaudio.paFloat32, channels=1, rate=param.fs, output=True)
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

    def write(self, sig: npt.NDArray[np.float32]) -> None:
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
) -> npt.NDArray[np.float32]:
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
    sig = traction_wave(2 * np.pi * frequency * t, count_anti_node).astype(np.float32)

    # 牽引力方向の調整
    if traction_direction == TractionDirection.down:
        sig = -sig

    return sig


def play(app_state: AppState, player_param: PlayerState, sig_param: SignalParam, game_state: GameState) -> None:
    """音声出力

    :param app_state: アプリ状態
    :param player_param: プレイヤー状態
    :param sig_param: 信号状態
    :param game_param: ゲーム状態
    """

    try:
        touch_count = 0
        game_sound = GameSoundEffect()

        with Player(player_param) as player:
            player.start()

            while app_state.is_running:
                if not player_param.play_state:
                    player.stop()
                    continue
                else:
                    player.start()

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
                    sig = traction_wave * player_param.volume

                touch_count = game_state.touch_count
                player.write(sig)

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)
