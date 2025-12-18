#!/usr/bin/env python3
# -*- coding: utf8 -*-

import os
import subprocess
import threading
import time
from dotenv import load_dotenv

from core.io import IO
from core.logger import get_logger

from core.api_client import APIClient
from core.mqtt_client import MQTTClient
from exceptions.module_exception import ModuleInitializationException
from core.temp_db import TempDB
from exceptions.api_exception import ServerNotReachableException
from exceptions.io_exception import IOInitializationException
from core.light import Light
from system_ui.system_ui import SystemUI
from core.module_manager import ModuleManager
from entities.config_entity import DeviceConfig

# listen for restart prompt
def handle_restart():
    get_logger().warning("App restart command received")
    output = subprocess.run(['sudo', 'reboot'], capture_output=True, text=True)
    if output.returncode != 0:
        get_logger().error(output.stderr)
    else:
        get_logger().warning(f"The system will reboot now! {output.stdout}")

def main():

    try:

        # led is possibly not available. we catch the not available error here
        led = None
        try:
            led = Light()
            led.init_sequence()
            get_logger().info("Initialize Light")
        except Exception as error:
            get_logger().warning(f"Light could not be initialized: {error}")

        # display is possibly not available. we catch the not available error here
        try:
            system_ui = SystemUI()
            get_logger().info("Initialize SystemUI")
        except Exception as error:
            get_logger().warning(f"Display could not be initialized: {error}")
            # raise error

        api_client = APIClient()
        mqtt_client = MQTTClient()
        module_manager = ModuleManager()
        localDb = TempDB()

        mqtt_client.subscribe('/restart', lambda data: handle_restart())

        # setup all modules on the module_manager and listen for Configs
        module_manager.setup_modules( DeviceConfig(api_client.get_device_config()) )

        mqtt_client.subscribe( '/config', lambda data: module_manager.setup_modules(DeviceConfig(data)) )

        next_contact = time.time()

        # start main loop
        while True:

            # on each tick the modules check there tasks and do some stuf eg. writing sensor values to the db
            module_manager.tick()

            try:
                if next_contact <= time.time():
                    if led is not None: led.blink()
                    api_client.send_ping()
                    next_contact += 60

                    module_values = localDb.get_sensor_readings()

                    if len(module_values) > 0:
                        api_client.send_sensor_values(module_values)

            except ServerNotReachableException as error:
                get_logger().error(f"{error}")

            # wait before next run to save energy
            time.sleep(0.5)


    except ModuleInitializationException as error:
        get_logger().critical( f"Error on Initialization {error.module_class} ({error.module_name})! {error.message} Reboot in 5 minutes.")
        time.sleep(60 * 5)
        handle_restart()

    except IOInitializationException as error:
        get_logger().critical( f"Failed to initiate gpio: {error.gpio}. {error}")

    except KeyboardInterrupt:
        get_logger().critical( "KeyboardInterrupt!" )

    except Exception as error:
        get_logger().critical( f"Error on Runtime! {error}")
        raise error

    finally:

        try:
            if module_manager is not None:
                module_manager.on_destroy()
        except Exception as error:
            get_logger().error( f"Failed to destroy module_manager! {error}")

        try:
            if mqtt_client is not None:
                mqtt_client.on_destroy()
        except Exception as error:
            get_logger().error( f"Failed to destroy mqtt_client! {error}")

        try:
            if system_ui is not None and system_ui.display:
                system_ui.on_destroy()
        except Exception as error:
            get_logger().error( f"Failed to destroy system_ui! {error}")


if __name__ == "__main__":

    load_dotenv()
    main()
