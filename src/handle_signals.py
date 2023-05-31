import signal
import src.gpio_adapter
import logging

def clear_gpio(signum, frame):
    src.gpio_adapter.get_GPIO().cleanup()
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    exit(signum)

def config_signals() -> None:
    signal.signal(signal.SIGINT, clear_gpio)
    signal.signal(signal.SIGTERM, clear_gpio)
