# Smart Camera Project - Raspberry Pi 3B

## Descripción
Cámara inteligente de bajo coste basada en Raspberry Pi 3B + PiCamera que emula características de cámaras de gama alta mediante redundancia y procesamiento en backend Python.

### Arquitectura
- **Backend**: Python (Flask + OpenCV + PiCamera)
- **Frontend/Orquestación**: Node-RED (flujos visuales)
- **Transporte**: MQTT (JSON) para eventos; HTTP para archivos
- **Filosofía**: Referencias a archivos (no datos binarios) entre nodos; backend ejecuta todo

## Estructura
```
backend/
  __init__.py
  camera.py          (SmartCamera: PiCamera → fallback OpenCV)
  mqtt_client.py     (wrapper paho-mqtt)
  server.py          (Flask REST + file serving)
node-red/
  flow.json          (flujo ejemplo: captura → MQTT → fetch → save)
storage/             (donde se guardan las imágenes capturadas)
requirements.txt
run.py
```

## Requisitos (Raspberry Pi 3B)
- Raspberry Pi OS 64-bit headless
- Python 3.7+
- `mosquitto` (broker MQTT)
- `picamera` o `picamera2` según versión
- `opencv-python`, `numpy`, `flask`, `paho-mqtt`

## Instalación
```bash
# En la Raspberry Pi
sudo apt update && sudo apt install -y mosquitto mosquitto-clients
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Arranque
```bash
# Terminal 1: Broker MQTT (si no está como servicio)
sudo systemctl enable --now mosquitto

# Terminal 2: Backend Python
python3 run.py
# El servidor estará en http://<RPI_IP>:5000
```

## APIs REST del backend
- `POST /api/capture` — captura imagen, guarda en storage/, publica MQTT
- `GET /stream` — MJPEG stream en vivo
- `GET /api/health` — estado de cámara
- `POST /api/start` / `POST /api/stop` — controlar captura
- `GET /files/<filename>` — servir archivo capturado

## Flujo Node-RED
1. Importar `node-red/flow.json` en Node-RED
2. Editar nodos HTTP: reemplazar `<RPI_IP>` por IP real de la Pi
3. Nodo inject → POST capture → MQTT event → GET file → save /tmp/capture.jpg

## Filosofía de diseño
- **Referencias**: nodos pasen rutas/URLs, no imágenes
- **Ejecución**: backend Python; Node-RED solo orquesta
- **Escalabilidad**: fácil añadir backends remotos (Fiji, ComfyUI, etc.)
- **Modularidad**: inspirado en modelo OSI; capas independientes

## Próximos pasos
- Fusión redundante (HDR, denoise, stacking)
- Almacenamiento/rotación circular de clips
- TLS/autenticación
- Soporte para backends remotos especializados
