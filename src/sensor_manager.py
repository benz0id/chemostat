from typing import List

from src.device_manager import DeviceManager
from src.pinout import WATER_LEVEL_SENSOR_PIN
from src.sensor import TemperatureSensor, WaterLevelSensor, Sensor
from src.system_status import SystemInfoManager


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
