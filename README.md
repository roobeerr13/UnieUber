# Proyecto Sincronización y Comunicación entre Procesos: UNIETAXI

**Fecha de Entrega:** 12 de diciembre de 2025  
**Lenguaje:** Python  
**Materia:** Sistemas Operativos / Programación Concurrente

---

## 1. Informe Técnico

### 1.1 Descripción del Problema
El objetivo del proyecto es simular el sistema de gestión de taxis "UNIETAXI", donde múltiples entidades concurrentes (Clientes y Taxistas) interactúan para solicitar y prestar servicios de transporte. El desafío principal radica en la gestión correcta de los recursos compartidos y la sincronización de procesos para evitar condiciones de carrera, bloqueos y asegurar la integridad de los datos financieros y estadísticos.

### 1.2 Abordaje de la Solución
Para modelar la concurrencia requerida ("adaptarse a la realidad"), se ha implementado un sistema basado en **Hilos (Threads)**:

*   **Taxistas:** Cada taxi se representa como un hilo independiente (`threading.Thread`) que hereda de la clase `Taxi`. Estos hilos tienen un ciclo de vida continuo donde esperan asignaciones, realizan viajes simulados y vuelven a estar disponibles.
*   **Clientes:** Cada solicitud de cliente se maneja en un hilo independiente (`threading.Thread`) que nace, solicita el servicio, espera la respuesta y muere al completar la solicitud.
*   **Sistema Central:** Actúa como el orquestador y recurso compartido principal, gestionando las listas de taxis, servicios y estadísticas.

### 1.3 Primitivas de Sincronización Utilizadas
Para garantizar la corrección del sistema, se han empleado las siguientes herramientas de la librería `threading` de Python:

1.  **Locks (Cerrojos / Mutex):**
    *   `mutex_match`: Garantiza **Exclusión Mutua** en el proceso de asignación de taxis. Evita que dos solicitudes simultáneas se asignen al mismo taxi disponible.
    *   `mutex_servicio`: Protege la sección crítica donde se actualizan los datos financieros del taxi ("ganancia_acumulada"), las estadísticas del día y se modifica la lista de servicios. Es crucial para evitar pérdidas de datos en los contadores de dinero.
    *   `mutex_findeldia`: Protege el contador global de `servicios_activos`, asegurando que el sistema sepa con precisión cuándo han terminado todos los servicios del día.
    *   `mutex_control_servicios`: Protege la escritura concurrente en `servicios_control`, que almacena el histórico de todas las solicitudes.

2.  **Eventos (`threading.Event`):**
    *   `_viaje_asignado_event` (en clase `Taxi`): Permite una **Espera Pasiva** eficiente. El hilo del taxi se duerme (`wait()`) hasta que el sistema central le asigna un viaje y "activa" el evento (`set()`). Esto evita el "busywait" (espera activa) y ahorra CPU.

3.  **Semáforos (`threading.Semaphore`):**
    *   `no_hay_servicios_activos`: Se utiliza para coordinar el cierre del día. El hilo principal puede esperar en este semáforo hasta que el contador de servicios activos llegue a cero.

### 1.4 Recursos Críticos
Los recursos compartidos que requieren protección (Secciones Críticas) son:
*   La lista de taxis disponibles (`self.taxis`).
*   Los contadores financieros (`self.ganancia_total_diaria`, `self.ganancia_por_taxi`).
*   Las listas de reportes (`self.servicios_control`, `self.servicios_seguimiento`).
*   El contador de servicios activos (`self.servicios_activos`).

---

## 2. Especificación de Módulos (Entradas y Salidas)

El sistema se ha diseñado de forma modular. A continuación se detallan los módulos principales y sus interfaces:

### 2.1 Módulo `core/data_loader.py` (Carga de Datos)
*   **Entrada:**
    *   Archivo `taxis_input.txt`: Contiene el número de días `d`, y para cada día `di`, la cantidad `Mi` de taxis y sus detalles (Cédula, nombre, placa, etc.).
    *   Archivo `clientes_input.txt`: Lista de clientes afiliados (Cédula, nombre, tarjeta).
*   **Salida:**
    *   Estructuras de datos (diccionarios y listas) listas para ser consumidas por el `SistemaCentral`.

### 2.2 Módulo `core/sistema.py` (Lógica Central)
*   **Entrada:** Solicitudes de servicio (Origen, Destino, ID Cliente) provenientes de hilos `Cliente`.
*   **Procesamiento:** Asignación de taxis, cálculo de tarifas, gestión de hilos.
*   **Salida:** Actualización de estados de `Taxi` y generación de datos para reportes.

### 2.3 Módulo `core/report_generator.py` (Reportes)
*   **Entrada:** Datos acumulados en `SistemaCentral` (ganancias, listas de servicios).
*   **Salidas (Archivos Generados):**
    *   **Reporte Diario (Parte I):** Archivo `reportes_examen.txt`. Muestra ganancia del día y detalle de 5 servicios de seguimiento.
    *   **Reporte Mensual (Parte II):** Archivo `reporte_mensual_examen.txt`. Muestra desglose de ganancias por taxista, deducciones (20%) y neto a pagar.
    *   **Control de Servicios:** Archivo `control_servicios_examen.txt`. Histórico completo de todas las solicitudes procesadas.

### 2.4 Módulo `main_batch.py` (Ejecución)
*   Script principal que orquesta la carga de datos, inicia el sistema central, lanza los hilos de taxistas y clientes según la configuración de entrada, y finalmente invoca la generación de reportes.

---

## 3. Casos de Prueba

El sistema incluye generación automática de casos de prueba a través de `main_batch.py` y `data_loader.py`:

1.  **Caso Normal:** Ejecución estándar con múltiples taxis y clientes. Se verifica que todos los clientes sean atendidos si hay capacidad.
2.  **Caso de Concurrencia:** Múltiples clientes solicitando servicio simultáneamente. El sistema debe asignar taxis diferentes a cada uno sin errores. (Verificable en `control_servicios_examen.txt`: no deben haber taxis duplicados en el mismo instante).
3.  **Caso Sin Disponibilidad:** Si hay más clientes que taxis, el sistema debe rechazar o poner en espera (según implementación) las solicitudes excedentes, o asignarlas cuando se liberen. En esta versión, si no hay taxis, se rechaza y registra.
4.  **Cálculo Financiero:** Se verifica que el "Importe Mensual" (20%) y "Ganancia del Taxista" (80%) sumen el "Total Generado" en el reporte mensual.

---

## 4. Instrucciones de Ejecución

1.  Asegúrese de tener Python instalado (3.8+ recomendado).
2.  Ejecute el script de modo "examen" (Batch):
    ```bash
    python main_batch.py
    ```
3.  El sistema generará automáticamente archivos de entrada de ejemplo (`taxis_input.txt`, `clientes_input.txt`) si no existen.
4.  Al finalizar, revise los archivos de salida generados en el mismo directorio:
    *   `reportes_examen.txt`
    *   `reporte_mensual_examen.txt`
    *   `control_servicios_examen.txt`

*(Nota: También existe una versión Web con Flask en `main.py`, pero para efectos de la entrega del examen y generación de archivos de texto específicos, se debe usar `main_batch.py`)*