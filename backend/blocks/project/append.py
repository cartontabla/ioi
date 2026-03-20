from backend.models.tile import Tile
from backend.storage.manager import ProjectManager


class AppendTile:
    """Append a calibrated Tile to an existing OrthoProject."""

    def run(self, manager: ProjectManager, tile: Tile) -> dict:
        project = manager.append_tile(tile.project_id, tile)
        if project is None:
            return {'ok': False, 'reason': 'project-not-found'}
        return {'ok': True, 'project_id': project.project_id, 'tile_count': len(project.tile_ids)}
