"""Unified financial reversal effects and attributable recovery."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from test_unified_invoice_entry import confirm
from test_unified_payment_entry import obligation
from test_unified_payment_entry import prepare as prepare_payment

from reality.db.core import BusinessEvent, LedgerEntry, LedgerReversal
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)


def fixture(session, b, direction="customer"):
    invoice = obligation(session, b, direction)
    payment = (
        core.post_customer_payment
        if direction == "customer"
        else core.post_supplier_payment
    )(session, b.tenant.id, invoice.id, "125")
    group = core._settlement_control_entry(
        session, b.tenant.id, invoice.id
    ).posting_group_id
    return invoice, group, payment[0].posting_group_id


def prepare(session, b, group, request="reverse-123", reason="Incorrect entry"):
    return prepare_delivery_action(
        session,
        b.tenant.id,
        "ledger_reverse",
        {"posting_group_id": group, "reason": reason},
        request_id=request,
    )


@pytest.mark.parametrize("direction", ["customer", "supplier"])
@pytest.mark.parametrize("target", ["invoice", "payment"])
def test_exact_effects_and_recovery(session, business, direction, target):
    invoice, invoice_group, payment_group = fixture(session, business, direction)
    p = prepare(
        session, business, invoice_group if target == "invoice" else payment_group
    )
    review = json.loads(p.input)["_delivery_review"]
    effects = review["state"]["effects"]
    row = next(r for r in effects["invoices"] if r["id"] == invoice.id)
    assert Decimal(row["before"]) == 175
    assert Decimal(row["after"]) == (0 if target == "invoice" else 300)
    payment = effects["payments"][0]
    assert Decimal(payment["before"]) == 0
    assert Decimal(payment["after"]) == (125 if target == "invoice" else 0)
    assert len(effects["newly_inactive"]) == 1
    assert session.scalar(select(func.count()).select_from(LedgerReversal)) == 0
    confirm(session, business, p)
    detail = delivery_proposal_detail(session, business.tenant.id, p.id)
    assert detail["verification"] == "verified"
    assert core.open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(
        row["after"]
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.action_id == p.id,
            BusinessEvent.event_type == "ledger.reversed",
        )
    )
    assert event and event.correlation_id == p.id
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    p.status = "executing"
    p.output = "{}"
    session.commit()
    assert (
        reconcile_delivery(session, business.tenant.id, p.id)["receipt"]
        == detail["receipt"]
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before


def test_counterpart_change_stale_then_historical_proof(session, business):
    _invoice, ig, pg = fixture(session, business)
    p = prepare(session, business, ig)
    core.reverse_ledger_posting_group(
        session, business.tenant.id, pg, reason="Counterpart"
    )
    with pytest.raises(core.InvalidOperation, match="changed"):
        confirm(session, business, p)
    fresh = prepare(session, business, ig, request="fresh")
    effects = json.loads(fresh.input)["_delivery_review"]["state"]["effects"]
    assert not effects["newly_inactive"] and len(effects["already_inactive"]) == 1
    confirm(session, business, fresh)
    assert (
        delivery_proposal_detail(session, business.tenant.id, fresh.id)["verification"]
        == "verified"
    )


def test_overlap_with_payments_both_directions(session, business):
    invoice, ig, pg = fixture(session, business)
    p = prepare(session, business, pg)
    p.status = "executing"
    session.commit()
    with pytest.raises(core.InvalidOperation, match="unresolved"):
        prepare_payment(session, business, invoice)
    p.status = "rejected"
    session.commit()
    payment = prepare_payment(session, business, invoice)
    payment.status = "executing"
    session.commit()
    with pytest.raises(core.InvalidOperation, match="unresolved"):
        prepare(session, business, ig, request="blocked")


def test_foreign_reason_and_reversing_group(session, business):
    _, ig, _ = fixture(session, business)
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, ig, reason=" ")
    foreign = core.create_tenant(session, "Foreign")
    with pytest.raises(core.NotFound):
        prepare_delivery_action(
            session,
            foreign.id,
            "ledger_reverse",
            {"posting_group_id": ig, "reason": "No"},
            request_id="foreign",
        )
    p = prepare(session, business, ig)
    confirm(session, business, p)
    result = json.loads(p.output)
    with pytest.raises(core.InvalidOperation):
        prepare(
            session, business, result["reversing_posting_group_id"], request="inverse"
        )


def test_event_tampering_cannot_verify(session, business):
    _, ig, _ = fixture(session, business)
    p = prepare(session, business, ig)
    confirm(session, business, p)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.action_id == p.id,
            BusinessEvent.event_type == "ledger.reversed",
        )
    )
    payload = json.loads(event.payload)
    payload["reason"] = "Different"
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, p.id)["verification"]
        == "unresolved"
    )


def test_choices_are_scoped_grouped_and_exclude_reversals(session, business):
    from reality.services.financial_reversal_actions import _reversal_choices

    _, ig, pg = fixture(session, business)
    rows = _reversal_choices(session, business.tenant.id)
    assert rows["page"]["total"] == 2
    assert {r["id"] for r in rows["items"]} == {ig, pg}
    assert (
        _reversal_choices(session, business.tenant.id, "INV-121")["page"]["total"] == 1
    )
    foreign = core.create_tenant(session, "Foreign choices")
    assert not _reversal_choices(session, foreign.id)["items"]
    core.reverse_ledger_posting_group(
        session, business.tenant.id, ig, reason="Duplicate"
    )
    assert [
        r["id"] for r in _reversal_choices(session, business.tenant.id)["items"]
    ] == [pg]


def test_historical_proof_survives_later_counterpart_reversal(session, business):
    _, ig, pg = fixture(session, business)
    p = prepare(session, business, pg)
    confirm(session, business, p)
    original = delivery_proposal_detail(session, business.tenant.id, p.id)["receipt"]
    core.reverse_ledger_posting_group(
        session, business.tenant.id, ig, reason="Later correction"
    )
    detail = delivery_proposal_detail(session, business.tenant.id, p.id)
    assert detail["verification"] == "verified" and detail["receipt"] == original
    assert Decimal(detail["observation"]["invoices"][0]["before"]) == 0


def test_current_actor_and_practice_are_required(session, business):
    from types import SimpleNamespace

    from reality.tools.application import approve_and_execute_proposal

    _, ig, _ = fixture(session, business)
    p = prepare(session, business, ig)
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, p.id)
    with pytest.raises(core.NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            p.id,
            confirmed=True,
            review_token=json.loads(p.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="missing", is_platform_admin=False
            ),
        )
    from reality.db.core import Tenant

    practice = Tenant(id=core.uid("ten"), name="Practice", purpose="playground")
    session.add(practice)
    session.commit()
    with pytest.raises(core.InvalidOperation, match="practice"):
        prepare_delivery_action(
            session,
            practice.id,
            "ledger_reverse",
            {"posting_group_id": ig, "reason": "Test"},
            request_id="practice",
        )


def test_reversal_http_choices_and_confirmation(session, business):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    _, ig, _ = fixture(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            result = client.get(f"{base}/finance/reversal-choices?q=INV-121")
            assert result.status_code == 200, result.text
            assert len(result.json()["items"]) == 1
            result = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "ledger_reverse",
                    "request_id": "http-reverse",
                    "arguments": {"posting_group_id": ig, "reason": "Wrong invoice"},
                },
            )
            assert result.status_code == 200, result.text
            proposal = result.json()
            result = client.post(
                f"{base}/change-proposals/{proposal['id']}/approve",
                json={"confirmed": True, "review_token": proposal["review"]["token"]},
            )
            assert result.status_code == 200, result.text
            assert (
                client.get(f"{base}/delivery-actions/{proposal['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()


def test_missing_attribution_and_inverse_tampering_stay_unresolved(session, business):
    _, ig, _ = fixture(session, business)
    p = prepare(session, business, ig)
    confirm(session, business, p)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.action_id == p.id,
            BusinessEvent.event_type == "ledger.reversed",
        )
    )
    event.action_id = None
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, p.id)["verification"]
        == "unresolved"
    )
    event.action_id = p.id
    group = json.loads(p.output)["reversing_posting_group_id"]
    entry = session.scalar(
        select(LedgerEntry).where(LedgerEntry.posting_group_id == group)
    )
    entry.amount = Decimal(1)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, p.id)["verification"]
        == "unresolved"
    )


def test_event_failure_rolls_back_inverse_group(session, business, monkeypatch):
    _, ig, _ = fixture(session, business)
    p = prepare(session, business, ig)
    before = session.scalar(select(func.count()).select_from(LedgerEntry))

    def fail(*args, **kwargs):
        raise core.InvalidOperation("Injected reversal event failure")

    monkeypatch.setattr(core, "emit_business_event", fail)
    with pytest.raises(core.InvalidOperation, match="Injected"):
        confirm(session, business, p)
    assert session.scalar(select(func.count()).select_from(LedgerReversal)) == 0
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before


def test_concurrent_payment_and_reversal_do_not_bypass_review(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.tools.application import approve_and_execute_proposal

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = core.create_tenant(session, "Concurrent finance")
            b = SimpleNamespace(
                tenant=tenant,
                customer=core.create_party(session, tenant.id, "Customer", "customer"),
            )
            invoice, ig, _ = fixture(session, b)
            first = prepare(session, b, ig)
            second = prepare_payment(session, b, invoice)
            claims = [
                (p.id, json.loads(p.input)["_delivery_review"]["token"])
                for p in (first, second)
            ]
            tenant_id = tenant.id
        gate = Barrier(2)

        def execute(claim):
            with factory() as connection:
                gate.wait(timeout=10)
                try:
                    approve_and_execute_proposal(
                        connection,
                        tenant_id,
                        claim[0],
                        confirmed=True,
                        review_token=claim[1],
                    )
                    return True
                except core.InvalidOperation as error:
                    assert any(
                        word in str(error)
                        for word in ("unresolved", "changed", "reversed", "review")
                    )
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, claims)) == [False, True]
        with factory() as session:
            assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 6
    finally:
        engine.dispose()
