"""
Simulador RIS/PACS para flujo HL7 v2 con HIS usando hl7apy y MLLP.
Actúa como servidor MLLP (recibe ADT, OMI) y cliente MLLP (envía ACK, ORU).
"""
# Importación de librerías estándar y de terceros
import socket  # Para comunicación de red
import threading  # Para ejecución en hilos
import time  # Para delays y timestamps
import random  # Para simular variabilidad si se desea
import requests  # Para enviar logs al monitor web
from hl7apy.core import Message  # Para construir mensajes HL7
from hl7apy.parser import parse_message  # Para parsear mensajes HL7

# Configuración de puertos y hosts para MLLP
RIS_MLLP_SERVER_HOST = 'localhost'  # Host local para el servidor RIS
RIS_MLLP_SERVER_PORT = 6662  # Puerto donde el RIS escucha ADT y OMI
HIS_MLLP_SERVER_HOST = 'localhost'  # Host local para el HIS
HIS_MLLP_SERVER_PORT = 6661  # Puerto donde el HIS escucha ACK y ORU

# Caracteres especiales del protocolo MLLP
MLLP_SB = b'\x0b'  # <VT> - Start Block
MLLP_EB = b'\x1c'  # <FS> - End Block
MLLP_CR = b'\x0d'  # <CR> - Carriage Return

# Datos simulados de paciente y médicos
PACIENTE = {
    'id': '123456',
    'nombre': 'Juan Antonio',
    'apellido': 'Pérez García',
    'fecha_nac': '19850315',
    'sexo': 'M',
    'motivo': 'Tos persistente'
}
MEDICO_SOLICITANTE = 'Dra. Ana Rodríguez'  # Médico que solicita el estudio
RADIOLOGO = 'Dr. Carlos López'  # Radiólogo que informa

# Bandera y tiempo de delay para presentación didáctica
DEMO_DELAY = True  # Si es True, agrega pausas entre pasos
DEMO_DELAY_SECONDS = 7  # Segundos de pausa

# Función para enviar mensajes HL7 usando MLLP como cliente
# host: destino, port: puerto destino, hl7_message: mensaje HL7 en string
# Devuelve el mensaje HL7 recibido como respuesta (ACK, ORU, etc.)
def send_mllp_message(host, port, hl7_message):
    with socket.create_connection((host, port)) as s:
        mllp_msg = MLLP_SB + hl7_message.encode() + MLLP_EB + MLLP_CR
        s.sendall(mllp_msg)
        data = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if MLLP_EB in chunk:
                break
        if data:
            # Extrae el mensaje HL7 del bloque MLLP
            hl7 = data.split(MLLP_SB)[-1].split(MLLP_EB)[0].decode(errors='ignore')
            return hl7
        return None

# Función para levantar un servidor MLLP que recibe mensajes HL7
# port: puerto a escuchar, on_message: función callback para procesar cada mensaje recibido
def mllp_server(port, on_message):
    def server():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', port))
            s.listen(1)
            print(f"[RIS] Servidor MLLP escuchando en puerto {port}")
            while True:
                conn, addr = s.accept()
                with conn:
                    data = b''
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                        if MLLP_EB in chunk:
                            break
                    if data:
                        # Extrae el mensaje HL7 y lo pasa al callback
                        hl7 = data.split(MLLP_SB)[-1].split(MLLP_EB)[0].decode(errors='ignore')
                        on_message(hl7, conn)
    threading.Thread(target=server, daemon=True).start()

# Creación de mensajes HL7

# Función para construir un mensaje ACK para respuestas a mensajes ADT^A04 y OMI^O23
# msg_ctrl_id: ID de control del mensaje original, ack_code: código de reconocimiento (AA, AE, etc.)
# Devuelve el mensaje ACK en formato ER7
def build_ack(msg_ctrl_id, ack_code='AA'):
    msg = Message("ACK", version="2.5")
    msg.msh.msh_3 = 'RIS'
    msg.msh.msh_4 = 'RAD'
    msg.msh.msh_5 = 'HIS'
    msg.msh.msh_6 = 'HOSP'
    msg.msh.msh_7 = time.strftime('%Y%m%d%H%M%S')
    msg.msh.msh_9 = 'ACK'
    msg.msh.msh_10 = f"ACK{msg_ctrl_id}"
    msg.msh.msh_11 = 'P'
    msg.msh.msh_12 = '2.5'
    msg.msa.msa_1 = ack_code
    msg.msa.msa_2 = msg_ctrl_id
    return msg.to_er7()

# Función para construir un mensaje ORU^R01 con los resultados de estudios
# msg_ctrl_id: ID de control del mensaje, order_id: ID de la orden, estudio: tipo de estudio (TAC, RX, etc.)
# obr4: código y descripción del procedimiento, obx5: resultados en texto
# Devuelve el mensaje ORU^R01 en formato ER7
def build_oru_r01(msg_ctrl_id, order_id, estudio, obr4, obx5):
    # Construye un mensaje ORU^R01 usando la estructura de grupos estándar HL7 v2.5
    try:
        msg = Message("ORU_R01", version="2.5")
        msg.msh.msh_3 = 'RIS'
        msg.msh.msh_4 = 'RAD'
        msg.msh.msh_5 = 'HIS'
        msg.msh.msh_6 = 'HOSP'
        msg.msh.msh_7 = time.strftime('%Y%m%d%H%M%S')
        msg.msh.msh_9 = 'ORU^R01'
        msg.msh.msh_10 = msg_ctrl_id
        msg.msh.msh_11 = 'P'
        msg.msh.msh_12 = '2.5'
        # Grupos: PATIENT_RESULT -> PATIENT (PID) y ORDER_OBSERVATION (ORC, OBR, OBX)
        pr = msg.add_group('PATIENT_RESULT')
        pat = pr.add_group('PATIENT')
        pat.pid.pid_3 = PACIENTE['id']
        pat.pid.pid_5 = f"{PACIENTE['apellido']}^{PACIENTE['nombre']}"
        pat.pid.pid_7 = PACIENTE['fecha_nac']
        pat.pid.pid_8 = PACIENTE['sexo']
        oo = pr.add_group('ORDER_OBSERVATION')
        oo.orc.orc_2 = order_id
        oo.orc.orc_12 = RADIOLOGO
        oo.obr.obr_2 = order_id
        oo.obr.obr_4 = obr4
        oo.obr.obr_16 = RADIOLOGO
        oo.obr.obr_13 = PACIENTE['motivo']
        obx = oo.add_segment('OBX')
        obx.obx_1 = '1'
        obx.obx_2 = 'TX'
        obx.obx_3 = estudio
        obx.obx_5 = obx5
        return msg.to_er7()
    except Exception as e:
        print(f"[RIS] Error construyendo ORU^R01: {e}")
        return ''

