import math
import threading
from typing import Callable, Union
import pigpio
import time

BIT_SEND_TIME = 0.0001  # seconds
BODY_SIZE     = 8      # bytes
SEND_TIME_OUT = 30      # seconds

def print_bits(bytes):
    bit_string = bin(bytes)[2:]
    print(bit_string.replace('0', '_'))

class BitBuffer:
    def __init__(self, max_bytes:int=1):
        self.buffer = 0                 # Store bits as an integer
        self.bit_length = 0             # Number of valid bits
        self.max_bits = max_bytes * 8   # Maximum bits allowed

    def append(self, bit):
        """Appends a single bit and shifts if exceeding max size."""
        self.buffer = (self.buffer << 1) | (bit & 1)  # Append bit
        self.bit_length += 1
        
        # If buffer exceeds max size, discard the oldest bits
        if self.bit_length > self.max_bits:
            self.buffer &= (1 << self.max_bits) - 1
            self.bit_length = self.max_bits
            
    def to_bytes(self) -> bytes:
        """Converts the buffer to a bytearray."""
        num_bytes = (self.bit_length + 7) // 8  # Round up to full bytes
        return self.buffer.to_bytes(num_bytes, 'big')
    
    def get_byte(self, index: int):
        """Returns the byte at the given index or raises an EOFError if out of bounds."""
        num_bytes = (self.bit_length + 7) // 8  # Total bytes in buffer

        if index < 0 or index >= num_bytes:
            raise EOFError("Byte index out of range")

        shift_amount = (num_bytes - 1 - index) * 8  # Calculate shift
        return (self.buffer >> shift_amount) & 0xFF  # Extract the byte
    
    def starts_with(self, prefix: bytes) -> bool:
        """Checks if the buffer starts with the given byte sequence efficiently."""
        prefix_bits = len(prefix) * 8
        if self.bit_length < prefix_bits:
            return False  # Not enough bits to compare

        mask = (1 << prefix_bits) - 1  # Mask to extract only the first N bits
        buffer_start = (self.buffer >> (self.bit_length - prefix_bits)) & mask
        prefix_value = int.from_bytes(prefix, 'big')

        return buffer_start == prefix_value
    
    def is_full(self) -> bool:
        """Checks if the buffer has reached its maximum size."""
        return self.bit_length == self.max_bits
    
    def print_bits(self):
        """Prints the bits in the buffer where 0 is '_' and 1 is '#'."""
        bit_string = bin(self.buffer)[2:].zfill(self.bit_length)  # Convert to binary string
        print(bit_string.replace('0', '_'))

class Package:
    def __init__(self,
            target_address: bytes,
            src_address: bytes,
            total_packages: int,
            package_number: int,
            body: bytes,
            parity: Union[bytes, None] = None
        ):
        """
        This class represents a package that is sent over the serial line.
        It has attributes for target address, source address, total packages, package number, body, and parity.
        """
        
        if len(body) < BODY_SIZE:
            raise ValueError(f"Body size should not be less than {BODY_SIZE} bytes")
        
        self.__target_address   = target_address                    # two bytes
        self.__src_address      = src_address                       # two bytes
        self.__total_packages   = total_packages.to_bytes(2, 'big') # two bytes
        self.__package_number   = package_number.to_bytes(2, 'big') # two bytes
        self.__body             = body                              # a lot of bytes

        if parity is not None: 
            self.__parity       = parity                            # store parity byte
        else: 
            self.__parity       = self.__calc_parity()              # or calculate it if not provided
        
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Package':
        """
        Creates a Package object from a byte array.
        """
        if len(data) < 8 + BODY_SIZE + 1:
            raise ValueError(f"Body cannot be created from the given data. {len(data)} bytes is too short.")
        
        return cls(
            data[0:2],                         # target_address
            data[2:4],                         # source_address
            int.from_bytes(data[4:6], 'big'),  # total_packages
            int.from_bytes(data[6:8], 'big'),  # package_number
            data[8: 8 + BODY_SIZE],            # body
            data[-1:]                          # parity
        )
           
    def get_target_address(self):
        return self.__target_address
        
    def get_src_address(self):
        return self.__src_address
    
    def get_total_packages(self):
        return self.__total_packages

    def get_total_packages_int(self):
        return int.from_bytes(self.__total_packages, 'big')
    
    def get_package_number(self):
        return self.__package_number
        
    def get_package_number_int(self):
        return int.from_bytes(self.__package_number, 'big')
        
    def get_body(self):
        return self.__body
    
    def is_valid(self) -> bool:
        """
        Validate the package by checking the parity.
        """
        return self.__calc_parity() == self.__parity
            
    
    def to_bytes(self) -> bytes:
        """
        Combine all the attributes into a single byte array.
        The parity attribute is not included in the final byte array.
        """
        return b''.join([
            self.__target_address,
            self.__src_address,
            self.__total_packages,
            self.__package_number,
            self.__body,
            self.__parity
        ])
        
    def __calc_parity(self) -> bytes:
        """
        Generates a parity byte from the header and the body of the Package.
        The parity byte is computed using XOR over all bytes in the Package.
        """
        package_bytes = b''.join([
            self.__target_address,
            self.__src_address,
            self.__total_packages,
            self.__package_number,
            self.__body,
        ])
        parity = 0
        for byte in package_bytes:
            parity ^= byte  # XOR all bytes together
        return bytes([parity])  # Return the single parity byte as a bytes object

