import glob
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, List
from pinout import *

from src import log_config
from src.device import DeviceManager
from src.observe import Observable, Observer
import RPi.GPIO as GPIO

from src.system_status import SystemInfoManager

handler = logging.FileHandler('logs/sensors.log')
handler.setFormatter(log_config.basic_formatter)

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

    def __init__(self, observers: List[Observer] = None) -> None:
        Sensor.__init__(self, 'Temperature Sensor',  observers)

        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]
        self._device_file = device_folder + '/w1_slave'
        self.last_reading = self.get_reading()

    def get_reading(self) -> Any:
        """Get an updated temperature and notify observers."""
        self.logger.debug("Fetching current temperature.")
        self.last_reading = self._read_temp_c()
        self.logger.info("Current Temperature: " + str(self.last_reading))
        self.logger.debug("Notifying observers.")
        self.notify_observers()
        return self.last_reading

    def _read_temp_raw(self) -> List[str]:
        """Fetch raw temperature data from sensor."""
        f = open(self._device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def _read_temp_c(self) -> float:
        """Convert raw temperature data from HEX and return it as a float
        value."""
        lines = self._read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            lines = self._read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = int(temp_string) / 1000.0
            return temp_c


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
        self.logger.info("Water currently at sensor: " +
                         str(bool(self.last_reading)))
        self.notify_observers()
        return self.last_reading


class SensorManager:
    """Manages the sensors used by the chemostat.

    === Attributes ===

    temp_sensor: the temperature sensor

    wl_sensor: the water level sensor
    """
    temp_sensor: TemperatureSensor
    wl_sensor: WaterLevelSensor
    sensors: List[Sensor]

    def __init__(self, sys_info: SystemInfoManager, dm: DeviceManager):
        self.temp_sensor = TemperatureSensor([sys_info])
        self.wl_sensor = WaterLevelSensor(WATER_LEVEL_SENSOR_PIN,
                                          [sys_info, dm.yellow_led])
        self.sensors = [self.temp_sensor, self.wl_sensor]

    def update_readings(self) -> None:
        for sensor in self.sensors:
            sensor.get_reading()

    def get_temp(self) -> float:
        """Gets the current temperature of the reaction vessel."""
        return self.temp_sensor.get_reading()

    def wl_exceeded(self) -> bool:
        """Returns whether the water level has been exceeded."""
        return self.wl_sensor.get_reading()

    def get_media_level_string(self) -> str:
        wl_above_sensor = self.wl_exceeded()
        wl_str = ['below', 'above'][wl_above_sensor]
        return "Media currently " + wl_str + ' water level sensor.'


if __name__ == '__main__':
    temp_sensor = TemperatureSensor()
    wl_sensor = WaterLevelSensor(WATER_LEVEL_SENSOR_PIN)
    while True:
        temp_sensor.get_reading()
        wl_sensor.get_reading()
        time.sleep(1)
