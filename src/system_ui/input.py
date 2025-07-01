#!/usr/bin/python3
# -*- coding: utf8 -*-

import threading
import time
from custom_libs.adafruid_ssd1306 import SSD1306_I2C
from core.logger import get_logger
from abstract_base_classes.thread_base import ThreadBase
from abstract_base_classes.ui_controls import UIControls


from typing import Callable

from custom_libs.adafruit_framebuf import FrameBuffer


CHAR_SET = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTVWXYX1234567890.,;:!?_-+*/=<>(){}[]\"^´`\\§$@%&|"
WHITE = 1
BLACK = 0

class Cursor():
    def __init__(self, input: 'Input'):
        self.input = input

        self.x, self.y = 0,0
        self.length = 5

    def set_position(self, x: int, y: int):
        self.__draw_cursor(BLACK)
        self.x, self.y = x, y

    def __draw_cursor(self, color: int):
        if "nav" == self.input.mode:
            self.input.display.line(self.x, self.y, self.x + self.length, self.y, color)
        elif "edit" == self.input.mode:
            self.input.display.rect(self.x-1, self.y-1, self.length+3, 2, color)
            
    def draw(self):
        if "nav" == self.input.mode:
            cursor_speed = 1
            if time.time() % cursor_speed <= cursor_speed / 2:
                self.__draw_cursor(WHITE)
            else:
                self.__draw_cursor(BLACK)
            
        elif "edit" == self.input.mode:
            self.__draw_cursor(WHITE)

class Input(ThreadBase):
    def __init__(self, display: FrameBuffer, controls: UIControls, okay_func: Callable[[str], None], stop_func: Callable, title="Eingabe", value=""):
        self.display = display
        self.controls = controls
        self.mode = "nav" # "nav", "edit"
        self.__nav_p = 0
        self.cursor = Cursor(self)
        self.char_i = [] # characters indexes on there positions
        self.__append_text(value)
        self.title = title
        
        self.__okay_func = okay_func
        self.__stop_func = stop_func
        self.on_draw_func: list[Callable] = []

        self.controls.reset_callbacks()
        self.controls.on_next(lambda: self.__next_action())
        self.controls.on_prev(lambda: self.__prev_action())
        self.controls.on_okay(lambda: self.__okay_action())
        self.controls.on_back(lambda: self.__back_action())
        
        self.__draw_thread = threading.Thread(target=self.run,)
        self.__draw_thread.start()
        

    def __next_action(self):
        if "nav" == self.mode:
            if self.__nav_p >= len(self.char_i): self.__nav_p = -2
            else: self.__nav_p += 1
            
        elif "edit" == self.mode:
            self.char_i[self.__nav_p] = (self.char_i[self.__nav_p] + 1) % len(CHAR_SET)

    def __prev_action(self):
        if "nav" == self.mode:
            self.__nav_p -= 1
            if self.__nav_p < -2: self.__nav_p = len(self.char_i)

        elif "edit" == self.mode:
            self.char_i[self.__nav_p] -= 1
            if self.char_i[self.__nav_p] < 0: self.char_i[self.__nav_p] = len(CHAR_SET) - 1

    def __okay_action(self):
        if "edit" == self.mode: 
            self.__nav_mode()
            return
        
        if self.is_pointer_on_char(): # wenn pointer auf char zeigt
            self.__edit_mode()
        elif self.is_pointer_after_text(): # wenn pointer auf char zeigt
            self.__append_text(" ")
            self.__edit_mode()
        elif -1 == self.__nav_p: # wenn pointer auf okay button zeigt
            self.stop()
            self.__okay_func(self.__get_text())
        elif -2 == self.__nav_p: # wenn pointer auf cancel button zeigt
            self.stop()
            self.__stop_func()

    def __back_action(self):
        if "nav" == self.mode:
            if self.__nav_p > 0 and self.__nav_p <= len(self.char_i):
                self.__nav_p -= 1
                self.char_i.pop(self.__nav_p)
            elif self.__nav_p in [-1, 0]:
                self.__nav_p = -2
            elif -2 == self.__nav_p:
                self.__stop_func()
        if "edit" == self.mode:
            self.__nav_mode()

    def __edit_mode(self):
        self.mode = "edit"
        self.cursor.set_position(4 + self.__nav_p * 6, 28)

    def __nav_mode(self):
        self.mode = "nav"
        
    def run(self):
        self.__running = True
        while self.__running:
            self._draw()
        
    def stop(self):
        self.__running = False
        self.__draw_thread.join()
    
    def isRunning(self):
        return self.__draw_thread.is_alive()

    def _draw(self):
        """Das Input Feld wird auf dem Bildschirm dargestellt"""
        
        self.display.fill(BLACK)
        
        # Title
        self.display.text(self.title, 4, 4, WHITE)
        
        # input box
        self.display.rect(0, 15, self.display.width, 16, WHITE)
        self.display.text(self.__get_text(), 4, 19, WHITE)
        
        # Zurück Button (self.__nav_p == -2)
        if -2 == self.__nav_p:
            self.display.fill_rect(10, 40, 45, 16, WHITE)
            self.display.text('Abbr', 20, 44, BLACK)
        else: 
            self.display.rect(10, 40, 45, 16, WHITE)
            self.display.text('Abbr', 20, 44, WHITE)
        
        # Okay Button (self.__nav_p == -1)
        if -1 == self.__nav_p:
            self.display.fill_rect(self.display.width - 55, 40, 45, 16, WHITE)
            self.display.text('Okay', self.display.width - 45, 44, BLACK)
        else: 
            self.display.rect(self.display.width - 55, 40, 45, 16, WHITE)
            self.display.text('Okay', self.display.width - 45, 44, WHITE)
        
        self.cursor.set_position(max([4, (4 + self.__nav_p * 6)]), 28)
        if not self.is_pointer_on_button(): self.cursor.draw()
        
        self.display.show()
    
    def __get_text(self):
        text = ""
        for i in self.char_i:
            text += CHAR_SET[i]
        return text
    
    def __append_text(self, text: str):
        for c in text:
            self.char_i.append(CHAR_SET.find(c))
            
    def is_pointer_on_button(self):
        return self.__nav_p < 0
    
    def is_pointer_on_char(self):
        return self.__nav_p >= 0 and self.__nav_p < len(self.char_i)
    
    def is_pointer_after_text(self):
        return self.__nav_p == len(self.char_i)