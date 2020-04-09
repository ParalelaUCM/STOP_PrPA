class Player:
    #Constructora
    def __init__(self, player_id, player_table):
        self.id = player_id #El id unico del jugador
        self.table = player_table #El tablero del jugador
        self.score = 0 #la puuntuacion actual del jugador. Por defecto 0

    #Funcion que calcula la puntuacion en base a los rivales
    def calculate_score(self, rivals):
        for key in self.table:
            filled = (self.table[key] != None) #Comprobamos que este rellenado ese tema
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
        return (self.score) #Para comprobar que funciona

#Ejemplo con dos jugadores
p1 = Player(1, {"comida": "canelones", "pais": "canada", "ciudad": "copanhage"})

p2 = Player(2, {"comida": "camaron", "pais": "canada", "ciudad": None})

print("El jugador 1 obtuvo una puntuacion de:",p1.calculate_score([p1, p2]), "pts")
print("El jugador 2 obtuvo una puntuacion de:",p2.calculate_score([p1, p2]), "pts")

