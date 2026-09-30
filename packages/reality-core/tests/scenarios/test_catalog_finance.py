"""Scenario catalog: finance cases that were supported but never proven.

Each test names its catalog ID (C04, C06, E09, E10, F13, M08, N01, N02, N04, N06) and drives the business
through the same application services the web, CLI and agent use.
"""

import hashlib
import io
import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    Party,
    SourceArtifact,
    SourceRecord,
)
from reality.services import core, payment_intake
from reality.services.artifacts import materialize_artifact, stage_artifact
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.finance import components
from reality.services.finance import references as finance_references
from reality.services.finance.accounts import initialize_accounts, list_accounts
from reality.services.finance.balances import party_balance_rows
from reality.services.finance.credits import available_credit_items
from reality.services.finance.settlement_flows import settlement_context
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.services.payment_intake import NormalisedPayment, Reference
from reality.tools.application import (
    approve_and_execute_proposal,
    confirm_tool,
    create_change_proposal,
    propose_tool,
)


def _sales_order(session, business, number, lines, total, **extra):
    return core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        lines,
        total,
        **extra,
    )


def _order_line(business, quantity, unit_price, gross_amount):
    return {
        "item_id": business.item.id,
        "quantity": quantity,
        "unit": "pcs",
        "unit_price": unit_price,
        "gross_amount": gross_amount,
    }


def _customer_balance(session, business, before):
    rows = party_balance_rows(
        session,
        business.tenant.id,
        side="customer",
        effective_before=before,
        party_ids={business.customer.id},
    )
    return {(row["open"], row["credit"], row["balance"]) for row in rows}


# --- C06 ---------------------------------------------------------------------


def test_payment_after_a_cancelled_prepayment_order_stays_credit_and_is_refunded(
    session, business
):
    """C06: money paid after the order was cancelled stays as the customer's
    credit, is visible as owed back, and can be refunded exactly once."""
    tenant = business.tenant.id
    _, order, _, commitments = _sales_order(
        session,
        business,
        "SO-PRE-1",
        [_order_line(business, "1", "119.00", "119.00")],
        "119.00",
        customer_reference="PO-PRE-1",
    )
    for commitment in commitments:
        core.cancel_commitment(
            session, tenant, commitment.id, reason="Customer cancelled before paying"
        )
    assert [c.status for c in commitments] == ["cancelled"]

    # The prepayment arrives anyway, naming the cancelled order.
    at = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
    payload = {
        "references": [{"type": "shop_order_number", "value": "SO-PRE-1"}],
        "remittance_text": "Prepayment SO-PRE-1",
    }
    source, _ = core.enqueue_source(
        session, tenant, "bank_statement", "payment", "stmt-7:line-1", payload
    )
    _, payment, entries, allocation, resolution = (
        payment_intake.interpret_customer_payment(
            session,
            tenant,
            source,
            NormalisedPayment(
                party_id=business.customer.id,
                amount=Decimal("119.00"),
                currency="EUR",
                effective_at=at,
                external_payment_id="stmt-7:line-1",
                references=(Reference(type="shop_order_number", value="SO-PRE-1"),),
                remittance_text=payload["remittance_text"],
            ),
        )
    )

    # The money is recorded, but nothing is invoiced, so nothing absorbs it.
    assert allocation is None and resolution.unambiguous is None
    assert resolution.reasons == ("order SO-PRE-1 is not invoiced yet",)
    assert sorted((e.account, e.debit_credit, e.amount) for e in entries) == [
        ("accounts_receivable", "credit", Decimal("119.0000")),
        ("cash", "debit", Decimal("119.0000")),
    ]
    assert payment_intake.unallocated_amount(session, tenant, payment.id) == Decimal(
        "119.0000"
    )
    credits = available_credit_items(session, tenant, side="customer")["items"]
    assert [(r["document_id"], r["origin"], Decimal(r["open"])) for r in credits] == [
        (payment.id, "payment", Decimal("119.0000"))
    ]
    before = datetime(2026, 9, 11, tzinfo=UTC)
    assert _customer_balance(session, business, before) == {
        (Decimal(0), Decimal("119.0000"), Decimal("-119.0000"))
    }
    # The order itself carries no payment status: it is still only evidence.
    assert order.status == "recorded"

    # The refund goes through the confirmed guided settlement.
    proposal = create_change_proposal(
        session,
        tenant,
        "finance.settlement.apply",
        {
            "document_id": payment.id,
            "mode": "refund_credit",
            "amount": "119.00",
            "expected_revision": list_accounts(session, tenant)["revision"],
            "reference": "Refund SO-PRE-1 cancelled",
            "effective_at": "2026-09-12T09:00:00+00:00",
        },
        actor_type="human",
    )
    review = json.loads(proposal.output)["settlement"]
    assert review["cash_direction"] == "outgoing"
    assert Decimal(review["remaining_credit"]) == 0
    receipt = json.loads(
        approve_and_execute_proposal(session, tenant, proposal.id).output
    )

    refund = record_by_id(session, Document, receipt["refund"]["document_id"])
    assert refund.type == "customer_refund"
    assert refund.party_id == business.customer.id
    assert refund.gross_amount == Decimal("119.0000")
    refund_entries = [
        record_by_id(session, LedgerEntry, id_)
        for id_ in receipt["refund"]["ledger_entry_ids"]
    ]
    assert sorted((e.account, e.debit_credit, e.amount) for e in refund_entries) == [
        ("accounts_receivable", "debit", Decimal("119.0000")),
        ("cash", "credit", Decimal("119.0000")),
    ]
    assert Decimal(settlement_context(session, tenant, payment.id)["available"]) == 0
    assert available_credit_items(session, tenant, side="customer")["items"] == []
    # Nothing is owed any more; before the refund the credit was still owed.
    assert _customer_balance(session, business, None) == set()
    assert _customer_balance(session, business, before) == {
        (Decimal(0), Decimal("119.0000"), Decimal("-119.0000"))
    }


