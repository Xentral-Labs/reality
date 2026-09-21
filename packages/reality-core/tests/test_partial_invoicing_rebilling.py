"""Quantity availability follows invoice evidence and complete reversals."""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from conftest import record_by_id
from sqlalchemy import func, select
from test_multi_position_invoices import order, prepare
from test_unified_financial_reversal import prepare as prepare_reversal
from test_unified_invoice_entry import confirm

from reality.db.core import Document, SourceRecord
from reality.services import core
from reality.services.delivery_actions import delivery_proposal_detail


def args(line, quantity="1"):
    return {
        "order_line_id": line.id,
        "quantity": quantity,
        "gross_amount": "101.1234",
        "number": "PART-" + uuid4().hex,
    }


def invoice(session, b, line, quantity="1", direction="sales"):
    result = (
        core.record_sales_invoice
        if direction == "sales"
        else core.record_supplier_invoice
    )(session, b.tenant.id, **args(line, quantity))
    doc = record_by_id(
        session,
        Document,
        next(r["id"] for r in result["records"] if r["family"] == "document"),
    )
    return doc, core._settlement_control_entry(
        session, b.tenant.id, doc.id
    ).posting_group_id


@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_partial_reversal_rebilling_and_historical_proof(session, business, direction):
    b = business
    line = order(session, b, direction)[0]
    first = prepare(session, b, args(line), direction)
    confirm(session, b, first)
    billing = core._order_line_billing(session, b.tenant.id, line.id)
    assert (billing["ordered"], billing["invoiced"], billing["remaining"]) == (3, 1, 2)
    records = delivery_proposal_detail(session, b.tenant.id, first.id)["receipt"][
        "records"
    ]
    doc_id = next(r["id"] for r in records if r["family"] == "document")
    group = core._settlement_control_entry(
        session, b.tenant.id, doc_id
    ).posting_group_id
    second = prepare(
        session,
        b,
        {
            "lines": [{k: v for k, v in args(line, "2").items() if k != "number"}],
            "number": "REST",
            "gross_amount": "999.0001",
        },
        direction,
        request="rest",
    )
    confirm(session, b, second)
    before = session.scalar(select(func.count()).select_from(SourceRecord))
    with pytest.raises(core.InvalidOperation, match="remaining"):
        invoice(session, b, line, direction=direction)
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before
    reversal = prepare_reversal(session, b, group)
    effects = json.loads(reversal.input)["_delivery_review"]["state"]["effects"][
        "billing"
    ]
    assert Decimal(effects[0]["remaining_before"]) == 0
    assert Decimal(effects[0]["remaining_after"]) == 1
    confirm(session, b, reversal)
    assert core._order_line_billing(session, b.tenant.id, line.id)["remaining"] == 1
    invoice(session, b, line, direction=direction)
    assert core._order_line_billing(session, b.tenant.id, line.id)["remaining"] == 0
    for proposal in [first, second, reversal]:
        assert (
            delivery_proposal_detail(session, b.tenant.id, proposal.id)["verification"]
            == "verified"
        )


def evidence(s, b, line, quantity, kind="sales_invoice"):
    return core.create_manual_document_with_lines(
        s,
        b.tenant.id,
        kind,
        "RECEIVED-" + uuid4().hex,
        b.customer.id,
        [
            {
                "item_id": b.item.id,
                "quantity": quantity,
                "unit_price": "1",
                "gross_amount": "2",
                "billed_document_line_id": line.id,
            }
        ],
        "2",
    )[0]


def test_unposted_and_multiple_groups_are_conservative(session, business):
    b = business
    line = order(session, b)[0]
    doc = evidence(session, b, line, "2")
    assert core._order_line_billing(session, b.tenant.id, line.id)["remaining"] == 1
    g1 = core.post_sales_invoice(session, b.tenant.id, doc.id)[0].posting_group_id
    g2 = core.post_ledger(
        session,
        b.tenant.id,
        doc.id,
        b.customer.id,
        [("accounts_receivable", "debit", "1"), ("sales_revenue", "credit", "1")],
    )[0].posting_group_id
    core.reverse_ledger_posting_group(session, b.tenant.id, g1, reason="Correction")
    assert core._order_line_billing(session, b.tenant.id, line.id)["remaining"] == 1
    core.reverse_ledger_posting_group(session, b.tenant.id, g2, reason="Correction")
    billing = core._order_line_billing(session, b.tenant.id, line.id)
    assert billing["remaining"] == 3
    assert len(billing["evidence"][0]["reversal_ids"]) == 2


