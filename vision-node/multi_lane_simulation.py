import threading
import time

from mqtt_publish import publish_data
import random

LANES = {
    # lane direction, then incoming and outgoing traffic severity
    "north": ["HIGH", "LOW"],
    "east": ["LOW", "LOW"],
    "south": ["NORMAL", "HIGH"],
    "west": ["HIGH", "HIGH"]
}

def simulate_traffic(lane, severity_in=None, severity_out=None):
    while True:
        count_in = 0
        count_out = 0
        match severity_in:
            case "NORMAL":
                count_in = random.randint(10, 15)
                avg_speed = random.randint(40, 60)
            case "LOW":
                count_in = random.randint(5, 10)
                avg_speed = random.randint(60, 80)
            case "HIGH":
                count_in = random.randint(35, 100)
                avg_speed = random.randint(20, 40)

        match severity_out:
            case "NORMAL":
                count_out = random.randint(10, 15)
            case "LOW":
                count_out = random.randint(5, 10)
            case "HIGH":
                count_out = random.randint(35, 40)

        payload = {
            "lane": lane,
            "vehicle_count": count_in + count_out,
            # "avg_speed": payload.get("avg_speed"),
            # "queue_length": payload.get("queue_length"),
            "incoming": count_in,  # optional aggregated
            "outgoing": count_out,  # optional aggregated
            "timestamp": time.time()
        }

        on_update(lane, payload)
        time.sleep(2)   # published every 2 seconds


def on_update(lane, data):
    publish_data(lane, data)

# def start_lane(lane, video):
#     simulate_traffic()

threads = []

for lane, severity in LANES.items():
    t = threading.Thread(target=simulate_traffic, args=(lane, severity[0], severity[1]))
    t.start()
    threads.append(t)

for t in threads:
    t.join()