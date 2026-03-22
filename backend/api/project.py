from flask import Blueprint, jsonify, request
import config
from backend.storage.manager import ProjectManager
from backend.models.tile import Tile

bp = Blueprint('project', __name__)

_manager = None


def manager() -> ProjectManager:
    global _manager
    if _manager is None:
        _manager = ProjectManager(base_dir=config.PROJECTS_DIR)
    return _manager


@bp.route('/api/project/create', methods=['POST'])
def create():
    from backend.blocks.project.create import CreateProject
    j = request.get_json(silent=True) or {}
    result = CreateProject().run(manager(), j)
    return jsonify(result)


@bp.route('/api/project/list', methods=['GET'])
def list_projects():
    return jsonify({'ok': True, 'projects': manager().list_projects()})


@bp.route('/api/project/<project_id>', methods=['GET'])
def load(project_id):
    from backend.blocks.project.load import LoadProject
    result = LoadProject().run(manager(), project_id)
    return jsonify(result), 200 if result['ok'] else 404


@bp.route('/api/project/<project_id>/clean', methods=['POST'])
def clean(project_id):
    """Delete all files inside a project (raw, corrected, thumbnails) but keep the structure."""
    import shutil
    from pathlib import Path
    j = request.get_json(silent=True) or {}
    subdirs = j.get('subdirs', ['raw', 'corrected', 'thumbnails', 'tiles', 'logs'])
    project_dir = Path(config.PROJECTS_DIR) / project_id
    if not project_dir.exists():
        return jsonify({'ok': False, 'reason': 'project-not-found'}), 404
    cleaned = []
    for sub in subdirs:
        path = project_dir / sub
        if path.exists():
            shutil.rmtree(path)
            path.mkdir()
            cleaned.append(sub)
    return jsonify({'ok': True, 'project_id': project_id, 'cleaned': cleaned})


@bp.route('/api/project/<project_id>/tile', methods=['POST'])
def append_tile(project_id):
    from backend.blocks.project.append import AppendTile
    j = request.get_json(silent=True) or {}
    j['project_id'] = project_id
    tile = Tile.from_dict(j)
    result = AppendTile().run(manager(), tile)
    return jsonify(result), 200 if result['ok'] else 404
