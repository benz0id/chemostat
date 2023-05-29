import datetime
import platform
import logging

# Global program constants.
HIGH = True
LOW = False

# Pump flow rates in ml/s.
MEDIA_IN_FLOWRATE = 3.4
MEDIA_OUT_FLOWRATE = 3.4
SUPPLEMENTAL_MEDIA_IN_FLOWRATE = 1

# === Media cycling parameters ===

# Maximum ratio of initial media to add when calibrating for underfilling.
MAX_CALIB_RATIO = 1

# Whether delay first cycle.
DELAY_FIRST_CYCLE = False
#TODO
FIRST_CYCLE_DELAY = datetime.timedelta(minutes=1)

# Reactor maximum capacity in mL
REACTOR_MAX_VOLUME = 1000

# System states
DEBUG = 'DEBUG'
STANDARD = 'STANDARD'

DEBUG_MODE = False

# LCD Attributes
LCD_NROW = 4
LCD_NCOL = 20
LCD_REFRESH_PERIOD = 2

FAST_PAUSE_TICK = 0.1
SLOW_PAUSE_TICK = 10

OFF_PI = 'Linux' not in platform.platform()
OFF_PI_DEFAULT_TEMP = 23
OFF_PI_DEFAULT_SIG = False
