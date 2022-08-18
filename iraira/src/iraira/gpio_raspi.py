# pyright: reportGeneralTypeIssues=false
import RPi.GPIO as GPIO

from iraira.player import SignalParam
from iraira.state import AppState

PIN_TRRACTION_CHANGE = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TRRACTION_CHANGE, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def switch_listener(
    app_state: AppState,
    sig_param: SignalParam,
) -> None:
    while app_state.is_running:
        _ = GPIO.wait_for_edge(PIN_TRRACTION_CHANGE, GPIO.FALLING, bouncetime=500)
        sig_param.traction_change()
