from abc import ABC
from typing import List, Any, Union


class Observer:

    def notify(self, observer: Any) -> None:
        pass


class Observable:
    _observers: List[Observer]

    def __init__(self, observers: Union[List[Observer], None]):
        if isinstance(observers, list):
            self._observers = observers
        else:
            self._observers = []

    def notify_observers(self) -> None:
        for observer in self._observers:
            observer.notify(self)
