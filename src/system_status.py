import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any, List
from src.global_constants import *
from src.device import Device
from src.log_config import get_basic_formatter
from src.observe import Observer, Observable
from src.sensor import Sensor, TemperatureSensor, WaterLevelSensor

handler = logging.FileHandler('logs/system_status.log')
handler.setFormatter(get_basic_formatter())

class CycleData:
    """Stores information regarding an active media cycle.

    === Attributes ===

    target_exchange_vol:

    inlet_ontime: the time the inlet pump has been active for.
    outlet_ontime: the time the outlet pump has been active for.


    state:
        start
        drain
        fill
        over - water level sensor triggered before media addition complete
        under - water  level sensor not before media addition complete
        calib
        error
        done
    """
    target_pump_ontime: float
    inlet_ontime: float
    outlet_ontime: float
    fill_state: str
    error_description: str

    def __init__(self, target_exchange_vol: float) -> None:
        self.target_exchange_vol = target_exchange_vol
        self.inlet_ontime = 0
        self.outlet_ontime = 0
        self.state = "start"

    def get_in_vol(self) -> float:
        return MEDIA_IN_FLOWRATE * self.inlet_ontime

    def get_out_vol(self) -> float:
        return MEDIA_OUT_FLOWRATE * self.outlet_ontime

    def get_targ_exchange_vol(self) -> float:
        return self.target_exchange_vol


class SystemInfoManager(Observer, Observable):
    """ Stores and collects dynamic properties of the system.

    === Private Attributes ===

    start_time: time at which the program began running

    last_temp: the last recorded temperature

    active_devices: all devices that are currently running

    system_state: the state of the system
        standby - only gas exchange is active
        media_exchange - media is currently being exchanged
        error - sensors indicate that system has fallen out of equilibrium.
        debug - displays system stats

    num_warnings: number of warnings produced throughout the program's operation

    num_errors: the number of errors that have occurred throughout the programs
        operation.

    total_media_in: the total amount of media added to the system in ml.

    total_media_out: the total amount of media removed from the system in ml.

    cycle_data: stores properties of the current media exchange cycle.
    """
    logger: logging.Logger

    _start_time: datetime.datetime

    _next_cycle: datetime.datetime

    _last_temp: float
    _min_temp: float
    _max_temp: float

    _total_media_in: float
    _total_media_out: float

    _water_level_exceeded: bool

    _active_devices: List[Device]
    _system_state: str
    _num_warnings: int
    _num_errors: int
    _cycle_data: CycleData

    def __init__(self, observers: List[Observer]) -> None:
        Observable.__init__(self, observers)
        self.logger = logging.getLogger('System State')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

        self._start_time = datetime.datetime.now()
        self._next_cycle = datetime.datetime.now()
        self._system_state = "standby"
        self._last_temp = 0
        self._min_temp = 100
        self._max_temp = 0
        self.error_description = 'No recorded error.'
        self.error_time = None

        self._total_media_in = 0
        self._total_media_out = 0

        self._reactor_volume = REACTOR_VOLUME

        self._water_level_exceeded = False
        self._active_devices = []
        self._num_errors = 0
        self._num_warnings = 0
        self._cycle_data = CycleData(0)

    # Getters
    def get_last_temp(self) -> float:
        return self._last_temp

    def set_reactor_volume(self, vol: float) -> None:
        self._reactor_volume = vol

    def water_level_exceeded(self) -> bool:
        return self._water_level_exceeded


    def get_reactor_volume(self) -> float:
        return self._reactor_volume

    def get_start_time(self) -> datetime.datetime:
        return self._start_time

    def get_uptime(self) -> str:
        ut = datetime.datetime.now() - self._start_time
        days = ut.days
        hours = ut.seconds // 60 ** 2
        mins = (ut.seconds - hours * 60 ** 2) / 60

        return "{days:02.0f}:{hours:02.0f}:{minutes:02.0f}".format(
            days=ut.days,
            hours=hours,
            minutes=mins
        )

    def get_max_temp(self) -> float:
        return self._max_temp

    def set_error_state(self, error_description: str) -> None:
        self._system_state = 'error'
        self.error_description = error_description
        self.error_time = datetime.datetime.now()
        self.notify_observers()

    def get_min_temp(self) -> float:
        return self._min_temp

    def get_total_media_in(self) -> float:
        return self._total_media_in

    def get_total_media_out(self) -> float:
        return self._total_media_out

    def begin_media_cycle(self) -> None:
        if not self._in_error_state():
            self._system_state = 'media_exchange'

    def end_media_cycle(self) -> None:
        if not self._in_error_state():
            self._system_state = 'standby'

    def in_error_state(self) -> bool:
        return self._system_state == 'error'

    def get_time_until_next_media_cycle(self) -> str:
        ut = self._next_cycle - datetime.datetime.now()
        mins = ut.seconds // 60
        secs = ut.seconds - mins * 60

        return "{mins:02.0f}:{secs:02.0f}".format(
            mins=mins,
            secs=secs
        )

    def set_next_cycle(self, next_cycle: datetime.datetime) -> None:
        self._next_cycle = next_cycle

    def get_cycle_data(self) -> CycleData:
        return self._cycle_data

    def get_state(self) -> str:
        return self._system_state

    def _in_error_state(self) -> bool:
        if self._system_state == 'error':
            self.logger.warning("System tried to exit error state.")
            return False

    def get_active_device_names(self) -> List[str]:
        return [device.get_name() for device in self._active_devices]

    def update_dispensed_volumes(self) -> None:
        if self._cycle_data.state != "done":
            raise ValueError("Expected Cycle to be complete, instead it was \""
                             + self._cycle_data.state + "\"")
        self._total_media_in += self._cycle_data.get_in_vol()
        self._total_media_out += self._cycle_data.get_out_vol()
        self._cycle_data.state = "inactive"

    def notify(self, observable: Any) -> None:
        """Handle incoming changes to system state, inform observers that system
        state has changed."""
        if isinstance(observable, Device):
            self._notify_device(observable)
        elif isinstance(observable, Sensor):
            self._notify_sensor(observable)
        else:
            raise ValueError("Unrecognised observable: " + str(observable))

        # Inform observers that system state has changed.
        self.notify_observers()

    def _notify_device(self, observable: Device) -> None:
        """Handle a notification from a device."""
        if observable.is_on():
            if observable in self._active_devices:
                self.logger.warning(observable.get_name() +
                                    " was double activated.")
            else:
                self._active_devices.append(observable)
        else:
            if observable not in self._active_devices:
                self.logger.warning(observable.get_name() +
                                    " was double de-activated.")
            else:
                self._active_devices.remove(observable)

    def _notify_sensor(self, observable: Sensor) -> None:
        if isinstance(observable, TemperatureSensor):
            self._last_temp = observable.last_reading
            self.logger.debug("Temperature updated to " + str(self._last_temp)
                             + ".")
            if self._last_temp < self._min_temp:
                self._min_temp = self._last_temp
                self.logger.info("New min temp : " + str(self._min_temp))
            if self._last_temp > self._max_temp:
                self._max_temp = self._last_temp
                self.logger.info("New max temp : " + str(self._max_temp))

        elif isinstance(observable, WaterLevelSensor):
            self._water_level_exceeded = observable.last_reading
            self.logger.debug("Water level updated to " +
                             str(self._water_level_exceeded) + ".")
        else:
            raise ValueError("Unknown sensor type:" + str(observable))


# === Thermal Regulation Constants ===
