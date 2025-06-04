"""
Simulador HIS para flujo HL7 v2 con RIS/PACS usando hl7apy y MLLP.
Actúa como cliente MLLP (envía ADT, OMI) y servidor MLLP (recibe ACK, ORU).
"""
# Importación de librerías estándar y de terceros
import socket  # Para comunicación de red
import threading  # Para ejecución en hilos
import time  # Para delays y timestamps
import requests  # Para enviar logs al monitor web
from hl7apy.core import Message  # Para construir mensajes HL7
from hl7apy.parser import parse_message  # Para parsear mensajes HL7

# Configuración de puertos y hosts para MLLP
HIS_MLLP_SERVER_HOST = 'localhost'  # Host local para el servidor HIS
HIS_MLLP_SERVER_PORT = 6661  # Puerto donde el HIS escucha ACK y ORU
RIS_MLLP_SERVER_HOST = 'localhost'  # Host local para el RIS
RIS_MLLP_SERVER_PORT = 6662  # Puerto donde el RIS escucha ADT y OMI

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
            print(f"[HIS] Servidor MLLP escuchando en puerto {port}")
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

# Función para construir un mensaje ADT_A01 (registro de paciente)
# msg_ctrl_id: ID de control del mensaje (para correlacionar con ACK)
# Devuelve el mensaje ADT_A01 en formato ER7
def build_adt_a04(msg_ctrl_id):
    # Cambiar ADT_A04 por ADT_A01 (estructura base compatible en hl7apy)
    msg = Message("ADT_A01", version="2.5")
    msg.msh.msh_3 = 'HIS'
    msg.msh.msh_4 = 'HOSP'
    msg.msh.msh_5 = 'RIS'
    msg.msh.msh_6 = 'RAD'
    msg.msh.msh_7 = time.strftime('%Y%m%d%H%M%S')
    msg.msh.msh_9 = 'ADT^A04'
    msg.msh.msh_10 = msg_ctrl_id
    msg.msh.msh_11 = 'P'
    msg.msh.msh_12 = '2.5'
    msg.pid.pid_3 = PACIENTE['id']
    msg.pid.pid_5 = f"{PACIENTE['apellido']}^{PACIENTE['nombre']}"
    msg.pid.pid_7 = PACIENTE['fecha_nac']
    msg.pid.pid_8 = PACIENTE['sexo']
    msg.pv1.pv1_2 = 'I'
    return msg.to_er7()

# Función para construir un mensaje OMI_O23 (orden de estudio)
# msg_ctrl_id: ID de control del mensaje, order_id: ID de la orden
# estudio: nombre del estudio, modality: modalidad del estudio (ej. CR, CT)
# obr4: código y descripción del procedimiento (CPT4), ipc5: código del ítem en el paquete
# Devuelve el mensaje OMI_O23 en formato ER7
def build_omi_o23(msg_ctrl_id, order_id, estudio, modality, obr4, ipc5):
    # Usar la estructura OMI_O23 para mensajes OMI^O23 (no OML_O21)
    try:
        msg = Message("OMI_O23", version="2.5")
        msg.msh.msh_3 = 'HIS'
        msg.msh.msh_4 = 'HOSP'
        msg.msh.msh_5 = 'RIS'
        msg.msh.msh_6 = 'RAD'
        msg.msh.msh_7 = time.strftime('%Y%m%d%H%M%S')
        msg.msh.msh_9 = 'OMI^O23'
        msg.msh.msh_10 = msg_ctrl_id
        msg.msh.msh_11 = 'P'
        msg.msh.msh_12 = '2.5'
        msg.pid.pid_3 = PACIENTE['id']
        msg.pid.pid_5 = f"{PACIENTE['apellido']}^{PACIENTE['nombre']}"
        msg.pid.pid_7 = PACIENTE['fecha_nac']
        msg.pid.pid_8 = PACIENTE['sexo']
        msg.orc.orc_1 = 'NW'
        msg.orc.orc_2 = order_id
        msg.orc.orc_12 = MEDICO_SOLICITANTE
        msg.obr.obr_2 = order_id
        msg.obr.obr_4 = obr4
        msg.obr.obr_16 = RADIOLOGO
        msg.obr.obr_13 = PACIENTE['motivo']
        # El segmento IPC no es estándar en OMI_O23, solo agregar si la estructura lo permite
        if hasattr(msg, 'ipc'):
            msg.ipc.ipc_5 = ipc5
        return msg.to_er7()
    except Exception as e:
        print(f"[HIS] Error construyendo OMI^O23: {e}")
        return ''

