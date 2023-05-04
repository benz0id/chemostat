import logging
import threading
from abc import ABC, abstractmethod
from time import sleep

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

    def add_pumps(self):


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

    def on(self, seconds: float = None) -> None:
        """Turn on the device."""
        if seconds:
            self.on_for(seconds)
            return

        if self._is_on:
            self.logger.warning("Attempting to turn on " + self._name +
                                " while it is already turned on.")

        self.logger.info("Turning on device.")
        GPIO.output(self._pin, self._on_sig)

    def off(self, seconds: float = None) -> None:
        """Turn off the device."""
        if seconds:
            self.off_for(seconds)
            return

        if self._is_on:
            self.logger.warning("Attempting to turn off " + self._name +
                                " while it is already turned off.")
        self.logger.info("Turning off device.")
        GPIO.output(self._pin, self._off_sig)

    def _on_for(self, seconds: float) -> None:
        """Turn on the device for <seconds>. Non-blocking. Should only be used
        when the device is off."""

        def on_for_dur(seconds: float) -> None:
            self.logger.info('Turning on device and waiting ' + str(seconds) +
                             'before turning it off.')
            self.on()
            sleep(seconds)
            self.logger.info( str(seconds) + 'have passed. Turning device off.')
            self.off()

        logging.info('Starting thread...')
        x = threading.Thread(target=on_for_dur, args=(seconds,))
        x.start()

        return

    def _off_for(self, seconds: float) -> None:
        """Turn off the device for <seconds>. Non-blocking. Should only be used
        when the device is on."""

        def off_for_dur(seconds: float) -> None:
            self.logger.info('Turning off device and waiting ' + str(seconds) +
                             'before turning it on.')
            self.off()
            sleep(seconds)
            self.logger.info(str(seconds) + 'have passed. Turning device on.')
            self.on()

        logging.debug('Starting thread...')
        x = threading.Thread(target=off_for_dur, args=(seconds,))
        x.start()

        return


class PeristalticPump(Device):
    """A peristaltic pump that can be used to dispense a known amount of fluid.


    === Private Attributes ===
    _mls_p_s

    """
    _mls_p_s: float

    def __init__(self, name: str, pin: int, ml_p_s: float) -> None:
        """
        Initialise a pump using the given attributes.;
        :param name: the name of this pump
        :param pin: the GPIO pin to which this pump is attached
        :param ml_p_s: millimeters of fluid moved in one second
        """
        super().__init__(name, pin, HIGH)
        self._mls_p_s = ml_p_s

    def dispense(self, mls: float) -> None:
        """Dispense the given amount of liquid by running the pump for the
        correct amount of time."""
        time = mls / self._mls_p_s

        self.logger.info("Running " + self._name + " for " +
                         "{.2f}".format(time) + " seconds to pump" +
                         "{.2f}".format(mls) + "mls of fluid")

        self.on(time)








