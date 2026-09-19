"""The desktop transport reuses authenticated company setup without public signup."""

from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from reality.services import desktop_identity
from reality.services.account_sessions import issue_session
from reality.web.desktop import create_desktop_app


@pytest.fixture
def desktop_client(session, tmp_path, monkeypatch, request):
    from reality.web import api, app, auth

    session.info["desktop_installation_id"] = str(uuid4())
    user = desktop_identity.bootstrap_owner(
        session, session.info["desktop_installation_id"]
    )
    session.info["desktop_owner_id"] = user.id
    token = issue_session(session, user)
    session.flush()

    @contextmanager
    def factory():
        yield session

    for module in (api, app, auth):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    (tmp_path / "index.html").write_text("<html>Reality product</html>")
    (tmp_path / "assets").mkdir()
    instance = create_desktop_app(
        origin="http://127.0.0.1:49123",
        frontend=tmp_path,
        session_factory=factory,
        product=app.app,
        development=getattr(request, "param", False),
    )
    with TestClient(instance, base_url="http://127.0.0.1:49123") as client:
        client.cookies.set("reality_session", token)
        yield client


def test_cookie_required_for_static_and_api(desktop_client):
    assert desktop_client.get("/app").status_code == 200
    assert desktop_client.get("/api/auth/me").status_code == 200
    desktop_client.cookies.clear()
    assert desktop_client.get("/app").status_code == 401
    assert desktop_client.get("/api/auth/me").status_code == 401


def test_exact_host_origin_and_hosted_routes_denied(desktop_client):
    assert (
        desktop_client.get("/api/auth/me", headers={"Host": "evil.example"}).status_code
        == 403
    )
    assert (
        desktop_client.get(
            "/api/auth/me", headers={"Origin": "http://localhost:49123"}
        ).status_code
        == 403
    )
    assert (
        desktop_client.post(
            "/api/auth/signup", headers={"Origin": "http://127.0.0.1:49123"}, json={}
        ).status_code
        == 404
    )
    assert desktop_client.get("/api/admin/overview").status_code == 404
    assert desktop_client.post("/api/company-setup", json={}).status_code == 403


def test_existing_company_setup_then_real_product_reads(desktop_client):
    assert desktop_client.get("/api/company-setup/options").json()["environments"] == [
        "business",
        "sandbox",
    ]
    payload = {
        "request_key": "native-first-company",
        "name": "Desktop test company",
        "environment": "business",
        "content": "empty",
        "confirmed": True,
    }
    response = desktop_client.post(
        "/api/company-setup", json=payload, headers={"Origin": "http://127.0.0.1:49123"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "ready"
    replay = desktop_client.post(
        "/api/company-setup", json=payload, headers={"Origin": "http://127.0.0.1:49123"}
    )
    assert replay.json()["tenant_id"] == response.json()["tenant_id"]
    assert desktop_client.get("/api/tenants/not-owned/bootstrap").status_code == 404


@pytest.mark.parametrize("desktop_client", [True], indirect=True)
def test_development_setup_exposes_shared_demo_and_ai_choices(desktop_client):
    assert desktop_client.get("/api/company-setup/options").json()["environments"] == [
        "business",
        "sandbox",
    ]
    headers = {"Origin": "http://127.0.0.1:49123"}
    demo = desktop_client.post(
        "/api/company-setup",
        headers=headers,
        json={
            "request_key": "native-live-demo",
            "name": "Live desktop demo",
            "environment": "sandbox",
            "content": "international_demo",
            "live_simulation": True,
            "confirmed": True,
        },
    )
    assert demo.status_code == 201, demo.text
    assert demo.json()["status"] == "initializing"
    assert demo.json()["preparation"] == "queued"
    assert (
        desktop_client.put(
            "/api/tenants/unknown/settings/ai", headers=headers, json={}
        ).status_code
        == 404
    )
    test_existing_company_setup_then_real_product_reads_for_development(desktop_client)


def test_existing_company_setup_then_real_product_reads_for_development(desktop_client):
    payload = {
        "request_key": "native-empty",
        "name": "Empty desktop company",
        "environment": "business",
        "content": "empty",
        "confirmed": True,
    }
    response = desktop_client.post(
        "/api/company-setup", json=payload, headers={"Origin": "http://127.0.0.1:49123"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "ready"