# Función para construir un mensaje ACK (acknowledgment)
# msg_ctrl_id: ID de control del mensaje original
# ack_code: código de ACK, 'AA' para acknowledgment positivo
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

# Función para construir un mensaje ORU_R01 (informe de resultado)
# msg_ctrl_id: ID de control del mensaje, order_id: ID de la orden
# estudio: nombre del estudio, obr4: código y descripción del procedimiento (CPT4)
# obx5: resultado del estudio
# Devuelve el mensaje ORU_R01 en formato ER7
def build_oru_r01(msg_ctrl_id, order_id, estudio, obr4, obx5):
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
    msg.pid.pid_3 = PACIENTE['id']
    msg.pid.pid_5 = f"{PACIENTE['apellido']}^{PACIENTE['nombre']}"
    msg.pid.pid_7 = PACIENTE['fecha_nac']
    msg.pid.pid_8 = PACIENTE['sexo']
    msg.orc.orc_2 = order_id
    msg.orc.orc_12 = RADIOLOGO
    msg.obr.obr_2 = order_id
    msg.obr.obr_4 = obr4
    msg.obr.obr_16 = RADIOLOGO
    msg.obr.obr_13 = PACIENTE['motivo']
    msg.obx.obx_1 = '1'
    msg.obx.obx_2 = 'TX'
    msg.obx.obx_3 = estudio
    msg.obx.obx_5 = obx5
    return msg.to_er7()

# Función para enviar logs al monitor web
# msg: mensaje a enviar, source: fuente del mensaje (por defecto 'HIS')
def web_log(msg, source='HIS'):
    try:
        requests.post('http://localhost:5000/log', json={'source': source, 'msg': msg})
    except Exception:
        pass

# Manejo de mensajes recibidos por el HIS

# Función que procesa los mensajes HL7 recibidos en el HIS
# hl7: mensaje HL7 en formato string, conn: conexión del socket
def on_his_message(hl7, conn):
    print(f"\n[HIS] Recibido mensaje HL7:\n{hl7}\n")
    web_log(f"Recibido mensaje HL7:\n{hl7}")
    if not hl7.strip():
        print("[HIS] Advertencia: Mensaje vacío recibido. Ignorando.")
        web_log("Advertencia: Mensaje vacío recibido. Ignorando.")
        return
    try:
        # Intenta parsear el mensaje HL7
        msg = parse_message(hl7, find_groups=False)
    except Exception as e:
        print(f"[HIS] Error al parsear mensaje HL7: {e}\nMensaje recibido:\n{hl7}")
        web_log(f"Error al parsear mensaje HL7: {e}\nMensaje recibido:\n{hl7}")
        return
    # Manejo de mensajes ACK
    if msg.msh.msh_9.value.startswith('ACK'):
        ack_code = msg.msa.msa_1.value
        print(f"[HIS] ACK recibido: {ack_code}")
        web_log(f"ACK recibido: {ack_code}")
        if ack_code != 'AA':
            print(f"[HIS] ¡Error en ACK! Código: {ack_code}")
            web_log(f"¡Error en ACK! Código: {ack_code}")
    # Manejo de mensajes ORU^R01 (resultados de estudios)
    elif msg.msh.msh_9.value.startswith('ORU^R01'):
        print(f"[HIS] Resultado recibido para orden: {msg.orc.orc_2.value}")
        web_log(f"Resultado recibido para orden: {msg.orc.orc_2.value}")
        # Enviar ACK de vuelta al RIS
        ack = build_ack(msg.msh.msh_10.value, 'AA')
        mllp_msg = MLLP_SB + ack.encode() + MLLP_EB + MLLP_CR
        conn.sendall(mllp_msg)
        print(f"[HIS] ACK enviado por ORU^R01\n")
        web_log("ACK enviado por ORU^R01")

