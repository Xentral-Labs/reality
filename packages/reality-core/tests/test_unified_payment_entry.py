"""Reviewed payment recording and allocation share exact financial authority."""

import json
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Document,
    LedgerEntry,
    Movement,
    SettlementAllocation,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_document,
    create_tenant,
    open_invoice_amount,
    post_sales_invoice,
    post_supplier_invoice,
    reverse_ledger_posting_group,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.tools.application import approve_and_execute_proposal


def obligation(session, business, direction="customer"):
    supplier = direction == "supplier"
    doc = create_document(
        session,
        business.tenant.id,
        "supplier_invoice" if supplier else "sales_invoice",
        "INV-121",
        business.supplier.id if supplier else business.customer.id,
        "300",
        currency="USD",
    )
    (post_supplier_invoice if supplier else post_sales_invoice)(
        session, business.tenant.id, doc.id
    )
    return doc


def prepare(
    session, business, invoice, direction="customer", request="payment-121", **changes
):
    args = {
        "invoice_id": invoice.id,
        "amount": "125",
        "payment_number": "PAY-121",
        "effective_at": "2026-09-08T12:00:00Z",
    }
    args.update(changes)
    return prepare_delivery_action(
        session,
        business.tenant.id,
        f"{direction}_payment_post",
        args,
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirmed=True,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
    )


@pytest.mark.parametrize("direction", ["customer", "supplier"])
def test_partial_payment_preview_exact_receipt_recovery_and_remainder(
    session, business, direction
):
    invoice = obligation(session, business, direction)
    proposal = prepare(session, business, invoice, direction)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 0
    review = json.loads(proposal.input)["_delivery_review"]
    assert Decimal(review["state"]["open_before"]) == 300
    assert Decimal(review["state"]["open_after"]) == 175
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert len(detail["receipt"]["records"]) == 2
    assert Decimal(detail["observation"]["open"]) == 175
    entries = [session.get(LedgerEntry, r["id"]) for r in detail["receipt"]["records"]]
    assert {(e.account, e.debit_credit, e.amount, e.currency) for e in entries} == {
        (
            "cash" if direction == "customer" else "accounts_payable",
            "debit",
            Decimal(125),
            "USD",
        ),
        (
            "accounts_receivable" if direction == "customer" else "cash",
            "credit",
            Decimal(125),
            "USD",
        ),
    }
    confirm(session, business, proposal)
    receipt = detail["receipt"]
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare(
            session,
            business,
            invoice,
            direction,
            request="unknown-overlap",
            amount="10",
        )
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["receipt"]
        == receipt
    )
    remainder = prepare(
        session, business, invoice, direction, request="remainder", amount="175"
    )
    confirm(session, business, remainder)
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == 0
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 2
    assert session.scalar(select(func.count()).select_from(Movement)) == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "301"},
        {"amount": "0"},
        {"amount": "NaN"},
        {"amount": "0.00001"},
        {"source_record_id": "foreign"},
        {"effective_at": "invalid"},
        {"unexpected": True},
    ],
)
def test_invalid_payment_is_inert(session, business, changes):
    invoice = obligation(session, business)
    with pytest.raises((InvalidOperation, NotFound)):
        prepare(session, business, invoice, **changes)
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


def test_foreign_wrong_type_and_current_actor(session, business):
    invoice = obligation(session, business)
    with pytest.raises(InvalidOperation):
        prepare(session, business, invoice, "supplier")
    supplier = obligation(session, business, "supplier")
    with pytest.raises(InvalidOperation):
        prepare(session, business, supplier, "customer", request="wrong")
    foreign = create_tenant(session, "Foreign payment tenant")
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session,
            foreign.id,
            "customer_payment_post",
            {"invoice_id": invoice.id, "amount": "1"},
            request_id="foreign",
        )
    proposal = prepare(session, business, invoice)
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="absent", is_platform_admin=False
            ),
        )


def test_stale_allocation_and_historical_reversal(session, business):
    invoice = obligation(session, business)
    first = prepare(session, business, invoice)
    stale = prepare(session, business, invoice, request="stale", amount="50")
    confirm(session, business, first)
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, business, stale)
    assert stale.status == "proposed"
    receipt = json.loads(first.output)
    entry = session.get(LedgerEntry, receipt["records"][0]["id"])
    reverse_ledger_posting_group(
        session, business.tenant.id, entry.posting_group_id, reason="Incorrect payment"
    )
    detail = delivery_proposal_detail(session, business.tenant.id, first.id)
    assert detail["verification"] == "verified"
    assert Decimal(detail["observation"]["open"]) == 300
    assert detail["observation"]["allocation_active"] is False


