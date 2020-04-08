# -*- coding: utf-8 -*-

from paho.mqtt.client import Client

broker="localhost"
#broker="wild.mat.ucm.es"

nombre_usuario=input("¿nombre usuario? ")

def jugar(id_partida,letra):
    #aqui he puesto una funcion cualquiera que consigue modificar
    #el userdata del servidor
    #luego será lafunciondePablo
    n=input("¿pais? ")
    mqttc.publish("clients/estop/partidas/"+id_partida+"/"+nombre_usuario,
                  payload=n)

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
    #
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    spl=msg.topic.split("/") #['clients','estop','partidas','1']
    num_partida=spl[3]
    l="JUGAR RONDA" #llga un msg.payload=b"JUGAR RONDA/C"
    if str(msg.payload)[2:-1]=="JUGAR RONDA":
        letra=msg.payload[-1]
        jugar(num_partida,letra)

def on_message(mqttc, userdata, msg):
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    #para las /solicitudes (pues /servidor y /partidas tienen sus callback propias)
    if msg.topic=="clients/estop/jugadores/"+userdata:
        l=len("NUEVA PARTIDA") #llega el msg.payload=b"NUEVA PARTIDA 3"
        if msg.payload[:l]==b"NUEVA PARTIDA":
            mqttc.subscribe("clients/estop/partidas/"+str(msg.payload[l+1:])[2:-1])
            mqttc.publish("clients/estop/solicitudes",payload="PARTIDA CREADA")
            print("Has creado la partida "+str(msg.payload[l+1:])[2:-1])
            print("Esperando a más jugadores...")
        l=len("NUEVA [0] o CARGAR") #llega el msg.payload=b"NUEVA [0] o CARGAR [1,3]"
        if msg.payload[:l]==b"NUEVA [0] o CARGAR":
            disponibles=msg.payload[l+1:]
            eleccion=input("¿PARTIDA...?\nNUEVA: 0\nCARGAR una: "
                           +str(disponibles)[2:-1]+"\n")
            if eleccion=="0": #si elige 0 se crea nueva
                mqttc.publish("clients/estop/solicitudes/"+userdata,
                          payload=eleccion)
                print("Has creado una partida nueva")
                print("Esperando a más jugadores...")
            elif eleccion in str(disponibles)[2:-1]: #si elige una disponible, se une
                print(eleccion,disponibles)
                mqttc.publish("clients/estop/solicitudes/"+userdata,
                          payload=eleccion)
                mqttc.subscribe("clients/estop/partidas/"+eleccion)
                print("Consigues entrar en la partida",eleccion)
            else: #si elige algo raro, se le echa del juego
                print("No existe esa partida")
                mqttc.disconnect()

        
###
                
mqttc = Client(userdata=nombre_usuario)

#funciones callback:
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.message_callback_add("clients/estop/servidor", callback_servidor)
mqttc.message_callback_add("clients/estop/partidas/#", callback_partidas)

#will_set:
#ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
mqttc.will_set("clients/estop/jugadores/"+nombre_usuario,payload="DISCONNECT")

mqttc.connect(broker)

#suscripciones iniciales del cliente
mqttc.subscribe("clients/estop/jugadores/"+nombre_usuario)
mqttc.subscribe("clients/estop/servidor")

#publicación inicial para unirse al juego
mqttc.publish("clients/estop/solicitudes",payload=nombre_usuario)

mqttc.loop_forever()

###
