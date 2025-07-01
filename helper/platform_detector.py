from core.logger import get_logger


def get_platform_model():
    try:
        with open("/proc/cpuinfo", "r") as file:
            for line in file:
                if "Model" in line:
                    return line.split(":")[1].strip()
    except FileNotFoundError:
        return "Nicht auf einem Raspberry Pi oder Datei nicht verfügbar."


def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temp_str = file.read()
            return float(temp_str) / 1000
    except FileNotFoundError as error:
        get_logger().error("Kann die CPU-Temperatur nicht auslesen.", error)
        return None


if __name__ == "__main__":
    
    # Platform ausgeben
    model = get_platform_model()
    print("Platform:", model)