# --- E09 ---------------------------------------------------------------------


def test_invoice_billed_to_the_orderer_keeps_a_different_ship_to_party(
    session, business
):
    """E09: an order billed to the orderer but shipped to another party keeps
    both parties; the invoice and its receivable name the orderer, and the
    ship-to stays readable through the invoice line's order."""
    tenant = business.tenant.id
    recipient = core.create_party(session, tenant, "Filiale Nord KG", "customer")
    _, order, order_lines, commitments = _sales_order(
        session,
        business,
        "SO-SHIP-1",
        [_order_line(business, "2", "40.00", "80.00")],
        "80.00",
        ship_to_party_id=recipient.id,
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    result = core.record_sales_invoice(
        session,
        tenant,
        order_lines[0].id,
        "2",
        "80.00",
        "RE-SHIP-1",
        effective_at=datetime(2026, 9, 15, 9, 0, tzinfo=UTC),
    )
    invoice = record_by_id(
        session,
        Document,
        next(r["id"] for r in result["records"] if r["family"] == "document"),
    )

    # Bill-to: the orderer owes the money, not the recipient.
    assert order.party_id == business.customer.id
    assert invoice.party_id == business.customer.id
    receivable = core._settlement_control_entry(session, tenant, invoice.id)
    assert receivable.party_id == business.customer.id
    assert receivable.amount == Decimal("80.0000")
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal("80.0000")
    balances = party_balance_rows(
        session,
        tenant,
        side="customer",
        effective_before=datetime(2026, 9, 16, tzinfo=UTC),
    )
    assert {(r["party_id"], r["open"]) for r in balances} == {
        (business.customer.id, Decimal("80.0000"))
    }

    # Ship-to: kept on the order and reached from the invoice by its line link.
    invoice_line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == invoice.id
        )
    )
    billed = record_by_id(session, DocumentLine, invoice_line.billed_document_line_id)
    billed_order = record_by_id(session, Document, billed.document_id)
    assert billed_order.id == order.id
    assert billed_order.ship_to_party_id == recipient.id
    assert recipient.id != business.customer.id
    detail = core.document_detail(session, tenant, order.id)
    assert detail["party"].id == business.customer.id
    assert detail["ship_to_party"].id == recipient.id
    assert detail["ship_to_party"].name == "Filiale Nord KG"
    source = record_by_id(session, SourceRecord, order.source_record_id)
    assert json.loads(source.payload)["ship_to_party_id"] == recipient.id
    assert core.fulfilled_quantity(session, tenant, commitments[0].id) == Decimal(
        "2.0000"
    )


# --- E10 ---------------------------------------------------------------------

XRECHNUNG = (
    '﻿<?xml version="1.0" encoding="UTF-8"?>\r\n'
    '<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"'
    ' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
    "\r\n  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#"
    "urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>\r\n"
    "  <cbc:ID>RE-2026-0917</cbc:ID>\r\n"
    "  <cbc:IssueDate>2026-09-17</cbc:IssueDate>\r\n"
    "  <cbc:Note>Lieferung Fahrradlichter, Straße 5, München</cbc:Note>\r\n"
    '  <cbc:PayableAmount currencyID="EUR">1190.00</cbc:PayableAmount>\r\n'
    "</ubl:Invoice>\r\n"
).encode()


def test_e_invoice_xml_is_stored_losslessly_as_traceable_source_evidence(
    session, business, tmp_path, monkeypatch
):
    """E10: an XRechnung XML is kept byte for byte as a source artifact, traced
    from its SourceRecord, and is not interpreted into a document."""
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    tenant = business.tenant.id
    artifact, sample = stage_artifact(
        session,
        tenant,
        io.BytesIO(XRECHNUNG),
        filename="RE-2026-0917.xml",
        content_type="application/xml",
    )
    assert artifact.sha256 == hashlib.sha256(XRECHNUNG).hexdigest()
    assert artifact.byte_size == len(XRECHNUNG)
    assert sample == XRECHNUNG
    with materialize_artifact(artifact) as path:
        assert path.read_bytes() == XRECHNUNG

    proposal = propose_tool(
        session,
        tenant,
        "source_ingest",
        {
            "artifact_id": artifact.id,
            "source_system": "einvoice_inbox",
            "source_type": "xrechnung",
            "expected_target": "supplier_invoice",
        },
        actor_type="human",
    )
    output = json.loads(confirm_tool(session, tenant, proposal.id).output)
    source = record_by_id(session, SourceRecord, output["source_record_id"])
    session.refresh(artifact)

    assert artifact.status == "attached"
    assert source.source_artifact_id == artifact.id
    assert json.loads(source.payload)["artifact"] == {
        "filename": "RE-2026-0917.xml",
        "content_type": "application/xml",
        "byte_size": len(XRECHNUNG),
        "sha256": hashlib.sha256(XRECHNUNG).hexdigest(),
        "storage": "managed",
    }
    # No e-invoice interpreter exists: the evidence waits, nothing is invented.
    assert output["import_status"] == "unmapped"
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant)
        )
        == 0
    )
    # The same bytes arriving again are the same artifact, still byte-exact.
    again, _ = stage_artifact(
        session,
        tenant,
        io.BytesIO(XRECHNUNG),
        filename="copy.xml",
        content_type="application/xml",
    )
    assert again.id == artifact.id
    assert (
        session.scalar(
            select(func.count())
            .select_from(SourceArtifact)
            .where(SourceArtifact.tenant_id == tenant)
        )
        == 1
    )
    with materialize_artifact(again) as path:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == again.sha256


