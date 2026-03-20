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


@bp.route('/api/project/<project_id>/tile', methods=['POST'])
def append_tile(project_id):
    from backend.blocks.project.append import AppendTile
    j = request.get_json(silent=True) or {}
    j['project_id'] = project_id
    tile = Tile.from_dict(j)
    result = AppendTile().run(manager(), tile)
    return jsonify(result), 200 if result['ok'] else 404
