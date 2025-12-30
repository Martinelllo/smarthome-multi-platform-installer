#!/usr/bin/env python3
# -*- coding: utf8 -*-

from core.logger import get_logger

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import DeviceConfig, ModuleConfig

from hardware_modules.bme280_module import BME280ReadingModule
from hardware_modules.boolean_read_module import BooleanReadingModule
from hardware_modules.dht_module import DHTReadingModule
from hardware_modules.raspi_basic_module import RaspiBasicModule
from hardware_modules.pwm_control_module import PWMControlModule
from hardware_modules.boolean_control_module import BooleanControlModule
from hardware_modules.open_close_control_module import OpenCloseControlModule
from hardware_modules.display_info_module import DisplayInfoModule
from hardware_modules.hc_sr04_module import HCSR04Module
from entities.config_entity import ModuleConfig
from abstract_base_classes.singleton_meta import SingletonMeta

class ModuleManager(metaclass=SingletonMeta):

    def __init__(self) -> None:
        self.__modules: list[ModuleBase] = []

    def tick(self):
        for module in self.__modules:
            try:
                module.tick()
            except Exception as error:
                get_logger().error(f"Error on module tick for module id: {module.get_config().get_id()}: {error}")
                raise error

    def setup_modules(self, deviceConfig: DeviceConfig):

        module_configs = deviceConfig.get_all_configs()

        # stop modules that are not on the config
        for existing_module in self.__modules:
            # find a config by module id
            configExists = any(existing_module.get_config().get_id() == config.get_id() for config in module_configs)
            get_logger().debug(F"Module: {existing_module.get_config().type} with id: {existing_module.get_config().id} -> configExists: {configExists}")
            if not configExists:
                existing_module.on_destroy()
                self.__modules.remove(existing_module)

        # create new modules or patch module configs
        for config in module_configs:
            # if config module id is on the config of a running module return it and stop and patch the config
            module = next((m for m in self.__modules if config.get_id() == m.get_config().get_id()), None)
            # get_logger().debug(F"Module: {config.module_type} with id: {config.module_id} -> moduleExists {len(modulesFound) > 0}")

            if module is not None: # update config of module
                module.set_config(config)
                # get_logger().debug(F"Module: {config.module_type} with id: {config.module_id} updates config")

            else: # create module
                new_module = self.__create_module(config)
                self.__modules.append(new_module)
                get_logger().info(f"Module: {config.type} with id: {config.id} initialized!")


    def __create_module(self, moduleConf: ModuleConfig):
        # System
        if moduleConf.is_type("RASPI_BASIC"):   return RaspiBasicModule(moduleConf)
        if moduleConf.is_type("DISPLAY"):       return DisplayInfoModule(moduleConf)
        # Sensors
        if moduleConf.is_type("DHT"):           return DHTReadingModule(moduleConf)
        if moduleConf.is_type("BME280"):        return BME280ReadingModule(moduleConf)
        if moduleConf.is_type("BOOLEAN_READ"):  return BooleanReadingModule(moduleConf)
        if moduleConf.is_type("HC-SR04"):      return HCSR04Module(moduleConf)
        # Controller
        if moduleConf.is_type("BOOLEAN_WRITE"): return BooleanControlModule(moduleConf)
        if moduleConf.is_type("PWM"):           return PWMControlModule(moduleConf)
        # Hybrid
        if moduleConf.is_type("OPEN_CLOSE"):    return OpenCloseControlModule(moduleConf)

        raise ValueError("Module type '%s' not supported" %(moduleConf.type) )

    def on_destroy(self):
        for existing_module in self.__modules:
            existing_module.on_destroy()
            self.__modules.remove(existing_module)


if __name__ == "__main__":
   pass