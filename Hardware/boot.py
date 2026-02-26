# boot.py

'''
On normal IDEs there will be an error for the network, machine umqtt and ujson libraries,
This is because they are MicroPython exclusive.
'''

import network
import time
from config import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)

print("WiFi connected:", wlan.ifconfig())