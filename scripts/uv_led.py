import src.log_config as log_config
from src.controller_builder import Builder
import src.gpio_adapter

def main():
    log_config.config_loggers()

    builder = Builder()
    builder



if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        src.gpio_adapter.get_GPIO().cleanup()
        Builder()
        raise e




