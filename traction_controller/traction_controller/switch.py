# pyright: reportGeneralTypeIssues=false
import RPi.GPIO as GPIO

from traction_controller.player import SignalParam
from traction_controller.state import AppState

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def switch_listener(
    app_state: AppState,
    sig_param: SignalParam,
):
    while app_state.is_running:
        res = GPIO.wait_for_edge(17, GPIO.FALLING, bouncetime=500)
        sig_param.traction_change()