class PackageList:
    def __init__(self):
        self.__packages: list[Package] = []

    def add(self, package: Package):
        """add a package to the list, if the number don't exist."""
        package_number = package.get_package_number()
        found = [package for package in self.__packages if package.get_package_number() == package_number]
        if len(found) <= 0:
            self.__packages.append(package)
        # self.__packages = list({package.get_package_number(): package for package in self.__packages}.values())
        
    def has(self, package_number: int) -> bool:
        return len([package for package in self.__packages if package.get_package_number_int() == package_number]) > 0
    
    def remove(self, package_number: int):
        """remove a package from the list by package number"""
        self.__packages = [package for package in self.__packages if package.get_package_number_int()!= package_number]
    
    def concatenate(self, package_list: 'PackageList') -> 'PackageList':
        """concatenate this package list with another package list and return the result"""
        result = PackageList()
        result.__packages = self.__packages.copy()
        result.__packages.extend(package_list.get_packages())
        return result
    
    def get_packages(self) -> list[Package]:
        return self.__packages
    
    def get_length(self) -> int:
        return len(self.__packages)
    
    def get_package_numbers(self) -> list[bytes]:
        """return a list of all existing package numbers"""
        return [package.get_package_number() for package in self.__packages] # create a list of arrived packages as body
    
    def get_package_numbers_int(self) -> list[int]:
        """return a list of all existing package numbers"""
        return [package.get_package_number_int() for package in self.__packages] # create a list of arrived packages as body
    
    def is_valid_message(self) -> bool:
        """check if all packages have arrived and the total number of packages matches the total packages attribute of the first package"""
        
        if len(self.__packages) == 0:
            return False
        
        first_package = self.__packages[0]
        if len(self.__packages) != first_package.get_total_packages_int():
            return False
        
        # Check if all packages have the same target address
        src_addresses = [package.get_src_address() for package in self.__packages]
        if len(set(src_addresses))!= 1:
            return False
        
        # Check if all packages have the same total_number
        total_packages = [package.get_total_packages() for package in self.__packages]
        if len(set(total_packages))!= 1:
            return False
        
        return True
    
    @classmethod
    def from_message( cls, target_address: bytes, src_address: bytes, message: bytes, fill_byte= b'\x00' ) -> 'PackageList':
        package_list: PackageList = cls()

        total_message_length = len(message)
        total_packages = math.ceil(total_message_length / BODY_SIZE)
                
        # add full packages
        for package_number in range(total_packages):
            
            body_start = package_number * BODY_SIZE
            body_end = min(body_start + BODY_SIZE, total_message_length)
                        
            package = Package(
                target_address,
                src_address,
                total_packages,
                package_number,
                message[body_start : body_end].ljust(BODY_SIZE, fill_byte)  # get the body of the package
            )
                        
            package_list.add(package)
        
        return package_list
    
    def to_message(self) -> bytes:
        """Accepts a array of packages. Returns a Message if all packages have arrived"""
        
        # Construct the message by concatenating all package bodies in the order of his numbers
        self.__sort()
        return b''.join([p.get_body() for p in self.__packages])
        
    def __sort(self) -> None:
        self.__packages = sorted(self.__packages, key=lambda package: package.get_package_number_int())
        
    def to_bytes(self) -> bytes:
        """
        Serialize the PackageList into a byte array.
        """
        return b''.join([package.to_bytes() for package in self.__packages])

