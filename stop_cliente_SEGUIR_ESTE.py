from multiprocessing import Value ###Process no lo usamos
from paho.mqtt.client import Client
import paho.mqtt.publish as publish
import pickle ###para el envío de listas y diccionarios
from time import sleep
from random import random

#broker="localhost"
broker="wild.mat.ucm.es"
choques="clients/estop" #topic=choques+"/servidor...
###choques: para evitar colisiones en el broker en las pruebas

nombre_usuario=input("¿nombre usuario? ")

"""
Con esta función print_state se borra todo lo que había en pantalla y se imprime la tabla actual.
Si el mensaje es un error o que alguien ha dado stop o la puntuacion de la ronda se
se pondrá a true el 'need_verification'. Esto hará que solo salga en mensaje por pantalla
sin la tabla ni nada y que se mantenga ahi hata que se le de a enter o entre otro mensaje
"""
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_state(msg= "", need_verification = False, print_table = True):
    os.system('cls' if os.name == 'nt' else "printf '\033c'")
    if (not(need_verification) and print_table):
        print("La letra de esta ronda es la ",str(letra.value)[2:-1].upper()) ###imprimimos la letra actual
        ### para que salga en horizontal, lo veo más intuitivo
        i = 1
        for key in table:
            print(bcolors.WARNING + "["+ str(i)+ "]" +bcolors.ENDC, key.upper(), " : ",end ="")
            if (table[key] != None):
                print(bcolors.UNDERLINE+  table[key] + bcolors.ENDC)
            else:
                print("________")
            i += 1
        print("")
        print("Parar el juego: 'STOP' / '0'\nSalir de la partida: 'EXIT' / '!'")
        print(msg, end="")
    else:
        print(msg, end="")
    if (need_verification):
        input()


"""
Esta funcion se encarga de mostrar la tabla de un rival y recoger los datos de votacion.
El jugador deberá indicar una secuencia numerica separada por espacios referenciando el
número de la categoría que quiera marcar como erronea.

NOTA: Esta función no envía nada al Servidor. Tampoco recibe nada de el. Esta funcion
solamente trata los datos
"""
def vote(rival_table):
    print_state("Te toca verificar la siguiente tabla\n", False, False)
    for key in rival_table:
        print(bcolors.WARNING + "["+ str(i)+ "]" +bcolors.ENDC, key.upper(), " : ",end ="")
        if (table[key] != None):
            print(bcolors.UNDERLINE+  table[key] + bcolors.ENDC)
        else:
            print("________")
        i += 1
    print("")
    print("Escribe separado por espacios los numeros de las categorías que creeas que esten erroneas.")
    errors = input("\n->")
    errors.split(" ")
    lst = list(init_table().keys())
    lst = ["0"]+lst
    for tema in errors:
        try:
            index = int(tema)
        except:
            pass
        if (0 < index and index < len(lst)):
            rival_table[lst[index]] = None
    return (rival_table)



def Stop(num_partida):
    global stop
    stop = True
    #mqttc.publish(choques+"/jugadores/elisa", payload = "Sergio ha hecho Stop, pulsa intro")
    #mqttc.publish(choques+"/partidas/"+str(num_partida), payload="STOP")
    publish.single(choques+"/partidas/"+str(num_partida),
                   payload="STOP", hostname=broker)

def init_table():
    return ({"nombre": None, "animal": None, "comida": None, "pais": None, "ciudad": None,
             "famos@": None})

def insert_word(word, tema, table, letter):
    if (not(stop)):
        if (word[0].upper() == letter[0].upper()):
            table[tema.lower()] = word.upper()
        else:
            print_state("Esa palabra no empieza por " + letter.upper(), True, True)

def fit_theme(tema):
    #lst = ["0","nombre", "animal", "comida", "pais", "ciudad", "famos@"]
    lst = list(init_table().keys())
    lst = ["0"]+lst
    try:
        index = int(tema)
    except:
        return tema
    if (0 <= index and index < len(lst)):
        return (lst[index])
    else:
        return("ERROR")

