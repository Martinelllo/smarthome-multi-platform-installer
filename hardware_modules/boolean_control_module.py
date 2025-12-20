#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import threading
import time
import pigpio

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig
from entities.job_config_entity import JobEntity, TaskEntity
from helper.pin_to_gpio import map_gpio_for
from typing import TYPE_CHECKING, Callable

from core.logger import get_logger
from core.io import IO
from core.mqtt_client import MQTTClient

class BooleanControlModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config

        self.topic = f"/module/{self.module_config.get_id()}"
        self.mqtt_client = MQTTClient()
        self.pi = IO().get_pigpio()

        self.pin1 =  map_gpio_for(self.module_config.get_pin_by_key('PIN1'))
        if self.pin1: self.pi.set_mode(self.pin1, pigpio.OUTPUT)

        self.pin2 =  map_gpio_for(self.module_config.get_pin_by_key('PIN2'))
        if self.pin2: self.pi.set_mode(self.pin2, pigpio.OUTPUT)

        self.npin1 = map_gpio_for(self.module_config.get_pin_by_key('nPIN1'))
        if self.npin1: self.pi.set_mode(self.npin1, pigpio.OUTPUT)

        self.npin2 = map_gpio_for(self.module_config.get_pin_by_key('nPIN2'))
        if self.npin2: self.pi.set_mode(self.npin2, pigpio.OUTPUT)

        self.__use_default_value()
        self.mqtt_client.subscribe(self.topic, self.__execute_job)

    def get_config(self) -> ModuleConfig:
        return self.module_config

    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.__use_default_value()

    def tick(self):
        pass

    def __execute_job(self, payload: dict, stopper: threading.Event):
        job = JobEntity(payload)

        for task in job.get_tasks():
            if self.pin1:  self.pi.write(self.pin1, task.get_value("value"))
            if self.pin2:  self.pi.write(self.pin2, task.get_value("value"))
            if self.npin1: self.pi.write(self.npin1, 1 - int(task.get_value("value")))
            if self.npin2: self.pi.write(self.npin2, 1 - int(task.get_value("value")))
            stopper.wait(task.get_duration())

        self.__use_default_value()

    def on_destroy(self):
        get_logger().warning(f"Stop module")
        if self.pin1:  self.pi.set_mode(self.pin1, pigpio.INPUT)
        if self.pin2:  self.pi.set_mode(self.pin2, pigpio.INPUT)
        if self.npin1: self.pi.set_mode(self.npin1, pigpio.INPUT)
        if self.npin2: self.pi.set_mode(self.npin2, pigpio.INPUT)
        self.mqtt_client.unsubscribe(self.topic)

    def __use_default_value(self):
        controller_config = self.module_config.get_controllers()[0]
        if controller_config.has_default_value():
            if self.pin1:  self.pi.write(self.pin1, controller_config.get_default_value("value"))
            if self.pin2:  self.pi.write(self.pin2, controller_config.get_default_value("value"))
            if self.npin1: self.pi.write(self.npin1, 1 - int(controller_config.get_default_value("value")))
            if self.npin2: self.pi.write(self.npin2, 1 - int(controller_config.get_default_value("value")))


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
