
import pigpio

class PinAdapter():
    
    OUT = pigpio.OUTPUT
    IN = pigpio.INPUT
    
    def __init__(self, gpio: int, pi = pigpio.pi()):
        self.gpio = gpio
        self.pi = pi
        self.pigpio = pi
        
    def init(self, mode, value=0):
        self.pigpio.set_mode(self.gpio, mode)
        self.pi.write(self.gpio, value)
        
    def __call__(self, value):
        self.state = value
        self.pi.write(self.gpio,value)
    