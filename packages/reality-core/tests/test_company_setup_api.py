from conftest import seed_company
from test_playground_api import playground_http as _playground_http

playground_http = _playground_http


def test_setup_routes_pending_isolation_and_exact_destination(
    session, playground_http, monkeypatch
):
    client, _, user, _, login = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user.status = "pending_approval"
    session.flush()
    login(user)
    options = client.get("/api/company-setup/options")
    assert options.status_code == 200, options.text
    assert options.json()["environments"] == ["sandbox"]
    assert client.get("/api/v1/bootstrap").status_code == 403
    body = {
        "request_key": "http-setup",
        "name": "My Practice",
        "environment": "sandbox",
        "content": "empty",
        "confirmed": True,
    }
    result = client.post("/api/company-setup", json=body)
    assert result.status_code == 201, result.text
    created = result.json()
    assert created["destination"] == f"/playground/runs/{created['run_id']}"
    assert (
        client.get("/api/company-setup/requests/http-setup").json()["tenant_id"]
        == created["tenant_id"]
    )
    assert (
        client.post(
            "/api/company-setup", json={**body, "environment": "business"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/company-setup",
            json={**body, "request_key": "denied", "environment": "business"},
        ).status_code
        == 403
    )
    assert client.get("/api/company-setup/requests/unknown").status_code == 404
    assert client.get("/api/company-setup/arbitrary").status_code == 403


def test_options_prefill_is_application_metadata_without_company_creation(
    session, playground_http
):
    from sqlalchemy import func, select

    from reality.db.core import AccessApplication, Tenant, uid

    client, _tenant, user, _run, login = playground_http
    session.add(
        AccessApplication(
            id=uid("app"), user_id=user.id, company_name="Northstar Request"
        )
    )
    session.flush()
    login(user)
    before = session.scalar(select(func.count()).select_from(Tenant))
    result = client.get("/api/company-setup/options")
    assert result.status_code == 200
    assert result.json()["suggested_name"] == "Northstar Request"
    assert session.scalar(select(func.count()).select_from(Tenant)) == before


def test_live_creation_api_connects_and_starts_without_extra_requests(
    session, playground_http, monkeypatch
):
    from reality.services import demo_data

    client, _, user, _, login = playground_http
    login(user)
    body = {
        "request_key": "live-api",
        "name": "Live API",
        "environment": "sandbox",
        "content": "international_demo",
        "live_simulation": True,
        "confirmed": True,
    }
    assert (
        client.post(
            "/api/company-setup", json={**body, "live_simulation": "true"}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/company-setup", json={**body, "content": "empty"}).status_code
        == 422
    )
    created = client.post("/api/company-setup", json=body)
    assert created.status_code == 201, created.text
    # Feature 199: the request answers before the profile is seeded; the worker seeds
    # it and completes the live setup, and the receipt reports that.
    assert created.json()["status"] == "initializing"
    tenant = created.json()["tenant_id"]
    assert seed_company(session, tenant) == "succeeded"
    assert (
        client.get("/api/company-setup/requests/live-api").json()["status"] == "ready"
    )
    assert demo_data.status(session, tenant, user.id)["state"] == "running"


def test_free_entry_requires_explicit_signup_consent_and_reads_do_not_create(
    session, playground_http
):
    from sqlalchemy import func, select

    from reality.db.core import Tenant
    from reality.services.free_playground import request_entry

    client, _, user, _, login = playground_http
    login(user)
    before = session.scalar(select(func.count()).select_from(Tenant))
    state = client.get("/api/company-setup/playground")
    assert state.status_code == 200
    assert not state.json()["requested"]
    assert (
        client.post(
            "/api/company-setup/playground", json={"confirmed": True}
        ).status_code
        == 422
    )
    request_entry(session, user.id)
    session.flush()
    assert client.get("/api/company-setup/playground").json()["requested"]
    assert session.scalar(select(func.count()).select_from(Tenant)) == before
    assert (
        client.post(
            "/api/company-setup/playground", json={"confirmed": False}
        ).status_code
        == 422
    )


def test_free_entry_accepts_only_the_two_offered_starts(session, playground_http):
    """Feature 198: the chosen start is a closed set and the demo is the default."""
    from reality.db.core import PlaygroundRun
    from reality.services.free_playground import request_entry

    client, _, user, _, login = playground_http
    login(user)
    request_entry(session, user.id)
    session.flush()
    assert (
        client.post(
            "/api/company-setup/playground",
            json={"confirmed": True, "content": "storyline"},
        ).status_code
        == 422
    )
    created = client.post(
        "/api/company-setup/playground", json={"confirmed": True, "content": "empty"}
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "ready"
    assert (
        session.get(PlaygroundRun, created.json()["run_id"]).preset_key
        == "company-empty"
    )
    assert (
        client.get("/api/company-setup/playground").json()["receipt"]["tenant_id"]
        == created.json()["tenant_id"]
    )
