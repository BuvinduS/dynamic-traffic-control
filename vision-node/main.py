from detection import run_detection
from mqtt_publish import publish_data

def on_update(data):
    publish_data("west", data)

run_detection(on_update=on_update)