#!/usr/bin/python3
# -*- coding: utf8 -*-

from custom_libs.adafruid_ssd1306 import SSD1306_I2C
from abstract_base_classes.ui_controls import UIControls

from typing import TYPE_CHECKING, Callable, Union

from custom_libs.adafruit_framebuf import FrameBuffer

if TYPE_CHECKING:
    from system_ui import SystemUI

WHITE = 1
BLACK = 0

class MenuNode():
    def __init__(self, name: str, callable: Union[ Callable[ [], Union[bool,None] ], None ]=None, menu: Union['Menu',None]=None):
        self.name = name
        self.callable = callable
        self.menu = menu


class Menu():
    def __init__(self, system_ui: 'SystemUI', parent: Union['Menu',None] = None) -> 'Menu':
        self.system_ui = system_ui
        
        self.nodes: list[MenuNode] = []
        self.parent = parent
        
        self.is_active = False
        
        self.on_draw_func: list[Callable]
        if parent: self.on_draw_func = parent.on_draw_func
        else: self.on_draw_func = []
        
        self.pointer = 0
        self.scrolled_y = 0

    def create_from_map(system_ui: 'SystemUI', map: dict[str, any], parent: Union['Menu',None] = None) -> 'Menu':
        """Erzeugt ein Baum anhand der Map. Die keys sind die Texte im Menü. Am ende eines Zweiges kommt eine Callable"""
        menu = Menu(system_ui, parent)
        for key, value in map.items():
            if isinstance(value, dict):
                # Recursive call
                sub_menu = Menu.create_from_map(system_ui, value, menu)
                menu.nodes.append(MenuNode(name=key, menu=sub_menu))
            elif callable(value):
                menu.nodes.append(MenuNode(name=key, callable=value))
            else:
                raise TypeError(f"Value on key '{key}' has type {type(value).__name__}. Expected is dict or Callable")
        return menu
    
    def patch_pointers(self, map: dict[str, any]):
        """Hier können Zweige der Map hinterlegt werden und am ende der index oder der Text des ausgewählten Feldes als Wert hinterlegt werden"""
        for key, value in map.items():
            item = next((x for x in self.nodes if x.name == key), None)
            if not item: raise TypeError(f"Item with name '{key}' not found on instance of: {self.__class__.__name__}")
            if not item.menu: raise TypeError(f"Item with name '{key}' is not a menu")
            if isinstance(value, dict):
                # Recursive call
                item.menu.patch_pointers(value)
            # set pointer with int
            elif isinstance(value, int):
                if value >= len(item.menu.nodes): raise TypeError(f"Item: '{value}' on Menu: '{key}' not found. The menu has '{len(item.menu.nodes)}' items.")
                item.menu.pointer = value
            # set pointer with name of button
            elif isinstance(value, str):
                selected_item_index = next((i for i, x in enumerate(item.menu.nodes) if x.name == value), None)
                if selected_item_index == None: raise TypeError(f"Item: '{value}' on Menu: '{key}' not found.")
                item.menu.pointer = selected_item_index
            else:
                raise TypeError(f"Value on key '{key}' has type {type(value).__name__}. Expected is dict or int")
    
    def activate(self):
        """Zeigt das Menü auf dem Bildschirm und bindet alle Controls an dieses Menü"""
        # if pointer is on a active menu activate this it instead otherwise the menu starts always on root
        if self.nodes[self.pointer].menu and self.nodes[self.pointer].menu.is_active:
            self.nodes[self.pointer].menu.activate()
        else: # set buttons on target menu
            self.is_active = True
            self.system_ui.controls.reset_callbacks()
            self.system_ui.controls.on_next(lambda: self.__next_action())
            self.system_ui.controls.on_prev(lambda: self.__prev_action())
            self.system_ui.controls.on_okay(lambda: self.__okay_action())
            self.system_ui.controls.on_back(lambda: self.__back_action())
            self._draw()
        
    def __next_action(self):
        self.pointer = (self.pointer + 1) % len(self.nodes)
        self._draw()
        
    def __prev_action(self):
        self.pointer -= 1
        if self.pointer < 0: self.pointer = len(self.nodes) - 1
        self._draw()
        
    def __okay_action(self):
        # if child is a menu set the menu active
        if self.nodes[self.pointer].menu is not None:
            self.nodes[self.pointer].menu.is_active = True
            self.nodes[self.pointer].menu.activate()
            
        # else if child is a function run 
        else:
            if self.nodes[self.pointer].callable() == True:
                self.__back_action()
        
    def __back_action(self):
        # mark all as inactive
        if self.parent:
            self.is_active = False # set inactive to avoid auto routing from parent again
            self.parent.activate()
    
    def on_draw(self, func: Callable):
        self.on_draw_func.append(func)

    def _draw(self):
        """Das menu wird auf dem Bildschirm dargestellt"""
        for func in self.on_draw_func: func()
        
        row_height = 12
        
        # calc self.scrolled_y with cursor position
        cursor_top = next((i for i,x in enumerate(self.nodes) if i == self.pointer), None) * row_height
        if cursor_top + 12 - self.scrolled_y > 64: self.scrolled_y = cursor_top - 64 + row_height
        if cursor_top - self.scrolled_y < 0: self.scrolled_y = cursor_top
        
        self.system_ui.display.fill(0)
        for index, item in enumerate(self.nodes):
            # draw row
            row_top = (index * row_height) - self.scrolled_y
            
            if index == self.pointer: # white background black digits (active element)
                self.system_ui.display.fill_rect(0, row_top, self.system_ui.display.width, row_height, WHITE)
                if item.menu: self.system_ui.display.line(2, row_top+5, 5, row_top+5, BLACK)
                else: self.system_ui.display.fill_rect(3, row_top+4, 2, 2, BLACK)
                self.system_ui.display.text(item.name, 8, row_top+2, BLACK)
                
            else: # white digits on black background
                if item.menu: self.system_ui.display.line(2, row_top+5, 5, row_top+5, WHITE)
                else: self.system_ui.display.fill_rect(3, row_top+4, 2, 2, WHITE)
                self.system_ui.display.text(item.name, 8, row_top+2, WHITE)
                
        self.system_ui.display.show()
