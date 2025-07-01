from abc import ABC, abstractmethod
import threading
from typing import Callable

class ThreadBase(ABC):

    @abstractmethod
    def run(self, stopper: threading.Event, ended: Callable):
        pass

    @abstractmethod
    def stop(self):
        pass
    
    @abstractmethod
    def isRunning(self):
        pass