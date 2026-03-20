from backend.models.project import OrthoProject
from backend.storage.manager import ProjectManager


class CreateProject:
    """Create a new OrthoProject and initialize its directory structure."""

    def run(self, manager: ProjectManager, params: dict) -> dict:
        project = manager.create(
            name=params.get('name', ''),
            metadata=params.get('metadata', {}),
            capture_params=params.get('capture_params', {}),
        )
        return {'ok': True, 'project': project.to_dict()}
