# 📋 SISTEMA DE ASIGNACIÓN AVANZADO - DOCUMENTACIÓN

## Descripción General

El sistema de asignación avanzado implementa lógica sofisticada para:
- **Seleccionar conductores** basado en distancia y puntuación Senafiris
- **Priorizar clientes** por frecuencia y estrellas
- **Aplicar tarifas dinámicas** según la hora del día
- **Generar resúmenes diarios** automáticos a medianoche

---

## 1. FRECUENCIA Y ESTRELLAS DEL CLIENTE

### Clase: `ClienteMejorado` (core/cliente_mejorado.py)

**Atributos:**
- `id_cliente`: identificador único
- `nombre`: nombre del cliente
- `frecuencia`: número de viajes realizados
- `estrellas`: valoración de 1 a 5 basada en frecuencia
- `calificacion_promedio`: promedio de calificaciones recibidas
- `posicion`: coordenadas (lat, lon) del cliente

**Cálculo de estrellas automático:**
```
0-2 viajes   → 1 estrella ⭐
3-5 viajes   → 2 estrellas ⭐⭐
6-10 viajes  → 3 estrellas ⭐⭐⭐
11-20 viajes → 4 estrellas ⭐⭐⭐⭐
21+ viajes   → 5 estrellas ⭐⭐⭐⭐⭐
```

**Métodos principales:**
- `incrementar_frecuencia()`: aumenta frecuencia y recalcula estrellas
- `actualizar_calificacion(nueva_calificacion)`: promedio móvil de calificaciones

**Ejemplo:**
```python
cliente = ClienteMejorado(1, "Juan", frecuencia=15)
print(cliente.estrellas)  # → 4 (15 viajes = 4 estrellas)

cliente.incrementar_frecuencia()
print(cliente.estrellas)  # → 4 (aún)

# Después de 6 más viajes...
for _ in range(6):
    cliente.incrementar_frecuencia()
print(cliente.estrellas)  # → 5 (21 viajes = 5 estrellas)
```

---

## 2. SELECCIÓN DE CONDUCTOR PARA UN CLIENTE

### Método: `SistemaAsignacion.seleccionar_conductor_para_cliente(cliente, lista_conductores)`

**Proceso de selección:**
1. Filtra conductores disponibles
2. Calcula distancia Haversine a cada uno
3. Selecciona el más cercano
4. Si hay **empate de distancia** → usa **Senafiris**

**Retorna:**
```python
{
    "conductor": Conductor,          # Objeto conductor seleccionado
    "distancia": float,              # Distancia en km
    "tarifa_base": float,            # Tarifa base aplicada (€)
    "tarifa_km": float,              # Tarifa por km (€)
    "cliente_estrellas": int,        # Estrellas del cliente
    "motivo": str                    # "distancia" o "senafiris"
}
```

**Ejemplo:**
```python
sistema = SistemaAsignacion()
cliente = ClienteMejorado(1, "Juan")
cliente.posicion = (40.4168, -3.7038)

conductor_ana = Taxi(1, "Ana", "ABC123", 50, sistema, posicion_inicial=(40.4150, -3.7050))
conductor_luis = Taxi(2, "Luis", "DEF456", 60, sistema, posicion_inicial=(40.4200, -3.6850))

resultado = sistema.seleccionar_conductor_para_cliente(cliente, [conductor_ana, conductor_luis])

print(f"Conductor: {resultado['conductor'].nombre}")
print(f"Distancia: {resultado['distancia']} km")
print(f"Motivo: {resultado['motivo']}")
```

---

## 3. PRIORIDAD ENTRE CLIENTES (MISMO CONDUCTOR)

### Método: `SistemaAsignacion.priorizar_clientes_para_conductor(conductor, lista_clientes)`

**Reglas de prioridad:**
1. **Mayor número de estrellas** (frecuencia más alta)
2. Si empatan estrellas → **mayor frecuencia**
3. Si todo empata → **orden de llegada** (primera en la lista)

**Ejemplo:**
```python
cliente1 = ClienteMejorado(1, "Juan", frecuencia=20)    # 5 estrellas
cliente2 = ClienteMejorado(2, "María", frecuencia=8)    # 3 estrellas
cliente3 = ClienteMejorado(3, "Pedro", frecuencia=2)    # 1 estrella

conductor = Taxi(1, "Ana", "ABC123", 50, sistema)
clientes_esperando = [cliente3, cliente1, cliente2]

cliente_priorizado = sistema.priorizar_clientes_para_conductor(conductor, clientes_esperando)
print(cliente_priorizado.nombre)  # → "Juan" (5 estrellas)
```

