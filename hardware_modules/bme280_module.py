#!/usr/bin/python3
# -*- coding: utf8 -*-

import time
from typing import Union
import board
import busio

from adafruit_bme280 import basic as adafruit_bme280

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig, SensorConfig
from core.logger import get_logger
from core.api_client import APIClient
from core.io import IO
from exceptions.module_exception import ModuleInitializationException
from core.lokal_db import LokalDB


class BME280ReadingModule(ModuleBase):
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.next_time = time.time()

        try:
            self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(IO().get_i2c(), address=0x76)
            self.bme280.mode = adafruit_bme280.MODE_NORMAL
            self.bme280.temperature # init
        except Exception as error:
            raise ModuleInitializationException(
                message=str(error),
                module_class=F"BME280ReadingModule",
                module_name=config.name
            )

        self.db = LokalDB()

        time.sleep(0.5)

    def get_config(self) -> ModuleConfig:
        return self.config

    def set_config(self, module_config: ModuleConfig):
        self.config = module_config

    def tick(self):

        now = time.time()

        if self.next_time > now: return

        sensorValues = []
        for sensor in self.config.get_sensors():

            if sensor.is_type("Temperatur"):
                sensorValues.append({
                    "sensorId": sensor.get_id(),
                    "value": round(self.bme280.temperature, 2)
                })

            if sensor.is_type("Relative Luftfeuchtigkeit"):
                sensorValues.append({
                    "sensorId": sensor.get_id(),
                    "value": round(self.bme280.relative_humidity, 2)
                })

            if sensor.is_type("Luftdruck"):
                sensorValues.append({
                    "sensorId": sensor.get_id(),
                    "value": round(self.bme280.pressure, 2)
                })

        self.db.safe_sensor_readings(sensorValues)
        self.next_time += self.config.get_interval()


    def on_destroy(self):
        pass


if __name__ == "__main__":

    from datetime import datetime
    import requests
    import board
    import busio

    headers = {"Content-Type": "application/json; charset=utf-8"}

    def get_sensor():
        i2c = busio.I2C(board.SCL, board.SDA)
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
        bme280.mode = adafruit_bme280.MODE_NORMAL

        # change this to match the location's pressure (hPa) at sea level
        # need to be configured for the real altitude. Check your next Weatherstation for the pressure
        #bme280.sea_level_pressure = 1013.25

        return bme280

    def send_sensor_value(id, value, headers):
        body = {
            "sensorId": id,
            "value": round(value, 1)
        }
        try:
            response = requests.post(URL + '/sensor-value', json=body, headers=headers)
            get_logger().debug('Sensor wert erfolgreich gesendet. Id: ' + str(id) + ' value: ' + str(value))
        except Exception as error:
            get_logger().error(error)


    URL = "https://smarthome-api.hellmannweb.de" # server
    # URL = "http://192.168.178.20"

    bme280 = get_sensor()

    # DEVICE_NAME='SensorPi'
    # DEVICE_PASSWORD='awdawd123'
    # body = {
    #    "deviceName": DEVICE_NAME,
    #    "devicePassword": DEVICE_PASSWORD,
    # }
    # try:
    #    response = requests.post(URL + '/device-auth', json=body, headers=headers)
    #    token = response.text
    #    print(token)
    #    headers = {
    #       "Content-Type": "application/json; charset=utf-8",
    #       "Authorization": "Bearer "+token,
    #    }
    # except:
    # except Exception as error:
    #    print(error)
    #    exit('Unauthorized')

    INTERVAL = 60

    time.sleep(1) # wait until gpiod starts

    while True:

        print("Temperature: %0.1f C" % bme280.temperature)
        # print("Humidity: %0.1f %%" % bme280.humidity)
        print("relative Humidity: %0.1f %%" % bme280.relative_humidity)
        print("absolute Pressure: %0.1f hPa" % bme280.pressure)
        # print("Altitude = %0.2f meters" % bme280.altitude)
        print("-------------------------------------")

        send_sensor_value(3, bme280.temperature, headers)
        send_sensor_value(4, bme280.relative_humidity, headers)
        send_sensor_value(5, bme280.pressure, headers)

        # utcTimeStamp = datetime.utcnow().timestamp()
        # currentTime = datetime.now()


        time.sleep(INTERVAL)  # Overall INTERVAL second polling.
