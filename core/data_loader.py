import os
import random

class DataLoader:
    """
    Clase encargada de cargar los datos de entrada desde archivos de texto
    con el formato específico requerido para el examen.
    """

    @staticmethod
    def leer_archivo_taxis(filepath):
        """
        Lee el archivo de registro de taxistas.
        Formato esperado:
        d (días)
        Mi (cantidad de taxistas para el día i)
        Cedula, nombre, apellido, placa, marca, modelo, velocidad, disponibilidad
        ...
        """
        if not os.path.exists(filepath):
            print(f"[DataLoader] Archivo {filepath} no encontrado.")
            return None

        datos = {
            "dias": 0,
            "registros_por_dia": {}  # dia -> lista de datos de taxis
        }

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                
                if not lines:
                    return None

                dias = int(lines[0])
                datos["dias"] = dias
                
                idx = 1
                for d in range(1, dias + 1):
                    if idx >= len(lines):
                        break
                    
                    try:
                        num_taxis = int(lines[idx])
                        idx += 1
                        
                        taxis_dia = []
                        for _ in range(num_taxis):
                            if idx >= len(lines):
                                break
                            
                            linea_taxi = lines[idx]
                            partes = [p.strip() for p in linea_taxi.split(',')]
                            
                            # Validar que tengamos todos los campos
                            if len(partes) >= 8:
                                # Parsear disponibilidad (0 o 1)
                                disp = int(partes[7]) == 1
                                
                                taxi_data = {
                                    "cedula": partes[0],
                                    "nombre": partes[1],
                                    "apellido": partes[2],
                                    "placa": partes[3],
                                    "marca": partes[4],
                                    "modelo": partes[5],
                                    "velocidad": int(partes[6]),
                                    "disponible": disp
                                }
                                taxis_dia.append(taxi_data)
                            
                            idx += 1
                        
                        datos["registros_por_dia"][d] = taxis_dia
                        
                    except ValueError as e:
                        print(f"[DataLoader] Error parseando datos del día {d}: {e}")
                        continue

            return datos

        except Exception as e:
            print(f"[DataLoader] Error leyendo archivo de taxis: {e}")
            return None

    @staticmethod
    def leer_archivo_clientes(filepath):
        """
        Lee el archivo de clientes afiliados.
        Formato esperado:
        Cedula, nombre, apellido, NroTarjetaCredito
        """
        if not os.path.exists(filepath):
            print(f"[DataLoader] Archivo {filepath} no encontrado.")
            return []

        clientes = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    partes = [p.strip() for p in line.split(',')]
                    if len(partes) >= 4:
                        cliente_data = {
                            "cedula": partes[0],
                            "nombre": partes[1],
                            "apellido": partes[2],
                            "tarjeta": partes[3]
                        }
                        clientes.append(cliente_data)
            return clientes
            
        except Exception as e:
            print(f"[DataLoader] Error leyendo archivo de clientes: {e}")
            return []

    @staticmethod
    def generar_archivos_ejemplo():
        """
        Genera archivos de ejemplo si no existen para poder probar el sistema.
        """
        if not os.path.exists("taxis_input.txt"):
            with open("taxis_input.txt", "w", encoding='utf-8') as f:
                f.write("2\n") # 2 días
                
                # Día 1: 3 taxis
                f.write("3\n") 
                f.write("1001, Juan, Perez, ABC1234, Toyota, Corolla, 60, 1\n")
                f.write("1002, Ana, Lopez, XYZ9876, Ford, Fiesta, 55, 1\n")
                f.write("1003, Carlos, Ruiz, DEF4567, Chevrolet, Spark, 50, 0\n")
                
                # Día 2: 2 taxis (pueden ser los mismos o nuevos)
                f.write("2\n")
                f.write("1001, Juan, Perez, ABC1234, Toyota, Corolla, 60, 1\n")
                f.write("1004, Marta, Diaz, GHI1122, Nissan, Sentra, 65, 1\n")
                
            print("[DataLoader] Generado archivo ejemplo 'taxis_input.txt'")

        if not os.path.exists("clientes_input.txt"):
            with open("clientes_input.txt", "w", encoding='utf-8') as f:
                f.write("5001, Pedro, Gomez, 123456789\n")
                f.write("5002, Lucia, Fernandez, 987654321\n")
                f.write("5003, Roberto, Silva, 456123789\n")
            print("[DataLoader] Generado archivo ejemplo 'clientes_input.txt'")
