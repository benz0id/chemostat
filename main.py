import time
import src.log_config as log_config
from src.controller_builder import Builder
from src.global_constants import *

log_config.config_loggers()

builder = Builder()

while True:
    builder.mc.cycle_check()
    builder.sm.update_readings()
    time.sleep(FAST_PAUSE_TICK)



