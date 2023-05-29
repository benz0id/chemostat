from src.media_controller import MediaExchangeController
from src.device_manager import DeviceManager
from src.presenters.presenters import LCD
from src.sensor_manager import SensorManager
from src.system_status import SystemInfoManager


class Builder:
    """Builds all managers, presenters, and controllers."""
    def __init__(self):
        self.lcd = LCD()

        self.sys_info = SystemInfoManager([self.lcd])
        self.dm = DeviceManager(self.sys_info)
        self.sm = SensorManager(self.sys_info, self.dm)

        self.mc = MediaExchangeController(None, 0.17, 6, self.sys_info, self.dm, self.sm)


