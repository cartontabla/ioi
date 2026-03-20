from pathlib import Path
from backend.models.frame import Frame


class CaptureFrame:
    """
    Capture a single still frame from the camera and save as TIFF.
    Non-destructive: always writes a new file, never overwrites.
    """

    def run(self, camera, output_dir: Path, params: dict = None) -> dict:
        params = params or {}
        frame = Frame(
            project_id=params.get('project_id'),
            tile_id=params.get('tile_id'),
            capture_params=params,
        )
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{frame.frame_id}.tiff"

        result = camera.capture_still(path=str(path))
        if result is None:
            return {'ok': False, 'reason': 'no-frame'}

        frame.image_path = str(path)
        frame.camera_metadata = camera.get_metadata()
        return {'ok': True, 'frame': frame.to_dict()}


class CaptureBurst:
    """
    Capture N frames in rapid succession (ring buffer) for superresolution/noise reduction.
    Returns paths to N saved TIFF files.
    """

    def run(self, camera, output_dir: Path, n: int = 5, params: dict = None) -> dict:
        params = params or {}
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        frames_data = camera.get_burst(n)
        if not frames_data:
            return {'ok': False, 'reason': 'no-frames'}

        import cv2
        saved = []
        for bgr in frames_data:
            frame = Frame(project_id=params.get('project_id'), capture_params=params)
            path = output_dir / f"{frame.frame_id}.tiff"
            cv2.imwrite(str(path), bgr)
            frame.image_path = str(path)
            saved.append(frame.to_dict())

        return {'ok': True, 'frames': saved, 'count': len(saved)}


class CaptureZStack:
    """
    Capture frames at different focus positions for focus stacking.
    Requires motorized focus control (future).
    Each step: move focus → capture frame → repeat.
    """

    def run(self, camera, focus_controller, output_dir: Path, steps: list, params: dict = None) -> dict:
        """
        steps: list of focus positions (e.g. [0, 10, 20, 30, 40])
        focus_controller: device with .set_position(pos) method (future)
        """
        raise NotImplementedError("Motorized focus control not yet implemented")
