from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _frame_id() -> str:
    return f"frame_{uuid.uuid4().hex[:8]}"


@dataclass
class Frame:
    """
    Elemental capture unit: a single raw image from the sensor.
    Immutable once created — the pipeline never modifies the original.
    """
    frame_id: str = field(default_factory=_frame_id)
    project_id: Optional[str] = None
    tile_id: Optional[str] = None
    image_path: Optional[str] = None
    timestamp: str = field(default_factory=_now)
    camera_metadata: dict = field(default_factory=dict)
    capture_params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'frame_id': self.frame_id,
            'project_id': self.project_id,
            'tile_id': self.tile_id,
            'image_path': self.image_path,
            'timestamp': self.timestamp,
            'camera_metadata': self.camera_metadata,
            'capture_params': self.capture_params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Frame':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
