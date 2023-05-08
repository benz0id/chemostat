import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any, List
from global_constants import *
from src.device import Device
from src.observe import Observer, Observable
from src.sensor import Sensor



handler = logging.FileHandler('logs/system_status.log')
handler.setFormatter(LOG_FORMAT)


class SystemData(Observer, Observable):
    """ Stores and collects dynamic properties of the system.

    === Private Attributes ===

    start_time: time at which the program began running

    last_temp: the last recorded temperature

    active_devices: all devices that are currently running

    system_state: the state of the system

    num_warnings: number of warnings produced throughout the program's operation

    num_errors: the number of errors that have occurred throughout the programs
        operation.
    """
    logger: logging.Logger

    _start_time: datetime.datetime
    _last_temp: float
    _active_devices: List[Device]
    _system_state: str
    # TODO
    _num_warnings: int
    _num_errors: int

    def __init__(self, observers: List[Observer]) -> None:
        Observable.__init__(self, observers)
        self.logger = logging.getLogger('System State')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

        self._start_time = datetime.datetime.now()
        self._system_state = STANDARD
        self._last_temp = 0
        self._active_devices = []
        self._num_errors = 0
        self._num_warnings = 0

    # Getters
    def get_last_temp(self) -> float:
        return self._last_temp

    def get_uptime(self):
        return datetime.datetime.now() - self._start_time

    def get_active_device_names(self) -> List[str]:
        return [device.get_name() for device in self._active_devices]



    def notify(self, observable: Any) -> None:
        """Handle incoming changes to system state, inform observers that system
        state has changed."""
        if isinstance(observable, Device):
            self._notify_device(observable)
        elif isinstance(observable, Sensor):
            self._notify_sensor(observable)
        else:
            raise ValueError("Unrecognised observable")

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

    def _notify_sensor(self, notifier: Sensor) -> None:
        pass