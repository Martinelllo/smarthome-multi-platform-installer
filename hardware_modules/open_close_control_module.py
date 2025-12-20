#!/usr/bin/python3
# -*- coding: utf8 -*-

import time
import threading
from typing import Callable

import pigpio

from core.logger import get_logger
from core.mqtt_client import MQTTClient

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig
from entities.job_config_entity import JobEntity
from helper.pin_to_gpio import map_gpio_for
from core.io import IO


class OpenCloseControlModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.controller_config = module_config.get_controllers()[0]
        self.mqtt_client = MQTTClient()
        self.pi = IO().get_pigpio()
        self.topic = f"/module/{self.module_config.get_id()}"

        # example: {"button_open_pin":12,"button_close_pin":25,"control_open_pin":5,"control_close_pin":6}

        self.__control_open_gpio = map_gpio_for(module_config.get_pin_by_key('control_open_pin'))
        if self.__control_open_gpio is None: raise ValueError('control_open_pin is not set')

        self.__control_close_gpio = map_gpio_for(module_config.get_pin_by_key('control_close_pin'))
        if self.__control_close_gpio is None: raise ValueError('control_close_pin is not set')

        self.__button_open_gpio = map_gpio_for(module_config.get_pin_by_key('button_open_pin'))
        self.__button_close_gpio = map_gpio_for(module_config.get_pin_by_key('button_close_pin'))


        if self.__button_open_gpio is not None:
            self.pi.set_pull_up_down(self.__button_open_gpio, pigpio.PUD_UP)
            self.next_button = self.pi.callback(
                self.__button_open_gpio,
                pigpio.FALLING_EDGE,
                lambda gpio, level, time: self.__set_direction('open')
            )
            self.next_button = self.pi.callback(
                self.__button_open_gpio,
                pigpio.RISING_EDGE,
                lambda gpio, level, time: self.__set_direction('hold')
            )
        else: get_logger().warning("button_open_gpio is not set on the interface!")

        if self.__button_close_gpio is not None:
            self.pi.set_pull_up_down(self.__button_close_gpio, pigpio.PUD_UP)
            self.next_button = self.pi.callback(
                self.__button_close_gpio,
                pigpio.FALLING_EDGE,
                lambda gpio, level, time: self.__set_direction('close')
            )
            self.next_button = self.pi.callback(
                self.__button_close_gpio,
                pigpio.RISING_EDGE,
                lambda gpio, level, time: self.__set_direction('hold')
            )
        else: get_logger().warning("button_close_gpio is not set on the interface!")

        self.pi.set_mode(self.__control_open_gpio, pigpio.OUTPUT)
        self.pi.set_mode(self.__control_close_gpio, pigpio.OUTPUT)

        self.__use_default_value()
        self.mqtt_client.subscribe(self.topic, self.__execute_job)

    def get_config(self) -> ModuleConfig:
        return self.module_config

    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.__use_default_value()

    def tick(self):
        return None

    def __execute_job(self, payload: dict, stopper: threading.Event):
        self.stopper = stopper
        job = JobEntity(payload)

        for task in job.get_tasks():
            self.__set_direction(task.get_value('dir'))
            stopper.wait(task.get_duration())

        self.__use_default_value()

    def on_destroy(self):
        get_logger().warning(f"Stop module")
        self.pi.set_pull_up_down(self.__control_open_gpio, pigpio.PUD_OFF)
        self.pi.set_pull_up_down(self.__control_close_gpio, pigpio.PUD_OFF)
        self.pi.set_mode(self.__control_open_gpio, pigpio.INPUT)
        self.pi.set_mode(self.__control_close_gpio, pigpio.INPUT)
        self.mqtt_client.unsubscribe(self.topic)

    def __use_default_value(self):
        controller_config = self.module_config.get_controllers()[0]
        if controller_config.has_default_value():
            self.__set_direction(controller_config.get_default_value("dir"))

    def __set_direction(self, dir:str = None):
        if dir == 'open':
            self.pi.write(self.__control_close_gpio, 1)
            self.stopper.wait(0.1)
            self.pi.write(self.__control_open_gpio, 0)
        elif dir == 'close':
            self.pi.write(self.__control_open_gpio, 1)
            self.stopper.wait(0.1)
            self.pi.write(self.__control_close_gpio, 0)
        else: # else the dir can be 'hold' or None
            self.pi.write(self.__control_open_gpio, 1)
            self.pi.write(self.__control_close_gpio, 1)


if __name__ == "__main__":

    # GPIO-Pin-Nummer (verwenden Sie die BCM-Nummerierung)
    GPIO_PIN = 18  # Beispiel-Pin, an den das PWM-Signal gesendet wird

    # pigpio-Instanz erstellen
    pi = pigpio.pi()

    # Prüfen, ob pigpio-Daemon läuft
    if not pi.connected:
        exit()

    pi.set_mode(GPIO_PIN, pigpio.OUTPUT)
    pi.write(GPIO_PIN, 1)

    time.sleep(1)

    pi.write(GPIO_PIN, 0)

    pi.stop()
