import sys
import time

import RPi.GPIO as GPIO

from iraira.state import AppState, GameState

GPIO_1ST_STAGE = 21
GPIO_START_POINT = 26
GPIO_CHECK_POINT = 19
GPIO_GOAL_POINT = 13
GPIO_2ND_STAGE = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_1ST_STAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_CHECK_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_2ND_STAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_GOAL_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

POLLING_INTERVAL = 0.02  # sec
INVINCIBLE_INTERVAL = 0.2  # sec


def touch_listener(
    app_state: AppState,
    game_state: GameState,
) -> None:
    try:
        last_touched_time: float = 0.0
        is_touching: bool = False
        elapsed_time: float = 0.0

        while app_state.is_running:
            if GPIO.input(GPIO_1ST_STAGE) == 0 or GPIO.input(GPIO_2ND_STAGE) == 0:
                elapsed_time = time.time() - last_touched_time

                if not is_touching:
                    last_touched_time = time.time()
                    is_touching = True
                else:
                    game_state.add_touch_time(POLLING_INTERVAL)

                if elapsed_time > INVINCIBLE_INTERVAL:
                    game_state.increment_touch_count()
                    last_touched_time = time.time()
            else:
                is_touching = False

            if GPIO.input(GPIO_GOAL_POINT) == 0:
                game_state.is_goaled = True
            else:
                game_state.is_goaled = False
            time.sleep(POLLING_INTERVAL)

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)
