class IOInitializationException(Exception):
    def __init__(self, message=None, gpio=None):
        self.message = message or "An error occurred during GPIO initialization."
        self.gpio = gpio
        super().__init__(self.message)