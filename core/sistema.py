import threading
from typing import List, Dict, Tuple
from .taxi import Taxi, SolicitudServicio


class SistemaCentral:
    def __init__(self):
        # Listas compartidas
        self.taxis: List[Taxi] = []
        self.servicios_control: List[Dict] = []      # Todas las solicitudes realizadas
        self.servicios_seguimiento: List[Dict] = []  # Hasta 5 servicios por día
        self.ganancia_total_diaria: float = 0.0
        self.ganancia_por_taxi: Dict[int, float] = {}

        # Contador de servicios activos
        self.servicios_activos: int = 0
        self.mutex_match = threading.Lock()          # "mutexMatch"
        self.mutex_findeldia = threading.Lock()      # "mutexFindelDía"
        self.mutex_servicio = threading.Lock()       # "mutexServicio"
        self.mutex_control_servicios = threading.Lock()  # "mutexControlServicios"

        # Semáforos / Eventos
        self.no_hay_servicios_activos = threading.Semaphore(0)  # "noHayServiciosActivos"

        # Para simplificar, trabajamos con un solo día (dia = 1)
        self.dia_actual = 1

        # Inicializar algunos taxis de prueba
        self._inicializar_taxis_demo()

    def _inicializar_taxis_demo(self):
        taxi1 = Taxi(1, "Ana", "ABC123", 50, self, posicion_inicial=(0, 0))
        taxi2 = Taxi(2, "Luis", "DEF456", 60, self, posicion_inicial=(5, 5))
        taxi3 = Taxi(3, "Marta", "GHI789", 45, self, posicion_inicial=(10, 0))

        self.taxis.extend([taxi1, taxi2, taxi3])

        for t in self.taxis:
            t.start()

    def procesar_solicitud_cliente(self, solicitud: SolicitudServicio):

        with self.mutex_findeldia:
            self.servicios_activos += 1
            print(f"[Sistema] Activando servicio. Servicios activos: {self.servicios_activos}")

        # Región crítica: match (no puede haber dos clientes haciendo match a la vez)
        taxi_asignado = self._match(solicitud)

        if taxi_asignado is None:
            # No se pudo asignar taxi
            print(f"[Sistema] No hay taxis disponibles para cliente {solicitud.id_cliente}")
            self._registrar_servicio_control(
                solicitud=solicitud,
                taxi_id=None,
                km=0.0,
                costo=0.0,
                calificacion=None,
                aceptado=False
            )
            # Desactivamos el servicio
            self._finalizar_servicio_sin_viaje()
        else:
            # El taxi seguirá el flujo y al terminar llamará a registrar_final_viaje()
            print(f"[Sistema] Taxi {taxi_asignado.id_taxi} asignado al cliente {solicitud.id_cliente}")

    def convertir_direccion_a_coordenadas(self, direccion: str) -> tuple[float, float]:
        """
        Convierte una dirección tipo texto en unas coordenadas (x, y) ficticias
        pero deterministas, para poder calcular distancias.
        """
        if not direccion:
            return (0.0, 0.0)

        h = int(hashlib.md5(direccion.encode("utf-8")).hexdigest(), 16)
        x = (h % 100) / 10.0          # 0.0 - 9.9
        y = ((h // 100) % 100) / 10.0 # 0.0 - 9.9
        return (x, y)


    def _match(self, solicitud: SolicitudServicio) -> Taxi | None:
        from math import sqrt

        with self.mutex_match:
            mejor_taxi = None
            mejor_distancia = float("inf")

            for taxi in self.taxis:
                if not taxi.disponible:
                    continue
                dx = taxi.posicion[0] - solicitud.origen[0]
                dy = taxi.posicion[1] - solicitud.origen[1]
                distancia = sqrt(dx*dx + dy*dy)

                if distancia < mejor_distancia:
                    mejor_distancia = distancia
                    mejor_taxi = taxi

            if mejor_taxi is not None:
                mejor_taxi.asignar_viaje(solicitud)

            return mejor_taxi

    def registrar_final_viaje(self, taxi: Taxi, solicitud: SolicitudServicio,
                              km: float, costo: float, calificacion: float):
        # Región crítica: modificación de servicios + seguimiento
        with self.mutex_servicio:
            taxi.actualizar_calificacion(calificacion)
            taxi.acumular_ganancia(costo)

            # Ganancia por taxi
            self.ganancia_por_taxi[taxi.id_taxi] = self.ganancia_por_taxi.get(taxi.id_taxi, 0.0) + costo
            self.ganancia_total_diaria += costo

            # Registro en servicios_control (todas las solicitudes)
            self._registrar_servicio_control(
                solicitud=solicitud,
                taxi_id=taxi.id_taxi,
                km=km,
                costo=costo,
                calificacion=calificacion,
                aceptado=True
            )

            # Registro en servicios_seguimiento (máx. 5 por día)
            if len(self.servicios_seguimiento) < 5:
                self._registrar_servicio_seguimiento(
                    solicitud=solicitud,
                    taxi_id=taxi.id_taxi,
                    km=km,
                    costo=costo,
                    calificacion=calificacion,
                )

        # Desactivación de servicio
        self._finalizar_servicio_con_viaje()

    def _registrar_servicio_control(self, solicitud, taxi_id, km, costo, calificacion, aceptado: bool):
        with self.mutex_control_servicios:
            self.servicios_control.append({
                "dia": solicitud.dia,
                "id_taxi": taxi_id,
                "id_cliente": solicitud.id_cliente,
                "origen": solicitud.origen,
                "destino": solicitud.destino,
                "direccion_origen": getattr(solicitud, "direccion_origen", None),
                "direccion_destino": getattr(solicitud, "direccion_destino", None),
                "km": km,
                "costo": costo,
                "calificacion": calificacion,
                "aceptado": aceptado,
            })

    def _registrar_servicio_seguimiento(self, solicitud, taxi_id, km, costo, calificacion):
        self.servicios_seguimiento.append({
            "dia": solicitud.dia,
            "id_taxi": taxi_id,
            "id_cliente": solicitud.id_cliente,
            "origen": solicitud.origen,
            "destino": solicitud.destino,
            "direccion_origen": getattr(solicitud, "direccion_origen", None),
            "direccion_destino": getattr(solicitud, "direccion_destino", None),
            "km": km,
            "costo": costo,
            "calificacion": calificacion,
        })
    def _finalizar_servicio_con_viaje(self):
        with self.mutex_findeldia:
            self.servicios_activos -= 1
            print(f"[Sistema] Servicio finalizado. Servicios activos: {self.servicios_activos}")
            if self.servicios_activos == 0:
                # Liberamos al hilo que espere fin de día (si lo hubiera)
                self.no_hay_servicios_activos.release()

    def _finalizar_servicio_sin_viaje(self):
        with self.mutex_findeldia:
            self.servicios_activos -= 1
            print(f"[Sistema] Servicio sin viaje. Servicios activos: {self.servicios_activos}")
            if self.servicios_activos == 0:
                self.no_hay_servicios_activos.release()

    def obtener_reportes(self):
        reportes_diarios = {
            "dia": self.dia_actual,
            "ganancia_total": self.ganancia_total_diaria,
            "servicios_seguimiento": self.servicios_seguimiento,
        }

        reportes_mensuales = []
        for taxi in self.taxis:
            reportes_mensuales.append({
                "id_taxi": taxi.id_taxi,
                "nombre": taxi.nombre,
                "placa": taxi.placa,
                "total_generado": self.ganancia_por_taxi.get(taxi.id_taxi, 0.0),
                "ganancia_taxista": taxi.ganancia_acumulada * 0.8,  # por ejemplo
                "importe_mensual": taxi.ganancia_acumulada * 0.2,
            })

        return reportes_diarios, reportes_mensuales
