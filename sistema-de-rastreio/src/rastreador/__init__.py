import random

class Rastreador:
    def __init__(self):
        self.is_tracking = False
        self.localizacao_atual = None

    def iniciar_rastreamento(self):
        self.is_tracking = True
        # Lógica para iniciar o rastreamento
        print("Rastreamento inciado")

    def parar_rastreamento(self):
        self.is_tracking = False
        # Lógica para parar o rastreamento
        print("Rastreamento parado")

    def obter_localizacao(self):
        if self.is_tracking:
            # Lógica para obter a localização atual
           latitude = round(random.uniform(-90, 90), 6)
           longitude = round(random.uniform(-180, 180), 6)
           self.localizacao_atual = (latitude, longitude)
           return sel.localizacao_atual
        else:
          raise Exception("Rastreamento não inciado")