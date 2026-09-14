import json
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from reality.jobs.health import HealthServer, LoopHealth
from reality.services import system_readiness


def test_health_requires_a_fresh_successful_sweep():
    clock = [10.0]
    health = LoopHealth("worker", clock=lambda: clock[0])
    assert health.snapshot()["status"] == "starting"
    health.succeeded()
    assert health.snapshot()["status"] == "ready"
    clock[0] += 89
    assert health.snapshot()["status"] == "ready"
    clock[0] += 2
    assert health.snapshot()["status"] == "stale"
    health.succeeded()
    health.failed()
    assert health.snapshot()["status"] == "unavailable"
    health.succeeded()
    health.close()
    assert health.snapshot()["status"] == "stopped"


def test_health_http_is_read_only_and_contains_no_job_data():
    with HealthServer("scheduler", 0) as server:
        server.health.succeeded()
        with urlopen(f"http://127.0.0.1:{server.port}/healthz", timeout=2) as response:
            body = json.load(response)
        assert body["status"] == "ready"
        assert set(body) == {"role", "status", "last_sweep_age_seconds"}
        with pytest.raises(URLError):
            urlopen(f"http://127.0.0.1:{server.port}/jobs", timeout=2)


@pytest.mark.parametrize(
    "payload",
    [
        {"role": "worker", "status": "ready", "last_sweep_age_seconds": 0},
        {"role": "scheduler", "status": "ready", "last_sweep_age_seconds": 91},
        {"role": "scheduler", "status": "starting", "last_sweep_age_seconds": None},
        {"role": "scheduler", "status": "ready", "last_sweep_age_seconds": True},
        {"role": "scheduler", "status": "ready"},
    ],
)
def test_incorrect_or_stale_probe_never_reports_ready(monkeypatch, payload):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            return json.dumps(payload).encode()

    monkeypatch.setattr(system_readiness, "_open", lambda *args, **kwargs: Response())
    assert (
        system_readiness.probe("http://scheduler:8081/healthz", "scheduler")
        == "unavailable"
    )


def test_unconfigured_and_unreachable_states_do_not_expose_details(monkeypatch):
    assert system_readiness.probe("", "scheduler") == "unknown"
    assert (
        system_readiness.probe("http://secret:password@host/healthz", "scheduler")
        == "unavailable"
    )

    def fail(*args, **kwargs):
        raise URLError("secret transport detail")

    monkeypatch.setattr(system_readiness, "_open", fail)
    assert (
        system_readiness.probe("http://scheduler:8081/healthz", "scheduler")
        == "unavailable"
    )


def test_readiness_uses_database_and_requires_all_roles(session, business, monkeypatch):
    monkeypatch.setenv("REALITY_SCHEDULER_HEALTH_URL", "http://scheduler:8081/healthz")
    monkeypatch.delenv("REALITY_WORKER_HEALTH_URL", raising=False)
    monkeypatch.setattr(
        system_readiness, "probe", lambda url, role: "ready" if url else "unknown"
    )
    result = system_readiness.readiness(session, business.tenant.id)
    assert result["status"] == "unknown"
    assert result["components"] == {
        "connection": "ready",
        "scheduler": "ready",
        "worker": "unknown",
    }
    monkeypatch.setenv("REALITY_WORKER_HEALTH_URL", "http://worker:8081/healthz")
    assert system_readiness.readiness(session, business.tenant.id)["status"] == "ready"


from test_playground_api import playground_http as _playground_http

playground_http = _playground_http


def test_readiness_http_requires_company_admission(
    session, playground_http, monkeypatch
):
    client, tenant, user, run, login = playground_http
    run.sandbox_kind = "practice"
    session.flush()
    login(user)
    monkeypatch.delenv("REALITY_SCHEDULER_HEALTH_URL", raising=False)
    monkeypatch.delenv("REALITY_WORKER_HEALTH_URL", raising=False)
    response = client.get(f"/api/tenants/{tenant.id}/readiness")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "unknown"
    assert set(response.json()) == {"status", "components", "observed_at"}
    assert client.get("/api/tenants/foreign/readiness").status_code in (403, 404)


def test_probe_accepts_actual_fresh_health_server():
    with HealthServer("worker", 0) as server:
        server.health.succeeded()
        assert (
            system_readiness.probe(f"http://127.0.0.1:{server.port}/healthz", "worker")
            == "ready"
        )
        server.health.failed()
        assert (
            system_readiness.probe(f"http://127.0.0.1:{server.port}/healthz", "worker")
            == "unavailable"
        )
