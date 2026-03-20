from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_id() -> str:
    return f"proj_{uuid.uuid4().hex[:8]}"


@dataclass
class OrthoProject:
    """
    Top-level work unit: a collection of calibrated tiles
    that will be assembled into a gigapixel orthoimage.
    Persisted as project.json inside the project directory.
    """
    project_id: str = field(default_factory=_project_id)
    name: str = ''
    created_at: str = field(default_factory=_now)
    tile_ids: List[str] = field(default_factory=list)
    grid_spec: dict = field(default_factory=dict)   # rows, cols, overlap_pct
    capture_params: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    orthomosaic_path: Optional[str] = None
    pyramid_path: Optional[str] = None
    status: str = 'open'  # open | processing | complete

    def to_dict(self) -> dict:
        return {
            'project_id': self.project_id,
            'name': self.name,
            'created_at': self.created_at,
            'tile_ids': self.tile_ids,
            'grid_spec': self.grid_spec,
            'capture_params': self.capture_params,
            'metadata': self.metadata,
            'orthomosaic_path': self.orthomosaic_path,
            'pyramid_path': self.pyramid_path,
            'status': self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'OrthoProject':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
