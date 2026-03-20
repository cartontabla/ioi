# Workflow: Desarrollo en Mac → Despliegue en Raspberry Pi

## Filosofía
1. **Develop locally on Mac**: testear sin hardware especializado (fallback OpenCV)
2. **Deploy to Pi**: cuando esté listo, copiar código y correr en hardware real
3. **Iterate**: cambios locales → git push → git pull en Pi → reload servicio

## Flujo rápido

### Primera vez: setup completo
```bash
cd ~/IOI
./setup.sh
# Responde preguntas sobre tu Pi (IP, usuario)
# Script hace: local test + deploy + instrucciones finales
```

### Desarrollo iterativo

**En tu Mac** (dentro de `~/IOI`):
```bash
# Terminal 1: Backend
source venv/bin/activate
python3 run.py
# Logs en stdout, Ctrl+C para parar

# Terminal 2: Editar código
vim backend/camera.py
# hacer cambios...
# Ctrl+C en Terminal 1, volver a ejecutar

# Terminal 3: Probar con curl
curl -X POST http://localhost:5001/api/capture
```

**Cuando funciona localmente**, commit + push:
```bash
git add .
git commit -m "Feature: add HDR processing"
git push origin main
```

**En la Raspberry Pi**:
```bash
# SSH desde Mac
ssh pi@192.168.1.100

# En la Pi
cd ~/smartcam
git pull origin main

# Si es servicio systemd
sudo systemctl restart smartcam
sudo journalctl -u smartcam -f

# Si es manual
source venv/bin/activate
python3 run.py
```

## Comandos útiles (desde tu Mac)

```bash
# Setup inicial
make install          # Crear venv + instalar deps

# Desarrollo
make dev             # Correr backend local (localhost:5000)
make test            # Suite de pruebas
make clean           # Limpiar venv y cache

# Despliegue
make deploy PI_HOST=192.168.1.100

# Sincronizar cambios (sin git)
make sync PI_HOST=192.168.1.100  # (próximamente)
```

## Requisitos en tu Mac

```bash
# Check que tienes Python 3
python3 --version    # 3.7+

# Check que git está instalado
git --version

# SSH acceso a Pi (copiar clave si no la tienes)
ssh-keygen -t ed25519
ssh-copy-id pi@192.168.1.100
```

## Estructura de directorios

```
~/IOI/                          (tu repo local en Mac)
├── backend/
├── node-red/
├── storage/                    (local, filled by dev run)
├── venv/                       (local Python env)
├── config.py                   (importado por server.py)
├── run.py
├── requirements.txt
├── Makefile
├── setup.sh
├── deploy.sh
└── ...

~pi/smartcam/                   (en Pi, después de deploy)
├── backend/
├── storage/                    (archivos reales capturados)
├── venv/
├── ...
```

## Variables de entorno (para override de config.py)

En tu máquina local o Pi, puedes setear:

```bash
# Customizar cámara
export CAMERA_RESOLUTION=1280,720
export CAMERA_FRAMERATE=30
export CAMERA_JPEG_QUALITY=90

# Customizar MQTT
export MQTT_HOST=192.168.1.50   # si broker está en otra máquina
export MQTT_PORT=1883

# Customizar Flask
export FLASK_DEBUG=true         # recargar en cambios
export FLASK_PORT=5001          # si 5000 está ocupado

# Debug
export LOG_LEVEL=DEBUG

python3 run.py
```

## Troubleshooting

### "Cannot connect to MQTT broker"
```bash
# En local: arrancar mosquitto
brew install mosquitto
mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf

# En Pi: ya debería estar corriendo
sudo systemctl status mosquitto
```

### "OpenCV ImportError"
```bash
# En Mac: reinstalar con caché limpio
source venv/bin/activate
pip install --upgrade --force-reinstall opencv-python
```

### "Puerto 5000 ocupado"
```bash
# Ver qué está usando el puerto
lsof -i :5000

# O cambiar puerto
export FLASK_PORT=5001
python3 run.py
```

### "SSH key not configured"
```bash
# En tu Mac
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
ssh-copy-id -i ~/.ssh/id_ed25519 pi@192.168.1.100
```

## Checklist para despliegue a producción

- [ ] `make test` pasa sin errores en local
- [ ] Backend responde `curl http://localhost:5001/api/health`
- [ ] Cambios commiteados: `git status` limpio
- [ ] SSH funciona: `ssh pi@<IP> echo OK`
- [ ] `make deploy PI_HOST=<IP>` completa sin errores
- [ ] En Pi: `sudo systemctl enable smartcam` (auto-arranque)
- [ ] Monitorear logs: `sudo journalctl -u smartcam -f`
- [ ] Node-RED conecta: `curl http://<PI_IP>:5000/api/health` desde máquina con Node-RED

## Próximas automatizaciones

- [ ] Git hooks (pre-commit) para lint
- [ ] CI/CD con GitHub Actions (test antes de desplegar)
- [ ] Rollback automático si healthcheck falla
- [ ] Monitoreo remoto con Prometheus
