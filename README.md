# Simulador Didáctico HL7 v2 HIS ↔ RIS/PACS

## Resumen rápido para retomarlo

Este proyecto simula el flujo de mensajes HL7 v2 entre un sistema HIS y un RIS/PACS, usando Python, hl7apy y MLLP. Incluye una interfaz web en Flask+SocketIO para visualizar en tiempo real los mensajes y su significado, ideal para presentaciones y formación.

- **Propósito:** Demostrar y enseñar cómo se comunican un HIS y un RIS/PACS mediante mensajes HL7 v2 (registro de paciente, órdenes, resultados).
- **Componentes principales:**
  - `his_simulator.py`: Simula el HIS (envía ADT/OMI, recibe ACK/ORU).
  - `ris_simulator.py`: Simula el RIS/PACS (recibe ADT/OMI, envía ACK/ORU).
  - `web_monitor.py` + `templates/monitor.html`: Interfaz web para ver mensajes y explicaciones en tiempo real.
- **Cómo ejecutar la demo:**
  1. Activa el entorno virtual si lo tienes.
  2. Ejecuta `python web_monitor.py` y abre http://localhost:5000
  3. Ejecuta `python ris_simulator.py` en otra terminal.
  4. Ejecuta `python his_simulator.py` en otra terminal.
- **Delays:** Puedes ajustar la velocidad de la demo cambiando `DEMO_DELAY` y `DEMO_DELAY_SECONDS` en los scripts.
- **Explicaciones:** Los mensajes y su significado se muestran y explican en la web, diferenciando origen (HIS/RIS).

---

## Características
- Simulación de mensajes HL7 v2 (ADT^A04, OMI^O23, ORU^R01) entre HIS y RIS.
- Comunicación MLLP realista (cliente/servidor) usando sockets.
- Visualización web en tiempo real de los mensajes y explicaciones didácticas.
- Delays configurables para presentaciones paso a paso.
- Interfaz accesible y fácil de modificar.

## Requisitos
- Python 3.8+
- Instalar dependencias:
  ```bash
  pip install -r requirements.txt
  ```

## Estructura del Proyecto
- `his_simulator.py`: Simulador del HIS (envía ADT/OMI, recibe ACK/ORU).
- `ris_simulator.py`: Simulador del RIS/PACS (recibe ADT/OMI, envía ACK/ORU).
- `web_monitor.py`: Servidor Flask+SocketIO para monitorizar mensajes HL7 en tiempo real.
- `templates/monitor.html`: Interfaz web para visualizar mensajes y explicaciones.
- `requirements.txt`: Dependencias del proyecto.

## Cómo Ejecutar
1. **Inicia el monitor web:**
   ```bash
   python web_monitor.py
   ```
   Accede a [http://localhost:5000](http://localhost:5000) en tu navegador.

2. **En otra terminal, ejecuta el simulador RIS:**
   ```bash
   python ris_simulator.py
   ```

3. **En otra terminal, ejecuta el simulador HIS:**
   ```bash
   python his_simulator.py
   ```

Puedes modificar los delays de la demo cambiando las variables `DEMO_DELAY` y `DEMO_DELAY_SECONDS` en los scripts.

## Notas
- El sistema está preparado para ser ampliado con más tipos de mensajes HL7 o escenarios de error.
- El entorno virtual `env/` está excluido del repositorio.
- Repositorio: https://github.com/chris78rey/pres_HL7

---
¡Explora, aprende y personaliza la simulación para tus necesidades didácticas!