# Manejo de mensajes recibidos por el RIS
ordenes = []  # Lista para almacenar órdenes recibidas
def on_ris_message(hl7, conn):
    print(f"\n[RIS] Recibido mensaje HL7:\n{hl7}\n")
    web_log(f"Recibido mensaje HL7:\n{hl7}")
    msg = parse_message(hl7, find_groups=False)
    msh9 = msg.msh.msh_9.value
    msg_ctrl_id = msg.msh.msh_10.value
    if msh9.startswith('ADT^A04'):
        print("[RIS] Paciente registrado en RIS.")
        web_log("Paciente registrado en RIS.")
        ack = build_ack(msg_ctrl_id, 'AA')
        mllp_msg = MLLP_SB + ack.encode() + MLLP_EB + MLLP_CR
        conn.sendall(mllp_msg)
        print("[RIS] ACK enviado por ADT^A04\n")
        web_log("ACK enviado por ADT^A04")
        if DEMO_DELAY:
            time.sleep(DEMO_DELAY_SECONDS)
    elif msh9.startswith('OMI^O23'):
        print(f"[RIS] Nueva orden recibida: {msg.orc.orc_2.value} - {msg.obr.obr_4.value}")
        web_log(f"Nueva orden recibida: {msg.orc.orc_2.value} - {msg.obr.obr_4.value}")
        ordenes.append({
            'order_id': msg.orc.orc_2.value,
            'estudio': msg.obr.obr_4.value
        })
        ack = build_ack(msg_ctrl_id, 'AA')
        mllp_msg = MLLP_SB + ack.encode() + MLLP_EB + MLLP_CR
        conn.sendall(mllp_msg)
        print("[RIS] ACK enviado por OMI^O23\n")
        web_log("ACK enviado por OMI^O23")
        if DEMO_DELAY:
            time.sleep(DEMO_DELAY_SECONDS)
    else:
        print(f"[RIS] Mensaje no esperado: {msh9}")

# Envío de resultados ORU^R01

# Función que envía los resultados de los estudios al HIS en mensajes ORU^R01
def enviar_resultados():
    procesadas = set()  # Conjunto para llevar registro de órdenes ya procesadas
    while True:
        for i, orden in enumerate(ordenes):
            if orden['order_id'] in procesadas:
                continue
            if 'CT' in orden['estudio']:
                obx5 = 'Tomografía de tórax: sin hallazgos patológicos.'
                obr4 = '71250^CT TORAX SIN CONTRASTE^CPT4'
                estudio = 'TOMOGRAFIA TORAX'
            else:
                obx5 = 'Radiografía de tórax: sin infiltrados ni consolidaciones.'
                obr4 = '71020^RADIOGRAFIA TORAX^CPT4'
                estudio = 'RADIOGRAFIA TORAX'
            oru_id = f'ORU{i+1:04d}'
            oru_msg = build_oru_r01(oru_id, orden['order_id'], estudio, obr4, obx5)
            print(f"[RIS] Enviando ORU^R01 al HIS (orden {orden['order_id']}):\n{oru_msg}\n")
            web_log(f"Enviando ORU^R01 al HIS (orden {orden['order_id']}):\n{oru_msg}")
            ack = send_mllp_message(HIS_MLLP_SERVER_HOST, HIS_MLLP_SERVER_PORT, oru_msg)
            print(f"[RIS] ACK recibido por ORU^R01:\n{ack}\n")
            web_log(f"ACK recibido por ORU^R01:\n{ack}")
            procesadas.add(orden['order_id'])
            if DEMO_DELAY:
                time.sleep(DEMO_DELAY_SECONDS)
        time.sleep(2)  # Espera antes de revisar si hay nuevas órdenes

# Envío de logs al monitor web

# Función para enviar mensajes de log al monitor web
# msg: mensaje a enviar, source: fuente del mensaje (por defecto 'RIS')
def web_log(msg, source='RIS'):
    try:
        requests.post('http://localhost:5000/log', json={'source': source, 'msg': msg})
    except Exception:
        pass

# MAIN
if __name__ == "__main__":
    # Inicia el servidor MLLP para recibir mensajes RIS en el puerto configurado
    mllp_server(RIS_MLLP_SERVER_PORT, on_ris_message)
    print("[RIS] Esperando mensajes del HIS... (Ctrl+C para salir)")
    # Hilo para enviar resultados después de recibir órdenes
    threading.Thread(target=enviar_resultados, daemon=True).start()
    while True:
        time.sleep(DEMO_DELAY_SECONDS)
