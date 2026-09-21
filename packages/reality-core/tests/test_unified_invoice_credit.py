"""Invoice-linked financial credits retain exact evidence and explicit settlement."""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from conftest import record_by_id
from sqlalchemy import func, select
from test_multi_position_invoices import intent, order
from test_unified_invoice_entry import confirm

from reality.db.core import (
    BusinessEvent,
    Document,
    DocumentLine,
    Movement,
    SourceRecord,
)
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)


def fixture(s, b):
    result = core.record_sales_invoice(s, b.tenant.id, **intent(order(s, b)))
    doc = record_by_id(
        s,
        Document,
        next(r["id"] for r in result["records"] if r["family"] == "document"),
    )
    lines = [
        record_by_id(s, DocumentLine, r["id"])
        for r in result["records"]
        if r["family"] == "document_line"
    ]
    return doc, lines


def arguments(doc, lines, **changes):
    return {
        "invoice_id": doc.id,
        "lines": [
            {"invoice_line_id": line.id, "quantity": "1", "gross_amount": "31.1234"}
            for line in lines
        ],
        "gross_amount": "90.1234",
        "number": "CR-" + uuid4().hex,
        "reason": "Agreed invoice correction",
        "allocation_amount": "20",
        **changes,
    }


def prepare(s, b, args):
    return prepare_delivery_action(
        s, b.tenant.id, "sales_credit_record", args, request_id=uuid4().hex
    )


def test_partial_multi_credit_without_return_and_exact_recovery(session, business):
    b = business
    doc, lines = fixture(session, b)
    args = arguments(doc, lines)
    p = prepare(session, b, args)
    assert session.scalar(select(func.count()).select_from(Movement)) == 0
    confirm(session, b, p)
    detail = delivery_proposal_detail(session, b.tenant.id, p.id)
    assert detail["verification"] == "verified"
    records = detail["receipt"]["records"]
    assert len(records) == 7
    note = record_by_id(
        session, Document, next(r["id"] for r in records if r["family"] == "document")
    )
    assert note.gross_amount == Decimal("90.1234")
    credit_lines = [
        record_by_id(session, DocumentLine, r["id"])
        for r in records
        if r["family"] == "document_line"
    ]
    assert [line.billed_document_line_id for line in credit_lines] == [
        line.id for line in lines
    ]
    assert all(line.gross_amount == Decimal("31.1234") for line in credit_lines)
    assert core.open_invoice_amount(session, b.tenant.id, doc.id) == Decimal("189.1234")
    assert core.open_invoice_amount(session, b.tenant.id, note.id) == Decimal("70.1234")
    assert (
        json.loads(record_by_id(session, SourceRecord, note.source_record_id).payload)[
            "reason"
        ]
        == args["reason"]
    )
    p.status = "executing"
    p.output = "{}"
    session.commit()
    assert (
        reconcile_delivery(session, b.tenant.id, p.id)["receipt"] == detail["receipt"]
    )
    group = core._settlement_control_entry(
        session, b.tenant.id, note.id
    ).posting_group_id
    core.reverse_ledger_posting_group(session, b.tenant.id, group, reason="Correction")
    assert (
        delivery_proposal_detail(session, b.tenant.id, p.id)["verification"]
        == "verified"
    )
    fresh = prepare(session, b, arguments(doc, lines, allocation_amount="0"))
    confirm(session, b, fresh)
    assert session.scalar(select(func.count()).select_from(Movement)) == 0


def test_paid_invoice_zero_netting_and_capacity(session, business):
    b = business
    doc, lines = fixture(session, b)
    core.post_customer_payment(session, b.tenant.id, doc.id, doc.gross_amount)
    p = prepare(session, b, arguments(doc, lines, allocation_amount="0"))
    confirm(session, b, p)
    p2 = prepare(session, b, arguments(doc, lines, allocation_amount="0"))
    confirm(session, b, p2)
    with pytest.raises(core.InvalidOperation, match="quantity"):
        prepare(session, b, arguments(doc, lines, allocation_amount="0"))
    assert core.open_invoice_amount(session, b.tenant.id, doc.id) == 0


