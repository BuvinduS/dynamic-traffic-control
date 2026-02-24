import paho.mqtt.client as mqtt
from traffic_q_learning import TrafficQLearning
from junction_state import JunctionState, LANES, DECISION_INTERVAL_SEC
from decision_engine import DecisionEngine
import threading
import json
import time
import datetime

MQTT_BROKER = "broker.hivemq.com"

MQTT_QOS = 1
TOPIC_PREFIX = "traffic"


class MQTTClient:
    def __init__(self, broker=MQTT_BROKER):
        self.broker = broker
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="DecisionNode",
                                  protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Map junction_id -> JunctionState
        self.junctions = {}

        # Background worker
        self.running = False
        self.worker_thread = None

        self.model = TrafficQLearning()
        self.decision_engine = DecisionEngine(self.model)

        # dicts needed for smoothing plan output
        self.plan_history = {}
        self.last_publish_time = {}
        self.PUBLISHING_INTERVAL_SEC = 10   # demo: 60 sec instead of 5 min
        self.HISTORY_WINDOW = 12  # if interval=5s → 12 samples = 1 min

    def average_green_times(self, history):
        return [
            round(sum(values) / len(values))
            for values in zip(*history)
        ]

    def start(self):
        self.running = True
        self.client.connect(self.broker,keepalive=60)
        # subscribe to all junction/lane topics
        topic = "traffic/junction_1/+"
        self.client.subscribe(topic, qos=MQTT_QOS)
        self.client.loop_start()    # starts the MQTT network loop

        self.worker_thread = threading.Thread(target=self.decision_loop, daemon=True)   # start decision loop
        self.worker_thread.start()
        print("DecisionNodeService started, subscribed to:", topic)

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        self.client.loop_stop()
        try:
            self.client.disconnect()
        except Exception:
            pass

        print("DecisionNodeService stopped.")

    def decision_loop(self):
        print("Inside decision loop")
        while self.running:
            time.sleep(DECISION_INTERVAL_SEC)

            for junction_id, state in list(self.junctions.items()):
                if not state.is_fresh():
                    continue

                plan = self.decision_engine.compute_plan(state)

                # Initialize structures if needed
                if junction_id not in self.plan_history:
                    self.plan_history[junction_id] = []
                    self.last_publish_time[junction_id] = 0

                # Store raw plan
                self.plan_history[junction_id].append(plan["green_times"])

                # Keep only last N samples
                if len(self.plan_history[junction_id]) > self.HISTORY_WINDOW:
                    self.plan_history[junction_id].pop(0)

                # Check if it's time to publish
                current_time = time.time()
                readable_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if current_time - self.last_publish_time[junction_id] >= self.PUBLISHING_INTERVAL_SEC:
                    averaged = self.average_green_times(
                        self.plan_history[junction_id]
                    )

                    stable_plan = {
                        "junction_id": junction_id,
                        "plan": {
                            "green_times": averaged,
                            "road_priority": averaged.index(max(averaged))
                        },
                        "timestamp": current_time,
                        "timestamp_readable": readable_time
                    }

                    self.client.publish(
                        "traffic/junction_1/decision",
                        json.dumps(stable_plan),
                        qos=MQTT_QOS
                    )

                    self.last_publish_time[junction_id] = current_time

                # payload = {
                #     "junction_id": junction_id,
                #     "plan": plan,
                #     "timestamp": time.time()
                # }
                #
                # topic = "traffic/junction_1/decision"
                # print("publishing to the topic")
                # self.client.publish(
                #     topic,
                #     json.dumps(payload),
                #     qos=MQTT_QOS
                # )

    # MQTT callbacks
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        print(f"Connected to MQTT broker {self.broker}, reason={reason_code}")

    def on_message(self, client, userdata, msg):
        # Expect topic: traffic/<junction_id>/<lane>
        topic_parts = msg.topic.split('/')
        if len(topic_parts) < 3:
            print("Ignoring malformed topic:", msg.topic)
            return
        _, junction_id, lane = topic_parts[:3]

        if lane == "decision":
            return

        if lane == "aggregated":
            # optional aggregated payload for whole junction
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except Exception as e:
                print("Malformed JSON on aggregated:", e)
                return
            # aggregated should contain 'incoming' and 'outgoing' arrays
            js = payload
            flows = js.get("incoming"), js.get("outgoing")
            if js.get("incoming") and js.get("outgoing"):
                # create or get junction state and populate lanes
                if junction_id not in self.junctions:
                    self.junctions[junction_id] = JunctionState(junction_id)

                state = self.junctions[junction_id]
                for i, lane_name in enumerate(LANES):
                    p = {
                        "incoming": js["incoming"][i],
                        "outgoing": js["outgoing"][i],
                        "vehicle_count": js["incoming"][i],  # convenience
                        "timestamp": js.get("timestamp", time.time())
                    }
                    state.update_lane(lane_name, p)
                self.junctions[junction_id] = state
            else:
                print("Aggregated message missing incoming/outgoing arrays")
            return

        # otherwise per-lane payload
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except Exception as e:
            print("Malformed JSON message:", e)
            return

        # Create junction state if missing
        if junction_id not in self.junctions:
            self.junctions[junction_id] = JunctionState(junction_id)

        # Update lane data
        if lane not in LANES:
            # Accept unknown lane names but standardization is recommended
            print(f"Received data for unknown lane '{lane}'. Known lanes: {LANES}")
        self.junctions[junction_id].update_lane(lane, payload)
        # Debug:
        # print(f"Updated {junction_id}/{lane} -> {payload}")


