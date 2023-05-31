import argparse
from time import sleep

import src.handle_signals
import src.log_config as log_config
from src.controller_builder import Builder
import src.gpio_adapter
from src.global_constants import *

def main():
    parser = argparse.ArgumentParser(
        prog='pumps_manual',
        description='turn on the pumps for a given amount of time.')

    parser.add_argument('-i', '--inlet', type=int,
                        help='mls to pump into the reactor.',
                        default=0)

    parser.add_argument('-o', '--outlet', type=int,
                        help='mls to pump out of the reactor.',
                        default=0)

    args = parser.parse_args()

    src.handle_signals.config_signals()
    log_config.config_loggers()

    builder = Builder(presenters=False)

    if args.outlet > 0:
        print(f'Removing {args.outlet}ml from the reactor.')
        builder.dm.turn_on_outlet()
        sleep(args.outlet / MEDIA_OUT_FLOWRATE)
        print('Turning off outlet')
        builder.dm.turn_off_outlet()

    if args.inlet > 0:
        print(f'Adding {args.outlet}ml to the reactor.')
        builder.dm.turn_on_inlet()
        sleep(args.inlet / MEDIA_IN_FLOWRATE)
        print('Turning off inlet')
        builder.dm.turn_off_inlet()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        src.gpio_adapter.get_GPIO().cleanup()
        Builder()
        raise e




