import logging
from abc import ABC, abstractmethod
from global_constants import *
from pinout import *
import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BCM)

handler = logging.FileHandler('logs/device_control.log')
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
handler.setFormatter(formatter)


class DeviceManager:
    """Enables management of devices such as motors and relays.

    === Current Devices ===



    """

    logger = logging.getLogger('Device Manager')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    def __init__(self):
        pass


class Device:
    """A simple device that can be toggled on or off.

    === Private Attributes ===

    name: The device's name.

    pin: The GPIO pin to which this device is connected.

    is_on: Whether the device is currently turned on.

    on_sig: The signal to send to turn on the device.

    off_sig: The signal to send to turn off the device.
    """

    logger: logging.Logger

    _name: str
    _pin: int
    _is_on: bool
    _on_sig: bool
    _off_sig: bool

    def __init__(self, name: str, pin: int, on_sig=HIGH) -> None:
        self._name = name
        self._is_on = False
        self._pin = pin
        self._on_sig = on_sig
        self._off_sig = not on_sig
        GPIO.setup(pin, GPIO.OUT, initial=self._off_sig)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

























    # TODO
    def is_on(self) -> bool:
        """Returns whether the device is currently on."""
        return self._is_on

    def on(self) -> None:
        """Turn on the device."""
        GPIO.output(self._pin, self._on_sig)

    def off(self) -> None:
        """Turn off the device."""
        GPIO.output(self._pin, self._off_sig)

    def on_for(self, seconds: float) -> None:
        """Turn on the device for <seconds>. Non-blocking. Should only be used
        when the device is off."""
        assert not self._is_on

        pass

    def off_for(self, seconds: float) -> None:
        """Turn off the device for <seconds>. Non-blocking. Should only be used
        when the device is on."""
        assert self._is_on
        pass


class PeristalticPump(Device):
    """A peristaltic pump that can be used to dispense a known amount of fluid.
    """

    def __init__(self, pin: int) -> None:
        super().__init__(pin)

    def dispense(self, ml: float) -> None:
        """Dispense the given amount of liquid by running the pump for the
        correct amount of time."""





