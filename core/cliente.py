import threading
import random
from .taxi import SolicitudServicio


class Cliente(threading.Thread):
    def __init__(self, id_cliente, sistema_central, origen=None, destino=None, dia=1):
        super().__init__(name=f"Cliente-{id_cliente}", daemon=True)
        self.id_cliente = id_cliente
        self.sistema_central = sistema_central
        self.dia = dia

        # Si no se dan coordenadas, se generan aleatorias
        self.origen = origen if origen is not None else (random.randint(0, 10), random.randint(0, 10))
        self.destino = destino if destino is not None else (random.randint(0, 10), random.randint(0, 10))

    def run(self):
        solicitud = SolicitudServicio(
            id_cliente=self.id_cliente,
            origen=self.origen,
            destino=self.destino,
            dia=self.dia
        )
        print(f"[{self.name}] Solicita taxi. Origen {self.origen}, destino {self.destino}")
        self.sistema_central.procesar_solicitud_cliente(solicitud)
