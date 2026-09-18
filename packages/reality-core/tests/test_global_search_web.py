"""Transport validates bounds and delegates read-only search."""

from fastapi.testclient import TestClient
from sqlalchemy import event

from reality.web import api as api_module
from reality.web.app import app


def test_search_web_contract_and_no_business_writes(session, business):
    app.dependency_overrides[api_module.database_session] = lambda: session
    writes = []

    def inspect(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    event.listen(session.bind, "before_cursor_execute", inspect)
    try:
        client = TestClient(app)
        url = f"/api/tenants/{business.tenant.id}/search"
        response = client.post(
            url + "/query", json={"provider": "partners", "query": "Muller"}
        )
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["target"]["id"] == business.customer.id
        assert (
            client.post(
                url + "/query", json={"provider": "partners", "tenant_id": "other"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                url + "/query", json={"provider": "orders", "family": "item"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                url + "/query", json={"provider": "orders", "limit": 51}
            ).status_code
            == 422
        )
        assert (
            client.post(
                url + "/resolve",
                json={
                    "targets": [{"record_kind": "party", "id": business.customer.id}]
                },
            ).json()["items"][0]["label"]
            == "Müller GmbH"
        )
        assert writes == []
    finally:
        event.remove(session.bind, "before_cursor_execute", inspect)
        app.dependency_overrides.clear()


def test_search_admission_does_not_block_the_async_event_loop(monkeypatch):
    import asyncio
    import threading
    from contextlib import nullcontext
    from types import SimpleNamespace

    from starlette.requests import Request
    from starlette.responses import PlainTextResponse

    from reality.web import app as web_app

    started = threading.Event()
    release = threading.Event()

    def delayed_user(request, session):
        started.set()
        assert release.wait(timeout=2), (
            "The event loop could not release authorization."
        )
        return SimpleNamespace(status="active", is_platform_admin=False)

    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    monkeypatch.setattr(web_app, "Session", lambda: nullcontext(object()))
    monkeypatch.setattr(web_app, "user_from_request", delayed_user)

    async def next_handler(request):
        return PlainTextResponse("ok")

    async def exercise():
        request = Request(
            {"type": "http", "method": "GET", "path": "/api/auth/me", "headers": []}
        )
        task = asyncio.create_task(
            web_app.protect_application_api(request, next_handler)
        )
        try:
            for _ in range(100):
                if started.is_set():
                    break
                await asyncio.sleep(0.005)
            assert started.is_set()
            assert not task.done()
        finally:
            release.set()
        assert (await task).status_code == 200

    asyncio.run(exercise())
