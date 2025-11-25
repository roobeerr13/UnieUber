# core/cliente.py
import threading
import random
from .taxi import SolicitudServicio


class Cliente(threading.Thread):
    """
    Hilo que simula a un cliente que realiza una única solicitud de taxi.
    """

    def __init__(self, id_cliente, sistema_central,
                 origen=None, destino=None,
                 direccion_origen=None, direccion_destino=None,
                 dia=1):
        super().__init__(name=f"Cliente-{id_cliente}", daemon=True)
        self.id_cliente = id_cliente
        self.sistema_central = sistema_central
        self.dia = dia

        self.direccion_origen = direccion_origen
        self.direccion_destino = direccion_destino

        # Si no se dan coordenadas pero sí direcciones, las convertimos
        if origen is None and direccion_origen is not None:
            origen = sistema_central.convertir_direccion_a_coordenadas(direccion_origen)
        if destino is None and direccion_destino is not None:
            destino = sistema_central.convertir_direccion_a_coordenadas(direccion_destino)

        # Si tampoco hay direcciones, usamos coords aleatorias
        if origen is None:
            origen = (random.randint(0, 10), random.randint(0, 10))
        if destino is None:
            destino = (random.randint(0, 10), random.randint(0, 10))

        self.origen = origen
        self.destino = destino

    def run(self):
        solicitud = SolicitudServicio(
            id_cliente=self.id_cliente,
            origen=self.origen,
            destino=self.destino,
            dia=self.dia,
            direccion_origen=self.direccion_origen,
            direccion_destino=self.direccion_destino
        )
        print(f"[{self.name}] Solicita taxi. Origen {self.direccion_origen or self.origen}, "
              f"destino {self.direccion_destino or self.destino}")
        self.sistema_central.procesar_solicitud_cliente(solicitud)
