import json
import os

from abstract_base_classes.singleton_meta import SingletonMeta
from core.logger import get_logger

class ConfigStorage(metaclass=SingletonMeta):
    def __init__(self):
        try:
            relative_path = '../data/config.json'
            
            # Absoluter Pfad zum aktuellen Python-Skript
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Relativer Pfad zur Datei (basierend auf dem Ort der Python-Datei)
            self.file_path = os.path.join(script_dir, relative_path)

            # Ordner erstellen, falls nicht vorhanden
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            self.config = self.__load_config()
        except Exception as e:
            get_logger().error(f"Fehler beim Erzeugen der Config-Datei: {e}")
            raise e

    def __load_config(self):
        """Lädt die Konfiguration aus der Datei, falls sie existiert."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    print("Fehler beim Laden der JSON-Datei. Erstelle eine leere Konfiguration.")
                    return {}
        return {}

    def get(self, key, default=None):
        """Gibt einen Wert aus der Konfiguration zurück."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Setzt einen Wert in der Konfiguration und speichert die Datei."""
        self.config[key] = value
        self.__save_config()

    def __save_config(self):
        """Speichert die aktuelle Konfiguration in die Datei."""
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)

    def delete(self, key):
        """Löscht einen Schlüssel aus der Konfiguration und speichert die Datei."""
        if key in self.config:
            del self.config[key]
            self.__save_config()


if __name__ == "__main__":

    # Beispielnutzung
    config = ConfigStorage()
    config.set("username", "admin")
    config.set("timeout", 30)

    print(config.get("username"))  # Ausgabe: admin
    print(config.get("timeout", 10))  # Ausgabe: 30

    config.delete("username")
    print(config.get("username"))  # Ausgabe: None
