import logging
from time import sleep
from typing import List

from src import log_config
from src.device import Device, PeristalticPump, IndicatorLED
from src.global_constants import DEBUG_MODE, MEDIA_IN_FLOWRATE, \
    MEDIA_OUT_FLOWRATE, SUPPLEMENTAL_MEDIA_IN_FLOWRATE, HIGH
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

    media_in_pump: PeristalticPump
    media_out_pump: PeristalticPump
    supplemental_media_pump: PeristalticPump

    hotplate: Device

    red_led: IndicatorLED
    blue_led: IndicatorLED
    yellow_led: IndicatorLED
    green_led: IndicatorLED
    uv_led: Device

    def __init__(self, sys_info: SystemInfoManager):
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
        self.uv_led = IndicatorLED("Ultra-Violet LED", UV_LED_PIN, [self.sys_info])

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
                                             [self.sys_info])
        self.media_out_pump = PeristalticPump("Media Outlet Pump",
                                              MEDIA_OUT_PIN,
                                              MEDIA_OUT_FLOWRATE,
                                              [self.sys_info])
        self.supplemental_media_pump = \
            PeristalticPump("Supplemetal Media Inlet Pump",
                            SUPPLEMENTAL_MEDIA_IN_PIN,
                            SUPPLEMENTAL_MEDIA_IN_FLOWRATE,
                            [self.sys_info])
        pumps = [self.media_in_pump,
                 self.media_out_pump,
                 self.supplemental_media_pump]
        self.runtest(pumps)
        self.devices.extend(pumps)

    def configure_hotplate(self):
        """Configure the hotplate."""
        self.hotplate = Device('hotplate', HOTPLATE_PIN, HIGH,
                               observers=[self.sys_info])
        self.runtest([self.hotplate])
        self.devices.append(self.hotplate)
