# main.py
print("MAIN_STARTED")
from mqtt_handler import MQTTHandler
from traffic_controller import TrafficController
import time

controller = TrafficController()
mqtt = MQTTHandler(controller)

mqtt.connect()

while True:
    mqtt.check()
    phase_changed = controller.update()

    if phase_changed is not None:
        mqtt.publish_state(phase_changed)

    time.sleep(0.1)