import threading
import time
import math
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

    previous_total = 20  # starting value
    start_time = time.time()

    while True:
        t = time.time() - start_time

        # --- 1️⃣ Base traffic pattern (slow variation) ---
        if severity_in == "HIGH":
            base = 60 + 20 * math.sin(t / 30)
        elif severity_in == "NORMAL":
            base = 30 + 10 * math.sin(t / 40)
        else:  # LOW
            base = 15 + 5 * math.sin(t / 50)

        if 120 < t < 240 or 360 < t < 480:
            base += 60  # simulate rush hour spike

        # --- 2️⃣ Add small noise ---
        noise = random.randint(-5, 5)
        measured = max(0, base + noise)

        # --- 3️⃣ Add inertia (very important) ---
        total = 0.8 * previous_total + 0.2 * measured
        previous_total = total

        payload = {
            "lane": lane,
            "vehicle_count": int(total),
            "timestamp": time.time()
        }

        on_update(lane, payload)
        time.sleep(2)

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