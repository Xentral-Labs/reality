"""Private sandbox HTTP reads (096/FR-001, FR-003, DR-003)."""

from contextlib import nullcontext
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from reality.db.core import (
    AppUser,
    Item,
    Location,
    PlaygroundRun,
    Tenant,
    TenantMembership,
    UserSession,
    now,
    uid,
)
from reality.web import api, auth
from reality.web import app as web


def test_practice_company_is_shared_with_app(session, playground_http):
    client, tenant, user, run, login = playground_http
    run.sandbox_kind = "practice"
    session.flush()
    login(user)
    bootstrap = client.get("/api/v1/bootstrap").json()
    company = next(row for row in bootstrap["tenants"] if row["id"] == tenant.id)
    assert company["sandbox_run_id"] == run.id
    assert company["purpose"] == "playground"
    response = client.post(
        f"/api/tenants/{tenant.id}/items",
        json={"sku": "APP-ITEM", "name": "Shared item", "unit": "pcs"},
    )
    assert response.status_code == 201, response.text
    item_id = response.json()["id"]
    detail = client.get(f"/api/playground/runs/{run.id}").json()
    assert detail["tenant_id"] == tenant.id
    assert any(
        row["id"] == item_id
        for row in client.get(f"/api/tenants/{detail['tenant_id']}/items").json()
    )
    assert client.get(f"/api/tenants/{tenant.id}/dashboard").status_code == 200
    assert client.get(f"/api/tenants/{tenant.id}/attention").status_code == 200
    assert client.get(f"/api/tenants/{tenant.id}/attention/foreign").status_code == 404

    assert client.get(f"/api/tenants/{tenant.id}/analytics").status_code == 200
    assert (
        client.get(
            f"/api/tenants/{tenant.id}/analytics/contributors?metric=open"
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "restriction", ["temporary", "archived", "revoked", "unverified", "foreign"]
)
def test_shared_company_access_fails_closed(session, playground_http, restriction):
    client, tenant, user, run, login = playground_http
    run.sandbox_kind = "practice"
    if restriction == "temporary":
        run.sandbox_kind = "temporary"
    elif restriction == "archived":
        run.status = "archived"
        run.archived_at = now()
    elif restriction == "unverified":
        user.email_verified_at = None
    elif restriction == "revoked":
        from sqlalchemy import select

        session.scalar(
            select(TenantMembership).where(TenantMembership.tenant_id == tenant.id)
        ).status = "removed"
    else:
        user = AppUser(
            id=uid("usr"),
            email=f"{uid('mail')}@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
            is_platform_admin=True,
        )
        session.add(user)
    session.flush()
    login(user)
    bootstrap = client.get("/api/v1/bootstrap")
    assert tenant.id not in [row["id"] for row in bootstrap.json()["tenants"]]
    assert client.post(
        f"/api/tenants/{tenant.id}/items",
        json={"sku": "DENIED", "name": "Denied", "unit": "pcs"},
    ).status_code in {403, 404}


def test_practice_policy_keeps_external_and_unknown_actions_blocked(
    session, playground_http
):
    from reality.services.tenant_policy import (
        PlaygroundOperationDenied,
        require_business_operation,
    )

    _, tenant, _, run, _ = playground_http
    run.sandbox_kind = "practice"
    session.flush()
    require_business_operation(session, tenant.id, "create_item")
    for operation in (
        "connector_install",
        "invitation_delivery",
        "invitation_create",
        "unknown_future_operation",
        "permanently_delete_tenant",
    ):
        with pytest.raises(PlaygroundOperationDenied):
            require_business_operation(session, tenant.id, operation)


def test_practice_app_uses_normal_source_goods_and_finance_services(
    session, playground_http
):
    from reality.services.core import (
        create_item,
        create_location,
        create_manual_order,
        create_party,
        post_ledger,
        record_movement,
    )

    client, tenant, user, run, login = playground_http
    run.sandbox_kind = "practice"
    session.flush()
    company = create_party(session, tenant.id, "Practice company", "company")
    customer = create_party(session, tenant.id, "Customer", "customer")
    location = create_location(session, tenant.id, "Practice warehouse")
    item = create_item(session, tenant.id, "SHARED", "Shared item", "pcs")
    movement = record_movement(
        session, tenant.id, "receipt", item.id, "12", to_location_id=location.id
    )
    source, document, lines, commitments = create_manual_order(
        session,
        tenant.id,
        "sales",
        "APP-ORDER",
        company.id,
        customer.id,
        location.id,
        [
            {
                "item_id": item.id,
                "quantity": "2",
                "unit": "pcs",
                "label": "Shared item",
                "gross_amount": "50",
            }
        ],
        "50",
    )
    entries = post_ledger(
        session,
        tenant.id,
        document.id,
        customer.id,
        [("accounts_receivable", "debit", "50"), ("sales_revenue", "credit", "50")],
    )
    assert document.source_record_id == source.id
    assert commitments[0].document_line_id == lines[0].id
    assert all(entry.tenant_id == movement.tenant_id == tenant.id for entry in entries)
    login(user)
    reality = client.get(f"/api/playground/runs/{run.id}/reality")
    assert reality.status_code == 200, reality.text
    assert "Shared item" in reality.text


def test_exception_catalog_is_authenticated_and_matches_canonical_metadata(
    playground_http,
):
    from reality.catalogs import (
        load_exception_class_labels,
        load_operational_exception_catalog,
    )

    client, _, user, _, login = playground_http
    assert client.get("/api/playground/exception-catalog").status_code == 401
    login(user)
    response = client.get("/api/playground/exception-catalog")
    assert response.status_code == 200
    catalog = load_operational_exception_catalog()
    labels = load_exception_class_labels()
    fields = ("id", "label", "description", "severity", "owner", "clears_through")
    assert response.json() == {
        "version": catalog.version,
        "classes": [
            {**{key: row[key] for key in fields}, "labels": labels[row["id"]]}
            for row in catalog.classes
        ],
    }
    # Every class carries the German ERP label the resource catalog records.
    assert all(row["labels"]["de"] for row in response.json()["classes"])


@pytest.mark.parametrize("auth_mode", ["enabled", "disabled"])
def test_run_entry_requires_cookie(playground_http, monkeypatch, auth_mode):
    client, _, _, run, _ = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", auth_mode)
    assert client.get("/api/playground").status_code == 401
    assert client.get(f"/api/playground/runs/{run.id}").status_code == 401
    assert client.post("/api/playground/runs", json={}).status_code == 401


@pytest.mark.parametrize("status", ["active", "pending_approval"])
def test_run_entry_lists_only_owned_runs(session, playground_http, monkeypatch, status):
    client, _, user, run, login = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user.status = status
    session.flush()
    login(user)
    response = client.get("/api/playground")
    assert response.status_code == 200, response.text
    body = response.json()
    assert [row["id"] for row in body["runs"]] == [run.id]
    assert body["quotas"]["daily_remaining"] == 4
    assert body["quotas"]["retained_remaining"] == 19
    assert body["entry_enabled"] is True
    assert body["chat_available"] is False
    assert client.get(f"/api/playground/runs/{run.id}").status_code == 200


@pytest.mark.parametrize("status", ["suspended", "rejected", "unverified"])
def test_run_entry_revalidates_account(session, playground_http, status):
    client, _, user, run, login = playground_http
    user.status = "active" if status == "unverified" else status
    if status == "unverified":
        user.email_verified_at = None
    session.flush()
    login(user)
    assert client.get("/api/playground").status_code == 403
    assert client.get(f"/api/playground/runs/{run.id}").status_code == 403
    assert client.post("/api/playground/runs", json={}).status_code == 403


def test_run_entry_has_no_admin_override(session, playground_http):
    client, _, _, run, login = playground_http
    outsider = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
        is_platform_admin=True,
    )
    session.add(outsider)
    session.flush()
    login(outsider)
    assert client.get("/api/playground").json()["runs"] == []
    missing = client.get("/api/playground/runs/missing")
    foreign = client.get(f"/api/playground/runs/{run.id}")
    assert missing.status_code == foreign.status_code == 404
    assert missing.json() == foreign.json()


