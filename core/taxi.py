import threading
import time
import random
import hashlib
from math import sqrt


class SolicitudServicio:
    def __init__(self, id_cliente, origen, destino, dia=1,
                 direccion_origen=None, direccion_destino=None):
        self.id_cliente = id_cliente
        self.origen = origen      # (x, y) para cálculos internos
        self.destino = destino    # (x, y)
        self.dia = dia
        # Direcciones legibles para mostrar en la interfaz / reportes
        self.direccion_origen = direccion_origen
        self.direccion_destino = direccion_destino



class Taxi(threading.Thread):
    def __init__(self, id_taxi, nombre, placa, velocidad_kph, sistema_central, posicion_inicial=(0, 0)):
        super().__init__(name=f"Taxi-{id_taxi}", daemon=True)
        self.id_taxi = id_taxi
        self.nombre = nombre
        self.placa = placa
        self.velocidad_kph = velocidad_kph
        self.sistema_central = sistema_central
        self.posicion = posicion_inicial

        self.disponible = True
        self.calificacion_media = 5.0
        self.numero_viajes = 0
        self.ganancia_acumulada = 0.0

        # Sincronización con el SistemaCentral
        self._viaje_asignado_event = threading.Event()
        self._solicitud_actual = None

    def asignar_viaje(self, solicitud: SolicitudServicio):
        self._solicitud_actual = solicitud
        self.disponible = False
        self._viaje_asignado_event.set()

    def run(self):
        while True:
            self._viaje_asignado_event.wait()

            solicitud = self._solicitud_actual
            if solicitud is None:
                self._viaje_asignado_event.clear()
                continue

            print(f"[{self.name}] Asignado al cliente {solicitud.id_cliente}. "
                  f"Origen: {solicitud.origen}, Destino: {solicitud.destino}")

            # Simular desplazamiento hasta el cliente
            t_llegada, km_hasta_cliente = self._simular_desplazamiento(self.posicion, solicitud.origen)
            print(f"[{self.name}] Llega al cliente {solicitud.id_cliente} "
                  f"en {t_llegada:.2f}s, distancia {km_hasta_cliente:.2f} km")

            # Simular viaje origen → destino
            t_viaje, km_viaje = self._simular_desplazamiento(solicitud.origen, solicitud.destino)
            print(f"[{self.name}] Completa el viaje del cliente {solicitud.id_cliente} "
                  f"en {t_viaje:.2f}s, distancia {km_viaje:.2f} km")

            # Posición final
            self.posicion = solicitud.destino
            km_totales = km_hasta_cliente + km_viaje

            # Cálculo simple de costo
            costo = self._calcular_costo(km_viaje)

            # Simulamos calificación del cliente (1–5)
            calificacion = random.randint(3, 5)

            # Avisar al sistema central (región crítica dentro del sistema)
            self.sistema_central.registrar_final_viaje(
                taxi=self,
                solicitud=solicitud,
                km=km_totales,
                costo=costo,
                calificacion=calificacion,
            )

            # Prepararse para el siguiente viaje
            self._solicitud_actual = None
            self._viaje_asignado_event.clear()
            self.disponible = True

        def _simular_desplazamiento(self, origen, destino):
        dx = destino[0] - origen[0]
        dy = destino[1] - origen[1]
        distancia = sqrt(dx*dx + dy*dy)  # distancia en "unidades" del plano

        # Consideramos estas unidades como km directamente
        km = distancia

        # Velocidad en km/h (mínimo por seguridad)
        if self.velocidad_kph <= 0:
            self.velocidad_kph = 40

        horas = km / self.velocidad_kph
        segundos = horas * 3600

        # Escala para no estar esperando años
        segundos_simulados = max(0.2, segundos * 0.05)
        time.sleep(segundos_simulados)

        return segundos_simulados, km

    def _calcular_costo(self, km_viaje):
        tarifa_base = 0.5      # medio euro de arranque
        tarifa_km = 1.0        # 1 euro por km
        return round(tarifa_base + tarifa_km * km_viaje, 2)


    def actualizar_calificacion(self, nueva_nota: float):
        self.numero_viajes += 1
        self.calificacion_media = (
            (self.calificacion_media * (self.numero_viajes - 1)) + nueva_nota
        ) / self.numero_viajes

    def acumular_ganancia(self, monto: float):
        self.ganancia_acumulada += monto
