from flask import Flask, Response, request, jsonify, send_from_directory
import os
import json
from datetime import datetime

from backend.camera import SmartCamera
from backend.mqtt_client import MQTTClient
import config

app = Flask(__name__)

camera = SmartCamera(
    resolution=config.CAMERA_RESOLUTION,
    framerate=config.CAMERA_FRAMERATE,
    ring_size=config.CAMERA_RING_SIZE
)
mqtt = MQTTClient(
    host=config.MQTT_HOST,
    port=config.MQTT_PORT,
    client_id=config.MQTT_CLIENT_ID
)

STORAGE_DIR = config.STORAGE_DIR


@app.route('/stream')
def stream():
    return Response(camera.mjpeg_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/health')
def health():
    return jsonify(camera.health_check())


@app.route('/api/capture', methods=['POST'])
def capture():
    # Accept optional JSON like {"path": "custom/name.jpg"}
    j = request.get_json(silent=True) or {}
    fname = None
    if isinstance(j, dict) and j.get('path'):
        fname = os.path.basename(j.get('path'))
    else:
        fname = datetime.utcnow().strftime('capture_%Y%m%dT%H%M%S_%f.jpg')

    abs_path = os.path.join(STORAGE_DIR, fname)
    result = camera.capture_image(abs_path)
    if result is None:
        return jsonify({'ok': False, 'reason': 'no-frame'}), 503

    # Publish an MQTT JSON message with a stable path for clients
    payload = {
        'event': 'capture_saved',
        'filename': fname,
        # HTTP-accessible path (served by this Flask app)
        'path': f'/files/{fname}'
    }
    mqtt.publish('camera/event', json.dumps(payload))

    # Return the JSON with the path
    return jsonify({'ok': True, 'path': payload['path'], 'filename': fname})


@app.route('/api/start', methods=['POST'])
def api_start():
    if camera.running:
        return jsonify({'ok': False, 'reason': 'already-running'}), 400
    camera.start()
    mqtt.publish('camera/event', json.dumps({'event': 'started'}))
    return jsonify({'ok': True})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    if not camera.running:
        return jsonify({'ok': False, 'reason': 'not-running'}), 400
    camera.stop()
    mqtt.publish('camera/event', json.dumps({'event': 'stopped'}))
    return jsonify({'ok': True})


@app.route('/api/settings', methods=['POST'])
def settings():
    j = request.get_json(silent=True) or {}
    # Example: change framerate/resolution
    if 'framerate' in j:
        camera.framerate = int(j['framerate'])
    if 'resolution' in j:
        camera.resolution = tuple(j['resolution'])
    return jsonify({'ok': True, 'settings': {'framerate': camera.framerate, 'resolution': camera.resolution}})


@app.route('/files/<path:filename>')
def serve_file(filename):
    # Serve captured files from storage directory
    return send_from_directory(STORAGE_DIR, filename, as_attachment=False)


if __name__ == '__main__':
    # Minimal run for development
    camera.start()
    mqtt.connect()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
