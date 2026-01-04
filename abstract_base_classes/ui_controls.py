from abc import ABC, abstractmethod
from typing import Callable

class UIControls(ABC):

    @abstractmethod
    def on_next(self, callback: Callable):
        pass

    @abstractmethod
    def on_prev(self, callback: Callable):
        pass

    @abstractmethod
    def on_okay(self, callback: Callable):
        pass

    @abstractmethod
    def on_back(self, callback: Callable):
        pass

    @abstractmethod
    def on_any(self, callable: Callable):
        pass

    @abstractmethod
    def reset_callbacks(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def tick(self):
        pass
