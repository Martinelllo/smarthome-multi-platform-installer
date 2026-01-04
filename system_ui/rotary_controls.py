
import os
import time
import pigpio



from typing import TYPE_CHECKING, Callable, Union, TypedDict

from core.io import IO

from core.logger import get_logger
from abstract_base_classes.ui_controls import UIControls


class Trigger(TypedDict):
    name: str
    time: int


class RotaryControls(UIControls):
    def __init__(self):
        self.pigpio = IO().get_pigpio()

        try:
            self.next_gpio = int(os.getenv('NEXT_GPIO'))
            self.prev_gpio = int(os.getenv('PREV_GPIO'))
            self.okay_gpio = int(os.getenv('OKAY_GPIO'))
            self.back_gpio = int(os.getenv('BACK_GPIO'))
        except:
            raise KeyError('The RotaryControls needs environment variables NEXT_GPIO,'
                            'PREV_GPIO, OKAY_GPIO and BACK_GPIO on the .env file to work')

        self.pigpio.set_pull_up_down(self.next_gpio, pigpio.PUD_UP)
        self.pigpio.set_pull_up_down(self.prev_gpio, pigpio.PUD_UP)
        self.pigpio.set_pull_up_down(self.okay_gpio, pigpio.PUD_UP)
        self.pigpio.set_pull_up_down(self.back_gpio, pigpio.PUD_UP)

        self.next_func: list[Callable] = []
        self.prev_func: list[Callable] = []
        self.okay_func: list[Callable] = []
        self.back_func: list[Callable] = []

        self.last_rotary_trigger = 0
        self.last_press = 0
        self.last_tick = time.time()

        self.__init_callbacks(self)

    def __init_callbacks(self):
        try:
            self.cb1.cancel()
            self.cb2.cancel()
            self.cb3.cancel()
            self.cb4.cancel()
        except Exception:
            pass

        self.cb1 = self.pigpio.callback(self.next_gpio, pigpio.EITHER_EDGE,  lambda gpio, level, time: self.__trigger_rotary(self.next_func, time))
        self.cb2 = self.pigpio.callback(self.prev_gpio, pigpio.EITHER_EDGE,  lambda gpio, level, time: self.__trigger_rotary(self.prev_func, time))
        self.cb3 = self.pigpio.callback(self.okay_gpio, pigpio.FALLING_EDGE, lambda gpio, level, time: self.__debounce_run(  self.okay_func, time))
        self.cb4 = self.pigpio.callback(self.back_gpio, pigpio.FALLING_EDGE, lambda gpio, level, time: self.__debounce_run(  self.back_func, time))

    def __trigger_rotary(self, callables: list[Callable], time):
        if self.last_rotary_trigger:
            diff = time - self.last_rotary_trigger
            if 8000 < diff > 50000:
                for func in callables: func()
        self.last_rotary_trigger = time

    def __debounce_run(self, callables: list[Callable], time):
        debounce_time = 500000 # 0.5 seconds
        if time - self.last_press > debounce_time:
            for func in callables:
                func()
            self.last_press = time

    def on_next(self, callable: Callable):
        self.next_func.append(callable)

    def on_prev(self, callable: Callable):
        self.prev_func.append(callable)

    def on_okay(self, callable: Callable):
        self.okay_func.append(callable)

    def on_back(self, callable: Callable):
        self.back_func.append(callable)

    def on_any(self, callable: Callable):
        self.on_next(callable)
        self.on_prev(callable)
        self.on_okay(callable)
        self.on_back(callable)

    def reset_callbacks(self):
        self.next_func = []
        self.prev_func = []
        self.okay_func = []
        self.back_func = []

    def stop(self):
        self.reset_callbacks()

    def tick(self):
        now = time.time()
        if now - self.last_tick < 60: return
        self.last_tick = now

        self.__init_callbacks()


if __name__ == "__main__":
    pass
