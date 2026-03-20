from flask import Blueprint, jsonify, request
from pathlib import Path
import config

bp = Blueprint('blocks', __name__)


@bp.route('/api/blocks/calibration/dark', methods=['POST'])
def apply_dark():
    from backend.blocks.edge.calibration import ApplyDarkFrame
    j = request.get_json(silent=True) or {}
    result = ApplyDarkFrame().run(
        input_path=j['input_path'],
        dark_path=j['dark_path'],
        output_dir=Path(j.get('output_dir', config.PROJECTS_DIR)),
    )
    return jsonify(result), 200 if result['ok'] else 500


@bp.route('/api/blocks/calibration/flat', methods=['POST'])
def apply_flat():
    from backend.blocks.edge.calibration import ApplyFlatField
    j = request.get_json(silent=True) or {}
    result = ApplyFlatField().run(
        input_path=j['input_path'],
        flat_path=j['flat_path'],
        dark_path=j.get('dark_path'),
        output_dir=Path(j.get('output_dir', config.PROJECTS_DIR)),
    )
    return jsonify(result), 200 if result['ok'] else 500


@bp.route('/api/blocks/calibration/lens', methods=['POST'])
def apply_lens():
    from backend.blocks.edge.calibration import ApplyLensCorrection
    j = request.get_json(silent=True) or {}
    result = ApplyLensCorrection().run(
        input_path=j['input_path'],
        calibration=j['calibration'],
        output_dir=Path(j.get('output_dir', config.PROJECTS_DIR)),
    )
    return jsonify(result), 200 if result['ok'] else 500


@bp.route('/api/blocks/quality', methods=['POST'])
def quality_check():
    from backend.blocks.edge.quality import QualityCheck
    j = request.get_json(silent=True) or {}
    result = QualityCheck().run(
        image_path=j['image_path'],
        thresholds=j.get('thresholds', {}),
    )
    return jsonify(result), 200 if result['ok'] else 500


@bp.route('/api/blocks/preview', methods=['POST'])
def generate_preview():
    from backend.blocks.edge.preview import GeneratePreview
    j = request.get_json(silent=True) or {}
    result = GeneratePreview().run(
        input_path=j['input_path'],
        output_dir=Path(j.get('output_dir', config.PROJECTS_DIR)),
        max_size=j.get('max_size', 512),
        quality=j.get('quality', 85),
    )
    return jsonify(result), 200 if result['ok'] else 500
