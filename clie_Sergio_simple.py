# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:06:59 2020

@author: sergi
"""

from paho.mqtt.client import Client
from multiprocessing import Process,Lock

"""
Comentarios cliente:
    La idea es como la de berni, al iniciarse envia un mensaje por el canal solicitudes
    para que el servidor le regisitre y luego se queda esperando hasta que el servidor le 
    manda la letra para jugar, cuando se la manda la saca en la funcion on_message y ya 
    luego llama a la funcion de pablo new_play(letra) para jugar una partida. Cuando manda
    STOP no funciona y habria que arreglar eso. En el bucle del final la idea seria enviar
    los datos o ni eso, a lo mejor se puede hacer una funcion aparte que envie los datos de
    tu partida el server y ya estaría.
"""


nombre_usuario = input("Nombre: ")

broker="wild.mat.ucm.es"
max_jugadores_partida=10

def on_publish(mqttc, userdata, mid):
    pass
    #print("MESSAGE_Publish:", userdata, mid)

def on_message(mqttc, userdata, msg):
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    l = len("letra")
    if msg.topic == "clients/estop/partidas/1":
        print("Ronda con la", str(msg.payload)[2:-1] )
        new_play(str(msg.payload[l+1:])[2:-1])
    if msg.topic=="clients/estop/jugadores/"+userdata:
         mqttc.subscribe("clients/estop/partidas/1")
         print("Te has unido a la partida 1")
          
def Stop():
    global stop
    stop = True
    mqttc.publish("clients/estop/partidas/1", payload="msg: STOP")

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

def new_play(letter):
    table = init_table()
    print("\n____Empezamos nueva ronda_____\n")
    while (not(stop)):
        print("\n", table)
        tema = input("\n¿Que tema quieres rellenar?\n('STOP' para parar)\n\n->")
        if (not(stop)):
            if (tema == "STOP"):
                Stop()
            elif (tema in table):
                msg = "\n¿Que "+ tema + " se te ocurre con la letra '"+ letter + "' ?\n('STOP' para parar, 'BACK' para elegir tema de nuevo)\n\n->"
                word = input(msg)
                if (word == "STOP"):
                    Stop()
                elif (word != "BACK"):
                    insert_word(word, tema, table, letter)
                    print('\nok')
                    print("\n\n____________________\n")
            else:
                print("\nEse tema no existe actualmente... Prueba de nuevo")
        else:
            print("Lo siento pero alguien ya dió el STOP")

    print("\n____FIN DE LA RONDA___\n")

"""
def callback_partidas(mqttc, userdata, msg):
    print(msg.topic, msg.payload)
"""

mqttc = Client(userdata=nombre_usuario)

mqttc.on_message = on_message
#mqttc.on_connect = on_connect

mqttc.connect(broker)

mqttc.subscribe("clients/estop/jugadores/"+nombre_usuario)
mqttc.publish("clients/estop/solicitudes",payload=nombre_usuario)
#mqttc.subscribe("clients/estop/partidas/1")
#mqttc.message_callback_add("clients/estop/partidas/1", callback_partidas)

mqttc.loop_start()

while (True):
    stop = False
    #Si la partida ha empezado:
    #new_play("d")
    #Enviar mi tabla al servidor
    #Recibir puntuacion y mostrar
#Se acabo
###