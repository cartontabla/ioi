# Changelog

## Fase 1 — Captura y preview en Node-RED

### Arquitectura base
- Reestructuración completa del proyecto: de monolito (`server.py`) a arquitectura modular con Flask blueprints
- Separación en capas: `devices/`, `models/`, `storage/`, `blocks/`, `api/`
- Singletons compartidos en `context.py` para evitar imports circulares
- `config.py` centraliza toda la configuración y expone `to_http_path()` para convertir paths absolutos a URLs HTTP

### Cámara
- `backend/devices/camera.py`: picamera2 como driver principal, OpenCV como fallback para desarrollo en Mac
- Ring buffer en memoria para acceso rápido al último frame
- `capture_still()` guarda siempre en TIFF (pipeline no destructivo)
- MJPEG stream en vivo en `/stream`

### Modelos de datos
- `Frame`: unidad mínima de captura (frame_id, image_path, metadata de cámara)
- `Tile`: agrupación de frames para una posición de la rejilla
- `OrthoProject`: proyecto completo con grid_spec, tiles, rutas de mosaico y pirámide

### Storage
- `ProjectManager`: CRUD de proyectos en disco, crea estructura de directorios (`raw/`, `corrected/`, `tiles/`, `thumbnails/`, `metadata/`, `logs/`)
- Proyectos sin asignar van a `projects/unsorted/raw/`

### Bloques edge
- `CaptureFrame`, `CaptureBurst`: captura simple y ráfaga
- `GeneratePreview`: genera JPEG thumbnail desde TIFF maestro
- `QualityCheck`: métricas de sharpness (varianza Laplaciana), exposición, saturación
- `ApplyDarkFrame`, `ApplyFlatField`, `ApplyLensCorrection`: calibración no destructiva

### Bloques server
- Interfaz abstracta `ServerBackend` con patrón submit/poll/collect
- `GenericHTTPBackend`, `ComfyUIBackend`, `FijiBackend` (stub)

### Node-RED
- Flujo `node-red/flow.json` con nodos estándar únicamente (inject, function, http request, image)
- Pipeline: Set Project → Capture Frame → POST capture → POST preview → GET image → nodo image
- El nodo `image` (node-red-contrib-image-output) muestra el preview directamente en el canvas
- `global.project_id` controla en qué proyecto se guardan las capturas
- `global.backend_url` centraliza la URL del backend

### Deploy
- `deploy.sh`: sincroniza código vía rsync, instala deps Python, copia `flow.json` a `~/.node-red/flows.json` y reinicia Node-RED automáticamente
- SSH con clave `~/.ssh/id_ed25519_ioi` (sin contraseña)

### Fixes aplicados
- `BASE_DIR` apuntaba dos niveles arriba: corregido
- Puerto inconsistente 5000/5001: unificado en 5001
- `MQTTClient.subscribe` sobreescribía el `on_message` global: corregido con `message_callback_add`
- `backend/__init__.py` con imports obsoletos: vaciado
- Dashboard Node-RED con nodo `ui_base` duplicado al importar: descartado en favor del nodo `image` en el canvas
- `deploy.sh` no usaba clave SSH: corregido con `-i ~/.ssh/id_ed25519_ioi`

---

## Fase 2 — Iluminación + Calibración + Settings

### Iluminación I2C (PCA9685)

- `backend/devices/lighting.py`: `LightingController` con smbus2 directo (sin librería externa)
- 4 grupos de LEDs (3 por grupo, canales intercalados): visible (0,4,8), polarized (1,5,9), ir (2,6,10), uv (3,7,11)
- `backend/api/lighting.py`: blueprint `/api/lighting/on` y `/api/lighting/off`
- Parámetros: `group` (visible|polarized|ir|uv|all), `intensity` (0–100%), `warmup_ms`
- Flujo Node-RED `IOI / Capture + Lighting`: ON → warmup → capture → OFF → preview

### Calibración

