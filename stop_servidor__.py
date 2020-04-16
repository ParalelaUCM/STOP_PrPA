# -*- coding: utf-8 -*-
"""
@authors: Pablo San Gregorio, Sergio Ibañez, Bernardo Perez, Marcos Truchuelo, Elisabet Alejo.
"""

from paho.mqtt.client import Client
from random import shuffle,randint
import pickle

#Creamos la clase jugador para manejarnos mejor con el codigo y acceder asi directamente a objetos basicos de cada jugador.
class Player:
    #Constructora
    def __init__(self, player_id, player_table):
        self.id = player_id #El id unico del jugador.
        self.table = player_table #El tablero del jugador.
        self.score = 0 #la puntuación actual del jugador. Por defecto 0.

    #Funcion que calcula la puntuacion en base a los rivales
    def calculate_score(self, rivals):
        for key in self.table:
            if key!='puntos':
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
            else: #la clave son los puntos que tiene hasta ahora
                pass
        return (self.score)

#
def calcula_puntos(ids,diccs,num_partida,userdata):
    '''
    calcula las puntuaciones cuando se le pasa:
    ids: lista de nombres de usuario
    diccs: lista de diccionarios con las respuestas de cada usuario
    num_partida de los usuarios
    '''
    puntuacionesIniciales=[] #puntuaciones al inicio de la ronda.
    ldp=[] #lista de Players.
    print("\nRespuestas de la ronda:")
    for i in range(len(ids)):
        puntuacionesIniciales.append(diccs[i]['puntos'])
        p=Player(ids[i],diccs[i]) #el player actual
        p.score=diccs[i]['puntos'] #cogemos los puntos suyos actuales
        ldp.append(p)
    #
    puntuacionesFinales=[] #puntuaciones al final de la ronda
    for i in range(len(ldp)):
        jugador=ldp[i]
        puntos=jugador.calculate_score(ldp)
        puntuacionesFinales.append(puntos)
        userdata[int(num_partida)][ids[i]]['puntos']=puntos #actualizamos los puntos
        print(ids[i],puntos)
    #
    puntuacionesRonda=[] #puntuaciones de la ronda en sí
    for i in range(len(ids)):
        puntuacionesRonda.append(puntuacionesFinales[i]-puntuacionesIniciales[i])

    #publicamos resultados a los usuarios:
    if max(puntuacionesFinales) >= max_puntuacion:
        posicion = puntuacionesFinales.index(max(puntuacionesFinales))
        ganador = ids[posicion]
        print("TENEMOS GANADOR "+ganador)
        mqttc.publish(choques+"/partidas/"+str(num_partida)+"/ganador/"+ganador,
                      payload=pickle.dumps([ids,puntuacionesRonda,puntuacionesFinales]))
        userdata.pop(int(num_partida))
        #
    else:
        mqttc.publish(choques+"/partidas/"+str(num_partida)+"/puntos",
                      payload=pickle.dumps([ids,puntuacionesRonda,puntuacionesFinales]))

