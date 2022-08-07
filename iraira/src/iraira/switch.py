# pyright: reportGeneralTypeIssues=false
import RPi.GPIO as GPIO

from traction_controller.player import SignalParam
from traction_controller.state import AppState

GPIO_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def switch_listener(
    app_state: AppState,
    sig_param: SignalParam,
):
    while app_state.is_running:
        _ = GPIO.wait_for_edge(GPIO_PIN, GPIO.FALLING, bouncetime=500)
        sig_param.traction_change()