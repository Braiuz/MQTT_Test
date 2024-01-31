import time
from led import Led
#import dht
import bme280
from machine import Pin, I2C, reset

from constants import *
from connectivity import *

LED_OFF       = 0
LED_ON        = 1
LED_SLOWBLINK = 2
LED_FASTBLINK = 3

measured = False	# True if measure succeded
sensor: bme280.BME280
led: Led

def LedSignaling(ledStatus: int):
    # 0 -> off
    # 1 -> solid on
    # 2 -> slow blink
    # 3 -> fast blink
    global led
    if (LED_OFF == ledStatus):
        pass
    elif (LED_ON == ledStatus):
        led.on()
    elif ( LED_SLOWBLINK == ledStatus):
        while(True):
            led.on()
            time.sleep(1)
            led.off()
            time.sleep(1)
    elif (LED_FASTBLINK == ledStatus):
        while(True):
            led.on()
            time.sleep(0.2)
            led.off()
            time.sleep(0.2)
            
            
def Demo_Init():
    global sensor
    global led
    led = Led()
    #client = MakeConnections()
    print("BME280 init")
    i2c=I2C(0, sda=Pin(I2C_SDA_GPIO), scl=Pin(I2C_SCL_GPIO), freq=I2C_FREQ_HZ)
    #try:
    sensor = bme280.BME280(i2c=i2c)
    #except Exception as e:
    #    print('Failed BME280 init - ' + str(e))
        #machine.reset()
    print("Done")

    #sensor = dht.DHT11(Pin(28))

    time.sleep(2)


def Demo_Task():
    global measured
    global led
    while (not measured):
        try:
            #sensor.measure()
            print(sensor.values)
            measured = True
        except OSError as e:
             print('Failed to read sensor.')
             time.sleep(1)
    measured = False
    #temp = sensor.temperature()
    #hum = sensor.humidity()
    timestamp = time.time()
    # Json encode
    #sensorData = {"temperature":temp, "humidity":hum, "timestamp":timestamp}
    #jsonData = ujson.dumps(sensorData)
    
    #Publish("TestSensor", jsonData, client)
    #Publish("TestHumidity", str(hum), client)
    time.sleep(2)
    led.toggle()
    