@pytest.mark.parametrize(
    "bad",
    [
        "foreign",
        "duplicate",
        "mixed",
        "precision",
        "excess_quantity",
        "excess_amount",
        "allocation",
        "reason",
    ],
)
def test_invalid_credit_is_inert(session, business, bad):
    doc, lines = fixture(session, business)
    args = arguments(doc, lines)
    if bad == "foreign":
        args["invoice_id"] = "foreign"
    if bad == "duplicate":
        args["lines"][1]["invoice_line_id"] = lines[0].id
    if bad == "mixed":
        args["lines"][1]["invoice_line_id"] = fixture(session, business)[1][0].id
    if bad == "precision":
        args["lines"][0]["quantity"] = "0.00001"
    if bad == "excess_quantity":
        args["lines"][0]["quantity"] = "3"
    if bad == "excess_amount":
        args["gross_amount"] = "999"
    if bad == "allocation":
        args["allocation_amount"] = "999"
    if bad == "reason":
        args["reason"] = " "
    before = session.scalar(select(func.count()).select_from(SourceRecord))
    with pytest.raises((core.InvalidOperation, core.NotFound)):
        prepare(session, business, args)
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before


@pytest.mark.parametrize("change", ["payment", "credit", "reversal"])
def test_stale_credit_review(session, business, change):
    b = business
    doc, lines = fixture(session, b)
    p = prepare(session, b, arguments(doc, lines, allocation_amount="0"))
    if change == "payment":
        core.post_customer_payment(session, b.tenant.id, doc.id, "1")
    elif change == "credit":
        core.record_sales_credit(
            session, b.tenant.id, **arguments(doc, lines, allocation_amount="0")
        )
    else:
        core.reverse_ledger_posting_group(
            session,
            b.tenant.id,
            core._settlement_control_entry(
                session, b.tenant.id, doc.id
            ).posting_group_id,
            reason="Wrong invoice",
        )
    with pytest.raises(core.InvalidOperation):
        confirm(session, b, p)


def test_posting_failure_rolls_back(session, business, monkeypatch):
    doc, lines = fixture(session, business)
    p = prepare(session, business, arguments(doc, lines))
    before = session.scalar(select(func.count()).select_from(SourceRecord))

    def fail(*a, **kw):
        raise core.InvalidOperation("Injected failure")

    monkeypatch.setattr(core, "post_sales_credit_note", fail)
    with pytest.raises(core.InvalidOperation, match="Injected"):
        confirm(session, business, p)
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before


def test_tampered_credit_proof_is_unresolved(session, business):
    doc, lines = fixture(session, business)
    p = prepare(session, business, arguments(doc, lines))
    confirm(session, business, p)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.action_id == p.id,
            BusinessEvent.event_type == "credit.recorded",
        )
    )
    payload = json.loads(event.payload)
    payload["receipt"]["records"].pop()
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, p.id)["verification"]
        == "unresolved"
    )


def test_unposted_credit_and_legacy_ambiguity(session, business):
    from reality.services.credit_actions import _credit_context

    b = business
    doc, lines = fixture(session, b)
    core.create_manual_document_with_lines(
        session,
        b.tenant.id,
        "credit_note",
        "UNPOSTED",
        b.customer.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "1",
                "gross_amount": "1",
                "billed_document_line_id": lines[0].id,
            }
        ],
        "1",
    )
    context = _credit_context(session, b.tenant.id, doc.id)
    assert (
        next(r for r in context["positions"] if r["id"] == lines[0].id)["remaining"]
        == 1
    )
    core.create_manual_document_with_lines(
        session,
        b.tenant.id,
        "credit_note",
        "LEGACY",
        b.customer.id,
        [
            {
                "item_id": b.item.id,
                "quantity": "1",
                "gross_amount": "1",
                "billed_document_line_id": lines[1].billed_document_line_id,
            }
        ],
        "1",
    )
    with pytest.raises(core.InvalidOperation, match="attribution"):
        prepare(session, b, arguments(doc, lines))
    with pytest.raises(core.InvalidOperation, match="attribution"):
        prepare(session, b, arguments(doc, lines[:1]))


def test_two_invoices_same_order_have_independent_capacity(session, business):
    from reality.services.credit_actions import _credit_context

    b = business
    line = order(session, b)[0]
    docs = []
    for i in range(2):
        result = core.record_sales_invoice(
            session, b.tenant.id, line.id, "1", "100", f"INV-{i}"
        )
        docs.append(
            record_by_id(
                session,
                Document,
                next(r["id"] for r in result["records"] if r["family"] == "document"),
            )
        )
    first_lines = list(
        session.scalars(
            select(DocumentLine).where(DocumentLine.document_id == docs[0].id)
        )
    )
    p = prepare(session, b, arguments(docs[0], first_lines, allocation_amount="0"))
    confirm(session, b, p)
    assert (
        _credit_context(session, b.tenant.id, docs[0].id)["positions"][0]["remaining"]
        == 0
    )
    assert (
        _credit_context(session, b.tenant.id, docs[1].id)["positions"][0]["remaining"]
        == 1
    )
    assert core.uncredited_return_quantity(session, b.tenant.id, line.id) == -1


