import network
from umqtt.simple import MQTTClient
import ujson
from constants import *
import time

CONN_LAST_WILL_TOPIC = "fault"
CONN_LAST_WILL_MSG   = "Unexpected error"

def ConnectMQTT():
    '''Connects to Broker'''
    # Client ID can be anything
    client = MQTTClient(
        client_id=b"RaspberryPiPicoW",  # TODO cambia in modo incrementale
        server=SERVER_HOSTNAME,
        port=SERVER_PORT, #8883
        user=USER,
        password=PASSWORD,
        keepalive=7200,
        #ssl=True,
        ssl_params={'server_hostname': SERVER_HOSTNAME}
    )
    client.set_last_will(topic=CONN_LAST_WILL_TOPIC, msg=CONN_LAST_WILL_MSG, retain=False)
    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        try:
            client.connect(clean_session=False) # False --> persistent session
            return client
        except Exception as e:
            print("MQTT error")
            attempt += 1
            time.sleep(2*attempt)

        raise RuntimeError("Failed to connect to MQTT broker")


def ConnectInternet(ssid, password):
    # Pass in string arguments for ssid and password
    
    # Just making our internet connection
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    # Wait for connect or fail
    max_wait = 10
    attempt = 0
    while attempt > max_wait:
      if wlan.status() < 0 or wlan.status() >= 3:
        break
      attempt += 1
      print('Waiting for connection...')
      time.sleep(2*attempt)
    # Handle connection error
    if wlan.status() != 3:
       print(wlan.status())
       raise RuntimeError('Failed to connect to WiFi')
    else:
      print('Connected to wlan')
      #print("Wlan status = " + str(wlan.status()))
      status = wlan.ifconfig()
    
    return wlan


def MakeConnections():
    # Connect to internet and set MPU to start taking readings
    ConnectInternet(WLAN_NAME, WLAN_PASSWORD)
    return ConnectMQTT()


def Publish(topic, value, client):
    '''Sends data to the broker'''
    print(f"[PUBLISH] - [{topic}]: {value}")
    try:
        client.publish(topic, value)
        print("Done")
    except Exception as e:
        print(f"Failed to publish data: {e}")
        client = ReconnectMqtt(client)
    

def ReconnectMqtt(client: MQTTClient):
    client.disconnect()
    while True:
        try:
            client = ConnectMQTT()
            print("Reconnected to MQTT broker")
            return client
        except Exception as e:
            print(f"Reconnection attempt failed:{e}")
            time.sleep(5)

# Stop wifi to save power
def StopWiFi(wlan, client: MQTTClient):    # network.WLAN
    if not(client==None):
        client.disconnect()
        client=None
    if not(wlan==None):
        wlan.disconnect()
        wlan.active(False)
        wlan.deinit()
        wlan=None
    time.sleep_ms(100)
    