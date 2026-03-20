import json
from pathlib import Path
from flask import Blueprint, jsonify, request, Response
import config

bp = Blueprint('capture', __name__)


def _camera():
    from backend.context import camera
    return camera


def _mqtt():
    from backend.context import mqtt
    return mqtt


@bp.route('/api/capture/frame', methods=['POST'])
def capture_frame():
    """Capture a single still frame and save as TIFF."""
    from backend.blocks.edge.capture import CaptureFrame
    from backend.models.frame import Frame

    j = request.get_json(silent=True) or {}
    project_id = j.get('project_id')

    if project_id:
        output_dir = Path(config.PROJECTS_DIR) / project_id / 'raw'
    else:
        output_dir = Path(config.PROJECTS_DIR) / 'unsorted' / 'raw'

    result = CaptureFrame().run(_camera(), output_dir, params=j)

    if result['ok'] and config.ENABLE_MQTT:
        _mqtt().publish('camera/result/frame_ready', json.dumps({
            'frame_id': result['frame']['frame_id'],
            'path': result['frame']['image_path'],
            'project_id': project_id,
        }))

    return jsonify(result), 200 if result['ok'] else 503


@bp.route('/api/capture/burst', methods=['POST'])
def capture_burst():
    """Capture N frames from the ring buffer and save as TIFFs."""
    from backend.blocks.edge.capture import CaptureBurst

    j = request.get_json(silent=True) or {}
    project_id = j.get('project_id')
    n = int(j.get('n', 5))

    if project_id:
        output_dir = Path(config.PROJECTS_DIR) / project_id / 'raw'
    else:
        output_dir = Path(config.PROJECTS_DIR) / 'unsorted' / 'raw'

    result = CaptureBurst().run(_camera(), output_dir, n=n, params=j)
    return jsonify(result), 200 if result['ok'] else 503


@bp.route('/api/capture/start', methods=['POST'])
def start():
    cam = _camera()
    if cam.running:
        return jsonify({'ok': False, 'reason': 'already-running'}), 400
    cam.start()
    if config.ENABLE_MQTT:
        _mqtt().publish('camera/state/status', json.dumps({'status': 'running'}))
    return jsonify({'ok': True})


@bp.route('/api/capture/stop', methods=['POST'])
def stop():
    cam = _camera()
    if not cam.running:
        return jsonify({'ok': False, 'reason': 'not-running'}), 400
    cam.stop()
    if config.ENABLE_MQTT:
        _mqtt().publish('camera/state/status', json.dumps({'status': 'stopped'}))
    return jsonify({'ok': True})


@bp.route('/api/capture/controls', methods=['POST'])
def set_controls():
    """Set camera controls: ExposureTime, AnalogueGain, AwbMode, etc."""
    j = request.get_json(silent=True) or {}
    _camera().set_controls(j)
    return jsonify({'ok': True, 'controls': j})


@bp.route('/api/capture/settings', methods=['POST'])
def settings():
    """Change resolution/framerate — restarts the capture thread."""
    j = request.get_json(silent=True) or {}
    cam = _camera()
    changed = False
    if 'framerate' in j:
        cam.framerate = int(j['framerate'])
        changed = True
    if 'resolution' in j:
        cam.resolution = tuple(j['resolution'])
        changed = True
    if changed and cam.running:
        cam.stop()
        cam.start()
    return jsonify({'ok': True, 'settings': {'framerate': cam.framerate, 'resolution': cam.resolution}})


@bp.route('/api/health')
def health():
    return jsonify(_camera().health_check())
