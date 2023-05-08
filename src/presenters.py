import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any, List
from global_constants import *
from src.device import Device
from src.sensor import Sensor


class Presenter(ABC):
    @abstractmethod
    def test(self) -> None:
        pass


class LCD(Presenter):
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

    system_state: stores attributes of the system for presentation.
    """




