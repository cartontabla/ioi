from backend.server import app, camera, mqtt
import config

if __name__ == '__main__':
    try:
        camera.start()
        mqtt.connect()
        # Use config for port (default 5001 to avoid AirPlay on macOS)
        app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
    except KeyboardInterrupt:
        camera.stop()
        print('Shutting down')
