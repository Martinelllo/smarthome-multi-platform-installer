from digitalio import DigitalInOut
import board
import busio
from cpc import CC1101

myspi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = DigitalInOut(board.D12)
gdo0 = DigitalInOut(board.D5)

syncword = '666A'

radio = CC1101(myspi, cs, gdo0, 50000, 434400000, syncword)

def transmit(payload: str):
    radio.setupTX()
    bitstring = ''.join(f'{ord(char):08b}' for char in payload)
    radio.sendData(bitstring, syncword)

def receive():
    radio.setupRX()
    while True:
        payload = radio.receiveData(0x19)
        print(payload)
        

if __name__ == '__main__':

    # Transmit
    transmit('Hallo World.')
    
    # Receive
    receive()