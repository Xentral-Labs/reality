"""Reviewed invoice entry preserves stated evidence and avoids duplicate effects."""

import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Document, DocumentLine, LedgerEntry, Movement
from reality.services.core import InvalidOperation, NotFound, create_manual_order
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.services.finance import components
from reality.tools.application import (
    TOOLS,
    Tool,
    approve_and_execute_proposal,
    run_read_tool,
)


def prepare(
    session, business, direction="sales", line=None, request="invoice-120", **changes
):
    if not line:
        result = create_manual_order(
            session,
            business.tenant.id,
            direction,
            "ORDER-120",
            business.company.id,
            business.customer.id if direction == "sales" else business.supplier.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "3",
                    "unit_price": "100",
                    "gross_amount": "300",
                }
            ],
            gross_amount="300",
        )
        line = result[2][0].id
    values = {
        "order_line_id": line,
        "quantity": "2",
        "gross_amount": "301",
        "number": "INV-120",
        "effective_at": "2026-09-08T12:00:00Z",
    }
    values.update(changes)
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record" if direction == "sales" else "supplier_invoice_record",
        values,
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_invoice_review_atomic_effects_and_unknown_recovery(
    session, business, direction
):
    proposal = prepare(session, business, direction)
    for model in (LedgerEntry, Movement):
        assert (
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.tenant_id == business.tenant.id)
            )
            == 0
        )
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    records = detail["receipt"]["records"]
    assert len(records) == 5
    invoice = record_by_id(
        session, Document, next(r["id"] for r in records if r["family"] == "document")
    )
    assert invoice.gross_amount == Decimal(301)
    entries = list(
        session.scalars(
            select(LedgerEntry).where(LedgerEntry.tenant_id == business.tenant.id)
        )
    )
    assert {(e.account, e.debit_credit, e.amount) for e in entries} == {
        (
            "accounts_receivable" if direction == "sales" else "inventory",
            "debit",
            Decimal(301),
        ),
        (
            "sales_revenue" if direction == "sales" else "accounts_payable",
            "credit",
            Decimal(301),
        ),
    }
    confirm(session, business, proposal)
    receipt = detail["receipt"]
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["receipt"]
        == receipt
    )
    with pytest.raises(InvalidOperation, match="remaining"):
        prepare(
            session,
            business,
            direction,
            line=json.loads(proposal.input)["order_line_id"],
            request="again",
        )
    for model in (Movement,):
        assert (
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.tenant_id == business.tenant.id)
            )
            == 0
        )


def test_invoice_line_retains_source_stated_finance_detail(session, business):
    order = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "ORDER-FINANCE-DETAIL",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "59.50",
                "gross_amount": "119.00",
            }
        ],
        gross_amount="119.00",
    )
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record",
        {
            "lines": [
                {
                    "order_line_id": order[2][0].id,
                    "quantity": "2",
                    "gross_amount": "119.00",
                    "reality_finance_v1": {
                        "net": "100.00",
                        "tax": "19.00",
                        "gross": "119.00",
                        "currency": "EUR",
                    },
                }
            ],
            "gross_amount": "119.00",
            "number": "INV-FINANCE-DETAIL",
            "effective_at": "2026-09-24T08:00:00Z",
        },
        request_id="invoice-finance-detail",
    )

    confirm(session, business, proposal)

    invoice_line_id = next(
        row["id"]
        for row in json.loads(proposal.output)["records"]
        if row["family"] == "document_line"
    )
    invoice_line = record_by_id(session, DocumentLine, invoice_line_id)
    assert json.loads(invoice_line.payload)["reality_finance_v1"] == {
        "net": "100.00",
        "tax": "19.00",
        "gross": "119.00",
        "currency": "EUR",
    }
    finance = components.component_context(
        session, business.tenant.id, invoice_line.document_id
    )["items"][0]
    assert finance["amounts"] == {
        "net": "100",
        "tax": "19",
        "base": None,
        "gross": "119",
    }


