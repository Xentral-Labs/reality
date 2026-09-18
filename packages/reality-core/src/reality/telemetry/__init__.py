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

HTTP metrics come from the bundled instrumentation under
OTEL_SEMCONV_STABILITY_OPT_IN=http, which yields
http.server.request.duration keyed on the route TEMPLATE (http.route), in
seconds, with sub-second bucket boundaries. This is worth stating because the
first cut of this module did the opposite -- it dropped the bundled metrics and
hand-rolled a replacement, on the belief that they were keyed on the resolved
path. They are not: that is true of the SPAN attribute, not the metric. Five
requests to /u/{uid} produce one series, not five (tests/test_telemetry.py
asserts exactly this).

Traces are OFF unless REALITY_OTEL_TRACES is set, because there is no trace
backend deployed and FastAPI span attributes carry the query string, which on
this API includes free-text search terms.
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
    #
    # service.instance.id is set EXPLICITLY from the pod name. Left to itself
    # the SDK invents a random UUID per process, so on spot capacity every
    # restart and every Argo rollout would mint a complete new set of series
    # and strand the old ones. The pod name is stable for the life of the pod
    # and repeats no more often than the pod does.
    attributes = {
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "").strip() or service_name,
        "service.version": os.environ.get("REALITY_IMAGE_TAG", "").strip() or "unknown",
        "deployment.environment": os.environ.get("REALITY_ENV", "").strip()
        or "unknown",
    }
    pod = os.environ.get("REALITY_POD_NAME", "").strip()
    if pod:
        attributes["service.instance.id"] = pod
        attributes["k8s.pod.name"] = pod
    node = os.environ.get("REALITY_NODE_NAME", "").strip()
    if node:
        # Lets a latency spike be correlated with a spot reclaim.
        attributes["k8s.node.name"] = node
    return Resource.create(attributes)


def configure(service_name: str) -> None:
    """Install the trace and metric providers. Idempotent and never raises."""
    global _configured
    if _configured or not enabled():
        return
    try:
        # Must be set before any instrumentation package is imported: the
        # semconv mode is read at import time. Opting in gives us
        # http.server.request.duration keyed on http.route, in seconds, with
        # sub-second bucket boundaries -- rather than the legacy metric, which
        # is in milliseconds under non-standard attribute names.
        # Merged, not setdefault: the variable is a comma-separated list, so an
        # operator opting into another signal (e.g. "database" for SQLAlchemy)
        # would otherwise silently drop the http opt-in and hand back the
        # legacy millisecond-valued metric under different attribute names.
        opt_in = {
            part.strip()
            for part in os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN", "").split(",")
            if part.strip()
        }
        opt_in.add("http")
        os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = ",".join(sorted(opt_in))

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

        # Traces are OFF unless explicitly asked for, and deliberately so.
        # There is no trace backend deployed, so spans would be exported only
        # to be dropped -- and FastAPI span attributes carry the full request
        # target including the query string, which on this API means free-text
        # `q=` search terms. Shipping user-entered content to a collector that
        # discards it is cost with no benefit and a privacy surface with no
        # upside. Set REALITY_OTEL_TRACES=1 alongside a real backend.
        if os.environ.get("REALITY_OTEL_TRACES", "").strip() in ("1", "true", "yes"):
            tracer_provider = TracerProvider(resource=resource)
            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
            trace.set_tracer_provider(tracer_provider)

        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
            )
        )
        _configured = True
        log.info("OpenTelemetry configured for %s", service_name)
    except Exception:
        log.exception("OpenTelemetry setup failed; continuing without telemetry")


def instrument_fastapi(app: Any) -> None:
    """Install the bundled FastAPI instrumentation.

    /healthz and /readyz are excluded: probes fire every few seconds on every
    replica and would otherwise dominate the volume and skew the latency
    histograms without describing any real traffic.
    """
    if not enabled():
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz,readyz")
    except Exception:
        log.exception("FastAPI instrumentation failed")


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
    except Exception:
        log.exception("SQLAlchemy instrumentation failed")
    try:
        from reality.telemetry.metrics import observe_pool

        observe_pool(engine)
    except Exception:
        log.exception("Pool metrics registration failed")


def instrument_httpx() -> None:
    """Client spans for outbound calls - Anthropic and the Resend API."""
    if not enabled():
        return
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception:
        log.exception("httpx instrumentation failed")


def instrument_accounts(session_factory: Any) -> None:
    """Register the account-state gauges. Guarded like every other entry point.

    This used to be called inline from web/app.py with no try/except -- the one
    telemetry call in the package that could stop the API from booting if the
    opentelemetry packages were missing from an image.
    """
    if not enabled():
        return
    try:
        from reality.telemetry.metrics import observe_accounts

        observe_accounts(session_factory)
    except Exception:
        log.exception("account gauge registration failed")


def instrument_asgi(app: Any) -> Any:
    """HTTP metrics for a plain Starlette/ASGI app (the MCP server).

    The MCP app is server.streamable_http_app(), not FastAPI, so the FastAPI
    instrumentor does not apply -- without this the whole MCP surface reports
    no response times and no status codes.

    Note the metrics carry NO http.route: raw ASGI middleware runs before
    Starlette routing, so there is no route template to read. Duration and
    status are per-service rather than per-endpoint here. That is acceptable
    because streamable_http_app() is effectively a single endpoint, but do not
    assume parity with the FastAPI instrumentation.
    """
    if not enabled():
        return app
    try:
        from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

        return OpenTelemetryMiddleware(app, excluded_urls="healthz,readyz")
    except Exception:
        log.exception("ASGI instrumentation failed")
        return app
