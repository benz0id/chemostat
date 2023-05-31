from src.bubbler_regulation import BubblerController
from src.media_controller import MediaExchangeController
from src.device_manager import DeviceManager
from src.presenters.presenters import LCD, ConsolePresenter
from src.sensor_manager import SensorManager
from src.system_status import SystemInfoManager
from src.global_constants import *
from src.thermal_regulation import ThermalRegulationController


class Builder:
    """Builds all managers, presenters, and controllers."""
    def __init__(self, presenters: bool = True):
        if presenters:
            self.lcd = LCD()
            lst = [self.lcd]
        else:
            lst = []

        self.sys_info = SystemInfoManager(lst)
        self.dm = DeviceManager(self.sys_info)
        self.sm = SensorManager(self.sys_info, self.dm)

        self.mc = MediaExchangeController(REACTOR_VOLUME,
                                          MEDIA_FLOW_RATE,
                                          CYCLES_PER_HOUR,
                                          self.sys_info, self.dm, self.sm)

        self.bc = BubblerController(self.sys_info, self.dm, self.sm)
        self.tc = ThermalRegulationController(self.sys_info, self.dm, self.sm)

        if presenters:
            self.monitor = ConsolePresenter(self.dm, self.sm, self.mc)
            self.sys_info.add_observer(self.monitor)



