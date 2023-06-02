import datetime
import platform
import logging

OFF_PI = 'Linux' not in platform.platform()
if OFF_PI:
    logging.info("Operating with dummy device and sensor interface.")

# Whether to delay the first cycle.
DELAY_FIRST_CYCLE = True
FIRST_CYCLE_DELAY = datetime.timedelta(hours=10)

# Runtime Constants for Standard Operation
if not OFF_PI:
    MEDIA_FLOW_RATE = 0.05 # vol / hr
    TARGET_TEMP = 33 # C
    REACTOR_VOLUME = 550 # ml at sensor, none for empty
    CYCLES_PER_HOUR = 0.5

    # Misc.
    MEDIA_CALMING = True
    TERMINAL_UPDATE_PERIOD = 0.2
    UV_LED_ON = True

# Runtime Constants for Simulated Operation
else:
    MEDIA_FLOW_RATE = 0.1  # vol / hr
    TARGET_TEMP = 33  # C
    REACTOR_VOLUME = None  # ml at sensor, none for empty
    CYCLES_PER_HOUR = 1

    # Misc.
    MEDIA_CALMING = False
    TERMINAL_UPDATE_PERIOD = 2
    UV_LED_ON = True


# === Basic program constants ===
HIGH = True
LOW = False

# Pump flow rates in ml/s.
MEDIA_IN_FLOWRATE = 3.4
MEDIA_OUT_FLOWRATE = 3.4
SUPPLEMENTAL_MEDIA_IN_FLOWRATE = 1

# === Media cycling parameters ===

# Maximum ratio of initial media to add when calibrating for underfilling.
MAX_CALIB_RATIO = 1

# Reactor maximum capacity in mL
REACTOR_MAX_VOLUME = 999.99

# System states
DEBUG = 'DEBUG'
STANDARD = 'STANDARD'
DEBUG_MODE = False

# === Presenter Constants ===
LCD_NROW = 4
LCD_NCOL = 20
LCD_REFRESH_PERIOD = 0.5

ULTRA_FAST_TICK = 0.01
FAST_PAUSE_TICK = 0.1
SLOW_PAUSE_TICK = 10

# === Simulator Constants ===
SIMULATOR_TICK = 0.1
WL_SENSOR_THRESHOLD = 80
SIMULATOR_NOTIFY_EVERY = 1
OFF_PI_DEFAULT_TEMP = 23
OFF_PI_DEFAULT_SIG = False

# === Temperature Regulation Constants ===
SHUTDOWN_TEMP = 40


# === Bubbler Constants ===
BUBBLER_PERCENT_ONTIME = 50
BUBBLER_PERIOD = datetime.timedelta(minutes=10)
