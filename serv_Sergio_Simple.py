# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:18:50 2020

@author: sergi
"""


'''
nuevas cosas (por orden de aparición):
choques
alfabeto
def calcula puntos
IMPORTTANTE: el creado un nuevo cliente, llamado ccc, que se encarga con su userdata
de llevar el diccionario de usuarios, y de administrar las puntuaciones, de momento
está en un topic separado clients/prueba/1...: tiene tb su callback propio, llamado
callback_prueba
'''

from paho.mqtt.client import Client
from multiprocessing import Process,Lock
from time import sleep
from random import shuffle
import pickle
#creo que habrá que poner un Lock (por si acaso) en los accesos al diccionario del userdata

#broker="localhost"
broker="wild.mat.ucm.es"
choques="estop2" #topic="clients/"+choques+"/servidor...
#para evitar que coincidamos en el broker, cada uno que ponga uno

alfabeto=[chr(i) for i in range(97,123)] #65a91 para MAY, 97a123 para minusculas
shuffle(alfabeto)

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
            filled = (self.table[key] != None) and (self.table[key] != "") #Comprobamos que este rellenado ese tema
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
def calcula_puntos(ids,diccs,num_partida):
    '''
    calcula las puntuaciones cuando se le pasa:
    ids: lista de nombres de usuario
    diccs: lista de diccionarios con las respuestas de cada usuario
    num_partida de los usuarios
    '''
    puntuaciones=[]
    ldp=[] #lista de Players
    print("\nRespuestas de la ronda:")
    for i in range(len(ids)):
        ldp.append(Player(ids[i],diccs[i]))
        print(ids[i],":",diccs[i])
    for i in range(len(ldp)):
        jugador=ldp[i]
        #p2.calculate_score([p1, p2]) ejemplo
        puntos=jugador.calculate_score(ldp)
        puntuaciones.append(puntos)
    print("Puntuaciones de la ronda")
    for i in range(len(ids)):
        print(ids[i],":",puntuaciones[i])
    #publicamos resultados a los usuarios:
    mqttc.publish("clients/"+choques+"/partidas/"+str(num_partida)+"/puntos",
                  payload=pickle.dumps([ids,puntuaciones]))
    #preparamos la siguiente ronda
    letra=alfabeto.pop(0)
    sleep(30)
    mqttc.publish("clients/"+choques+"/partidas/"+str(num_partida),
                  payload="JUGAR RONDA/"+letra)

#
def callback_partidas(mqttc, userdata, msg):
    #creo que este if no hace falta, pues el cliente tiene un print similar
    #lo del else creo que tb sobra
    #probar
    '''
    if (msg.payload == b'STOP'):
        mqttc.publish(msg.topic, payload = "Otro jugador ha hecho STOP, pulsa into para continuar")
    else:
        spl=msg.topic.split("/") #spl=['clients','estop','partidas','1','jugador_x']
        if len(spl)==5 and spl[4]!="puntos":
            num_partida=spl[3]
            usuario=spl[4]
            mensaje=str(msg.payload)[2:-1]
            (userdata[int(num_partida)]).append(usuario+mensaje)
    '''

def callback_jugadores(mqttc, userdata, msg):
    #maneja las desconexiones inesperadas de los jugadores
    #eliminandolos del diccionario del servidor
    if msg.payload==b"DISCONNECT":
        l=len("clients/"+choques+"/jugadores/")
        usuario=msg.topic[l:]
        for clave,valor in userdata.items():
            if usuario in valor:
                valor.remove(usuario)
                if len(valor)==1:
                    userdata.pop(clave)
                    break
                #este mensaje ver si hace falta
                mqttc.publish("clients/"+choques+"/partidas/"+str(clave),
                              payload=str(usuario)+" ha abandonado la partida")

def on_message(mqttc, userdata, msg):
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    #para las /solicitudes (pues /partidas y /jugadores tienen sus callback propias)
    #nota para más tarde: mejorar esta entrada de usuarios
    if msg.topic=="clients/"+choques+"/solicitudes":
        if userdata=={}:
            #si no hay nadie aún, mete al usuario en la partida 1
            mqttc.publish("clients/"+choques+"/jugadores/"+str(msg.payload)[2:-1],
                          payload="NUEVA PARTIDA 1")
            userdata[1]=["partidas/1",str(msg.payload)[2:-1]]
            #Process(target=partida,args=(1,)).start()#¿Esto al final va ser necesario?
        else:
            #si hay alguna partida, deja al usuario elegir entre nueva o cargar
            partidas_disponibles=[]
            for clave,valor in userdata.items():
                if len(valor)<max_jugadores_partida+1:
                    partidas_disponibles.append(clave)
            mqttc.publish("clients/"+choques+"/jugadores/"+str(msg.payload)[2:-1],
                          payload="NUEVA [0] o CARGAR "+str(partidas_disponibles))
    #
    #ahora manejamos la eleccion de partida del cada usuario
    l=len("clients/"+choques+"/solicitudes/")
    if msg.topic[:l]=="clients/"+choques+"/solicitudes/":
        if msg.payload==b"0":
            num_partidas=len(userdata)
            mqttc.publish("clients/"+choques+"/jugadores/"+msg.topic[l:],
                          payload="NUEVA PARTIDA "+str(num_partidas+1))
            userdata[num_partidas+1]=["partidas/"+str(num_partidas+1),msg.topic[l:]]
        else:
            indice_partida=int(str(msg.payload)[2:-1])
            userdata[indice_partida].append(msg.topic[l:])
            #decidimos cuando empezar la partida, según los usuarios apuntados
            if len(userdata[indice_partida])-1 < min_jugadores_partida:
                mqttc.publish("clients/"+choques+"/partidas/"+str(indice_partida),
                              payload="AUN NO HAY JUGADORES SUFICIENTES")
            elif len(userdata[indice_partida])-1 == min_jugadores_partida:
                mqttc.publish("clients/"+choques+"/partidas/"+str(indice_partida),
                              payload="YA HAY JUGADORES SUFICIENTES")
                mqttc.publish("clients/"+choques+"/partidas/"+str(indice_partida),
                              payload = "La partida comenzara en 10 segundos")
                sleep(1) #tiempo de espera para aceptar más jugadores
                letra=alfabeto.pop(0)
                mqttc.publish("clients/"+choques+"/partidas/"+str(indice_partida),
                              payload="JUGAR RONDA/"+letra)
            else:
                #falta el caso en el que se conecta uno más tarde
                #de momento creo que es mejor que funcione como una partida
                #normal en la que todos los jugadores están desde el principio
                pass
    #
    print("estop actual",userdata) #mostramos el diccionario tras cada mensaje
    #
#
def callback_prueba(ccc, userdata, msg):
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    spl=msg.topic.split("/") #['clients','prueba','1','berni']
    mensaje=pickle.loads(msg.payload) #{'ciudad':'madrid'}
    userdata[spl[3]]=mensaje
    if len(userdata)==2: #probamos con 2 jugadores->generalizar
        ids=[]
        diccs=[]
        for clave,valor in userdata.items():
            ids.append(clave)
            diccs.append(valor)
        print("ENTRAMOS A CALCULAR PUNTOS")
        calcula_puntos(ids,diccs,spl[2])
        userdata={}
        sleep(5)

###

mqttc = Client(userdata={}) #diccionario como userdata para la info del juego

#funciones callback:
#mqttc.on_publish = on_publish
mqttc.on_message = on_message
mqttc.message_callback_add("clients/"+choques+"/jugadores/#", callback_jugadores)
mqttc.message_callback_add("clients/"+choques+"/partidas/#", callback_partidas)

#will_set:
#ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
mqttc.will_set("clients/"+choques+"/servidor",payload="SERVER_FAIL")

mqttc.connect(broker)

mqttc.publish("clients/"+choques+"/servidor",payload="SERVER_READY")
print("SERVIDOR ACTIVO...")

#suscripciones iniciales del servidor
mqttc.subscribe("clients/"+choques+"/solicitudes/#")
mqttc.subscribe("clients/"+choques+"/jugadores/#")
mqttc.subscribe("clients/"+choques+"/partidas/#")

#
#
#de momento he hecho un cliente auxiliar que maneje a los usuarios
#creo que no hace falta separarlo, solo hay que
#ver una manera de que la info de este userdata se pueda sacar del otro
ccc = Client(userdata={}) #diccionario de usuarios
ccc.message_callback_add("clients/prueba/#", callback_prueba)
ccc.connect(broker)
ccc.subscribe("clients/prueba/#")

ccc.loop_start()
mqttc.loop_forever()