- `backend/api/calibration.py`: endpoints `/api/calibration/dark/capture` y `/api/calibration/flat/capture`
- Captura N frames a máxima resolución y los promedia → TIFF en `projects/<id>/calibration/`
- Flat field enciende/apaga iluminación automáticamente desde Node-RED
- Flujo `IOI / Calibration / Dark Frame`: tapa el objetivo → captura
- Flujo `IOI / Calibration / Flat Field`: iluminación automática → superficie uniforme → captura
- Flujo `IOI / Calibration / Apply`: aplica dark + flat en secuencia con preview comparativo (original vs corregido)

### Resolución de captura

- Stream en vivo: 640×480 (para enfoque manual)
- Captura still: 4056×3040 (máxima resolución IMX477) via `switch_mode_and_capture_array`
- Calibración burst: N capturas still individuales a máxima resolución
- `config.py`: nuevo parámetro `CAPTURE_RESOLUTION` (por defecto 4056×3040)

### Preview con flag full_res

- Endpoint `/api/blocks/preview`: acepta `full_res: true/false`
- `full_res: false` → thumbnail 800px (rápido)
- `full_res: true` → resolución original del TIFF
- Flujo `IOI / Preview`: toggle global que afecta a todos los flujos de captura

### Settings de cámara

- Flujo `IOI / Settings`: parámetros en JSON con toggle auto/manual
- Exposición (`AeEnable`, `ExposureTime`), gain (`AnalogueGain`), balance de blancos (`AwbEnable`, `ColourGains`)
- Resolución y framerate del stream

### Deploy mejorado

- `deploy.sh`: ahora reinicia también el backend Python (no solo Node-RED)
- SSH con clave `~/.ssh/id_ed25519_ioi` en todos los comandos

### Organización Node-RED

- Pestañas con prefijo `IOI /` para agrupación visual
- Nodos comment con rangos y valores posibles en cada flujo
- Flujos independientes: Capture, Capture+Lighting, Calibration/*, Settings, Preview

---

## Fase 3 — Controls, deploy y UX

### IOI/Settings — controles de cámara ampliados

- Añadidos controles de picamera2 a la función Translate:
  - `ev` → `ExposureValue` (-8.0 a +8.0, compensación de exposición con AE activo)
  - `awb_mode` → `AwbMode` (Auto/Tungsten/Fluorescent/Indoor/Daylight/Cloudy)
  - `metering_mode` → `AeMeteringMode` (CentreWeighted/Spot/Matrix)
  - `noise_reduction` → `NoiseReductionMode` (Off/Fast/HighQuality)
- Bug fix: `gain_auto=false` sobreescribía `AeEnable=false` incorrectamente — ahora `AnalogueGain` es independiente del AE
- Payload del inject actualizado con todos los nuevos campos y defaults

### IOI/Capture + Lighting — toggle de preview

- Añadidos dos inject nodes: **Thumbnail (800px)** y **Full Resolution**
- El nodo "Prepare Preview" ahora respeta la variable global `preview_full_res`
- Permite cambiar el modo de preview sin hacer deploy

### Limpieza de flujos

- Eliminada pestaña **IOI/Preview** (innecesaria — la variable `preview_full_res` tiene `|| false` como fallback en todos los nodos que la leen)

### Deploy mejorado (sesión anterior)

- `ioi-backend.service`: servicio systemd para gestión del backend Python en la Pi
- `deploy.sh`: ahora usa `systemctl restart ioi-backend` en lugar de `nohup` — soluciona el cuelgue causado por los file descriptors de libcamera/picamera2
- Health check corre desde el Mac directamente (`curl http://${PI_HOST}:5001/api/health`) en lugar de via SSH

---

## Pendiente — Fase 4

- Calibración de lente (tablero de ajedrez + OpenCV)
- Calibración de color (ColorChecker)
- Captura de teselas + grid OrthoProject
- Registro espacial + ortomosaico
