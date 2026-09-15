"""OpenTelemetry wiring.

Everything here is INERT unless OTEL_EXPORTER_OTLP_ENDPOINT is set. That is the
central design rule: the collector does not exist in every environment this code
runs in, and telemetry must never be the reason a process fails to boot. Every
entry point returns early when disabled, and every exporter/instrument call is
wrapped so a telemetry fault degrades to "no data" rather than an outage.

Configuration follows the OTel specification's own environment variables, so
nothing bespoke has to be learned:

    OTEL_EXPORTER_OTLP_ENDPOINT   e.g. http://alloy.monitoring:4318   (enables everything)
    OTEL_SERVICE_NAME             defaults to the name passed to configure()
    OTEL_RESOURCE_ATTRIBUTES      merged over the defaults set below

`service.version` is deliberately wired to the image tag, which CI already sets
to the git SHA, so every metric and span points at an exact commit.
"""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_configured = False


def enabled() -> bool:
    """True when an OTLP endpoint is configured. The single on/off switch."""
    return bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip())


def _resource(service_name: str) -> Any:
    from opentelemetry.sdk.resources import Resource

    # deployment.environment lets one Grafana serve several estates without the
    # dashboards colliding; service.version ties a datapoint to a build.
    attributes = {
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "").strip() or service_name,
        "service.version": os.environ.get("REALITY_IMAGE_TAG", "").strip() or "unknown",
        "deployment.environment": os.environ.get("REALITY_ENV", "").strip() or "unknown",
    }
    return Resource.create(attributes)


def configure(service_name: str) -> None:
    """Install the trace and metric providers. Idempotent and never raises."""
    global _configured
    if _configured or not enabled():
        return
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = _resource(service_name)

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)

        from opentelemetry.sdk.metrics.view import DropAggregation, View

        # The bundled http.server.* metrics are dropped, not exported.
        #
        # Measured, not assumed: this instrumentation keys them on `http.target`
        # -- the RESOLVED path -- and never on `http.route`. Every distinct
        # /api/tenants/<id>/... path would become its own Prometheus series, so
        # across 265 routes the series count grows with tenants and resource
        # ids rather than with endpoints. That is the classic way to take a
        # Prometheus down.
        #
        # The equivalent, bounded metric is recorded by the middleware in
        # instrument_fastapi() below, which reads the route TEMPLATE. Tracing is
        # left untouched: span attributes are not aggregated, so http.target is
        # useful there and costs nothing.
        drop_builtin_http = View(
            instrument_name="http.server.*", aggregation=DropAggregation()
        )

        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
                views=[drop_builtin_http],
            )
        )
        _configured = True
        log.info("OpenTelemetry configured for %s", service_name)
    except Exception:  # noqa: BLE001 - telemetry must never break the process
        log.exception("OpenTelemetry setup failed; continuing without telemetry")


def instrument_fastapi(app: Any) -> None:
    """Traces from the instrumentor, plus a bounded per-route latency metric.

    /healthz and /readyz are excluded from both: probes fire every few seconds
    on every replica and would otherwise dominate span volume and skew the
    latency histograms without describing real traffic.
    """
    if not enabled():
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz,readyz")
    except Exception:  # noqa: BLE001
        log.exception("FastAPI instrumentation failed")

    try:
        _install_http_metric(app)
    except Exception:  # noqa: BLE001
        log.exception("HTTP metric middleware failed")


_EXCLUDED_PATHS = ("/healthz", "/readyz")


def _install_http_metric(app: Any) -> None:
    """Record request duration keyed on the ROUTE TEMPLATE.

    Three attributes only, all bounded: the template (one value per route), the
    method, and the status code.

    Unmatched requests collapse to http.route="unmatched" rather than reporting
    their path. Otherwise a crawler or a scanner hitting random URLs would mint
    a new permanent series per URL -- the same unbounded-cardinality failure,
    arriving from outside.
    """
    import time

    from opentelemetry import metrics as _metrics

    meter = _metrics.get_meter("reality")
    histogram = meter.create_histogram(
        "reality.http.server.duration",
        description="Request duration by route template, method and status",
        unit="s",
    )

    @app.middleware("http")
    async def _record(request, call_next):
        if request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            # Starlette populates scope["route"] during routing, so this is the
            # template ("/api/tenants/{tenant_id}/copilot"), not the resolved path.
            template = _route_template(request)
            try:
                histogram.record(
                    time.perf_counter() - started,
                    {
                        "http.route": template,
                        "http.request.method": request.method,
                        "http.response.status_code": status,
                    },
                )
            except Exception:  # noqa: BLE001
                pass


def instrument_engine(engine: Any) -> None:
    """Spans for SQL statements, plus the connection-pool gauges.

    The pool is the component most likely to take this application down: each
    replica is capped at pool_size + max_overflow connections, several GET
    handlers refresh projections synchronously, and a Copilot turn can hold a
    connection for minutes. Saturation surfaces as 500s and flapping readiness,
    so the pool is measured directly rather than inferred.
    """
    if not enabled():
        return
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=False)
    except Exception:  # noqa: BLE001
        log.exception("SQLAlchemy instrumentation failed")
    try:
        from reality.telemetry.metrics import observe_pool

        observe_pool(engine)
    except Exception:  # noqa: BLE001
        log.exception("Pool metrics registration failed")


def instrument_httpx() -> None:
    """Client spans for outbound calls - Anthropic and the Resend API."""
    if not enabled():
        return
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception:  # noqa: BLE001
        log.exception("httpx instrumentation failed")

def _route_template(request: Any) -> str:
    """Best-effort route TEMPLATE for a request.

    scope["route"] is set by the router, so it is absent whenever middleware
    short-circuits first -- which is every 401 from the authentication
    middleware. Without a fallback, all auth failures collapse into a single
    "unmatched" bucket and it becomes impossible to see WHICH endpoint a
    misbehaving client is hammering.

    FastAPI does not flatten included routers: app.router.routes holds
    fastapi.routing._IncludedRouter wrappers whose own `path` is None, with the
    real routes underneath. So the search descends, in registration order -- the
    same order Starlette itself resolves in, which matters because the app ends
    with a catch-all `/{legacy_path:path}` that would otherwise swallow
    everything.

    Whatever comes back is a template, so the attribute stays bounded; a
    genuinely unroutable request yields "unmatched" rather than its raw path.
    """
    template = getattr(request.scope.get("route"), "path", None)
    if template:
        return template
    try:
        return _search_routes(request.app.router.routes, request.scope) or "unmatched"
    except Exception:  # noqa: BLE001
        return "unmatched"


def _search_routes(routes: Any, scope: Any, depth: int = 0) -> str | None:
    """Depth-limited search for the first matching route that has a path."""
    from starlette.routing import Match

    if depth > 4:  # guards against a cyclic or pathological router graph
        return None
    for candidate in routes:
        try:
            match, _ = candidate.matches(scope)
        except Exception:  # noqa: BLE001 - a route that cannot match is not fatal
            continue
        if match is Match.NONE:
            continue
        path = getattr(candidate, "path", None)
        if path:
            return path
        nested = getattr(candidate, "routes", None) or getattr(
            getattr(candidate, "original_router", None), "routes", None
        )
        if nested:
            found = _search_routes(nested, scope, depth + 1)
            if found:
                return found
    return None
