"""
Sistema de clientes simulados que realizan solicitudes automáticas.
"""
import threading
import time
import random
from .cliente import Cliente
from .cliente_mejorado import ClienteMejorado


class ClienteSimulado:
    """
    Representa un cliente simulado que realiza solicitudes periódicas.
    """
    def __init__(self, id_cliente, nombre, sistema_central, intervalo_min=10, intervalo_max=30):
        self.id_cliente = id_cliente
        self.nombre = nombre
        self.sistema_central = sistema_central
        self.intervalo_min = intervalo_min  # segundos reales
        self.intervalo_max = intervalo_max  # segundos reales
        self.activo = False
        self.hilo = None
        
    def iniciar(self):
        """Inicia el cliente simulado."""
        if not self.activo:
            self.activo = True
            self.hilo = threading.Thread(target=self._loop_solicitudes, daemon=True)
            self.hilo.start()
            print(f"[ClienteSimulado] {self.nombre} ({self.id_cliente}) iniciado")
    
    def detener(self):
        """Detiene el cliente simulado."""
        self.activo = False
    
    def _loop_solicitudes(self):
        """Loop principal que realiza solicitudes periódicas."""
        while self.activo:
            # Esperar un intervalo aleatorio
            intervalo = random.uniform(self.intervalo_min, self.intervalo_max)
            time.sleep(intervalo)
            
            if not self.activo:
                break
            
            # Generar direcciones aleatorias en Madrid
            direcciones_madrid = [
                ("Calle Gran Vía", "28013", "Madrid"),
                ("Plaza Mayor", "28012", "Madrid"),
                ("Avenida de América", "28028", "Madrid"),
                ("Calle Serrano", "28001", "Madrid"),
                ("Paseo de la Castellana", "28046", "Madrid"),
                ("Calle Alcalá", "28014", "Madrid"),
                ("Plaza de España", "28008", "Madrid"),
                ("Calle Princesa", "28008", "Madrid"),
                ("Avenida de la Paz", "28036", "Madrid"),
                ("Calle Orense", "28020", "Madrid"),
            ]
            
            origen = random.choice(direcciones_madrid)
            destino = random.choice([d for d in direcciones_madrid if d != origen])
            
            direccion_origen = ", ".join(origen)
            direccion_destino = ", ".join(destino)
            
            # Crear y lanzar cliente
            cliente = Cliente(
                id_cliente=self.id_cliente,
                sistema_central=self.sistema_central,
                direccion_origen=direccion_origen,
                direccion_destino=direccion_destino,
                dia=self.sistema_central.dia_actual
            )
            cliente.start()
            
            print(f"[ClienteSimulado] {self.nombre} solicita taxi: {direccion_origen} → {direccion_destino}")


class GestorClientesSimulados:
    """
    Gestiona múltiples clientes simulados.
    """
    def __init__(self, sistema_central):
        self.sistema_central = sistema_central
        self.clientes_simulados: list[ClienteSimulado] = []
        self.activo = False
    
    def crear_clientes_simulados(self, cantidad=9):
        """
        Crea clientes simulados con nombres y características diferentes.
        """
        nombres = [
            ("cliente-1", "María García"),
            ("cliente-2", "Carlos López"),
            ("cliente-3", "Ana Martínez"),
            ("cliente-4", "David Rodríguez"),
            ("cliente-5", "Laura Sánchez"),
            ("cliente-6", "Javier Fernández"),
            ("cliente-7", "Sofía Pérez"),
            ("cliente-8", "Miguel González"),
            ("cliente-9", "Elena Torres"),
        ]
        
        for i, (id_cliente, nombre) in enumerate(nombres[:cantidad]):
            # Variar intervalos para que no todos soliciten al mismo tiempo
            intervalo_min = 15 + i * 2  # Entre 15 y 33 segundos
            intervalo_max = 30 + i * 3  # Entre 30 y 57 segundos
            
            cliente = ClienteSimulado(
                id_cliente=id_cliente,
                nombre=nombre,
                sistema_central=self.sistema_central,
                intervalo_min=intervalo_min,
                intervalo_max=intervalo_max
            )
            self.clientes_simulados.append(cliente)
        
        print(f"[GestorClientesSimulados] Creados {len(self.clientes_simulados)} clientes simulados")
    
    def iniciar_todos(self):
        """Inicia todos los clientes simulados."""
        if not self.activo:
            self.activo = True
            for cliente in self.clientes_simulados:
                cliente.iniciar()
            print(f"[GestorClientesSimulados] Todos los clientes simulados iniciados")
    
    def detener_todos(self):
        """Detiene todos los clientes simulados."""
        self.activo = False
        for cliente in self.clientes_simulados:
            cliente.detener()
        print(f"[GestorClientesSimulados] Todos los clientes simulados detenidos")

