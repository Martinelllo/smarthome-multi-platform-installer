#!/usr/bin/python3
# -*- coding: utf8 -*-


from typing import Union
from abstract_base_classes.module_base import ModuleBase

import time

from entities.config_entity import ModuleConfig

from helper.platform_detector import get_cpu_temperature
from core.temp_db import TempDB
    
class RaspiBasicModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.next_time = time.time()
        self.db = TempDB()
    
    def get_config(self) -> ModuleConfig:
        return self.module_config
    
    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config
             
    def tick(self):
        now = time.time()

        if self.next_time > now: return None
        
        sensorValues = []
        for sensor in self.module_config.get_sensors():
            if sensor.is_type("CPU Temp"):
                sensorValues.append({
                    "sensorId": sensor.get_id(),
                    "value": round(get_cpu_temperature(), 2)
                })
                
        self.db.safe_sensor_readings(sensorValues)
        self.next_time += self.module_config.get_interval()
    
    def on_destroy(self):
        pass

if __name__ == "__main__":
    pass