@pytest.mark.parametrize("status", ["initializing", "initialization_failed"])
def test_run_entry_hides_unready_references(session, playground_http, status):
    client, tenant, user, run, login = playground_http
    run.status, run.ready_at = status, None
    run.initialization_progress = {"items": {"unsafe_partial": "not_ready"}}
    session.flush()
    login(user)
    body = client.get(f"/api/playground/runs/{run.id}").json()
    assert body["status"] == status
    assert body["references"] is None
    assert body["tenant_id"] is None
    assert "not_ready" not in str(body)
    assert client.get(f"/api/tenants/{tenant.id}/items").status_code == 403


@pytest.mark.parametrize("status", ["active", "pending_approval"])
def test_confirmed_http_start_and_replay(session, playground_http, monkeypatch, status):
    client, old_tenant, user, old_run, login = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user.status = status
    old_run.status = "archived"
    old_run.archived_at = old_tenant.archived_at = now()
    session.flush()
    login(user)
    payload = {"request_key": "http-start", "confirmed": True}
    first = client.post("/api/playground/runs", json=payload)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "active"
    assert body["id"] != old_run.id
    assert len(body["references"]["items"]) == 3
    assert len(body["references"]["parties"]) == 4
    assert client.post("/api/playground/runs", json=payload).json() == body
    assert client.get(f"/api/playground/runs/{body['id']}").json() == body
    assert (
        client.post(
            "/api/playground/runs", json={**payload, "request_key": "other"}
        ).status_code
        == 409
    )
    if status == "pending_approval":
        assert (
            client.post("/api/v1/companies", json={"name": "Production"}).status_code
            == 403
        )


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"request_key": "new"}, 403),
        ({"request_key": "new", "confirmed": "true"}, 422),
        ({"request_key": "new", "confirmed": True, "tenant_id": "business"}, 422),
        ({"request_key": "new", "confirmed": True, "user_id": "other"}, 422),
        ({"request_key": " ", "confirmed": True}, 422),
        ({"request_key": "new", "confirmed": True, "preset_version": 2}, 422),
    ],
)
def test_run_start_rejects_unsafe_inputs(
    playground_http, monkeypatch, payload, expected
):
    client, _, user, _, login = playground_http
    login(user)
    assert client.post("/api/playground/runs", json=payload).status_code == expected


