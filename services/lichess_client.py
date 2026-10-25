import json
from threading import Event, Lock
from time import monotonic

import requests


class LichessClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.stopped = Event()
        self.request_lock = Lock()
        self.next_request = 0
        self.headers = {"Authorization": f"Bearer {cfg.lichess.token}"}

    def request(self, method, path, **kwargs):
        with self.request_lock:
            delay = max(0, self.next_request - monotonic())
            if self.stopped.wait(delay):
                raise InterruptedError("Lichess stopped")
            response = requests.request(
                method,
                self.cfg.lichess.url + path,
                headers=self.headers,
                timeout=self.cfg.lichess.timeout_seconds,
                **kwargs,
            )
            self.next_request = monotonic() + 1
            if response.status_code == 429:
                self.next_request = monotonic() + max(
                    60, int(response.headers.get("Retry-After", 60))
                )
            response.raise_for_status()
            return response

    def stream(self, path):
        with requests.get(
            self.cfg.lichess.url + path,
            headers=self.headers,
            stream=True,
            timeout=(10, self.cfg.lichess.timeout_seconds),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if self.stopped.is_set():
                    break
                if line:
                    yield json.loads(line)
