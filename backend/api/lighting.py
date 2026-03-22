from flask import Blueprint, request, jsonify
from backend.context import lighting

bp = Blueprint('lighting', __name__)


@bp.route('/api/lighting/on', methods=['POST'])
def light_on():
    j = request.get_json(silent=True) or {}
    group         = j.get('group', 'all')
    intensity_pct = float(j.get('intensity', 100))
    lighting.on(group=group, intensity_pct=intensity_pct)
    return jsonify(ok=True, group=group, intensity=intensity_pct)


@bp.route('/api/lighting/off', methods=['POST'])
def light_off():
    j = request.get_json(silent=True) or {}
    group = j.get('group', 'all')
    lighting.off(group=group)
    return jsonify(ok=True, group=group)


@bp.route('/api/lighting/status', methods=['GET'])
def light_status():
    return jsonify(ok=True, available=lighting.available)
