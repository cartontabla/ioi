import cv2
import numpy as np


class QualityCheck:
    """
    Run quality metrics on a captured frame.
    Returns a report with sharpness, exposure, and saturation indicators.
    Does not modify any file.
    """

    def run(self, image_path: str, thresholds: dict = None) -> dict:
        thresholds = thresholds or {}
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return {'ok': False, 'reason': 'cannot-read-image'}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        mean_brightness = float(gray.mean())
        overexposed_pct = float((gray > 250).mean() * 100)
        underexposed_pct = float((gray < 5).mean() * 100)

        min_sharpness = thresholds.get('min_sharpness', 50.0)
        max_overexposed = thresholds.get('max_overexposed_pct', 5.0)
        max_underexposed = thresholds.get('max_underexposed_pct', 5.0)

        issues = []
        if sharpness < min_sharpness:
            issues.append('blurry')
        if overexposed_pct > max_overexposed:
            issues.append('overexposed')
        if underexposed_pct > max_underexposed:
            issues.append('underexposed')

        status = 'ok' if not issues else 'rejected'
        return {
            'ok': True,
            'status': status,
            'issues': issues,
            'metrics': {
                'sharpness': sharpness,
                'mean_brightness': mean_brightness,
                'overexposed_pct': overexposed_pct,
                'underexposed_pct': underexposed_pct,
            },
        }
