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

CONSTANT_SOUND_SPEED = 0.0343 # sound needs 0.0343µs to travel 1mm

class HCSR04Module(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.next_time = time.time()
        self.trigger_pin = map_gpio_for(module_config.get_pin_by_key('trigger_pin'))
        self.echo_pin = map_gpio_for(module_config.get_pin_by_key('echo_pin'))

        self.pi = IO().get_pigpio()

        self.pi.set_mode(self.trigger_pin, pigpio.OUTPUT)
        self.pi.write(self.trigger_pin, pigpio.HIGH)

        self.pi.set_mode(self.echo_pin, pigpio.INPUT)
        # self.pi.set_pull_up_down(self.echo_pin, pigpio.PUD_DOWN)

        self.start_time = None
        self.echo_time = None

        self.cb1 = self.pi.callback(self.echo_pin, pigpio.RISING_EDGE, lambda gpio, level, tick: self.send_echo(tick))
        self.cb2 = self.pi.callback(self.echo_pin, pigpio.FALLING_EDGE, lambda gpio, level, tick: self.receive_echo(tick))

        self.db = TempDB()


    def get_config(self) -> ModuleConfig:
        return self.module_config

    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config

    def tick(self):
        now = time.time()

        if self.next_time > now: return

        sensor = self.module_config.get_sensors()[0]

        self.trigger()

        time.sleep(0.15) # max distance is 4 meters so the max time is 0,01166180758017492711370262390671 seconds

        # print(f"echo_time {self.echo_time}µs = distance {self._get_current_value()}mm")

        if self.echo_time is None: return

        sensorValues = [{
            "sensorId": sensor.get_id(),
            "value": self._get_current_value()
        }]

        self.db.safe_sensor_readings(sensorValues)
        self.next_time += self.module_config.get_interval()

    def _get_current_value(self) -> float:
        if self.echo_time is None:
            return -1
        return self.echo_time * CONSTANT_SOUND_SPEED / 2

    def trigger(self):
        self.start_time = None
        self.echo_time = None
        self.pi.write(self.trigger_pin, pigpio.LOW)
        time.sleep(0.00001),  # 10 us delay
        self.pi.write(self.trigger_pin, pigpio.HIGH)

    def send_echo(self, us):
        self.start_time = us

    def receive_echo(self, us):
        self.echo_time = us - self.start_time

    def on_destroy(self):
        self.cb1.cancel()
        self.cb2.cancel()

if __name__ == "__main__":
   pass
