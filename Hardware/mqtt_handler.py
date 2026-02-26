# mqtt_handler.py

'''
On normal IDEs there will be an error for the network, machine umqtt and ujson libraries,
This is because they are MicroPython exclusive.
'''

from umqtt.simple import MQTTClient
import ujson
import config
import time


class MQTTHandler:
    def __init__(self, controller):
        self.controller = controller
        self.client = MQTTClient("esp32_R.O.G", config.MQTT_BROKER, keepalive=60, port=1883)
        self.client.set_callback(self.on_message)

    def connect(self):
        print("Connecting to MQTT...")
        self.client.connect()
        print("Connected. Subscribing...")
        self.client.subscribe(config.MQTT_TOPIC)
        print("MQTT connected and subscribed")

    def on_message(self, topic, msg):
        try:
            payload = ujson.loads(msg)
            green_times = payload["plan"]["green_times"]
            self.controller.set_new_plan(green_times)
        except Exception as e:
            print("MQTT parse error:", e)

    def check(self):
        self.client.check_msg()  # non-blocking

    def publish_state(self, phase):
        msg = ujson.dumps({
            "phase": phase,
            "timestamp": time.time()
        })

        self.client.publish("traffic/junction_1/state", msg)