def test_scenario_switch_is_confirmed_and_replayable(playground_http, monkeypatch):
    client, _, user, run, login = playground_http
    login(user)
    path = f"/api/playground/runs/{run.id}/restart"
    payload = {
        "preset_key": "partial-delivery",
        "preset_version": 1,
        "request_key": "switch-fixture",
    }
    assert client.post(path, json=payload).status_code == 403
    assert client.get(f"/api/playground/runs/{run.id}").json()["status"] == "active"
    response = client.post(path, json={**payload, "confirmed": True})
    assert response.status_code == 200, response.text
    assert response.json()["preset_key"] == "partial-delivery"
    repeated = client.post(path, json={**payload, "confirmed": True})
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["id"] == response.json()["id"]


def test_run_start_quota(playground_http, monkeypatch):
    client, _, user, _run, login = playground_http
    login(user)
    payload = {"request_key": "new", "confirmed": True}
    monkeypatch.setenv("REALITY_PLAYGROUND_RETAINED_RUN_LIMIT", "1")
    response = client.post("/api/playground/runs", json=payload)
    assert response.status_code == 429, response.text
    assert response.json()["code"] == "playground_run_quota_exceeded"
    assert response.json()["quotas"]["retained_remaining"] == 0
    assert response.json()["quotas"]["daily_resets_at"]


def _http_step_references(session, run):
    item = Item(
        id=uid("itm"), tenant_id=run.tenant_id, sku="BIKE-LIGHT", name="Bike Light"
    )
    location = Location(id=uid("loc"), tenant_id=run.tenant_id, name="Warehouse")
    session.add_all([item, location])
    run.initialization_progress = {
        "items": {"BIKE-LIGHT": item.id},
        "locations": {"warehouse": location.id},
    }
    session.flush()
    return run.initialization_progress