def new_play():
    print_state()
    #global stop
    #print("\n____Empezamos nueva ronda_____\n")
    #print_state("La letra de la ronda es"+str(letra.value)[2:-1])
    salir = False
    while (not(stop) and not(salir)) :
        #print("\n", table)
        print_state("\n¿Que tema quieres rellenar?\n\n-> ")
        tema = input()
        tema = fit_theme(tema)
        if (not(stop)):
            if (conectado.value == 0):
                return
            if (tema.upper() == "STOP") or (tema == "0"):
                Stop(indice_partida.value)
            elif (tema.upper() =="EXIT") or (tema == "!"):
                salir = True
                conectado.value=0
                mqttc.publish(choques+"/jugadores/"+nombre_usuario, payload = "DISCONNECT")
                mqttc.disconnect()
                print_state("\n____ADIOS___\n", True, False)
            elif (tema.lower() in table):
                msg = "\n¿Que "+ tema.upper() + " se te ocurre con la letra "+ str(letra.value)[2:-1].upper()+"?\n\n-> "
                print_state(msg)
                word = input()
                if (tema.upper() == "STOP") or (tema == "0"):
                    Stop(indice_partida.value)
                elif (tema.upper() =="EXIT") or (tema == "!"):
                    salir = True
                    conectado.value=0
                    mqttc.publish(choques+"/jugadores/"+nombre_usuario, payload = "DISCONNECT")
                    mqttc.disconnect()
                    print_state("\n____ADIOS___\n", True, False)
                elif (word != "BACK") and (word != "<" and len(word)>1):
                    insert_word(word, tema, table, str(letra.value)[2:-1])
                    print_state()
                elif (len(word) <= 1):
                    print_state("Eso no es una palabra, es una simple letra...", True, False)
            else:
                print_state("\nEse tema no existe actualmente... Prueba de nuevo", True)
        else:
            pass
            #print_state("Lo siento pero alguien ya dió el STOP", True, False)
    if not(salir):
        print("\n____FIN DE LA RONDA___\n")

def callback_partidas(mqttc, userdata, msg):
    spl=msg.topic.split("/") #['clients','estop','partidas','1','puntosR']
    if len(spl)==5 and spl[4]=="puntos":
        ###imprimimos las puntuaciones después de cada ronda
        datos=pickle.loads(msg.payload)
        print("PUNTUACIONES | RONDA | TOTALES")
        for ii in range(len(datos[0])):
            print(datos[0][ii],"\t\t",datos[1][ii],"\t",datos[2][ii])
            if datos[0][ii]==userdata[0]:
                userdata[1]+=datos[1][ii]
        print("MIS PUNTOS TOTALES",userdata[1])
        sleep(5) #elisa: He puesto este sleep, porque se iba super rápido, y no daba tiempo a leer bien las puntuaciones.

def on_message(mqttc, userdata, msg):
    print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    ###al final no usamos el on_message pues hemos definido todo en callbacks
    ###separadas para mayor claridad
#
def callback_jugadores(mqttc, userdata, msg):
    #topic: ['clients','estop','jugadores','usuario']
    l=len("NUEVA_PARTIDA") #llega el msg.payload=b"NUEVA_PARTIDA 3"
    mensaje=str(msg.payload)[2:-1]
    ###distinguimos todos los casos de los mensajes que llegan del servidor
    ###todos en mayusculas para saber que son como "claves"
    #
    if mensaje[:l]=="NUEVA_PARTIDA":
        num_partida=mensaje[l+1:]
        ###no nos suscribimos a la partida,solo a los puntos
        ###mqttc.subscribe(choques+"/partidas/"+num_partida)
        mqttc.subscribe(choques+"/partidas/"+num_partida+"/puntos")
        indice_partida.value=int(num_partida)
        userdata[2]=int(num_partida)
        print_state("Has creado la partida "+num_partida+"\n", False, False) ###Para que se vea mas claro
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
            print_state("Consigues entrar en la partida "+str(eleccion)+"\n", False, False)
        else: #si elige algo raro, se le echa del juego
            print("No existe esa partida")
            conectado.value=0
            mqttc.disconnect()
    #
    elif msg.payload[:4]==b"NOT_INOF":
        print("Aún no hay jugadores suficientes para esta partida...")
    #
    elif mensaje[:5]=="READY":
        print("\nPreparados: la siguiente letra es...")
        espera=int(mensaje[5])
        if espera==1:
            sleep(5) ###cuanto esperamos para admitir nueeva gente
            mqttc.publish(choques+"/partidas/"+str(userdata[2]),payload="READY_YES")
    #
    elif mensaje[:4]=="PLAY": #ahora llega algo como PLAY-R
        let=ord(mensaje[-1])
        letra.value = let
        #print_state("EMPIEZA UNA NUEVA RONDA CON LA LETRA "+chr(let), True)
        jugar.value = 1
    #
    elif mensaje == "WAIT":
        print("Partida en marcha, esperando a que empiece la siguiente ronda")
    #
    elif msg.payload == b'STOP':
        global stop
        if stop!=True: ###este jugador no ha hecho stop
            stop = True
            print("Otro jugador ha dado STOP, pulse intro para continuar")
        else: ###este jugador ha hecho stop
            pass

