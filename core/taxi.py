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
        
        # Atributos para el sistema de asignación avanzado (Senafiris)
        self.viajes_hoy = 0  # Contador diario de viajes
        self.tiempo_desde_ultimo_viaje = 3600  # segundos (inicialmente una hora)
        self.ultima_actualizacion_tiempo = time.time()

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

            # Cálculo de costo usando tarifas dinámicas del sistema
            costo = self._calcular_costo(km_viaje, solicitud)

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

    def _calcular_costo(self, km_viaje, solicitud=None):
        """
        Calcula el costo del viaje usando tarifas dinámicas.
        Si la solicitud tiene tarifas definidas (del sistema de asignación), las usa.
        Si no, usa tarifas por defecto.
        """
        if solicitud and hasattr(solicitud, 'tarifa_base') and hasattr(solicitud, 'tarifa_km'):
            tarifa_base = solicitud.tarifa_base
            tarifa_km = solicitud.tarifa_km
        else:
            # Fallback: usar tarifas del sistema de asignación si está disponible
            if hasattr(self.sistema_central, 'sistema_asignacion'):
                sistema_asignacion = self.sistema_central.sistema_asignacion
                if sistema_asignacion.modo_tarifa_alta:
                    tarifa_base = sistema_asignacion.tarifa_base_alta
                    tarifa_km = sistema_asignacion.tarifa_km_alta
                else:
                    tarifa_base = sistema_asignacion.tarifa_base_normal
                    tarifa_km = sistema_asignacion.tarifa_km_normal
            else:
                # Tarifas por defecto
                tarifa_base = 0.5
                tarifa_km = 1.0
        
        return round(tarifa_base + tarifa_km * km_viaje, 2)


    def actualizar_calificacion(self, nueva_nota: float):
        self.numero_viajes += 1
        self.calificacion_media = (
            (self.calificacion_media * (self.numero_viajes - 1)) + nueva_nota
        ) / self.numero_viajes

    def acumular_ganancia(self, monto: float):
        """
        Acumula la ganancia total generada (el monto completo del viaje).
        El cálculo del 80% para el taxista se hace en los reportes.
        """
        self.ganancia_acumulada += monto