# --- F13 ---------------------------------------------------------------------


def test_return_credit_after_month_end_books_in_the_next_month(session, business):
    """F13: a credit note for a returned item of an August invoice, stated on
    3 September, posts in September while the invoice stays in August."""
    tenant = business.tenant.id
    _, _, order_lines, commitments = _sales_order(
        session,
        business,
        "SO-MONTH-1",
        [_order_line(business, "2", "50.00", "100.00")],
        "100.00",
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
        occurred_at=datetime(2026, 8, 27, 14, 0, tzinfo=UTC),
    )
    invoiced_at = datetime(2026, 8, 28, 10, 0, tzinfo=UTC)
    result = core.record_sales_invoice(
        session,
        tenant,
        order_lines[0].id,
        "2",
        "100.00",
        "RE-0828",
        effective_at=invoiced_at,
    )
    invoice = record_by_id(
        session,
        Document,
        next(r["id"] for r in result["records"] if r["family"] == "document"),
    )
    invoice_line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == invoice.id
        )
    )
    # One item comes back after month end.
    core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
        commitment_id=commitments[0].id,
        occurred_at=datetime(2026, 9, 3, 8, 0, tzinfo=UTC),
    )
    credited_at = datetime(2026, 9, 3, 9, 0, tzinfo=UTC)
    receipt = core.record_sales_credit(
        session,
        tenant,
        invoice_id=invoice.id,
        lines=[
            {
                "invoice_line_id": invoice_line.id,
                "quantity": "1",
                "gross_amount": "50.00",
            }
        ],
        gross_amount="50.00",
        number="GS-0903",
        reason="Returned after month end",
        allocation_amount="0",
        effective_at=credited_at,
    )
    note = record_by_id(
        session,
        Document,
        next(r["id"] for r in receipt["records"] if r["family"] == "document"),
    )

    assert invoice.document_date.isoformat() == "2026-08-28"
    assert note.document_date.isoformat() == "2026-09-03"

    def postings(document):
        return sorted(
            (e.account, e.debit_credit, e.amount, e.effective_at)
            for e in session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == tenant,
                    LedgerEntry.document_id == document.id,
                )
            )
        )

    assert postings(invoice) == [
        ("accounts_receivable", "debit", Decimal("100.0000"), invoiced_at),
        ("sales_revenue", "credit", Decimal("100.0000"), invoiced_at),
    ]
    assert postings(note) == [
        ("accounts_receivable", "credit", Decimal("50.0000"), credited_at),
        ("sales_revenue", "debit", Decimal("50.0000"), credited_at),
    ]

    # The August close sees the full invoice and no credit; September adds the
    # credit, which stays the customer's until it is netted or refunded.
    september = datetime(2026, 9, 1, tzinfo=UTC)
    october = datetime(2026, 10, 1, tzinfo=UTC)
    assert _customer_balance(session, business, september) == {
        (Decimal("100.0000"), Decimal(0), Decimal("100.0000"))
    }
    assert _customer_balance(session, business, october) == {
        (Decimal("100.0000"), Decimal("50.0000"), Decimal("50.0000"))
    }

    def revenue(start, end):
        return sum(
            (
                e.amount if e.debit_credit == "credit" else -e.amount
                for e in session.scalars(
                    select(LedgerEntry).where(
                        LedgerEntry.tenant_id == tenant,
                        LedgerEntry.account == "sales_revenue",
                        LedgerEntry.effective_at >= start,
                        LedgerEntry.effective_at < end,
                    )
                )
            ),
            Decimal(0),
        )

    assert revenue(datetime(2026, 8, 1, tzinfo=UTC), september) == Decimal("100.0000")
    assert revenue(september, october) == Decimal("-50.0000")
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal("100.0000")
    assert core.open_invoice_amount(session, tenant, note.id) == Decimal("50.0000")


# --- E02 ---------------------------------------------------------------------


