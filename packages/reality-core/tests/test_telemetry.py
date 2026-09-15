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
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader

    reader = InMemoryMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))

    app = FastAPI()

    @app.get("/u/{uid}")
    def _read(uid: str):
        return {"uid": uid}

    telemetry.instrument_fastapi(app)
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
