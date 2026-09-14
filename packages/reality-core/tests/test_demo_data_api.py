from test_playground_api import playground_http as _playground_http

playground_http = _playground_http


def test_pending_integration_only_uses_owned_playground_routes(
    session, playground_http, monkeypatch
):
    from reality.services import company_setup

    client, _, user, _, login = playground_http
    monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", "true")
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user.status = "pending_approval"
    session.commit()
    login(user)
    setup = company_setup.create_company(
        session,
        user.id,
        "api-demo-source",
        "Source Practice",
        "sandbox",
        "empty",
        confirmed=True,
    )
    prefix = f"/api/playground/runs/{setup['run_id']}/demo-data"
    preview = client.get(prefix + "/preview")
    assert preview.status_code == 200, preview.text
    assert client.get(f"/api/tenants/{setup['tenant_id']}/demo-data").status_code == 403
    assert client.get("/api/playground/runs/foreign/demo-data").status_code == 404
    body = {
        "request_key": "api-connect",
        "preview_fingerprint": preview.json()["fingerprint"],
        "confirmed": True,
    }
    connected = client.post(prefix + "/connect", json=body)
    assert connected.status_code == 200, connected.text
    assert connected.json()["state"] == "stopped"
    assert client.get(prefix + "/imports").json()["items"] == []
    recent = client.get(prefix + "/imports?recent=true")
    assert recent.status_code == 200
    assert recent.json() == {"items": [], "next_cursor": None, "has_more": False}
    assert (
        client.get(
            "/api/playground/runs/foreign/demo-data/imports?recent=true"
        ).status_code
        == 404
    )
    assert client.get(prefix + "/imports?limit=101").status_code == 422
    assert (
        client.post(
            prefix + "/control",
            json={
                "action": "start",
                "expected_revision": connected.json()["revision"],
                "request_key": "api-start",
                "confirmed": False,
            },
        ).status_code
        == 422
    )