def test_step_http_prepare_confirm_reject_and_owner_boundary(
    session, playground_http, monkeypatch
):
    client, _tenant, user, run, login = playground_http
    login(user)
    references = _http_step_references(session, run)
    payload = {
        "request_key": "opening-http",
        "tool_name": "movement_create",
        "arguments": {
            "movement_type": "opening_stock",
            "item_id": references["items"]["BIKE-LIGHT"],
            "to_location_id": references["locations"]["warehouse"],
            "quantity": "20",
        },
    }
    prepared = client.post(f"/api/playground/runs/{run.id}/steps", json=payload)
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["status"] == "proposed" and body["preview"]["targets"]
    replay = client.post(f"/api/playground/runs/{run.id}/steps", json=payload)
    assert replay.status_code == 200 and replay.json() == body
    detail = client.get(f"/api/playground/runs/{run.id}/steps/{body['step_id']}")
    assert detail.status_code == 200 and detail.json()["receipt"] is None
    run_detail = client.get(f"/api/playground/runs/{run.id}")
    assert run_detail.status_code == 200
    assert [step["step_id"] for step in run_detail.json()["steps"]] == [body["step_id"]]
    reality = client.get(f"/api/playground/runs/{run.id}/reality")
    assert reality.status_code == 200
    assert {
        "inventory",
        "exceptions",
        "events",
        "event_sequence",
    } <= reality.json().keys()
    confirmed = client.post(
        f"/api/playground/runs/{run.id}/steps/{body['step_id']}/confirm",
        json={"preview_revision": body["preview"]["revision"], "confirmed": True},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "executed"
    assert confirmed.json()["receipt"]["after"]["physical"] == "20.0000"

    outsider = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(outsider)
    session.flush()
    login(outsider)
    denied = client.get(f"/api/playground/runs/{run.id}/steps/{body['step_id']}")
    assert denied.status_code == 404


def test_http_financial_story_and_preview_boundaries(
    session, playground_http, monkeypatch
):
    client, tenant, user, old, login = playground_http
    old.status = "archived"
    old.archived_at = tenant.archived_at = now()
    session.flush()
    login(user)
    response = client.post(
        "/api/playground/runs", json={"request_key": "finance-http", "confirmed": True}
    )
    assert response.status_code == 200, response.text
    run = response.json()
    refs = run["references"]
    base = f"/api/playground/runs/{run['id']}/steps"

    def execute(tool, args):
        prepared = client.post(
            base,
            json={"request_key": uid("request"), "tool_name": tool, "arguments": args},
        )
        assert prepared.status_code == 200, prepared.text
        review = prepared.json()
        detail = client.get(f"{base}/{review['step_id']}").json()
        assert detail["status"] == "proposed" and detail["receipt"] is None
        confirmation = {
            "preview_revision": review["preview"]["revision"],
            "confirmed": True,
        }
        if tool in {"sales_invoice_record", "customer_payment_post"}:
            wrong = client.post(
                f"{base}/{review['step_id']}/confirm",
                json={**confirmation, "preview_revision": "wrong"},
            )
            assert wrong.status_code == 409
        confirmed = client.post(
            f"{base}/{review['step_id']}/confirm", json=confirmation
        )
        assert confirmed.status_code == 200, confirmed.text
        result = confirmed.json()
        assert result["status"] == "executed" and result["receipt"], result
        replay = client.post(f"{base}/{review['step_id']}/confirm", json=confirmation)
        assert replay.json()["receipt"] == result["receipt"]
        return result

    item, location = refs["items"]["BIKE-LIGHT"], refs["locations"]["warehouse"]
    execute(
        "movement_create",
        {
            "movement_type": "opening_stock",
            "item_id": item,
            "to_location_id": location,
            "quantity": "12",
        },
    )
    order = execute(
        "order_create",
        {
            "direction": "sales",
            "number": "SO-HTTP",
            "company_party_id": refs["parties"]["company"],
            "counterparty_id": refs["parties"]["customer_huber"],
            "location_id": location,
            "item_id": item,
            "quantity": "12",
            "unit_price": "25",
        },
    )
    records = order["receipt"]["records"]
    commitment = next(row["id"] for row in records if row["family"] == "commitment")
    line = next(row["id"] for row in records if row["family"] == "document_line")
    invoice_args = {
        "order_line_id": line,
        "quantity": "12",
        "gross_amount": "300",
        "number": "INV-HTTP",
    }
    too_early = client.post(
        base,
        json={
            "request_key": "early",
            "tool_name": "sales_invoice_record",
            "arguments": invoice_args,
        },
    )
    assert too_early.status_code == 422
    execute("reserve", {"commitment_id": commitment, "quantity": "12"})
    execute(
        "movement_create",
        {
            "movement_type": "shipment",
            "commitment_id": commitment,
            "item_id": item,
            "from_location_id": location,
            "quantity": "12",
        },
    )
    delivered = client.get(f"/api/playground/runs/{run['id']}/reality").json()
    assert any(
        row["class_id"] == "shipped_not_billed" for row in delivered["exceptions"]
    )
    invoice = execute("sales_invoice_record", invoice_args)
    invoice_id = invoice["receipt"]["after"]["document_id"]
    assert Decimal(invoice["receipt"]["after"]["open_amount"]) == 300
    payment_args = {
        "invoice_id": invoice_id,
        "amount": "301",
        "payment_number": "PAY-HTTP",
    }
    excessive = client.post(
        base,
        json={
            "request_key": "excessive",
            "tool_name": "customer_payment_post",
            "arguments": payment_args,
        },
    )
    assert excessive.status_code == 422
    payment = execute("customer_payment_post", {**payment_args, "amount": "300"})
    assert Decimal(payment["receipt"]["after"]["open_amount"]) == 0
    money = client.get(f"/api/tenants/{run['tenant_id']}/finance/open-items")
    assert money.status_code == 200
    current = client.get(f"/api/playground/runs/{run['id']}/reality").json()
    assert not any(
        row["class_id"] == "shipped_not_billed" for row in current["exceptions"]
    )


def test_step_http_requires_confirmation_and_rejection_has_no_effect(
    session, playground_http, monkeypatch
):
    client, _tenant, user, run, login = playground_http
    login(user)
    references = _http_step_references(session, run)
    payload = {
        "request_key": "reject-http",
        "tool_name": "movement_create",
        "arguments": {
            "movement_type": "opening_stock",
            "item_id": references["items"]["BIKE-LIGHT"],
            "to_location_id": references["locations"]["warehouse"],
            "quantity": "20",
        },
    }
    prepared = client.post(f"/api/playground/runs/{run.id}/steps", json=payload).json()
    not_confirmed = client.post(
        f"/api/playground/runs/{run.id}/steps/{prepared['step_id']}/reject", json={}
    )
    assert not_confirmed.status_code == 403
    rejected = client.post(
        f"/api/playground/runs/{run.id}/steps/{prepared['step_id']}/reject",
        json={"confirmed": True},
    )
    assert rejected.status_code == 200 and rejected.json()["status"] == "rejected"
    run_detail = client.get(f"/api/playground/runs/{run.id}")
    assert run_detail.status_code == 200
    assert run_detail.json()["steps"][0]["status"] == "rejected"
    assert client.get(f"/api/playground/runs/{run.id}/reality").status_code == 200


def test_run_entry_requires_current_membership(session, playground_http):
    from sqlalchemy import select

    client, tenant, user, run, login = playground_http
    login(user)
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant.id,
            TenantMembership.user_id == user.id,
        )
    )
    member.status = "removed"
    session.flush()
    assert client.get("/api/playground").json()["runs"] == []
    assert client.get(f"/api/playground/runs/{run.id}").status_code == 404


