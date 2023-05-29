from src.global_constants import OFF_PI, OFF_PI_DEFAULT_SIG


class GPIO:
    """A Dummy GPIO module for local testing."""
    sig = OFF_PI_DEFAULT_SIG
    BCM = None
    OUT = None
    IN = None

    def setwarnings(self, *args, **kwargs):
        pass
    def setmode(self, *args, **kwargs):
        pass
    def cleanup(self, *args, **kwargs):
        pass
    def output(self, *args, **kwargs):
        pass
    def setup(self, *args, **kwargs):
        pass
    def input(self, *args):
        return self.sig

if not OFF_PI:
    import RPi.GPIO as GPIO
else:
    GPIO = GPIO()