# MAIN
if __name__ == "__main__":
    # Inicia el servidor MLLP para recibir mensajes HIS
    mllp_server(HIS_MLLP_SERVER_PORT, on_his_message)
    time.sleep(1)  # Espera a que el servidor esté listo

    # Paso 1: Registro del paciente (ADT^A04)
    adt_id = 'MSG0001'
    adt_msg = build_adt_a04(adt_id)
    print(f"[HIS] Enviando ADT^A04 al RIS:\n{adt_msg}\n")
    web_log(f"Enviando ADT^A04 al RIS:\n{adt_msg}")
    ack = send_mllp_message(RIS_MLLP_SERVER_HOST, RIS_MLLP_SERVER_PORT, adt_msg)
    print(f"[HIS] ACK recibido por ADT^A04:\n{ack}\n")
    web_log(f"ACK recibido por ADT^A04:\n{ack}")
    if DEMO_DELAY:
        time.sleep(DEMO_DELAY_SECONDS)

    # Paso 3a: Orden de Radiografía (OMI^O23)
    omi1_id = 'MSG0002'
    order1_id = 'ORD0001'
    omi1_msg = build_omi_o23(omi1_id, order1_id, 'RADIOGRAFIA TORAX', 'CR', '71020^RADIOGRAFIA TORAX^CPT4', 'CR^RADIOGRAFIA^DCM')
    print(f"[HIS] Enviando OMI^O23 (Radiografía) al RIS:\n{omi1_msg}\n")
    web_log(f"Enviando OMI^O23 (Radiografía) al RIS:\n{omi1_msg}")
    ack = send_mllp_message(RIS_MLLP_SERVER_HOST, RIS_MLLP_SERVER_PORT, omi1_msg)
    print(f"[HIS] ACK recibido por OMI^O23 (Radiografía):\n{ack}\n")
    web_log(f"ACK recibido por OMI^O23 (Radiografía):\n{ack}")
    if DEMO_DELAY:
        time.sleep(DEMO_DELAY_SECONDS)

    # Paso 3b: Orden de Tomografía (OMI^O23)
    omi2_id = 'MSG0003'
    order2_id = 'ORD0002'
    omi2_msg = build_omi_o23(omi2_id, order2_id, 'TOMOGRAFIA TORAX', 'CT', '71250^CT TORAX SIN CONTRASTE^CPT4', 'CT^TOMOGRAFIA COMPUTARIZADA^DCM')
    print(f"[HIS] Enviando OMI^O23 (Tomografía) al RIS:\n{omi2_msg}\n")
    web_log(f"Enviando OMI^O23 (Tomografía) al RIS:\n{omi2_msg}")
    ack = send_mllp_message(RIS_MLLP_SERVER_HOST, RIS_MLLP_SERVER_PORT, omi2_msg)
    print(f"[HIS] ACK recibido por OMI^O23 (Tomografía):\n{ack}\n")
    web_log(f"ACK recibido por OMI^O23 (Tomografía):\n{ack}")
    if DEMO_DELAY:
        time.sleep(DEMO_DELAY_SECONDS)

    print("[HIS] Esperando resultados ORU^R01 del RIS... (Ctrl+C para salir)")
    web_log("Esperando resultados ORU^R01 del RIS... (Ctrl+C para salir)")
    while True:
        time.sleep(DEMO_DELAY_SECONDS)
