# -*- coding: utf-8 -*-
"""
@authors: Pablo San Gregorio, Sergio Ibañez, Bernardo Perez, Marcos Truchuelo, Elisabet Alejo.
"""

from multiprocessing import Value 
from paho.mqtt.client import Client
import paho.mqtt.publish as publish
import pickle ###para el envío de listas y diccionarios
from time import sleep
from random import random
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
    """
    Borra todo lo que había en pantalla e imprime la tabla actual.
    El 'need_verification' a True hará que solo salga en mensaje por pantalla
    y que se mantenga ahi hasta que se le de a enter o entre otro mensaje
    """
    os.system('cls' if os.name == 'nt' else "printf '\033c'")
    if (not(need_verification) and print_table):
        print("La letra de esta ronda es la",str(letra.value)[2:-1].upper(),"\n")
        i = 1
        for key in table:
            print(bcolors.WARNING + "["+ str(i)+ "]" +bcolors.ENDC, key.upper(), " : ",end ="")
            if (table[key] != None):
                print(bcolors.UNDERLINE+  table[key] + bcolors.ENDC)
            else:
                print("________")
            i += 1
        print("")
        print("Parar el juego: 'STOP' / '0'\nSalir de la partida: 'EXIT' / '!'\nVolver a categorías: 'BACK' / '-'")
        print(msg, end="")
    else:
        print(msg, end="")
    if (need_verification):
        input()

def vote(rival_table):
    """
    Muestra la tabla de un rival y maneja la votacion.
    El jugador deberá indicar una secuencia numerica separada por espacios
    referenciando el número de la categoría que quiera marcar como erronea.
    NOTA: Esta función no se comunica con el Servidor, solamente trata los datos.
    """
    sleep(1)
    print_state("Te toca verificar la siguiente tabla\n\n", False, False)
    i=1
    for key in rival_table:
        print(bcolors.WARNING + "["+ str(i)+ "]" +bcolors.ENDC, key.upper(), " : ",end ="")
        if (rival_table[key] != None):
            print(bcolors.UNDERLINE+  rival_table[key] + bcolors.ENDC)
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
            index = 0
            pass
        if (0 < index and index < len(lst)):
            rival_table[lst[index]] = None
    return (rival_table)

def Stop(num_partida):
    '''
    Para la ronda y manda el STOP a todos los jugadores de la partida actual
    '''
    global stop
    stop = True
    publish.single(choques+"/partidas/"+str(num_partida),payload="STOP", hostname=broker)

def init_table():
    '''
    Inicializa el diccionario con las categorías del juego, lo que va a ser
    el tablero del jugador en cada ronda
    '''
    return ({"nombre": None, "animal": None, "comida": None, "pais": None, "ciudad": None,
             "famos@": None,"marca": None})

def insert_word(word, tema, table, letter):
    '''
    Inserta una palabra en el tablero, si es válida y entra a tiempo
    '''
    if (not(stop)):
        if (word[0].upper() == letter[0].upper()):
            table[tema.lower()] = word.upper()
        else:
            print_state("Esa palabra no empieza por " + letter.upper(), True, True)

def fit_theme(tema):
    '''
    Elige la categoría a rellenar según la entrada, numérica o textual
    '''
    lst = list(init_table().keys()) #pasamos las categorías a una lista
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
    '''
    Se encarga de jugar una ronda, hasta que alguien da al STOP
    '''
    print_state()
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
                if (word.upper() == "STOP") or (word == "0"):
                    Stop(indice_partida.value)
                elif (word.upper() =="EXIT") or (word == "!"):
                    salir = True
                    conectado.value=0
                    mqttc.publish(choques+"/jugadores/"+nombre_usuario, payload = "DISCONNECT")
                    mqttc.disconnect()
                    print_state("\n____ADIOS___\n", True, False)
                elif (word.upper() != "BACK") and (word != "-") and (word != "<" and len(word)>1):
                    insert_word(word, tema, table, str(letra.value)[2:-1])
                    print_state()
                elif (word.upper() == "BACK") or (word == "-"):
                    print_state()
                elif (len(word) == 1):
                    print_state("Eso no es una palabra, es una simple letra...", True, False)
            else:
                print_state("\nEse tema no existe actualmente... Prueba de nuevo", True)
        else:
            pass
    if not(salir):
        print("\n____FIN DE LA RONDA___\n")

