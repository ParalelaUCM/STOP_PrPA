# -*- coding: utf-8 -*-

from paho.mqtt.client import Client

broker="localhost"
#broker="wild.mat.ucm.es"

nombre_usuario=input("¿nombre usuario? ")

def jugar(id_partida):
    n=input("¿cuanto?")
    mqttc.publish("clients/estop/partidas/"+id_partida,
                  payload=nombre_usuario+" suma "+n)

#
def on_connect(mqttc, userdata, flags, rc):
    #print("CONNECT:", userdata, flags, rc)
    pass

def on_message(mqttc, userdata, msg):
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    if msg.topic=="clients/estop/jugadores/"+userdata:
        l=len("NUEVA PARTIDA")
        if msg.payload[:l]==b"NUEVA PARTIDA":
            print("aqui:",str(msg.payload[l+1:])[2:-1])
            mqttc.subscribe("clients/estop/partidas/"+str(msg.payload[l+1:])[2:-1])
            print("Has creado la partida 1")
        l=len("NUEVA [0] o CARGAR")
        if msg.payload[:l]==b"NUEVA [0] o CARGAR":
            disponibles=msg.payload[l+1:]
            eleccion=input("¿qué quiereshacer?\nNUEVA: 0\nCARGAR una: "
                           +str(disponibles)[2:-1]+"\n")
            print("Has elegido",eleccion)
            if eleccion=="0":
                mqttc.publish("clients/estop/solicitudes/"+userdata,
                          payload=eleccion)
                print("Has creado una partida nueva")
            elif eleccion in str(disponibles)[2:-1]:
                print(eleccion,disponibles)
                mqttc.publish("clients/estop/solicitudes/"+userdata,
                          payload=eleccion)
                mqttc.subscribe("clients/estop/partidas/"+eleccion)
                print("Consigues entrar en la partida",eleccion)
            else:
                print("No existe esa partida")
                mqttc.disconnect()
    #
    l=len("clients/estop/partidas/")
    if msg.topic[:l]=="clients/estop/partidas/" and msg.payload==b"jugar":
        partida=msg.topic[l:]
        jugar(partida)
#
def callback_partidas(mqttc, userdata, msg):
    print("hoLAHFHFL")
            
###
mqttc = Client(userdata=nombre_usuario)

mqttc.on_message = on_message
mqttc.on_connect = on_connect

mqttc.connect(broker)

mqttc.subscribe("clients/estop/jugadores/"+nombre_usuario)
mqttc.publish("clients/estop/solicitudes",payload=nombre_usuario)
mqttc.message_callback_add("clients/estop/partidas/1", callback_partidas)

mqttc.loop_forever()
###
