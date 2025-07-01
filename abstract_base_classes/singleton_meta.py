

class SingletonMeta(type):
    """
    A Class that inherits from the Singleton metaclass exists only ones. 
    Even if you initialize it multiple times but it can not have a parameters __init__() method.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]