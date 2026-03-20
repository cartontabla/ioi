# Arquitectura de Smart Camera (modelo OSI-like)

## Principios de diseño
- **Modularidad tipo LEGO**: cada pieza colabora desde independencia absoluta
- **Interfaces bien definidas**: cada capa exporta solo lo que necesita
- **Referencias, no datos**: entre componentes se pasan URLs/paths, no blobs binarios
- **Backend ejecuta, Node-RED orquesta**: separación clara MVC + cliente-servidor

## Capas (modelo OSI inspirado)

### Capa 1: Adquisición (Physical)
**Responsabilidad**: capturar fotogramas del sensor

**Componentes**:
- `SmartCamera` (backend/camera.py)
  - Intenta usar `picamera.PiCamera` en Raspberry Pi
  - Fallback a `cv2.VideoCapture(0)` si no está disponible
  - Mantiene ring buffer en memoria para redundancia

**Interfaz saliente**:
```python
camera = SmartCamera()
camera.start()              # inicia thread de captura
frame = camera.get_frame()  # obtiene último fotograma (bytes JPEG)
path = camera.capture_image('/path/to/file.jpg')  # guarda a archivo
camera.stop()
```

---

### Capa 2: Almacenamiento (Data Link)
**Responsabilidad**: persistencia de archivos y referencias

**Componentes**:
- Directorio `storage/` (control local)
- Endpoint Flask `GET /files/<filename>` (servicio HTTP)

**Interfaz saliente**:
```http
GET /files/capture_20260320T120000_000000.jpg
# Respuesta: binary JPEG data
```

---

### Capa 3: Procesamiento (Network)
**Responsabilidad**: filtros, fusión, enhancements (futuro)

**Componentes planeados**:
- `ImageProcessor` (fusión HDR, denoise, stacking)
- Endpoints como `POST /api/process` que aceptan `{"input_file": "...", "operation": "hdr"}`

**Interfaz saliente**:
```python
processor.fuse_hdr([file1, file2, file3])  # → output_file
processor.denoise(input_file)              # → output_file
```

---

### Capa 4: Control & Orquestación (Transport)
**Responsabilidad**: coordinación entre capas y componentes

**Componentes**:
- `MQTTClient` (backend/mqtt_client.py) — eventos y comandos
- Flask REST (backend/server.py) — APIs síncronas

**Interfaz saliente**:
```python
# MQTT (pub)
mqtt.publish('camera/event', json.dumps({
  'event': 'capture_saved',
  'filename': 'capture_...jpg',
  'path': '/files/capture_...jpg'
}))

# REST (GET/POST)
POST /api/capture        → {"ok": true, "path": "/files/...", "filename": "..."}
POST /api/start
POST /api/stop
```

---

### Capa 5: Sesión & Estado (Session)
**Responsabilidad**: gestión de estado de flujos Node-RED

**Componentes**:
- Node-RED context (almacén de estado por flujo)
- Persistencia: archivos JSON en `/data/contexts` (Node-RED)

**Interfaz saliente**:
```javascript
// Dentro de nodo Node-RED
context.set('last_capture', msg.payload.filename);
var last = context.get('last_capture');
```

---

### Capa 6: Presentación (Presentation)
**Responsabilidad**: formateo de datos, UI

**Componentes**:
- Nodos `json` (parse/stringify MQTT)
- Nodos `http request` (fetch images)
- Dashboards Node-RED (ui-dashboard)

**Interfaz saliente**:
```javascript
// JSON parse/stringify
msg.payload = JSON.parse(msg.payload);  // MQTT → JSON
msg.payload = JSON.stringify(msg.payload);
```

---

### Capa 7: Aplicación (Application)
**Responsabilidad**: flujos de usuario, lógica de negocio

**Componentes**:
- Flujo Node-RED principal (`node-red/flow.json`)
  - Trigger captura → POST /api/capture
  - Escuchar MQTT events → GET /files/{filename} → save to /tmp/
  - Dashboard: mostrar imágenes, historiales

**Interfaz saliente**:
```
[Inject] → [HTTP POST capture] → [MQTT listener] → [HTTP GET file] → [File write] → [Dashboard]
```

---

## Flujo de datos: captura simple

```
┌─────────────────────────────────────────────────────────────────┐
│ Node-RED (Capa 7: Aplicación)                                   │
├─────────────────────────────────────────────────────────────────┤
│ [Trigger inject] ────→ [HTTP POST /api/capture]                │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend Flask (Capa 6: Presentación + Capa 4: Transporte)      │
├─────────────────────────────────────────────────────────────────┤
│ POST /api/capture:                                              │
│   ├─ SmartCamera.capture_image() [Capa 1]                       │
│   ├─ guardar en storage/ [Capa 2]                               │
│   └─ publish MQTT {"path": "/files/..."} [Capa 4]               │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Node-RED (Capa 7)                                               │
├─────────────────────────────────────────────────────────────────┤
│ [MQTT listener] ← {"path": "/files/..."}                       │
│       ↓                                                          │
│ [HTTP GET /files/{filename}] ← binario JPEG [Capa 2]           │
│       ↓                                                          │
│ [File writer] → /tmp/capture.jpg                                │
│       ↓                                                          │
│ [Dashboard] → visualizar                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Extensibilidad futura: backends remotos

### Ej: ComfyUI para procesamiento de imagen

**Capa 3 mejorada**:
```python
# backend/processors/comfyui.py
class ComfyUIProcessor:
    def __init__(self, url='http://comfyui-server:8188'):
        self.url = url
    
    def upscale(self, input_file):
        # 1. upload input_file → ComfyUI
        # 2. run workflow (upscale)
        # 3. download → output_file (en storage/)
        # 4. retornar path relativo
        return output_file
```

**Nuevo endpoint**:
```
POST /api/process
{
  "input": "capture_...jpg",
  "backend": "comfyui",
  "operation": "upscale"
}
→ {"ok": true, "output": "/files/capture_..._upscaled.jpg"}
```

**Node-RED lo consume igual**:
```
[Trigger] → [POST /api/process] → [MQTT event] → [HTTP GET] → [Display]
```

---

## Principios de comunicación inter-capas

1. **MQTT (pub/sub)**:
   - Eventos de bajo nivel (cámara iniciada, captura hecha)
   - Payloads JSON (sin datos binarios)
   - Bueno para: logging, triggers, coordinación async

2. **REST/HTTP (req/resp)**:
   - Comandos síncronos (capturar, procesar)
   - Archivos binarios (imágenes, streams)
   - Bueno para: operaciones que retornan resultado

3. **Context/Estado (Node-RED)**:
   - Persistencia local de flujo
   - Cachés, flags, metadatos
   - Bueno para: correlacionar eventos, guardar historial

---

## Checklist de independencia

Para que una nueva capa/componente sea "LEGO-compatible":

- [ ] Define entrada/salida clara (API)
- [ ] No accede directamente a capas no adyacentes
- [ ] Manejo de errores robusto (fallbacks)
- [ ] Testeable en aislamiento
- [ ] Documentado con ejemplos

---

## Ejemplos de futuros módulos

- **Capa 1+**: Sensores adicionales (temperature, luz, distancia)
- **Capa 3**: ML inference (object detection, face recognition)
- **Capa 5**: Persistencia de metadatos en BD (InfluxDB, SQLite)
- **Capa 7**: Webhooks HTTP para notificaciones externas

Cada uno sigue el mismo patrón de interfaces limpias y referencias.