def callback_servidor(mqttc, userdata, msg):
    #maneja las desconexiones inesperadas del servidor
    #desconectando a todos los jugadores
    #print("MESSAGE:", userdata, msg.topic, msg.qos, msg.payload, msg.retain)
    spl=msg.topic.split("/") #['clients','estop','servidor','nombre']
    if msg.payload==b"SERVER_FAIL":
        print("SERVER_FAIL: se ha caido el servidor. Por favor, introduzca 0.") #elisa: He puesto pulse 0, porque si está a mitad de una ronda tienes que darle como al stop para que se salga.
        mqttc.disconnect()
        conectado.value=0
    elif msg.payload==b"SERVER_READY":
        sleep(random()*10)
        mqttc.publish(choques+"/servidor/"+userdata[0],payload="CONNECT_REQUEST")
    elif msg.payload==b"CONNECT_ACCEPT":
        print("SERVIDOR ACTIVO")
        mqttc.unsubscribe(choques+"/servidor/exception")
        mqttc.unsubscribe(choques+"/servidor/"+userdata[0])
        ###si aceptan al jugador, nos desuscribimos de exception
        ###y enviamos la solicitud de acceso a la partida con nuestro nombre
        mqttc.publish(choques+"/solicitudes",payload=userdata[0])
    elif msg.payload==b"USER_EXC":
        print("Usuario no válido")
        print("Prueba otro usuario que no este en uso")
        mqttc.disconnect()
        nombre_usuario=input("¿nombre usuario? ")
        sleep(1)
        mqttc=Client(userdata=[nombre_usuario,0,0])#,clean_session=True)
        mqttc.on_message = on_message
        mqttc.message_callback_add(choques+"/servidor/#", callback_servidor)
        mqttc.message_callback_add(choques+"/partidas/#", callback_partidas)
        mqttc.message_callback_add(choques+"/jugadores/"+nombre_usuario, callback_jugadores)
        mqttc.will_set(choques+"/jugadores/"+nombre_usuario,payload="DISCONNECT")
        mqttc.connect(broker)
        mqttc.subscribe(choques+"/jugadores/"+nombre_usuario)
        mqttc.subscribe(choques+"/servidor")
        mqttc.subscribe(choques+"/servidor/"+nombre_usuario)
        mqttc.subscribe(choques+"/servidor/exception")
        mqttc.publish(choques+"/servidor/"+nombre_usuario,payload="CONNECT_REQUEST")
        mqttc.loop_start()
        #conectado.value=0
        #mqttc.disconnect()
    """
    esto lo había puesto para distingui el caso.
    elif msg.payload==b"REPEATED_USER":
        print("El usuario ya existe")
        nombre_usuario=input("¿nombre usuario? ")
        mqttc.publish(choques+"/servidor/"+nombre_usuario,payload="CONNECT_REQUEST")
    """
    #

###################################################

mqttc = Client(userdata=[nombre_usuario,0,0]) #userdata=[nombre_usuario,puntos,num_partida]

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
    stop=False ###ponemos el stop a False para las siguientes rondas
    table = init_table()
    new_play()
    jugar.value = 0
    ###publicamos las categorias para que trabaje el servidor con ellas
    mqttc.publish(choques+"/partidas/"+str(indice_partida.value)+"/"+nombre_usuario,
                  payload = pickle.dumps(table))
    #publish.single(choques+"/partidas/"+str(indice_partida.value)+"/"+nombre_usuario,
     #              payload=pickle.dumps(table),hostname=broker)
