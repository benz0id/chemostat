import datetime
import logging

# Global program constants.
HIGH = True
LOW = False

# Pump flow rates in ml/s.
MEDIA_IN_FLOWRATE = 1
MEDIA_OUT_FLOWRATE = 1
SUPPLEMENTAL_MEDIA_IN_FLOWRATE = 1

# System states
DEBUG = 'DEBUG'
STANDARD = 'STANDARD'

LOG_FORMAT = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
