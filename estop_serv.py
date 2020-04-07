# -*- coding: utf-8 -*-

from paho.mqtt.client import Client
from multiprocessing import Process,Lock

broker="localhost"
#broker="wild.mat.ucm.es"
max_jugadores_partida=10

def on_publish(mqttc, userdata, mid):
    pass
    #print("MESSAGE_Publish:", userdata, mid)

def on_message(mqttc, userdata, msg):
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    if msg.topic=="clients/estop/solicitudes":
        if userdata=={}:
            mqttc.publish("clients/estop/jugadores/"+str(msg.payload)[2:-1],
                          payload="NUEVA PARTIDA 1")
            userdata[1]=["partida1",str(msg.payload)[2:-1]]
            Process(target=partida,args=(1,)).start()
        else:
            partidas_disponibles=[]
            for clave,valor in userdata.items():
                if len(valor)<max_jugadores_partida+1:
                    partidas_disponibles.append(clave)
            mqttc.publish("clients/estop/jugadores/"+str(msg.payload)[2:-1],
                          payload="NUEVA [0] o CARGAR "+str(partidas_disponibles))
    l=len("clients/estop/solicitudes/")
    if msg.topic[:l]=="clients/estop/solicitudes/":
        if msg.payload==b"0":
            num_partidas=len(userdata)
            mqttc.publish("clients/estop/jugadores/"+msg.topic[l:],
                          payload="NUEVA PARTIDA "+str(num_partidas+1))
            userdata[num_partidas+1]=["partida"+str(num_partidas+1),msg.topic[l:]]
        else:
            userdata[int(str(msg.payload)[2:-1])].append(msg.topic[l:])
    print("estop",userdata)
    #
        
###
mqttc = Client(userdata={})

mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(broker)

mqttc.publish("clients/estop",payload="SERVIDOR ACTIVO")
print("SERVIDOR ACTIVO...")
mqttc.subscribe("clients/estop/solicitudes/#")
#mqttc.subscribe("clients/estop/jugadores/#")
#mqttc.subscribe("clients/estop/partidas/#")


mqttc.loop_forever()
###
