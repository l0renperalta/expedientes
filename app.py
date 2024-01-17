from flask import Flask, render_template,send_file
from flask_socketio import SocketIO
import sys
import os
from werkzeug.utils import url_quote  # Importa url_quote desde werkzeug.utils
from function.webScraping import *  # Importa la función webScraping
from zipfile import ZipFile

app = Flask(__name__)
socketio = SocketIO(app)


class ConsoleRedirect:
    def __init__(self, log_file_path='exp/app.log'):
        self.console_output = []
        self.log_file_path = log_file_path

    def write(self, text):
        self.console_output.append(text)
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(text + '\n')

    def flush(self):
        pass


sys.stdout = ConsoleRedirect()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("submit_form")
def handle_submit_form(data):
    requests = data["requests"]
    threads = int(data["threads"])
    alert = int(data["alert"])
    
    # Lógica de la aplicación
    executeWebScraping(requests, threads,alert ,socketio)

@app.route('/descargar_expedientes', methods=['GET'])
def descargar_expedientes():
    # Ruta a la carpeta "expedientes"
    ruta_expedientes = 'exp'

    # Crear un archivo zip de la carpeta "expedientes"
    with ZipFile('exp.zip', 'w') as zip_file:
        for carpeta_actual, subcarpetas, archivos in os.walk(ruta_expedientes):
            for archivo in archivos:
                ruta_completa = os.path.join(carpeta_actual, archivo)
                nombre_archivo = os.path.relpath(ruta_completa, ruta_expedientes)
                zip_file.write(ruta_completa, nombre_archivo)

    # Devolver el archivo zip para su descarga
    return send_file('exp.zip', as_attachment=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002, debug=True)