@pytest.mark.parametrize("invalid_cookie", ["expired", "revoked"])
def test_run_entry_rejects_invalid_cookie(session, playground_http, invalid_cookie):
    from sqlalchemy import select

    client, _, user, _, login = playground_http
    login(user)
    cookie = session.scalar(select(UserSession).where(UserSession.user_id == user.id))
    if invalid_cookie == "expired":
        cookie.expires_at = now() - timedelta(seconds=1)
    else:
        cookie.revoked_at = now()
    session.flush()
    assert client.get("/api/playground").status_code == 401


def test_run_entry_has_bounded_pages(playground_http):
    client, _, user, run, login = playground_http
    login(user)
    first = client.get("/api/playground?limit=1").json()
    assert first["total"] == 1
    assert first["runs"][0]["id"] == run.id
    second = client.get("/api/playground?limit=1&offset=1").json()
    assert second["total"] == 1
    assert second["runs"] == []
    assert client.get("/api/playground?limit=101").status_code == 422
    assert client.get("/api/playground?offset=-1").status_code == 422


def test_http_seed_failure_is_not_success_and_retries_same_run(
    session, playground_http, monkeypatch
):
    from reality.services import playground

    client, tenant, user, run, login = playground_http
    run.status = "archived"
    run.archived_at = tenant.archived_at = now()
    session.flush()
    login(user)
    seed = playground._seed_references

    def unavailable(*_args):
        raise RuntimeError("Do not leak this internal exception")

    monkeypatch.setattr(playground, "_seed_references", unavailable)
    payload = {"request_key": "retry-setup", "confirmed": True}
    response = client.post("/api/playground/runs", json=payload)
    assert response.status_code == 200
    failed = response.json()
    assert failed["status"] == "initialization_failed"
    assert failed["initialization_error_code"] == "seed_failed"
    assert failed["references"] is None
    saved = client.get(f"/api/playground/runs/{failed['id']}").json()
    assert saved["request_key"] == payload["request_key"]
    assert "internal exception" not in response.text
    monkeypatch.setattr(playground, "_seed_references", seed)
    ready = client.post(
        "/api/playground/runs",
        json={"request_key": saved["request_key"], "confirmed": True},
    ).json()
    assert ready["id"] == failed["id"]
    assert ready["status"] == "active"
    assert len(ready["references"]["items"]) == 3


