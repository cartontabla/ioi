# Arquitectura IOI

Sistema de captura de ortoimágenes científicas para documentación de obras de arte.

## Principios de diseño

- **Modularidad LEGO**: cada componente es independiente y reemplazable
- **Pipeline no destructivo**: los archivos maestros son siempre TIFF, nunca se modifican
- **Referencias, no datos**: entre componentes se pasan paths/URLs, nunca blobs binarios
- **Backend ejecuta, Node-RED orquesta**: separación clara cliente-servidor
- **Sin over-engineering**: la mínima complejidad necesaria para el pipeline actual

---

## Infraestructura

| Componente | Descripción |
|---|---|
| Raspberry Pi 3B | Hardware de producción (ioi.local, 192.168.0.39) |
| Python 3 (sistema) | Backend Flask, sin venv |
| picamera2 | Driver de cámara principal (Pi) |
| OpenCV | Fallback para desarrollo en Mac |
| Node-RED 4.x | Frontend visual (puerto 1880) |
| Flask | Backend REST API (puerto 5001) |

---

## Estructura del repositorio

```
backend/
  app.py              — Flask app, registro de blueprints, CORS, stream, /view
  context.py          — Singletons compartidos (camera, mqtt)
  config.py           — Configuración global, to_http_path()
  run.py              — Entrypoint: inicia cámara, MQTT, Flask

  devices/
    camera.py         — SmartCamera: picamera2 + OpenCV fallback, ring buffer

  models/
    frame.py          — Frame (frame_id, image_path, metadata)
    tile.py           — Tile (grid position, frames, calibración)
    project.py        — OrthoProject (tiles, grid_spec, mosaico)

  storage/
    manager.py        — ProjectManager: CRUD de proyectos en disco

  blocks/
    edge/             — Bloques que ejecutan en la Pi
      capture.py      — CaptureFrame, CaptureBurst, CaptureZStack
      calibration.py  — ApplyDarkFrame, ApplyFlatField, ApplyLensCorrection
      quality.py      — QualityCheck (sharpness, exposición, saturación)
      preview.py      — GeneratePreview (JPEG thumbnail desde TIFF)
    server/           — Adaptadores para backends externos
      base.py         — ServerBackend (interfaz abstracta)
      generic.py      — GenericHTTPBackend
      fiji.py         — FijiBackend (stub)
      comfyui.py      — ComfyUIBackend
    project/          — Ciclo de vida de proyectos
      create.py       — CreateProject
      append.py       — AppendFrame
      load.py         — LoadProject

  api/
    capture.py        — Blueprint /api/capture/*
    blocks.py         — Blueprint /api/blocks/*
    project.py        — Blueprint /api/project/*

node-red/
  flow.json           — Flujo principal (se despliega automáticamente con deploy.sh)

projects/             — Almacenamiento en Pi (excluido del repo)
  <project_id>/
    raw/              — TIFF maestros (nunca modificar)
    corrected/        — TIFF tras calibración
    tiles/            — Teselas para el mosaico
    thumbnails/       — JPEG previews
    metadata/
    logs/
```

---

## API REST

### Captura

```
POST /api/capture/frame
  body: { "project_id": "nombre" }
  response: { "ok": true, "frame": { "frame_id": "frame_a3f7c901", "image_path": "...", "http_path": "..." } }

POST /api/capture/burst
  body: { "project_id": "nombre", "n": 5 }
```

### Bloques de procesamiento

```
POST /api/blocks/preview
  body: { "image_path": "/abs/path/frame.tiff", "max_size": 800, "quality": 90 }
  response: { "ok": true, "http_path": "/files/project/thumbnails/frame.jpg" }

POST /api/blocks/quality
POST /api/blocks/calibration/dark
POST /api/blocks/calibration/flat
POST /api/blocks/calibration/lens
```

### Proyectos

```
POST /api/project/create      — crea un OrthoProject en disco
GET  /api/project/list        — lista proyectos existentes
GET  /api/project/<id>        — carga un proyecto
POST /api/project/<id>/tile   — añade una tesela
```

### Utilidades

```
GET  /stream          — MJPEG stream en vivo
GET  /view            — Página HTML simple (stream + capture)
GET  /files/<path>    — Sirve archivos del directorio projects/
GET  /api/health      — Estado del sistema
```

---

## Flujo de datos: captura de frame

```
Node-RED
  [Set Project] ──→ global.project_id = "nombre"
  [Capture Frame]
       │
       ▼
  POST /api/capture/frame  { project_id }
       │
       ▼  Backend Flask
  CaptureFrame.run()
    ├─ camera.capture_still() → TIFF en projects/<id>/raw/frame_<hex>.tiff
    └─ devuelve Frame { frame_id, image_path, http_path }
       │
       ▼
  POST /api/blocks/preview  { image_path }
       │
       ▼
  GeneratePreview.run()
    └─ JPEG en projects/<id>/thumbnails/frame_<hex>.jpg
       │
       ▼
  GET /files/<project>/thumbnails/frame_<hex>.jpg  (buffer binario)
       │
       ▼
  Node-RED [image] → preview en el canvas
```

---

## Fases del proyecto

| Fase | Estado | Descripción |
|---|---|---|
| 1 | **Completa** | Captura de frame, preview en Node-RED |
| 2 | Pendiente | Iluminación I2C + captura de teselas |
| 3 | Pendiente | Registro espacial + ortomosaico |
| 4 | Pendiente | Superresolución (redundancia subpíxel) |
| 5 | Pendiente | Focus stacking (redundancia axial) |
| 6 | Pendiente | Pirámides gigapíxel |
| 7 | Pendiente | Integración IA externa (ComfyUI, Fiji) |

---

## Deploy

```bash
./deploy.sh ioi.local
```

Sincroniza código, instala dependencias Python, despliega `flow.json` a Node-RED y reinicia el servicio. La clave SSH debe estar en `~/.ssh/id_ed25519_ioi`.

Para arrancar el backend en la Pi:
```bash
ssh -i ~/.ssh/id_ed25519_ioi lino@ioi.local
cd ~/IOI && python3 run.py
```
