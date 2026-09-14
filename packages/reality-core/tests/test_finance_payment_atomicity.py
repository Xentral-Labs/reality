"""Durable finance prerequisites for Playground O2C (096/FR-017)."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Base,
    BusinessEvent,
    Document,
    LedgerEntry,
    SettlementAllocation,
)
from reality.services import core
from reality.services.finance.accounts import initialize_accounts
from reality.tools.application import confirm_tool, propose_tool


@pytest.fixture(params=["supplier", "refund"])
def outgoing_obligation(postgres_database, request):
    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    supplier = request.param == "supplier"
    with Session(engine, expire_on_commit=False) as session:
        tenant = core.create_tenant(session, "Outgoing finance example")
        initialize_accounts(session, tenant.id)
        party = core.create_party(
            session, tenant.id, "Counterparty", "supplier" if supplier else "customer"
        )
        document = core.create_document(
            session,
            tenant.id,
            "supplier_invoice" if supplier else "credit_note",
            "OUT-1",
            party.id,
            "300",
            currency="USD",
        )
        post = core.post_supplier_invoice if supplier else core.post_sales_credit_note
        post(session, tenant.id, document.id)
        identity = tenant.id, document.id
    try:
        yield engine, *identity, request.param
    finally:
        engine.dispose()


@pytest.mark.parametrize("after_allocation", [False, True])
def test_outgoing_payment_rolls_back_all_records(
    outgoing_obligation, monkeypatch, after_allocation
):
    engine, tenant_id, document_id, kind = outgoing_obligation
    allocate = core.allocate_settlement

    def fail(*args, **kwargs):
        if after_allocation:
            allocate(*args, **kwargs)
        raise RuntimeError("Outgoing allocation failed")

    monkeypatch.setattr(core, "allocate_settlement", fail)
    service = (
        core.post_supplier_payment if kind == "supplier" else core.post_customer_refund
    )
    with Session(engine) as session:
        before_events = session.scalar(select(func.count()).select_from(BusinessEvent))
        with pytest.raises(RuntimeError, match="Outgoing allocation failed"):
            service(session, tenant_id, document_id, "125")
        session.commit()
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 1
        assert observer.scalar(select(func.count()).select_from(LedgerEntry)) == 2
        assert (
            observer.scalar(select(func.count()).select_from(SettlementAllocation)) == 0
        )
        assert (
            observer.scalar(select(func.count()).select_from(BusinessEvent))
            == before_events
        )
        assert core.open_invoice_amount(observer, tenant_id, document_id) == 300


def test_outgoing_payment_is_attributed_and_preserves_currency(outgoing_obligation):
    engine, tenant_id, document_id, kind = outgoing_obligation
    supplier = kind == "supplier"
    with Session(engine, expire_on_commit=False) as session:
        proposal = propose_tool(
            session,
            tenant_id,
            "supplier_payment_post" if supplier else "customer_refund_post",
            {
                "invoice_id" if supplier else "credit_note_id": document_id,
                "payment_number" if supplier else "refund_number": "OUT-PAY-1",
                "amount": "125",
                "effective_at": "2026-09-06T12:00:00+00:00",
            },
        )
        assert core.open_invoice_amount(session, tenant_id, document_id) == 300
        assert (
            confirm_tool(
                session,
                tenant_id,
                proposal.id,
                confirmed=True,
                review_token=json.loads(proposal.input)
                .get("_delivery_review", {})
                .get("token"),
            ).status
            == "executed"
        )
        events = list(
            session.scalars(
                select(BusinessEvent)
                .where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.action_id == proposal.id,
                )
                .order_by(BusinessEvent.sequence)
            )
        )
        assert [event.event_type for event in events] == [
            "document.recorded",
            "ledger.posted",
            "settlement.allocated",
        ]
        assert all(event.correlation_id == proposal.id for event in events)
        payment = session.get(Document, events[0].subject_id)
        assert payment.currency == "USD"
        assert core.open_invoice_amount(session, tenant_id, document_id) == 175
        confirm_tool(
            session,
            tenant_id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)
            .get("_delivery_review", {})
            .get("token"),
        )
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 2
        assert observer.scalar(select(func.count()).select_from(LedgerEntry)) == 4
        assert (
            observer.scalar(select(func.count()).select_from(SettlementAllocation)) == 1
        )


def test_outgoing_payment_joins_caller_transaction(outgoing_obligation):
    engine, tenant_id, document_id, kind = outgoing_obligation
    service = (
        core.post_supplier_payment if kind == "supplier" else core.post_customer_refund
    )
    with Session(engine) as session:
        service(session, tenant_id, document_id, "125", _commit=False)
        assert core.open_invoice_amount(session, tenant_id, document_id) == 175
        with Session(engine) as observer:
            assert core.open_invoice_amount(observer, tenant_id, document_id) == 300
        session.rollback()
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 1


@pytest.fixture
def posted_invoice(postgres_database):
    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        tenant = core.create_tenant(session, "Atomic finance example")
        initialize_accounts(session, tenant.id)
        customer = core.create_party(session, tenant.id, "Customer", "customer")
        invoice = core.create_document(
            session, tenant.id, "sales_invoice", "INV-1", customer.id, "300"
        )
        core.post_sales_invoice(session, tenant.id, invoice.id)
        identity = tenant.id, invoice.id
    try:
        yield engine, *identity
    finally:
        engine.dispose()


def test_return_credit_posting_failure_rolls_back_evidence(
    session, business, monkeypatch
):
    from reality.db.core import DocumentLine, SourceRecord

    tenant = business.tenant.id
    _, _, lines, commitments = core.create_manual_order(
        session,
        tenant,
        "sales",
        "RET-ORDER",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "25",
                "gross_amount": "25",
            }
        ],
        "25",
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    tables = (SourceRecord, Document, DocumentLine, LedgerEntry, BusinessEvent)
    before = [
        session.scalar(select(func.count()).select_from(table)) for table in tables
    ]
    post = core.post_sales_credit_note

    def fail(*args, **kwargs):
        post(*args, **kwargs)
        raise RuntimeError("Credit failed after posting")

    monkeypatch.setattr(core, "post_sales_credit_note", fail)
    with pytest.raises(RuntimeError, match="Credit failed"):
        core.record_sales_credit(session, tenant, lines[0].id, "1", "26", "CR-FAIL")
    session.commit()
    assert [
        session.scalar(select(func.count()).select_from(table)) for table in tables
    ] == before
    assert core.uncredited_return_quantity(session, tenant, lines[0].id) == 1


@pytest.mark.parametrize("after_allocation", [False, True])
def test_failed_payment_leaves_no_durable_partial_records(
    posted_invoice, monkeypatch, after_allocation
):
    engine, tenant_id, invoice_id = posted_invoice
    allocate = core.allocate_settlement

    def fail(*args, **kwargs):
        if after_allocation:
            allocate(*args, **kwargs)
        raise RuntimeError("Simulated allocation failure")

    monkeypatch.setattr(core, "allocate_settlement", fail)
    with Session(engine) as session:
        before_events = session.scalar(select(func.count()).select_from(BusinessEvent))
        with pytest.raises(RuntimeError, match="allocation failure"):
            core.post_customer_payment(
                session, tenant_id, invoice_id, "125", payment_number="PAY-1"
            )
        # Even a later caller commit must not persist a half-finished command.
        session.commit()
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 1
        assert observer.scalar(select(func.count()).select_from(LedgerEntry)) == 2
        assert (
            observer.scalar(select(func.count()).select_from(SettlementAllocation)) == 0
        )
        assert (
            observer.scalar(select(func.count()).select_from(BusinessEvent))
            == before_events
        )
        assert core.open_invoice_amount(observer, tenant_id, invoice_id) == Decimal(300)


def test_confirmed_payment_has_one_causal_event_chain(posted_invoice):
    engine, tenant_id, invoice_id = posted_invoice
    with Session(engine, expire_on_commit=False) as session:
        proposal = propose_tool(
            session,
            tenant_id,
            "customer_payment_post",
            {
                "invoice_id": invoice_id,
                "amount": "125",
                "payment_number": "PAY-1",
                "effective_at": "2026-09-06T12:00:00+00:00",
            },
        )
        assert core.open_invoice_amount(session, tenant_id, invoice_id) == Decimal(300)
        result = confirm_tool(
            session,
            tenant_id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)
            .get("_delivery_review", {})
            .get("token"),
        )
        assert result.status == "executed"
        events = list(
            session.scalars(
                select(BusinessEvent)
                .where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.action_id == proposal.id,
                )
                .order_by(BusinessEvent.sequence)
            )
        )
        assert [event.event_type for event in events] == [
            "document.recorded",
            "ledger.posted",
            "settlement.allocated",
        ]
        assert all(event.correlation_id == proposal.id for event in events)
        assert len(json.loads(events[1].payload)["entries"]) == 2
        assert core.open_invoice_amount(session, tenant_id, invoice_id) == Decimal(175)
        confirm_tool(
            session,
            tenant_id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)
            .get("_delivery_review", {})
            .get("token"),
        )
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 2
        assert observer.scalar(select(func.count()).select_from(LedgerEntry)) == 4
        assert (
            observer.scalar(select(func.count()).select_from(SettlementAllocation)) == 1
        )


def test_payment_can_join_a_callers_transaction(posted_invoice):
    engine, tenant_id, invoice_id = posted_invoice
    with Session(engine) as session:
        core.post_customer_payment(session, tenant_id, invoice_id, "125", _commit=False)
        assert core.open_invoice_amount(session, tenant_id, invoice_id) == Decimal(175)
        with Session(engine) as observer:
            assert core.open_invoice_amount(observer, tenant_id, invoice_id) == Decimal(
                300
            )
        session.rollback()
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 1
        assert observer.scalar(select(func.count()).select_from(LedgerEntry)) == 2
        assert (
            observer.scalar(select(func.count()).select_from(SettlementAllocation)) == 0
        )


def test_failed_standalone_payment_posting_leaves_no_evidence(
    posted_invoice, monkeypatch
):
    engine, tenant_id, invoice_id = posted_invoice

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated ledger failure")

    monkeypatch.setattr(core, "post_ledger", fail)
    with Session(engine) as session:
        invoice = session.get(Document, invoice_id)
        before_events = session.scalar(select(func.count()).select_from(BusinessEvent))
        with pytest.raises(RuntimeError, match="ledger failure"):
            core.record_customer_payment(session, tenant_id, invoice.party_id, "125")
        session.commit()
    with Session(engine) as observer:
        assert observer.scalar(select(func.count()).select_from(Document)) == 1
        assert (
            observer.scalar(select(func.count()).select_from(BusinessEvent))
            == before_events
        )


@pytest.mark.parametrize("fail_posting", [False, True])
@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_shared_invoice_preserves_stated_amount_and_rolls_back(
    session, business, monkeypatch, fail_posting, direction
):
    from reality.db.core import DocumentLine, SourceRecord

    _, order, lines, _ = core.create_manual_order(
        session,
        business.tenant.id,
        direction,
        "ORDER-INV",
        business.company.id,
        business.customer.id if direction == "sales" else business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "12",
                "unit": "pcs",
                "unit_price": "25",
                "gross_amount": "300",
            }
        ],
        "300",
    )
    before = session.scalar(select(func.count()).select_from(Document))
    service = (
        core.record_sales_invoice
        if direction == "sales"
        else core.record_supplier_invoice
    )
    if fail_posting:

        def fail(*args, **kwargs):
            raise RuntimeError("Invoice posting failed")

        monkeypatch.setattr(
            core,
            "post_sales_invoice" if direction == "sales" else "post_supplier_invoice",
            fail,
        )
        with pytest.raises(RuntimeError, match="Invoice posting failed"):
            service(session, business.tenant.id, lines[0].id, "12", "301", "INV-STATED")
        session.commit()
        assert session.scalar(select(func.count()).select_from(Document)) == before
        return
    result = service(
        session, business.tenant.id, lines[0].id, "12", "301", "INV-STATED"
    )
    id_ = next(r["id"] for r in result["records"] if r["family"] == "document")
    invoice = session.get(Document, id_)
    assert invoice.gross_amount == 301
    assert core.open_invoice_amount(session, business.tenant.id, invoice.id) == 301
    source = session.get(SourceRecord, invoice.source_record_id)
    assert json.loads(source.payload)["gross_amount"] == "301"
    invoice_line = session.scalar(
        select(DocumentLine).where(DocumentLine.document_id == invoice.id)
    )
    assert invoice_line.billed_document_line_id == lines[0].id
    assert order.gross_amount == 300
