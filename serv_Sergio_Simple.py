# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:18:50 2020

@author: sergi
"""

from paho.mqtt.client import Client
from multiprocessing import Process,Lock
from time import sleep
#--creo que habrá que poner un Lock para todos los accesos al diccionario del userdata

#broker="localhost"
broker="wild.mat.ucm.es"

max_jugadores_partida=3
min_jugadores_partida=2

class Player:
    #Constructora
    def __init__(self, player_id, player_table):
        self.id = player_id #El id unico del jugador
        self.table = player_table #El tablero del jugador
        self.score = 0 #la puuntuacion actual del jugador. Por defecto 0

    #Funcion que calcula la puntuacion en base a los rivales
    def calculate_score(self, rivals):
        for key in self.table:
            filled = (self.table[key] != None) #Comprobamos que este rellenado ese tema
            if (filled):
                unique = True
                #Buscamos si la palabra es unica o no para calcular la puntuacion
                for rival in rivals:
                    if (rival.id != self.id):
                        unique = (self.table[key] != rival.table[key])
                        if (not(unique)):
                            break
                if (unique):
                    self.score += 25 # 25 pts si es unica
                else:
                    self.score += 10 # 10 pts si esta repetida
        return (self.score) #Para comprobar que funciona

"""
#Ejemplo con dos jugadores
p1 = Player(1, {"comida": "canelones", "pais": "canada", "ciudad": "copanhage"})

p2 = Player(2, {"comida": "camaron", "pais": "canada", "ciudad": None})

print("El jugador 1 obtuvo una puntuacion de:",p1.calculate_score([p1, p2]), "pts")
print("El jugador 2 obtuvo una puntuacion de:",p2.calculate_score([p1, p2]), "pts")
"""



def on_publish(mqttc, userdata, mid):
    pass
    #print("MESSAGE_Publish:", userdata, mid)

def callback_partidas(mqttc, userdata, msg):
    #aquí se manejan los mensajes que llegan de cada partida
    #se puede modificar el diccionario del servidor
    #falta cambiar la función, de momento he puesto una que no hace nada útil
    if (msg.payload == b'STOP'):
        mqttc.publish(msg.topic, payload = "Otro jugador ha hecho STOP, pulsa into para continuar")
    else: 
        spl=msg.topic.split("/") #spl=['clients','estop','partidas','1','jugador_x']
        if len(spl)==5:
            num_partida=spl[3]
            usuario=spl[4]
            mensaje=str(msg.payload)[2:-1]
            (userdata[int(num_partida)]).append(usuario+mensaje)
        print("estop actual",userdata) #mostramos el diccionario tras cada mensaje

def callback_jugadores(mqttc, userdata, msg):
    #maneja las desconexiones inesperadas de los jugadores
    #eliminandolos del diccionario del servidor
    if msg.payload==b"DISCONNECT":
        l=len("clients/estop1/jugadores/")
        usuario=msg.topic[l:]
        for clave,valor in userdata.items():
            if usuario in valor:
                valor.remove(usuario)
                if len(valor)==1:
                    userdata.pop(clave)
                    break
                mqttc.publish("clients/estop1/partidas/"+str(clave),
                              payload=str(usuario)+" ha abandonado la partida")
        print("estop actual",userdata) #mostramos el diccionario tras cada mensaje


def on_message(mqttc, userdata, msg):
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    #para las /solicitudes (pues /partidas y /jugadores tienen sus callback propias)
    if msg.topic=="clients/estop1/solicitudes":
        if userdata=={}:
            #si no hay nadie aún, mete al usuario en la partida 1
            mqttc.publish("clients/estop1/jugadores/"+str(msg.payload)[2:-1],
                          payload="NUEVA PARTIDA 1")
            userdata[1]=["partidas/1",str(msg.payload)[2:-1]]
            #Process(target=partida,args=(1,)).start()#¿Esto al final va ser necesario?
        else:
            #si hay alguna partida, deja al usuario elegir entre nueva o cargar
            partidas_disponibles=[]
            for clave,valor in userdata.items():
                if len(valor)<max_jugadores_partida+1:
                    partidas_disponibles.append(clave)
            mqttc.publish("clients/estop1/jugadores/"+str(msg.payload)[2:-1],
                          payload="NUEVA [0] o CARGAR "+str(partidas_disponibles))
    #
    #ahora manejamos la eleccion de partida del cada usuario
    l=len("clients/estop1/solicitudes/")
    if msg.topic[:l]=="clients/estop1/solicitudes/":
        if msg.payload==b"0":
            num_partidas=len(userdata)
            mqttc.publish("clients/estop1/jugadores/"+msg.topic[l:],
                          payload="NUEVA PARTIDA "+str(num_partidas+1))
            userdata[num_partidas+1]=["partidas/"+str(num_partidas+1),msg.topic[l:]]
        else:
            indice_partida=int(str(msg.payload)[2:-1])
            userdata[indice_partida].append(msg.topic[l:])
            #decidimos cuando empezar la partida, según los usuarios apuntados
            if len(userdata[indice_partida])-1 < min_jugadores_partida:
                mqttc.publish("clients/estop1/partidas/"+str(indice_partida),
                              payload="AUN NO HAY JUGADORES SUFICIENTES")
            elif len(userdata[indice_partida])-1 == min_jugadores_partida:
                mqttc.publish("clients/estop1/partidas/"+str(indice_partida),
                              payload="YA HAY JUGADORES SUFICIENTES")
                mqttc.publish("clients/estop1/partidas/"+str(indice_partida),
                              payload = "La partida comenzara en 10 segundos")
                sleep(5)
                mqttc.publish("clients/estop1/partidas/"+str(indice_partida),
                              payload="JUGAR RONDA/c")
            else:
                #falta el caso en el que se conecta uno más tarde
                #de momento creo que es mejor que funcione como una partida
                #normal en la que todos los jugadores están desde el principio
                pass
    #
    print("estop actual",userdata) #mostramos el diccionario tras cada mensaje
    #


###

mqttc = Client(userdata={}) #diccionario como userdata para la info del juego

#funciones callback:
mqttc.on_publish = on_publish
mqttc.on_message = on_message
mqttc.message_callback_add("clients/estop1/jugadores/#", callback_jugadores)
mqttc.message_callback_add("clients/estop1/partidas/#", callback_partidas)

#will_set:
#ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
mqttc.will_set("clients/estop1/servidor",payload="SERVER_FAIL")

mqttc.connect(broker)

mqttc.publish("clients/estop1/servidor",payload="SERVER_READY")
print("SERVIDOR ACTIVO...")

#suscripciones iniciales del servidor
mqttc.subscribe("clients/estop1/solicitudes/#")
mqttc.subscribe("clients/estop1/jugadores/#")
mqttc.subscribe("clients/estop1/partidas/#")

mqttc.loop_forever()

###