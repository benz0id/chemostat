import time
import src.log_config as log_config
from src.controller_builder import Builder
import src.gpio_adapter
from src.global_constants import *

def main():
    log_config.config_loggers()

    builder = Builder()

    while True:
        builder.mc.cycle_check()
        builder.sm.update_readings()
        builder.tc.regulate_temp()
        builder.bc.regulate_airflow()
        time.sleep(FAST_PAUSE_TICK)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        src.gpio_adapter.get_GPIO().cleanup()
        Builder()




