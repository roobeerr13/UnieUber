import os

class ReportGenerator:
    """
    Clase encargada de generar los reportes de salida en archivos de texto
    con el formato específico requerido.
    """
    
    @staticmethod
    def generar_reporte_diario(dia, ganancia_total, servicios_seguimiento, filepath="reporte_diario.txt"):
        """
        Parte I (Diaria)
        Muestra la información de los 5 servicios que se siguieron diariamente.
        """
        mode = 'a' if os.path.exists(filepath) else 'w'
        
        with open(filepath, mode, encoding='utf-8') as f:
            f.write(f"Día {dia}\n")
            f.write(f"Ganancia total: {ganancia_total:.2f}\n")
            
            # Formato requerido:
            # 1- idTaxi: idt IdCliente: idc Origen: (x1,y1) Destino (x2,y2) Km: km_ Costo: costo_ Calificación c_
            
            for i, servicio in enumerate(servicios_seguimiento, 1):
                linea = (
                    f"{i}- idTaxi: {servicio['id_taxi']} "
                    f"IdCliente: {servicio['id_cliente']} "
                    f"Origen: {servicio['origen']} "
                    f"Destino: {servicio['destino']} "
                    f"Km: {servicio['km']:.2f} "
                    f"Costo: {servicio['costo']:.2f} "
                    f"Calificación {servicio['calificacion']}\n"
                )
                f.write(linea)
            f.write("\n")
            
    @staticmethod
    def generar_reporte_mensual(taxis, ganancia_por_taxi, filepath="reporte_mensual.txt"):
        """
        Parte II (Mensual)
        Detalles de ganancias por taxista.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("REPORTE MENSUAL DE GANANCIAS\n")
            f.write("============================\n\n")
            
            for taxi in taxis:
                total_generado = ganancia_por_taxi.get(taxi.id_taxi, 0.0)
                descuento = total_generado * 0.20  # 20% para la empresa
                ganancia_final = total_generado - descuento
                
                f.write(f"IDTaxista: {taxi.id_taxi} :: Nombre: {taxi.nombre}\n")
                f.write(f"Placa: {taxi.placa} :: Marca: {getattr(taxi, 'marca', 'N/A')} :: Modelo: {getattr(taxi, 'modelo', 'N/A')}\n")
                f.write(f"Total Generado: {total_generado:.2f} :: Importe Mensual: {descuento:.2f} :: Ganancia del taxista: {ganancia_final:.2f}\n")
                f.write("-" * 50 + "\n")

    @staticmethod
    def generar_control_servicios(servicios_control, filepath="control_servicios.txt"):
        """
        Control Servicios (Salida)
        Contiene todas las solicitudes realizadas.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("CONTROL DE SERVICIOS (HISTÓRICO)\n")
            f.write("================================\n\n")
            
            for s in servicios_control:
                estado = "ACEPTADA" if s['aceptado'] else "RECHAZADA"
                calif = s['calificacion'] if s['aceptado'] else "N/A"
                
                f.write(f"Día: {s['dia']} | Estado: {estado}\n")
                f.write(f"Taxi: {s['id_taxi']} | Cliente: {s['id_cliente']}\n")
                f.write(f"Origen: {s['origen']} -> Destino: {s['destino']}\n")
                f.write(f"Distancia: {s['km']:.2f} km | Costo: {s['costo']:.2f}\n")
                f.write(f"Calificación: {calif}\n")
                f.write("-" * 40 + "\n")