def test_one_monthly_invoice_bills_the_deliveries_of_three_orders(session, business):
    """E02: the month's deliveries of one customer are billed on one invoice."""
    from reality.services.exceptions import operational_exceptions
    from reality.services.invoice_billing import billable_positions

    tenant = business.tenant.id
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    for index, shipped in enumerate(("2", "3", "1"), 1):
        _, _, _, commitments = _sales_order(
            session,
            business,
            f"SO-E02-{index}",
            [_order_line(business, "3", "10.00", "30.00")],
            "30.00",
            document_date=f"2026-09-0{index}",
        )
        core.record_movement(
            session,
            tenant,
            "shipment",
            business.item.id,
            shipped,
            from_location_id=business.location.id,
            commitment_id=commitments[0].id,
        )

    def unbilled():
        return {
            row.record_id
            for row in operational_exceptions(
                session, tenant, as_of=datetime(2026, 9, 30, tzinfo=UTC)
            )
            if row.class_id == "shipped_not_billed"
        }

    month = billable_positions(
        session,
        tenant,
        direction="sales",
        party_id=business.customer.id,
        currency="EUR",
    )
    assert [order["number"] for order in month["orders"]] == [
        "SO-E02-1",
        "SO-E02-2",
        "SO-E02-3",
    ]
    positions = [p for order in month["orders"] for p in order["positions"]]
    assert [p["billable"] for p in positions] == [Decimal(2), Decimal(3), Decimal(1)]
    assert unbilled() == {p["order_line_id"] for p in positions}

    core.record_sales_invoice(
        session,
        tenant,
        lines=[
            {
                "order_line_id": p["order_line_id"],
                "quantity": str(p["billable"]),
                "gross_amount": str(p["billable"] * 10),
            }
            for p in positions
        ],
        gross_amount="60.00",
        number="INV-E02-2026-09",
        effective_at=datetime(2026, 9, 30, 12, tzinfo=UTC),
    )

    assert unbilled() == set()
    after = billable_positions(
        session,
        tenant,
        direction="sales",
        party_id=business.customer.id,
        currency="EUR",
    )
    assert (after["total"], after["orders"]) == (0, [])


# --- Payments, balances and stated tax: C04, M08, N06, N01, N02 (spec 292) -----


