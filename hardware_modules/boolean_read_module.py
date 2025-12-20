#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import threading
from typing import Union

import pigpio

import time

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig
from helper.pin_to_gpio import map_gpio_for
from core.io import IO
from core.temp_db import TempDB


class BooleanReadingModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.next_time = time.time()
        self.gpio_number = map_gpio_for(module_config.get_pin_by_key('PIN'))
        self.pi = IO().get_pigpio()
        self.pi.set_mode(self.gpio_number, pigpio.INPUT)
        self.db = TempDB()


    def get_config(self) -> ModuleConfig:
        return self.module_config

    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config

    def tick(self):

        now = time.time()

        if self.next_time > now: return

        sensor = self.module_config.get_sensors()[0]

        sensorValues = [{
            "sensorId": sensor.get_id(),
            "value": self._get_current_value()
        }]

        self.db.safe_sensor_readings(sensorValues)
        self.next_time += self.module_config.get_interval()


    def _get_current_value(self) -> int:
        '''Returns den aktuell anliegenden wert am gpio als 1 oder 0'''
        # XOR the current pin value with 1 to toggle between 0 and 1
        value = self.pi.read(self.gpio_number) ^ 1
        return value

    def on_destroy(self):
        pass

if __name__ == "__main__":
   pass
