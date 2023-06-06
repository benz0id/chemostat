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

        if not HEATING_ENABLED:
            self.dm.turn_on_hotplate()
            self.logger.warning('Assuming that hotplate heating is disabled. '
                                'Using stirring-only mode.')

    def failsafe(self) -> None:
        """Terminate the program if the temperature gets too high."""
        # Safely circulate media when temperature is unavailable.
        if not self.sys_info.temp_sensor_is_working() and HEATING_ENABLED:
            if self.dm.hotplate_is_on():
                self.dm.turn_off_hotplate()
            return

        overheat = self.sm.get_temp() > SHUTDOWN_TEMP
        system_error = self.sys_info.in_error_state()

        if overheat or system_error:
            self.dm.turn_off_hotplate()

        if overheat:
            self.sys_info.set_error_state("System Overheated")

        return

    def regulate_temp(self) -> None:
        """Makes sure that the hotplate does not overheat the reactor."""

        # If not heating, keep hotplate on regardless of temperature.
        if not HEATING_ENABLED:
            if not self.dm.hotplate_is_on():
                self.dm.turn_on_hotplate()
            return

        # Account for sensor errors.
        self.failsafe()

        # If system is failing, do not regulate the temperature.
        if self.sys_info.in_error_state():
            assert not self.dm.hotplate_is_on()
            return

        over_heating = self.sm.get_temp() > TARGET_TEMP
        hotplate_on = self.dm.hotplate_is_on()

        if over_heating and hotplate_on:
            self.logger.info('Target Temp Achieved. Turning off hotplate.')
            self.dm.turn_off_hotplate()

        elif not over_heating and not hotplate_on:
            self.logger.info('Media Cooling. Turning on hotplate.')
            self.dm.turn_on_hotplate()