def _reviewed(session, business, tool, arguments, request_id):
    proposal = prepare_delivery_action(
        session, business.tenant.id, tool, arguments, request_id=request_id
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    executed = approve_and_execute_proposal(
        session, business.tenant.id, proposal.id, review_token=token, confirmed=True
    )
    assert executed.status == "executed"
    return json.loads(executed.output)


def _finance(session, business, command, arguments):
    proposal = create_change_proposal(
        session, business.tenant.id, command, arguments, actor_type="human"
    )
    # What the person reviewed, read before the execution receipt replaces it.
    review = json.loads(proposal.output)
    receipt = json.loads(
        approve_and_execute_proposal(session, business.tenant.id, proposal.id).output
    )
    return review, receipt


def _revision(session, business):
    return list_accounts(session, business.tenant.id)["revision"]


def _document_id(receipt):
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def _invoice_line(session, business, order_line_id, quantity, gross, number, **extra):
    receipt = _reviewed(
        session,
        business,
        "sales_invoice_record",
        {
            "order_line_id": order_line_id,
            "quantity": quantity,
            "gross_amount": gross,
            "number": number,
            "effective_at": "2026-09-01T10:00:00Z",
            **extra,
        },
        number,
    )
    return _document_id(receipt), receipt


# --- C04 ---------------------------------------------------------------------


def test_one_payment_releases_two_prepaid_orders(session, business):
    """C04: one transfer pays both prepayment invoices and both orders may ship."""
    tenant = business.tenant.id
    core.create_payment_term(
        session, tenant, "PREPAY", "Prepayment", 0, requires_prepayment=True
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    orders = []
    for number in ("SO-C04-1", "SO-C04-2"):
        _, _, lines, commitments = _sales_order(
            session,
            business,
            number,
            [_order_line(business, "5", "20.00", "100.00")],
            "100.00",
            payment_term_code="PREPAY",
        )
        core.reserve(session, tenant, commitments[0].id)
        orders.append((lines[0], commitments[0]))
    invoices = [
        _invoice_line(session, business, line.id, "5", "100.00", f"RE-C04-{n}")[0]
        for n, (line, _) in enumerate(orders, start=1)
    ]
    blocked = [
        fulfillment_readiness(session, tenant, commitment.id)
        for _, commitment in orders
    ]
    assert [r.blocker_codes for r in blocked] == [("prepayment_required",)] * 2

    # One bank line of 200: booked on the first invoice, the rest on the second.
    _, paid = _finance(
        session,
        business,
        "finance.settlement.apply",
        {
            "document_id": invoices[0],
            "mode": "payment",
            "amount": "200.00",
            "allocation_amount": "100.00",
            "expected_revision": _revision(session, business),
            "reference": "Bank line 2026-09-02 SO-C04-1 SO-C04-2",
            "effective_at": "2026-09-02T09:00:00Z",
        },
    )
    payment_id = paid["payment"]["document_id"]
    _finance(
        session,
        business,
        "finance.settlement.apply",
        {
            "document_id": payment_id,
            "mode": "allocate_credit",
            "invoice_id": invoices[1],
            "amount": "100.00",
            "expected_revision": _revision(session, business),
        },
    )

    assert [core.open_invoice_amount(session, tenant, i) for i in invoices] == [0, 0]
    assert Decimal(settlement_context(session, tenant, payment_id)["available"]) == 0
    released = [
        fulfillment_readiness(session, tenant, commitment.id)
        for _, commitment in orders
    ]
    assert [(r.ship_ready, r.blocker_codes) for r in released] == [(True, ())] * 2
    assert [r.remaining_amount for r in released] == [0, 0]
    assert core.account_balance(session, tenant, "cash") == Decimal("200.00")


# --- M08 ---------------------------------------------------------------------


def test_a_customer_deduction_with_an_agreed_reason_leaves_nothing_open(
    session, business
):
    """M08: the customer keeps a marketing contribution; the invoice closes with why."""
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-M08",
        business.customer.id,
        "1000.00",
        document_date="2026-09-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)

    reviewed, receipt = _finance(
        session,
        business,
        "finance.settlement.apply",
        {
            "document_id": invoice.id,
            "mode": "payment",
            "amount": "970.00",
            "allocation_amount": "970.00",
            "expected_revision": _revision(session, business),
            "reference": "Bank line RE-M08 less WKZ",
            "effective_at": "2026-09-20T09:00:00Z",
            "reduction": {
                "amount": "30.00",
                "reason_category": "agreed_deduction",
                "reason": "Marketing contribution per annual agreement",
            },
        },
    )

    review = reviewed["settlement"]
    assert review["reduction"]["reason_category"] == "agreed_deduction"
    assert Decimal(review["remaining_claim"]) == 0
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    assert Decimal(receipt["cash_amount"]) == Decimal("970.00")
    adjustment = session.scalars(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == "internal_settlement_adjustment",
        )
    ).one()
    stated = json.loads(adjustment.payload)
    assert stated["reason_category"] == "agreed_deduction"
    assert stated["reason"] == "Marketing contribution per annual agreement"
    assert _customer_balance(session, business, None) == set()


# --- N06 ---------------------------------------------------------------------


def test_the_party_balance_counts_credits_deposits_and_prepayments_once(
    session, business
):
    """N06: open invoices, a credit note, a deposit and prepayments in one balance."""
    tenant = business.tenant.id
    core.create_payment_term(
        session, tenant, "PREPAY", "Prepayment", 0, requires_prepayment=True
    )

    def invoice(number, amount, term=""):
        document = core.create_document(
            session,
            tenant,
            "sales_invoice",
            number,
            business.customer.id,
            amount,
            document_date="2026-09-01",
            payment_term_code=term,
        )
        core.post_sales_invoice(session, tenant, document.id)
        return document

    invoice("RE-N06-OPEN", "500.00")
    unpaid_prepayment = invoice("RE-N06-PRE", "200.00", term="PREPAY")
    note = core.create_document(
        session, tenant, "credit_note", "GS-N06", business.customer.id, "50.00"
    )
    core.post_sales_credit_note(session, tenant, note.id)
    _finance(
        session,
        business,
        "finance.deposit.record",
        {
            "expected_revision": _revision(session, business),
            "side": "customer",
            "party_id": business.customer.id,
            "amount": "300.00",
            "currency": "EUR",
            "reference": "DEP-N06",
            "effective_at": "2026-09-02T10:00:00+00:00",
        },
    )
    # A prepayment that arrived before its invoice is unallocated money.
    core.record_customer_payment(
        session, tenant, business.customer.id, "80.00", payment_number="PAY-N06"
    )

    credits = {
        row["origin"]: Decimal(row["open"])
        for row in available_credit_items(session, tenant, side="customer")["items"]
    }
    assert credits == {
        "credit_note": Decimal("50.00"),
        "deposit": Decimal("300.00"),
        "payment": Decimal("80.00"),
    }
    assert core.open_invoice_amount(session, tenant, unpaid_prepayment.id) == (
        Decimal("200.00")
    )
    # Open 500 + 200; credit 50 + 300 + 80; each item counted once.
    assert _customer_balance(session, business, None) == {
        (Decimal("700.0000"), Decimal("430.0000"), Decimal("270.0000"))
    }


# --- N01 / N02 ---------------------------------------------------------------


def test_an_intra_community_supply_keeps_its_stated_zero_tax_and_case(
    session, business
):
    """N01: zero tax, the EU case and the customer's VAT ID are kept as stated."""
    tenant = business.tenant.id
    customer = core.create_party(
        session, tenant, "Lyon Cycles SARL", "customer", tax_identifier="FR12345678901"
    )
    _, _, lines, _ = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-N01",
        business.company.id,
        customer.id,
        business.location.id,
        [_order_line(business, "10", "25.00", "250.00")],
        "250.00",
    )
    stated = {"net": "250.00", "tax": "0.00"}
    invoice_id, _ = _invoice_line(
        session,
        business,
        lines[0].id,
        "10",
        "250.00",
        "RE-N01",
        reality_finance_v1=stated,
    )
    _, case = _finance(
        session,
        business,
        "finance.reference.create",
        {
            "expected_revision": finance_references.list_references(session, tenant)[
                "revision"
            ],
            "kind": "case_code",
            "code": "EU_B2B_SUPPLY",
            "name": "Intra-community supply",
            "reason": "Tax case of the invoice",
        },
    )
    context = components.component_context(session, tenant, invoice_id)
    item = context["items"][0]
    _, assigned = _finance(
        session,
        business,
        "finance.component.assign",
        {
            "document_id": invoice_id,
            "document_line_id": item["document_line_id"],
            "basis": "net",
            "expected_evidence_hash": item["evidence_hash"],
            "expected_revision": context["revision"],
            "parts": [],
            "case_reference_id": case["id"],
            "reason": "Stated intra-community supply",
        },
    )

    amounts = components.component_context(session, tenant, invoice_id)["items"][0][
        "amounts"
    ]
    assert (amounts["net"], amounts["tax"], amounts["gross"]) == ("250", "0", "250")
    history = components.component_history(session, tenant, assigned["component_id"])
    assert history["items"][0]["references"]["case"]["code"] == "EU_B2B_SUPPLY"
    assert record_by_id(session, Party, customer.id).tax_identifier == "FR12345678901"
    # Nothing was computed: the receivable is the stated gross.
    assert core.open_invoice_amount(session, tenant, invoice_id) == Decimal("250.00")


