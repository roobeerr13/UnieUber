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
    """
    Usa Nominatim (OpenStreetMap) para obtener lat/lon de una dirección.
    Gratis, pero hay que usar un User-Agent identificable.
    """
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

            dist_km = haversine_km(orig_lat, orig_lon, dest_lat, dest_lon)
            if dist_km is not None:
                dist_km = round(dist_km, 2)
                precio = round(0.5 + 1.0 * dist_km, 2)

        # Lanzamos el hilo Cliente (para la simulación interna)
        cliente = Cliente(
            id_cliente=cliente_id,
            sistema_central=sistema,
            direccion_origen=direccion_origen,
            direccion_destino=direccion_destino,
            dia=sistema.dia_actual
        )
        cliente.start()

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
    )


@app.route("/reportes")
def reportes():
    diarios, mensuales = sistema.obtener_reportes()
    return render_template("reportes.html", diarios=diarios, mensuales=mensuales)


if __name__ == "__main__":
    app.run(debug=True)
