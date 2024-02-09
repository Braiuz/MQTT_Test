import time
from led import Led
import ujson
import bme280
from machine import Pin, I2C, reset, lightsleep

from constants import *
from connectivity import *

DEBUG = True # False to suppres print and led debug
         
         
def Demo_Init():
    global sensor
    global led
    led = Led()
    led.blink(led.LED_SLOW_PERIOD_MS)
    #client = MakeConnections()
    i2c=I2C(0, sda=Pin(I2C_SDA_GPIO), scl=Pin(I2C_SCL_GPIO), freq=I2C_FREQ_HZ)
    try:
        sensor = bme280.BME280(i2c=i2c)
    except Exception as e:
        if(True == DEBUG):
            print('Failed BME280 init - ' + str(e))
            led.blink(led.LED_FAST_PERIOD_MS)
        while(True):
            time.sleep(1)
    if(True == DEBUG):
        print("BME280 init done")
    led.off()

    time.sleep(2)


def Demo_Task():
    global measured
    global led
    
    global temp
    global press
    global hum
    
    while (not measured):
        try:
            temp, press, hum = sensor.values
            if(True == DEBUG):
                print("Temp=" + temp + "°C - Press=" + press + "hPa - Hum=" + hum + "%")
            measured = True
        except OSError as e:
            if(True == DEBUG):
                print('Failed to read sensor.')
                led.blink(LED_FAST_PERIOD_MS)
            while(True):
                time.sleep(1)
    measured = False
    timestamp = time.time()
    # Json encode
    sensorData = {"timestamp":timestamp, "temperature":temp, "pressure":press, "humidity":hum}
    jsonData = ujson.dumps(sensorData)
    Publish("TestSensor", jsonData, client)
    
    lightsleep(5000)
    