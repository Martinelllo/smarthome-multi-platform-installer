class DisplayInitializationException(Exception):
    def __init__(self, message=None, module_class=None, module_name=None):
        self.message = message or "An error occurred during display initialization."
        self.module_class = module_class
        self.module_name = module_name
        super().__init__(self.message)