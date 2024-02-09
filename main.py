from demo import *
import time
import machine

Demo_Init()

try:
    while(True):
        Demo_Task()
except OSError as e:
    time.sleep_ms(500)
    machine.reset()
    