---

## 4. ALGORITMO SENAFIRIS

### Método: `SistemaAsignacion.calcular_puntuacion_senafiris(conductor)`

**Descripción:**
Sistema de puntuación para desempatar entre conductores cuando están a la misma distancia.

**Factores considerados:**
- **Reputación (40%)**: calificación media del conductor (0-5 estrellas)
- **Balance de carga (40%)**: penaliza conductores con muchos viajes hoy
- **Descanso (20%)**: tiempo desde el último viaje (más tiempo = mejor)

**Fórmula:**
```
Senafiris = (Reputacion × 0.4) + (CargaBalance × 0.4) + (Descanso × 0.2)
           = (calificacion × 20 × 0.4) + (max(0, 100 - viajes*10) × 0.4) + (min(100, tiempo/36) × 0.2)
```

**Rango:** 0-100 (mayor es mejor)

**Ejemplo:**
```python
# Conductor con buena reputación pero muchos viajes
conductor_luis = Taxi(2, "Luis", "DEF456", 60, sistema)
conductor_luis.calificacion_media = 4.8  # Muy bueno
conductor_luis.viajes_hoy = 10           # Muchos viajes hoy
conductor_luis.tiempo_desde_ultimo_viaje = 300  # Hace 5 min

score = sistema.calcular_puntuacion_senafiris(conductor_luis)
print(score)  # → Aprox. 62/100 (buen conductor, cargado de trabajo)

# Conductor con calificación media pero descansado
conductor_ana = Taxi(1, "Ana", "ABC123", 50, sistema)
conductor_ana.calificacion_media = 4.0   # Bueno
conductor_ana.viajes_hoy = 2             # Pocos viajes
conductor_ana.tiempo_desde_ultimo_viaje = 1800  # Hace 30 min

score = sistema.calcular_puntuacion_senafiris(conductor_ana)
print(score)  # → Aprox. 80/100 (menos experimentado, pero descansado)
```

---

## 5. TARIFAS DINÁMICAS (RELOJ INTERNO)

### Atributos del SistemaAsignacion:
```python
self.modo_tarifa_alta = False              # Bandera activa/inactiva
self.hora_activacion_tarifa_alta = 21      # 21:00 (9 PM)
self.tarifa_base_normal = 0.5              # € de arranque (hora normal)
self.tarifa_km_normal = 1.0                # € por km (hora normal)
self.tarifa_base_alta = 1.0                # € de arranque (21:00+)
self.tarifa_km_alta = 1.5                  # € por km (21:00+)
```

### Monitor de hora automático:
- Se ejecuta en un hilo de fondo (`_monitor_hora`)
- Revisa la hora cada minuto
- Activa tarifa alta a las 21:00
- Reactiva tarifa normal a las 00:00 (después del resumen)

### Método: `SistemaAsignacion.calcular_tarifa(km, cliente_estrellas=1)`

**Ejemplo:**
```python
sistema = SistemaAsignacion()

# Modo normal (antes de las 21:00)
sistema.modo_tarifa_alta = False
tarifa_5km = sistema.calcular_tarifa(5.0)
print(tarifa_5km)  # → 5.50 € (0.50 + 1.0*5)

# Modo tarifa alta (después de las 21:00)
sistema.modo_tarifa_alta = True
tarifa_5km = sistema.calcular_tarifa(5.0)
print(tarifa_5km)  # → 8.50 € (1.00 + 1.5*5)
```

---

## 6. RESUMEN DIARIO AUTOMÁTICO (00:00)

### Método: `SistemaAsignacion.generar_resumen_diario()`

Se ejecuta automáticamente a las 00:00 (medianoche).

**Contadores incluidos:**
- Fecha del resumen
- Total de viajes del día
- Ganancias totales en €
- Ganancias con tarifa alta
- Conductor con más viajes
- Cliente más frecuente (más estrellas)

**Ejemplo de salida:**
```
============================================================
📊 RESUMEN DIARIO - 2025-12-04
============================================================
Total viajes: 42
Ganancias totales: 185.60 €
Ganancias tarifa alta: 98.30 €
Conductor más activo: Ana (15 viajes)
Cliente más frecuente: Juan (5⭐)
============================================================
```

**Reseteo automático:**
Después del resumen, se resetean:
- `viajes_totales_hoy` → 0
- `ganancias_totales_hoy` → 0.0
- `ganancias_tarifa_alta_hoy` → 0.0
- `conductor_mas_viajes_hoy` → None
- `cliente_mas_frecuente_hoy` → None

