__pin_gpio_map = {
    3: 2,    # Pin 3 -> GPIO 2
    5: 3,    # Pin 5 -> GPIO 3
    7: 4,    # Pin 7 -> GPIO 4
    8: 14,   # Pin 8 -> GPIO 14
    10: 15,  # Pin 10 -> GPIO 15
    11: 17,  # Pin 11 -> GPIO 17
    12: 18,  # Pin 12 -> GPIO 18
    13: 27,  # Pin 13 -> GPIO 27
    15: 22,  # Pin 15 -> GPIO 22
    16: 23,  # Pin 16 -> GPIO 23
    18: 24,  # Pin 18 -> GPIO 24
    19: 10,  # Pin 19 -> GPIO 10
    21: 9,   # Pin 21 -> GPIO 9
    22: 25,  # Pin 22 -> GPIO 25
    23: 11,  # Pin 23 -> GPIO 11
    24: 8,   # Pin 24 -> GPIO 8
    26: 7,   # Pin 26 -> GPIO 7
    29: 5,   # Pin 29 -> GPIO 5
    31: 6,   # Pin 31 -> GPIO 6
    32: 12,  # Pin 32 -> GPIO 12
    33: 13,  # Pin 33 -> GPIO 13
    35: 19,  # Pin 35 -> GPIO 19
    36: 16,  # Pin 36 -> GPIO 16
    37: 26,  # Pin 37 -> GPIO 26
    38: 20,  # Pin 38 -> GPIO 20
    40: 21   # Pin 40 -> GPIO 21
}

def map_gpio_for(pin):
    return __pin_gpio_map.get(pin)


if __name__ == "__main__":

    # Beispiel für die Verwendung
    import pigpio
    pi = pigpio.pi()

    pin_number: 3
    pin_value: 1

    gpio = map_gpio_for(pin_number)

    if gpio is not None:
        pi.write(gpio, pin_value)
    else:
        raise ValueError("Ungültige Pin-Nummer")
