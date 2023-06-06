import datetime
import logging
from time import sleep
from typing import List

from src import log_config
from src.device import Device, PeristalticPump, IndicatorLED
from src.global_constants import DEBUG_MODE, MEDIA_IN_FLOWRATE, \
    MEDIA_OUT_FLOWRATE, SUPPLEMENTAL_MEDIA_IN_FLOWRATE, HIGH, UV_LED_ON
from src.observe import Observer
from src.pinout import RED_LED_PIN, BLUE_LED_PIN, YELLOW_LED_PIN, GREEN_LED_PIN, \
    UV_LED_PIN, MEDIA_IN_PIN, MEDIA_OUT_PIN, SUPPLEMENTAL_MEDIA_IN_PIN, \
    HOTPLATE_PIN
from src.system_status import SystemInfoManager


handler = logging.FileHandler('logs/device_manager.log')
handler.setFormatter(log_config.get_basic_formatter())


class DeviceManager:
    """Enables management of devices such as motors and relays.

    === Devices ===

    media_in_pump: Inlet pump for fresh media

    media_out_pump: Outlet pump

    supplemental_media_pump: Inlet pump for supplemental media

    hotplate: Controls agitation and temperature.
    """
    logger: logging.Logger
    sys_info: SystemInfoManager

    devices: List[Device]

    _media_in_pump: PeristalticPump
    _media_out_pump: PeristalticPump
    _air_pump: PeristalticPump

    _hotplate: Device

    red_led: IndicatorLED
    blue_led: IndicatorLED
    yellow_led: IndicatorLED
    green_led: IndicatorLED
    _uv_led: Device

    _hotplate_ontime: datetime.timedelta
    _media_in_pump_ontime: datetime.timedelta
    _media_out_pump_ontime: datetime.timedelta
    _air_pump_ontime: datetime.timedelta

    _hotplate_start_time: datetime.datetime
    _media_in_pump_start_time: datetime.datetime
    _media_out_pump_start_time: datetime.datetime
    _air_pump_start_time: datetime.datetime

    def __init__(self, sys_info: Observer):
        # Configure Logger.
        self.logger = logging.getLogger('Device Manager')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.sys_info = sys_info

        self.devices = []

        self.configure_leds()
        self.configure_pumps()
        self.configure_hotplate()

        self.runtest(self.devices, t=0.1)

        self._hotplate_ontime = datetime.timedelta(seconds=0)
        self._media_in_pump_ontime = datetime.timedelta(seconds=0)
        self._media_out_pump_ontime = datetime.timedelta(seconds=0)
        self._air_pump_ontime = datetime.timedelta(seconds=0)
        self._uv_led_ontime = datetime.timedelta(seconds=0)

        self._hotplate_start_time = datetime.datetime.now()
        self._media_in_pump_start_time = datetime.datetime.now()
        self._media_out_pump_start_time = datetime.datetime.now()
        self._uv_led_start_time = datetime.datetime.now()

    def runtest(self, devices: List[Device], t: float = 1):
        if DEBUG_MODE:
            for device in devices:
                device.on()
                sleep(t)
                device.off()
                sleep(t)

    def configure_leds(self):
        self.red_led = IndicatorLED("Red LED", RED_LED_PIN, [self.sys_info])
        self.blue_led = IndicatorLED("Blue LED", BLUE_LED_PIN, [self.sys_info])
        self.yellow_led = IndicatorLED("Yellow LED", YELLOW_LED_PIN, [self.sys_info])
        self.green_led = IndicatorLED("Green LED", GREEN_LED_PIN, [self.sys_info])
        self._uv_led = IndicatorLED("Ultra-Violet LED", UV_LED_PIN, [self.sys_info])

        if UV_LED_ON:
            self._uv_led.on()

        leds = [self.red_led,
                self.blue_led,
                self.yellow_led,
                self.green_led]
        self.runtest(leds)
        self.devices.extend(leds)

    def configure_pumps(self):
        """Configure the pumps."""
        self._media_in_pump = PeristalticPump("Media Inlet Pump", MEDIA_IN_PIN,
                                              MEDIA_IN_FLOWRATE,
                                              [self.sys_info])
        self._media_out_pump = PeristalticPump("Media Outlet Pump",
                                               MEDIA_OUT_PIN,
                                               MEDIA_OUT_FLOWRATE,
                                               [self.sys_info])
        self._air_pump = \
            PeristalticPump("Supplemetal Media Inlet Pump",
                            SUPPLEMENTAL_MEDIA_IN_PIN,
                            SUPPLEMENTAL_MEDIA_IN_FLOWRATE,
                            [self.sys_info])
        pumps = [self._media_in_pump,
                 self._media_out_pump,
                 self._air_pump]
        self.runtest(pumps)
        self.devices.extend(pumps)

    def turn_on_hotplate(self) -> None:
        if not self._hotplate.is_on():
            self._hotplate_start_time = datetime.datetime.now()
        self._hotplate.on()

    def turn_off_hotplate(self) -> None:
        self._hotplate_ontime += datetime.datetime.now() - \
                                 self._hotplate_start_time
        self._hotplate.off()

    def turn_on_inlet(self) -> None:
        if not self._media_in_pump.is_on():
            self._media_in_pump_start_time = datetime.datetime.now()
        self._media_in_pump.on()

    def turn_off_inlet(self) -> None:
        self._media_in_pump_ontime += datetime.datetime.now() - \
                                      self._media_in_pump_start_time
        self._media_in_pump.off()

    def turn_on_outlet(self) -> None:
        if not self._media_out_pump.is_on():
            self._media_out_pump_start_time = datetime.datetime.now()
        self._media_out_pump.on()

    def turn_off_outlet(self) -> None:
        self._media_out_pump_ontime += datetime.datetime.now() - \
                                       self._media_out_pump_start_time
        self._media_out_pump.off()

    def turn_on_air_pump(self) -> None:
        if not self._air_pump.is_on():
            self._air_pump_start_time = datetime.datetime.now()
        self._air_pump.on()

    def turn_off_air_pump(self) -> None:
        self._air_pump_ontime += datetime.datetime.now() - \
                                 self._air_pump_start_time
        self._air_pump.off()

    def shutdown(self) -> None:
        """Only use before terminating the program. Not reccomended during
        standard operation."""
        for device in self.devices:
            device.off()

    def outlet_is_on(self) -> bool:
        return self._media_out_pump.is_on()

    def inlet_is_on(self) -> bool:
        return self._media_in_pump.is_on()

    def hotplate_is_on(self) -> bool:
        return self._hotplate.is_on()

    def air_pump_is_on(self) -> bool:
        return self._air_pump.is_on()

    def get_inlet_ontime(self) -> float:
        if self._media_in_pump.is_on():
            add_ontime = (datetime.datetime.now() -
                          self._media_in_pump_start_time).total_seconds()
            return self._media_in_pump_ontime.total_seconds() + add_ontime
        else:
            return self._media_in_pump_ontime.total_seconds()

    def get_outlet_ontime(self) -> float:
        if self._media_out_pump.is_on():
            add_ontime = (datetime.datetime.now() -
                          self._media_out_pump_start_time).total_seconds()
            return self._media_out_pump_ontime.total_seconds() + add_ontime
        else:
            return self._media_out_pump_ontime.total_seconds()

    def get_air_pump_ontime(self) -> float:
        if self._air_pump.is_on():
            add_ontime = (datetime.datetime.now() -
                          self._air_pump_start_time).total_seconds()
            return self._air_pump_ontime.total_seconds() + add_ontime
        else:
            return self._air_pump_ontime.total_seconds()

    def get_hotplate_ontime(self) -> float:
        if self._hotplate.is_on():
            add_ontime = (datetime.datetime.now() -
                          self._hotplate_start_time).total_seconds()
            return self._hotplate_ontime.total_seconds() + add_ontime
        else:
            return self._hotplate_ontime.total_seconds()


    def uv_led_is_on(self) -> bool:
        return self._uv_led.is_on()

    def get_uv_led_ontime(self) -> float:
        if self._uv_led.is_on():
            add_ontime = (datetime.datetime.now() -
                          self._uv_led_start_time).total_seconds()
            return self._uv_led_ontime.total_seconds() + add_ontime
        else:
            return self._uv_led_ontime.total_seconds()

    def turn_on_uv_led(self) -> None:
        if not self._uv_led.is_on():
            self._uv_led_start_time = datetime.datetime.now()
        self._uv_led.on()

    def turn_off_uv_led(self) -> None:
        self._uv_led_ontime += datetime.datetime.now() - \
                                 self._uv_led_start_time
        self._uv_led.off()






    def configure_hotplate(self):
        """Configure the hotplate."""
        self._hotplate = Device('hotplate', HOTPLATE_PIN, HIGH,
                                observers=[self.sys_info])
        self.runtest([self._hotplate])
        self.devices.append(self._hotplate)