def test_credit_http_context_and_tenant(session, business):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    doc, lines = fixture(session, business)
    foreign = core.create_tenant(session, "Foreign")
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as s:
            yield s

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            response = client.get(f"{base}/finance/invoice-credit/{doc.id}")
            assert response.status_code == 200, response.text
            assert response.json()["positions"][0]["remaining"] == "2"
            assert (
                client.get(
                    f"/api/tenants/{foreign.id}/finance/invoice-credit/{doc.id}"
                ).status_code
                == 404
            )
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "sales_credit_record",
                    "arguments": arguments(doc, lines),
                    "request_id": "http-credit",
                },
            )
            assert response.status_code == 200, response.text
    finally:
        app.dependency_overrides.clear()


def test_financial_credit_does_not_require_return_exception(session, business):
    from reality.services.exceptions import operational_exceptions

    doc, lines = fixture(session, business)
    p = prepare(session, business, arguments(doc, lines))
    confirm(session, business, p)
    assert not any(
        row.class_id == "credited_not_returned"
        for row in operational_exceptions(session, business.tenant.id)
    )


def test_concurrent_direct_and_reviewed_credit(postgres_database):
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
        with factory() as s:
            tenant = core.create_tenant(s, "Concurrent credits")
            b = SimpleNamespace(
                tenant=tenant,
                company=core.create_party(s, tenant.id, "Company", "company"),
                customer=core.create_party(s, tenant.id, "Customer", "customer"),
                item=core.create_item(s, tenant.id, "SKU", "Item"),
                location=core.create_location(s, tenant.id, "Warehouse"),
            )
            doc, lines = fixture(s, b)
            args = arguments(doc, lines, gross_amount="150", allocation_amount="0")
            p = prepare(s, b, args)
            claim = p.id, json.loads(p.input)["_delivery_review"]["token"]
            tenant_id = tenant.id
        gate = Barrier(2)

        def execute(reviewed):
            with factory() as s:
                gate.wait(timeout=10)
                try:
                    if reviewed:
                        approve_and_execute_proposal(
                            s,
                            tenant_id,
                            claim[0],
                            review_token=claim[1],
                            confirmed=True,
                        )
                    else:
                        core.record_sales_credit(s, tenant_id, **args)
                    return True
                except core.InvalidOperation as error:
                    assert any(
                        word in str(error)
                        for word in ["remaining", "changed", "review", "unresolved"]
                    )
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, [True, False])) == [False, True]
        with factory() as s:
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(Document)
                    .where(Document.type == "credit_note")
                )
                == 1
            )
    finally:
        engine.dispose()


def test_credit_inspector_follows_invoice_then_order(session, business):
    from reality.services.delivery_reads import delivery_evidence
    from reality.web.api import document_inspector

    doc, lines = fixture(session, business)
    p = prepare(session, business, arguments(doc, lines))
    confirm(session, business, p)
    records = delivery_proposal_detail(session, business.tenant.id, p.id)["receipt"][
        "records"
    ]
    credit_id = next(r["id"] for r in records if r["family"] == "document")
    credit_line = next(r["id"] for r in records if r["family"] == "document_line")
    detail = document_inspector(session, business.tenant.id, credit_id)
    links = [
        row.get("link") for section in detail["sections"] for row in section["rows"]
    ]
    assert {"kind": "document_line", "id": lines[0].id} in links
    detail = delivery_evidence(
        session, business.tenant.id, "document_line", credit_line
    )
    links = [
        row.get("link") for section in detail["sections"] for row in section["rows"]
    ]
    assert {"kind": "document_line", "id": lines[0].id} in links
    detail = delivery_evidence(
        session, business.tenant.id, "document_line", lines[0].id
    )
    links = [
        row.get("link") for section in detail["sections"] for row in section["rows"]
    ]
    assert {"kind": "document_line", "id": lines[0].billed_document_line_id} in links
