# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:06:59 2020

@author: sergi
"""

'''
nuevas cosas (por orden de aparición):
on_connect y on_publish: los he quitado, que ya molestaban más que otra cosa
choques
Values globales: conectado, indice_partida,letra,jugar
las letras ya cambian (aunque eso lo envía el servidor)
se activan la ronda siguiente justo después del recuento de puntos
while True del final, cambiado por el Value conectado, para que salga del bucle si
por lo que sea se va el jugador
opcion adicional para hacer STOP: darle al 0, que es más rápido
'''


from multiprocessing import Process, Value
from paho.mqtt.client import Client
import paho.mqtt.publish as publish
import pickle

#broker="localhost"
broker="wild.mat.ucm.es"
choques="estop2" #topic="clients/"+choques+"/servidor...
#para evitar que coincidamos en el broker, cada uno que ponga uno

nombre_usuario=input("¿nombre usuario? ")

def callback_servidor(mqttc, userdata, msg):
    #maneja las desconexiones inesperadas del servidor
    #desconectando a todos los jugadores
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    if msg.payload==b"SERVER_FAIL":
        print("SERVER_FAIL: se ha caido el servidor")
        conectado.value=0
        mqttc.disconnect()

def callback_partidas(mqttc, userdata, msg):
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    spl=msg.topic.split("/") #['clients','estop','partidas','1','puntos']
    if (msg.payload == b'STOP'):
        global stop
        stop = True
        print("Otro jugador ha dado STOP, pulse intro para continuar")
    elif msg.payload[:5]==b"JUGAR":
        spl=msg.topic.split("/") #['clients','estop','partidas','1']
        num_partida=spl[3]
        l="JUGAR RONDA" #llga un msg.payload=b"JUGAR RONDA/C"
        if str(msg.payload)[2:-3]=="JUGAR RONDA":
            print("EMPIEZA UNA NUEVA RONDA")
            let=msg.payload[-1]
            jugar.value = 1
            letra.value = let
            #jugar(num_partida,letra)
    elif len(spl)==5 and spl[4]=="puntos": #llegan las puntuaciones con el pickle
        #falta ver como mostrar las puntuacioines totales de todos, no solo de la ronda
        datos=pickle.loads(msg.payload)
        print("PUNTUACIONES RONDA")
        for ii in range(len(datos[0])):
            print(datos[0][ii],":",datos[1][ii])
            if datos[0][ii]==userdata[0]:
                userdata[1]+=datos[1][ii]
        print("MIS PUNTOS TOTALES",userdata[1])

def on_message(mqttc, userdata, msg):
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    #para las /solicitudes (pues /servidor y /partidas tienen sus callback propias)
    if (msg.topic == "clients/"+choques+"/partidas/1"):
        callback_partidas(msg.topic, msg.payload)
    if msg.topic=="clients/"+choques+"/jugadores/"+userdata[0]:
        l=len("NUEVA PARTIDA") #llega el msg.payload=b"NUEVA PARTIDA 3"
        if msg.payload[:l]==b"NUEVA PARTIDA":
            num_partida=str(msg.payload[l+1:])[2:-1]
            mqttc.subscribe("clients/"+choques+"/partidas/"+num_partida)
            mqttc.subscribe("clients/"+choques+"/partidas/"+num_partida+"/puntos")
            indice_partida.value=1
            mqttc.publish("clients/"+choques+"/solicitudes",payload="PARTIDA CREADA")
            print("Has creado la partida "+str(msg.payload[l+1:])[2:-1])
            print("Esperando a más jugadores...")
        l=len("NUEVA [0] o CARGAR") #llega el msg.payload=b"NUEVA [0] o CARGAR [1,3]"
        if msg.payload[:l]==b"NUEVA [0] o CARGAR":
            disponibles=msg.payload[l+1:]
            eleccion=input("¿PARTIDA...?\nNUEVA: 0\nCARGAR una: "
                           +str(disponibles)[2:-1]+"\n")
            if eleccion=="0": #si elige 0 se crea nueva
                mqttc.publish("clients/"+choques+"/solicitudes/"+userdata[0],
                          payload=eleccion)
                print("Has creado una partida nueva")
                print("Esperando a más jugadores...")
            elif eleccion in str(disponibles)[2:-1]: #si elige una disponible, se une
                mqttc.subscribe("clients/"+choques+"/partidas/"+eleccion)
                mqttc.subscribe("clients/"+choques+"/partidas/"+eleccion+"/puntos")
                indice_partida.value=int(eleccion)
                mqttc.publish("clients/"+choques+"/solicitudes/"+userdata[0],
                          payload=eleccion)
               # mqttc.subscribe("clients/estop/partidas/"+eleccion)
                print("Consigues entrar en la partida",eleccion)
            else: #si elige algo raro, se le echa del juego
                print("No existe esa partida")
                mqttc.disconnect()

#stop = False

def Stop(num_partida):
    global stop
    stop = True
    #mqttc.publish("clients/"+choques+"/jugadores/elisa", payload = "Sergio ha hecho Stop, pulsa intro")
    #mqttc.publish("clients/"+choques+"/partidas/"+str(num_partida), payload="STOP")
    publish.single("clients/"+choques+"/partidas/"+str(num_partida), 
                   payload="STOP", hostname="wild.mat.ucm.es")

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

###
                
mqttc = Client(userdata=[nombre_usuario,0]) #userdata=[nombre_usuario,puntos]

#funciones callback:
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.message_callback_add("clients/"+choques+"/servidor", callback_servidor)
mqttc.message_callback_add("clients/"+choques+"/partidas/#", callback_partidas)

#will_set:
#ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
mqttc.will_set("clients/"+choques+"/jugadores/"+nombre_usuario,payload="DISCONNECT")

mqttc.connect(broker)

#suscripciones iniciales del cliente
mqttc.subscribe("clients/"+choques+"/jugadores/"+nombre_usuario)
mqttc.subscribe("clients/"+choques+"/servidor")

#publicación inicial para unirse al juego
mqttc.publish("clients/"+choques+"/solicitudes",payload=nombre_usuario)

mqttc.loop_start()

conectado = Value('i',1)
indice_partida = Value('i',0)
jugar = Value('i', 0)
letra = Value('c', b'z')
stop = False

while conectado.value==1:
    while jugar.value == 0:
        if conectado.value==0:
                break
        pass
    if conectado.value==0:
            break
    stop=False #ponemos el stop a False para las siguientes rondas
    table = init_table()
    #global stop
    print("\n____Empezamos nueva ronda_____\n")
    print("La letra de la ronda es",str(letra.value)[2:-1])
    while (not(stop)):
        print("\n", table)
        tema = input("\n¿Que tema quieres rellenar?\n(0 o STOP para parar)\n\n-> ")
        if (not(stop)):
            print(tema)
            if (tema == "STOP") or (tema == "0"):
                Stop(1)
            elif (tema in table):
                msg = "\n¿Que "+ tema + " se te ocurre con la letra "+str(letra.value)[2:-1]+"?\n('STOP' para parar, 'BACK' para elegir tema de nuevo)\n\n-> "
                word = input(msg)
                if (word == "STOP") or (word == "0"):
                    Stop(1)
                elif (word != "BACK"):
                    insert_word(word.lower(), tema, table, str(letra.value)[2:-1])
                    print('\nok')
                    print("\n\n____________________\n")
            else:
                print("\nEse tema no existe actualmente... Prueba de nuevo")
        else:
            print("Lo siento pero alguien ya dió el STOP")
    print("\n____FIN DE LA RONDA___\n")
    jugar.value = 0
    #publicamos en el topic prueba, cambiarlo junto con lo del servidor
    #quiza se puede hacer un grupo nuevo de topics que sea clients/estop/puntos/3
    mqttc.publish("clients/prueba/"+str(indice_partida.value)+"/"+nombre_usuario,
                                        payload=pickle.dumps(table))
    print("La puntuacion es pts")
    