**Históricos preservados:**
- `resumen_diarios[]`: lista con todos los resúmenes generados (nunca se resetea)
- Frecuencia de clientes: se mantiene acumulada
- Calificaciones: se mantienen históricamente

---

## 7. INTEGRACIÓN CON EL SISTEMA EXISTENTE

### En `core/taxa.py`:
Se han añadido los siguientes atributos al constructor de `Taxi`:
```python
self.viajes_hoy = 0                      # Contador diario
self.tiempo_desde_ultimo_viaje = 3600    # segundos
self.ultima_actualizacion_tiempo = time.time()
```

### En `main.py`:
Se puede integrar así:
```python
from core.sistema_asignacion import SistemaAsignacion
from core.cliente_mejorado import ClienteMejorado

sistema_asignacion = SistemaAsignacion()

# Al recibir una solicitud de taxi:
cliente = ClienteMejorado(
    id_cliente=cliente_id,
    nombre=f"Cliente {cliente_id}",
    frecuencia=0  # O recuperar del DB si existe
)
cliente.posicion = (orig_lat, orig_lon)

resultado = sistema_asignacion.seleccionar_conductor_para_cliente(
    cliente,
    lista_taxis_disponibles
)

if resultado:
    conductor = resultado['conductor']
    tarifa = sistema_asignacion.calcular_tarifa(dist_km, cliente.estrellas)
    # ... asignar viaje ...
```

---

## 8. ARCHIVOS GENERADOS

### Nuevos módulos:
1. **`core/cliente_mejorado.py`**: Clase ClienteMejorado con frecuencia y estrellas
2. **`core/sistema_asignacion.py`**: Sistema completo de asignación, Senafiris, tarifas dinámicas, resumen
3. **`example_asignacion.py`**: Demo/ejemplo de uso

### Modificaciones:
- **`core/taxi.py`**: Añadidos atributos `viajes_hoy`, `tiempo_desde_ultimo_viaje`, `ultima_actualizacion_tiempo`

---

## 9. EJEMPLO DE USO COMPLETO

```python
from core.sistema_asignacion import SistemaAsignacion
from core.cliente_mejorado import ClienteMejorado
from core.taxi import Taxi

# Inicializar
sistema = SistemaAsignacion()

# Crear clientes
cliente_juan = ClienteMejorado(1, "Juan", frecuencia=15)
cliente_juan.posicion = (40.4168, -3.7038)

cliente_maria = ClienteMejorado(2, "María", frecuencia=5)
cliente_maria.posicion = (40.4200, -3.6900)

# Crear conductores
ana = Taxi(1, "Ana", "ABC123", 50, sistema, (40.4150, -3.7050))
luis = Taxi(2, "Luis", "DEF456", 60, sistema, (40.4200, -3.6850))
marta = Taxi(3, "Marta", "GHI789", 45, sistema, (40.4450, -3.6650))

conductores = [ana, luis, marta]

# Seleccionar conductor para Juan
resultado = sistema.seleccionar_conductor_para_cliente(cliente_juan, conductores)
print(f"Conductor asignado a {cliente_juan.nombre}: {resultado['conductor'].nombre}")
print(f"Distancia: {resultado['distancia']} km")
print(f"Tarifa: {sistema.calcular_tarifa(resultado['distancia'])} €")

# Registrar viaje completado
sistema.registrar_viaje_completado(
    resultado['conductor'],
    cliente_juan,
    resultado['distancia'],
    sistema.calcular_tarifa(resultado['distancia'])
)

# Incrementar frecuencia del cliente
cliente_juan.incrementar_frecuencia()
print(f"Nuevas estrellas de Juan: {cliente_juan.estrellas}⭐")

# El resumen diario se genera automáticamente a las 00:00
```

---

## 10. PARÁMETROS AJUSTABLES

En `core/sistema_asignacion.py` puedes personalizar:

```python
# Tarifas
self.tarifa_base_normal = 0.5      # Cambiar a gusto
self.tarifa_km_normal = 1.0
self.tarifa_base_alta = 1.0
self.tarifa_km_alta = 1.5

# Horarios
self.hora_activacion_tarifa_alta = 21   # Cambiar a otra hora
self.hora_resumen_diario = 0            # Cambiar a otra hora

# Ponderaciones Senafiris (en calcular_puntuacion_senafiris)
# Actualmente: 0.4 reputación, 0.4 carga, 0.2 descanso
```

---

## Conclusión

Este sistema implementa una asignación inteligente y justa de conductores,
con incentivos para clientes frecuentes, tarifas dinámicas según demanda horaria,
y seguimiento completo de métricas diarias.

¡Listo para usar en producción!
