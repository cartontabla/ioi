# Deploy — Mac → Raspberry Pi

## Infraestructura

| Elemento | Valor |
|---|---|
| Pi hostname | ioi.local |
| Pi IP | 192.168.0.39 |
| Pi usuario | lino |
| SSH key | `~/.ssh/id_ed25519_ioi` |
| Backend puerto | 5001 |
| Node-RED puerto | 1880 |

---

## Deploy completo

```bash
./deploy.sh ioi.local
```

Esto hace en orden:
1. Verifica SSH
2. Sincroniza código vía rsync (excluye `projects/`, `__pycache__`, `.git`)
3. Instala dependencias Python (`pip3 install -r requirements.txt`)
4. Reinicia el backend Python (puerto 5001)
5. Copia `node-red/flow.json` → `~/.node-red/flows.json` y reinicia Node-RED

---

## Servicios en la Pi

### Backend Flask

```bash
# Ver si está corriendo
curl http://ioi.local:5001/api/health

# Ver logs
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local "cat /tmp/ioi_backend.log"

# Arrancar manualmente
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local "cd ~/IOI && python3 run.py"
```

### Node-RED

```bash
# Estado
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local "sudo systemctl status nodered"

# Logs
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local "sudo journalctl -u nodered -n 50"

# Reiniciar
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local "sudo systemctl restart nodered"
```

---

## Acceso a la Pi

```bash
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local
```

---

## Variables de entorno (override de config.py)

```bash
# Resolución del stream en vivo (no afecta a las capturas)
export CAMERA_RESOLUTION=640,480
export CAMERA_FRAMERATE=24

# Resolución de captura still (máximo sensor)
export CAPTURE_RESOLUTION=4056,3040

# Directorio de proyectos
export PROJECTS_DIR=/home/lino/IOI/projects

# Puerto Flask
export FLASK_PORT=5001
```

---

## Checklist de deploy

- [ ] `curl http://ioi.local:5001/api/health` responde `running: true`
- [ ] Node-RED accesible en `http://ioi.local:1880`
- [ ] Stream visible en `http://ioi.local:5001/stream`
- [ ] Flujo Node-RED desplegado y sin errores rojos
