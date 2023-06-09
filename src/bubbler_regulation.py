import datetime
import logging
import time
from typing import List, Tuple, Union

from src.device_manager import DeviceManager
from src.global_constants import *
from src.log_config import get_basic_formatter
from src.sensor_manager import SensorManager
from src.system_status import SystemInfoManager, CycleData

handler = logging.FileHandler('logs/controllers.log')
handler.setFormatter(get_basic_formatter())


class Failsafe(Exception):
    def __init__(self, *args):
        super.__init__(*args)


class BubblerController:
    """Controls the exchange of media through the reactor."""

    dm: DeviceManager
    sm: SensorManager
    sys_info: SystemInfoManager

    def __init__(self, sys_info: SystemInfoManager, dm: DeviceManager,
                 sm: SensorManager) -> None:
        """
        Initializes a media exchange controller that ensures that spent media is
        continually replaced with fresh media.
        :param sys_info: stores system info
        :param dm: allows for control of devices
        :param sm: allows for control of sensors
        :return: None
        """

        self.logger = logging.getLogger('Bubbler Controller')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.dm = dm
        self.sm = sm
        self.sys_info = sys_info

        self.time_on = BUBBLER_PERIOD * BUBBLER_PERCENT_ONTIME / 100
        self.time_off = BUBBLER_PERIOD - self.time_on

        self.dm.turn_on_air_pump()
        self.next_swap = datetime.datetime.now() + self.time_on

    def regulate_airflow(self) -> None:
        """Makes sure that the hotplate does not overheat the reactor."""

        if self.sys_info.in_error_state():
            return

        # Safely circulate media when temperature is unavailable.
        if not self.sys_info.temp_sensor_is_working() and HEATING_ENABLED:
            if not self.dm.air_pump_is_on():
                self.dm.turn_on_air_pump()

        if datetime.datetime.now() > self.next_swap:
            bubbler_is_on = self.dm.air_pump_is_on()
            action_string = ['on', 'off'][bubbler_is_on]
            dur = [self.time_on, self.time_off][bubbler_is_on]

            self.logger.info(f"Turning {action_string} bubbler for "
                             f"{dur.seconds} seconds.")

            if bubbler_is_on:
                self.dm.turn_off_air_pump()
                self.next_swap = self.next_swap + self.time_off
            else:
                self.dm.turn_on_air_pump()
                self.next_swap = self.next_swap + self.time_on




