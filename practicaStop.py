# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 19:46:56 2020

@author: sergi
"""

from paho.mqtt.client import Client 
from multiprocessing import Value

turno = Value('i', 0)
#letra = Value('s','c')

def on_message(client, userdata, msg):
    if (msg.payload == b'STOP'):
        print("Algun jugador ha dicho STOP, escribe STOP para acabar")
        turno.value = 1


client = Client(userdata = "Sergio")
client.connect("wild.mat.ucm.es")
client.on_message = on_message

client.subscribe("clients/STOP")

client.loop_start()

while turno.value == 0: #Aqui iria algo que siga funcionando hasta que un participante consiga
    soluciones = {}     #la puntuacion maxima y entonces esto ya pare porque el juego ha acabado.
    letra = 'c'
    while (turno.value == 0):
        data = input('Numero y palabra: ')
        if (turno.value == 0):
            if (data == 'STOP'):
                print("Se acabo la ronda")
                turno.value = 1
                client.publish('clients/STOP', data)
                break
            pos, palabra = data.split()
            if (palabra[0] == letra):
                if pos in soluciones:
                    print("Para", pos, "ya tenias la palabra", soluciones[pos])
                    cambio = input("Si deseas cambiar la palabra anterior por la nueva escribe si ")
                    if (cambio == 'si'):
                        soluciones[pos] = [palabra]
                else:
                    soluciones[pos] = [palabra]
            else:
                print(palabra, "no empieza por "+str(letra)+", escribe otra combinacion")
        else:
            print("Se acabo la ronda")
    print(soluciones)#aqui se mandaria la lista al servidor para que ya trabajara con ella.
