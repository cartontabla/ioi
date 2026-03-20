import requests
from .base import ServerBackend


class FijiBackend(ServerBackend):
    """
    Adapter for Fiji (ImageJ) via its HTTP server plugin (SCIFIO REST or similar).
    Handles: focus stacking, deconvolution, advanced corrections.
    """

    def __init__(self, base_url: str = 'http://localhost:8080', timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._jobs: dict = {}  # local job tracking if Fiji has no native job API

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/", timeout=self.timeout)
            return r.status_code < 500
        except Exception:
            return False

    def submit(self, operation: str, params: dict) -> str:
        raise NotImplementedError("Fiji adapter: submit not yet implemented")

    def poll(self, job_id: str) -> dict:
        raise NotImplementedError("Fiji adapter: poll not yet implemented")

    def collect(self, job_id: str) -> dict:
        raise NotImplementedError("Fiji adapter: collect not yet implemented")
