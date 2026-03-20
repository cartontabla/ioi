import requests
import uuid
from .base import ServerBackend


class GenericHTTPBackend(ServerBackend):
    """
    Adapter for any HTTP backend that follows the standard job API:
      POST /jobs           → {'job_id': '...'}
      GET  /jobs/<id>      → {'status': 'done', ...}
      GET  /jobs/<id>/result → {'output_path': '...', ...}
    """

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return r.status_code == 200
        except Exception:
            return False

    def submit(self, operation: str, params: dict) -> str:
        payload = {'operation': operation, **params}
        r = requests.post(f"{self.base_url}/jobs", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()['job_id']

    def poll(self, job_id: str) -> dict:
        r = requests.get(f"{self.base_url}/jobs/{job_id}", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def collect(self, job_id: str) -> dict:
        r = requests.get(f"{self.base_url}/jobs/{job_id}/result", timeout=self.timeout)
        r.raise_for_status()
        return {'ok': True, **r.json()}