def test_a_reverse_charge_supplier_invoice_keeps_its_stated_amounts(session, business):
    """N02: net and zero tax are kept as stated; self-assessed tax is not a field."""
    tenant = business.tenant.id
    _, _, lines, _ = core.create_manual_order(
        session,
        tenant,
        "purchase",
        "PO-N02",
        business.company.id,
        business.supplier.id,
        business.location.id,
        # Twenty ordered, so a second invoice can only fail on its tax.
        [_order_line(business, "20", "40.00", "800.00")],
        "800.00",
    )
    arguments = {
        "order_line_id": lines[0].id,
        "quantity": "10",
        "gross_amount": "400.00",
        "number": "ER-N02",
        "effective_at": "2026-09-01T10:00:00Z",
    }
    receipt = _reviewed(
        session,
        business,
        "supplier_invoice_record",
        {**arguments, "reality_finance_v1": {"net": "400.00", "tax": "0.00"}},
        "ER-N02",
    )
    invoice_id = _document_id(receipt)

    amounts = components.component_context(session, tenant, invoice_id)["items"][0][
        "amounts"
    ]
    assert (amounts["net"], amounts["tax"], amounts["gross"]) == ("400", "0", "400")
    # The self-assessed 19 % cannot be stated as tax on a gross that excludes it.
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session,
            tenant,
            "supplier_invoice_record",
            {
                **arguments,
                "number": "ER-N02-RC",
                "reality_finance_v1": {"net": "400.00", "tax": "76.00"},
            },
            request_id="ER-N02-RC",
        )
    assert refused.value.code == "stated_invoice_net_tax_gross_mismatch"


# --- R01 (spec 294) ----------------------------------------------------------


def test_a_partly_paid_prepayment_order_cannot_be_released_anyway(session, business):
    """R01 stays partial: the catalog story releases an 80 % prepaid order anyway.

    Spec 275 FR-005 keeps a prepayment order non-shippable until paid, and no
    reviewed release overrides that. Both shipping routes refuse, so the
    combined story stops at its third step. The day a reviewed release exists,
    this test turns red and R01 can be written end to end.
    """
    tenant = business.tenant.id
    core.create_payment_term(
        session, tenant, "PREPAY", "Prepayment", 0, requires_prepayment=True
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "4",
        to_location_id=business.location.id,
    )
    _, _, lines, commitments = _sales_order(
        session,
        business,
        "SO-R01",
        [_order_line(business, "10", "10.00", "100.00")],
        "100.00",
        payment_term_code="PREPAY",
    )
    commitment = commitments[0]
    core.reserve(session, tenant, commitment.id)
    invoice_id, _ = _invoice_line(
        session, business, lines[0].id, "10", "100.00", "RE-R01"
    )
    core.post_customer_payment(session, tenant, invoice_id, "80.00")

    readiness = fulfillment_readiness(
        session, tenant, commitment.id, proposed_quantity=4
    )
    assert "prepayment_required" in readiness.blocker_codes
    assert readiness.remaining_amount == Decimal("20.00")

    for tool, arguments in (
        (
            "shipment_dispatch",
            {
                "purpose": "customer_delivery",
                "counterparty_id": business.customer.id,
                "movements": [
                    {
                        "commitment_id": commitment.id,
                        "item_id": business.item.id,
                        "from_location_id": business.location.id,
                        "quantity": "4",
                    }
                ],
            },
        ),
        (
            "movement_create",
            {
                "movement_type": "shipment",
                "item_id": business.item.id,
                "quantity": "4",
                "from_location_id": business.location.id,
                "commitment_id": commitment.id,
            },
        ),
    ):
        with pytest.raises(core.InvalidOperation) as refused:
            prepare_delivery_action(
                session, tenant, tool, arguments, request_id=f"r01-{tool}"
            )
        assert refused.value.code == "shipment_blocked_readiness", tool
    assert core.fulfilled_quantity(session, tenant, commitment.id) == 0


# --- N04 (spec 295) ------------------------------------------------------------


def _dunning_fee_account(session, business):
    from reality.services.finance.accounts import create_account, set_default_account

    tenant = business.tenant.id
    account = create_account(
        session,
        tenant,
        code="4740",
        name="Dunning fees",
        role="dunning_fee_revenue",
        expected_revision=_revision(session, business),
    )
    set_default_account(
        session,
        tenant,
        role="dunning_fee_revenue",
        account_id=account["id"],
        expected_revision=_revision(session, business),
    )


def _overdue_invoice(session, business, number, party, day, amount="400.00"):
    invoice = core.create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        number,
        party.id,
        amount,
        document_date=day,
    )
    core.post_sales_invoice(session, business.tenant.id, invoice.id)
    return invoice


def _run_preview(session, business, day):
    from reality.tools.application import run_read_tool

    return run_read_tool(
        session, business.tenant.id, "finance.dunning.run_context", {"run_date": day}
    )


def _proposed_levels(context):
    return {
        item["number"]: (notice["level"], notice["fee_amount"])
        for notice in context["notices"]
        for item in notice["items"]
    }


def _run_proposal(session, business, context):
    return create_change_proposal(
        session,
        business.tenant.id,
        "finance.dunning.run",
        {
            "schedule_source_record_id": context["schedule_source_record_id"],
            "run_date": context["run_date"],
            "items": [
                {"invoice_id": item["invoice_id"], "level": notice["level"]}
                for notice in context["notices"]
                for item in notice["items"]
            ],
        },
        actor_type="human",
    )


