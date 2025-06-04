from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('monitor.html')

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    # data: {'source': 'HIS'/'RIS', 'msg': 'texto'}
    data['timestamp'] = datetime.datetime.now().strftime('%H:%M:%S')
    socketio.emit('new_log', data)
    return {'status': 'ok'}

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
