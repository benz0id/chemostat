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


class ThermalRegulationController:
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

        self.logger = logging.getLogger('Temperature Regulation Controller')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.dm = dm
        self.sm = sm
        self.sys_info = sys_info


    def failsafe(self) -> None:
        """Terminate the program if the temperature gets too high."""
        overheat = self.sm.get_temp() > SHUTDOWN_TEMP
        system_error = self.sys_info.in_error_state()

        if overheat or system_error:
            self.dm.hotplate.off()

        if overheat:
            self.sys_info.set_error_state("System Overheated")

        return


    def regulate_temp(self) -> None:
        """Makes sure that the hotplate does not overheat the reactor."""
        if self.sys_info.in_error_state():
            return

        over_heating = self.sm.get_temp() > TARGET_TEMP
        hotplate_on = self.dm.hotplate.is_on()

        if over_heating and hotplate_on:
            self.logger.info('Target Temp Achieved. Turning off hotplate.')
            self.dm.hotplate.off()

        elif not over_heating and not hotplate_on:
            self.logger.info('Media Cooling. Turning on hotplate.')
            self.dm.hotplate.on()






