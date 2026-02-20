import threading
import time

# Lanes order (must be consistent with vision node)
LANES = ["north", "east", "south", "west"]

# How often (seconds) to compute/publish decisions per junction
DECISION_INTERVAL_SEC = 5

# How long a per-lane message is considered fresh (seconds)
FRESHNESS_TIMEOUT_SEC = 2 * DECISION_INTERVAL_SEC


class JunctionState:
    """Stores latest per-lane data for one junction"""
    def __init__(self, junction_id):
        self.junction_id = junction_id
        # For each lane index: dict with keys vehicle_count, avg_speed, queue_length, ts
        self.lane_data = {lane: None for lane in LANES}
        self.lock = threading.Lock()
        self.last_decision_ts = 0

    def update_lane(self, lane, payload):
        """Update stored info for a single lane"""
        with self.lock:
            entry = {
                "vehicle_count": payload.get("vehicle_count"),
                "avg_speed": payload.get("avg_speed"),
                "queue_length": payload.get("queue_length"),
                "incoming": payload.get("incoming"),  # optional aggregated
                "outgoing": payload.get("outgoing"),  # optional aggregated
                "timestamp": payload.get("timestamp", time.time())
            }
            self.lane_data[lane] = entry

    def is_fresh(self):
        """Return True if all four lanes have fresh data"""
        with self.lock:
            now = time.time()
            for lane in LANES:
                entry = self.lane_data.get(lane)
                if not entry:
                    return False
                if now - entry.get("timestamp", 0) > FRESHNESS_TIMEOUT_SEC:
                    return False
            return True

    def build_flows(self):
        """Return flows = incoming[4] + outgoing[4] arrays (integers).
           If per-lane 'incoming'/'outgoing' are provided, use them.
           Otherwise, estimate outgoing using heuristic.
        """
        with self.lock:
            incoming = []
            outgoing = []
            for lane in LANES:
                entry = self.lane_data.get(lane) or {}
                # Prefer explicit incoming/outgoing if provided
                inc = entry.get("incoming")
                out = entry.get("outgoing")

                if inc is None: # Data has not been provided in the payload
                    # fallback to vehicle_count as incoming
                    vc = entry.get("vehicle_count")
                    inc = int(vc) if vc is not None else 0

                if out is None:
                    # Heuristic outgoing estimate:
                    # - if queue_length exists, estimate outgoing = max(1, incoming - queue_length)
                    # - else approximate outgoing as 60% of incoming (tunable)
                    qlen = entry.get("queue_length")
                    if qlen is not None:    # If queue_length exists
                        out = max(1, int(inc - qlen))
                    else:   # If no queue_length assume 60% of vehicles move through
                        out = max(1, int(inc * 0.6))

                incoming.append(int(inc))   # incoming count for the specific lane
                outgoing.append(int(out))   # outgoing count for the specific lane

            flows = incoming + outgoing
            return flows, incoming, outgoing