# Importación de librerías necesarias para el servidor web
from flask import Flask, render_template, request  # Flask para la web, render_template para HTML, request para POST
from flask_socketio import SocketIO, emit  # SocketIO para comunicación en tiempo real
import datetime  # Para timestamp de los logs

# Inicialización de la aplicación Flask y SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Permite conexiones desde cualquier origen

# Ruta principal: muestra la interfaz web de monitorización
def index():
    return render_template('monitor.html')  # Renderiza la plantilla HTML
app.route('/')(index)

# Ruta para recibir logs desde los simuladores (HIS/RIS) vía POST
@app.route('/log', methods=['POST'])
def log():
    data = request.json  # Recibe JSON con {'source': 'HIS'/'RIS', 'msg': 'texto'}
    data['timestamp'] = datetime.datetime.now().strftime('%H:%M:%S')  # Agrega hora
    socketio.emit('new_log', data)  # Envía el log a todos los clientes conectados
    return {'status': 'ok'}  # Respuesta simple

# Punto de entrada principal: inicia el servidor web en modo debug
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