class RFClient:
    HEADER_BYTES = 8  # target address, source address, total packages, package number
    PARITY_BYTES = 1  # parity hash 1 byte on the end of each package
    SILENCE_TIME = BIT_SEND_TIME * 2000 # the silence time between between messages is 2000 times the BIT_SEND_TIME

    def __init__(self, pi: pigpio.pi, send_gpio: int, read_gpio: int, device_address: bytes):
        """
        - pi: a pigpio.pi object
        - the send_gpio can be the same as the read_gpio
        - the device_address has two bytes
        """
        self.__pi: pigpio.pi = pi
        
        self.__read_gpio: int = read_gpio
        self.__send_gpio: int = send_gpio
        self.__device_address: bytes = device_address
        
        self.__last_bit_send = 0
        self.__last_bit_read = 0
        
        # Callback gets the message as bytes and the number if lost_packages
        self.__subscribers: list[Callable[[bytes, int],None]] = []
                        
        self.thread: threading.Thread
        self.__start_listening()
        
    def __activate_reading_mode(self):
        if self.__pi.get_mode(self.__read_gpio) != pigpio.INPUT:
            self.__pi.set_mode(self.__read_gpio, pigpio.INPUT)
            self.__pi.set_pull_up_down(self.__read_gpio, pigpio.PUD_DOWN)
        
    def __activate_writing_mode(self):
        if self.__pi.get_mode(self.__send_gpio) != pigpio.OUTPUT:
            self.__pi.set_mode(self.__send_gpio, pigpio.OUTPUT)
        
    def on_message(self, callback: Callable[[bytes],None]):
        self.__subscribers.append(callback)
        
    def send_message(self, target_address: bytes, message: bytes) -> Union[int, None]:
        self.__stop_listening()
        package_list: PackageList = PackageList.from_message(
            target_address, 
            self.__device_address, 
            message
        )
        
        lost_packages = 0
        
        start_time = time.time()
        
        # repeat sending until all packages arrive the target
        while package_list.get_length() > 0:
            self.__activate_writing_mode()
                        
            for package in package_list.get_packages():
                self.__send_package(package)
            
            # this starts the listening loop that runs until no package arrives for a given time (timeout)
            
            response = PackageList()
            self.__activate_reading_mode()
            time.sleep(self.SILENCE_TIME)  # wait until receiver detect the silence and start listening for response
            while True:
                # find a package on the stream with target_address of this device
                package = None
                package = self.__wait_for_next_package(self.SILENCE_TIME)
                if package is None: break
                response.add(package)
                
            # if response arrived handle valid packages from the response
            if response.get_length() > 0:
                # if a response arrives get the successful arrived package_numbers and slice it from the packages_array
                response_body = response.to_message()
                
                # divide the body to chunks of 2 bytes because package numbers are 2 bytes long
                successful_numbers: list[int] = [int.from_bytes(byte_pair, 'big') for byte_pair in zip(response_body[::2], response_body[1::2])]
                
                current_numbers = package_list.get_package_numbers_int()
                successful_numbers: list[int] = [number for number in successful_numbers if number != 0xFFFF and number in current_numbers]
                
                lost_packages += package_list.get_length() - len(successful_numbers)
                                
                # remove successful packages from the list to send
                {package_list.remove(package_number) for package_number in successful_numbers}
                            
            if time.time() - start_time > SEND_TIME_OUT: return None
            
        self.__start_listening()
        return lost_packages

    def __start_listening(self):
        self.thread = threading.Thread(name='rf_client_loop', target=self.__read_bit_stream, daemon=False)
        self.thread.start()
        
    def __stop_listening(self):
        self.listening = False
        if self.thread.is_alive():  # wait for the thread to finish its job
            self.thread.join()
    
    def __read_bit_stream(self):
        packages = PackageList()
        lost_packages = 0
                        
        self.listening = True
        while self.listening:
            self.__activate_reading_mode()
            
            # find a package on the stream with target_address of this device
            package = self.__wait_for_next_package(self.SILENCE_TIME)
            
            # escape the function because listening flag is false
            if not self.listening: return  
            
            # if package arrives store it to burst
            if package is not None:
                packages.add(package)
                
            # if timeout handle burst
            elif packages.get_length() > 0:
                self.__activate_writing_mode()
                
                lost_packages += packages.get_packages()[0].get_total_packages_int() - packages.get_length()
                
                response: PackageList = PackageList.from_message(
                    target_address  = packages.get_packages()[0].get_src_address(),
                    src_address     = self.__device_address,
                    message         = b"".join(packages.get_package_numbers()),
                    fill_byte=b'\xFF'  # fill rest of the package with 255
                )
                
                # if more packages are expected
                if not packages.is_valid_message():
                    
                    # receiver sends response packages
                    for package in response.get_packages():
                        self.__send_package(package)
                    time.sleep(self.SILENCE_TIME) # wait for sender to detect silence

                # else message is ready
                else:
                    
                    # receiver sends response packages multiple times to make sure the sender stops sending
                    for _ in range(3):  # repeat
                        for package in response.get_packages():
                            self.__send_package(package)
                    
                    # built message and send it to the subscribers
                    message = packages.to_message()
                    for s in self.__subscribers:
                        s(message, lost_packages)
                        
                    time.sleep(self.SILENCE_TIME) # wait for sender to detect silence
                    
                    # clear arrived packages and listen for next message
                    packages = PackageList()
                    lost_packages = 0

    def __wait_for_next_package(self, timeout: float) -> Union[Package, None]:
        """Read the stream until a package with this address of the device is on the bit_buffer or timeout is exceeded ."""        
        timeout_counter = int(timeout / BIT_SEND_TIME)
        
        bit_buffer = BitBuffer(BODY_SIZE + self.HEADER_BYTES + self.PARITY_BYTES)
        self.listening = True
        while self.listening:
            bit = self.__read_bit()
            bit_buffer.append(bit)
            time.sleep(BIT_SEND_TIME)
            
            if timeout_counter <= 0:
                return None  # timeout reached, stop listening and return None
            timeout_counter -= 1
            
            if bit_buffer.is_full() and bit_buffer.starts_with(self.__device_address):
                package = Package.from_bytes(bit_buffer.to_bytes())
                if package.is_valid():
                    return package
        return None

    def __read_bit(self) -> int:
        bit = self.__pi.read(self.__read_gpio)
        if self.__last_bit_read != bit:
            self.__last_bit_read = bit
            return 1
        else:
            return 0

    def __send_package(self, package: Package):
        for byte in package.to_bytes():
            for i in range(7, -1, -1):  # Restliche Bits
                bit = (byte >> i) & 1
                if bit == 1:  # Nur wenn Änderung
                    self.__last_bit_send = self.__last_bit_send ^ 1 # alternate bit
                self.__pi.write(self.__send_gpio, self.__last_bit_send)
                time.sleep(BIT_SEND_TIME)


