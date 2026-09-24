"""HTTP host for the Reality API, authentication and remote MCP server.

The browser product is the independently deployed React application.  This
module deliberately contains no templates, static assets or business rules.
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select, text
from starlette.concurrency import run_in_threadpool

from reality.catalogs import runtime_application_catalog
from reality.db.core import Session, TenantMembership
from reality.services.bootstrap import bootstrap_empty_database
from reality.services.platform import running_commit, running_version
from reality.services.tenant_policy import PlaygroundOperationDenied
from reality.web.api import public_router as public_api_router
from reality.web.api import router as api_router
from reality.web.auth import admin_router as auth_admin_router
from reality.web.auth import bootstrap_platform_admin, user_from_request
from reality.web.auth import router as auth_router
from reality.web.company_setup_api import is_account_setup_path
from reality.web.company_setup_api import router as company_setup_router
from reality.web.demo_data_api import router as demo_data_router
from reality.web.mcp_authorization import router as mcp_authorization_router
from reality.web.interactions_api import router as interactions_router
from reality.web.playground import router as playground_router
from reality.web.storyline_api import account_router as storyline_account_router
from reality.web.storyline_api import tenant_router as storyline_tenant_router


def configured_url(name: str, default: str) -> str:
    """Return a public URL while treating unset and empty values identically."""
    return (os.environ.get(name) or default).rstrip("/")


API_URL = configured_url("API_URL", "http://127.0.0.1:8000")
APP_URL = configured_url("APP_URL", "http://localhost:8080")


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    runtime_application_catalog()
    with Session() as session:
        bootstrap_empty_database(session)
        bootstrap_platform_admin(session)
    yield


from reality import telemetry as _telemetry


def _engine_for_telemetry():
    from reality.db.core import engine

    return engine


# Configured before the app object exists so the providers are in place when the
# instrumentors attach below. Inert unless OTEL_EXPORTER_OTLP_ENDPOINT is set.
_telemetry.configure("reality-api")

app = FastAPI(
    title="Reality API",
    description="Tenant-scoped application API for Reality.",
    lifespan=app_lifespan,
)


@app.exception_handler(PlaygroundOperationDenied)
async def playground_operation_denied(
    _request: Request, error: PlaygroundOperationDenied
) -> JSONResponse:
    return JSONResponse({"detail": str(error), "code": error.code}, status_code=403)


allowed_origins = [APP_URL]
if APP_URL in {"http://localhost:8080", "http://127.0.0.1:8080"}:
    allowed_origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "X-Reality-Correlation",
        "X-Reality-Refresh",
    ],
)


@app.middleware("http")
async def record_storyline_views(request: Request, call_next):
    """Spec 182: the views a person opens in a storyline company join the trace.

    Only GET requests on tenant routes are recorded here, and only after the
    response, from the route template and the parameters, never the body. Tool
    calls record themselves in the dispatcher and know that they run inside a
    request through the marker this middleware sets.
    """
    path = request.url.path
    if not path.startswith("/api/tenants/"):
        return await call_next(request)
    from reality.storyline import recorder

    started = time.perf_counter()
    with recorder.http_request():
        response = await call_next(request)
    route = request.scope.get("route")
    tenant_id = request.path_params.get("tenant_id")
    if request.method == "GET" and route is not None and tenant_id:
        params = {
            **{k: v for k, v in request.path_params.items() if k != "tenant_id"},
            **dict(request.query_params),
        }
        await run_in_threadpool(
            recorder.record_http_view,
            Session,
            tenant_id=tenant_id,
            route=route.path.removeprefix("/api/tenants/{tenant_id}"),
            params=params,
            status=response.status_code,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    return response


@app.middleware("http")
async def record_interactions(request: Request, call_next):
    """Spec 266: every company request the web makes is one engine-room interaction.

    Declared after the storyline middleware and before `protect_application_api`,
    which makes it run inside the admission check: a request refused because the
    caller is not a member of that company never reaches this point, so it is
    recorded in neither company. The engine room's own reads are not recorded;
    watching must not become something to watch.
    """
    from reality.services import interaction_recorder as interactions

    path = request.url.path
    parts = path.split("/")
    if (
        not path.startswith("/api/tenants/")
        or len(parts) < 4
        or not parts[3]
        or (len(parts) > 4 and parts[4] == "interactions")
        or not interactions.enabled()
    ):
        return await call_next(request)
    user = getattr(request.state, "user", None)
    observation, token = interactions.begin(
        parts[3],
        "web",
        f"{request.method} (unmatched)",
        correlation_id=request.headers.get("x-reality-correlation"),
        actor_user_id=getattr(user, "id", None),
        refresh=request.headers.get("x-reality-refresh") == "1",
    )
    error: BaseException | None = None
    try:
        response = await call_next(request)
    except BaseException as exc:
        error = exc
        raise
    else:
        if observation is not None:
            observation.http_status = response.status_code
        return response
    finally:
        if observation is not None:
            route = request.scope.get("route")
            if route is not None:
                observation.operation = (
                    f"{request.method} "
                    + route.path.removeprefix("/api/tenants/{tenant_id}")
                )[:200]
                dependant = getattr(route, "dependant", None)
                declared = {
                    parameter.name
                    for parameter in getattr(dependant, "query_params", ())
                }
                observation.arguments = tuple(
                    sorted(declared & set(request.query_params))
                )[: interactions.ARGUMENT_LIMIT]
        interactions.release(token)
        await run_in_threadpool(interactions.end, observation, None, error)


@app.middleware("http")
async def protect_application_api(request: Request, call_next):
    """Authenticate product APIs and enforce company membership at the boundary."""
    if os.environ.get("REALITY_AUTH_MODE", "enabled").lower() == "disabled":
        return await call_next(request)
    path = request.url.path
    public_paths = {
        "/api/auth/signup",
        "/api/auth/verify-email",
        "/api/auth/resend-code",
        "/api/auth/login",
        "/api/auth/invitations/inspect",
        "/api/auth/invitations/signup",
        "/api/v1/system/status",
        "/healthz",
    }
    if not path.startswith("/api/") or path in public_paths:
        return await call_next(request)

    def authorize():
        with Session() as session:
            user = user_from_request(request, session)
            if not user:
                return JSONResponse(
                    {"detail": "Authentication required."}, status_code=401
                )
            request.state.user = user
            user_paths = {
                "/api/auth/me",
                "/api/auth/logout",
                "/api/auth/profile",
                "/api/auth/application",
                "/api/auth/invitations/accept",
            }
            if (
                path not in user_paths
                and not is_account_setup_path(path, request.method)
                and not path.startswith("/api/tenants/")
                and path != "/api/playground"
                and not path.startswith("/api/playground/")
                and user.status != "active"
                and not user.is_platform_admin
            ):
                return JSONResponse(
                    {"detail": "Access approval is still pending."}, status_code=403
                )
            marker = "/api/tenants/"
            if marker in path and not user.is_platform_admin:
                tenant_id = path.split(marker, 1)[1].split("/", 1)[0]
                membership = session.scalar(
                    select(TenantMembership).where(
                        TenantMembership.tenant_id == tenant_id,
                        TenantMembership.user_id == user.id,
                        TenantMembership.status == "active",
                    )
                )
                if not membership:
                    return JSONResponse(
                        {"detail": "Company not found."}, status_code=404
                    )

    rejection = await run_in_threadpool(authorize)
    if rejection is not None:
        return rejection
    return await call_next(request)


app.include_router(auth_router)
app.include_router(auth_admin_router)
app.include_router(interactions_router)
app.include_router(api_router)
app.include_router(public_api_router)
app.include_router(playground_router)
app.include_router(storyline_account_router)
app.include_router(storyline_tenant_router)
app.include_router(company_setup_router)
app.include_router(demo_data_router)
app.include_router(mcp_authorization_router)

_telemetry.instrument_fastapi(app)
_telemetry.instrument_httpx()
_telemetry.instrument_engine(_engine_for_telemetry())

# Account state gauges live in the api only: every replica would report the same
# numbers, and the runners have no reason to query the accounts table.
_telemetry.instrument_accounts(Session)


@app.get("/healthz", include_in_schema=False)
def healthcheck():
    with Session() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/api/v1/system/status", tags=["system"])
def api_system_status():
    """Small stable probe for independently deployed web clients."""
    with Session() as session:
        session.execute(text("SELECT 1"))
    return {
        "service": "reality-backend",
        "status": "ready",
        "database": "connected",
        "artifact_storage": os.environ.get("REALITY_ARTIFACT_STORAGE", "file"),
        "version": running_version(),
        "commit": running_commit(),
    }


def _frontend_redirect(path: str, request: Request) -> RedirectResponse:
    target = f"{APP_URL}{path}"
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(target, status_code=308)


@app.get("/", include_in_schema=False)
def frontend_home(request: Request):
    """Compatibility redirect; marketing is owned by the React deployment."""
    return _frontend_redirect("/", request)


@app.get("/{legacy_path:path}", include_in_schema=False)
def retired_browser_route(legacy_path: str, request: Request):
    """Move old browser bookmarks to React without retaining a second UI."""
    first_segment = legacy_path.split("/", 1)[0]
    public_paths = {"homepage", "waitlist"}
    application_paths = {
        "app",
        "signup",
        "login",
        "verify-email",
        "access-pending",
        "profile",
        "admin",
        "settings",
        "commitments",
        "orders",
        "holds",
        "inventory",
        "reservations",
        "movements",
        "warehouse",
        "exceptions",
        "issues",
        "documents",
        "finance",
        "master",
        "timeline",
        "integrations",
        "imports",
        "system",
        "documentation",
        "chat",
        "explorer",
    }
    if first_segment in public_paths:
        return _frontend_redirect("/", request)
    if first_segment in application_paths:
        return _frontend_redirect("/app", request)
    raise HTTPException(status_code=404, detail="Not found")