@pytest.fixture
def playground_http(session, monkeypatch):
    tenant = Tenant(id=uid("ten"), name="Private experiment", purpose="playground")
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add_all([tenant, user])
    session.flush()
    from reality.services.finance.accounts import _bootstrap_accounts

    _bootstrap_accounts(session, tenant.id)
    run = PlaygroundRun(
        id=uid("pgr"),
        tenant_id=tenant.id,
        owner_user_id=user.id,
        preset_key="trading",
        preset_version=1,
        lesson_key="order-stock",
        lesson_version=1,
        client_request_key=uid("req"),
        status="active",
        ready_at=now(),
    )
    session.add_all(
        [run, TenantMembership(id=uid("tmb"), tenant_id=tenant.id, user_id=user.id)]
    )
    session.flush()
    monkeypatch.setattr(web, "Session", lambda: nullcontext(session))

    def database_session():
        yield session

    monkeypatch.setitem(
        web.app.dependency_overrides, api.database_session, database_session
    )
    client = TestClient(web.app)

    def login(account):
        token = uid("session")
        session.add(
            UserSession(
                id=uid("ses"),
                user_id=account.id,
                token_hash=auth.digest(token),
                expires_at=now() + timedelta(days=1),
            )
        )
        session.flush()
        client.cookies.set(auth.COOKIE_NAME, token)

    return client, tenant, user, run, login


@pytest.mark.parametrize("auth_mode", ["enabled", "disabled"])
def test_sandbox_requires_real_login_even_in_local_mode(
    playground_http, monkeypatch, auth_mode
):
    client, tenant, _, _, _ = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", auth_mode)
    assert client.get(f"/api/tenants/{tenant.id}/items").status_code == 401


@pytest.mark.parametrize("status", ["active", "pending_approval"])
@pytest.mark.parametrize("archived", [False, True])
def test_owner_can_read_active_and_archived_runs_without_production_admission(
    session, playground_http, monkeypatch, status, archived
):
    client, tenant, user, run, login = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user.status = status
    if archived:
        run.status = "archived"
        run.archived_at = tenant.archived_at = now()
    session.flush()
    login(user)
    response = client.get(f"/api/tenants/{tenant.id}/items")
    assert response.status_code == 200, response.text
    assert response.json() == []
    if status == "pending_approval":
        assert (
            client.post("/api/v1/companies", json={"name": "Real business"}).status_code
            == 403
        )


def test_admin_cannot_inspect_someone_elses_run(session, playground_http, monkeypatch):
    client, tenant, _, _, login = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
        is_platform_admin=True,
    )
    session.add(user)
    session.flush()
    login(user)
    assert client.get(f"/api/tenants/{tenant.id}/items").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "settings/members",
        "explorer",
        "integrations",
        "copilot",
        "inspector/secret/unknown",
    ],
)
def test_even_owner_cannot_read_unapproved_sandbox_surfaces(playground_http, path):
    client, tenant, user, _, login = playground_http
    login(user)
    assert client.get(f"/api/tenants/{tenant.id}/{path}").status_code == 403


def test_company_selectors_do_not_disclose_sandboxes(playground_http):
    client, tenant, _, _, _ = playground_http
    for path in ("/api/v1/bootstrap", "/api/v1/companies"):
        response = client.get(path)
        assert response.status_code == 200
        assert tenant.id not in response.text
        assert tenant.name not in response.text