# import json

# HEADER_BYTES = 8  # target address, source address, total packages, package number
# PARITY_BYTES = 1  # parity hash 1 byte on the end of each package
# BIT_TIME = 5

# # Initialize pigpio
# pi = pigpio.pi()
# if not pi.connected:
#     exit()


# RX_GPIO = 13  # Receiving GPIO

# received_data = PackageList()
# bit_buffer = BitBuffer(BODY_SIZE + HEADER_BYTES + PARITY_BYTES)
# last_tick = (time.time_ns() // 1000)
# message_counter = 0

# message_as_bytes = "Hallo Welt!".encode()

# message_as_bytes = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat".encode()

# # Example bytes object to send
# package_list = PackageList.from_message(int.to_bytes(1234, 2, 'big'), int.to_bytes(5678, 2, 'big'), message_as_bytes)
# print(f'Message length: {package_list.get_length()}')
# data = package_list.to_bytes()

# def rx_callback(gpio, level, tick):
#     global last_tick, bit_buffer, received_data, data, message_counter
#     dif = tick - last_tick
#     last_tick = tick
#     for _ in range(min(dif // BIT_TIME, bit_buffer.max_bits)):
#         bit_buffer.append(level^1)
#         if bit_buffer.is_full() and bit_buffer.starts_with(int.to_bytes(1234, 2, 'big')):
#             package = Package.from_bytes(bit_buffer.to_bytes())
#             if package.is_valid():
#                 received_data.add(package)
#                 bit_buffer = BitBuffer(BODY_SIZE + HEADER_BYTES + PARITY_BYTES)
#                 if received_data.is_valid_message():
#                     message_counter += 1
#                     print(f'Received message {message_counter}: {received_data.to_message().decode()}')
#                     received_data = PackageList()


