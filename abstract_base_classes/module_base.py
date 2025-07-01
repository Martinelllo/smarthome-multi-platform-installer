from abc import ABC, abstractmethod
from typing import Union

from entities.config_entity import ModuleConfig

class ModuleBase(ABC):

    @abstractmethod
    def get_config(self) -> ModuleConfig:
        pass
    
    @abstractmethod
    def set_config(self):
        pass
    
    @abstractmethod
    def tick(self):
        """
        On every tick the module locks if he has something to do 
        and does it and sets the timer to the next time it has some thing to do.
        """
        pass
    
    @abstractmethod
    def on_destroy(self):
        pass