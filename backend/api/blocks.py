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
    input_path = j['image_path']
    if 'output_dir' in j:
        output_dir = Path(j['output_dir'])
    else:
        output_dir = Path(input_path).parent.parent / 'thumbnails'
    full_res = j.get('full_res', False)
    max_size = 99999 if full_res else j.get('max_size', 800)
    result = GeneratePreview().run(
        input_path=input_path,
        output_dir=output_dir,
        max_size=max_size,
        quality=j.get('quality', 90),
    )
    if result['ok']:
        result['http_path'] = config.to_http_path(result['preview_path'])
    return jsonify(result), 200 if result['ok'] else 500
