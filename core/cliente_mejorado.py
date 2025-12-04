"""
Módulo mejorado para gestionar clientes con frecuencia y estrellas.
"""


class ClienteMejorado:
    """
    Representa a un cliente con seguimiento de frecuencia y estrellas.
    
    Atributos:
        id_cliente: identificador único del cliente.
        nombre: nombre del cliente.
        frecuencia: número de viajes realizados.
        estrellas: valoración de 1 a 5 estrellas basada en frecuencia.
        calificacion_promedio: promedio de calificaciones recibidas del cliente.
    """

    def __init__(self, id_cliente, nombre="Cliente", frecuencia=0, calificacion_promedio=5.0):
        self.id_cliente = id_cliente
        self.nombre = nombre
        self.frecuencia = frecuencia
        self.calificacion_promedio = calificacion_promedio
        self._actualizar_estrellas()

    def _actualizar_estrellas(self):
        """
        Calcula estrellas basado en la frecuencia:
        - 0-2 viajes: 1 estrella
        - 3-5 viajes: 2 estrellas
        - 6-10 viajes: 3 estrellas
        - 11-20 viajes: 4 estrellas
        - 21+ viajes: 5 estrellas
        """
        if self.frecuencia < 3:
            self.estrellas = 1
        elif self.frecuencia < 6:
            self.estrellas = 2
        elif self.frecuencia < 11:
            self.estrellas = 3
        elif self.frecuencia < 21:
            self.estrellas = 4
        else:
            self.estrellas = 5

    def incrementar_frecuencia(self):
        """Incrementa la frecuencia y recalcula las estrellas."""
        self.frecuencia += 1
        self._actualizar_estrellas()

    def actualizar_calificacion(self, nueva_calificacion):
        """Actualiza el promedio de calificación del cliente."""
        # Promedio móvil simple
        self.calificacion_promedio = (
            (self.calificacion_promedio * (self.frecuencia - 1) + nueva_calificacion)
            / self.frecuencia
        )

    def __repr__(self):
        return (
            f"ClienteMejorado(id={self.id_cliente}, nombre={self.nombre}, "
            f"frecuencia={self.frecuencia}, estrellas={self.estrellas}⭐)"
        )