def callback_partidas(mqttc, userdata, msg):
    """
    Aqui gestionamos todos los mensajes que le llegan al jugador relativos a la partida:
    -votaciones para invalidar palabras incorrectas
    -recuento de puntos y muestra por pantalla
    -ganador cuando se termina la partida
    o mientras esta se esta desarrollando. Como pueden ser mensajes de espera, de stop...
    """
    spl=msg.topic.split("/") #['clients','stop','partidas','1','puntos/ganador']
    if len(spl)>=5 and (spl[4]=="puntos" or spl[4]=="ganador"):
        #Comprobamos si el mensaje es puntos o ganador primero para ver que mensaje imprimimos
        if spl[4]=="puntos":
            #imprimimos las puntuaciones después de cada ronda
            print_state("Momento de ver las puntuaciones\n", False, False)
        elif spl[4]=="ganador":
            print_state("La partida ha acabado, ¡Y EL GANADOR ES...\n", False, False)
            sleep(5) #Tiempo para que no salga inmediatamente el ganador
            print("\n\t\t..."+str(spl[5].upper())+"!\n\n")
            sleep(5) 
            print("Momento de ver las puntuaciones finales\n")
        #
        datos=pickle.loads(msg.payload) #recibimos los datos sin ordenar
        #
        datos_ord=[ [datos[0][ii],datos[1][ii],datos[2][ii]] for ii in range(len(datos[0])) ]
        # datos_ord = [ ['ber',10,60] , ['sergii',25,100] ]
        datos_ord.sort(reverse=True, key= lambda x: x[2]) #ordenamos los datos por puntuacion total
        print("\nPUNTUACIONES | RONDA | TOTALES")
        for ii in range(len(datos_ord)):
            if datos_ord[ii][0]==userdata[0]:
                userdata[1]+=datos_ord[ii][1]
                print(bcolors.BOLD + datos_ord[ii][0] + bcolors.ENDC,"\t\t",datos_ord[ii][1],"\t",datos_ord[ii][2])
            else:
                print(datos_ord[ii][0],"\t\t",datos_ord[ii][1],"\t",datos_ord[ii][2])
        print("\nMIS PUNTOS TOTALES",userdata[1])
        sleep(7)
        if spl[4]=="ganador":
            msg = "\nSi quieres jugar otra partida pulsa 1, si quieres salir pulsa 0\n\n-> "
            print_state(msg, False, False)
            eleccion = input()
            if int(eleccion) == 1 and eleccion != "":
                mqttc.subscribe(choques+"/servidor/"+userdata[0])
                mqttc.publish(choques+"/servidor/"+userdata[0],payload="CONNECT_REQUEST")
                print("ESPERANDO AL SERVIDOR...")
            else:
                print_state("\n____ADIOS___\n", False, False)
                conectado.value = 0
    #
    if len(spl)>=5 and spl[4]=="votacion": #['clients','stop','partidas','1','votacion']
        #le llega la info de otro usuario para la correción
        datos=pickle.loads(msg.payload) # [nombre_del_otro,dicc_del_otro]
        datos1=datos[1]
        datos1.pop('puntos')
        corregidos=vote(datos1)
        datos=[datos[0],corregidos]
        mqttc.publish(choques+"/partidas/"+str(indice_partida.value)+"/votacion",
                                  payload=pickle.dumps(datos))

