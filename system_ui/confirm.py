#!/usr/bin/python3
# -*- coding: utf8 -*-

import threading
from core.logger import get_logger
from abstract_base_classes.ui_controls import UIControls

from typing import Callable, Union

from custom_libs.adafruit_framebuf import FrameBuffer

WHITE = 1
BLACK = 0

class Confirm():
    def __init__(self, display: FrameBuffer, controls: UIControls, okay_func: Callable, cancel_func: Callable, title="Confirm", text="Wollen Sie fortfahren?"):
        self.display = display
        self.controls = controls

        self.title = title
        
        self.text = text

        self.__okay_func = okay_func
        self.__cancel_func = cancel_func
        
        self.okay_unlocked = False
        self.cancel_unlocked = False
        
        self.reset_timer: Union[threading.Timer, None] = None
        
        self.controls.reset_callbacks()
        self.controls.on_next(lambda: self.__okay_action())
        self.controls.on_okay(lambda: self.__okay_action())
        self.controls.on_prev(lambda: self.__cancel_action())
        self.controls.on_back(lambda: self.__cancel_action())
        self._draw()

    def __okay_action(self):
        if self.okay_unlocked is False:
            self.okay_unlocked = True
            self.cancel_unlocked = False
            self._draw()
            self.__start_reset_timer()
        else:
            if self.reset_timer is not None: self.reset_timer.cancel()
            self.__okay_func()

    def __cancel_action(self):
        if self.cancel_unlocked is False:
            self.cancel_unlocked = True
            self.okay_unlocked = False
            self._draw()
            self.__start_reset_timer()
        else:
            if self.reset_timer is not None: self.reset_timer.cancel()
            self.__cancel_func()
            
    def __reset_actions(self):
        self.okay_unlocked = False
        self.cancel_unlocked = False
        self._draw()
    
    def __start_reset_timer(self):
        if self.reset_timer is not None:
            self.reset_timer.cancel()
        # Run the callback after 1 seconds
        self.reset_timer = threading.Timer(1.0, lambda: self.__reset_actions())
        self.reset_timer.start()

    def _draw(self):
        """Das Input Feld wird auf dem Bildschirm dargestellt"""
        
        self.display.fill(BLACK)
        
        # Title center
        self.display.text(
            self.title, 
            x=int(self.display.width / 2) - len(self.title) * 6, 
            y=2, 
            color=WHITE, 
            size=2
        )
        
        # Text
        length=20
        lines = [self.text[i:i+length] for i in range(0, len(self.text), length)]
        for index, line in enumerate(lines):
            self.display.text(
                line.strip(),
                x=5, 
                y=20 + index * 8,
                color=WHITE
            )
        
        button_hight = 16
        button_width = 45
        button_margin_x = 10
        
        button_row_y = self.display.height - button_hight - 4  # relative to bottom

        # Zurück Button
        if self.cancel_unlocked:
            self.display.fill_rect(button_margin_x, button_row_y, button_width, button_hight, WHITE)
            self.display.text('Abbr', x=button_margin_x + 10, y=button_row_y + 4, color=BLACK)
        else: 
            self.display.rect(button_margin_x, button_row_y, button_width, button_hight, WHITE)
            self.display.text('Abbr', x=button_margin_x + 10, y=button_row_y + 4, color=WHITE)
        
        
        # Okay Button
        button_column_2_x = self.display.width - button_width - button_margin_x  # relative to right side of screen
        if self.okay_unlocked:
            self.display.fill_rect(button_column_2_x, button_row_y, button_width, button_hight, WHITE)
            self.display.text('Okay', x=button_column_2_x + 10, y=button_row_y + 4, color=BLACK)
        else: 
            self.display.rect(button_column_2_x, button_row_y, button_width, button_hight, WHITE)
            self.display.text('Okay', x=button_column_2_x + 10, y=button_row_y + 4, color=WHITE)
        
        self.display.show()