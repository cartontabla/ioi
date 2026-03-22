from flask import Blueprint, jsonify, request
from pathlib import Path
import numpy as np
import cv2
import config

bp = Blueprint('calibration', __name__)


def _camera():
    from backend.context import camera
    return camera


def _capture_and_average(n: int, output_path: Path) -> dict:
    """Capture N full-resolution stills, average them, save as TIFF."""
    cam = _camera()
    frames = []
    for _ in range(n):
        frame = cam.capture_still()
        if frame is not None:
            frames.append(frame.astype(np.float32))

    if not frames:
        return {'ok': False, 'reason': 'no-frames'}

    stack = np.stack(frames, axis=0)
    averaged = np.mean(stack, axis=0).astype(np.uint16)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), averaged)
    return {'ok': True, 'path': str(output_path), 'frames_averaged': len(frames)}


@bp.route('/api/calibration/dark/capture', methods=['POST'])
def capture_dark():
    """Capture N frames with lens covered and average → dark_frame.tiff."""
    j = request.get_json(silent=True) or {}
    project_id = j.get('project_id', 'calibration')
    n = int(j.get('n', 10))
    output_path = Path(config.PROJECTS_DIR) / project_id / 'calibration' / 'dark_frame.tiff'
    result = _capture_and_average(n, output_path)
    if result['ok']:
        result['http_path'] = config.to_http_path(str(output_path))
    return jsonify(result), 200 if result['ok'] else 503


@bp.route('/api/calibration/flat/capture', methods=['POST'])
def capture_flat():
    """Capture N frames pointing at uniform surface and average → flat_frame.tiff."""
    j = request.get_json(silent=True) or {}
    project_id = j.get('project_id', 'calibration')
    n = int(j.get('n', 10))
    output_path = Path(config.PROJECTS_DIR) / project_id / 'calibration' / 'flat_frame.tiff'
    result = _capture_and_average(n, output_path)
    if result['ok']:
        result['http_path'] = config.to_http_path(str(output_path))
    return jsonify(result), 200 if result['ok'] else 503
