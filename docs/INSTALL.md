# Instalación y configuración en Raspberry Pi 3B

## Requisitos previos
- Raspberry Pi 3B con Raspberry Pi OS 64-bit (headless recomendado)
- PiCamera conectada y habilitada en `raspi-config`
- Conexión a red (Ethernet o WiFi)
- SSH acceso para instalación remota

## 1. Preparar Raspberry Pi

### Enable Camera
```bash
sudo raspi-config
# Interfacing Options → Camera → Enable
# Reboot cuando se pida
```

### Instalar dependencias del sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  mosquitto mosquitto-clients \
  python3-pip \
  python3-venv \
  python3-dev \
  libatlas-base-dev \
  libjasper-dev \
  libtiff5 \
  libjasper1 \
  libharfbuzz0b \
  libwebp6 \
  libtiff5 \
  libopenjp2-7 \
  libhdf5-dev \
  libharfbuzz0b \
  libwebp6
```

### Enable MQTT broker
```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
# Verificar
mosquitto_sub -h localhost -t "#"  # Ctrl+C para salir
```

## 2. Clonar y setup del proyecto

### Clone repo (cambiar URL según tu caso)
```bash
cd ~
git clone https://github.com/tu-usuario/smartcam.git
cd smartcam
```

### Crear virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### Instalar dependencias Python
```bash
pip install -r requirements.txt
```

**Nota**: Si encuentras errores con `picamera` en Bullseye/Bookworm:
```bash
# Para Raspberry Pi OS Bullseye (Python 3.9+)
pip install picamera2

# Para versiones más viejas
pip install picamera
```

## 3. Configurar e iniciar

### Crear archivo de configuración (opcional)
```bash
cat > config.env << 'EOF'
CAMERA_RESOLUTION=640x480
CAMERA_FRAMERATE=24
MQTT_HOST=localhost
MQTT_PORT=1883
FLASK_PORT=5000
STORAGE_DIR=./storage
EOF
```

### Iniciar el backend
```bash
source venv/bin/activate
python3 run.py
# Salida esperada:
# * Running on http://0.0.0.0:5000
```

### Verificar en otra terminal
```bash
# Check health
curl http://localhost:5000/api/health
# Respuesta: {"running":false,"source":null,"ring_len":0}

# Capturar una imagen
curl -X POST http://localhost:5000/api/capture
# Respuesta: {"ok":true,"path":"/files/capture_...jpg","filename":"...jpg"}

# Verificar archivo generado
ls -la storage/
```

## 4. Instalar Node-RED (opcional, en otra máquina)

Si quieres correr Node-RED en la Pi:
```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
```

O en otra máquina (PC/Mac) con Node-RED:
```bash
# En el sistema con Node-RED
npm install -g node-red
node-red
# Abrir en navegador: http://localhost:1880
# Importar flow.json desde Manage palette
```

## 5. Configurar flujo Node-RED

1. Abrir Node-RED en http://<NODE_RED_IP>:1880
2. Menú hamburguer → Import → seleccionar `node-red/flow.json`
3. Doble-clic en nodos `http request`:
   - Reemplazar `<RPI_IP>` con IP de tu Raspberry Pi
   - Ej: `http://192.168.1.100:5000/api/capture`
4. Deploy

## 6. Prueba end-to-end

1. **Backend corriendo** en RPi: `python3 run.py`
2. **Node-RED** corriendo (local o remoto)
3. **Mosquitto** en RPi: `sudo systemctl status mosquitto`
4. Click en nodo `Inject` "Trigger capture"
   - Aparecerá en debug: captura guardada
   - `/tmp/capture.jpg` debe existir en máquina con Node-RED
5. Verificar imagen capturada:
   ```bash
   file /tmp/capture.jpg
   # Salida: JPEG image data...
   ```

## 7. Ejecutar como servicio (opcional)

### Crear archivo de servicio systemd
```bash
sudo tee /etc/systemd/system/smartcam.service > /dev/null << 'EOF'
[Unit]
Description=Smart Camera Backend
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smartcam
Environment="PATH=/home/pi/smartcam/venv/bin"
ExecStart=/home/pi/smartcam/venv/bin/python3 run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### Habilitar e iniciar
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartcam
sudo systemctl start smartcam
sudo systemctl status smartcam

# Ver logs
sudo journalctl -u smartcam -f
```

## 8. Troubleshooting

### PiCamera no detectada
```bash
# Verificar camera
vcgencmd get_camera
# Salida debe ser: supported=1 detected=1

# O usar libcamera-hello
libcamera-hello --list-cameras
```

### MQTT no conecta
```bash
# Verificar broker
sudo systemctl status mosquitto
# Intentar publicar
mosquitto_pub -h localhost -t test -m "hello"
# En otra terminal
mosquitto_sub -h localhost -t test
```

### Puerto 5000 ocupado
```bash
# Buscar qué está usando el puerto
sudo lsof -i :5000
# Cambiar puerto en run.py:
# app.run(host='0.0.0.0', port=5001)
```

### OpenCV/picamera imports fallan
```bash
# Reinstalar con caché limpio
pip install --no-cache-dir opencv-python picamera2
```

## 9. Monitoreo básico

```bash
# Ver uso de CPU/memoria
top
ps aux | grep python3

# Ver logs de Flask
# Cambiar debug=True en run.py para más verbosidad

# Testear MQTT
mosquitto_sub -h localhost -t "camera/#" -v
# En otra terminal: curl -X POST http://localhost:5000/api/capture
```

## 10. Próximos pasos

- [ ] Configurar auto-arranque con systemd
- [ ] Añadir monitoreo (Prometheus/Grafana)
- [ ] Backups de imágenes capturadas
- [ ] TLS para conexiones remotas
- [ ] Autenticación MQTT
