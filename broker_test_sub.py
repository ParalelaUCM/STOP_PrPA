# -*- coding: utf-8 -*-

from paho.mqtt.client import Client

broker="localhost"
#broker="wild.mat.ucm.es"

def on_message(mqttc, userdata, msg):
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)

mqttc = Client()

mqttc.on_message = on_message
mqttc.connect(broker)

topic = input('topic? ')
mqttc.subscribe(topic)
mqttc.loop_forever()