#
def callback_partidas(mqttc, userdata, msg):
    """
    Aqui gestionamos todos los mensajes que se producen a la hora de empezar una partida
    o mientras esta se esta desarrollando. Como pueden ser mensajes de espera, de stop...
    
    Nos indicamos en que estado se encuentra la partida mediante numeros:
        1: En espera.
        2: En juego.
        3: En recuento de puntos.
    """
    spl=msg.topic.split("/") #['clients','estop','partidas','1','puntos']
    indice_partida=int(spl[3]) #1
    if (msg.payload==b"READY_YES") and (userdata[indice_partida]['info']['estado']==1):
        #si el estado es en espera y llega el READY_YES, iniciamos la ronda
        letra=(userdata[indice_partida]['info']['alfabeto']).pop(0)
        userdata[indice_partida]['info']['estado']=2 #estado: en juego
        for jugador in userdata[indice_partida]:
            mqttc.publish(choques+"/jugadores/"+jugador,payload="PLAY_"+letra)
    #
    if msg.payload==b"STOP":
        userdata[indice_partida]['info']['estado']=3 #estado: en recuento
        for jugador in userdata[indice_partida]:
            mqttc.publish(choques+"/jugadores/"+jugador,payload="STOP")
    #
    elif len(spl)==5:
        #Aqui entramos a calcular los puntos y la varificacion de las palabras. El primer if
        #es para el caso en el que un jugador se quede solo en el desarrollo de la partida, con
        #lo cual, no puede seguir jugando. (Necesario por el randit(1,0), que produciria error cuando
        #se mandan las tablas del resto de jugadores para verificarlas.)
        if len(userdata[indice_partida])==2:
            lista_usuarios=list(userdata[indice_partida])
            lista_usuarios.remove('info')
            usuario_actual=lista_usuarios[0]
            mqttc.publish(choques+"/jugadores/"+usuario_actual,
                                      payload= "JUGADORES_INSUFICIENTES")
        #
        if spl[4]!="puntos" and spl[4]!="votacion": #['clients','estop','partidas','1','jugador']
            mensaje=pickle.loads(msg.payload) #llega el diccionario entero
            #con las respuestas {'comida':None,'pais':'marruecos'}
            for clave,valor in mensaje.items():
                userdata[indice_partida][spl[4]][clave]=valor
            userdata[indice_partida]['info']['confirmados']+=1
            cuantos=len(userdata[indice_partida])-1 #cuantos jugadores hay
            
            if (cuantos == userdata[indice_partida]['info']['confirmados']):
                #cuando ha llegado la info de todos los jugadores, enviamos para su verificacion.
                userdata[indice_partida]['info']['confirmados']=0
                ##
                lista_usuarios=list(userdata[indice_partida])
                #lista_usuarios=['info','berni','sergio',elisa','pablo','marcos']
                lista_usuarios.remove('info')
                #lista_usuarios=['berni','sergio',elisa','pablo','marcos']
                shuffle(lista_usuarios)
                #lista_usuarios=[elisa','sergio','berni','marcos','pablo']
                cuantos=len(lista_usuarios) #cuantos=5
                modulo=randint(1,cuantos-1) #modulo=2
                for i in range(len(lista_usuarios)):
                    # i de 0 a 4, i=3
                    usuario_actual=lista_usuarios[i]
                    # usuario_actual='elisa'
                    usuario_modulo=lista_usuarios[(i+modulo)%cuantos]
                    # usuario_modulo='marcos'
                    datos0=usuario_actual
                    datos1=userdata[indice_partida][usuario_actual]
                    datos=[datos0,datos1]
                    # datos = ['elisa',{'ciudad':'dinamarca,'apellido':'dinamarca'} ]
                    mqttc.publish(choques+"/partidas/"+str(indice_partida)+"/votacion/"+usuario_modulo,
                                  payload=pickle.dumps(datos))
                    #y se lo publicamos al otro usuario para que corrija
            ##
        elif spl[4]=="votacion": #['clients','estop','partidas','1','votacion']
            mensaje=pickle.loads(msg.payload) #llega [nombre,diccionario]
            #con las respuestas {'comida':None,'pais':'marruecos'}
            mensaje_usuario=mensaje[0]
            mensaje_dicc=mensaje[1]
            print(mensaje_usuario)
            print(mensaje_dicc)
            for clave,valor in mensaje_dicc.items():
                userdata[indice_partida][mensaje[0]][clave]=valor
            userdata[indice_partida]['info']['confirmados']+=1
            cuantos=len(userdata[indice_partida])-1 #cuantos jugadores hay
            print(userdata)
            #
            if (cuantos == userdata[indice_partida]['info']['confirmados']):
                #cuando ha llegado la info de todos los jugadores, calculamos puntos.
                userdata[indice_partida]['info']['confirmados']=0
                ids=[]
                diccs=[]
                for clave,valor in userdata[indice_partida].items():
                    if clave!='info':
                        ids.append(clave)
                        diccs.append(valor)
                print("Entramos a calcular los puntos de la ronda")
                calcula_puntos(ids,diccs,spl[3],userdata)
            ##
        elif spl[4]=="puntos": #['clients','estop','partidas','1','puntos']
            ###se han publicado los puntos, y preparamos la siguiente ronda
            for jugador in userdata[indice_partida]['info']['lista_espera']:
                userdata[indice_partida][jugador]={'puntos':0}
            userdata[indice_partida]['info']['lista_espera'] = []
            userdata[indice_partida]['info']['estado']=1 #estado: en espera
            if len(userdata[indice_partida]) - 1 < min_jugadores_partida:
                userdata[indice_partida]['info']['estado']=0 #estado: en 0 porque se necistan jugadores
                for jugador in userdata[indice_partida]:
                    mqttc.publish(choques+"/jugadores/"+jugador, payload="WAIT2")
                print("NO HAY JUGADORES SUFICIENTES PARA EMPEZAR LA SIGUIENTE RONDA")
            else:
                for jugador in userdata[indice_partida]:
                    mqttc.publish(choques+"/jugadores/"+jugador,payload="READY1")

