import datetime
import logging

# Global program constants.
HIGH = True
LOW = False

# Pump flow rates in ml/s.
MEDIA_IN_FLOWRATE = 1
MEDIA_OUT_FLOWRATE = 1
SUPPLEMENTAL_MEDIA_IN_FLOWRATE = 1

# === Media cycling parameters ===

# Maximum ratio of initial media to add when calibrating for underfilling.
MAX_CALIB_RATIO = 1

# Whether delay first cycle.
DELAY_FIRST_CYCLE = False

# System states
DEBUG = 'DEBUG'
STANDARD = 'STANDARD'

DEBUG_MODE = False

# LCD Attributes
LCD_NROW = 4
LCD_NCOL = 20
LCD_REFRESH_PERIOD = 0.5

FAST_PAUSE_TICK = 0.1
SLOW_PAUSE_TICK = 10
