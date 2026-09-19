"""Authenticated loopback transport around the existing product application.

The trusted runtime supplies a bound origin and a session factory with an exact
installation/owner binding. This module never migrates or bootstraps a database.
"""

import json
import os
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp

from reality.services.account_policy import account_eligible
from reality.web.auth import user_from_request

SessionFactory = Callable[[], AbstractContextManager[Session]]


def create_desktop_app(
    *,
    origin: str,
    frontend: Path,
    session_factory: SessionFactory,
    product: ASGIApp,
    development: bool = False,
) -> FastAPI:
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("An exact bound loopback origin is required.")
    if os.environ.get("REALITY_AUTH_MODE", "enabled").lower() == "disabled":
        raise ValueError("Desktop must not disable product authentication.")
    if not (frontend / "index.html").is_file():
        raise ValueError("Bundled product frontend is missing.")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def desktop_boundary(request: Request, call_next):
        if request.headers.getlist("host") != [parsed.netloc]:
            return JSONResponse({"detail": "Invalid local origin."}, status_code=403)
        origins = request.headers.getlist("origin")
        if (origins and origins != [origin]) or (
            request.method not in {"GET", "HEAD"} and origins != [origin]
        ):
            return JSONResponse({"detail": "Invalid local origin."}, status_code=403)
        path = request.url.path
        if path.startswith("/api/admin") or (
            path.startswith("/api/auth/")
            and path not in {"/api/auth/me", "/api/auth/profile", "/api/auth/logout"}
        ):
            return JSONResponse({"detail": "Not found."}, status_code=404)

        def authenticated():
            with session_factory() as session:
                user = user_from_request(request, session)
                return (
                    user is not None
                    and user.authentication_method == "local_os"
                    and account_eligible(session, user)
                )

        if not await run_in_threadpool(authenticated):
            return JSONResponse({"detail": "Local session required."}, status_code=401)
        if (
            development
            and request.method not in {"GET", "HEAD"}
            and "/integrations" in path
        ):
            return JSONResponse(
                {
                    "detail": "Connections are unavailable in this disposable development build."
                },
                status_code=403,
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.get("/")
    def home():
        return RedirectResponse("/app")

    @app.get("/app")
    @app.get("/app/{path:path}")
    def product_page(path: str = ""):
        if development:
            html = (frontend / "index.html").read_text()
            notice = (
                '<style>.onboarding-screen{min-height:calc(100dvh - 37px)}</style>'
                '<div role="status" style="box-sizing:border-box;height:37px;'
                'background:#fff4cd;color:#413400;padding:9px;text-align:center;'
                'font:14px system-ui">Temporary test installation — quitting removes '
                'this company, credentials and all test data. External connections '
                "are not available yet.</div>"
            )
            return HTMLResponse(
                html.replace('<div id="root">', notice + '<div id="root">')
            )
        return FileResponse(frontend / "index.html")

    if development:

        @app.post("/api/desktop/proof")
        async def proof(request: Request):
            payload = await request.json()
            if (
                not isinstance(payload, dict)
                or set(payload) != {"cookie_hidden", "native_command_denied"}
                or any(type(value) is not bool for value in payload.values())
            ):
                return JSONResponse({"detail": "Invalid proof."}, status_code=400)
            print(json.dumps(payload), flush=True)
            return {"ok": True}

        @app.get("/api/company-setup/options")
        def setup_options(request: Request):
            from reality.services import company_setup

            with session_factory() as session:
                user = user_from_request(request, session)
                return {
                    **company_setup.options(session, user.id),
                    "desktop_anthropic_setup": True,
                }

    app.mount(
        "/assets", StaticFiles(directory=frontend / "assets"), name="desktop-assets"
    )
    # Mounted app lifespan is intentionally not executed: legacy hosted bootstrap
    # belongs to the hosted entrypoint, not to this already-prepared local runtime.
    app.mount("/", product)
    return app
