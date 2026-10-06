"""Loopback-only read-only artifact HTTP adapter."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scenarios.company_simulator.viewer.reader import ArtifactStore

ASSETS = {
    "/stories": ("stories.html", "text/html"),
    "/stories.js": ("stories.js", "text/javascript"),
    "/stories.css": ("stories.css", "text/css"),
    "/": ("index.html", "text/html"),
    "/app.js": ("app.js", "text/javascript"),
    "/style.css": ("style.css", "text/css"),
}


def make_server(root: Path, port: int = 8765) -> ThreadingHTTPServer:
    store = ArtifactStore(root)

    class Handler(BaseHTTPRequestHandler):
        def respond(
            self, status: int, body: bytes, content_type: str = "application/json"
        ):
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            authority = f"127.0.0.1:{self.server.server_port}"
            hosts = {authority, f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in hosts or self.headers.get(
                "Origin"
            ) not in {None, *("http://" + h for h in hosts)}:
                self.respond(403, b'{"error":"Local viewer access only"}')
                return
            path = unquote(urlsplit(self.path).path)
            if path in ASSETS:
                filename, content_type = ASSETS[path]
                self.respond(
                    200, (Path(__file__).parent / filename).read_bytes(), content_type
                )
                return
            try:
                if path == "/api/runs":
                    payload = store.list_runs()
                elif path.startswith("/api/stories/"):
                    payload = store.story_data(path.removeprefix("/api/stories/"))
                elif path.startswith("/api/runs/"):
                    payload = store.read_run(path.removeprefix("/api/runs/"))
                else:
                    raise FileNotFoundError()
                self.respond(200, json.dumps(payload, ensure_ascii=False).encode())
            except FileNotFoundError:
                self.respond(404, b'{"error":"Run or route not found"}')
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                self.respond(
                    503, b'{"error":"Artifacts unavailable or updating; retry shortly"}'
                )

        def do_POST(self):
            self.respond(405, b'{"error":"Read-only viewer"}')

        do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_POST

        def log_message(self, format, *args):
            return

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(
        description="Watch captured simulator runs; no database connection needed"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[5] / "artifacts/company_simulator",
    )
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with make_server(args.root, args.port) as server:
        print(
            f"Simulator spectator: http://127.0.0.1:{server.server_port} · artifacts: {args.root.resolve()}",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