def callback_jugadores(mqttc, userdata, msg):
    """
    maneja las desconexiones de los jugadores eliminándolos del diccionario
    del servidor.
    """
    spl=msg.topic.split("/") #['clients','estop','jugadores','nombre']
    if msg.payload==b"DISCONNECT":
        usuario=spl[3]
        for clave,valor in userdata.items():
            if usuario in valor:
                valor.pop(usuario)
                if len(valor)==1:# and valor=='info':
                    userdata.pop(clave)
                    break
        print("estop userdata",userdata)

#
def callback_solicitudes(mqttc, userdata, msg):
    """
    Aqui gestionamos los mensajes que se producen en el inicio de la partida.
    Gestionamos el numero de partidas, si la partida esta lista o no...
    """

    spl=msg.topic.split("/") #['clients','estop','solicitudes','jugador']
    if len(spl)==3: #['clients','estop','solicitudes']
        usuario=str(msg.payload)[2:-1] 
        if userdata=={}:
            #si no hay nadie aún, mete al usuario en la partida 1 directamente
            mqttc.publish(choques+"/jugadores/"+usuario,payload="NUEVA_PARTIDA 1")
            #Creamos el alfabeto de la partida
            alfabeto=[chr(i) for i in range(97,123)] #65a91 para MAY, 97a123 para minusculas.
            shuffle(alfabeto) #lo barajamos.
            #inicializamos el userdata
            userdata[1]={"info":{'estado':0,'alfabeto':alfabeto,'confirmados':0,'lista_espera':[]},
                         usuario:{'puntos':0}}
        else:
            #si hay alguna partida, deja al usuario elegir entre nueva o cargar
            partidas_disponibles=[]
            for clave,valor in userdata.items():
                if len(valor)<max_jugadores_partida+1:
                    partidas_disponibles.append(clave)
            mqttc.publish(choques+"/jugadores/"+usuario,
                          payload="NUEVA [0] o CARGAR "+str(partidas_disponibles))
    #
    #ahora manejamos la eleccion de partida de cada usuario
    if len(spl)==4: #['clients','estop','solicitudes','jugador']
        usuario=spl[3]
        if msg.payload==b"0":
            p_libre=1 #buscamos que partida esta libre
            while p_libre in userdata.keys():
                p_libre+=1
            mqttc.publish(choques+"/jugadores/"+usuario,
                          payload="NUEVA_PARTIDA "+str(p_libre))
            #Creamos el alfabeto de la partida
            alfabeto=[chr(i) for i in range(97,123)] #65a91 para MAY, 97a123 para minusculas.
            shuffle(alfabeto) #lo barajamos.
            #inicializamos el userdata
            userdata[p_libre]={"info":{'estado':0,'alfabeto':alfabeto,'confirmados':0,'lista_espera':[]}
                               ,usuario:{'puntos':0}}
        #
        else:
            indice_partida=int(str(msg.payload)[2:-1])
            userdata[indice_partida][usuario]={'puntos':0} #Añadimos siempre al usuario, pero si se une tarde hay que eliminarle abajo
            #decidimos cuando empezar la partida, segun los usuarios apuntados
            
            if len(userdata[indice_partida])-1 < min_jugadores_partida:
                #no hay jugadores suficientes
                for jugador in userdata[indice_partida]:
                    mqttc.publish(choques+"/jugadores/"+jugador,payload="NOT_INOF")
            #
            elif userdata[indice_partida]['info']['estado'] < 2:
                if userdata[indice_partida]['info']['estado']==1:
                    mqttc.publish(choques+"/jugadores/"+usuario,payload="READY2")
                else:
                    userdata[indice_partida]['info']['estado']=1 #estado: en espera
                    for jugador in userdata[indice_partida]:
                        mqttc.publish(choques+"/jugadores/"+jugador,payload="READY1")
            #
            elif userdata[indice_partida]['info']['estado'] >= 2:
                userdata[indice_partida]['info']['lista_espera'].append(usuario)
                userdata[indice_partida].pop(usuario) #Eliminamos al usuario que se ha unido tarde
                mqttc.publish(choques+"/jugadores/"+usuario, payload="WAIT1")
                print("Hay un jugador en espera")
    #
    print("estop actual",userdata) #mostramos el diccionario tras cada mensaje
    #

