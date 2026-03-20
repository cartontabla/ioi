from pathlib import Path
import cv2


class GeneratePreview:
    """
    Generate a JPEG thumbnail from a TIFF master.
    Non-destructive: always writes to thumbnails/ dir, never touches the master.
    """

    def run(self, input_path: str, output_dir: Path, max_size: int = 512, quality: int = 85) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return {'ok': False, 'reason': 'cannot-read-image'}

        h, w = img.shape[:2]
        scale = min(max_size / w, max_size / h, 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        stem = Path(input_path).stem
        out_path = output_dir / f"{stem}_preview.jpg"
        cv2.imwrite(str(out_path), img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return {'ok': True, 'preview_path': str(out_path), 'size': (img.shape[1], img.shape[0])}
