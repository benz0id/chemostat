import time
import src.log_config as log_config
from src.controller_builder import Builder
import src.gpio_adapter
import src.handle_signals
from src.global_constants import *

def main():
    log_config.config_loggers()
    src.handle_signals.config_signals()

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
    except Exception as e:
        src.gpio_adapter.get_GPIO().cleanup()
        src.gpio_adapter.get_GPIO().setmode(src.gpio_adapter.get_GPIO().BCM)
        Builder().dm.shutdown()
        src.gpio_adapter.get_GPIO().cleanup()
        raise e




