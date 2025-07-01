#!/usr/bin/env python3
# -*- coding: utf8 -*-

import json
from typing import Callable, Union
import requests
import socket
import os
import time

from core.logger import get_logger
from abstract_base_classes.singleton_meta import SingletonMeta
from core.temp_db import TempDB
from exceptions.api_exception import ServerNotReachableException

DEFAULT_TIMEOUT = 10            # how long to wait for a response before throwing an error

class APIClient(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.headers = {
            "Origin":self.__get_local_ip(),
            "Content-Type":"application/json; charset=utf-8"
        }

        self.url = os.getenv("API_LINK")
        self.device_uid = os.getenv("DEVICE_UID")
        self.time_offset = 0 # milliseconds shift from server time to compensate all sensor readings
        self.db = TempDB()

        self.__auth()

    def __auth(self):
            response = requests.post(f"{self.url}/device-auth", json={"uid": self.device_uid}, headers=self.headers, timeout=DEFAULT_TIMEOUT)
            
            if response.status_code != 200: raise ValueError(f"{self.url}/device-auth: Response Status Code: {response.status_code}. Message: {response.text}")
                
            self.headers['Authorization'] = 'Bearer ' + response.text
            
            # todo: do a validation vor the auth token here to avoid error responses written to the Authorization header
            
            get_logger().debug(f"{response} POST:{self.url}/device-auth")
            # get_logger().debug(f"Authorization response detail: \n {response.text}")
            
            return None
        
    def get_device_config(self) -> Union[dict, None]:
            response = requests.get(f"{self.url}/device-config", headers=self.headers, timeout=DEFAULT_TIMEOUT)
            get_logger().debug(f"{response} GET:{self.url}/device-config")
            # get_logger().debug(f"Detail: " + json.dumps(json.loads(response.text), indent=1))
            if self.__restoreAuth(response):
                return self.get_device_config()
            return response.json()
        
    def get_mqtt_credentials(self) -> Union[dict, None]:
        response = requests.get(f"{self.url}/mqtt-credentials", headers=self.headers, timeout=DEFAULT_TIMEOUT)
        get_logger().debug(f"{response} GET:{self.url}/mqtt-credentials")
        # get_logger().debug(f"Detail: " + json.dumps(json.loads(response.text), indent=1))
        if self.__restoreAuth(response):
            return self.get_mqtt_credentials()
        return response.json()

    def send_sensor_values(self, sensorReadings: list):
        try:
            for sensor in sensorReadings:
                sensor['createdAt'] = int(sensor['createdAt']) + self.time_offset
            
            response = requests.post(f"{self.url}/sensor-readings-save", json=sensorReadings, headers=self.headers, timeout=DEFAULT_TIMEOUT)
            get_logger().debug(f"{response} POST:{self.url}/sensor-readings-save BODY:{response.text}")
            
            if self.__restoreAuth(response):
                self.send_sensor_values(sensorReadings)
            
            if response.status_code == 200:
                self.db.delete_all_sensor_readings()
                
        except Exception as error:
            raise ServerNotReachableException("POST:{self.url}/sensor-readings-save")
                
    def __get_local_ip(self):
            # Stellen Sie eine Verbindung zu einem öffentlichen DNS-Server her
            s = socket.create_connection(("1.1.1.1", 80))
            ip = s.getsockname()[0]
            s.close()
            get_logger().debug(f"Lokalen IP-Adresse: {ip}")
            return ip
    
    def __restoreAuth(self, response: requests.Response):
        if response.status_code == 401:
            time.sleep(1)
            self.__auth() # if not authenticated get new token and send again
            return True
        return False
    
    def send_ping(self) -> Union[dict, None]:
        try:
            response = requests.post(f"{self.url}/device-ping", headers=self.headers, timeout=DEFAULT_TIMEOUT)
            get_logger().debug(f"{response} GET:{self.url}/device-ping")
            # get_logger().debug(f"Detail: " + json.dumps(json.loads(response.text), indent=1))
            if self.__restoreAuth(response):
                return self.send_ping()
        
            try:
                body: dict = response.json()
                
                if 'time' in body:
                    local_time = int(time.time() * 1000) # UTC-Millisekunden seit 1970
                    self.time_offset = local_time - body['time']
                    
            except Exception as error:
                get_logger().error(f"Failed to parse json response from ping! {error}")


        except Exception as error:
            raise ServerNotReachableException("Server not reachable on send_sensor_values POST:{self.url}/device-ping {error}")
            
        
if __name__ == "__main__":
   pass
