class Celular:
    def __init__(self, modelo, numero_serie, proprietario):
        self.modelo = modelo
        self.numero_serie = numero_serie
        self.proprietario = proprietario

    def __str__(self):
        return f"Celular(Modelo: {self.modelo}, Número de Série: {self.numero_serie}, Proprietário: {self.proprietario})"