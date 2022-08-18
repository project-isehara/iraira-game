# pyright: reportGeneralTypeIssues=false
from ipaddress import v6_int_to_packed
import RPi.GPIO as GPIO

from iraira.player import SignalParam
from iraira.state import AppState,PlayerState
import time

GPIO_PARALLEL_0 = 21
GPIO_PARALLEL_1 = 20
GPIO_PARALLEL_2 = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PARALLEL_0, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_PARALLEL_1, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_PARALLEL_2, GPIO.IN,pull_up_down=GPIO.PUD_UP)

def analog_listener(
    app_state: AppState,
    sig_param: SignalParam,
    player_state:PlayerState,
) -> None:
    while app_state.is_running:
        parallelValue=0
        if GPIO.input(GPIO_PARALLEL_0):
           parallelValue |= (1 << 0)
        if GPIO.input(GPIO_PARALLEL_1):
           parallelValue |= (1 << 1)
        if GPIO.input(GPIO_PARALLEL_2):
           parallelValue |= (1 << 2) 
        
        parallelValue-=4 # -4 ~ +3 に変換
        if parallelValue>0:
            v=parallelValue/3 
            sig_param.traction_up()
        elif parallelValue<-1:
            v=(-parallelValue-1)/3 
            sig_param.traction_down()
        else : # parallelValue=0,-1のとき
            v=0

        player_state.volume=v
        time.sleep(0.2)