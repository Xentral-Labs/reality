"""Optional private readiness probe; never runs jobs or accesses business records."""

import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from time import monotonic


class LoopHealth:
    def __init__(self, role: str, *, clock=monotonic):
        self.role = role
        self.clock = clock
        self.last_success: float | None = None
        self.state = "starting"
        self.lock = Lock()

    def succeeded(self) -> None:
        with self.lock:
            self.last_success = self.clock()
            self.state = "ready"

    def failed(self) -> None:
        with self.lock:
            self.state = "unavailable"

    def close(self) -> None:
        with self.lock:
            self.state = "stopped"

    def snapshot(self) -> dict:
        with self.lock:
            age = (
                None
                if self.last_success is None
                else max(0, self.clock() - self.last_success)
            )
            status = self.state
            if status == "ready" and (age is None or age > 90):
                status = "stale"
            return {
                "role": self.role,
                "status": status,
                "last_sweep_age_seconds": None if age is None else round(age, 3),
            }


class HealthServer:
    def __init__(self, role: str, port: int):
        self.health = LoopHealth(role)
        health = self.health

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/healthz":
                    self.send_error(404)
                    return
                payload = health.snapshot()
                body = json.dumps(payload).encode()
                self.send_response(200 if payload["status"] == "ready" else 503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        class Server(ThreadingHTTPServer):
            daemon_threads = True
            allow_reuse_address = True
            address_family = (
                socket.AF_INET6 if socket.has_dualstack_ipv6() else socket.AF_INET
            )

            def server_bind(self):
                if self.address_family == socket.AF_INET6:
                    self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                super().server_bind()

        host = "::" if Server.address_family == socket.AF_INET6 else "0.0.0.0"
        self.server = Server((host, port), Handler)
        self.port = self.server.server_port
        self.thread = Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True
        )

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.health.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
