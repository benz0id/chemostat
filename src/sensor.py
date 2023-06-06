import glob
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, List
from src.pinout import *

from src import log_config, gpio_adapter
from src.global_constants import OFF_PI, OFF_PI_DEFAULT_TEMP, ERROR_TEMPERATURE
from src.observe import Observable, Observer
import src.gpio_adapter

handler = logging.FileHandler('logs/sensors.log')
handler.setFormatter(log_config.get_basic_formatter())


GPIO = src.gpio_adapter.get_GPIO()
GPIO.setmode(GPIO.BCM)

class Sensor(Observable, ABC):
    """Superclass for all sensors.

    === Attributes ===
    last_reading: The last datum recorded by this sensor.

    logger: the
    """

    last_reading: Any
    logger: logging.Logger

    def __init__(self, name: str, observers: List[Observer]) -> None:
        Observable.__init__(self, observers)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    @abstractmethod
    def get_reading(self) -> Any:
        """Fetches updated sensor value and notifies observers."""
        pass


class TemperatureSensor(Sensor):
    """A temperature sensor configure over the one-wire protocol.

    Some code borrowed from https://www.circuitbasics.com/raspberry-pi-ds18b20-temperature-sensor-tutorial/

    === Attributes ===

    last_reading: The last temperature recording.

    === Private Attributes ===

    _device_file: filepath to the file containing this sensor's info.

    """

    last_reading: float
    _device_file: glob.glob
    _working: bool

    def __init__(self, observers: List[Observer] = None) -> None:
        Sensor.__init__(self, 'Temperature Sensor',  observers)
        self._working = True

        if not OFF_PI:
            try:
                base_dir = '/sys/bus/w1/devices/'
                device_folder = glob.glob(base_dir + '28*')[0]
                self._device_file = device_folder + '/w1_slave'
                self.last_reading = self.get_reading()
            except Exception as e:
                self.logger.warning(str(e))
                self.set_working_state(False)
                self.notify_observers()

    def get_reading(self) -> Any:
        """Get an updated temperature and notify observers."""

        self.logger.debug("Fetching current temperature.")
        self.last_reading = ERROR_TEMPERATURE
        if OFF_PI:
            self.last_reading = gpio_adapter.get_GPIO().simulator.temp
        else:
            self.last_reading = self._read_temp_c()
        self.logger.debug("Current Temperature: " + str(self.last_reading))
        self.logger.debug("Notifying observers.")
        self.notify_observers()
        return self.last_reading

    def set_working_state(self, state: bool) -> None:
        """Sets this sensor's operational state to <state>"""
        if self._working and not state:
            self.logger.warning("Unable to detect temperature sensor.")
        if not self._working and state:
            self.logger.warning("Temperature sensor back online.")

        self._working = state

    def get_working_state(self) -> bool:
        return self._working

    def _read_temp_raw(self) -> List[str]:
        """Fetch raw temperature data from sensor."""
        f = open(self._device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def _read_temp_c(self) -> float:
        """Convert raw temperature data from HEX and return it as a float
        value."""
        try:
            lines = self._read_temp_raw()
            while lines[0].strip()[-3:] != 'YES':
                lines = self._read_temp_raw()
            equals_pos = lines[1].find('t=')
            temp_string = lines[1][equals_pos + 2:]
            temp_c = int(temp_string) / 1000.0
            self.set_working_state(True)
            return temp_c
        except Exception as e:
            self.logger.warning(str(e))
            self.set_working_state(False)
            return self.last_reading


class WaterLevelSensor(Sensor):
    """A sensor capable of detecting the water level in the chemostat.

    === Attributes ===
    last_reading: whether the water level has reached the sensor.

    === Private attributes ===
    _pin: the GPIO pin to which this sensor is connected.

    """
    last_reading: bool

    def __init__(self, pin: int, observers: List[Observer] = None) -> None:
        Sensor.__init__(self, "Water Level Sensor", observers)
        self._pin = pin
        GPIO.setup(pin, GPIO.IN)

    def get_reading(self) -> bool:
        """Gets the current water level."""
        self.logger.debug("Getting water level.")
        self.last_reading = GPIO.input(self._pin)
        self.logger.debug("Water currently at sensor: " +
                         str(bool(self.last_reading)))
        self.notify_observers()
        return self.last_reading


if __name__ == '__main__':
    temp_sensor = TemperatureSensor()
    wl_sensor = WaterLevelSensor(WATER_LEVEL_SENSOR_PIN)
    while True:
        temp_sensor.get_reading()
        wl_sensor.get_reading()
        time.sleep(1)