def test_incomplete_proof_stays_unresolved_and_default_reference_is_supported(
    session, business
):
    invoice = obligation(session, business)
    proposal = prepare(
        session, business, invoice, payment_number=None, effective_at=None
    )
    confirm(session, business, proposal)
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "settlement.allocated",
        )
    )
    event.action_id = None
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


@pytest.mark.parametrize("direction", ["customer", "supplier"])
def test_payment_http_review_and_confirmation(session, business, direction):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    invoice = obligation(session, business, direction)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": f"{direction}_payment_post",
                    "request_id": "http",
                    "arguments": {"invoice_id": invoice.id, "amount": "100"},
                },
            )
            assert response.status_code == 200, response.text
            proposal = response.json()
            response = client.post(
                f"{base}/change-proposals/{proposal['id']}/approve",
                json={"confirmed": True, "review_token": proposal["review"]["token"]},
            )
            assert response.status_code == 200, response.text
            assert (
                client.get(f"{base}/delivery-actions/{proposal['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()


def test_original_payment_source_is_preserved(session, business):
    from reality.db.core import SourceRecord
    from reality.services.core import create_master_source_record

    invoice = obligation(session, business)
    payload = {"amount": "125", "bank_reference": "Original <bank> note"}
    source = create_master_source_record(
        session, business.tenant.id, "payment", "bank", "bank-121", payload
    )
    proposal = prepare(session, business, invoice, source_record_id=source.id)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert {"kind": "source_record", "id": source.id} in detail["links"]
    assert json.loads(session.get(SourceRecord, source.id).payload) == payload
    for record in detail["receipt"]["records"]:
        assert session.get(LedgerEntry, record["id"]).source_record_id == source.id


def test_reversed_invoice_rejects_stale_and_new_payment(session, business):
    invoice = obligation(session, business)
    proposal = prepare(session, business, invoice)
    control = json.loads(proposal.input)["_delivery_review"]["state"]["control"]
    reverse_ledger_posting_group(
        session, business.tenant.id, control["posting_group_id"], reason="Wrong invoice"
    )
    with pytest.raises(InvalidOperation, match="reversed"):
        confirm(session, business, proposal)
    with pytest.raises(InvalidOperation, match="reversed"):
        prepare(session, business, invoice, request="new")
    assert session.scalar(select(func.count()).select_from(SettlementAllocation)) == 0


def test_malformed_attributed_amount_is_not_verified(session, business):
    invoice = obligation(session, business)
    proposal = prepare(session, business, invoice)
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "document.recorded",
        )
    )
    payload = json.loads(event.payload)
    payload["amount"] = "not a number"
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_concurrent_reviews_cannot_silently_spend_changed_capacity(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.services.core import create_party

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = create_tenant(session, "Concurrent payment test")
            party = create_party(session, tenant.id, "Customer", "customer")
            business = SimpleNamespace(tenant=tenant, customer=party)
            invoice = obligation(session, business)
            first = prepare(session, business, invoice, request="first", amount="100")
            second = prepare(session, business, invoice, request="second", amount="100")
            claims = [
                (p.id, json.loads(p.input)["_delivery_review"]["token"])
                for p in (first, second)
            ]
            tenant_id, invoice_id = tenant.id, invoice.id
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
                except InvalidOperation as error:
                    assert "review" in str(error) or "unresolved" in str(error)
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, claims)) == [False, True]
        with factory() as session:
            assert open_invoice_amount(session, tenant_id, invoice_id) == Decimal(200)
            assert (
                session.scalar(select(func.count()).select_from(SettlementAllocation))
                == 1
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize("amount", ["0.0001", "125.1234", "125.00000"])
def test_supported_payment_precision_is_preserved(session, business, amount):
    invoice = obligation(session, business)
    proposal = prepare(session, business, invoice, amount=amount)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    for record in detail["receipt"]["records"]:
        assert session.get(LedgerEntry, record["id"]).amount == Decimal(amount)
    assert Decimal(detail["observation"]["open"]) == Decimal(300) - Decimal(amount)
