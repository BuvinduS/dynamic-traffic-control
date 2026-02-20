import signal
import time
from mqtt_client import MQTTClient


def main():
    client = MQTTClient()

    def shutdown(sig, frame):
        print("\nShutting down Decision Node...")
        client.stop()
        exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    client.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
