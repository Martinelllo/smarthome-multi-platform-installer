#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import threading
import time
from typing import Callable
import pigpio

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig
from entities.job_config_entity import JobEntity, TaskEntity
from helper.pin_to_gpio import get_gpio_for

from core.logger import get_logger
from core.mqtt_client import MQTTClient
from core.io import IO

    
class PWMControlModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.topic = f"/module/{self.module_config.get_id()}"
        self.mqtt_client = MQTTClient()
        self.gpio_number = get_gpio_for(module_config.get_pin_by_key('PIN'))        
        self.pi = IO().get_pigpio()
        self.pi.set_mode(self.gpio_number, pigpio.OUTPUT)
        self.pi.set_PWM_range(self.gpio_number, 100)
        
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
        job = JobEntity(payload)
        
        for task in job.get_tasks():
            self.pi.set_PWM_frequency(self.gpio_number, task.get_value("pwm_frequency"))
            self.pi.set_PWM_dutycycle(self.gpio_number, task.get_value("value"))
            stopper.wait(task.get_duration())
            
        self.__use_default_value()

    def on_destroy(self):        
        get_logger().warning(f"Stop module")
        self.pi.set_mode(self.gpio_number, pigpio.INPUT)
        self.pi.set_pull_up_down(self.gpio_number, pigpio.PUD_OFF)
        self.mqtt_client.unsubscribe(self.topic)
    
    def __use_default_value(self):
        controller_config = self.module_config.get_controllers()[0]
        if controller_config.has_default_value():
            self.pi.set_PWM_frequency(self.gpio_number, controller_config.get_default_value("pwm_frequency"))
            self.pi.set_PWM_dutycycle(self.gpio_number, controller_config.get_default_value("value"))
    
    
    
if __name__ == "__main__":
    
    import pigpio

    # gpio-Pin-Nummer (verwenden Sie die BCM-Nummerierung)
    GPIO_PIN = 18  # Beispiel-Pin, an den das PWM-Signal gesendet wird

    # pigpio-Instanz erstellen
    pi = pigpio.pi()

    # Prüfen, ob pigpio-Daemon läuft
    if not pi.connected:
        exit()

    # PWM-Frequenz und Duty Cycle einstellen
    frequency = 800  # Frequenz in Hz
    duty_cycle = 128  # Duty Cycle (0-255)

    # PWM auf dem Pin starten
    pi.set_PWM_frequency(GPIO_PIN, frequency)
    pi.set_PWM_dutycycle(GPIO_PIN, duty_cycle)

    # Lassen Sie das PWM-Signal für eine Weile laufen
    time.sleep(10)

    # PWM stoppen
    pi.set_PWM_dutycycle(GPIO_PIN, 0)

    # pigpio-Instanz beenden
    pi.stop()
