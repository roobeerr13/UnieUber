"""
Ejemplo de uso del sistema de asignación avanzado con Senafiris,
tarifas dinámicas y resumen diario.
"""

from core.cliente_mejorado import ClienteMejorado
from core.sistema_asignacion import SistemaAsignacion
from datetime import datetime


# Simulación de conductores (usando diccionarios para simplicidad en el ejemplo)
class ConductorSimulado:
    def __init__(self, id_taxi, nombre, posicion=(0, 0)):
        self.id_taxi = id_taxi
        self.nombre = nombre
        self.posicion = posicion
        self.disponible = True
        self.calificacion_media = 4.5
        self.viajes_hoy = 0
        self.tiempo_desde_ultimo_viaje = 3600  # 1 hora


def main():
    print("🚕 SISTEMA DE ASIGNACIÓN AVANZADO - DEMO\n")
    
    # Inicializar sistema
    sistema = SistemaAsignacion()
    
    # Crear clientes
    cliente1 = ClienteMejorado(1, "Juan", frecuencia=15)
    cliente2 = ClienteMejorado(2, "María", frecuencia=5)
    cliente3 = ClienteMejorado(3, "Pedro", frecuencia=2)
    
    cliente1.posicion = (40.4168, -3.7038)  # Madrid centro
    cliente2.posicion = (40.4200, -3.6900)  # Cerca de Atocha
    cliente3.posicion = (40.4500, -3.6700)  # Más al norte
    
    print(f"Clientes creados:")
    print(f"  {cliente1} - Posición: {cliente1.posicion}")
    print(f"  {cliente2} - Posición: {cliente2.posicion}")
    print(f"  {cliente3} - Posición: {cliente3.posicion}\n")
    
    # Crear conductores
    conductor_ana = ConductorSimulado(1, "Ana", (40.4150, -3.7050))
    conductor_luis = ConductorSimulado(2, "Luis", (40.4200, -3.6850))
    conductor_marta = ConductorSimulado(3, "Marta", (40.4450, -3.6650))
    
    conductores = [conductor_ana, conductor_luis, conductor_marta]
    
    print(f"Conductores disponibles:")
    for c in conductores:
        print(f"  {c.nombre} (ID {c.id_taxi}) - Posición: {c.posicion}, "
              f"Calificación: {c.calificacion_media}⭐, Viajes hoy: {c.viajes_hoy}")
    print()
    
    # TEST 1: Seleccionar conductor para cliente (distancia + Senafiris)
    print("=" * 70)
    print("TEST 1: Selección de conductor para cliente")
    print("=" * 70)
    
    resultado = sistema.seleccionar_conductor_para_cliente(cliente1, conductores)
    if resultado:
        print(f"\n✅ Cliente: {cliente1.nombre} ({cliente1.estrellas}⭐)")
        print(f"   Conductor seleccionado: {resultado['conductor'].nombre}")
        print(f"   Distancia: {resultado['distancia']} km")
        print(f"   Tarifa base: {resultado['tarifa_base']} €")
        print(f"   Tarifa/km: {resultado['tarifa_km']} €")
        print(f"   Motivo selección: {resultado['motivo']}\n")
    
    # TEST 2: Prioridad de clientes para un conductor
    print("=" * 70)
    print("TEST 2: Prioridad de clientes para un conductor")
    print("=" * 70)
    
    clientes = [cliente1, cliente2, cliente3]
    cliente_priorizado = sistema.priorizar_clientes_para_conductor(conductor_ana, clientes)
    print(f"\nConductor: {conductor_ana.nombre}")
    print(f"Clientes en espera: {[c.nombre for c in clientes]}")
    print(f"Cliente prioritario: {cliente_priorizado.nombre} ({cliente_priorizado.estrellas}⭐)\n")
    
    # TEST 3: Cálculo de tarifa
    print("=" * 70)
    print("TEST 3: Cálculo de tarifa")
    print("=" * 70)
    
    km_viaje = 5.0
    tarifa_normal = sistema.calcular_tarifa(km_viaje)
    print(f"\nTarifa normal para {km_viaje} km: {tarifa_normal} €")
    
    # Activar tarifa alta manualmente para test
    sistema.modo_tarifa_alta = True
    tarifa_alta = sistema.calcular_tarifa(km_viaje)
    print(f"Tarifa alta para {km_viaje} km: {tarifa_alta} €")
    sistema.modo_tarifa_alta = False
    print()
    
    # TEST 4: Registrar viajes completados
    print("=" * 70)
    print("TEST 4: Registrar viajes completados")
    print("=" * 70)
    
    sistema.registrar_viaje_completado(conductor_ana, cliente1, 5.0, 5.50)
    sistema.registrar_viaje_completado(conductor_luis, cliente2, 3.0, 3.30)
    sistema.registrar_viaje_completado(conductor_ana, cliente3, 4.0, 4.40)
    
    print(f"\nViajes registrados:")
    print(f"  - Ana: 2 viajes, Ganancias: 9.90 €")
    print(f"  - Luis: 1 viaje, Ganancias: 3.30 €")
    print(f"\nContadores diarios:")
    print(f"  - Total viajes hoy: {sistema.viajes_totales_hoy}")
    print(f"  - Ganancias totales: {sistema.ganancias_totales_hoy} €")
    print(f"  - Conductor más activo: {sistema.conductor_mas_viajes_hoy[0].nombre} ({sistema.conductor_mas_viajes_hoy[1]} viajes)")
    print(f"  - Cliente más frecuente: {sistema.cliente_mas_frecuente_hoy.nombre} ({sistema.cliente_mas_frecuente_hoy.estrellas}⭐)")
    print()
    
    # TEST 5: Algoritmo Senafiris
    print("=" * 70)
    print("TEST 5: Puntuación Senafiris de conductores")
    print("=" * 70)
    
    print(f"\nPuntuaciones Senafiris:")
    for conductor in conductores:
        score = sistema.calcular_puntuacion_senafiris(conductor)
        print(f"  - {conductor.nombre}: {score}/100")
    print()
    
    # TEST 6: Incrementar frecuencia de cliente
    print("=" * 70)
    print("TEST 6: Incremento de frecuencia y estrellas")
    print("=" * 70)
    
    print(f"\nAntes: {cliente2}")
    cliente2.incrementar_frecuencia()
    cliente2.incrementar_frecuencia()
    print(f"Después: {cliente2}\n")
    
    # TEST 7: Simulación de cambio de tarifa a las 21:00
    print("=" * 70)
    print("TEST 7: Cambio de tarifa según hora (21:00)")
    print("=" * 70)
    
    print(f"\nHora actual: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Modo tarifa alta: {sistema.modo_tarifa_alta}")
    print(f"Tarifa base normal: {sistema.tarifa_base_normal} €")
    print(f"Tarifa base alta (21:00+): {sistema.tarifa_base_alta} €")
    print(f"Tarifa/km normal: {sistema.tarifa_km_normal} €")
    print(f"Tarifa/km alta (21:00+): {sistema.tarifa_km_alta} €\n")
    
    print("📊 El monitor de hora se ejecuta automáticamente en background.")
    print("   A las 21:00 se activará modo tarifa alta.")
    print("   A las 00:00 se generará el resumen diario.\n")
    
    print("✅ DEMO COMPLETADA")
    
    # Detener monitor antes de salir
    sistema.detener_monitor()


if __name__ == "__main__":
    main()