#
def callback_jugadores(mqttc, userdata, msg):
    '''
    manejamos los mensajes que le llegan a cada jugador:
    -entrada a la partida
    -esperas entre rondas
    -el propio juego, por aquí recibe el STOP para parar de jugar la ronda
    '''
    #topic: ['clients','stop','jugadores','usuario']
    l=len("NUEVA_PARTIDA") #llega el msg.payload=b"NUEVA_PARTIDA 3"
    mensaje=str(msg.payload)[2:-1]
    #
    if mensaje[:l]=="NUEVA_PARTIDA":
        num_partida=mensaje[l+1:]
        mqttc.subscribe(choques+"/partidas/"+num_partida+"/puntos")
        mqttc.subscribe(choques+"/partidas/"+num_partida+"/votacion/"+userdata[0])
        mqttc.subscribe(choques+"/partidas/"+num_partida+"/ganador/#")
        indice_partida.value=int(num_partida)
        userdata[2]=int(num_partida)
        print_state("Has creado la partida "+num_partida+"\n", False, False)
        print("Esperando a más jugadores...")
    #
    l=len("NUEVA [0] o CARGAR") #llega el msg.payload=b"NUEVA [0] o CARGAR [1,3]"
    if msg.payload[:l]==b"NUEVA [0] o CARGAR":
        disponibles=str(msg.payload[l+1:])[2:-1]
        eleccion=input("¿PARTIDA...?\nNUEVA: [0]\nCARGAR una: "+disponibles+"\n")
        if eleccion=="0": #si elige 0 se crea una nueva
            mqttc.publish(choques+"/solicitudes/"+userdata[0],payload=eleccion)
        elif eleccion in disponibles: #si elige una disponible, se une directamente
            mqttc.subscribe(choques+"/partidas/"+eleccion+"/puntos")
            mqttc.subscribe(choques+"/partidas/"+eleccion+"/votacion/"+userdata[0])
            mqttc.subscribe(choques+"/partidas/"+eleccion+"/ganador/#")
            indice_partida.value=int(eleccion)
            userdata[2]=int(eleccion)
            mqttc.publish(choques+"/solicitudes/"+userdata[0],payload=eleccion)
            print_state("Consigues entrar en la partida "+str(eleccion)+"\n", False, False)
        else: #si elige algo raro, se le echa del juego
            print("No existe esa partida")
            conectado.value=0
            mqttc.disconnect()
    #
    elif mensaje[:8]==b"NOT_INOF":
        print("Aún no hay jugadores suficientes para esta partida.")
        print("Esperando a más jugadores...")
    #
    elif mensaje[:5]=="READY":
        print_state("\nPREPARADOS\n\nLa siguiente letra es...",False,False)
        espera=int(mensaje[5])
        if espera==1:
            sleep(5)
            mqttc.publish(choques+"/partidas/"+str(userdata[2]),payload="READY_YES")
    #
    elif mensaje[:4] == "WAIT":
        opcion = int(mensaje[4:5])
        if opcion == 1:
            print("Partida en marcha, esperando a que empiece la siguiente ronda")
        elif opcion == 2:
            print_state("Numero de jugadores insuficiente para iniciar la ronda\n", False, False)
            print("Esperando a mas jugadores...")
    #
    elif mensaje[:4]=="PLAY":
        let=ord(mensaje[-1])
        letra.value = let
        jugar.value = 1            
    #
    elif msg.payload == b'STOP':
        global stop
        if stop!=True: #si este jugador no ha hecho stop, lo paramos
            stop = True
            print("Otro jugador ha dado STOP, pulse intro para continuar")
    #
    elif msg.payload == b"JUGADORES_INSUFICIENTES":
        print_state("Lo siento, todos los jugadores se han marchado, vuelve más tarde :)",True, False)
        print("\n____ADIOS___\n")
        sleep(1)
        conectado.value=0
        mqttc.publish(choques+"/jugadores/"+userdata[0], payload = "DISCONNECT")
        mqttc.disconnect()

def callback_servidor(mqttc, userdata, msg):
    '''
    maneja la conexión inicial con el servidor hasta que recibe permiso,
    y las desconexiones inesperadas del servidor desconectando a todos los jugadores
    '''
    if msg.payload==b"SERVER_FAIL":
        print("SERVER_FAIL: se ha caido el servidor. Por favor, introduzca 0.")
        mqttc.disconnect()
        conectado.value=0
    elif msg.payload==b"SERVER_READY":
        sleep(random()*10)
        mqttc.publish(choques+"/servidor/"+userdata[0],payload="CONNECT_REQUEST")
    elif msg.payload==b"CONNECT_ACCEPT":
        print("SERVIDOR ACTIVO")
        mqttc.unsubscribe(choques+"/servidor/exception")
        mqttc.unsubscribe(choques+"/servidor/"+userdata[0])
        mqttc.publish(choques+"/solicitudes",payload=userdata[0])
    elif msg.payload==b"USER_EXC":
        print("Usuario no válido")
        print("Prueba otro usuario que no este en uso")
        mqttc.disconnect()
        nombre_usuario=input("¿nombre usuario? ")
        sleep(1)
        mqttc=Client(userdata=[nombre_usuario,0,0])#,clean_session=True)
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
    #

#

if __name__ == "__main__":    

    broker="wild.mat.ucm.es"
    choques="clients/stop" #topic=choques+"/servidor...
    ###choques: para evitar colisiones en el broker en las pruebas

    nombre_usuario=input("¿nombre usuario? ") #identificador del usuario

    mqttc = Client(userdata=[nombre_usuario,0,0])
    #userdata=[nombre_usuario,puntos_usuario,numero_partida_usuario]

    #funciones callback:
    #redirigimos los mensajes según el topic del que vengan para mayor claridad
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

    #

    conectado = Value('i',1)
    indice_partida = Value('i',0) #indice de la partida a la que se conecta el jugador
    jugar = Value('i', 0)
    letra = Value('c', b'z') #el character tiene que ser de tipo byte para el Value

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
    mqttc.disconnect()
