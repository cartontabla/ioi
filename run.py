from backend.server import app, camera, mqtt

if __name__ == '__main__':
    try:
        camera.start()
        mqtt.connect()
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        camera.stop()
        print('Shutting down')
