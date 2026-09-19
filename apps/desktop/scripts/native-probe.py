"""Isolated native cookie proof; exposes no product or database operations."""

from __future__ import annotations

import json
import secrets
import sys
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = b"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reality Local Preview</title><link rel="stylesheet" href="/style.css">
<main><p class="eyebrow">REALITY / LOCAL</p><h1>A home for your<br>business reality.</h1>
<p class="intro">Native macOS preview. Your local connection is ready.</p>
<section><h2>Connection check</h2><p>Local endpoint <strong id="endpoint"></strong></p>
<p>Protected session <strong id="session">Checking...</strong></p>
<p>Page access to native commands <strong id="bridge">Checking...</strong></p></section>
<p class="note">Development preview / Company setup and AI settings are coming next.</p>
</main><script src="/app.js"></script></html>"""
STYLE = b"""body{margin:0;background:#f6f4ef;color:#19372e;font:17px -apple-system,BlinkMacSystemFont,sans-serif}main{max-width:680px;margin:70px auto;padding:0 36px}.eyebrow{font-size:12px;letter-spacing:3px}h1{font-size:50px;line-height:1.08;font-weight:550;letter-spacing:-2px}.intro{color:#5a6c63;line-height:1.6}section{background:white;border:1px solid #dfe5dc;border-radius:16px;padding:20px 28px;margin-top:36px}h2{font-size:18px}section p{display:flex;justify-content:space-between;gap:20px;font-size:14px;padding:8px 0}strong{font-weight:500;color:#28754b}.note{font-size:12px;color:#6c7770;margin-top:28px}"""
SCRIPT = b"""(async()=>{let denied=false;
try { await window.__TAURI_INTERNALS__.invoke('plugin:app|version'); } catch(error) { denied=/not allowed|denied|not permitted/i.test(String(error)); }
const proof={cookie_hidden:!document.cookie.includes('reality_native_probe'),native_command_denied:denied};
document.getElementById('endpoint').textContent=location.host;
try {const r=await fetch('/proof',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(proof)});if(!r.ok)throw Error();document.getElementById('session').textContent=proof.cookie_hidden?'HttpOnly cookie verified':'Failed';document.getElementById('bridge').textContent=proof.native_command_denied?'Denied by policy':'Check failed';}catch{document.getElementById('session').textContent='Check failed';}})();"""


class ProbeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, runtime: Path, scripts: Path):
        self.token = secrets.token_urlsafe(32)
        self.proof = {"cookie_hidden": None, "native_command_denied": None}
        super().__init__(("127.0.0.1", 0), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"

    def status(self):
        return dict(self.proof)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body=b"", content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self, mutation=False):
        if self.headers.get_all("Host") != [self.server.origin.removeprefix("http://")]:
            self.reply(403)
            return False
        origins = self.headers.get_all("Origin") or []
        if (mutation and origins != [self.server.origin]) or (
            origins and origins != [self.server.origin]
        ):
            self.reply(403)
            return False
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            value = cookie.get("reality_native_probe")
            valid = value is not None and secrets.compare_digest(
                value.value, self.server.token
            )
        except (ValueError, TypeError):
            valid = False
        if not valid:
            self.reply(401)
        return valid

    def do_GET(self):
        if not self.authorized():
            return
        assets = {
            "/": (PAGE, "text/html; charset=utf-8"),
            "/style.css": (STYLE, "text/css"),
            "/app.js": (SCRIPT, "text/javascript"),
        }
        if self.path in assets:
            self.reply(200, *assets[self.path])
        elif self.path == "/status":
            self.reply(200, json.dumps(self.server.status()).encode())
        else:
            self.reply(404)

    def do_POST(self):
        if not self.authorized(mutation=True):
            return
        if self.path != "/proof":
            self.reply(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError()
            payload = json.loads(self.rfile.read(length))
            if (
                not isinstance(payload, dict)
                or set(payload) != set(self.server.proof)
                or any(type(v) is not bool for v in payload.values())
            ):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.reply(400)
            return
        self.server.proof = payload
        print(json.dumps(payload), flush=True)
        self.reply(200, b'{"ok":true}')


def main():
    server = ProbeServer(
        Path(__file__).parent.parent / "runtime", Path(__file__).parent
    )
    # This single private pipe message is consumed by Rust; never forward it to logs.
    print(json.dumps({"origin": server.origin, "token": server.token}), flush=True)

    def parent_closed():
        sys.stdin.buffer.read()
        server.shutdown()

    threading.Thread(target=parent_closed, daemon=True).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
