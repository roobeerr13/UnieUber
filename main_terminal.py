# main_batch.py
import time
import threading
import sys
import os
from core.sistema import SistemaCentral
from core.data_loader import DataLoader
from core.report_generator import ReportGenerator
from core.taxi import Taxi
from core.cliente import Cliente
from core.cliente_mejorado import ClienteMejorado

def main():
    print("=== UNIETAXI - Modo Batch (Examen) ===")
    
    # 1. Generar/Cargar archivos de entrada
    DataLoader.generar_archivos_ejemplo()
    
    datos_taxis = DataLoader.leer_archivo_taxis("taxis_input.txt")
    if not datos_taxis:
        print("No se pudieron cargar los datos de taxis. Saliendo.")
        return

    lista_clientes = DataLoader.leer_archivo_clientes("clientes_input.txt")
    
    # Instanciar Sistema Central
    # Nota: El sistema central inicia por defecto con algunos taxis demo y clientes simulados.
    # Para el modo batch, podríamos querer limpiar eso o adaptarlo, pero por ahora lo usaremos así
    # y añadiremos los taxis del archivo.
    sistema = SistemaCentral()
    
    # Detener el gestor de clientes simulados automático para tener control total
    sistema.gestor_clientes_simulados.detener_todos()
    
    # Registrar clientes del archivo ("Afiliación")
    print(f"\n[Batch] Afiliando {len(lista_clientes)} clientes del archivo...")
    for c_data in lista_clientes:
        # Registrar en el sistema (usamos ClienteMejorado para persistencia)
        c_mejorado = ClienteMejorado(
            id_cliente=c_data["cedula"],
            nombre=f"{c_data['nombre']} {c_data['apellido']}",
            frecuencia=0
        )
        sistema.clientes_mejorados[c_data["cedula"]] = c_mejorado
        print(f"  - Cliente afiliado: {c_mejorado.nombre} (ID: {c_mejorado.id_cliente})")

    # Ejecución por días
    total_dias = datos_taxis["dias"]
    print(f"\n[Batch] Iniciando simulación de {total_dias} días.")
    
    for dia in range(1, total_dias + 1):
        print(f"\n--- INICIO DÍA {dia} ---")
        sistema.dia_actual = dia
        
        # 2. Registrar/Cargar taxistas del día (Turno)
        taxis_del_dia_data = datos_taxis["registros_por_dia"].get(dia, [])
        nuevos_taxis = []
        
        print(f"[Batch] Registrando {len(taxis_del_dia_data)} taxis para el día {dia}...")
        for t_data in taxis_del_dia_data:
            # Crear instancia de Taxi
            # Usamos la cédula como ID para simplificar
            nuevo_taxi = Taxi(
                id_taxi=int(t_data["cedula"]),
                nombre=f"{t_data['nombre']} {t_data['apellido']}",
                placa=t_data["placa"],
                velocidad_kph=t_data["velocidad"],
                sistema_central=sistema
            )
            # Añadimos atributos extra requeridos para el reporte mensual
            nuevo_taxi.marca = t_data["marca"]
            nuevo_taxi.modelo = t_data["modelo"]
            nuevo_taxi.disponible = t_data["disponible"]
            
            nuevos_taxis.append(nuevo_taxi)
            nuevo_taxi.start()
        
        # Agregamos al sistema (podríamos limpiar los anteriores si fuera rotación estricta)
        sistema.taxis.extend(nuevos_taxis)
        
        # 3. Generar tráfico de clientes (Solicitudes)
        # Usamos los clientes afiliados para generar solicitudes aleatorias este día
        num_solicitudes = 5  # Por ejemplo, 5 solicitudes por día
        
        print(f"[Batch] Generando {num_solicitudes} solicitudes de servicio...")
        
        hilos_clientes = []
        import random
        
        for _ in range(num_solicitudes):
            if not lista_clientes:
                break
                
            c_data = random.choice(lista_clientes)
            cliente_id = c_data["cedula"]
            
            # Crear hilo Cliente para solicitar servicio
            # Usamos coordenadas aleatorias (0-20 km aprox)
            origen = (random.uniform(0, 10), random.uniform(0, 10))
            destino = (random.uniform(0, 10), random.uniform(0, 10))
            
            cliente_thread = Cliente(
                id_cliente=cliente_id,
                sistema_central=sistema,
                origen=origen,
                destino=destino,
                dia=dia
            )
            hilos_clientes.append(cliente_thread)
            cliente_thread.start()
            
            # Pequeña pausa entre solicitudes
            time.sleep(0.5)
            
        # Esperar a que se procesen (simulado)
        # En un sistema real de hilos, esperaríamos a que terminen o usaríamos un tiempo límite
        print("[Batch] Esperando procesamiento de viajes...")
        time.sleep(5) 
        
        # for c in hilos_clientes:
        #     c.join() # Los hilos cliente terminan rápido (al enviar solicitud), lo que tarda es el Taxi
        
        # 4. Generar Reporte Diario (Parte I)
        print(f"[Batch] Generando reporte diario del día {dia}...")
        ReportGenerator.generar_reporte_diario(
            dia=dia,
            ganancia_total=sistema.ganancia_total_diaria,
            servicios_seguimiento=sistema.servicios_seguimiento,
            filepath="reportes_examen.txt" # Un solo archivo acumulativo como pide el ejemplo
        )
        
        # Limpieza fin de día
        sistema.ganancia_total_diaria = 0.0
        sistema.servicios_seguimiento = [] # Resetear los 5 de seguimiento
        
        print(f"--- FIN DÍA {dia} ---")

    # 5. Generar Reporte Mensual (Parte II)
    print("\n[Batch] Generando reporte mensual...")
    ReportGenerator.generar_reporte_mensual(
        taxis=sistema.taxis,
        ganancia_por_taxi=sistema.ganancia_por_taxi,
        filepath="reporte_mensual_examen.txt"
    )

    # 6. Generar Control de Servicios
    print("[Batch] Generando control de servicios histórico...")
    ReportGenerator.generar_control_servicios(
        servicios_control=sistema.servicios_control,
        filepath="control_servicios_examen.txt"
    )

    print("\n=== EJECUCIÓN FINALIZADA ===")
    print("Revise los archivos generados: reportes_examen.txt, reporte_mensual_examen.txt, control_servicios_examen.txt")
    
    # Detener monitor de sistema de asignación
    sistema.sistema_asignacion.detener_monitor()
    
    # Forzar salida (hilos daemon morirán)
    os._exit(0)

if __name__ == "__main__":
    main()
