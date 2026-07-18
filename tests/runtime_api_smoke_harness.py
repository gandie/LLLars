from __future__ import annotations

import json
import threading
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


@dataclass
class SmokeHarness:
    base_url: str
    submissions: list[dict[str, object]]


class _HarnessServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler: type[BaseHTTPRequestHandler],
        *,
        statuses: list[dict[str, object]],
        logs: dict[str, object],
    ) -> None:
        super().__init__(server_address, request_handler)
        self.job_id = "job-1"
        self.statuses = statuses
        self.logs = logs
        self.submissions: list[dict[str, object]] = []
        self._status_index = 0
        self._lock = threading.Lock()

    def next_status(self) -> dict[str, object]:
        with self._lock:
            if self._status_index >= len(self.statuses):
                return self.statuses[-1]
            payload = self.statuses[self._status_index]
            self._status_index += 1
            return payload


class _HarnessHandler(BaseHTTPRequestHandler):
    server: _HarnessServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json_response(
        self,
        payload: dict[str, object],
        status_code: int,
    ) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _path(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:
        path = self._path()
        if path == "/health":
            self._json_response({"status": "ok"}, 200)
            return
        if path == f"/jobs/{self.server.job_id}":
            self._json_response(self.server.next_status(), 200)
            return
        if path == f"/jobs/{self.server.job_id}/logs":
            self._json_response(self.server.logs, 200)
            return
        self._json_response({"error": "not found"}, 404)

    def do_POST(self) -> None:
        path = self._path()
        if path != "/jobs":
            self._json_response({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        payload = json.loads(body) if body else {}
        self.server.submissions.append(payload)
        self._json_response({"job_id": self.server.job_id}, 200)


@contextmanager
def serve_harness(
    statuses: list[dict[str, object]],
    *,
    logs: dict[str, object] | None = None,
) -> Generator[SmokeHarness, None, None]:
    if not statuses:
        raise ValueError("statuses must include at least one payload")
    server = _HarnessServer(
        ("127.0.0.1", 0),
        _HarnessHandler,
        statuses=statuses,
        logs=logs or {"agent_stdout": "done", "agent_stderr": ""},
    )
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    )
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield SmokeHarness(base_url=base_url, submissions=server.submissions)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
        if thread.is_alive():
            raise RuntimeError("serve harness did not shut down within 2s")
