from abc import ABC, abstractmethod
from typing import Callable, List, Generic, TypeVar

T = TypeVar('T')


class Event(ABC, Generic[T]):
    def __init__(self) -> None:
        self.__handlers: List[Callable[[T], None]] = []

    def subscribe(self, handler: Callable[[T], None]) -> None:
        self.__handlers.append(handler)

    def unsubscribe(self, handler: Callable[[T], None]) -> None:
        if handler in self.__handlers:
            self.__handlers.remove(handler)

    def clear_subscribers(self) -> None:
        self.__handlers.clear()

    def _fire(self, arg: T) -> None:
        for handler in self.__handlers:
            handler(arg)
