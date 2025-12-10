# app.py
from flask import Flask, render_template, request, redirect, url_for
from core.sistema import SistemaCentral
from core.cliente import Cliente
import requests
import math

app = Flask(__name__)

# Instancia única del sistema
sistema = SistemaCentral()


def geocode_address(address: str):
    if not address:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "UnieUber-student-project/1.0 (tu-email@ejemplo.com)"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()
        if not data:
            return None, None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    except Exception as e:
        print("Error geocodificando:", e)
        return None, None


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Distancia aproximada en km entre dos puntos lat/lon.
    """
    if None in (lat1, lon1, lat2, lon2):
        return None

    R = 6371.0  # radio de la tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lon2 - lon1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/solicitar-taxi", methods=["GET", "POST"])
def solicitar_taxi():
    direccion_origen = direccion_destino = None
    orig_lat = orig_lon = dest_lat = dest_lon = None
    dist_km = precio = None
    taxi_info = None
    cliente_info = None

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", "cliente-web")

        # Origen
        dir_o = request.form.get("direccion_origen", "").strip()
        cp_o = request.form.get("cp_origen", "").strip()
        ciudad_o = request.form.get("ciudad_origen", "").strip()
        direccion_origen = ", ".join([x for x in [dir_o, cp_o, ciudad_o] if x]) or None

        # Destino
        dir_d = request.form.get("direccion_destino", "").strip()
        cp_d = request.form.get("cp_destino", "").strip()
        ciudad_d = request.form.get("ciudad_destino", "").strip()
        direccion_destino = ", ".join([x for x in [dir_d, cp_d, ciudad_d] if x]) or None

        # Geocodificación (lat/lon)
        if direccion_origen and direccion_destino:
            orig_lat, orig_lon = geocode_address(direccion_origen)
            dest_lat, dest_lon = geocode_address(direccion_destino)

            # Si Nominatim no devuelve resultados, usar las coordenadas
            # deterministas del sistema (convertir_direccion_a_coordenadas)
            if orig_lat is None or orig_lon is None:
                ox, oy = sistema.convertir_direccion_a_coordenadas(direccion_origen)
                orig_lat, orig_lon = ox, oy
            if dest_lat is None or dest_lon is None:
                dx_c, dy_c = sistema.convertir_direccion_a_coordenadas(direccion_destino)
                dest_lat, dest_lon = dx_c, dy_c

            dist_km = haversine_km(orig_lat, orig_lon, dest_lat, dest_lon)
            if dist_km is not None:
                dist_km = round(dist_km, 2)
                # Usar tarifas dinámicas del sistema de asignación
                precio = sistema.sistema_asignacion.calcular_tarifa(dist_km)

        # Obtener información del cliente mejorado
        cliente_mejorado = sistema._obtener_cliente_mejorado(cliente_id)
        cliente_info = {
            "id": cliente_mejorado.id_cliente,
            "nombre": cliente_mejorado.nombre,
            "frecuencia": cliente_mejorado.frecuencia,
            "estrellas": cliente_mejorado.estrellas
        }

        # Lanzamos el hilo Cliente (para la simulación interna)
        cliente = Cliente(
            id_cliente=cliente_id,
            sistema_central=sistema,
            direccion_origen=direccion_origen,
            direccion_destino=direccion_destino,
            dia=sistema.dia_actual
        )
        cliente.start()
        
        # Esperar un momento para que se procese la solicitud y obtener info del taxi
        import time
        time.sleep(0.3)  # Pequeña espera para que se procese la asignación
        
        # Buscar el último servicio en servicios_control para obtener info del taxi asignado
        # También buscar en servicios_seguimiento que se actualiza más rápido
        servicios_recientes = sistema.servicios_seguimiento[-1:] if sistema.servicios_seguimiento else []
        if not servicios_recientes and sistema.servicios_control:
            servicios_recientes = sistema.servicios_control[-1:]
        
        for servicio in servicios_recientes:
            if servicio.get("aceptado") and servicio.get("id_taxi"):
                taxi_id = servicio["id_taxi"]
                # Buscar el taxi en la lista
                for taxi in sistema.taxis:
                    if taxi.id_taxi == taxi_id:
                        taxi_info = {
                            "id": taxi.id_taxi,
                            "nombre": taxi.nombre,
                            "placa": taxi.placa,
                            "calificacion": round(taxi.calificacion_media, 1),
                            "viajes_hoy": taxi.viajes_hoy,
                            "motivo": servicio.get("motivo_seleccion", "distancia")
                        }
                        break
                if taxi_info:
                    break

    return render_template(
        "solicitar_taxi.html",
        direccion_origen=direccion_origen,
        direccion_destino=direccion_destino,
        orig_lat=orig_lat,
        orig_lon=orig_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        dist_km=dist_km,
        precio=precio,
        taxi_info=taxi_info,
        cliente_info=cliente_info,
        modo_tarifa_alta=sistema.sistema_asignacion.modo_tarifa_alta,
    )


@app.route("/reportes")
def reportes():
    diarios, mensuales = sistema.obtener_reportes()
    # Agregar información del sistema de asignación
    resumenes_diarios = sistema.sistema_asignacion.resumen_diarios
    modo_tarifa_alta = sistema.sistema_asignacion.modo_tarifa_alta
    # Calcular hora virtual para mostrar en reportes
    from datetime import datetime, timedelta
    start_time = datetime.now()
    virtual_speed = 30
    virtual_elapsed = (datetime.now() - start_time).total_seconds() * virtual_speed
    virtual_time = start_time + timedelta(seconds=virtual_elapsed)
    return render_template(
        "reportes.html", 
        diarios=diarios, 
        mensuales=mensuales,
        resumenes_diarios=resumenes_diarios,
        modo_tarifa_alta=modo_tarifa_alta,
        hora_virtual=virtual_time.strftime("%H:%M:%S")
    )


if __name__ == "__main__":
    app.run(debug=True)
