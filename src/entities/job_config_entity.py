
from typing import Union


class TaskEntity():
    def __init__(self, config: dict):
        self.task = config
        
        if 'duration' not in config or not isinstance(config['duration'], int): raise TypeError('TaskEntity needs a "duration" to work')
        if 'value' not in config or not isinstance(config['value'], (dict)): raise TypeError('TaskEntity needs a "value" to work')
        
    def get_duration(self) -> float:
        """Gibt die Dauer in Sekunden als float zurück"""
        return self.task['duration'] / 1000
        
    def get_values(self) -> dict:
        """Gibt alle Values zurück"""
        return self.task['value']

        
    def get_value(self, key: str) -> any:
        """Gibt den Wert eines Value oder None zurück"""
        if not key or not isinstance(key, str): raise KeyError("getValue function expects a key on the params")
        values = self.get_values()
        if values and key in values:
            return values[key]
        else: raise KeyError("Key: " + key + " not in values")
        
    def get_transition_style(self) -> Union[str, None]:
        """Gibt den Transition Style als string oder None zurück"""
        if 'transition' in self.task:
            return self.task['transition']
        else:
            return None
     

class JobEntity():
    def __init__(self, config: dict):
        self.job = config
        
        if not isinstance(config['tasks'], list): raise TypeError('JobEntity needs a list of "tasks" to work')
        # if 'offset' not in config or not isinstance(config['offset'], int): raise TypeError('JobEntity needs a "offset" to work')

        self.tasks = []
        
        for task in self.job['tasks']:
            self.tasks.append(TaskEntity(task))
        
    def get_tasks(self) -> list[TaskEntity]:
        return self.tasks
    
    def get_offset(self) -> Union[float, None]:
        """Waiting time to the next job run in Seconds or None"""
        if 'offset' not in self.job or not isinstance(self.job['offset'], int): 
            return None
        return self.job['offset'] / 1000

    