from abc import ABC, abstractmethod
from typing import Any


class SensorObserver(ABC):

    @abstractmethod
    def notify(self, notifier: Any) -> None:
        pass

class Sensor:
    pass