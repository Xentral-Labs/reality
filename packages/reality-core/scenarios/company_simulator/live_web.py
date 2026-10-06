"""Explicitly scoped loopback live console; separate from the read-only artifact viewer."""

import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reality.services import live_company
from reality.services.core import RealityError


def make_live_server(engine, tenant, actor, run_id, port=8768):
    with Session(engine) as session:
        live_company._owner(session, tenant, actor)
        live_company._run(session, tenant, run_id)
    token = secrets.token_urlsafe(32)
    assets = Path(__file__).parent / "viewer"

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, payload, kind="application/json"):
            body = (
                json.dumps(payload, ensure_ascii=False, default=str).encode()
                if kind == "application/json"
                else payload
            )
            self.send_response(status)
            for key, value in {
                "Content-Type": kind + "; charset=utf-8",
                "Content-Length": str(len(body)),
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            }.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def allowed(self, write=False):
            hosts = {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }
            if self.headers.get("Host") not in hosts:
                return False
            origin = self.headers.get("Origin")
            if origin not in {None, *("http://" + h for h in hosts)}:
                return False
            return not write or (
                origin is not None
                and secrets.compare_digest(
                    self.headers.get("X-Simulator-Token", ""), token
                )
            )

        def do_GET(self):
            if not self.allowed():
                self.respond(403, {"error": "Loopback only"})
                return
            if self.path in ["/", "/live.js", "/live.css", "/stories.css"]:
                name = {
                    "/": "live.html",
                    "/live.js": "live.js",
                    "/live.css": "live.css",
                    "/stories.css": "stories.css",
                }[self.path]
                kind = (
                    "text/html"
                    if self.path == "/"
                    else "text/javascript"
                    if name.endswith(".js")
                    else "text/css"
                )
                self.respond(200, (assets / name).read_bytes(), kind)
                return
            request_url = urlsplit(self.path)
            if request_url.path != "/api/state":
                self.respond(404, {"error": "Not found"})
                return
            order_filter = parse_qs(request_url.query).get("order_filter", [""])[0]
            if order_filter not in {
                "",
                "ready",
                "blocked",
                "reservation_blocked",
                "held",
                "overdue",
                "at_risk",
                "complete",
                "partial",
                "unshipped",
            }:
                self.respond(400, {"error": "Invalid order filter"})
                return
            try:
                with Session(engine) as session:
                    live_company._owner(session, tenant, actor)
                    state = live_company.live_view(
                        session, tenant, run_id, performance_filter=order_filter
                    )
                self.respond(200, {**state, "csrf": token})
            except (SQLAlchemyError, RealityError, OSError):
                self.respond(503, {"error": "Live records unavailable; retry shortly"})

        def do_POST(self):
            if not self.allowed(write=True):
                self.respond(403, {"error": "Same-origin local confirmation required"})
                return
            if self.path not in ["/api/preview", "/api/inject"]:
                self.respond(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 24000:
                    raise ValueError("Invalid request size")
                args = json.loads(self.rfile.read(length))
                with Session(engine) as session:
                    live_company._owner(session, tenant, actor)
                    if self.path == "/api/preview":
                        result = live_company.preview_event(
                            session, tenant, run_id, args["event"]
                        )
                    else:
                        result = live_company.inject(
                            session,
                            tenant,
                            actor,
                            run_id,
                            args["event"],
                            request_id=args["request_id"],
                            confirmed=args.get("confirmed") is True,
                        )
                    session.commit()
                self.respond(200, result)
            except (ValueError, KeyError, TypeError) as error:
                self.respond(400, {"error": str(error)})
            except (SQLAlchemyError, RealityError, OSError):
                self.respond(
                    503,
                    {
                        "error": "Event unavailable; reconcile its request ID before retry"
                    },
                )

        def do_DELETE(self):
            self.respond(405, {"error": "Unsupported operation"})

        do_PUT = do_PATCH = do_OPTIONS = do_DELETE

        def log_message(self, *args):
            return

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(engine, tenant, actor, run_id, port):
    with make_live_server(engine, tenant, actor, run_id, port) as server:
        print(
            f"Reality Company Simulator live: http://127.0.0.1:{server.server_port}",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
