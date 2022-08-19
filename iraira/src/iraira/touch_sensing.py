# pyright: reportGeneralTypeIssues=false
import RPi.GPIO as GPIO

from iraira.state import GameState
import time

GPIO_1ST_STAGE = 26
GPIO_CHECK_POINT =19 
GPIO_GOAL_POINT = 13
GPIO_2ND_STAGE = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_1ST_STAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_CHECK_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_2ND_STAGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_GOAL_POINT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

POLLING_INTERVAL = 0.02 #sec
INVINCIBLE_INTERVAL = 0.2 #sec

def touch_listener(
    game_state: GameState,
) -> None:
    lastTouchedTime:float = 0.0
    isTouching:bool = False
    elapsedTime:float = 0.0
    while True:
        if GPIO.input(GPIO_1ST_STAGE) == 0 or GPIO.input(GPIO_2ND_STAGE) == 0:
            elapsedTime = time.time() - lastTouchedTime
            if not isTouching:
                lastTouchedTime = time.time()
                isTouching = True
            else: #isTouching 
                game_state.add_touch_time(POLLING_INTERVAL)

            if elapsedTime > INVINCIBLE_INTERVAL:
                game_state.increment_touch_count()
                lastTouchedTime = time.time()
        else:
            isTouching = False

        if GPIO.input(GPIO_GOAL_POINT) == 0:
            game_state.isGoaled=True
        else:
            game_state.isGoaled=False
        time.sleep(POLLING_INTERVAL)
