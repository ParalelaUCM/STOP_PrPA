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
from time import sleep

#broker="localhost"
broker="wild.mat.ucm.es"
choques="clients/estop" #topic=choques+"/servidor...
#para evitar que coincidamos en el broker, cada uno que ponga uno

nombre_usuario=input("¿nombre usuario? ")

def Stop(num_partida):
    global stop
    stop = True
    #mqttc.publish(choques+"/jugadores/elisa", payload = "Sergio ha hecho Stop, pulsa intro")
    #mqttc.publish(choques+"/partidas/"+str(num_partida), payload="STOP")
    publish.single(choques+"/partidas/"+str(num_partida),
                   payload="STOP", hostname=broker)

def init_table():
    return ({"comida": None, "pais": None, "ciudad": None})

def insert_word(word, tema, table, letter):
    if (not(stop)):
        if (word[0] == letter[0]):
            table[tema] = word
        else:
            print_state("Esa palabra no empieza por " + letter, True)
    else:
        print_state("Lo siento pero alguien ya dió el STOP", True)

"""
Con esta función se borra todo lo que había en pantalla y se imprime la tabla actual.
Si el mensaje es un error o que alguien ha dado stop o la puntuacion de la ronda se
se pondrá a true el 'need_verification'. Esto hará que solo salga en mensaje por pantalla
sin la tabla ni nada y que se mantenga ahi hata que se le de a enter o entre otro mensaje
"""
import os
def print_state(msg= "", need_verification = False):
    os.system('cls' if os.name == 'nt' else "printf '\033c'")
    if (not(need_verification)):
        for key in table:
            print("|",key, "|", end =" ")
        print("")
        for key in table:
            print("|",table[key], "|", end =" ")
        print("")
        print(msg, end="")
    else:
        print(msg, end="")
        input()

def callback_partidas(mqttc, userdata, msg):
    spl=msg.topic.split("/") #['clients','estop','partidas','1','puntos']
    if len(spl)==5 and spl[4]=="puntos": #llegan las puntuaciones con el pickle
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

#
def callback_jugadores(mqttc, userdata, msg):
    #topic: ['clients','estop','jugadores','usuario']
    l=len("NUEVA_PARTIDA") #llega el msg.payload=b"NUEVA_PARTIDA 3"
    mensaje=str(msg.payload)[2:-1]
    #
    if mensaje[:l]=="NUEVA_PARTIDA":
        num_partida=mensaje[l+1:]
        #no nos suscribimos a la partida,solo a los puntos
        ###mqttc.subscribe(choques+"/partidas/"+num_partida)
        mqttc.subscribe(choques+"/partidas/"+num_partida+"/puntos")
        indice_partida.value=1
        print("Has creado la partida "+num_partida)
        userdata[2]=int(num_partida)
        print("Esperando a más jugadores...")
    #
    l=len("NUEVA [0] o CARGAR") #llega el msg.payload=b"NUEVA [0] o CARGAR [1,3]"
    if msg.payload[:l]==b"NUEVA [0] o CARGAR":
        disponibles=str(msg.payload[l+1:])[2:-1]
        eleccion=input("¿PARTIDA...?\nNUEVA: [0]\nCARGAR una: "+disponibles+"\n")
        if eleccion=="0": #si elige 0 se crea nueva
            mqttc.publish(choques+"/solicitudes/"+userdata[0],payload=eleccion)
        elif eleccion in disponibles: #si elige una disponible, se une directamente
            ###no nos suscribimos a la partida, solo a los puntos
            ###mqttc.subscribe(choques+"/partidas/"+eleccion)
            mqttc.subscribe(choques+"/partidas/"+eleccion+"/puntos")
            indice_partida.value=int(eleccion)
            userdata[2]=int(eleccion)
            mqttc.publish(choques+"/solicitudes/"+userdata[0],payload=eleccion)
            print("Consigues entrar en la partida",eleccion)
        else: #si elige algo raro, se le echa del juego
            print("No existe esa partida")
            conectado.value=0
            mqttc.disconnect()
    #
    elif msg.payload[:4]==b"NOT_INOF":
        print("Aún no hay jugadores suficientes para esta partida...")
    #
    elif mensaje[:5]=="READY":
        sleep(5) #cuanto esperamos para admitir nueeva gente
        mqttc.publish(choques+"/partidas/"+str(userdata[2]),payload="READY_YES")
    #
    elif mensaje[:4]=="PLAY": #ahora llega algo como PLAY-R
        let=ord(mensaje[-1])
        letra.value = let
        print_state("EMPIEZA UNA NUEVA RONDA CON LA LETRA "+chr(let), True)
        jugar.value = 1
    #
    elif (msg.payload == b'STOP'):
        global stop
        if stop!=True: #este jugador no ha hecho stop
            stop = True
            print("Otro jugador ha dado STOP, pulse intro para continuar")
        else: #este jugador ha hecho stop
            pass

