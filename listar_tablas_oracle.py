"""
Script para conectarse a una base de datos Oracle y listar las tablas del esquema SEGMENTOS_HL7.
Requiere: cx_Oracle (pip install cx_Oracle) y Oracle Instant Client instalado/configurado.
"""
import cx_Oracle
from hl7apy.core import Message
from hl7apy.parser import parse_message

# Configuración de conexión
usuario = 'SEGMENTOS_HL7'
clave = 'SEGMENTOS_HL7'
host = '172.16.60.21'
port = 1521
sid = 'prdsgh2'
# Usar makedsn para construir el DSN con SID
dsn = cx_Oracle.makedsn(host, port, sid=sid)

try:
    # Establecer conexión
    conn = cx_Oracle.connect(user=usuario, password=clave, dsn=dsn)
    print(f"Conectado a Oracle como {usuario}\n")
    cur = conn.cursor()
    # Consultar tablas del usuario
    cur.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    tablas = cur.fetchall()
    print("Tablas en el esquema SEGMENTOS_HL7:")
    for (tabla,) in tablas:
        print(f"- {tabla}")
    print("\n---\n")
    # Leer y mostrar todos los registros de ADT_MESSAGES
    print("Registros en ADT_MESSAGES:")
    cur.execute("SELECT ADT_MESSAGE_ID, HL7_RAW_MESSAGE, MESSAGE_SENT_FLAG, CREATED_AT FROM ADT_MESSAGES ORDER BY ADT_MESSAGE_ID")
    rows = cur.fetchall()
    hl7_objs = []  # Lista para almacenar los objetos hl7apy
    for row in rows:
        adt_id, hl7_msg, sent_flag, created_at = row
        print(f"ID: {adt_id} | Enviado: {sent_flag} | Fecha: {created_at}")
        print("Mensaje HL7 crudo:")
        print(hl7_msg)
        # Obtener todos los campos de la fila para construir el mensaje HL7 desde los campos de la tabla
        cur2 = conn.cursor()
        cur2.execute("""
            SELECT ADT_MESSAGE_ID, MSH_FIELD_SEPARATOR, MSH_ENCODING_CHARACTERS, MSH_SENDING_APPLICATION, MSH_SENDING_FACILITY, 
                   MSH_RECEIVING_APPLICATION, MSH_RECEIVING_FACILITY, MSH_DATETIME_OF_MESSAGE, MSH_MESSAGE_TYPE, MSH_MESSAGE_CONTROL_ID, 
                   MSH_PROCESSING_ID, MSH_VERSION_ID, EVN_EVENT_TYPE_CODE, EVN_DATE_TIME_OF_EVENT, PID_SET_ID, PID_PATIENT_IDENTIFIER_LIST, 
                   PID_PATIENT_NAME_FAMILY, PID_PATIENT_NAME_GIVEN, PID_DATE_OF_BIRTH, PID_ADMIN_SEX, PV1_SET_ID, PV1_PATIENT_CLASS, 
                   PV1_ASSIGNED_PATIENT_LOCATION, PV1_ADMISSION_TYPE, PV1_ATTENDING_DOCTOR_ID
            FROM ADT_MESSAGES WHERE ADT_MESSAGE_ID = :1
        """, (adt_id,))
        campos = cur2.fetchone()
        if campos:
            # Construir el mensaje HL7 desde los campos
            try:
                msg = Message("ADT_A01", version="2.5")
                # MSH
                msg.msh.msh_1 = campos[1] or '|'
                msg.msh.msh_2 = campos[2] or '^~\&'
                msg.msh.msh_3 = campos[3] or ''
                msg.msh.msh_4 = campos[4] or ''
                msg.msh.msh_5 = campos[5] or ''
                msg.msh.msh_6 = campos[6] or ''
                msg.msh.msh_7 = campos[7] or ''
                msg.msh.msh_9 = campos[8] or ''
                msg.msh.msh_10 = campos[9] or ''
                msg.msh.msh_11 = campos[10] or ''
                msg.msh.msh_12 = campos[11] or ''
                # EVN
                msg.evn.evn_1 = campos[12] or ''
                msg.evn.evn_2 = campos[13] or ''
                # PID
                msg.pid.pid_1 = campos[14] or ''
                msg.pid.pid_3 = campos[15] or ''
                msg.pid.pid_5 = campos[16] or ''
                msg.pid.pid_6 = campos[17] or ''
                msg.pid.pid_7 = campos[18] or ''
                msg.pid.pid_8 = campos[19] or ''
                # PV1
                msg.pv1.pv1_1 = campos[20] or ''
                msg.pv1.pv1_2 = campos[21] or ''
                msg.pv1.pv1_3 = campos[22] or ''
                msg.pv1.pv1_4 = campos[23] or ''
                msg.pv1.pv1_7 = campos[24] or ''
                hl7_objs.append(msg)
                print("[hl7apy] Mensaje HL7 construido desde campos de tabla:")
                print(msg.to_er7())
            except Exception as e:
                print(f"[hl7apy] Error al construir HL7 desde campos: {e}")
        cur2.close()
        print("-"*60)
    # Imprimir todos los mensajes almacenados en la lista como ER7
    print("\nMensajes HL7 construidos desde campos de tabla:")
    for i, msg in enumerate(hl7_objs, 1):
        print(f"\n--- Mensaje {i} ---")
        try:
            print(msg.to_er7())
        except Exception as e:
            print(f"Error al imprimir mensaje {i}: {e}")
    cur.close()
    conn.close()
except cx_Oracle.DatabaseError as e:
    error, = e.args
    print(f"Error de Oracle: {error.message}")
    print("Verifica usuario, clave, DSN y que el Oracle Instant Client esté instalado.")