def _confirm(session, business, proposal):
    return json.loads(
        approve_and_execute_proposal(session, business.tenant.id, proposal.id).output
    )


def test_three_levels_of_dunning_then_collection(session, business):
    """N04: a company schedule, runs over three customers, escalation and collection."""
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    _dunning_fee_account(session, business)
    weber = core.create_party(session, tenant, "Weber AG", "customer")
    klein = core.create_party(session, tenant, "Klein KG", "customer")
    _finance(
        session,
        business,
        "finance.dunning.schedule.set",
        {
            "expected_revision": _revision(session, business),
            "levels": [
                {"level": 1, "wait_days": 7, "fee_amount": "0"},
                {"level": 2, "wait_days": 14, "fee_amount": "5.00"},
                {"level": 3, "wait_days": 14, "fee_amount": "10.00"},
            ],
        },
    )
    mueller = _overdue_invoice(
        session, business, "RE-N04-M", business.customer, "2026-06-01"
    )
    _overdue_invoice(session, business, "RE-N04-W", weber, "2026-06-01")
    klein_invoice = _overdue_invoice(session, business, "RE-N04-K", klein, "2026-06-01")
    later = _overdue_invoice(
        session, business, "RE-N04-M2", business.customer, "2026-08-25"
    )

    # Run 1: every customer's item is overdue by more than seven days.
    first = _run_preview(session, business, "2026-06-10")
    assert _proposed_levels(first) == {
        "RE-N04-M": (1, "0.0000"),
        "RE-N04-W": (1, "0.0000"),
        "RE-N04-K": (1, "0.0000"),
    }
    receipt = _confirm(session, business, _run_proposal(session, business, first))
    assert len(receipt["notices"]) == 3 and receipt["skipped"] == []
    assert all(notice["fee_document_id"] is None for notice in receipt["notices"])

    # Klein pays; before its waiting period nothing else is due.
    core.post_customer_payment(session, tenant, klein_invoice.id, "400.00")
    assert _proposed_levels(_run_preview(session, business, "2026-06-20")) == {}

    # Run 2: the second level with its fee. Weber pays after the review.
    second = _run_preview(session, business, "2026-06-24")
    assert _proposed_levels(second) == {
        "RE-N04-M": (2, "5.0000"),
        "RE-N04-W": (2, "5.0000"),
    }
    proposal = _run_proposal(session, business, second)
    weber_invoice = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "RE-N04-W"
        )
    )
    core.post_customer_payment(session, tenant, weber_invoice.id, "400.00")
    receipt = _confirm(session, business, proposal)
    assert [notice["invoice_ids"] for notice in receipt["notices"]] == [[mueller.id]]
    assert receipt["skipped"] == [
        {
            "invoice_id": weber_invoice.id,
            "number": "RE-N04-W",
            "level": 2,
            "code": "paid",
        }
    ]
    fees = [receipt["notices"][0]["fee_document_id"]]

    # Run 3: the last level.
    third = _run_preview(session, business, "2026-07-08")
    assert _proposed_levels(third) == {"RE-N04-M": (3, "10.0000")}
    receipt = _confirm(session, business, _run_proposal(session, business, third))
    fees.append(receipt["notices"][0]["fee_document_id"])
    assert [core.open_invoice_amount(session, tenant, fee) for fee in fees] == [
        Decimal("5.00"),
        Decimal("10.00"),
    ]

    # After level 3 the item is ready for collection, not dunned again.
    fourth = _run_preview(session, business, "2026-07-22")
    assert _proposed_levels(fourth) == {}
    assert [item["number"] for item in fourth["ready_for_collection"]] == ["RE-N04-M"]
    assert (
        core.active_party_delivery_hold(session, tenant, business.customer.id) is None
    )

    _, handover = _finance(
        session,
        business,
        "finance.dunning.collection.handover",
        {
            "expected_revision": _revision(session, business),
            "invoice_ids": [mueller.id],
            "handover_date": "2026-08-01",
            "reason": "Unpaid after the third reminder",
        },
    )
    hold = core.active_party_delivery_hold(session, tenant, business.customer.id)
    assert hold.reason_code == "collection" and handover["hold_id"] == hold.id

    # The handed-over item is never dunned again; the customer's newer invoice is.
    fifth = _run_preview(session, business, "2026-09-10")
    assert _proposed_levels(fifth) == {"RE-N04-M2": (1, "0.0000")}
    assert {item["number"]: item["code"] for item in fifth["left_out"]} == {
        "RE-N04-M": "in_collection"
    }
    assert later.id in {
        item["invoice_id"] for notice in fifth["notices"] for item in notice["items"]
    }


# --- C15, E08 (spec 297) -------------------------------------------------------------


def _payment_fee_account(session, business):
    from reality.services.finance.accounts import create_account, set_default_account

    tenant = business.tenant.id
    if "payment_fee_expense" in list_accounts(session, tenant)["defaults"]:
        return
    account = create_account(
        session,
        tenant,
        code="6855",
        name="Payment fees",
        role="payment_fee_expense",
        expected_revision=_revision(session, business),
    )
    set_default_account(
        session,
        tenant,
        role="payment_fee_expense",
        account_id=account["id"],
        expected_revision=_revision(session, business),
    )