@pytest.mark.parametrize(
    "change", ["quantity", "gross_amount", "number", "order_line_id"]
)
def test_invalid_invoice_is_inert(session, business, change):
    with pytest.raises((InvalidOperation, NotFound)):
        prepare(
            session,
            business,
            **{
                change: {
                    "quantity": "4",
                    "gross_amount": "NaN",
                    "number": " ",
                    "order_line_id": "foreign",
                }[change]
            },
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_stale_line_and_unresolved_guard(session, business):
    proposal = prepare(session, business)
    line_id = json.loads(proposal.input)["order_line_id"]
    line = record_by_id(session, DocumentLine, line_id)
    line.gross_amount = Decimal(299)
    session.commit()
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, business, proposal)
    next_proposal = prepare(session, business, line=line_id, request="fresh")
    next_proposal.status = "executing"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare(session, business, line=line_id, request="blocked")
    assert (
        reconcile_delivery(session, business.tenant.id, next_proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_receipt_requires_exact_attributed_proof(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "invoice.recorded",
        )
    )
    assert event is not None
    payload = json.loads(event.payload)
    payload["creation"]["gross_amount"] = "999"
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_historical_invoice_proof_survives_reversal_and_unverified_output(
    session, business
):
    from reality.services.core import reverse_ledger_posting_group

    proposal = prepare(session, business)
    confirm(session, business, proposal)
    receipt = json.loads(proposal.output)
    entry_id = next(
        r["id"] for r in receipt["records"] if r["family"] == "ledger_entry"
    )
    group = record_by_id(session, LedgerEntry, entry_id).posting_group_id
    reverse_ledger_posting_group(
        session, business.tenant.id, group, reason="Invoice entered in error"
    )
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )
    proposal.output = "{}"
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_invoice_foreign_direction_and_current_actor(session, business):
    from types import SimpleNamespace

    from reality.services.core import create_tenant

    proposal = prepare(session, business)
    line_id = json.loads(proposal.input)["order_line_id"]
    with pytest.raises(InvalidOperation, match="purchase order"):
        prepare(
            session,
            business,
            direction="purchase",
            line=line_id,
            request="wrong-direction",
        )
    foreign = create_tenant(session, "Foreign invoice tenant")
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session,
            foreign.id,
            "sales_invoice_record",
            json.loads(proposal.input)["_delivery_review"]["intent"],
            request_id="foreign",
        )
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="missing", is_platform_admin=False
            ),
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_default_effective_time_and_two_proposals_for_same_line(session, business):
    first = prepare(session, business, effective_at=None)
    second = prepare(
        session,
        business,
        line=json.loads(first.input)["order_line_id"],
        request="second",
        effective_at=None,
    )
    confirm(session, business, first)
    assert (
        delivery_proposal_detail(session, business.tenant.id, first.id)["verification"]
        == "verified"
    )
    with pytest.raises(InvalidOperation, match="remaining"):
        confirm(session, business, second)
    assert second.status == "proposed"
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


def test_reviewed_deterministic_handler_refusal_is_terminal_and_effect_free(
    session, business, monkeypatch
):
    proposal = prepare(session, business)
    original = TOOLS["sales_invoice_record"]

    def refuse(_session, _tenant_id, _arguments):
        raise InvalidOperation("Deterministic relationship refusal.")

    monkeypatch.setitem(
        TOOLS,
        "sales_invoice_record",
        Tool(original.name, original.description, original.mutating, refuse),
    )
    with pytest.raises(InvalidOperation, match="relationship refusal"):
        confirm(session, business, proposal)

    session.refresh(proposal)
    assert proposal.status == "failed"
    assert json.loads(proposal.output) == {
        "business_effect": "none",
        "error_type": "InvalidOperation",
        "message": "Deterministic relationship refusal.",
    }
    status = run_read_tool(
        session,
        business.tenant.id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )
    assert status["verification"]["execution"] == "failed"
    assert status["verification"]["operational_state"] == "no_effect"
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


@pytest.mark.parametrize("tool", ["sales_invoice_record", "supplier_invoice_record"])
def test_invoice_prepare_http_uses_shared_review(session, business, tool):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    first = prepare(
        session, business, "sales" if tool == "sales_invoice_record" else "purchase"
    )
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
                    "tool": tool,
                    "request_id": "http",
                    "arguments": json.loads(first.input)["_delivery_review"]["intent"],
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


def delivered_invoice(session, business):
    from reality.db.core import Commitment
    from reality.services.core import record_movement

    seed = prepare(session, business, request="delivery-seed")
    line_id = json.loads(seed.input)["order_line_id"]
    line = record_by_id(session, DocumentLine, line_id)
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == business.tenant.id,
            Commitment.document_line_id == line_id,
            Commitment.type == "customer_delivery",
        )
    )
    assert commitment is not None
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "3",
        to_location_id=business.location.id,
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "3",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    guard = {
        "condition_id": f"exc__shipped_not_billed__{line_id}",
        "unbilled_quantity": "3",
        "unit": line.unit,
    }
    return line_id, commitment.id, guard


