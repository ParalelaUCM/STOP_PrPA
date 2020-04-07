from paho.mqtt.client import Client
import paho.mqtt.publish as publish

def on_message(client, userdata, msg):
    global stop
    splitted_msg = str(msg.payload).split("'")[1].split(" ")
    try:
        msg_id = splitted_msg[0]
        msg_content = splitted_msg[1]
        if (msg_id == "msg:"):
            if (msg_content == "STOP"):
                print("\n______\nAlguien hizo STOP. Pulsa INTRO para continuar\n______\n")
                stop = True
    except:
        print ("")

client = Client()
client.on_message = on_message
client.connect("wild.mat.ucm.es")
topic = 'clients/STOP'
client.subscribe(topic)
client.loop_start()

stop = False

def Stop():
    global stop
    stop = True
    publish.single(topic, payload="msg: STOP", hostname="wild.mat.ucm.es")

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



#Cliente de Berni
while (True):
    stop = False
    #Si la partida ha empezado:
    new_play("d")
    #Enviar mi tabla al servidor
    #Recibir puntuacion y mostrar
#Se acabo
