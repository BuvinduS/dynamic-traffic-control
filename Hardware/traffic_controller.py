# traffic_controller.py

'''
On normal IDEs there will be an error for the network, machine umqtt and ujson libraries,
This is because they are MicroPython exclusive.
'''

import time
from machine import Pin
import config


class TrafficController:

    def __init__(self):
        self.current_plan = config.DEFAULT_GREEN
        self.next_plan = None

        self.phase = 0
        self.phase_start = time.time()

        # Example LED pins
        self.leds = [
            Pin(13, Pin.OUT),
            Pin(9, Pin.OUT),
            Pin(3, Pin.OUT),
            Pin(17, Pin.OUT)
        ]

        self.leds[self.phase].on()

    def set_new_plan(self, plan):
        self.next_plan = plan

    def update(self):
        now = time.time()

        if now - self.phase_start >= self.current_plan[self.phase]:
            return self._next_phase()

        return None

    def _next_phase(self):
        # Turn off all
        for led in self.leds:
            led.off()

        # Move to next phase
        self.phase = (self.phase + 1) % 4
        self.phase_start = time.time()

        # Turn on current phase LED
        self.leds[self.phase].on()

        # Apply new plan only after full cycle
        if self.phase == 0 and self.next_plan:
            self.current_plan = self.next_plan
            self.next_plan = None

        return self.phase
