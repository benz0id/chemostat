import datetime
import sys
from threading import Thread
from typing import Dict
import time

from src.global_constants import *
from src.pinout import *

def seconds_since(dt: datetime.datetime) -> float:
    return (datetime.datetime.now() - dt).total_seconds()


class Simulator:
    water_level: float
    pins: Dict[int, bool]
    last_check: datetime.datetime
    last_notify: datetime.datetime

    def __init__(self, pins: Dict[int, bool], initial_water_level: float = 0):
        self.last_check = datetime.datetime.now()
        self.last_notify = datetime.datetime.now()
        self.pins = pins
        self.water_level = initial_water_level
        if initial_water_level is None:
            self.water_level = 0

        thread = Thread(target=self.run)
        thread.start()

    def run(self):
        self.last_notify = datetime.datetime.now()
        while True:
            self.check_pins()
            self.print_state()
            time.sleep(SIMULATOR_TICK)

    def print_state(self) -> None:
        if seconds_since(self.last_notify) > SIMULATOR_NOTIFY_EVERY:
            print('Volume: {:}'.format(self.water_level),
                  '\nSensor: {:}'.format(WL_SENSOR_THRESHOLD), file=sys.stderr)
            self.last_notify = datetime.datetime.now()

    def check_pins(self):
        for pin in self.pins:
            state = self.pins[pin]

            if pin == MEDIA_OUT_PIN and state == 0:
                self.water_level -= seconds_since(self.last_check) * \
                                    MEDIA_OUT_FLOWRATE

            if pin == MEDIA_IN_PIN and state == 0:
                self.water_level += seconds_since(self.last_check) * \
                                    MEDIA_IN_FLOWRATE
        self.last_check = datetime.datetime.now()

    def get_wl_state(self) -> bool:
        return self.water_level > WL_SENSOR_THRESHOLD


class GPIO:
    """A Dummy GPIO module for local testing."""
    sig = OFF_PI_DEFAULT_SIG
    BCM = None
    OUT = 'out'
    IN = 'in'

    def __init__(self):
        self.pins = {}
        self.simulator = Simulator(self.pins, REACTOR_VOLUME)

    def setwarnings(self, *args, **kwargs):
        pass
    def setmode(self, *args, **kwargs):
        pass
    def cleanup(self, *args, **kwargs):
        pass
    def output(self, pin: int, mode):
        self.pins[pin] = mode
    def setup(self, pin: int, mode, initial=0):
        if mode == self.OUT:
            self.pins[pin] = initial
    def input(self, pin: int):
        if pin == WATER_LEVEL_SENSOR_PIN:
            return self.simulator.get_wl_state()

        return self.sig

if not OFF_PI:
    import RPi.GPIO as real_gpio
else:
    dummy_gpio = GPIO()

def get_GPIO():
    if not OFF_PI:
        return real_gpio
    else:
        return dummy_gpio
