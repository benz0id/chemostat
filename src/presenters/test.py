import RPi.GPIO as GPIO
import dht11
import I2C_LCD_driver

from time import *

mylcd = I2C_LCD_driver.lcd()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

while True:

    instance = dht11.DHT11(pin=4)
    result = instance.read()

    # Uncomment for Fahrenheit:
    # result.temperature = (result.temperature * 1.8) + 32

    if result.is_valid():
        mylcd.lcd_display_string(
            "Temp: %d%s C" % (result.temperature, chr(223)), 1)
        mylcd.lcd_display_string("Humidity: %d %%" % result.humidity, 2)