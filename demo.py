import time
from led import Led
import ujson
import bme280
from machine import Pin, I2C, reset, lightsleep

from constants import *
from connectivity import *

DEBUG = True # False to suppres print and led debug
client = None         
         
def Demo_Init():
    global sensor
    global led
    global client
    led = Led()
    led.blink(led.LED_SLOW_PERIOD_MS)
    client = MakeConnections()
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

    global client

    jsonData = SensorRead()

    try:
        Publish("TestSensor", jsonData, client)
        lightsleep(60000)
    except Exception as e:
        if not wlan.isconnected():
            print("WiFi connection lost. Attempting to reconnect...")
            wlan = ConnectInternet(WLAN_NAME, WLAN_PASSWORD)
            client = ReconnectMqtt(client)
        else:
            client = ReconnectMqtt(client)
    

def SensorRead():
    global temp
    global press
    global hum

    global measured
    global led

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
                time.sleep(5)
            # wait and then try again, keep the old sensor values    
            time.sleep(1)
    measured = False
    timestamp = time.time()
    # Json encode
    sensorData = {"timestamp":timestamp, "temperature":temp, "pressure":press, "humidity":hum}
    jsonData = ujson.dumps(sensorData)

    return jsonData