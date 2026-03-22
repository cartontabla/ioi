"""
Shared singletons: camera and MQTT client.
Import from here in API blueprints to avoid circular imports.
Instantiated once at module load time.
"""
import config
from backend.devices.camera import SmartCamera
from backend.devices.lighting import LightingController
from backend.mqtt_interface import MQTTClient

camera = SmartCamera(
    resolution=config.CAMERA_RESOLUTION,
    framerate=config.CAMERA_FRAMERATE,
    ring_size=config.CAMERA_RING_SIZE,
    use_picamera=config.USE_PICAMERA,
    capture_resolution=config.CAPTURE_RESOLUTION,
)

lighting = LightingController()

mqtt = MQTTClient(
    host=config.MQTT_HOST,
    port=config.MQTT_PORT,
    client_id=config.MQTT_CLIENT_ID,
)
