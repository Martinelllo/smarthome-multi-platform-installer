import logging
from datetime import datetime
import os
from pathlib import Path

def __get_file_path() -> Path: 
    # Pfad zum Parent des aktuellen Skripts
    return Path(__file__).parent.parent / 'logs'

def __get_file_name() -> str: 
    # Erstellen eines relativen Pfads mit Datum
    datum = datetime.now().strftime("%Y_%m_%d")
    return f"{datum}.log"


def __get_formatter() -> logging.Formatter: 
    return logging.Formatter('Time: %(asctime)s - [ %(filename)s:%(lineno)d ] - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

def get_logger():
    """
    Richtlinien:
    * debug ist für häufige Ereignisse wie z.B. Polling requests. 
    * info ist für seltene Ereignisse wie das Initialisieren der App oder der Module.
    * warning ist für Ereignisse, die potenziell schlimm sind, aber in manchen Situationen in kauf genommen werden können,
    wie z.B. wenn kein Bildschirm an dem gerät angeschlossen ist.
    * error ist für Errors die nicht passieren sollten und z.B. in einem Try -> Except abgefangen werden.
    * critical ist für Fehler die auf keinen fall auftreten dürfen.
    """
    
    logger = logging.getLogger('multi_platform_logger')     # Erstelle einen Logger
    logger.setLevel(logging.DEBUG)                          # level threshold for logger not for handler
 
    is_dev_env = '1' == os.getenv("DEVELOPMENT_ENV")        # Ermittle den Debug Level für die aktuelle Umgebung
    
    if is_dev_env:                                          # In Development Umgebung gebe Logs in der Console aus
        if logger.handlers:
            return logger
        console_handler = logging.StreamHandler()           # Erstelle einen Console Handler, der Nachrichten in der Console anzeigt
        console_handler.setLevel(logging.DEBUG)             # Logging Level for console_handler
        console_handler.setFormatter(__get_formatter())
        logger.addHandler(console_handler)

    else:                                                   # In einer productiven Umgebung gebe Logs einem logfile aus
        file_name = __get_file_name()                       # Prüfe oder erzeuge File Path
        if logger.handlers and logger.handlers[0].get_name() == file_name: # Prüfe ob der Handler mit diesem File Name existiert
            return logger
        if logger.handlers:                                 # Prüfe ob ein veralteten Handler existiert
            for handler in logger.handlers:                 # Schließe alle veralteten Handler
                handler.close()
            logger.handlers.clear()
        fiele_path = __get_file_path()                      # Prüfe oder erzeuge File Path
        if not os.path.exists(fiele_path):                  # Create file if not exist
            os.makedirs(fiele_path)
        file_handler = logging.FileHandler(fiele_path / file_name)      # Erstelle einen File Handler, der Nachrichten in eine Datei schreibt
        file_handler.setLevel(logging.ERROR)                # Logging Level for file_handler
        file_handler.setFormatter(__get_formatter())
        file_handler.set_name(file_name)
        logger.addHandler(file_handler)

    return logger

if __name__ == '__main__':

    # Logge Nachrichten
    get_logger().debug("Dies ist eine Debug-Nachricht.")    # Der debug wird nur in Entwicklungsumgebungen geloggt
    get_logger().info("Dies ist eine Info-Nachricht.")      # Eine info wird nur in Entwicklungsumgebungen geloggt
    get_logger().warning("Dies ist eine Warn-Nachricht.")
    get_logger().error("Dies ist eine Fehler-Nachricht.")
    get_logger().critical("Dies ist eine kritische Nachricht.", exc_info=True)