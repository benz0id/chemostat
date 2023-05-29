from abc import ABC, abstractmethod
from time import sleep
from typing import Any, List

from src import log_config
from src.global_constants import *
from src.observe import Observable, Observer
from src.presenters import lcd_driver
from src.presenters.lcd_driver import lcd
from src.system_status import SystemInfoManager

def seconds_since(dt: datetime.datetime) -> float:
    return (datetime.datetime.now() - dt).total_seconds()

class Presenter(ABC):
    @abstractmethod
    def test(self) -> None:
        pass


handler = logging.FileHandler('logs/presenters.log')
handler.setFormatter(log_config.get_basic_formatter())


class LCD(Presenter, Observer):
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

        cycle - display progress through media cycling, including:
        > vol media added
        > vol media removed
        > time

    system_state: stores attributes of the system for presentation.

    screen_state: The text displayed on the screen.

    lcd_driver: The lcd screen to which this class presenters.
    """
    logger: logging.Logger

    _screen_state: List[str]
    _lcd_driver: lcd_driver.lcd
    _last_refresh: datetime

    def __init__(self) -> None:
        """Initialize the LCD to a basic state."""
        super().__init__()
        self.logger = logging.getLogger('LCD')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self._screen_state = [''] * LCD_NROW
        self._lcd_driver = lcd()
        self._last_refresh = datetime.datetime.now()

    def update_screen(self) -> None:
        """Updates the screen to the current <screen_state>"""
        in_rows = len(self._screen_state) <= LCD_NROW
        in_cols = all([len(row) <= LCD_NCOL for row in self._screen_state])
        if not in_cols or not in_rows:
            self.logger.warning("LCD text is beyond screen bounds. Offending text:" +
                                '\n\t' + '\n\t'.join(self._screen_state))

        self.logger.info("Printing to screen:" +
                         '\n\t' + '\n\t'.join(self._screen_state))
        for row in range(LCD_NROW):
            self._lcd_driver.lcd_display_string(self._screen_state[row],
                                                    row + 1)
        return

    def test(self) -> None:
        """Do a quick test of the LCD. Saves initial state"""
        save_state = self._screen_state
        if DEBUG_MODE:
            for i in range(LCD_NCOL):
                char = ["/", '|', '\\', '-'][i % 4]
                self._screen_state = [' ' * i + char + ' ' * (LCD_NCOL - i - 1)] * 4
                self.update_screen()
                sleep(0.5)
        self._screen_state = save_state
        self.update_screen()

    def notify(self, sys_info: Observable) -> None:
        """Updates the screen using the information in the system state manager.
        """
        if not isinstance(sys_info, SystemInfoManager):
            raise ValueError('Expected SystemInfoManager, not ' + str(sys_info))

        # Do not update screen; not enough time has passed since last refresh.
        if seconds_since(self._last_refresh) < LCD_REFRESH_PERIOD:
            return
        self._last_refresh = datetime.datetime.now()

        if sys_info.get_state() == "standby":
            self.display_system_info(sys_info)
        elif sys_info.get_state() == "media_exchange":
            self.display_media_exchange_info(sys_info)
        elif sys_info.get_state() == "error":
            self.display_error_state(sys_info)
        else:
            raise ValueError("Unrecognised system state : " +
                             sys_info.get_state())


    def display_system_info(self, sys_info: SystemInfoManager) -> None:
        """Displays basic system info. in the following format.

        # ____________________
        # Cur %% Min %% Max %%
        # In %%.%%L Out %%.%%L
        # Next cycle: %%:%%
        # Uptime %%:%%:%%
        """

        self._screen_state = [
            "cur {cur_temp:.0f} min {min_temp:.0f} max {max_temp:.0f}".format(
                cur_temp=sys_info.get_last_temp(),
                min_temp=sys_info.get_min_temp(),
                max_temp=sys_info.get_max_temp()
            ),
            "in {in_vol:2.2f}L out {out_vol:2.2f}L".format(
                in_vol=sys_info.get_total_media_in() / 1000,
                out_vol=sys_info.get_total_media_out() / 1000
            ),
            "next cycle: " + sys_info.get_time_until_next_media_cycle(),
            "uptime: " + sys_info.get_uptime()
        ]

        self.update_screen()

    def display_media_exchange_info(self, sys_info: SystemInfoManager) -> None:
        """
        Displays information regarding the current media exchange cycle in the
        following format.

        # ____________________
        # Target Vol: %%.%%mL
        # Volume In : %%.%%ml
        # Volume Out: %%.%%ml
        # State - %%%%% Cur %%
        """
        cd = sys_info.get_cycle_data()
        self._screen_state = [
            "Target Vol: {:02.2f}mL".format(cd.get_targ_exchange_vol()),
            "Volume In : {:02.2f}ml".format(cd.get_in_vol()),
            "Volume Out: {:02.2f}ml".format(cd.get_out_vol()),
            "State - " + (cd.state + '     ')[:5] +
            ' Cur ' + "{:2.0f}".format(
                sys_info.get_last_temp())
        ]

        self.update_screen()

    def display_error_state(self, sys_info: SystemInfoManager) -> None:
        """
        Displays information regarding the current error in the
        following format.

        # ____________________
        # Error: Time
        # <error desc>
        # <error desc>
        # <error desc>
        """

        lines = ['']
        curr = 0
        i = 0

        for word in sys_info.error_description.strip().split(' '):
            if len(word) + curr <= 20:
                lines[i] += ' ' + word
                curr += len(word) + 1
            else:
                lines.append(word)
                i += 1
                curr = len(word)

        lines.insert(0, sys_info.error_time.strftime("%m/%d/%Y %H:%M:%S"))

        self._screen_state = lines
        self.update_screen()


if __name__ == "__main__":
    lcd = LCD()
    lcd.test()

