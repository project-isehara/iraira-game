import sys
import time

import RPi.GPIO as GPIO

from iraira.state import AppState, GameState, GuiState, Page

GPIO_LED = 14

GPIO.setup(GPIO_LED, GPIO.OUT, initial=GPIO.HIGH)


def led_listener(
    app_state: AppState,
    game_state: GameState,
    gui_state: GuiState
) -> None:

    CRASHED_BLINKING_TIME = 0.5  # sec
    GOALED_BLINKING_TIME = 9.3  # sec
    CRASHED_ALTERNATIVE_DURATION = 0.1  # sec.ここで指定した間隔で点滅。壁の場合。
    GOALED_ALTERNATIVE_DURATION = 0.3  # sec.ここで指定した間隔で点滅。ゴールの場合。

    local_touch_count = 0
    blinking_until_time = 0
    alternation_until_time = 0
    blinking_alternative_duration = CRASHED_ALTERNATIVE_DURATION

    previous_page = 0

    try:
        while app_state.is_running:
            time.sleep(0.001)
            current_time = time.time()

            if gui_state.current_page == Page.TITLE:
                GPIO.output(GPIO_LED, GPIO.HIGH)
                continue

            # ゲームリセットの検出
            if local_touch_count > game_state.touch_count:
                local_touch_count = game_state.touch_count

            # 壁接触
            if local_touch_count < game_state.touch_count:
                local_touch_count += 1
                blinking_until_time = current_time + CRASHED_BLINKING_TIME
                blinking_alternative_duration = CRASHED_ALTERNATIVE_DURATION

            # ゴール接触
            if gui_state.current_page == Page.RESULT and previous_page != Page.RESULT:
                blinking_until_time = current_time + GOALED_BLINKING_TIME
                blinking_alternative_duration = GOALED_ALTERNATIVE_DURATION

            # 点滅処理
            if current_time > blinking_until_time:
                GPIO.output(GPIO_LED, GPIO.HIGH)
            elif current_time > alternation_until_time:
                alternation_until_time = current_time + blinking_alternative_duration
                alternate_output(GPIO_LED)

            previous_page = gui_state.current_page

            #     course_elapsed_time = time.time() - course_last_touched_time

            # if gui_state.current_page != Page.GAME:
            #     goal_touching_time = 0.0
            #     start_touching_time = 0.0
            #     continue

            # GPIO.output(GPIO_LED, 1)

            # # コース上の接触判定
            # if GPIO.input(GPIO_1ST_STAGE) == 0 or GPIO.input(GPIO_2ND_STAGE) == 0:
            #     course_elapsed_time = time.time() - course_last_touched_time

            #     # 接触時間のカウント
            #     if not course_is_touching:
            #         course_last_touched_time = time.time()
            #         course_is_touching = True
            #     else:
            #         game_state.add_touch_time(POLLING_INTERVAL)

            #     # 無敵時間判定
            #     if course_elapsed_time > INVINCIBLE_INTERVAL:
            #         game_state.increment_touch_count()
            #         course_last_touched_time = time.time()
            # else:
            #     course_is_touching = False

            # # ゴールの接触判定
            # if GPIO.input(GPIO_GOAL_POINT) == 0:
            #     goal_touching_time += POLLING_INTERVAL
            #     if goal_touching_time >= GOAL_DETECTION_DURATION + POLLING_INTERVAL:
            #         game_state.is_goaled = True
            # else:
            #     goal_touching_time = 0

            # # スタートの接触判定
            # if GPIO.input(GPIO_START_POINT) == 0:
            #     start_touching_time += POLLING_INTERVAL
            #     if start_touching_time >= GOAL_DETECTION_DURATION + POLLING_INTERVAL:
            #         game_state.clear_game_state()

            # else:
            #     start_touching_time = 0

    except Exception as e:
        print(f"{__file__}: {e}")
        sys.exit(e)


def alternate_output(pin_no: int):
    if GPIO.input(pin_no) == GPIO.HIGH:
        GPIO.output(pin_no, GPIO.LOW)
        print("change to low")
    else:
        GPIO.output(pin_no, GPIO.HIGH)
        print("change to high")
