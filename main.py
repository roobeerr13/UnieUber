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
        try:
            x_origen = float(request.form.get("x_origen", 0))
            y_origen = float(request.form.get("y_origen", 0))
            x_dest = float(request.form.get("x_dest", 5))
            y_dest = float(request.form.get("y_dest", 5))
        except ValueError:
            x_origen, y_origen, x_dest, y_dest = 0, 0, 5, 5

        cliente = Cliente(
            id_cliente=cliente_id,
            sistema_central=sistema,
            origen=(x_origen, y_origen),
            destino=(x_dest, y_dest),
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
