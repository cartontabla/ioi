from backend.storage.manager import ProjectManager


class LoadProject:
    """Load an existing OrthoProject from disk."""

    def run(self, manager: ProjectManager, project_id: str) -> dict:
        project = manager.load(project_id)
        if project is None:
            return {'ok': False, 'reason': 'project-not-found'}
        return {'ok': True, 'project': project.to_dict()}