#
def callback_servidor(mqttc, userdata, msg):
    """
    Con esta funcion gestionamos los mensajes de conexion.
    """
    print("MESSAGE:", msg.topic, msg.payload)
    spl=msg.topic.split("/") #['clients','estop','servidor','nombre']
    if msg.payload==b"CONNECT_REQUEST":
        #comprobamos que el usuario no está aún registrado
        ya_registrado=False
        usuario=spl[3]
        print(usuario)
        for clave,valor in userdata.items():
            if usuario in valor:
                ya_registrado=True
                break
        if (usuario=="") or (usuario=="info") or ya_registrado or (usuario=="puntos"):
            #cosas que no aceptamos como nombre_usuario
            mqttc.publish(choques+"/servidor/exception",payload="USER_EXC")
        else:
            #aceptamos al usuario
            mqttc.publish(msg.topic,payload="CONNECT_ACCEPT")
    print("estop userdata",userdata)

#

if __name__ == "__main__":

    broker="wild.mat.ucm.es"
    choques="clients/estop5" #"topic=choques+"/servidor..."
    #Para evitar ponerlo todo el rato, y errores a la hora de probar el codigo.


    """
    En esta 'seccion' se eligen las condiciones de la partida.
    numero minimo y maximo de jugadores, asi como una puntuacion
    maxima que indicara el ganador.
    """
    max_jugadores_partida=10
    min_jugadores_partida=2
    max_puntuacion = 25

    mqttc = Client(userdata={}) #diccionario como userdata para la info del juego
    #'info' indica el estado de la partida:
    #estado: 0 es sin empezar,1 en espera,2 jugando,3 en recuento
    #alfabeto: las letras que quedan por jugar, de inicio ya están desordenadas
    #confirmados para tener una forma de ver si todos envian la info

    #funciones callback:
    mqttc.message_callback_add(choques+"/jugadores/#", callback_jugadores)
    mqttc.message_callback_add(choques+"/partidas/#", callback_partidas)
    mqttc.message_callback_add(choques+"/servidor/#", callback_servidor)
    mqttc.message_callback_add(choques+"/solicitudes/#", callback_solicitudes)

    #will_set:
    #ultimo mensaje que se envía si el Client se desconecta sin usar disconnect()
    mqttc.will_set(choques+"/servidor",payload="SERVER_FAIL")

    mqttc.connect(broker)

    mqttc.publish(choques+"/servidor",payload="SERVER_READY")
    print("SERVIDOR ACTIVO...")

    #suscripciones iniciales del servidor
    mqttc.subscribe(choques+"/servidor/#")
    mqttc.subscribe(choques+"/solicitudes/#")
    mqttc.subscribe(choques+"/jugadores/#")
    mqttc.subscribe(choques+"/partidas/#")

    mqttc.loop_forever()