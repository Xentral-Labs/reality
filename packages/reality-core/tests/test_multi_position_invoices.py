"""Multi-position invoices preserve stated values and exact receipts."""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from test_unified_invoice_entry import confirm

from reality.db.core import (
    BusinessEvent,
    Document,
    DocumentLine,
    LedgerEntry,
    SourceRecord,
)
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)


def order(session, b, direction="sales"):
    return core.create_manual_order(
        session,
        b.tenant.id,
        direction,
        "ORDER-122-" + uuid4().hex,
        b.company.id,
        b.customer.id if direction == "sales" else b.supplier.id,
        b.location.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "3",
                "unit_price": "100",
                "gross_amount": "300",
            },
            {
                "item_id": b.item.id,
                "quantity": "4",
                "unit_price": "100",
                "gross_amount": "400",
            },
        ],
        gross_amount="700",
    )[2]


def intent(lines):
    return {
        "lines": [
            {"order_line_id": r.id, "quantity": "2", "gross_amount": str(101 + i)}
            for i, r in enumerate(lines)
        ],
        "gross_amount": "209.1234",
        "number": "INV-122",
    }


def prepare(s, b, args, direction="sales", request="multi-122"):
    return prepare_delivery_action(
        s,
        b.tenant.id,
        "sales_invoice_record" if direction == "sales" else "supplier_invoice_record",
        args,
        request_id=request,
    )


@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_stated_values_and_recovery(session, business, direction):
    lines = order(session, business, direction)
    args = intent(lines)
    proposal = prepare(session, business, args, direction)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    confirm(session, business, proposal)
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    records = detail["receipt"]["records"]
    assert len(records) == 6
    doc = session.get(
        Document, next(r["id"] for r in records if r["family"] == "document")
    )
    assert doc.gross_amount == Decimal("209.1234")
    rows = [
        session.get(DocumentLine, r["id"])
        for r in records
        if r["family"] == "document_line"
    ]
    assert [(r.billed_document_line_id, r.quantity, r.gross_amount) for r in rows] == [
        (lines[0].id, Decimal(2), Decimal(101)),
        (lines[1].id, Decimal(2), Decimal(102)),
    ]
    assert (
        json.loads(session.get(SourceRecord, doc.source_record_id).payload)["lines"]
        == args["lines"]
    )
    assert all(
        session.get(LedgerEntry, r["id"]).amount == Decimal("209.1234")
        for r in records
        if r["family"] == "ledger_entry"
    )
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["receipt"]
        == detail["receipt"]
    )
    with pytest.raises(core.InvalidOperation, match="remaining"):
        prepare(session, business, args, direction, request="again")


@pytest.mark.parametrize(
    "bad", ["empty", "duplicate", "mixed", "quantity", "precision", "mixed_shape"]
)
def test_invalid_is_inert(session, business, bad):
    lines = order(session, business)
    args = intent(lines)
    if bad == "empty":
        args["lines"] = []
    if bad == "duplicate":
        args["lines"][1]["order_line_id"] = lines[0].id
    if bad == "mixed":
        args["lines"][1]["order_line_id"] = order(session, business)[0].id
    if bad == "quantity":
        args["lines"][1]["quantity"] = "99"
    if bad == "precision":
        args["lines"][1]["gross_amount"] = "0.00001"
    if bad == "mixed_shape":
        args.update(order_line_id=lines[0].id, quantity="1")
    with pytest.raises(core.InvalidOperation):
        prepare(session, business, args)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_second_line_stale_and_legacy_overlap(session, business):
    lines = order(session, business)
    proposal = prepare(session, business, intent(lines))
    lines[1].quantity = Decimal(5)
    session.commit()
    with pytest.raises(core.InvalidOperation, match="changed"):
        confirm(session, business, proposal)
    proposal.status = "executing"
    session.commit()
    with pytest.raises(core.InvalidOperation, match="unresolved"):
        prepare(
            session,
            business,
            {
                "order_line_id": lines[1].id,
                "quantity": "1",
                "gross_amount": "99",
                "number": "OTHER",
            },
            request="overlap",
        )


def test_omitted_second_line_proof(session, business):
    proposal = prepare(session, business, intent(order(session, business)))
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "invoice.recorded",
        )
    )
    payload = json.loads(event.payload)
    payload["receipt"]["records"].pop(3)
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_posting_failure_atomicity(session, business, monkeypatch):
    proposal = prepare(session, business, intent(order(session, business)))
    before = session.scalar(select(func.count()).select_from(SourceRecord))

    def fail(*a, **kw):
        raise core.InvalidOperation("Injected posting failure")

    monkeypatch.setattr(core, "post_sales_invoice", fail)
    with pytest.raises(core.InvalidOperation, match="Injected"):
        confirm(session, business, proposal)
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.type == "sales_invoice")
        )
        == 0
    )


def test_foreign_second_position_and_already_billed_are_inert(session, business):
    lines = order(session, business)
    args = intent(lines)
    args["lines"][1]["order_line_id"] = "foreign-or-missing-line"
    with pytest.raises(core.NotFound):
        prepare(session, business, args)
    core.record_sales_invoice(
        session, business.tenant.id, lines[1].id, "4", "100", "PRIOR"
    )
    before = session.scalar(select(func.count()).select_from(SourceRecord))
    with pytest.raises(core.InvalidOperation, match="remaining"):
        prepare(session, business, intent(lines), request="billed")
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before


def test_direct_multi_service_and_legacy_shape(session, business):
    args = intent(order(session, business))
    result = core.record_sales_invoice(session, business.tenant.id, **args)
    assert len(result["records"]) == 6
    with pytest.raises(core.InvalidOperation, match="either"):
        core.record_sales_invoice(
            session, business.tenant.id, order_line_id="unexpected", **args
        )


def test_receipt_line_order_must_match_document_event(session, business):
    proposal = prepare(session, business, intent(order(session, business)))
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "invoice.recorded",
        )
    )
    payload = json.loads(event.payload)
    records = payload["receipt"]["records"]
    records[2], records[3] = records[3], records[2]
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_overlapping_concurrent_multi_and_single_review(postgres_database):
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
            tenant = core.create_tenant(session, "Concurrent invoices")
            b = SimpleNamespace(
                tenant=tenant,
                company=core.create_party(session, tenant.id, "Company", "company"),
                customer=core.create_party(session, tenant.id, "Customer", "customer"),
                item=core.create_item(session, tenant.id, "SKU", "Item"),
                location=core.create_location(session, tenant.id, "Warehouse"),
            )
            lines = order(session, b)
            first = prepare(session, b, intent(lines))
            second = prepare(
                session,
                b,
                {
                    "order_line_id": lines[1].id,
                    "quantity": "1",
                    "gross_amount": "99",
                    "number": "SINGLE",
                },
                request="single",
            )
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
                        for word in (
                            "review",
                            "unresolved",
                            "remaining",
                            "changed",
                        )
                    )
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, claims)) == [False, True]
        with factory() as session:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(Document)
                    .where(Document.type == "sales_invoice")
                )
                == 1
            )
            assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    finally:
        engine.dispose()
