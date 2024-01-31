# MQTT_Test
Code to run a Raspberry Pi Pico W as an MQTT node. It reads temperature, humidity and pressure from a BME280 sensor and publishes those data to a MQTT topic. A local Mosquitto broker is used as MQTT broker (running on a Raspberry Pi).

Data on the topic has the following structure: Timestamp, Temperature, Humidity, Pressure.
