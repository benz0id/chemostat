import datetime
import logging
from abc import ABC, abstractmethod
from time import sleep
from typing import Any, List

from src import log_config
from src.global_constants import *
from src.device import Device
from src.presenters import lcd_driver
from src.presenters.lcd_driver import lcd
from src.sensor import Sensor


class Presenter(ABC):
    @abstractmethod
    def test(self) -> None:
        pass


handler = logging.FileHandler('logs/presenters.log')
handler.setFormatter(log_config.basic_formatter)


class LCD(Presenter):
    """
    An LCD meant to visualise system data.

    === Private Attributes ===

    mode: what to visualise on the display.

        === Modes ===

        basic - simple diagnostic information, including:
        > chemostat status
        > temperature
        > uptime
        > next cycle time

        debug - code operation logs
        > number of warnings
        > number of errors

    system_state: stores attributes of the system for presentation.

    screen_state: The text displayed on the screen.

    lcd_driver: The lcd screen to which this class presenters.
    """
    logger: logging.Logger

    _screen_state: List[str]
    _lcd_driver: lcd_driver.lcd

    def __init__(self) -> None:
        """Initialize the LCD to a basic state."""
        super().__init__()
        self.logger = logging.getLogger('LCD')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self._screen_state = [''] * LCD_NROW
        self._lcd_driver = lcd()
        self.test()

    def update_screen(self) -> None:
        """Updates the screen to the current <screen_state>"""
        in_rows = len(self._screen_state) <= 4
        in_cols = all([len(row) <= LCD_NROW for row in self._screen_state])
        if not in_cols or not in_rows:
            for row in range(LCD_NROW):
                self._lcd_driver.lcd_display_string(self._screen_state[row],
                                                    row)
        return

    def test(self) -> None:
        """Do a quick test of the LCD. Saves initial state"""
        save_state = self._screen_state
        if DEBUG_MODE:
            for i in range(LCD_NCOL):
                char = ["/", '|', '\\', '-'][i % 3]
                self._screen_state = ['' * i + char + '' * (LCD_NCOL - i)] * 4
                self.update_screen()
                sleep(0.1)
        self._screen_state = save_state
        self.update_screen()


if __name__ == "__main__":
    LCD()
