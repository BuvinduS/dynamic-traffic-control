from traffic_q_learning import get_current_time_info

class DecisionEngine:
    def __init__(self, model):
        self.model = model

    def compute_plan(self, junction_state):
        flows, incoming, outgoing = junction_state.build_flows()
        road_priority = incoming.index(max(incoming))
        day, time_slot = get_current_time_info()
        green_times = self.model.predict_green_times(
            road_priority, day, time_slot, flows
        )
        return {
            "green_times": list(green_times),
            "road_priority": road_priority
        }