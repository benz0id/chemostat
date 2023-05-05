import logging
import threading
import log_config
from abc import ABC, abstractmethod
from time import sleep
from typing import List, Any

from global_constants import *
from pinout import *
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

handler = logging.FileHandler('logs/device_control.log')
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
handler.setFormatter(formatter)


class DeviceObserver(ABC):
    """Some object that responds when a given device is turned off or on."""

    @abstractmethod
    def notify(self, sender: Any = None) -> None:
        pass


class Device(ABC):
    """A simple device that can be toggled on or off.

    === Private Attributes ===

    name: The device's name.

    pin: The GPIO pin to which this device is connected.

    is_on: Whether the device is currently turned on.

    on_sig: The signal to send to turn on the device.

    off_sig: The signal to send to turn off the device.

    === Public Attributes ===

    observers: List of observers to notify when this device is turned on or off.
    """

    logger: logging.Logger
    observers: List[DeviceObserver]

    _name: str
    _pin: int
    _is_on: bool
    _on_sig: bool
    _off_sig: bool

    def __init__(self, name: str, pin: int, on_sig=HIGH,
                 observers: List[DeviceObserver] = None) -> None:
        self._name = name
        self._is_on = False
        self._pin = pin
        self._on_sig = on_sig
        self._off_sig = not on_sig
        GPIO.setup(pin, GPIO.OUT, initial=self._off_sig)
        GPIO.output(self._pin, self._off_sig)
        if observers:
            self.observers = observers
        else:
            self.observers = []
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
            self._on_for(seconds)
            return

        if self._is_on:
            self.logger.warning("Attempting to turn on " + self._name +
                                " while it is already turned on.")

        self.logger.info("Turning on device.")
        GPIO.output(self._pin, self._on_sig)
        for observer in self.observers:
            observer.notify(self)

    def off(self, seconds: float = None) -> None:
        """Turn off the device."""
        if seconds:
            self._off_for(seconds)
            return

        if self._is_on:
            self.logger.warning("Attempting to turn off " + self._name +
                                " while it is already turned off.")
        self.logger.info("Turning off device.")
        GPIO.output(self._pin, self._off_sig)
        for observer in self.observers:
            observer.notify(self)

    def _on_for(self, seconds: float) -> None:
        """Turn on the device for <seconds>. Non-blocking. Should only be used
        when the device is off."""

        def on_for_dur(seconds: float) -> None:
            self.logger.info('Turning on ' + self._name + ' and waiting ' +
                             str(seconds) + ' seconds before turning it off.')
            self.on()
            sleep(seconds)
            self.logger.info(str(seconds) + ' seconds have passed. Turning ' +
                             self._name + ' off.')
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


class IndicatorLED(Device, DeviceObserver):
    """An indicator LED that turns on when the device it is observing is
    activated."""

    def __init__(self, name: str, pin: int) -> None:
        """
        Initialise an LED using the given attributes.;
        :param name: the name of this led
        :param pin: the GPIO pin to which this led is attached
        """
        super().__init__(name, pin, HIGH)

    def notify(self, sender: Any = Device) -> None:
        if sender.is_on():
            self.on()
        else:
            self.off()


class PeristalticPump(Device):
    """A peristaltic pump that can be used to dispense a known amount of fluid.

    === Private Attributes ===
    _mls_p_s

    """
    _mls_p_s: float

    def __init__(self, name: str, pin: int, ml_p_s: float,
                 observers: List[Any] = None) -> None:
        """
        Initialise a pump using the given attributes.;
        :param name: the name of this pump
        :param pin: the GPIO pin to which this pump is attached
        :param ml_p_s: millimeters of fluid moved in one second
        """
        super().__init__(name, pin, LOW, observers)
        self._mls_p_s = ml_p_s

    def dispense(self, mls: float) -> None:
        """Dispense the given amount of liquid by running the pump for the
        correct amount of time."""
        time = mls / self._mls_p_s

        self.logger.info("Running " + self._name + " for " +
                         "{.2f}".format(time) + " seconds to pump" +
                         "{.2f}".format(mls) + "mls of fluid")
        self.on(time)


class DeviceManager:
    """Enables management of devices such as motors and relays.

    === Devices ===

    media_in_pump: Inlet pump for fresh media

    media_out_pump: Outlet pump

    supplemental_media_pump: Inlet pump for supplemental media

    hotplate: Controls agitation and temperature.
    """
    logger: logging.Logger

    devices: List[Device]

    media_in_pump: PeristalticPump
    media_out_pump: PeristalticPump
    supplemental_media_pump: PeristalticPump

    hotplate: Device

    red_led: IndicatorLED
    blue_led: IndicatorLED
    yellow_led: IndicatorLED
    green_led: IndicatorLED

    def __init__(self):
        # Configure Logger.
        self.logger = logging.getLogger('Device Manager')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.devices = []

        self.configure_leds()
        self.configure_pumps()
        self.configure_hotplate()

        self.runtest(self.devices, t=0.1)


    def runtest(self, devices: List[Device], t: float = 1):
        if DEBUG:
            for device in devices:
                device.on()
                sleep(t)
                device.off()
                sleep(t)

    def configure_leds(self):
        self.red_led = IndicatorLED("Red LED", RED_LED_PIN)
        self.blue_led = IndicatorLED("Blue LED", BLUE_LED_PIN)
        self.yellow_led = IndicatorLED("Yellow LED", YELLOW_LED_PIN)
        self.green_led = IndicatorLED("Green LED", GREEN_LED_PIN)
        leds = [self.red_led,
                self.blue_led,
                self.yellow_led,
                self.green_led]
        self.runtest(leds)
        self.devices.extend(leds)

    def configure_pumps(self):
        """Configure the pumps."""
        self.media_in_pump = PeristalticPump("Media Inlet Pump", MEDIA_IN_PIN,
                                             MEDIA_IN_FLOWRATE,
                                             [self.green_led])
        self.media_out_pump = PeristalticPump("Media Outlet Pump",
                                              MEDIA_OUT_PIN,
                                              MEDIA_OUT_FLOWRATE,
                                              [self.yellow_led])
        self.supplemental_media_pump = \
            PeristalticPump("Supplemetal Media Inlet Pump",
                            SUPPLEMENTAL_MEDIA_IN_PIN,
                            SUPPLEMENTAL_MEDIA_IN_FLOWRATE,
                            [self.blue_led])
        pumps = [self.media_in_pump,
                 self.media_out_pump,
                 self.supplemental_media_pump]
        self.runtest(pumps)
        self.devices.extend(pumps)

    def configure_hotplate(self):
        """Configure the hotplate."""
        self.hotplate = Device('hotplate', HOTPLATE_PIN, HIGH,
                               observers=[self.red_led])
        self.runtest([self.hotplate])
        self.devices.append(self.hotplate)


if __name__ == '__main__':
    dm = DeviceManager()
    GPIO.cleanup()
