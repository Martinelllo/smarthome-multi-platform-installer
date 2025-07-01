import sqlite3
import os
from typing import List, Dict
from core.logger import get_logger
from abstract_base_classes.singleton_meta import SingletonMeta
import time

class TempDB(metaclass=SingletonMeta):
    def __init__(self):
        try:
            relative_path = '../data/temporary_sensor_reading.db'
            
            # Absoluter Pfad zum aktuellen Python-Skript
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Relativer Pfad zur Datenbank (basierend auf dem Ort der Python-Datei)
            self.db_path = os.path.join(script_dir, relative_path)

            # Ordner erstellen, falls nicht vorhanden
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Verbindung zur SQLite-Datenbank herstellen (Datei wird erstellt, falls sie nicht existiert)
            conn = sqlite3.connect(self.db_path)

            # Cursor-Objekt erstellen, um SQL-Befehle auszuführen
            cursor = conn.cursor()


            # Tabelle erstellen (falls nicht existiert)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, -- Auto-Increment
                value REAL NOT NULL,                  -- Float-Wert
                sensor_id INTEGER NOT NULL,           -- Sensor-ID
                created_at INTEGER NOT NULL           -- UTC-Milliseconds seit 1970
            )
            ''')

            # Änderungen speichern
            conn.commit()
        except sqlite3.Error as e:
            get_logger().error(f"Fehler beim Erzeugen der Database: {e}")
            raise e

        finally:
            # Verbindung schließen
            if conn:
                conn.close()

    def safe_sensor_readings(self, sensor_readings: List[Dict]):
        """
        Speichert eine Liste von Sensor-Daten in der Tabelle sensor_readings.

        Args:
            sensor_readings (List[Dict]): Eine Liste von Dictionaries mit den Sensor-Daten. 
                Jedes Dictionary sollte folgende Keys haben:
                    - "value" (float): Der Messwert.
                    - "sensor_id" (int): Die ID des Sensors.
                    - "created_at" (int): UTC-Zeitstempel in Millisekunden seit 1970.
        Raises:
            sqlite3.Error: Bei Fehlern in der Datenbankoperation.
        """
        
        try:
            # Verbindung zur Datenbank herstellen
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # SQL-Statement für das Einfügen der Daten
            insert_query = '''
            INSERT INTO sensor_readings (sensor_id, value, created_at)
            VALUES (?, ?, ?)
            '''
            
            # UTC-Millisekunden seit 1970
            utc_milliseconds = int(time.time() * 1000)

            # Daten iterativ einfügen
            for reading in sensor_readings:
                cursor.execute(insert_query, (
                    reading['sensorId'],
                    reading['value'],
                    utc_milliseconds,
                ))

            # Änderungen speichern
            conn.commit()
            get_logger().debug(f"{len(sensor_readings)} Einträge erfolgreich gespeichert.")

        except sqlite3.Error as e:
            get_logger().error(f"Fehler beim Speichern der Sensor-Daten: {e}")
            raise e

        finally:
            # Verbindung schließen
            if conn:
                conn.close()
            
    def get_sensor_readings(self) -> List[Dict]:
        """
        Ruft alle Sensor-Daten ab.

        Returns:
            List[Dict]: Eine Liste von Dictionaries mit den Spaltenwerten der Tabelle.
        """
        try:
            # Verbindung zur Datenbank herstellen
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Abfrage der Sensor-Daten
            query = '''
            SELECT value, sensor_id, created_at 
            FROM sensor_readings 
            '''
            cursor.execute(query)
            rows = cursor.fetchall()

            # Ergebnisse als Liste von Dictionaries formatieren
            result = [
                {"value": row[0], "sensorId": row[1], "createdAt": row[2]}
                for row in rows
            ]
            return result

        except sqlite3.Error as e:
            get_logger().error(f"Fehler beim Abrufen der Daten: {e}")
            return []

        finally:
            if conn:
                conn.close()

    def delete_all_sensor_readings(self):
        """
        Löscht alle Datensätze aus der Tabelle sensor_readings.

        Raises:
            sqlite3.Error: Bei Fehlern in der Datenbankoperation.
        """
        try:
            # Verbindung zur Datenbank herstellen
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # SQL-Befehl zum Löschen aller Datensätze
            delete_query = '''
            DELETE FROM sensor_readings
            '''
            cursor.execute(delete_query)

            # Änderungen speichern
            conn.commit()
            get_logger().info(f"Alle Datensätze wurden gelöscht. Anzahl der betroffenen Zeilen: {cursor.rowcount}")

        except sqlite3.Error as e:
            get_logger().error(f"Fehler beim Löschen der Datensätze: {e}")

        finally:
            if conn:
                conn.close()



if __name__ == "__main__":
    
    # Erzeuge dem Pfad -----------------------------------------
    
    # Absoluter Pfad zum aktuellen Python-Skript
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Relativer Pfad zur Datenbank (basierend auf dem Ort der Python-Datei)
    db_path = os.path.join(script_dir, '../data/example.db')

    # Ordner erstellen, falls nicht vorhanden
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Verbindung zur SQLite-Datenbank herstellen (Datei wird erstellt, falls sie nicht existiert)
    conn = sqlite3.connect(db_path)

    # Cursor-Objekt erstellen, um SQL-Befehle auszuführen
    cursor = conn.cursor()


    # Tabelle erstellen (falls nicht existiert)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL
    )
    ''')

    # Änderungen speichern
    conn.commit()
    
    # Daten Speichern -----------------------------------------

    # Einzelnen Datensatz einfügen
    cursor.execute('INSERT INTO users (name, age) VALUES (?, ?)', ('Alice', 25))

    # Mehrere Datensätze einfügen
    users = [('Bob', 30), ('Charlie', 22)]
    cursor.executemany('INSERT INTO users (name, age) VALUES (?, ?)', users)

    # Änderungen speichern
    conn.commit()

    # Daten Abrufen -----------------------------------------

    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()

    # Ergebnisse ausgeben
    for row in rows:
        print(row)
        
        
    # Verbindung schließen -----------------------------------------

    conn.close()

    # Fehlerbehandlung -----------------------------------------
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # SQL-Operationen...
    except sqlite3.Error as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
    finally:
        if conn:
            conn.close()
            
    # Kontextmanager verwenden -----------------------------------------

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        print(cursor.fetchall())
