from typing import List

from global_constants import *

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")


class GPIOAdapter:
    """Adapts RPi.GPIO functionality."""

    configured_out: List[int]
    configured_in: List[int]

    def __init__(self) -> None:
        self.configured_out = []
        self.configured_in = []

    def configure_out(self, pin: int, initial=LOW) -> None:
        """Configure the given pin as an output."""
        if pin in self.configured_out or pin in self.configured_in:
            raise ValueError("Pin is already configured.")

        GPIO.setup(pin, GPIO.OUT, initial=initial)

        self.configured_out.append(pin)

    def configure_in(self, pin: int) -> None:
        """Configure the given pin as an input."""
        if pin in self.configured_out or pin in self.configured_in:
            raise ValueError("Pin is already configured.")

        GPIO.setup(pin, GPIO.IN)

        self.configured_in.append(pin)

    def write():




GPIO.cleanup()