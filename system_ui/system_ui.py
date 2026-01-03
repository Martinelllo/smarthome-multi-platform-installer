#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import subprocess
import board
import digitalio
import threading

from typing import Union

from custom_libs.adafruid_ssd1306 import SSD1306_I2C, SSD1306_SPI
from helper.platform_detector import get_cpu_temperature, get_platform_model
from core.logger import get_logger
from helper.pin_adapter import PinAdapter
from abstract_base_classes.ui_controls import UIControls
from abstract_base_classes.singleton_meta import SingletonMeta
from core.io import IO
from exceptions.display_exception import DisplayInitializationException
from core.config_storage import ConfigStorage
from system_ui.confirm import Confirm
from system_ui.rotary_controls import RotaryControls
from system_ui.input import Input
from system_ui.menu import Menu
from system_ui.button_controls import ButtonControls
from custom_libs.SH1106.sh1106 import SH1106_I2C, SH1106_SPI

WHITE = 1
BLACK = 0

class SystemUI(metaclass=SingletonMeta):
    """
    display_type = 'SSD1306_I2C', 'SH1106_I2C', 'SSD1306_SPI', 'SH1106_SPI'
    """
    def __init__(self):

        self.config = ConfigStorage()

        self.turn_dark_timer: Union[threading.Timer, None] = None
        self.turn_off_timer: Union[threading.Timer, None] = None

        self.display_type = os.getenv('DISPLAY_TYPE')
        self.button_type = os.getenv('BUTTON_TYPE')
        self.io = IO()

        if self.display_type == 'SH1106_SPI':
            self.display = SH1106_SPI(width=128, height=64,
                                        spi=self.io.get_spi(),
                                        dc=PinAdapter(21, self.io.get_pigpio()),
                                        res=PinAdapter(22, self.io.get_pigpio()),
                                        cs=PinAdapter(8, self.io.get_pigpio())
                                    )
            self.display.show()

        elif self.display_type == 'SSD1306_SPI':
            self.display = SSD1306_SPI(width=128, height=64,
                                        spi=self.io.get_spi(),
                                        dc=digitalio.DigitalInOut( digitalio.D21 ),
                                        reset=None,
                                        cs=digitalio.DigitalInOut( digitalio.D8 ),
                                    )
            self.display.show()

        elif self.display_type == 'SH1106_I2C':

            self.display = SH1106_I2C(width=128, height=64,
                                        i2c=self.io.get_i2c(),
                                        addr=0x3C,
                                    )
            self.display.flip(True)
            # self.display.contrast(128)      # Helligkeitsstufe 6
            self.display.show()

        elif self.display_type == 'SSD1306_I2C':
            self.display = SSD1306_I2C(width=128, height=64,
                                        i2c=self.io.get_i2c(),
                                        addr=0x3C,
                                    )
            # self.display.contrast(128)      # Helligkeitsstufe 6
            self.display.show()
        else:
            raise DisplayInitializationException(f'DISPLAY_TYPE {self.display_type} on config not supported!')

        self.__set_contrast(self.config.get('display_contrast', 2))

        # init controls
        if self.button_type == 'ROTARY': self.controls = RotaryControls()
        else: self.controls = ButtonControls()

        self.input: Union[Input,None] = None

        # create and store menu
        self.main_menu: Menu = Menu.create_from_map(self, map={
            'Geraete Info':     lambda: self.show_system_info(),
            'Module Anzeigen':  lambda: self.show_info('Module Anzeigen ist noch nicht implementiert.'),
            'System Einstellungen': {
                'WLAN aendern': {
                    'WLAN SSID': lambda:        self.show_WLAN_SSID_input(),
                    'WLAN Passwort': lambda:    self.show_WLAN_passwd_input(),
                },
                'Kontrast': {
                    'Stufe 1': lambda: self.__set_contrast(0),
                    'Stufe 2': lambda: self.__set_contrast(1),
                    'Stufe 3': lambda: self.__set_contrast(2),
                    'Stufe 4': lambda: self.__set_contrast(3),
                    'Stufe 5': lambda: self.__set_contrast(4),
                    'Stufe 6': lambda: self.__set_contrast(5),
                },
                'Auto Off': {
                    'Immer an':     lambda: self.__set_auto_off(0),
                    '10 Sekunden':  lambda: self.__set_auto_off(1),
                    '1 minute':     lambda: self.__set_auto_off(2),
                    '2 minute':     lambda: self.__set_auto_off(3),
                    '10 minute':    lambda: self.__set_auto_off(4),
                    '30 minute':    lambda: self.__set_auto_off(5),
                },
                'System Neustarten': lambda: self.__show_restart_dialog(),
            },
            'Display Aus': lambda: self.display_off(),
        })
        # restore current menu option
        self.main_menu.patch_pointers({
            'System Einstellungen': {
                'Kontrast': self.config.get('display_contrast', 2),
                'Auto Off': self.config.get('auto_off_time', 0)
            }
        })
        # init menu
        self.main_menu.on_draw( lambda: self.__set_contrast() )
        self.main_menu.activate()

    def __set_contrast(self, step: Union[int,None] = None, static: bool = False):
        """Set Contrast"""
        # change contrast
        if step is not None:
            self.config.set('display_contrast', step)
        contrast = [1,10,30,50,90,128][self.config.get('display_contrast', 2)]
        self.display.contrast(contrast)
        # Run display save timer
        if self.turn_dark_timer is not None:
            self.turn_dark_timer.cancel()
        if static is False:
            self.turn_dark_timer = threading.Timer(5.0, lambda:self.display.contrast(1))
            self.turn_dark_timer.start()
        # Run display off timer
        seconds = [0,10,60,120,600,1800][self.config.get('auto_off_time', 0)]
        if self.turn_off_timer is not None:
            self.turn_off_timer.cancel()
        if seconds > 0:
            self.turn_off_timer = threading.Timer(seconds, lambda:self.display_off())
            self.turn_off_timer.start()
        return True

    def __set_auto_off(self, step: int):
        self.config.set('auto_off_time', step)
        self.__set_contrast()
        return True

    def show_menu(self):
        self.main_menu.activate()

    def show_system_info(self):
        self.__set_contrast(static=True)
        self.display.fill(0)
        self.display.fill_rect(0, 0, 32, 32, WHITE)
        self.display.fill_rect(2, 2, 28, 28, BLACK)
        self.display.vline(9, 8, 22, WHITE)
        self.display.vline(16, 2, 22, WHITE)
        self.display.vline(23, 8, 22, WHITE)
        # self.display.fill_rect(26, 24, 2, 4, WHITE)
        self.display.text('Smarthome', 40, 0, WHITE)
        self.display.text('MultiPlatform', 40, 12, WHITE)
        self.display.text(f"{get_platform_model()}", 40, 24, WHITE)
        self.display.text(f'Name: {os.getenv("DEVICE_UID")}', 0, 38, WHITE)
        self.display.text(f"CPU Temp: {get_cpu_temperature():.2f}'C", 0, 50, WHITE)
        self.display.show()
        self.controls.reset_callbacks()
        self.controls.on_any(lambda: self.main_menu.activate())

    def display_off(self):
        self.display.fill(BLACK)
        self.display.show()
        self.display.poweroff()
        self.controls.reset_callbacks()
        self.controls.on_any(lambda: self.display.poweron())
        self.controls.on_any(lambda: self.main_menu.activate())

    def show_menu(self):
        self.main_menu.activate()

    def show_WLAN_SSID_input(self):
        self.__set_contrast(static=True)
        def print_and_to_menu(input: str):
            get_logger().debug(f'save WLAN_SSID: {input}')
            self.config.set('WLAN_SSID', input)
            self.main_menu.activate()
        Input(
            display=self.display,
            controls=self.controls,
            okay_func=lambda text: print_and_to_menu(text),
            stop_func=lambda: self.main_menu.activate(),
            title='WLAN SSID',
            value=self.config.get('WLAN_SSID', '')
        )


    def show_WLAN_passwd_input(self):
        self.__set_contrast(static=True)
        def print_and_to_menu(input: str):
            get_logger().debug(f'save WLAN_passwd: {input}')
            self.config.set('WLAN_passwd', input)
            self.main_menu.activate()
        Input(
            display=self.display,
            controls=self.controls,
            okay_func=lambda text: print_and_to_menu(text),
            stop_func=lambda: self.main_menu.activate(),
            title='WLAN Passwort',
            value=''
        )

    def __show_restart_dialog(self):
        self.__set_contrast(static=True)
        def restart_system():
            get_logger().warning('App restart command received')
            self.show_info('System Startet jetzt neu. Bitte warten...')
            output = subprocess.run(['sudo', 'reboot'], capture_output=True, text=True)
            if output.returncode != 0:
                get_logger().error(output.stderr)
            else:
                get_logger().warning(f'The system will reboot now! {output.stdout}')
        Confirm(
            display=self.display,
            controls=self.controls,
            okay_func=lambda: restart_system(),
            cancel_func=lambda: self.main_menu.activate(),
            title='Neustart',
            text='Wollen Sie wirklich das System Neustarten?'
        )

    def show_info(self, text='Ein unbekannter Fehler ist aufgetreten', title='Info'):
        self.__set_contrast(static=True)
        self.display.fill(BLACK)

        # self.display.text('Error', 36, 4, WHITE, size=2)
        self.display.text(title, int(self.display.width / 2) - len(title) * 6, 4, WHITE, size=2)

        length=20
        lines = [text[i:i+length] for i in range(0, len(text), length)]
        for index, line in enumerate(lines):
            self.display.text(line.strip(), 5, 24 + index * 8, WHITE)

        self.display.show()
        self.controls.reset_callbacks()
        self.controls.on_any(lambda: self.main_menu.activate())

    def on_destroy(self):
        self.display.fill(BLACK)
        self.display.show()
        self.display.poweroff()




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