def test_payment_reversal_credit_and_excess_evidence(session, business):
    b = business
    line = order(session, b)[0]
    doc, _ = invoice(session, b, line, "2")
    payment = core.post_customer_payment(session, b.tenant.id, doc.id, "1")
    core.reverse_ledger_posting_group(
        session, b.tenant.id, payment[0].posting_group_id, reason="Payment correction"
    )
    evidence(session, b, line, "2", "credit_note")
    assert core._order_line_billing(session, b.tenant.id, line.id)["remaining"] == 1
    evidence(session, b, line, "7")
    billing = core._order_line_billing(session, b.tenant.id, line.id)
    assert (billing["invoiced"], billing["remaining"]) == (9, 0)
    other = core.create_tenant(session, "Other")
    with pytest.raises(core.NotFound):
        core._order_line_billing(session, other.id, line.id)


@pytest.mark.parametrize("change", ["invoice", "reversal"])
def test_review_stales_even_when_quantity_still_fits(session, business, change):
    b = business
    line = order(session, b)[1]
    _, group = invoice(session, b, line)
    pending = prepare(session, b, args(line))
    if change == "invoice":
        invoice(session, b, line)
    else:
        core.reverse_ledger_posting_group(
            session, b.tenant.id, group, reason="Correction"
        )
    with pytest.raises(core.InvalidOperation, match="changed"):
        confirm(session, b, pending)


def test_exact_fractional_quantities(session, business):
    line = order(session, business)[0]
    invoice(session, business, line, "0.0001")
    assert core._order_line_billing(session, business.tenant.id, line.id)[
        "remaining"
    ] == Decimal("2.9999")
    with pytest.raises(core.InvalidOperation, match="four decimal"):
        invoice(session, business, line, "0.00001")


def test_inspector_exposes_tenant_scoped_billing(session, business):
    from reality.web.api import document_inspector

    line = order(session, business)[0]
    doc, _ = invoice(session, business, line)
    result = document_inspector(session, business.tenant.id, line.document_id)
    row = next(r for r in result["evidence_lines"] if r["id"] == line.id)
    assert Decimal(str(row["billing"]["remaining"])) == 2
    assert row["billing"]["evidence"][0]["invoice_id"] == doc.id


def test_direct_and_reviewed_concurrent_invoices(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, LedgerEntry, build_engine
    from reality.tools.application import approve_and_execute_proposal

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as s:
            tenant = core.create_tenant(s, "Concurrent partial invoices")
            b = SimpleNamespace(
                tenant=tenant,
                company=core.create_party(s, tenant.id, "Company", "company"),
                customer=core.create_party(s, tenant.id, "Customer", "customer"),
                item=core.create_item(s, tenant.id, "SKU", "Item"),
                location=core.create_location(s, tenant.id, "Warehouse"),
            )
            line = order(s, b)[0]
            intent = args(line, "2")
            p = prepare(s, b, intent)
            claim = p.id, json.loads(p.input)["_delivery_review"]["token"]
            tenant_id, line_id = tenant.id, line.id
        gate = Barrier(2)

        def run(reviewed):
            with factory() as s:
                gate.wait(timeout=10)
                try:
                    if reviewed:
                        approve_and_execute_proposal(
                            s,
                            tenant_id,
                            claim[0],
                            confirmed=True,
                            review_token=claim[1],
                        )
                    else:
                        core.record_sales_invoice(
                            s, tenant_id, **{**intent, "number": "DIRECT"}
                        )
                    return True
                except core.InvalidOperation as error:
                    assert any(
                        word in str(error)
                        for word in ("remaining", "changed", "review")
                    )
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(run, [True, False])) == [False, True]
        with factory() as s:
            assert core._order_line_billing(s, tenant_id, line_id)["invoiced"] == 2
            assert s.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    finally:
        engine.dispose()


def test_http_availability_and_foreign_order(session, business):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    line = order(session, business)[0]
    invoice(session, business, line)
    foreign = core.create_tenant(session, "Other inspector tenant")
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            path = f"/inspector/document/{line.document_id}"
            response = client.get(f"/api/tenants/{business.tenant.id}{path}")
            assert response.status_code == 200, response.text
            row = next(
                r for r in response.json()["evidence_lines"] if r["id"] == line.id
            )
            assert Decimal(str(row["billing"]["remaining"])) == 2
            assert client.get(f"/api/tenants/{foreign.id}{path}").status_code == 404
    finally:
        app.dependency_overrides.clear()
