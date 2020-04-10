# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:06:59 2020

@author: sergi
"""


from multiprocessing import Process, Value
from paho.mqtt.client import Client
import paho.mqtt.publish as publish
from time import sleep
from random import random
#broker="localhost"
broker="wild.mat.ucm.es"

nombre_usuario=input("¿nombre usuario? ")

"""
Todo el tema de las puntuaciones la tiene que llevar el servidor porque si no desde aqui es
imposible detectar lo que han escrito los rivales. Al hacer STOP habria que mandar tu nombre
y tu tablero al server mediante el topic, por elejemplo,
clients/estop1/partidas/1/resultados para asi tratarlos mas comodamente desde el server
"""

"""
LEEEEEEEEEEEEEEEEEEEEEEEEEER ESTOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
He cambiado prints y lo he dejado todo mas claro a la hora de jugar. Tambien he conseguido 
que dada cualquier letra por el servidor(ya no solo da la c) la meta en una variable y
ya la fiuncion new_play juegue con ella. No hay nada mas nuevo
"""
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


#
def on_connect(mqttc, userdata, flags, rc):
    #print("CONNECT:", userdata, flags, rc)
    pass

def callback_servidor(mqttc, userdata, msg):
    #maneja las desconexiones inesperadas del servidor
    #desconectando a todos los jugadores
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    if msg.payload==b"SERVER_FAIL":
        print("SERVER_FAIL: se ha caido el servidor")
        mqttc.disconnect()

def callback_partidas(mqttc, userdata, msg):
    #Yo no pondria este print con el MESSAGE y todo eso
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    l=len("JUGAR RONDA") #llga un msg.payload=b"JUGAR RONDA/C"
    if (msg.payload == b'STOP'):
        global stop
        if (not(stop)):
            print("Otro jugador ha dado STOP, pulse intro para continuar")
        stop = True
    elif (msg.payload[:l] == b'JUGAR RONDA'):
        spl=msg.topic.split("/") #['clients','estop','partidas','1']
        #if (msg.payload[:l] == b'JUGAR RONDA'):
        partida.value = int(spl[3])
        global letra
        letra = str(msg.payload)[-2]
        print(letra)
    else:
        print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    

def on_message(mqttc, userdata, msg):
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    #para las /solicitudes (pues /servidor y /partidas tienen sus callback propias)
    if msg.topic=="clients/estop1/jugadores/"+userdata:
        l=len("NUEVA PARTIDA") #llega el msg.payload=b"NUEVA PARTIDA 3"
        if msg.payload[:l]==b"NUEVA PARTIDA":
            #Lo de abajo sobraria ya que ya tenemos
            mqttc.subscribe("clients/estop1/partidas/"+str(msg.payload[l+1:])[2:-1])
            #mqttc.message_callback_add("clients/estop1/partidas/"+str(msg.payload[l+1:])[2:-1], callback_partidas)
            mqttc.publish("clients/estop1/solicitudes",payload="PARTIDA CREADA")
            print("Has creado la partida "+str(msg.payload[l+1:])[2:-1])
            print("Esperando a más jugadores...")
        else:
            print("MESSAGE:",msg.payload)
        l=len("NUEVA [0] o CARGAR") #llega el msg.payload=b"NUEVA [0] o CARGAR [1,3]"
        if msg.payload[:l]==b"NUEVA [0] o CARGAR":
            disponibles=msg.payload[l+1:]
            eleccion=input("¿PARTIDA...?\nNUEVA: 0\nCARGAR una: "
                           +str(disponibles)[2:-1]+"\n")
            if eleccion=="0": #si elige 0 se crea nueva
                mqttc.publish("clients/estop1/solicitudes/"+userdata,
                          payload=eleccion)
                print("Has creado una partida nueva")
                print("Esperando a más jugadores...")
            elif eleccion in str(disponibles)[2:-1]: #si elige una disponible, se une
                print(eleccion,disponibles)
                #mqttc.message_callback_add("clients/estop1/partidas/"+eleccion, callback_partidas)
                mqttc.subscribe("clients/estop1/partidas/"+eleccion)
                mqttc.publish("clients/estop1/solicitudes/"+userdata,
                          payload=eleccion)
               # mqttc.subscribe("clients/estop/partidas/"+eleccion)
                print("Consigues entrar en la partida",eleccion)
            else: #si elige algo raro, se le echa del juego
                print("No existe esa partida")
                #¿Esto se podria hacer con un try y una excepcion? No se si con eso quedaria mejor
                mqttc.disconnect()

#stop = False

def Stop(num_partida):
    global stop
    stop = True
    #mqttc.publish("clients/estop1/jugadores/elisa", payload = "Sergio ha hecho Stop, pulsa intro")
    mqttc.publish("clients/estop1/partidas/"+str(num_partida), payload="STOP")
    #publish.single("clients/estop1/partidas/"+str(num_partida), 
                   #payload="STOP", hostname="wild.mat.ucm.es")

def init_table():
    return ({"comida": None, "pais": None, "ciudad": None})

def insert_word(word, tema, table, letter):
    if (not(stop)):
        if (word[0] == letter[0]):
            table[tema] = word
        else:
            print("Esa palabra no empieza por", letter)
    else:
        print("Lo siento pero alguien ya dió el STOP")

def new_play(num_partida, letter):
    table = init_table()
    #global stop
    print("\n____Empezamos nueva ronda_____\n")
    print("La letra de la ronda es:",letter)
    while (not(stop)):
        print("\n", table)
        tema = input("\n¿Que tema quieres rellenar?\n('STOP' para parar)\n\n-> ")
        if (not(stop)):
            print(tema)
            if (tema == "STOP"):
                Stop(num_partida)
            elif (tema in table):
                msg = "\n¿Que "+ tema + " se te ocurre con la letra " +letter+"?\n('STOP' para parar, 'BACK' para elegir tema de nuevo)\n\n-> "
                word = input(msg)
                if (word == "STOP"):
                    Stop(num_partida)
                elif (word != "BACK"):
                    insert_word(word, tema, table, letter)
                    print('\nok')
                    print("\n\n____________________\n")
            else:
                print("\nEse tema no existe actualmente... Prueba de nuevo")
    print("\n____FIN DE LA RONDA___\n")
    return table

###
                
mqttc = Client(userdata=nombre_usuario)

#funciones callback:
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.message_callback_add("clients/estop1/servidor", callback_servidor)
mqttc.message_callback_add("clients/estop1/partidas/#", callback_partidas)

#will_set:
#ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
mqttc.will_set("clients/estop1/jugadores/"+nombre_usuario,payload="DISCONNECT")

mqttc.connect(broker)

#suscripciones iniciales del cliente
mqttc.subscribe("clients/estop1/jugadores/"+nombre_usuario)
mqttc.subscribe("clients/estop1/servidor")

#publicación inicial para unirse al juego
mqttc.publish("clients/estop1/solicitudes",payload=nombre_usuario)

mqttc.loop_start()

jugar = Value('i', 0)
partida = Value('i', 0)

stop = False
global letra

while True:
    while partida.value == 0:
        pass
    table = new_play(partida.value,letra)
    partida.value = 0
    #sleep(1)
    datos = Player(1, table)
    print("La puntuacion es", datos.calculate_score([datos]), "pts")
    