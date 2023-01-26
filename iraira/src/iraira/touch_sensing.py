import sys
import time

import RPi.GPIO as GPIO

from iraira.state import AppState, GameState, GuiState, Page

GPIO_1ST_STAGE = 21
GPIO_START_POINT = 26
GPIO_CHECK_POINT = 19
GPIO_GOAL_POINT = 13
GPIO_2ND_STAGE = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_START_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_1ST_STAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_CHECK_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_2ND_STAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_GOAL_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

POLLING_INTERVAL = 0.005  # sec
INVINCIBLE_INTERVAL = 0.5  # sec

GOAL_DETECTION_DURATION = 0.3  # sec
START_DETECTION_DURATION = 1.0  # sec


def touch_listener(app_state: AppState, game_state: GameState, gui_state: GuiState) -> None:
    try:
        course_last_touched_time: float = 0.0
        course_is_touching: bool = False
        course_elapsed_time: float = 0.0

        goal_touching_time: float = 0.0
        start_touching_time: float = 0.0

        while app_state.is_running:
            time.sleep(POLLING_INTERVAL)

            if gui_state.current_page != Page.GAME:
                goal_touching_time = 0.0
                start_touching_time = 0.0
                continue

            # コース上の接触判定
            if GPIO.input(GPIO_1ST_STAGE) == 0 or GPIO.input(GPIO_2ND_STAGE) == 0:
                course_elapsed_time = time.time() - course_last_touched_time

                # 接触時間のカウント
                if not course_is_touching:
                    course_last_touched_time = time.time()
                    course_is_touching = True
                else:
                    game_state.add_touch_time(POLLING_INTERVAL)

                # 無敵時間判定
                if course_elapsed_time > INVINCIBLE_INTERVAL:
                    game_state.increment_touch_count()
                    course_last_touched_time = time.time()
            else:
                course_is_touching = False

            # ゴールの接触判定
            if GPIO.input(GPIO_GOAL_POINT) == 0:
                goal_touching_time += POLLING_INTERVAL
                if goal_touching_time >= GOAL_DETECTION_DURATION + POLLING_INTERVAL:
                    game_state.is_goaled = True
            else:
                goal_touching_time = 0

            # スタートの接触判定
            if GPIO.input(GPIO_START_POINT) == 0:
                start_touching_time += POLLING_INTERVAL
                if start_touching_time >= GOAL_DETECTION_DURATION + POLLING_INTERVAL:
                    game_state.clear_game_state()

            else:
                start_touching_time = 0

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)
