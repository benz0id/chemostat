from src.media_controller import MediaExchangeController
from src.device_manager import DeviceManager
from src.presenters.presenters import LCD
from src.sensor_manager import SensorManager
from src.system_status import SystemInfoManager
from src.global_constants import *


class Builder:
    """Builds all managers, presenters, and controllers."""
    def __init__(self):
        self.lcd = LCD()

        self.sys_info = SystemInfoManager([self.lcd])
        self.dm = DeviceManager(self.sys_info)
        self.sm = SensorManager(self.sys_info, self.dm)

        self.mc = MediaExchangeController(REACTOR_VOLUME,
                                          MEDIA_FLOW_RATE,
                                          CYCLES_PER_HOUR,
                                          self.sys_info, self.dm, self.sm)


