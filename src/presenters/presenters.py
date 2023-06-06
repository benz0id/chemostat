import sys
import warnings
from abc import ABC, abstractmethod
from time import sleep
from typing import Any, List, Union

from src import log_config, gpio_adapter
from src.device_manager import DeviceManager
from src.global_constants import *
from src.media_controller import MediaExchangeController
from src.observe import Observable, Observer
from src.presenters import lcd_driver
from src.presenters.lcd_driver import lcd
from src.sensor_manager import SensorManager
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
    _lcd_driver: Union[lcd_driver.lcd, None]
    _last_refresh: datetime
    _last_state: str

    def __init__(self) -> None:
        """Initialize the LCD to a basic state."""
        super().__init__()
        self.logger = logging.getLogger('LCD')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self._screen_state = [''] * LCD_NROW
        try:
            self._lcd_driver = lcd()
        except IOError:
            self._lcd_driver = None
            print('Unable to detect LCD. Continuing operation'
                                    'without LCD.', sys.stderr)
            self.logger.warning('Unable to detect LCD. Continuing operation'
                                'without LCD.')

        self._last_refresh = datetime.datetime.now()
        self._last_state = ''

    def update_screen(self) -> None:
        """Updates the screen to the current <screen_state>"""
        in_rows = len(self._screen_state) <= LCD_NROW
        in_cols = all([len(row) <= LCD_NCOL for row in self._screen_state])
        if not in_cols or not in_rows:
            self.logger.warning(
                "LCD text is beyond screen bounds. Offending text:" +
                '\n\t' + '\n\t'.join(self._screen_state))

        self.logger.info("Printing to screen:" +
                         '\n\t' + '\n\t'.join(self._screen_state))
        for row in range(LCD_NROW):
            if self._lcd_driver:
                try:
                    self._lcd_driver.lcd_display_string(self._screen_state[row],
                                                        row + 1)
                except IOError:
                    print('Failed to print to LCD.', sys.stderr)
                    self.logger.warning('Failed to print to LCD.')
        return

    def test(self) -> None:
        """Do a quick test of the LCD. Saves initial state"""
        save_state = self._screen_state
        if DEBUG_MODE:
            for i in range(LCD_NCOL):
                char = ["/", '|', '\\', '-'][i % 4]
                self._screen_state = [' ' * i + char + ' ' * (
                            LCD_NCOL - i - 1)] * 4
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

        # Clear screens between modes.
        if sys_info.get_state() != self._last_state:
            self._last_state = sys_info.get_state()
            if self._lcd_driver:
                try:
                    self._lcd_driver.lcd_clear()
                except IOError:
                    print('Failed to clear LCD.', sys.stderr)
                    self.logger.warning('Failed to print to LCD.')

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


def format_seconds(seconds: float) -> str:
    td = datetime.timedelta(seconds=seconds)
    return format_td(td)

def format_td(timedelta: datetime.timedelta) -> str:
    days = timedelta.days
    hours = timedelta.seconds // 60 ** 2
    mins = (timedelta.seconds - hours * 60 ** 2) / 60

    return "{days:02.0f}:{hours:02.0f}:{minutes:02.0f}".format(
        days=days,
        hours=hours,
        minutes=mins
    )


