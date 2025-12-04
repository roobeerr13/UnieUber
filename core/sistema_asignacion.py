"""
Sistema de asignación avanzado con Senafiris, tarifas dinámicas y resumen diario.
"""
import time
import threading
from datetime import datetime, time as dt_time, timedelta
from math import sqrt


class SistemaAsignacion:
    """
    Gestiona la asignación de conductores a clientes con lógica avanzada:
    - Selección por distancia + Senafiris
    - Prioridad de clientes por frecuencia/estrellas
    - Tarifas dinámicas según la hora
    - Generación de resumen diario a las 00:00
    """

    def __init__(self):
        """Inicializa el sistema de asignación."""
        self.tarifa_base_normal = 0.5  # € de arranque
        self.tarifa_km_normal = 1.0    # € por km (hora normal)
        self.tarifa_base_alta = 1.0    # € de arranque (tarifa alta)
        self.tarifa_km_alta = 1.5      # € por km (tarifa alta después de 21:00)
        
        self.modo_tarifa_alta = False  # Bandera para activar tarifa alta
        self.hora_activacion_tarifa_alta = 21  # 21:00 (9 PM)
        self.hora_resumen_diario = 0   # 00:00 (medianoche)
        
        # Reloj virtual: 30x más rápido (1 min real = 2 seg virtuales)
        self.virtual_speed = 30
        self.virtual_start_time = datetime.now()
        
        # Contadores diarios (se resetean a las 00:00)
        self.viajes_totales_hoy = 0
        self.ganancias_totales_hoy = 0.0
        self.ganancias_tarifa_alta_hoy = 0.0
        self.conductor_mas_viajes_hoy = None
        self.cliente_mas_frecuente_hoy = None
        
        # Históricos (nunca se resetean)
        self.resumen_diarios = []  # Lista de resúmenes diarios generados
        
        # Hilo para monitoreo de hora y tareas automáticas
        self.hilo_monitor = None
        self._stop_monitor = False
        self._iniciar_monitor()
    
    def obtener_hora_virtual(self):
        """Obtiene la hora virtual actual (30x más rápida)."""
        real_elapsed = (datetime.now() - self.virtual_start_time).total_seconds()
        virtual_elapsed = real_elapsed * self.virtual_speed
        virtual_time = self.virtual_start_time + timedelta(seconds=virtual_elapsed)
        return virtual_time

    def _iniciar_monitor(self):
        """Inicia el hilo de monitoreo de hora."""
        self.hilo_monitor = threading.Thread(target=self._monitor_hora, daemon=True)
        self.hilo_monitor.start()

    def _monitor_hora(self):
        """Monitorea la hora virtual para actualizar tarifas y generar resumen diario."""
        ultima_hora_procesada = None
        ultima_tarifa_procesada = None
        
        while not self._stop_monitor:
            # Usar hora virtual (30x más rápida)
            hora_virtual = self.obtener_hora_virtual()
            hora_actual = hora_virtual.hour
            
            # Cambio a tarifa alta a las 21:00
            if hora_actual >= self.hora_activacion_tarifa_alta and ultima_tarifa_procesada != "alta":
                self.modo_tarifa_alta = True
                print(f"[SistemaAsignacion] ⏰ Activada tarifa alta a las {hora_actual}:00 (hora virtual)")
                ultima_tarifa_procesada = "alta"
            
            # Cambio a tarifa normal antes de las 21:00
            if hora_actual < self.hora_activacion_tarifa_alta and ultima_tarifa_procesada != "normal":
                self.modo_tarifa_alta = False
                print(f"[SistemaAsignacion] ⏰ Activada tarifa normal a las {hora_actual}:00 (hora virtual)")
                ultima_tarifa_procesada = "normal"
            
            # Generar resumen diario a las 00:00 (virtual)
            if hora_actual == self.hora_resumen_diario and ultima_hora_procesada != hora_actual:
                sistema_central = getattr(self, '_sistema_central', None)
                self.generar_resumen_diario(sistema_central)
                ultima_hora_procesada = hora_actual
            
            # Resetear control de hora a las 01:00 para evitar ejecuciones repetidas
            if hora_actual == 1:
                ultima_hora_procesada = None
            
            time.sleep(2)  # Revisar cada 2 segundos reales (equivale a 1 minuto virtual)

    def detener_monitor(self):
        """Detiene el hilo de monitoreo."""
        self._stop_monitor = True
        if self.hilo_monitor:
            self.hilo_monitor.join(timeout=2)

    @staticmethod
    def calcular_distancia(origen, destino):
        """
        Calcula la distancia euclidiana entre dos puntos (x, y).
        El sistema usa coordenadas ficticias, no lat/lon reales.
        
        Args:
            origen: tupla (x, y)
            destino: tupla (x, y)
        
        Returns:
            Distancia en unidades del plano (float)
        """
        if None in (origen, destino):
            return float("inf")
        
        x1, y1 = origen
        x2, y2 = destino
        
        dx = x2 - x1
        dy = y2 - y1
        distancia = sqrt(dx*dx + dy*dy)
        
        return distancia

    def calcular_puntuacion_senafiris(self, conductor):
        """
        Calcula la puntuación Senafiris de un conductor.
        
        La puntuación considera:
        - Reputación (calificación media del conductor)
        - Número de viajes hoy (menos viajes = mejor puntuación)
        - Tiempo desde último viaje (más tiempo = mejor, permite descanso)
        
        Args:
            conductor: objeto Conductor
        
        Returns:
            Puntuación Senafiris (float, mayor es mejor)
        """
        # Reputación: basada en calificación (0-5 estrellas)
        reputacion_score = conductor.calificacion_media * 20  # 0-100
        
        # Balance de carga: penalizar conductores con muchos viajes hoy
        # Si tiene 0 viajes, score = 100; si tiene 10, score = 0
        carga_score = max(0, 100 - conductor.viajes_hoy * 10)
        
        # Tiempo de descanso: actualizar tiempo desde último viaje
        tiempo_actual = time.time()
        ultima_actualizacion = getattr(conductor, 'ultima_actualizacion_tiempo', tiempo_actual)
        tiempo_transcurrido = tiempo_actual - ultima_actualizacion
        # Actualizar tiempo desde último viaje si ha pasado tiempo
        if tiempo_transcurrido > 0:
            conductor.tiempo_desde_ultimo_viaje = getattr(conductor, 'tiempo_desde_ultimo_viaje', 3600) + tiempo_transcurrido
            conductor.ultima_actualizacion_tiempo = tiempo_actual
        
        tiempo_ultimo = getattr(conductor, 'tiempo_desde_ultimo_viaje', 3600)  # segundos
        descanso_score = min(100, tiempo_ultimo / 36)  # 100 si pasó 1 hora
        
        # Puntuación final (promedio ponderado)
        senafiris = (reputacion_score * 0.4 + carga_score * 0.4 + descanso_score * 0.2)
        
        return round(senafiris, 2)

    def seleccionar_conductor_para_cliente(self, cliente, lista_conductores):
        """
        Selecciona el mejor conductor para un cliente usando un score combinado.
        
        Proceso:
        1. Filtra conductores disponibles.
        2. Calcula score combinado: distancia + carga + Senafiris
        3. Selecciona el conductor con mejor score.
        
        Args:
            cliente: objeto ClienteMejorado
            lista_conductores: lista de conductores disponibles
        
        Returns:
            dict con claves:
                - conductor: conductor seleccionado
                - distancia: distancia en km
                - tarifa_base: tarifa base aplicada
                - tarifa_km: tarifa por km aplicada
                - cliente_estrellas: estrellas del cliente
                - motivo: 'distancia', 'senafiris' o 'balanceado'
        """
        if not lista_conductores:
            return None
        
        conductores_disponibles = [c for c in lista_conductores if getattr(c, 'disponible', True)]
        
        if not conductores_disponibles:
            return None
        
        # Calcular score combinado para cada conductor
        scores = {}
        distancias = {}
        
        # Encontrar el conductor con menos viajes para balancear
        min_viajes = min(c.viajes_hoy for c in conductores_disponibles)
        max_viajes = max(c.viajes_hoy for c in conductores_disponibles)
        diferencia_viajes = max_viajes - min_viajes
        
        for conductor in conductores_disponibles:
            pos_conductor = getattr(conductor, 'posicion', (0, 0))
            pos_cliente = getattr(cliente, 'posicion', (0, 0))
            
            # Distancia (normalizada, menor es mejor)
            dist = self.calcular_distancia(pos_conductor, pos_cliente)
            distancias[conductor] = dist
            dist_score = dist  # Distancia directa (menor es mejor)
            
            # Puntuación Senafiris (mayor es mejor)
            senafiris_score = self.calcular_puntuacion_senafiris(conductor)
            
            # Penalización por carga (más viajes = peor)
            # Aumentamos el peso de la penalización para balancear mejor
            # Si hay diferencia de viajes, penalizamos más a los que tienen más
            if diferencia_viajes > 0:
                # Penalización proporcional: si tiene más viajes que el mínimo, penalizar más
                viajes_extra = conductor.viajes_hoy - min_viajes
                carga_penalty = viajes_extra * 2.0  # Penalización más fuerte
            else:
                carga_penalty = 0
            
            # Bonus por tener menos viajes (para balancear)
            if conductor.viajes_hoy == min_viajes and diferencia_viajes > 0:
                bonus_balance = 1.0  # Bonus para el que tiene menos viajes
            else:
                bonus_balance = 0
            
            # Score combinado: distancia + penalización carga - bonus Senafiris - bonus balance
            # Normalizamos Senafiris para que tenga menos peso que la distancia
            score_final = dist_score + carga_penalty - (senafiris_score / 50) - bonus_balance
            
            scores[conductor] = score_final
        
        # Seleccionar el conductor con menor score (mejor)
        conductor_seleccionado = min(conductores_disponibles, key=lambda c: scores[c])
        distancia_minima = distancias[conductor_seleccionado]
        
        # Debug: mostrar scores para entender la selección
        print(f"[Asignación] Scores: {[(c.nombre, round(scores[c], 2), f'viajes:{c.viajes_hoy}') for c in conductores_disponibles]}")
        print(f"[Asignación] Seleccionado: {conductor_seleccionado.nombre} (score: {round(scores[conductor_seleccionado], 2)})")
        
        # Determinar motivo
        min_viajes_global = min(c.viajes_hoy for c in conductores_disponibles)
        if conductor_seleccionado.viajes_hoy == min_viajes_global and diferencia_viajes > 0:
            motivo = "balanceado"
        else:
            # Verificar si fue por distancia o Senafiris
            otros_scores = [s for c, s in scores.items() if c != conductor_seleccionado]
            if otros_scores:
                score_diferencia = min(abs(scores[conductor_seleccionado] - s) for s in otros_scores)
                if score_diferencia < 0.5:  # Scores muy cercanos
                    motivo = "senafiris"
                else:
                    motivo = "distancia"
            else:
                motivo = "distancia"
        
        # Determinar tarifa
        if self.modo_tarifa_alta:
            tarifa_base = self.tarifa_base_alta
            tarifa_km = self.tarifa_km_alta
        else:
            tarifa_base = self.tarifa_base_normal
            tarifa_km = self.tarifa_km_normal
        
        return {
            "conductor": conductor_seleccionado,
            "distancia": round(distancia_minima, 2),
            "tarifa_base": tarifa_base,
            "tarifa_km": tarifa_km,
            "cliente_estrellas": cliente.estrellas,
            "motivo": motivo
        }

    def priorizar_clientes_para_conductor(self, conductor, lista_clientes):
        """
        Prioriza clientes cuando varios compiten por el mismo conductor.
        
        Reglas de prioridad:
        1. Cliente con más estrellas/frecuencia.
        2. Si empatan, orden de llegada (primera en lista).
        
        Args:
            conductor: conductor disponible
            lista_clientes: lista de clientes esperando
        
        Returns:
            Cliente con mayor prioridad
        """
        if not lista_clientes:
            return None
        
        # Ordenar por estrellas (descendente)
        cliente_priorizado = max(lista_clientes, key=lambda c: (c.estrellas, c.frecuencia))
        
        return cliente_priorizado

    def calcular_tarifa(self, km, cliente_estrellas=1):
        """
        Calcula la tarifa para un viaje.
        
        Args:
            km: kilómetros del viaje
            cliente_estrellas: estrellas del cliente (posible descuento futuro)
        
        Returns:
            Tarifa total en €
        """
        if self.modo_tarifa_alta:
            tarifa = self.tarifa_base_alta + self.tarifa_km_alta * km
        else:
            tarifa = self.tarifa_base_normal + self.tarifa_km_normal * km
        
        return round(tarifa, 2)

    def registrar_viaje_completado(self, conductor, cliente, km, tarifa):
        """
        Registra un viaje completado y actualiza contadores.
        
        Args:
            conductor: conductor que realizó el viaje
            cliente: cliente que solicitó el viaje
            km: kilómetros recorridos
            tarifa: tarifa cobrada
        """
        # Actualizar contadores diarios
        self.viajes_totales_hoy += 1
        self.ganancias_totales_hoy += tarifa
        
        if self.modo_tarifa_alta:
            self.ganancias_tarifa_alta_hoy += tarifa
        
        # Rastrear conductor con más viajes
        viajes_conductor = getattr(conductor, 'viajes_hoy', 0)
        if self.conductor_mas_viajes_hoy is None:
            self.conductor_mas_viajes_hoy = (conductor, viajes_conductor + 1)
        elif viajes_conductor + 1 > self.conductor_mas_viajes_hoy[1]:
            self.conductor_mas_viajes_hoy = (conductor, viajes_conductor + 1)
        
        # Rastrear cliente más frecuente
        if self.cliente_mas_frecuente_hoy is None:
            self.cliente_mas_frecuente_hoy = cliente
        elif cliente.estrellas > self.cliente_mas_frecuente_hoy.estrellas:
            self.cliente_mas_frecuente_hoy = cliente

    def generar_resumen_diario(self, sistema_central=None):
        """
        Genera resumen diario a las 00:00 y resetea contadores.
        
        Args:
            sistema_central: Referencia opcional al SistemaCentral para resetear contadores de taxis
        """
        ahora = datetime.now()
        resumen = {
            "fecha": ahora.strftime("%Y-%m-%d"),
            "viajes_totales": self.viajes_totales_hoy,
            "ganancias_totales": round(self.ganancias_totales_hoy, 2),
            "ganancias_tarifa_alta": round(self.ganancias_tarifa_alta_hoy, 2),
            "conductor_mas_viajes": (
                f"{self.conductor_mas_viajes_hoy[0].nombre} ({self.conductor_mas_viajes_hoy[1]} viajes)"
                if self.conductor_mas_viajes_hoy else "N/A"
            ),
            "cliente_mas_frecuente": (
                f"{self.cliente_mas_frecuente_hoy.nombre} ({self.cliente_mas_frecuente_hoy.estrellas}⭐)"
                if self.cliente_mas_frecuente_hoy else "N/A"
            ),
        }
        
        self.resumen_diarios.append(resumen)
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN DIARIO - {resumen['fecha']}")
        print(f"{'='*60}")
        print(f"Total viajes: {resumen['viajes_totales']}")
        print(f"Ganancias totales: {resumen['ganancias_totales']} €")
        print(f"Ganancias tarifa alta: {resumen['ganancias_tarifa_alta']} €")
        print(f"Conductor más activo: {resumen['conductor_mas_viajes']}")
        print(f"Cliente más frecuente: {resumen['cliente_mas_frecuente']}")
        print(f"{'='*60}\n")
        
        # Resetear contadores diarios
        self.viajes_totales_hoy = 0
        self.ganancias_totales_hoy = 0.0
        self.ganancias_tarifa_alta_hoy = 0.0
        self.conductor_mas_viajes_hoy = None
        self.cliente_mas_frecuente_hoy = None
        
        # Resetear contadores diarios de los taxis si se proporciona sistema_central
        if sistema_central:
            for taxi in sistema_central.taxis:
                taxi.viajes_hoy = 0
                # No resetear tiempo_desde_ultimo_viaje, se actualiza automáticamente
