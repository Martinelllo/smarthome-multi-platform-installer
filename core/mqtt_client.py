import os
import threading
import paho.mqtt.client as mqtt
import json

from core.logger import get_logger

from typing import TYPE_CHECKING, Callable, Dict, Union, TypedDict

from core.api_client import APIClient
from abstract_base_classes.singleton_meta import SingletonMeta



class MQTTClient(metaclass=SingletonMeta):
    
    def __init__(self) -> None:
        __mqtt_credentials = APIClient().get_mqtt_credentials()
                
        host = os.getenv("MQTT_HOST")
        port = int( os.getenv("MQTT_PORT") )
        user = __mqtt_credentials["MQTT_USER"]
        passw = __mqtt_credentials["MQTT_PASSWORD"]
        
        self.baseTopic = __mqtt_credentials['MQTT_TOPIC']
        
        if not host: raise ValueError("Environment Variable 'MQTT_HOST' is not set.")
        if not isinstance(port, int): raise ValueError("Environment Variable 'MQTT_PORT' is not set.")
        
        self.__mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.__mqttc.on_connect = self.__on_connect
        self.__mqttc.on_disconnect = self.__on_disconnect
        self.__mqttc.on_message = self.__on_message
        
        self.__mqttc.username_pw_set(user, passw)
        self.__mqttc.connect(host, port, 60)
        self.__mqttc.loop_start()
        
        self.__subscribers: Dict[str, list[Callable[[dict], None]]] = {}
        
    def __on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        get_logger().info(f"MQTT Connected to Topic '{self.baseTopic}/#' {reason_code}")
        client.subscribe(f"{self.baseTopic}/#")
        
    def __on_disconnect(self, client: mqtt.Client, userdata, flags, reason_code, properties):
        # Subscribing in on_disconnect() means that if we lose the connection 
        # reconnect then we write a log.
        get_logger().info(f"MQTT Disconnect. reason_code: {reason_code}")
        client.unsubscribe(f"{self.baseTopic}/#")

    def __on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        # parse payload from bytes to dict
        payload = json.loads(msg.payload)
        get_logger().debug(msg.topic+" "+str(payload))
        
        if msg.topic in self.__subscribers:
            for subscription in self.__subscribers[msg.topic]:
                subscription(payload)
            
    def subscribe( self, topic: str, callback: Callable[[dict], None] ):
        """ 
        Subscribe for a mqtt topic on this device
        
        :param topic: The topic looks like: /module/module_id.
        :param callback: The callback should accept one argument: (payload: dict).
        """
        
        full_topic = f"{self.baseTopic}{topic}"
        if full_topic not in self.__subscribers:
            self.__subscribers[full_topic] = [callback]
        else:
            self.__subscribers[full_topic].append(callback)
        
    def unsubscribe( self, topic: str ):
        """
        Stopp listening and running the callbacks registered on this topic
        
        :param topic: The topic looks like: /module/module_id.
        """
        
        full_topic = f"{self.baseTopic}{topic}"
        if full_topic in self.__subscribers:
            del self.__subscribers[full_topic]

    def on_destroy(self):
        self.__mqttc.disconnect()
        
    def hasSubscription(self, topic):
        full_topic = f"{self.baseTopic}{topic}"
        if full_topic in self.__subscribers:
            return True
        return False
    
    def findSubscription(self, topic):
        full_topic = f"{self.baseTopic}{topic}"
        if full_topic in self.__subscribers:
            return self.__subscribers[full_topic]
        return None
        

if __name__ == "__main__":

    # more: https://pypi.org/project/paho-mqtt/#known-limitations

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("$SYS/#")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message

    mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    mqttc.loop_forever()