def _findings(session, business, class_id):
    from reality.services.exceptions import operational_exceptions

    return [
        row
        for row in operational_exceptions(
            session, business.tenant.id, as_of=datetime(2026, 10, 31, tzinfo=UTC)
        )
        if row.class_id == class_id
    ]


def _pay(session, business, invoice_id, cash, reference, reduction=None):
    arguments = {
        "mode": "payment",
        "document_id": invoice_id,
        "amount": cash,
        "allocation_amount": cash,
        "expected_revision": _revision(session, business),
        "reference": reference,
        "effective_at": "2026-09-15T08:00:00Z",
        **({"reduction": reduction} if reduction else {}),
    }
    return _finance(session, business, "finance.settlement.apply", arguments)[1]


def test_a_returned_direct_debit_reopens_the_invoice_and_charges_the_fee(
    session, business
):
    """C15: the debit comes back with a bank fee; the invoice is open until paid again."""
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    _payment_fee_account(session, business)
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-C15",
        business.customer.id,
        "240.00",
        document_date="2026-09-01",
    )
    core.post_sales_invoice(session, tenant, invoice.id)
    paid = _pay(session, business, invoice.id, "240.00", "SEPA debit 0915")
    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    # Positive control for the absence: a paid invoice raises no return finding.
    assert _findings(session, business, "payment_returned") == []

    review, returned = _finance(
        session,
        business,
        "finance.payment.return",
        {
            "payment_document_id": paid["payment"]["document_id"],
            "kind": "direct_debit_return",
            "returned_on": "2026-09-20",
            "reason": "AC04 account closed",
            "reference": "RTN-C15",
            "fee_amount": "3.50",
            "fee_bearer": "customer",
        },
    )

    assert review["payment_return"]["reopened"][0]["number"] == "RE-C15"
    assert core.open_invoice_amount(session, tenant, invoice.id) == Decimal("240.00")
    assert core.open_invoice_amount(
        session, tenant, returned["fee_charge_document_id"]
    ) == Decimal("3.50")
    (finding,) = _findings(session, business, "payment_returned")
    assert (finding.record_id, finding.causal_values["reason"]) == (
        invoice.id,
        "AC04 account closed",
    )

    _pay(session, business, invoice.id, "240.00", "Bank transfer after the return")

    assert core.open_invoice_amount(session, tenant, invoice.id) == 0
    assert _findings(session, business, "payment_returned") == []
    # The fee is the customer's own charge and stays owed.
    assert core.open_invoice_amount(
        session, tenant, returned["fee_charge_document_id"]
    ) == Decimal("3.50")


def test_freight_surcharge_and_a_deducted_payment_fee_stay_apart_from_the_goods(
    session, business
):
    """E08: freight and a small-quantity surcharge are their own lines; the PSP fee is a cost."""
    tenant = business.tenant.id
    initialize_accounts(session, tenant)
    _payment_fee_account(session, business)
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    _, _, lines, commitments = _sales_order(
        session,
        business,
        "SO-E08",
        [_order_line(business, "2", "50.00", "100.00")],
        "100.00",
        document_date="2026-09-01",
    )
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=commitments[0].id,
    )
    # Positive control: before the invoice, the delivery is shipped and not billed.
    assert {
        row.record_id for row in _findings(session, business, "shipped_not_billed")
    } == {lines[0].id}

    recording = propose_tool(
        session,
        tenant,
        "document_create",
        {
            "document_type": "sales_invoice",
            "number": "RE-E08",
            "party_id": business.customer.id,
            "gross_amount": "106.90",
            "document_date": "2026-09-05",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "2",
                    "unit": "pcs",
                    "unit_price": "50.00",
                    "gross_amount": "100.00",
                    "billed_document_line_id": lines[0].id,
                },
                {
                    "line_type": "shipping",
                    "description": "Freight",
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "4.90",
                    "gross_amount": "4.90",
                },
                {
                    "line_type": "charge",
                    "description": "Small-quantity surcharge",
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "2.00",
                    "gross_amount": "2.00",
                },
            ],
        },
    )
    invoice_id = json.loads(confirm_tool(session, tenant, recording.id).output)[
        "document_id"
    ]
    confirm_tool(
        session,
        tenant,
        propose_tool(
            session, tenant, "sales_invoice_post", {"document_id": invoice_id}
        ).id,
    )

    charges = [
        line
        for line in session.scalars(
            select(DocumentLine).where(DocumentLine.document_id == invoice_id)
        )
        if line.line_type in {"shipping", "charge"}
    ]
    assert sorted((line.line_type, line.gross_amount) for line in charges) == [
        ("charge", Decimal("2.00")),
        ("shipping", Decimal("4.90")),
    ]
    assert all(line.billed_document_line_id is None for line in charges)
    # The goods line billed the delivery; the charges are no unbilled or unmatched goods.
    assert _findings(session, business, "shipped_not_billed") == []

    # The provider pays out 103.50 and states a fee of 3.40.
    _pay(
        session,
        business,
        invoice_id,
        "103.50",
        "Stripe payout po_E08",
        reduction={
            "amount": "3.40",
            "reason_category": "payment_fee",
            "reason": "Stripe fee",
        },
    )

    assert core.open_invoice_amount(session, tenant, invoice_id) == 0
    assert core.account_balance(session, tenant, "payment_fee_expense") == Decimal(
        "3.40"
    )
