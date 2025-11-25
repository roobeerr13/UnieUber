# app.py
from flask import Flask, render_template, request, redirect, url_for
from core.sistema import SistemaCentral
from core.cliente import Cliente

app = Flask(__name__)

# Instancia única del sistema
sistema = SistemaCentral()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/solicitar-taxi", methods=["GET", "POST"])
def solicitar_taxi():
    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", "cliente-web")

        # Origen
        dir_o = request.form.get("direccion_origen", "").strip()
        cp_o = request.form.get("cp_origen", "").strip()
        ciudad_o = request.form.get("ciudad_origen", "").strip()
        direccion_origen = ", ".join(
            [x for x in [dir_o, cp_o, ciudad_o] if x]
        ) or None

        # Destino
        dir_d = request.form.get("direccion_destino", "").strip()
        cp_d = request.form.get("cp_destino", "").strip()
        ciudad_d = request.form.get("ciudad_destino", "").strip()
        direccion_destino = ", ".join(
            [x for x in [dir_d, cp_d, ciudad_d] if x]
        ) or None

        cliente = Cliente(
            id_cliente=cliente_id,
            sistema_central=sistema,
            direccion_origen=direccion_origen,
            direccion_destino=direccion_destino,
            dia=sistema.dia_actual
        )
        cliente.start()

        return redirect(url_for("index"))

    return render_template("solicitar_taxi.html")



@app.route("/reportes")
def reportes():
    diarios, mensuales = sistema.obtener_reportes()
    return render_template("reportes.html", diarios=diarios, mensuales=mensuales)


if __name__ == "__main__":
    app.run(debug=True)