class ConsolePresenter(Presenter, Observer):
    """Prints system information to the console.

    Format


    === System Statistics ===
    init: {init_datetime} | uptime: {uptime}
    media in: {media_in:.2f}ml | media out: {media_out:.2f}ml
    bubbler uptime: {bubbler_uptime}s | bubbler downtime: {bubbler_downtime}
    hotplate uptime: {hotplate_uptime}s | hotplate downtime {hotplate_downtime}
    vessel volume: {volume}ml | flow rate: {flow_rate} vol/hr
    cycle period {cycle_period}s | cycle exchange volume: {exchange_vol}mls

    === Sensor States ===
    water level: {wl_str}
    temperature: {temp}ml

    === Device Status ===
    inlet pump: {inlet_state}
    outlet pump: {outlet_state}
    bubbler: {bubbler_state}
    hotplate: {hotplate_state}
    uv led: {uv_led_state}

    === Transfer Status ===
    target: {target}ml
    media in: {media_in}ml | media out: {media_out}ml


    """

    s: str
    dm: DeviceManager
    sm: SensorManager
    mc: MediaExchangeController

    def __init__(self, dm: DeviceManager, sm: SensorManager,
                 mc: MediaExchangeController) -> None:
        self.s = ''
        self.dm = dm
        self.sm = sm
        self.mc = mc
        self.logger = logging.getLogger('Console Presenter')
        self._last_refresh = datetime.datetime.now()

    def test(self) -> None:
        print(':)')

    def notify(self, sys_info: SystemInfoManager) -> None:
        if not isinstance(sys_info, SystemInfoManager):
            raise ValueError("Notified by " + str(sys_info) +
                             " rather than a SystemInfoManager")

        if seconds_since(self._last_refresh) > TERMINAL_UPDATE_PERIOD:
            self._last_refresh = datetime.datetime.now()
            self.update_string(sys_info)
            self.logger.info(self.s)
            print('\n' * 15)
            print(self.s)
            print('\n' * 15)

    def update_string(self, sys_info: SystemInfoManager) -> None:

        self.s = self.get_system_string(sys_info)

        if sys_info.get_cycle_data().state != 'done':
            self.s += self.get_media_transfer_str(sys_info)
        if OFF_PI:
            self.s += self.get_simulation_string(sys_info)


    def get_system_string(self, sys_info: SystemInfoManager) -> str:
        init_time = sys_info.get_start_time()

        init_datetime = init_time.strftime("%m/%d/%Y %H:%M:%S")
        uptime = datetime.datetime.now() - init_time
        uptime_str = sys_info.get_uptime()
        media_in = sys_info.get_total_media_in()
        media_out = sys_info.get_total_media_out()
        bubbler_uptime = format_seconds(self.dm.get_air_pump_ontime())
        bubbler_downtime = format_seconds(uptime.seconds -
                                          self.dm.get_air_pump_ontime())
        hotplate_uptime = format_seconds(self.dm.get_hotplate_ontime())
        hotplate_downtime = format_seconds(uptime.total_seconds() -
                                          self.dm.get_hotplate_ontime())
        uv_led_uptime = format_seconds(self.dm.get_uv_led_ontime())
        uv_led_downtime = format_seconds(uptime.total_seconds() -
                                         self.dm.get_uv_led_ontime())
        volume = sys_info.get_reactor_volume()
        flow_rate = MEDIA_FLOW_RATE
        cycle_period = format_td(self.mc.time_between_cycles)
        exchange_vol = self.mc.flow_per_cycle
        next_cycle = format_td(sys_info.get_next_cycle())
        wl_str = ['not at sensor', 'at sensor'][sys_info.water_level_exceeded()]
        temp = sys_info.get_last_temp()

        def state_str(state: bool) -> str:
            return ['off', 'on'][state]

        inlet_state = state_str(self.dm.inlet_is_on())
        outlet_state = state_str(self.dm.outlet_is_on())
        bubbler_state = state_str(self.dm.air_pump_is_on())
        hotplate_state = state_str(self.dm.hotplate_is_on())
        uv_led_state = state_str(self.dm.uv_led_is_on())

        s = (
            "        === System Information ===\n"
            f"init: {init_datetime} | uptime: {uptime_str}\n"
            f"media in: {media_in:.2f}ml | media out: {media_out:.2f}ml\n"
            f"bubbler uptime: {bubbler_uptime} | bubbler downtime: {bubbler_downtime}\n"
            f"hotplate uptime: {hotplate_uptime} | hotplate downtime {hotplate_downtime}\n"
            f"uv led uptime: {uv_led_uptime} | uv led downtime {uv_led_downtime}\n"
            f"reactor volume: {volume:.2f}ml | flow rate: {flow_rate:.2f}vol/hr\n"
            f"cycle period {cycle_period} | cycle exchange volume: {exchange_vol:.2f}mls\n"
            f"next cycle: {next_cycle}\n"
            
            "\n=== Sensor Data ===\n"
            f"water level: {wl_str}\n"
            f"temperature: {temp:.2f}\n"
            f"\n=== Device States ===\n"
            f"inlet pump: {inlet_state}\n"
            f"outlet pump: {outlet_state}\n"
            f"bubbler: {bubbler_state}\n"
            f"hotplate: {hotplate_state}\n"
            f"uv led: {uv_led_state}\n"
        )
        return s

    def get_media_transfer_str(self, sys_info: SystemInfoManager) -> str:
        cd = sys_info.get_cycle_data()
        target = cd.target_exchange_vol
        media_in = cd.get_in_vol()
        media_out = cd.get_out_vol()
        state = cd.state
        start_time = cd.start_time.strftime("%H:%M:%S")

        finish_time = cd.end_time
        if finish_time is None:
            finish_time = '--:--:--'
        else:
            finish_time = finish_time.strftime("%H:%M:%S")
        s = (
        '\n=== Transfer Progress ===\n'
        f'target: {target:.2f}ml | state: {state}\n'
        f'media in: {media_in:.2f}ml | media out: {media_out:.2f}ml\n'
        f'start time: {start_time} | finish time: {finish_time}'
        )
        return s


    def get_simulation_string(self, sys_info: SystemInfoManager) -> str:
        s = (
            f'\n=== Simulation Stats ===\n' +
            gpio_adapter.get_GPIO().simulator.get_state_str()
        )
        return s





if __name__ == "__main__":
    lcd = LCD()
    lcd.test()
