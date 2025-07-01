#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import threading
import time
import pigpio

from typing import TYPE_CHECKING, Callable, Union

from core.io import IO
from abstract_base_classes.singleton_meta import SingletonMeta

class Light(metaclass=SingletonMeta):
    def __init__(self):
        self.pigpio = IO().get_pigpio()
        try:
            self.gpio = int(os.getenv('LIGHT_GPIO'))
        except:
            raise KeyError('The Light needs environment variable LIGHT_GPIO')
        
        self.pigpio.set_mode(self.gpio, pigpio.INPUT)
        
    def init_sequence(self):
        self.blink()
        timer = threading.Timer(0.3, lambda: self.blink())
        timer.start()
        self.blink()

    def on(self):
        self.pigpio.write(self.gpio, pigpio.HIGH)
        
    def off(self):
        self.pigpio.write(self.gpio, pigpio.LOW)

    def blink(self, duration=0.1):
        self.on()
        timer = threading.Timer(duration, lambda: self.off())
        timer.start()