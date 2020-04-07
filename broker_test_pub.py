# -*- coding: utf-8 -*-

from paho.mqtt.client import Client

broker="localhost"
#broker="wild.mat.ucm.es"

def on_publish(mqttc, userdata, mid):
    print("MESSAGE_Publish:", userdata, mid)

mqttc = Client()

mqttc.on_publish = on_publish

mqttc.connect(broker)
mqttc.loop_start()

topic = input('topic? ')
while True:
    mensaje = input('mensaje? ')
    if mensaje=="break":
        break
    mqttc.publish(topic,payload=mensaje)

