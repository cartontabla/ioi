from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple, List
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tile_id() -> str:
    return f"tile_{uuid.uuid4().hex[:8]}"


@dataclass
class Tile:
    """
    Scientific capture unit: a calibrated, corrected image ready for mosaicking.
    Produced by the edge pipeline from one or more Frames.
    All paths are absolute. The pipeline never overwrites existing files.
    """
    tile_id: str = field(default_factory=_tile_id)
    project_id: Optional[str] = None
    image_path: Optional[str] = None        # master TIFF (lossless)
    preview_path: Optional[str] = None      # JPEG thumbnail
    frame_ids: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    calibration: dict = field(default_factory=dict)
    grid_position: Optional[Tuple[int, int]] = None  # (row, col)
    timestamp: str = field(default_factory=_now)
    status: str = 'pending'  # pending | ok | rejected

    def to_dict(self) -> dict:
        return {
            'tile_id': self.tile_id,
            'project_id': self.project_id,
            'image_path': self.image_path,
            'preview_path': self.preview_path,
            'frame_ids': self.frame_ids,
            'metadata': self.metadata,
            'calibration': self.calibration,
            'grid_position': list(self.grid_position) if self.grid_position else None,
            'timestamp': self.timestamp,
            'status': self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Tile':
        d = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if d.get('grid_position'):
            d['grid_position'] = tuple(d['grid_position'])
        return cls(**d)
