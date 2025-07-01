from typing import Union


class SensorConfig():
    def __init__(self, config):
        if not config['id']: raise TypeError('SensorConfig needs a "id" to work')
        if not config['type']: raise TypeError('SensorConfig needs a "type" to work')
        
        self.id = config['id']
        self.type = config['type']

    def get_id(self) -> int:
        return self.id
    
    def is_type(self, type: str) -> bool:
        return self.type == type
    
class ControllerConfig():
    def __init__(self, config):
        self.patch_config(config)

    def patch_config(self, config):
        if not config['id']: raise TypeError('ControllerConfig needs a "id" to work')
        if not config['type']: raise TypeError('ControllerConfig needs a "type" to work')
       
        if 'defaultValue' in config: self.defaultValue = config['defaultValue'] 
        else: self.defaultValue = None

        self.controller_id = config['id']
        self.controller_type = config['type']

    def get_id(self) -> int:
        return self.controller_id
    
    def is_type(self, type: str) -> bool:
        return self.controller_type == type
    
    def has_default_value(self) -> bool:
        """Gibt alle defaultValues oder None zurück"""
        return bool(self.defaultValue)
    
    def get_default_values(self) -> Union[dict, None]:
        """Gibt alle defaultValues oder None zurück"""
        return self.defaultValue
    
    def get_default_value(self, key: str) -> any:
        """Gibt den Wert eines defaultValues oder None zurück"""
        if not key or not isinstance(key, str): raise KeyError("getValue function expects a key on the params")
        values = self.get_default_values()
        if values and key in values:
            return values[key]
        else: raise KeyError("Key: " + key + " not in values")
            
class ModuleConfig():
    def __init__(self, config):
        self.module_sensors: list[SensorConfig] = []
        self.module_controllers: list[ControllerConfig] = []

        if not config['name']:                      raise TypeError('ModuleConfig needs a "name" to work')
        if not config['moduleId']:                  raise TypeError('ModuleConfig needs a "moduleId" to work')
        if not config['type']:                      raise TypeError('ModuleConfig needs a "type" to work')
        if not config['readingInterval']:           raise TypeError('ModuleConfig needs a "readingInterval" to work')
        if not isinstance(config['sensors'], list): raise TypeError('ModuleConfig needs a list of "sensors" to work')
        for sensor in config['sensors']:
            if not isinstance(sensor, dict):        raise TypeError('ModuleConfig needs a list of "sensors" to work. The list exists but it has errors in it.')
            
        self.name = config['name']
        self.id = config['moduleId']
        self.type = config['type']
        self.interval = config['readingInterval']
        self.interface = config['interface']

        for sensor_config in config['sensors']:
            new_s_config = SensorConfig(sensor_config)
            old_s_config = self.get_sensor_config_by_id(new_s_config.get_id())
            if old_s_config: 
                old_s_config.patch_config(sensor_config)
            else:
                self.module_sensors.append(new_s_config)
                
        for controller_config in config['controllers']:
            new_c_config = ControllerConfig(controller_config)
            old_c_config = self.get_controller_config_by_id(new_c_config.get_id())
            if old_c_config: 
                old_c_config.patch_config(controller_config)
            else:
                self.module_controllers.append(new_c_config)
                
    def get_sensor_config_by_id(self, id):
        for item in self.module_sensors:
            if item and item.get_id() == id:
                return item
        return None
    
    def get_controller_config_by_id(self, id):
        for item in self.module_controllers:
            if item and item.get_id() == id:
                return item
        return None
    
    def get_id(self):
        return self.id
    
    def is_type(self, type: str) -> bool:
        return self.type == type
    
    def get_interval(self) -> float:
        """Gibt Sekunden wieder"""
        return self.interval / 1000
    
    def get_interface(self):
        """Deprecated: use get_pin_by_key(key) instead."""
        return self.interface
    
    def get_pin_by_key(self, key) -> Union[int, None]:
        """Gibt die Pin als Nummer aus. Als Key wird meistens 'PIN verwendet' wenn es nur einen im interface gibt"""
        if not self.interface: return None
        return self.interface[key]
    
    def get_sensors(self):
        return self.module_sensors
    
    def get_controllers(self):
        """Most Modules have only one controller"""
        return self.module_controllers


class DeviceConfig():
    def __init__(self, config: dict):
        if not config['id']:                                    raise TypeError('DeviceConfig needs a "id" to work')
        if not config['name']:                                  raise TypeError('DeviceConfig needs a "name" to work')
        if not config['modules']:                               raise TypeError('DeviceConfig needs a "modules" to work')
        if not isinstance(config['modules'], list):             raise TypeError('DeviceConfig "modules" should be a list')
        
        self.config = config
        
        self.modules: list[ModuleConfig] = []
        
        for module in config['modules']:
            module = ModuleConfig(module)
            self.modules.append(module)
    
    def get_id(self):
        return self.config['id']
    
    def get_name(self):
        return self.config['name']

    def get_config_by_id(self, id):
        for item in self.modules:
            if item and item.get_id() == id:
                return item
        return None

    def get_config_by_type(self, type: str):
        for item in self.modules:
            if item.is_type() == type:
                return item
        return None
    
    def has_module_with_type(self, type: str) -> bool:
        if self.get_config_by_type(type):
            return True
        return False

    def get_all_configs(self):
        return self.modules
    