import time
from collections import deque
from threading import Lock, Thread
from typing import Optional, List

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False

import cv2
import numpy as np


class SmartCamera:
    """
    Camera abstraction for scientific capture.
    Primary: picamera2 (Raspberry Pi).
    Fallback: OpenCV (Mac/Linux development).

    Frames are stored internally as BGR numpy arrays.
    The ring buffer supports burst and redundancy capture.
    JPEG output is only used for streaming previews — never for archival.
    """

    def __init__(self, resolution=(640, 480), framerate=24, ring_size=32, use_picamera=True,
                 capture_resolution=(4056, 3040)):
        self.resolution = resolution
        self.capture_resolution = capture_resolution
        self.framerate = framerate
        self.ring = deque(maxlen=ring_size)
        self.latest_frame: Optional[np.ndarray] = None
        self.lock = Lock()
        self._cam_lock = Lock()  # serializes camera access between stream loop and still capture
        self.running = False
        self.source: Optional[str] = None
        self._thread: Optional[Thread] = None
        self._use_picamera = use_picamera
        self._cam = None  # Picamera2 instance

    # ------------------------------------------------------------------ start/stop

    def start(self):
        if self.running:
            return
        self.running = True
        if PICAMERA2_AVAILABLE and self._use_picamera:
            self.source = 'picamera2'
            self._cam = Picamera2()
            cfg = self._cam.create_video_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self._cam.configure(cfg)
            self._cam.start()
            time.sleep(0.5)
            self._thread = Thread(target=self._picamera2_loop, daemon=True)
        else:
            self.source = 'opencv'
            self._thread = Thread(target=self._opencv_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._cam:
            try:
                self._cam.stop()
                self._cam.close()
            except Exception:
                pass
            self._cam = None

    # ------------------------------------------------------------------ capture loops

    def _picamera2_loop(self):
        try:
            while self.running:
                with self._cam_lock:
                    array = self._cam.capture_array()      # H×W×3 RGB
                bgr = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
                with self.lock:
                    self.latest_frame = bgr
                    self.ring.append(bgr.copy())
                time.sleep(1.0 / max(1, self.framerate))
        except Exception as e:
            print(f'picamera2 loop error: {e}')

    def _opencv_loop(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        cap.set(cv2.CAP_PROP_FPS, self.framerate)
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            with self.lock:
                self.latest_frame = frame.copy()
                self.ring.append(frame.copy())
            time.sleep(1.0 / max(1, self.framerate))
        cap.release()

    # ------------------------------------------------------------------ frame access

    def get_frame(self) -> Optional[np.ndarray]:
        """Return latest frame as BGR numpy array."""
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def get_burst(self, n: int) -> List[np.ndarray]:
        """Return last n frames from ring buffer (BGR numpy arrays)."""
        with self.lock:
            frames = list(self.ring)
        return [f.copy() for f in frames[-n:]] if frames else []

    # ------------------------------------------------------------------ still capture

    def capture_stills_batch(self, n: int) -> list:
        """
        Capture n full-resolution stills with a SINGLE mode switch.
        Avoids camera firmware timeout caused by rapid repeated mode switches.
        """
        if self.source == 'picamera2' and self._cam:
            frames = []
            with self._cam_lock:
                still_cfg = self._cam.create_still_configuration(
                    main={"size": self.capture_resolution, "format": "RGB888"}
                )
                self._cam.switch_mode(still_cfg)
                try:
                    for _ in range(n):
                        array = self._cam.capture_array("main")
                        frames.append(cv2.cvtColor(array, cv2.COLOR_RGB2BGR))
                finally:
                    video_cfg = self._cam.create_video_configuration(
                        main={"size": self.resolution, "format": "RGB888"}
                    )
                    self._cam.switch_mode(video_cfg)
            return frames
        else:
            return [f for f in (self.get_frame() for _ in range(n)) if f is not None]

    def capture_still(self, path: str = None) -> Optional[np.ndarray]:
        """
        Capture a full-resolution still frame as BGR numpy array.
        Switches picamera2 to still mode (capture_resolution), captures, returns to stream.
        Saves lossless TIFF to path if provided.
        Never saves as JPEG — TIFF only for archival.
        """
        if self.source == 'picamera2' and self._cam:
            with self._cam_lock:
                still_cfg = self._cam.create_still_configuration(
                    main={"size": self.capture_resolution, "format": "RGB888"}
                )
                array = self._cam.switch_mode_and_capture_array(still_cfg, "main")
            bgr = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
            if path:
                cv2.imwrite(str(path), bgr)
            return bgr
        else:
            bgr = self.get_frame()
            if bgr is None:
                return None
            if path:
                cv2.imwrite(str(path), bgr)
            return bgr

    # ------------------------------------------------------------------ camera controls

    def set_controls(self, controls: dict):
        """
        Set picamera2 controls: ExposureTime, AnalogueGain, AwbMode, etc.
        No-op on OpenCV fallback.
        """
        if self.source == 'picamera2' and self._cam:
            self._cam.set_controls(controls)

    def get_metadata(self) -> dict:
        """
        Return last capture metadata: ExposureTime, AnalogueGain, ColourGains, etc.
        Empty dict on OpenCV fallback.
        """
        if self.source == 'picamera2' and self._cam:
            try:
                return self._cam.capture_metadata()
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------ MJPEG streaming

    def get_jpeg_bytes(self, quality: int = 80) -> Optional[bytes]:
        """JPEG bytes for live preview/streaming only. Never used for archival."""
        frame = self.get_frame()
        if frame is None:
            return None
        _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return jpeg.tobytes()

    def mjpeg_generator(self):
        boundary = b'--frame'
        while True:
            if not self.running:
                time.sleep(0.05)
                continue
            data = self.get_jpeg_bytes()
            if data is None:
                time.sleep(0.02)
                continue
            yield (b'%s\r\nContent-Type: image/jpeg\r\n\r\n' % boundary) + data + b'\r\n'

    # ------------------------------------------------------------------ health

    def health_check(self) -> dict:
        return {
            'running': self.running,
            'source': self.source,
            'ring_len': len(self.ring),
            'resolution': self.resolution,
            'framerate': self.framerate,
        }
