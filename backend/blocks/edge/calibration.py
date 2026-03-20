from pathlib import Path
import numpy as np
import cv2


class ApplyDarkFrame:
    """
    Subtract a dark frame (sensor noise, hot pixels) from a raw image.
    Non-destructive: writes result to a new file in output_dir.
    """

    def run(self, input_path: str, dark_path: str, output_dir: Path) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        src = cv2.imread(input_path, cv2.IMREAD_UNCHANGED).astype(np.float32)
        dark = cv2.imread(dark_path, cv2.IMREAD_UNCHANGED).astype(np.float32)
        corrected = np.clip(src - dark, 0, None).astype(src.dtype)

        stem = Path(input_path).stem
        out_path = output_dir / f"{stem}_dark.tiff"
        cv2.imwrite(str(out_path), corrected)
        return {'ok': True, 'output_path': str(out_path)}


class ApplyFlatField:
    """
    Apply flat-field correction to normalize sensor response and illumination uniformity.
    Non-destructive: writes result to a new file in output_dir.
    """

    def run(self, input_path: str, flat_path: str, dark_path: str, output_dir: Path) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        src = cv2.imread(input_path, cv2.IMREAD_UNCHANGED).astype(np.float32)
        flat = cv2.imread(flat_path, cv2.IMREAD_UNCHANGED).astype(np.float32)
        dark = cv2.imread(dark_path, cv2.IMREAD_UNCHANGED).astype(np.float32) if dark_path else np.zeros_like(flat)

        flat_corr = flat - dark
        flat_mean = flat_corr.mean()
        corrected = np.clip((src - dark) * (flat_mean / (flat_corr + 1e-6)), 0, None).astype(src.dtype)

        stem = Path(input_path).stem
        out_path = output_dir / f"{stem}_flat.tiff"
        cv2.imwrite(str(out_path), corrected)
        return {'ok': True, 'output_path': str(out_path)}


class ApplyLensCorrection:
    """
    Apply geometric lens distortion correction using a calibration map.
    Non-destructive: writes result to a new file in output_dir.
    """

    def run(self, input_path: str, calibration: dict, output_dir: Path) -> dict:
        """
        calibration: dict with 'camera_matrix' and 'dist_coeffs' (OpenCV format).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        src = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        h, w = src.shape[:2]

        K = np.array(calibration['camera_matrix'], dtype=np.float64)
        D = np.array(calibration['dist_coeffs'], dtype=np.float64)
        K_new, roi = cv2.getOptimalNewCameraMatrix(K, D, (w, h), alpha=1)
        corrected = cv2.undistort(src, K, D, None, K_new)

        stem = Path(input_path).stem
        out_path = output_dir / f"{stem}_lens.tiff"
        cv2.imwrite(str(out_path), corrected)
        return {'ok': True, 'output_path': str(out_path), 'roi': roi}
