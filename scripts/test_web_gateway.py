"""Exercise the deployed Nginx template against an isolated synthetic API."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = """from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.reply()
    def do_POST(self):
        self.reply()
    def reply(self):
        data = {"method": self.command, "path": self.path,
                "body": self.rfile.read(int(self.headers.get("Content-Length", 0))).decode(),
                "cookie": self.headers.get("Cookie")}
        if self.path == "/oauth/complete/oai_redirect":
            self.send_response(303)
            self.send_header("Location", "/synthetic-callback?code=synthetic&state=retained")
            self.send_header("Set-Cookie", "synthetic-completion=; Max-Age=0; Path=/oauth")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    def log_message(self, *args):
        pass
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
"""


def docker(*args: str) -> str:
    return subprocess.check_output(["docker", *args], text=True).strip()


def main() -> None:
    name = "reality-gateway-" + uuid.uuid4().hex[:12]
    containers: list[str] = []
    docker("network", "create", name)
    try:
        with tempfile.TemporaryDirectory(prefix=name) as directory:
            fixture = Path(directory)
            (fixture / "upstream.py").write_text(UPSTREAM)
            (fixture / "index.html").write_text("<html>synthetic consent SPA</html>")
            config = (ROOT / "apps/web/default.conf.template").read_text()
            config = config.replace("${NGINX_LOCAL_RESOLVERS}", "127.0.0.11")
            config = config.replace("${API_UPSTREAM}", "upstream:8000")
            (fixture / "default.conf").write_text(config)
            containers.append(
                docker(
                    "run",
                    "-d",
                    "--network",
                    name,
                    "--network-alias",
                    "upstream",
                    "-v",
                    f"{fixture / 'upstream.py'}:/upstream.py:ro",
                    "python:3.12-alpine",
                    "python",
                    "/upstream.py",
                )
            )
            containers.append(
                docker(
                    "run",
                    "-d",
                    "--network",
                    name,
                    "-p",
                    "127.0.0.1::80",
                    "-v",
                    f"{fixture / 'default.conf'}:/etc/nginx/conf.d/default.conf:ro",
                    "-v",
                    f"{fixture / 'index.html'}:/usr/share/nginx/html/index.html:ro",
                    "nginx:1.27-alpine",
                )
            )
            address = docker("port", containers[-1], "80/tcp")
            base = "http://" + address

            def request(path: str, body: bytes | None = None) -> tuple[str, bytes]:
                req = urllib.request.Request(
                    base + path, data=body, headers={"Cookie": "synthetic=session"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.headers.get_content_type(), response.read()

            for attempt in range(50):
                try:
                    request("/healthz")
                    break
                except (OSError, urllib.error.URLError):
                    if attempt == 49:
                        raise
                    time.sleep(0.1)
            for path in (
                "/.well-known/oauth-authorization-server",
                "/.well-known/openid-configuration",
                "/oauth/authorize?response_type=code&state=synthetic",
                "/oauth/authorize",
                "/oauth/authorize?interaction=",
                "/oauth/complete/oai_synthetic?state=retained",
                "/api/example?tenant=synthetic",
                "/healthz",
            ):
                content_type, body = request(path)
                assert content_type == "application/json", (path, content_type, body)
                data = json.loads(body)
                assert data == {
                    "method": "GET",
                    "path": path,
                    "body": "",
                    "cookie": "synthetic=session",
                }, data
            for path in ("/oauth/token", "/oauth/revoke"):
                content_type, body = request(path, b"grant_type=synthetic&value=a%2Bb")
                assert content_type == "application/json", (path, body)
                data = json.loads(body)
                assert data["method"] == "POST" and data["path"] == path, data
                assert data["body"] == "grant_type=synthetic&value=a%2Bb", data
                assert data["cookie"] == "synthetic=session", data

            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None

            opener = urllib.request.build_opener(NoRedirect())
            try:
                opener.open(base + "/oauth/complete/oai_redirect", timeout=5)
                raise AssertionError("Completion must retain the redirect")
            except urllib.error.HTTPError as response:
                assert response.code == 303, response.code
                assert (
                    response.headers["Location"]
                    == "/synthetic-callback?code=synthetic&state=retained"
                )
                assert (
                    response.headers["Set-Cookie"]
                    == "synthetic-completion=; Max-Age=0; Path=/oauth"
                )
            for path in (
                "/oauth/authorize?interaction=oai_synthetic",
                "/app/settings",
                "/.well-known/unrelated",
                "/oauth/unrelated",
                "/.well-known/oauth-authorization-server/unrelated",
            ):
                content_type, body = request(path)
                assert (
                    content_type == "text/html" and b"synthetic consent SPA" in body
                ), (path, body)
            print(
                "Web gateway: discovery, protocol, consent and existing routes passed"
            )
    finally:
        for container in reversed(containers):
            subprocess.run(
                ["docker", "rm", "-f", container],
                check=False,
                stdout=subprocess.DEVNULL,
            )
        subprocess.run(
            ["docker", "network", "rm", name], check=False, stdout=subprocess.DEVNULL
        )


if __name__ == "__main__":
    main()
