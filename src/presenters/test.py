import RPi.GPIO as GPIO
import dht11
import lcd_driver

from time import *

mylcd = I2C_LCD_driver.lcd()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

mylcd.lcd_display_string(
    "test", 1)
mylcd.lcd_display_string("test", 2)

sleep(10)

GPIO.cleanup()