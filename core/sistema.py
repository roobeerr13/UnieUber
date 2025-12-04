import threading
import time
from typing import List, Dict, Tuple
import hashlib
from .taxi import Taxi, SolicitudServicio
from .sistema_asignacion import SistemaAsignacion
from .cliente_mejorado import ClienteMejorado


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

        # Sistema de asignación avanzado (Senafiris, tarifas dinámicas, etc.)
        self.sistema_asignacion = SistemaAsignacion()
        # Pasar referencia al sistema central para el resumen diario
        self.sistema_asignacion._sistema_central = self
        
        # Registro de clientes mejorados (para frecuencia y estrellas)
        self.clientes_mejorados: Dict[str, ClienteMejorado] = {}

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
        """
        Selecciona el mejor taxi para una solicitud usando el sistema de asignación avanzado.
        Integra distancia, Senafiris y prioridad de clientes.
        """
        with self.mutex_match:
            # Obtener o crear cliente mejorado para frecuencia/estrellas
            cliente_mejorado = self._obtener_cliente_mejorado(solicitud.id_cliente)
            
            # Crear objeto temporal con posición para el sistema de asignación
            class ClienteTemp:
                def __init__(self, cliente_mejorado, posicion):
                    self.id_cliente = cliente_mejorado.id_cliente
                    self.nombre = cliente_mejorado.nombre
                    self.frecuencia = cliente_mejorado.frecuencia
                    self.estrellas = cliente_mejorado.estrellas
                    self.posicion = posicion
            
            cliente_temp = ClienteTemp(cliente_mejorado, solicitud.origen)
            
            # Usar el sistema de asignación avanzado
            resultado = self.sistema_asignacion.seleccionar_conductor_para_cliente(
                cliente_temp, self.taxis
            )
            
            if resultado is None:
                return None
            
            taxi_seleccionado = resultado["conductor"]
            motivo = resultado["motivo"]
            
            print(f"[Sistema] Taxi {taxi_seleccionado.id_taxi} seleccionado para cliente {solicitud.id_cliente} "
                  f"(motivo: {motivo}, distancia: {resultado['distancia']:.2f} km, "
                  f"estrellas cliente: {resultado['cliente_estrellas']}⭐)")
            
            # Almacenar información de tarifa en la solicitud para uso posterior
            solicitud.tarifa_base = resultado["tarifa_base"]
            solicitud.tarifa_km = resultado["tarifa_km"]
            solicitud.motivo_seleccion = motivo
            
            if taxi_seleccionado is not None:
                taxi_seleccionado.asignar_viaje(solicitud)

            return taxi_seleccionado
    
    def _obtener_cliente_mejorado(self, id_cliente: str) -> ClienteMejorado:
        """
        Obtiene o crea un ClienteMejorado para un cliente dado.
        """
        if id_cliente not in self.clientes_mejorados:
            self.clientes_mejorados[id_cliente] = ClienteMejorado(
                id_cliente=id_cliente,
                nombre=f"Cliente-{id_cliente}",
                frecuencia=0
            )
        return self.clientes_mejorados[id_cliente]

    def registrar_final_viaje(self, taxi: Taxi, solicitud: SolicitudServicio,
                              km: float, costo: float, calificacion: float):
        # Región crítica: modificación de servicios + seguimiento
        with self.mutex_servicio:
            taxi.actualizar_calificacion(calificacion)
            taxi.acumular_ganancia(costo)
            
            # Actualizar contadores Senafiris del taxi
            taxi.viajes_hoy += 1
            taxi.tiempo_desde_ultimo_viaje = 0
            taxi.ultima_actualizacion_tiempo = time.time()

            # Ganancia por taxi
            self.ganancia_por_taxi[taxi.id_taxi] = self.ganancia_por_taxi.get(taxi.id_taxi, 0.0) + costo
            self.ganancia_total_diaria += costo
            
            # Actualizar cliente mejorado (frecuencia y estrellas)
            cliente_mejorado = self._obtener_cliente_mejorado(solicitud.id_cliente)
            cliente_mejorado.incrementar_frecuencia()
            cliente_mejorado.actualizar_calificacion(calificacion)
            
            # Registrar en el sistema de asignación
            self.sistema_asignacion.registrar_viaje_completado(
                conductor=taxi,
                cliente=cliente_mejorado,
                km=km,
                tarifa=costo
            )

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
            total_generado = self.ganancia_por_taxi.get(taxi.id_taxi, 0.0)
            reportes_mensuales.append({
                "id_taxi": taxi.id_taxi,
                "nombre": taxi.nombre,
                "placa": taxi.placa,
                "total_generado": total_generado,
                "ganancia_taxista": total_generado * 0.8,
                "importe_mensual": total_generado * 0.2,
            })

        return reportes_diarios, reportes_mensuales
