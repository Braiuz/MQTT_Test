import network
import time
from led import Led
from umqtt.simple import MQTTClient
import dht
from machine import Pin

import constants

def ConnectMQTT():
    '''Connects to Broker'''
    # Client ID can be anything
    client = MQTTClient(
        client_id=b"RaspberryPiPicoW",
        server=constants.SERVER_HOSTNAME,
        port=8883,
        user=constants.USER,
        password=constants.PASSWORD,
        keepalive=7200,
        ssl=True,
        ssl_params={'server_hostname': constants.SERVER_HOSTNAME}
    )
    client.connect()
    return client


def ConnectInternet(ssid, password):
    # Pass in string arguments for ssid and password
    
    # Just making our internet connection
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
      if wlan.status() < 0 or wlan.status() >= 3:
        break
      max_wait -= 1
      print('Waiting for connection...')
      time.sleep(1)
    # Handle connection error
    if wlan.status() != 3:
       print(wlan.status())
       raise RuntimeError('Network connection failed')
    else:
      print('Connected to wlan')
      #print("Wlan status = " + str(wlan.status()))
      status = wlan.ifconfig()
      
      
def MakeConnections():
    # Connect to internet and set MPU to start taking readings
    ConnectInternet(constants.WLAN_NAME, constants.WLAN_PASSWORD)
    return ConnectMQTT()


def Publish(topic, value, client):
    '''Sends data to the broker'''
    print(f"[PUBLISH] - [{topic}]: {value}")
    client.publish(topic, value)
    print("Done")
    
## MAIN ##
led = Led()
client = MakeConnections()
sensor = dht.DHT11(Pin(28))
measured = False	# True if measure gone well
temp = 0.0
hum = 0.0
time.sleep(2)

while True:
    while (not measured):
        try:
            sensor.measure()
            measured = True
        except OSError as e:
             print('Failed to read sensor.')
    measured = False
    temp = sensor.temperature()
    hum = sensor.humidity()
    Publish("TestTemperature", str(temp), client)
    Publish("TestHumidity", str(hum), client)
    time.sleep(2)
    led.toggle()