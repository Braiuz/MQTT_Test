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
    try:
        client.connect(clean_session=False) # False --> persistent session
    except ConnectionAbortedError:
        print("Error while connecting to MQTT broker. Check if broker is reachable and if credentials are valid")
        FaultHandling()
    except Exception as e:
        print("Unknown error")
        raise e
        
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
    
    return wlan


def MakeConnections():
    # Connect to internet and set MPU to start taking readings
    ConnectInternet(WLAN_NAME, WLAN_PASSWORD)
    return ConnectMQTT()


def Publish(topic, value, client):
    '''Sends data to the broker'''
    print(f"[PUBLISH] - [{topic}]: {value}")
    client.publish(topic, value)
    print("Done")
    

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
    