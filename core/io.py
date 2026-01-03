#!/usr/bin/env python3
# -*- coding: utf8 -*-

import board
import busio
import pigpio

from core.logger import get_logger
from abstract_base_classes.singleton_meta import SingletonMeta

class IO(metaclass=SingletonMeta):
    """
    This class handles all available bus systems and io gpio
    """
    def __init__(self):
        self.__i2c = None
        self.__pigpio = None
        self.__spi = None

    def stop(self):
        get_logger().warning(f"Stop IO")

        if self.__i2c is not None:
            self.__i2c.deinit()
        if self.__spi is not None:
            self.__spi.deinit()
        if self.__pigpio is not None:
            self.__pigpio.stop()

    def get_spi(self):
        if self.__spi == None:
            self.__spi = busio.SPI(board.SCLK, board.MOSI, board.MISO)
            get_logger().info("Initialize spi bus")
        return self.__spi

    def get_i2c(self):
        if self.__i2c == None:
            self.__i2c = busio.I2C(board.SCL, board.SDA, freq=100000)
            get_logger().info("Initialize i2c bus")
        return self.__i2c

    def get_pigpio(self):
        if self.__pigpio == None:
            self.__pigpio = pigpio.pi()
            get_logger().info("Initialize gpio")
        return self.__pigpio

if __name__ == "__main__":
   pass
