class Rastreador:
    def __init__(self):
        self.is_tracking = False

    def iniciar_rastreamento(self):
        self.is_tracking = True
        # Lógica para iniciar o rastreamento

    def parar_rastreamento(self):
        self.is_tracking = False
        # Lógica para parar o rastreamento

    def obter_localizacao(self):
        if self.is_tracking:
            # Lógica para obter a localização atual
            pass
        else:
            raise Exception("Rastreamento não iniciado.")