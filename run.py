from backend.app import app
from backend.context import camera, mqtt
import config

if __name__ == '__main__':
    try:
        camera.start()
        if config.ENABLE_MQTT:
            mqtt.connect()
        app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
    except KeyboardInterrupt:
        camera.stop()
        print('Shutting down')
