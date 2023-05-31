import argparse
from time import sleep

import src.log_config as log_config
from src.controller_builder import Builder
import src.gpio_adapter

def main():
    parser = argparse.ArgumentParser(
        prog='uv_led',
        description='turn on the UV led for a given amount of time.')

    parser.add_argument('ontime', type=int, help='time to turn the UV led on for')

    args = parser.parse_args()

    log_config.config_loggers()

    builder = Builder(presenters=False, controllers=False)

    print(f'Turning on UV LED for {args.ontime} seconds.')
    builder.dm.turn_on_uv_led()
    sleep(args.ontime)
    print('Turning off UV LED')
    builder.dm.turn_off_uv_led()
    return

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        src.gpio_adapter.get_GPIO().cleanup()
        Builder()
        raise e




