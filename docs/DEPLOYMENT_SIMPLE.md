# Despliegue: Mac → Raspberry Pi 3B

**Premisa**: Pi ya tiene todo instalado (Python, PiCamera, mosquitto, Node-RED)

## Setup inicial (primera vez)

```bash
cd ~/IOI
./setup.sh
# Responde: IP de Pi, usuario (default: pi)
# Script: crea venv local + testea + sincroniza a Pi
```

## Flujo normal (después de changes)

### Develop en Mac
```bash
source venv/bin/activate
python3 run.py
# localhost:5000 está vivo
# Editar código, cambios automáticos si FLASK_DEBUG=true
```

### Deploy a Pi
```bash
# Opción A: via git (si tienes repo remoto)
git push origin main

# En la Pi:
cd ~/smartcam && git pull
sudo systemctl restart smartcam

# Opción B: via script (local development sin git)
./deploy.sh 192.168.1.100 pi
# Sincroniza código, restart automático en instrucciones
```

## Comandos Makefile

```bash
make install       # venv + dependencias
make dev          # backend local
make test         # suite
make deploy PI_HOST=192.168.1.100
```

## Variables de entorno (config.py)

```bash
export CAMERA_RESOLUTION=1280,720
export CAMERA_FRAMERATE=30
export MQTT_HOST=192.168.1.100    # si broker en otra máquina
export FLASK_PORT=5001             # si 5000 ocupado

python3 run.py
```

## Verificar en Pi

```bash
# Health check
curl http://<PI_IP>:5000/api/health

# Logs (si es servicio)
sudo journalctl -u smartcam -f

# Manual restart
ssh pi@<IP>
cd ~/smartcam
source venv/bin/activate
python3 run.py
```

## Checklist

- [x] Mac: `python3 run.py` funciona (fallback OpenCV)
- [x] SSH a Pi: `ssh-copy-id pi@<IP>` sin password
- [ ] `./deploy.sh <IP> pi` sin errores
- [ ] Pi: `curl http://localhost:5000/api/health` OK
- [ ] Node-RED: importar flow.json, reemplazar `<RPI_IP>`
