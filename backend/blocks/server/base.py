from abc import ABC, abstractmethod


class ServerBackend(ABC):
    """
    Abstract adapter for external processing backends (Fiji, ComfyUI, generic HTTP).
    Each backend follows the same submit → poll → collect lifecycle.
    Node-RED always interacts with the same interface regardless of the backend.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is reachable."""
        ...

    @abstractmethod
    def submit(self, operation: str, params: dict) -> str:
        """
        Submit a job to the backend.
        Returns a job_id for polling.
        """
        ...

    @abstractmethod
    def poll(self, job_id: str) -> dict:
        """
        Poll job status.
        Returns: {'status': 'pending'|'running'|'done'|'error', ...}
        """
        ...

    @abstractmethod
    def collect(self, job_id: str) -> dict:
        """
        Collect result when done.
        Returns: {'ok': True, 'output_path': '...', ...}
        """
        ...

    def run_sync(self, operation: str, params: dict, poll_interval: float = 1.0, timeout: float = 300.0) -> dict:
        """
        Convenience: submit + poll until done + collect.
        Blocking — use only for short operations or in a background thread.
        """
        import time
        job_id = self.submit(operation, params)
        elapsed = 0.0
        while elapsed < timeout:
            status = self.poll(job_id)
            if status['status'] == 'done':
                return self.collect(job_id)
            if status['status'] == 'error':
                return {'ok': False, 'reason': status.get('reason', 'backend-error')}
            time.sleep(poll_interval)
            elapsed += poll_interval
        return {'ok': False, 'reason': 'timeout'}
