#!/usr/bin/python3
# -*- coding: utf8 -*-

import threading
import time
from typing import Callable

import adafruit_ssd1306

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig

from core.logger import get_logger
from entities.job_config_entity import JobEntity
from core.mqtt_client import MQTTClient
from system_ui.system_ui import SystemUI

class DisplayInfoModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.mqtt_client = MQTTClient()
        self.ui = SystemUI()
        self.topic = f"/module/{self.module_config.get_id()}"
        
        # init
        self.show_logo()
        time.sleep(5)
        self.__use_default_value()
        self.mqtt_client.subscribe(self.topic, self.__execute_job)
        
    def get_config(self) -> ModuleConfig:
        return self.module_config
    
    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.__use_default_value()
        
    def tick(self):
        return None

    def __execute_job(self, payload: dict):
        job = JobEntity(payload)
        
        for task in job.get_tasks():
            self.show_logo()
            # todo cms
            time.sleep(task.get_duration())
            
        self.__use_default_value()
            
    def show_logo(self):
        self.ui.show_info()
        
    def __use_default_value(self):
        self.ui.show_menu()
        
    def on_destroy(self):
        get_logger().warning(f"Stop module")


if __name__ == "__main__":
    
    # Basic example of clearing and drawing pixels on a SSD1306 OLED display.
    # This example and library is meant to work with Adafruit CircuitPython API.
    # Author: Tony DiCola
    # License: Public Domain

    # Import all board pins.
    import board
    import busio

    # Import the SSD1306 module.
    import adafruit_ssd1306


    # Create the I2C interface.
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create the SSD1306 OLED class.
    # The first two parameters are the pixel width and pixel height.  Change these
    # to the right size for your display!
    display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    # Alternatively you can change the I2C address of the device with an addr parameter:
    #display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x31)

    # Clear the display.  Always call show after changing pixels to make the display
    # update visible!
    display.fill(0)

    display.show()

    # Set a pixel in the origin 0,0 position.
    display.pixel(0, 0, 1)
    # Set a pixel in the middle 64, 16 position.
    display.pixel(64, 16, 1)
    # Set a pixel in the opposite 127, 31 position.
    display.pixel(127, 31, 1)
    display.show()