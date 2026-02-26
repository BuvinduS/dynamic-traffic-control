import paho.mqtt.client as mqtt
import time
import json
import csv
import os

CSV_FILE = '../utils/decision_logs.csv'

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "timestamp_readable",
            "north_g",
            "east_g",
            "south_g",
            "west_g",
            "road_priority"
        ])

def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode("utf-8"))

    green_times = payload["plan"]["green_times"]
    road_priority = payload["plan"]["road_priority"]
    timestamp = payload["timestamp"]
    timestamp_readable = payload["timestamp_readable"]

    # Flatten + write row
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            timestamp_readable,
            green_times[0],
            green_times[1],
            green_times[2],
            green_times[3],
            road_priority
        ])

    print("Logged decision:", green_times)

    print(json.dumps(payload, indent=2))

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected with reason code:", reason_code)
    if reason_code == 0:
        print("Connecting...")
        client.subscribe("traffic/junction_1/decision")
        print("Connected...")

mqttBroker = "broker.hivemq.com"
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="Logger", protocol=mqtt.MQTTv5)

client.on_message = on_message
client.on_connect = on_connect

client.connect(mqttBroker, 1883, 60)

print(client.is_connected())

client.loop_forever()