import threading
import time
from collections import deque
from threading import Lock, Thread

try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
    PICAMERA_AVAILABLE = True
except Exception:
    PICAMERA_AVAILABLE = False

import cv2
import numpy as np


class SmartCamera:
    """Wrapper that tries PiCamera first and falls back to OpenCV.
    Maintains an in-memory ring buffer of recent JPEG frames for redundancy.
    Provides an MJPEG generator for streaming and simple capture/health APIs.
    """

    def __init__(self, resolution=(640, 480), framerate=24, ring_size=32):
        self.resolution = resolution
        self.framerate = framerate
        self.ring = deque(maxlen=ring_size)
        self.latest_frame = None
        self.lock = Lock()
        self.running = False
        self.source = None
        self._thread = None

    def start(self):
        if self.running:
            return
        if PICAMERA_AVAILABLE:
            self.source = 'picamera'
            self._thread = Thread(target=self._picamera_loop, daemon=True)
        else:
            self.source = 'opencv'
            self._thread = Thread(target=self._opencv_loop, daemon=True)
        self.running = True
        self._thread.start()

    def _picamera_loop(self):
        try:
            camera = PiCamera()
            camera.resolution = self.resolution
            camera.framerate = self.framerate
            raw = PiRGBArray(camera, size=self.resolution)
            time.sleep(0.2)
            for frame in camera.capture_continuous(raw, format='bgr', use_video_port=True):
                image = frame.array
                _, jpeg = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                data = jpeg.tobytes()
                with self.lock:
                    self.latest_frame = data
                    self.ring.append(data)
                raw.truncate(0)
                if not self.running:
                    break
            camera.close()
        except Exception as e:
            # If picamera fails at runtime, switch to opencv fallback
            print('PiCamera error, falling back to OpenCV:', e)
            self.source = 'opencv'
            self._opencv_loop()

    def _opencv_loop(self):
        cap = cv2.VideoCapture(0)
        # try to set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        cap.set(cv2.CAP_PROP_FPS, self.framerate)
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            data = jpeg.tobytes()
            with self.lock:
                self.latest_frame = data
                self.ring.append(data)
            time.sleep(1.0 / max(1, self.framerate))
        cap.release()

    def get_frame(self):
        with self.lock:
            return self.latest_frame

    def mjpeg_generator(self):
        boundary = b'--frame'
        while True:
            if not self.running:
                time.sleep(0.05)
                continue
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.02)
                continue
            yield (b'%s\r\nContent-Type: image/jpeg\r\n\r\n' % boundary) + frame + b'\r\n'

    def capture_image(self, path=None):
        frame = self.get_frame()
        if frame is None:
            return None
        if path:
            with open(path, 'wb') as f:
                f.write(frame)
            return path
        return frame

    def health_check(self):
        return {
            'running': self.running,
            'source': self.source,
            'ring_len': len(self.ring)
        }

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
