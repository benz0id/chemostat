from abc import ABC
from typing import List


class Observer:

    def notify(self, observer: Observer) -> None:
        pass


class Observable:
    _observers: List[Observer]

    def __init__(self, observers: List[Observer]):
        self._observers = observers

    def notify_observers(self) -> None:
        for observer in self._observers:
            observer.notify(self)