def callback_servidor(mqttc, userdata, msg):
    #maneja las desconexiones inesperadas del servidor
    #desconectando a todos los jugadores
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    spl=msg.topic.split("/") #['clients','estop','servidor','nombre']
    if msg.payload==b"SERVER_FAIL":
        print("SERVER_FAIL: se ha caido el servidor")
        conectado.value=0
        mqttc.disconnect()
    elif msg.payload==b"SERVER_READY":
        mqttc.publish(choques+"/servidor/"+userdata[0],payload="CONNECT_REQUEST")
    elif msg.payload==b"CONNECT_ACCEPT":
        print("SERVIDOR ACTIVO")
        mqttc.unsubscribe(choques+"/servidor/exception")
        #si aceptan al jugador, nos desuscribimos de exception
        #y enviamos la solicitud de acceso a la partida con nuestro nombre
        mqttc.publish(choques+"/solicitudes",payload=userdata[0])
    elif msg.payload==b"USER_EXC":
        print("Usuario no válido o ya registrado")
        conectado.value=0
        mqttc.disconnect()
    #

###################################################

mqttc = Client(userdata=[nombre_usuario,0,0]) #userdata=[nombre_usuario,puntos,partida]

#funciones callback:
mqttc.on_message = on_message
#mqttc.on_connect = on_connect
mqttc.message_callback_add(choques+"/servidor/#", callback_servidor)
mqttc.message_callback_add(choques+"/partidas/#", callback_partidas)
mqttc.message_callback_add(choques+"/jugadores/"+nombre_usuario, callback_jugadores)


#will_set:
#ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
mqttc.will_set(choques+"/jugadores/"+nombre_usuario,payload="DISCONNECT")

mqttc.connect(broker)

#suscripciones iniciales del cliente
mqttc.subscribe(choques+"/jugadores/"+nombre_usuario)
mqttc.subscribe(choques+"/servidor")
mqttc.subscribe(choques+"/servidor/"+nombre_usuario)
mqttc.subscribe(choques+"/servidor/exception")

#publicación inicial para unirse al juego
mqttc.publish(choques+"/servidor/"+nombre_usuario,payload="CONNECT_REQUEST")
print("ESPERANDO AL SERVIDOR...")

mqttc.loop_start()

###########################################

conectado = Value('i',1)
indice_partida = Value('i',0) #indice de la partida a la que se conecta el jugador
jugar = Value('i', 0)
letra = Value('c', b'z') #el character tiene que ser de tipo byte para el Value
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
    print_state()
    print("\n____Empezamos nueva ronda_____\n")
    print("La letra de la ronda es",str(letra.value)[2:-1])
    while (not(stop)):
        print("\n", table)
        print_state()
        print_state("\n¿Que tema quieres rellenar?\n(0 o STOP para parar)\n\n-> ")
        tema = input()
        if (not(stop)):
            if (tema == "STOP") or (tema == "0"):
                Stop(1)
            elif (tema in table):
                msg = "\n¿Que "+ tema + " se te ocurre con la letra "+str(letra.value)[2:-1]+"?\n('STOP' para parar, 'BACK' para elegir tema de nuevo)\n\n-> "
                print_state(msg)
                word = input()
                if (word == "STOP") or (word == "0"):
                    Stop(1)
                elif (word != "BACK"):
                    insert_word(word.lower(), tema, table, str(letra.value)[2:-1])
                    print_state()
                    print('\nok')
                    print("\n\n____________________\n")
            else:
                print_state("\nEse tema no existe actualmente... Prueba de nuevo", True)
        else:
            print_state("Lo siento pero alguien ya dió el STOP", True)
    print("\n____FIN DE LA RONDA___\n")
    jugar.value = 0
    publish.single(choques+"/partidas/"+str(indice_partida.value)+"/"+nombre_usuario,
                   payload=pickle.dumps(table),hostname=broker)