@pytest.mark.parametrize("verified", [False, True])
def test_unavailable_account_cannot_read_run(session, playground_http, verified):
    client, tenant, user, _, login = playground_http
    user.email_verified_at = now() if verified else None
    user.status = "suspended" if verified else "active"
    session.flush()
    login(user)
    assert client.get(f"/api/tenants/{tenant.id}/items").status_code == 403


@pytest.mark.parametrize("run_status", ["initializing", "initialization_failed"])
def test_not_ready_run_cannot_be_inspected(session, playground_http, run_status):
    client, tenant, user, run, login = playground_http
    run.status = run_status
    run.ready_at = None
    session.flush()
    login(user)
    assert client.get(f"/api/tenants/{tenant.id}/items").status_code == 403


def test_pending_owner_cannot_read_own_business(session, playground_http, monkeypatch):
    client, _, user, _, login = playground_http
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    user.status = "pending_approval"
    business = Tenant(id=uid("ten"), name="Real company")
    session.add(business)
    session.flush()
    session.add(TenantMembership(id=uid("tmb"), tenant_id=business.id, user_id=user.id))
    session.flush()
    login(user)
    assert client.get(f"/api/tenants/{business.id}/items").status_code == 403


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("path", ["items", "settings/mcp/tokens"])
def test_owner_cannot_mutate_through_generic_routes(
    session, playground_http, archived, path
):
    client, tenant, user, run, login = playground_http
    if archived:
        run.status = "archived"
        run.archived_at = tenant.archived_at = now()
    session.flush()
    login(user)
    response = client.post(f"/api/tenants/{tenant.id}/{path}", json={"name": "Test"})
    assert response.status_code == 403
    assert response.json()["code"] == "playground_operation_denied"


@pytest.mark.parametrize("prefix", ["items", "inspector/item"])
def test_owned_run_does_not_expose_foreign_record_ids(session, playground_http, prefix):
    client, tenant, user, _, login = playground_http
    business = Tenant(id=uid("ten"), name="Foreign company")
    session.add(business)
    session.flush()
    item = Item(
        id=uid("itm"), tenant_id=business.id, sku="PRIVATE", name="Private item"
    )
    session.add(item)
    session.flush()
    login(user)
    response = client.get(f"/api/tenants/{tenant.id}/{prefix}/{item.id}")
    assert response.status_code == 404
    assert item.name not in response.text


def test_platform_company_overview_excludes_private_runs(session, playground_http):
    from reality.services.platform import companies_overview

    _, tenant, _, _, _ = playground_http
    overview = companies_overview(session)
    assert tenant.id not in {row["id"] for row in overview["rows"]}
    assert overview["total"] == 0
    assert overview["archived"] == 0


@pytest.mark.parametrize(
    "path",
    [
        "warehouse/stock",
        "warehouse/reservations",
        "warehouse/movements",
        "master-data?family=item",
        "master-data?family=customer",
        "master-data?family=supplier",
        "master-data?family=location",
        "data-sources/systems",
        "data-sources/records",
    ],
)
def test_ready_sandbox_business_reads_keep_authentication_and_ownership(
    session, playground_http, path
):
    client, tenant, user, run, login = playground_http
    run.sandbox_kind = "practice"
    session.flush()
    url = f"/api/tenants/{tenant.id}/{path}"
    assert client.get(url).status_code == 401
    login(user)
    response = client.get(url)
    assert response.status_code == 200, response.text
    foreign = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(foreign)
    session.flush()
    login(foreign)
    assert client.get(url).status_code == 404


def test_sandbox_archive_and_restore_are_confirmed_owner_actions(playground_http):
    """Spec 186: the danger zone archives and restores a sandbox through the run API."""
    client, _tenant, user, run, login = playground_http
    login(user)
    archive = f"/api/playground/runs/{run.id}/archive"
    restore = f"/api/playground/runs/{run.id}/restore"
    assert client.post(archive, json={}).status_code == 403
    assert client.get(f"/api/playground/runs/{run.id}").json()["status"] == "active"
    response = client.post(archive, json={"confirmed": True})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "archived"
    assert response.json()["archived_at"] is not None
    assert client.post(archive, json={"confirmed": True}).status_code == 409
    assert client.post(restore, json={}).status_code == 403
    restored = client.post(restore, json={"confirmed": True})
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "active"
    assert restored.json()["archived_at"] is None
    missing = client.post(
        f"/api/playground/runs/{uid('pgr')}/archive", json={"confirmed": True}
    )
    assert missing.status_code == 404
