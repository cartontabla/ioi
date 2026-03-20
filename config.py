"""
Configuration for Smart Camera backend.
Supports environment variables and local overrides.
"""

import os
from datetime import datetime

# Environment detection
IS_RASPBERRY_PI = os.path.exists('/boot/firmware/config.txt') or os.path.exists('/boot/config.txt')
IS_HEADLESS = not os.environ.get('DISPLAY', '')

# ===== Camera Configuration =====
CAMERA_RESOLUTION = tuple(map(int, os.environ.get('CAMERA_RESOLUTION', '640,480').split(',')))
CAMERA_FRAMERATE = int(os.environ.get('CAMERA_FRAMERATE', '24'))
CAMERA_RING_SIZE = int(os.environ.get('CAMERA_RING_SIZE', '32'))
CAMERA_JPEG_QUALITY = int(os.environ.get('CAMERA_JPEG_QUALITY', '80'))

# Try PiCamera on RPi, fallback to OpenCV
USE_PICAMERA = IS_RASPBERRY_PI and os.environ.get('USE_PICAMERA', 'true').lower() == 'true'

# ===== MQTT Configuration =====
MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MQTT_CLIENT_ID = os.environ.get('MQTT_CLIENT_ID', 'smartcam')
MQTT_USERNAME = os.environ.get('MQTT_USERNAME', None)
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', None)
MQTT_TLS = os.environ.get('MQTT_TLS', 'false').lower() == 'true'

# ===== Flask Configuration =====
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', '5001'))  # 5000 = AirPlay on macOS
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

# ===== Storage Configuration =====
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECTS_DIR = os.environ.get('PROJECTS_DIR', os.path.join(BASE_DIR, 'projects'))
os.makedirs(PROJECTS_DIR, exist_ok=True)


def to_http_path(abs_path: str) -> str:
    """Convert an absolute file path to its /files/... HTTP URL path."""
    from pathlib import Path
    try:
        rel = Path(abs_path).relative_to(PROJECTS_DIR)
        return f"/files/{rel.as_posix()}"
    except ValueError:
        return None

# ===== Logging Configuration =====
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', None)  # None = stdout

# ===== Feature Flags =====
ENABLE_MJPEG_STREAM = os.environ.get('ENABLE_MJPEG_STREAM', 'true').lower() == 'true'
ENABLE_MQTT = os.environ.get('ENABLE_MQTT', 'true').lower() == 'true'
ENABLE_CORS = os.environ.get('ENABLE_CORS', 'true').lower() == 'true'

# ===== Advanced Options =====
PROCESSOR_BACKEND = os.environ.get('PROCESSOR_BACKEND', 'opencv')  # opencv, comfyui, fiji
PROCESSOR_HOST = os.environ.get('PROCESSOR_HOST', 'localhost')
PROCESSOR_PORT = int(os.environ.get('PROCESSOR_PORT', '8188'))

# ===== Development Helpers =====
def print_config():
    """Print current configuration (for debugging)."""
    import json
    config = {
        'environment': {
            'is_rpi': IS_RASPBERRY_PI,
            'is_headless': IS_HEADLESS,
        },
        'camera': {
            'resolution': CAMERA_RESOLUTION,
            'framerate': CAMERA_FRAMERATE,
            'use_picamera': USE_PICAMERA,
        },
        'mqtt': {
            'host': MQTT_HOST,
            'port': MQTT_PORT,
            'client_id': MQTT_CLIENT_ID,
        },
        'flask': {
            'host': FLASK_HOST,
            'port': FLASK_PORT,
            'debug': FLASK_DEBUG,
        },
        'storage': {
            'projects_dir': PROJECTS_DIR,
        },
    }
    print(json.dumps(config, indent=2))

if __name__ == '__main__':
    print_config()