# pi.set_mode(RX_GPIO, pigpio.INPUT)
# pi.callback(RX_GPIO, pigpio.EITHER_EDGE, rx_callback)

# TX_GPIO = 5  # Sending GPIO

# # Ensure the TX GPIO is set as OUTPUT
# pi.set_mode(TX_GPIO, pigpio.OUTPUT)

# # Convert bytes to waveform
# last_bit_send = 0
# wave = []
# for byte in data:
#     for i in range(8):
#         bit = (byte >> (7 - i)) & 1  # Extract each bit
#         if bit:
#             wave.append(pigpio.pulse(1 << TX_GPIO, 0, BIT_TIME))  # HIGH
#         else:
#             wave.append(pigpio.pulse(0, 1 << TX_GPIO, BIT_TIME))  # LOW
        
# # wave.append(pigpio.pulse(0, 1 << TX_GPIO, 100000)) # LOW

# # Send the waveform
# pi.wave_clear()
# pi.wave_add_generic(wave)
# wave_id = pi.wave_create()

# # Transmit the waveform
# # for _ in range(100):  # repeat
# pi.wave_send_repeat(wave_id)

# # Wait for completion
# while pi.wave_tx_busy():
#     time.sleep(0.001)

# # Clean up
# pi.wave_delete(wave_id)

# pi.stop()

# exit()



# # Beispielverwendung:
# # if __name__ == "__main__":

from core.io import IO
import json

# message subscriber
client1 = RFClient(IO().get_pigpio(), 5, 5, int.to_bytes(5678, 2, 'big'))
client1.on_message(lambda payload, lost_packages: print(f"Receiver1 detects lost_packages: {lost_packages}. Message: {payload.decode('utf-8')}"))

# client2 = RFClient(IO().get_pigpio(), 13, 13, int.to_bytes(1234, 2, 'big'))
# client2.on_message(lambda payload, lost_packages: print(f"Receiver2 detects lost_packages: {lost_packages}. Message: {payload.decode('utf-8')}"))

counter = 0

time.sleep(0.5)

while True:
    
    start_time = time.time()
    
    lost_packages1 = client1.send_message(int.to_bytes(1234, 2, 'big'), f'{counter}. Hallo!'.encode('utf-8'))
    print(f"sender1 lost_packages: {lost_packages1}")
    
    # lost_packages2 = client2.send_message(
    #     int.to_bytes(5678, 2, 'big'),
    #     json.dumps([
    #         {
    #         "name": "John",
    #         "age": 10,
    #         "address": {
    #                 "street": "Main Street",
    #                 "number": 123,
    #                 "zip_code": "12345",
    #                 "country": "USA"
    #             }
    #         },
    #         {
    #         "name": "Wick",
    #         "age": 20,
    #         "address": {
    #                 "street": "Broadway",
    #                 "number": 456,
    #                 "zip_code": "67890",
    #                 "country": "Germany"
    #             }
    #         },
    #         {
    #         "name": "Max",
    #         "age": 30,
    #         "address": {
    #                 "street": "Hauptstraße",
    #                 "number": 789,
    #                 "zip_code": "23456",
    #                 "country": "Austria"
    #             }
    #         },
    #     ]).encode()
    # )
    # print(f"sender2 lost_packages: {lost_packages2}")

    print(f"send duration: {time.time() - start_time}")
    counter += 1
    
    time.sleep(0.5)

exit()