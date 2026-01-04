#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import threading
import time
import pigpio

from abstract_base_classes.module_base import ModuleBase
from entities.config_entity import ModuleConfig
from custom_libs.dht_reader import DHTSensor

from typing import Union

from helper.pin_to_gpio import map_gpio_for
from core.logger import get_logger
from core.io import IO
from core.lokal_db import LokalDB


class DHTReadingModule(ModuleBase):
    def __init__(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.dht = DHTSensor(IO().get_pigpio(), map_gpio_for(module_config.get_pin_by_key('PIN')))
        self.next_time = time.time()
        self.db = LokalDB()

    def get_config(self) -> ModuleConfig:
        return self.module_config

    def set_config(self, module_config: ModuleConfig):
        self.module_config = module_config

    def tick(self):

        now = time.time()

        if self.next_time > now: return

        self.dht.trigger()
        time.sleep(0.5)

        sensorValues = []
        for sensor in self.module_config.get_sensors():

            if sensor.is_type("Temperatur"):
                sensorValues.append({
                    "sensorId": sensor.get_id(),
                    "value": round(self.dht.temperature(), 2)
                })
            if sensor.is_type("Relative Luftfeuchtigkeit"):
                sensorValues.append({
                    "sensorId": sensor.get_id(),
                    "value": round(self.dht.humidity(), 2)
                })

        self.db.safe_sensor_readings(sensorValues)
        self.next_time += self.module_config.get_interval()

    def on_destroy(self):
        pass

if __name__ == "__main__":


    from datetime import datetime
    import requests
    # import subprocess

    # # Start the pigpiod deamon
    # cmd1 = subprocess.Popen('ps aux'.split(), stdout = subprocess.PIPE)
    # output, error = cmd1.communicate()

    # if error: print('error: ' + error)

    # elif output:
    #    # check pigpiod is running
    #    found = str(output).find('pigpiod')

    #    if found == -1:
    #       # start pigpiod
    #       print('starting pigpiod...')
    #       sudoPassword = 'B0denSee'
    #       cmd2 = subprocess.Popen(['echo',sudoPassword], stdout=subprocess.PIPE)
    #       cmd3 = subprocess.Popen(['sudo','-S','pigpiod'], stdin=cmd2.stdout, stdout=subprocess.PIPE)
    #       output, error = cmd3.communicate()

    #       if error: print('error: ' + error)

    #       print('error: ' + error if error else output)
    #       print('error: ')

    time.sleep(1) # wait until gpiod starts

    INTERVAL = 60 # Intervals of about 2 seconds or less will eventually hang the DHT22.

    pi = pigpio.pi()

    s = DHTSensor(pi, 2)

    r = 0

    while True:

        r += 1

        s.trigger()

        time.sleep(0.5)

        print("{} {} {} {:3.2f} {} {} {} {}".format(
            r,
            s.humidity(),
            s.temperature(),
            s.staleness(),
            s.bad_checksum(),
            s.short_message(),
            s.missing_message(),
            s.sensor_resets()
        ))

        url = "https://smarthome-api.hellmannweb.de" # server
        # url = "http://192.168.178.20" # server

        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }

        temperatureData = {
            "sensorId": 1,
            "value": round(s.temperature(), 2)
        }

        try:
            response = requests.post(url + '/sensor-value', json=temperatureData, headers=headers)
            print(response.text)
        except:
            print('request error')

        utcTimeStamp = datetime.utcnow().timestamp()
        humidityData  = {
            "sensorId": 2,
            "value": round(s.humidity(), 2)
        }

        try:
            response = requests.post(url + '/sensor-value', json=humidityData, headers=headers)
            print(response.text)
        except:
            print('request error')


        currentTime = datetime.now()

        print("{}, Hum: {:3.2f}%, Temp: {:3.2f}°C".format(
            datetime.strftime(currentTime, '%X'),
            s.humidity(),
            s.temperature(),
        ))

        time.sleep(INTERVAL-0.5)  # Overall INTERVAL second polling.
