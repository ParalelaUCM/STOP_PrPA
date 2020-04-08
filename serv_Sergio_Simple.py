# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:18:50 2020

@author: sergi
"""

from paho.mqtt.client import Client
from multiprocessing import Process,Lock, Value, current_process
from time import sleep

"""
Comentarios servidor:
    Es un servidor simple con la idea de berni de que si un cliente envia su id por el topic
    solicitudes se le mete directamente en la partida1 sin preguntarle si quiere iniciar una 
    partida o lo que sea. Minetras tanto esta el bucle de abajo preguntando si el numero de 
    jugadores es dos y en cuanto se cumple, deja 10 segundos para iniciar la partida y ya 
    le manda la letra por el topic global de partidas1 que lo leen todos los clientes y
    empiezan a jugar. Para el numero de jugadores he tenido que usar un Value ya al quitar
    los procesos no sabia como hacerlo mirando la longuitud del diccionario que seria lo
    normal. 
"""

#broker="localhost"
broker="wild.mat.ucm.es"
max_jugadores_partida=10


jugadores = []

def on_message(mqttc, userdata, msg):
    print(msg.topic, msg.payload, str(msg.payload)[2:-1])
    if (msg.topic=="clients/estop/solicitudes"):
        print("Se ha unido el jugador", str(msg.payload)[2:-1])
        mqttc.publish("clients/estop/jugadores/"
                      +str(msg.payload)[2:-1],payload="NUEVA PARTIDA 1")
        print("publico mensaje")
        if 1 in userdata:
            userdata[1].append(str(msg.payload)[2:-1])
        else:
            userdata[1] = ["Partida1", str(msg.payload)[2:-1]]
        jug.value += 1
        print(userdata)        

data = {}
mqttc = Client(userdata=data)

#mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(broker)

mqttc.publish("clients/estop",payload="SERVIDOR ACTIVO")
print("SERVIDOR ACTIVO...")
mqttc.subscribe("clients/estop/solicitudes/#")
mqttc.subscribe("clients/estop/jugadores/#")
mqttc.subscribe("clients/estop/partidas/#")

mqttc.loop_start()

while True:
    jug = Value('i', 0)
    if (jug.value < 2):
        print("Esperando mas jugadores")
        while jug.value < 2:
            pass
    print(len(data[1]))#Esta es la condicion que me gustaria poner en el if y en el bucle pero no se puede ya que al principio no existe data[1]
    print("La partida empieza en 10 segundos...")#Este mensaje habria que neviarlo a los jugadores para que lo vieran
    sleep(10)
    #Aqui a lo mejor hace un semaforo para evitar que se unan jugadores mientras se esta iniciando
    letra = 'c'
    mqttc.publish("clients/estop/partidas/1",payload = "letra "+letra)