@pytest.mark.parametrize("returned", ["1", "2", "3"])
def test_return_after_delivery_read_refuses_guarded_invoice_atomically(
    session, business, returned
):
    from reality.services.core import record_movement
    from reality.services.exceptions import explain_operational_exception

    line_id, commitment_id, guard = delivered_invoice(session, business)
    proposal = prepare(
        session, business, line=line_id, request="guarded", delivery_guard=guard
    )
    assert explain_operational_exception(
        session, business.tenant.id, guard["condition_id"]
    )["causal_values"]["unbilled_quantity"] == Decimal(3)
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        returned,
        to_location_id=business.location.id,
        commitment_id=commitment_id,
    )
    with pytest.raises(InvalidOperation, match="delivery"):
        confirm(session, business, proposal)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.type == "sales_invoice")
        )
        == 0
    )
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)["status"]
        == "proposed"
    )


def test_guarded_invoice_retains_exact_guard_and_replays_one_receipt(session, business):
    line_id, _, guard = delivered_invoice(session, business)
    proposal = prepare(
        session, business, line=line_id, request="guarded", delivery_guard=guard
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["intent"]["delivery_guard"] == guard
    assert review["state"]["creation"]["delivery_guard"] == guard
    confirm(session, business, proposal)
    receipt = delivery_proposal_detail(session, business.tenant.id, proposal.id)[
        "receipt"
    ]
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert detail["receipt"] == receipt
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.type == "sales_invoice")
        )
        == 1
    )


@pytest.mark.parametrize(
    "change",
    [
        {"condition_id": "exc__shipped_not_billed__foreign"},
        {"unbilled_quantity": "4"},
        {"unit": "foreign"},
    ],
)
def test_delivery_guard_refuses_wrong_or_changed_evidence(session, business, change):
    line_id, _, guard = delivered_invoice(session, business)
    with pytest.raises(InvalidOperation, match="delivery"):
        prepare(
            session,
            business,
            line=line_id,
            request="guarded",
            delivery_guard={**guard, **change},
        )


def test_guard_validation_and_invoice_commit_serialize_a_concurrent_return(
    postgres_database, monkeypatch
):
    import time
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue
    from threading import Event

    from conftest import Business
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, build_engine
    from reality.services import core

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    checked, release = Event(), Event()
    returning = Queue()
    try:
        with factory() as session:
            tenant = core.create_tenant(session, "Invoice guard concurrency")
            b = Business(
                tenant=tenant,
                company=core.create_party(session, tenant.id, "Company", "company"),
                customer=core.create_party(session, tenant.id, "Customer", "customer"),
                supplier=core.create_party(session, tenant.id, "Supplier", "supplier"),
                item=core.create_item(session, tenant.id, "GUARD", "Guard item"),
                location=core.create_location(session, tenant.id, "Warehouse"),
            )
            line_id, commitment_id, guard = delivered_invoice(session, b)
            proposal = prepare(
                session, b, line=line_id, request="guarded", delivery_guard=guard
            )
            proposal_id = proposal.id
            token = json.loads(proposal.input)["_delivery_review"]["token"]
            tenant_id, item_id, location_id = tenant.id, b.item.id, b.location.id

        original = core._validate_invoice_delivery_guard

        def hold_after_validation(*args, **kwargs):
            original(*args, **kwargs)
            if not checked.is_set():
                checked.set()
                assert release.wait(10)

        monkeypatch.setattr(
            core, "_validate_invoice_delivery_guard", hold_after_validation
        )

        def invoice():
            with factory() as session:
                return approve_and_execute_proposal(
                    session, tenant_id, proposal_id, review_token=token, confirmed=True
                )

        def send_return():
            with factory() as session:
                returning.put(session.scalar(text("select pg_backend_pid()")))
                return core.record_movement(
                    session,
                    tenant_id,
                    "return",
                    item_id,
                    "2",
                    to_location_id=location_id,
                    commitment_id=commitment_id,
                )

        with ThreadPoolExecutor(max_workers=2) as workers:
            writing = workers.submit(invoice)
            assert checked.wait(10)
            movement = workers.submit(send_return)
            pid = returning.get(timeout=10)
            try:
                deadline = time.monotonic() + 5
                with engine.connect() as observer:
                    while time.monotonic() < deadline:
                        blocked = observer.scalar(
                            text(
                                "select count(*) from pg_locks where pid=:pid and not granted"
                            ),
                            {"pid": pid},
                        )
                        if blocked:
                            break
                        time.sleep(0.01)
                    assert blocked == 1
                assert not movement.done()
            finally:
                release.set()
            writing.result(timeout=10)
            movement.result(timeout=10)
        with factory() as session:
            assert (
                delivery_proposal_detail(session, tenant_id, proposal_id)[
                    "verification"
                ]
                == "verified"
            )
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(Document)
                    .where(Document.type == "sales_invoice")
                )
                == 1
            )
    finally:
        release.set()
        engine.dispose()
