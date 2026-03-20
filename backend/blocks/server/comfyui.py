import requests
import json
import uuid
from .base import ServerBackend


class ComfyUIBackend(ServerBackend):
    """
    Adapter for ComfyUI via its native HTTP API.
    Handles: AI inference, upscaling, restoration, superresolution.

    ComfyUI API:
      POST /prompt          → {'prompt_id': '...'}
      GET  /history/<id>    → workflow output dict
    """

    def __init__(self, base_url: str = 'http://localhost:8188', timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/system_stats", timeout=self.timeout)
            return r.status_code == 200
        except Exception:
            return False

    def submit(self, operation: str, params: dict) -> str:
        """
        Submit a ComfyUI workflow.
        params must include 'workflow': dict (ComfyUI prompt graph).
        Returns prompt_id.
        """
        workflow = params.get('workflow')
        if not workflow:
            raise ValueError("ComfyUI submit requires 'workflow' in params")
        client_id = str(uuid.uuid4())
        payload = {'prompt': workflow, 'client_id': client_id}
        r = requests.post(f"{self.base_url}/prompt", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()['prompt_id']

    def poll(self, job_id: str) -> dict:
        r = requests.get(f"{self.base_url}/history/{job_id}", timeout=self.timeout)
        r.raise_for_status()
        history = r.json()
        if job_id not in history:
            return {'status': 'pending'}
        entry = history[job_id]
        if entry.get('status', {}).get('completed'):
            return {'status': 'done'}
        if entry.get('status', {}).get('status_str') == 'error':
            return {'status': 'error', 'reason': 'comfyui-error'}
        return {'status': 'running'}

    def collect(self, job_id: str) -> dict:
        r = requests.get(f"{self.base_url}/history/{job_id}", timeout=self.timeout)
        r.raise_for_status()
        history = r.json()
        outputs = history.get(job_id, {}).get('outputs', {})
        return {'ok': True, 'outputs': outputs}
