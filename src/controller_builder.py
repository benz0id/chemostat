from src.controllers import MediaExchangeController
from src.device import DeviceManager
from src.presenters.presenters import LCD
from src.sensor import SensorManager
from src.system_status import SystemInfoManager


class Builder:
    """Builds all managers, presenters, and controllers."""
    lcd = LCD()

    sys_info = SystemInfoManager([lcd])
    dm = DeviceManager(sys_info)
    sm = SensorManager(sys_info, dm)

    mc = MediaExchangeController(500, 0.17, 6, sys_info, dm, sm)


