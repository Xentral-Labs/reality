"""Telemetry must be inert when unconfigured and bounded when configured.

These are the two properties the deployment relies on: a cluster with no
collector pays nothing, and a cluster with one does not get a Prometheus
series per user id. Neither test needs a running collector.
"""

from __future__ import annotations

import os

import pytest

from reality import telemetry


@pytest.fixture(autouse=True)
def _clear_endpoint(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)


def test_disabled_without_endpoint():
    assert telemetry.enabled() is False


def test_enabled_with_endpoint(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    assert telemetry.enabled() is True


def test_blank_endpoint_is_disabled(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "   ")
    assert telemetry.enabled() is False


def test_instrumentation_is_a_noop_when_disabled():
    """Every entry point must tolerate being called with junk while off."""
    from fastapi import FastAPI

    app = FastAPI()
    telemetry.configure("reality-test")
    telemetry.instrument_fastapi(app)
    telemetry.instrument_httpx()
    telemetry.instrument_engine(None)
    telemetry.instrument_accounts(None)

    assert telemetry.instrument_asgi(app) is app
    assert app.user_middleware == []


def test_resource_carries_explicit_instance_identity(monkeypatch):
    """Left to itself the SDK invents a random UUID per process, which would
    mint a fresh set of series on every restart. The pod name pins it."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    monkeypatch.setenv("REALITY_POD_NAME", "reality-api-7d9f")
    monkeypatch.setenv("REALITY_NODE_NAME", "ip-10-0-1-5")
    monkeypatch.setenv("REALITY_IMAGE_TAG", "abc1234")

    attributes = telemetry._resource("reality-api").attributes

    assert attributes["service.instance.id"] == "reality-api-7d9f"
    assert attributes["k8s.pod.name"] == "reality-api-7d9f"
    assert attributes["k8s.node.name"] == "ip-10-0-1-5"
    assert attributes["service.version"] == "abc1234"
    assert attributes["service.name"] == "reality-api"


def test_resource_omits_pod_attributes_outside_kubernetes(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    monkeypatch.delenv("REALITY_POD_NAME", raising=False)
    monkeypatch.delenv("REALITY_NODE_NAME", raising=False)

    attributes = telemetry._resource("reality-api").attributes

    assert "k8s.pod.name" not in attributes
    assert "k8s.node.name" not in attributes


def test_route_attribute_is_the_template_not_the_resolved_path(monkeypatch):
    """The cardinality guarantee, asserted rather than assumed: many distinct
    ids on one route must collapse to a single series."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader

    # A local provider passed explicitly, NOT set_meter_provider: the global
    # can only be set once per process and silently no-ops afterwards, so a
    # global here would make this test pass alone and fail under xdist
    # depending on which test touched the provider first.
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])

    app = FastAPI()

    @app.get("/u/{uid}")
    def _read(uid: str):
        return {"uid": uid}

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(
        app, excluded_urls="healthz,readyz", meter_provider=provider
    )
    client = TestClient(app)
    for uid in ("alice", "bob", "carol", "dave", "erin"):
        client.get(f"/u/{uid}?q=a+search+term")

    routes = set()
    for resource_metric in reader.get_metrics_data().resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name != "http.server.request.duration":
                    continue
                for point in metric.data.data_points:
                    routes.add(point.attributes.get("http.route"))
                    # User-entered search terms must never reach an attribute.
                    assert "a+search+term" not in str(dict(point.attributes))

    assert routes == {"/u/{uid}"}


def test_seconds_histograms_do_not_use_millisecond_buckets(monkeypatch):
    """The SDK's default boundaries are (0, 5, 10, 25, ... 10000) -- shaped for
    MILLISECONDS. Every histogram here records seconds, so with the defaults a
    0.4s and a 3.0s sweep land in the same bucket and no percentile exists.
    This regression slipped through once on the HTTP histogram and again on the
    sweep histogram, so it is asserted rather than trusted."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    from reality.telemetry import metrics as m

    assert max(m.SECONDS_BUCKETS) <= 120, "seconds buckets must not be ms-shaped"
    assert min(m.SECONDS_BUCKETS) < 0.1, "needs sub-100ms resolution"
    # The Copilot runs to ~270s against a 300s ALB idle timeout, so its
    # boundaries must resolve either side of that cliff.
    assert max(m.COPILOT_BUCKETS) >= 300
    assert 270 in m.COPILOT_BUCKETS


def test_sweep_duration_separates_sub_second_from_multi_second(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader

    from reality.telemetry import metrics as m

    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    monkeypatch.setattr(m, "_meter", provider.get_meter("reality"))
    monkeypatch.setattr(m, "_instruments", {})

    for seconds in (0.4, 1.2, 3.0):
        m.record("reality.jobs.sweep_duration", "d", "s", seconds, role="worker")

    populated = []
    for resource_metric in reader.get_metrics_data().resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                for point in metric.data.data_points:
                    populated = [c for c in point.bucket_counts if c]

    assert len(populated) >= 3, (
        "0.4s, 1.2s and 3.0s must fall in distinct buckets; "
        "all in one means the millisecond defaults are still in use"
    )
