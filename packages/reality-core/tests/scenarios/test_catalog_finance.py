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
from intake_review_support import (
    accept_normalized_payment,
    reviewed_create_payment_term,
    reviewed_manual_document_with_lines,
    reviewed_manual_order,
    reviewed_post_customer_payment,
    reviewed_post_sales_credit_note,
    reviewed_post_sales_invoice,
    reviewed_post_supplier_invoice,
    reviewed_record_sales_credit,
    reviewed_record_sales_invoice,
    reviewed_reserve,
)
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
from reality.services.finance.accounts import list_accounts
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
    return reviewed_manual_order(
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
    _, payment, entries, allocation, resolution = accept_normalized_payment(
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
        approve_and_execute_proposal(
            session, tenant, proposal.id, confirmed=True
        ).output
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
    recipient = reviewed_create_party(session, tenant, "Filiale Nord KG", "customer")
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
    result = reviewed_record_sales_invoice(
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
    result = reviewed_record_sales_invoice(
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
    receipt = reviewed_record_sales_credit(
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

    reviewed_record_sales_invoice(
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
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        ).output
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
    reviewed_create_payment_term(
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
        reviewed_reserve(session, tenant, commitments[0].id)
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
    reviewed_initialize_accounts(session, tenant)
    invoice = core.create_document(
        session,
        tenant,
        "sales_invoice",
        "RE-M08",
        business.customer.id,
        "1000.00",
        document_date="2026-09-01",
    )
    reviewed_post_sales_invoice(session, tenant, invoice.id)

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
    reviewed_create_payment_term(
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
        reviewed_post_sales_invoice(session, tenant, document.id)
        return document

    invoice("RE-N06-OPEN", "500.00")
    unpaid_prepayment = invoice("RE-N06-PRE", "200.00", term="PREPAY")
    note = core.create_document(
        session, tenant, "credit_note", "GS-N06", business.customer.id, "50.00"
    )
    reviewed_post_sales_credit_note(session, tenant, note.id)
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
    customer = reviewed_create_party(
        session, tenant, "Lyon Cycles SARL", "customer", tax_identifier="FR12345678901"
    )
    _, _, lines, _ = reviewed_manual_order(
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
    _, _, lines, _ = reviewed_manual_order(
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


def test_a_partly_paid_prepayment_order_is_released_by_an_owner(session, business):
    """R01: 80 % paid, refused to ship; an owner releases it with a reason and it ships.

    Spec 275 FR-005 keeps a prepayment order unshippable until paid. Spec 347 lets
    a company owner ship it anyway, for this order and with a stated reason; the
    unpaid rest stays an open receivable.
    """
    from reality.db.core import AppUser, BusinessEvent, TenantMembership, uid
    from reality.services.decision_attribution import record_decisions
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    reviewed_create_payment_term(
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
    _, order, lines, commitments = _sales_order(
        session,
        business,
        "SO-R01",
        [_order_line(business, "10", "10.00", "100.00")],
        "100.00",
        payment_term_code="PREPAY",
    )
    commitment = commitments[0]
    reviewed_reserve(session, tenant, commitment.id)
    invoice_id, _ = _invoice_line(
        session, business, lines[0].id, "10", "100.00", "RE-R01"
    )
    reviewed_post_customer_payment(session, tenant, invoice_id, "80.00")

    readiness = fulfillment_readiness(
        session, tenant, commitment.id, proposed_quantity=4
    )
    assert "prepayment_required" in readiness.blocker_codes
    assert readiness.remaining_amount == Decimal("20.00")
    dispatch = {
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
    }
    for tool, arguments in (
        ("shipment_dispatch", dispatch),
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

    def person(role):
        user = AppUser(
            id=uid("usr"),
            email=f"{uid('m')}@example.test",
            password_hash="x",
            display_name=role,
            status="active",
            email_verified_at=core.now(),
        )
        session.add(user)
        session.flush()
        session.add(
            TenantMembership(
                id=uid("mem"),
                tenant_id=tenant,
                user_id=user.id,
                role=role,
                status="active",
            )
        )
        session.flush()
        return Principal(user.id)

    reason = "Long-standing customer, the remaining 20 come with the next order"
    proposal = prepare_delivery_action(
        session,
        tenant,
        "prepayment_release",
        {"document_id": order.id, "reason": reason},
        request_id="r01-release",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    # A member who is not an owner cannot release it.
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session,
            tenant,
            proposal.id,
            review_token=token,
            confirmed=True,
            confirming_principal=person("member"),
        )
    assert refused.value.code == "company_owner_access_required"
    approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        review_token=token,
        confirmed=True,
        confirming_principal=person("owner"),
    )
    released = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "order.prepayment_released",
            BusinessEvent.action_id == proposal.id,
        )
    ).one()
    assert json.loads(released.payload)["reason"] == reason
    assert (proposal.id, "prepayment_release") in {
        (row["id"], row["tool"])
        for row in record_decisions(session, tenant, "document", order.id)
    }

    _reviewed(session, business, "shipment_dispatch", dispatch, "r01-ship")
    assert core.fulfilled_quantity(session, tenant, commitment.id) == 4
    # The unpaid rest stays an ordinary open receivable.
    assert core.open_invoice_amount(session, tenant, invoice_id) == Decimal("20.00")

    # 6 are reordered; the supplier delivers 5 on two dates.
    _, _, _, (purchase,) = reviewed_manual_order(
        session,
        tenant,
        "purchase",
        "PO-R01",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [_order_line(business, "6", "6.00", "36.00")],
        "36.00",
    )
    for received in ("3", "2"):
        core.record_movement(
            session,
            tenant,
            "receipt",
            business.item.id,
            received,
            to_location_id=business.location.id,
            commitment_id=purchase.id,
        )
    # The customer cancels 1 of the 6 still open.
    core.revise_commitment(
        session, tenant, commitment.id, quantity="9", note="Customer cancels one"
    )
    # The rest ships; the release still covers the order.
    reviewed_reserve(session, tenant, commitment.id)
    rest = {**dispatch, "movements": [{**dispatch["movements"][0], "quantity": "5"}]}
    _reviewed(session, business, "shipment_dispatch", rest, "r01-ship-rest")
    # 2 come back damaged and are scrapped.
    from reality.services.return_dispositions import record_return_disposition

    returns_area = reviewed_create_location(session, tenant, "R01 Returns")
    goods_back = core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "2",
        to_location_id=returns_area.id,
        commitment_id=commitment.id,
    )
    record_return_disposition(
        session, tenant, goods_back.id, "scrap_loss", "2", reason="Damaged in transit"
    )
    # The cancelled one and the two damaged ones are credited: 30 settles the 20
    # still open, and the 10 paid too much is refunded.
    invoice_line_id = session.scalar(
        select(DocumentLine.id).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == invoice_id
        )
    )
    credited = _reviewed(
        session,
        business,
        "sales_credit_record",
        {
            "invoice_id": invoice_id,
            "lines": [
                {
                    "invoice_line_id": invoice_line_id,
                    "quantity": "3",
                    "gross_amount": "30.00",
                }
            ],
            "gross_amount": "30.00",
            "number": "GS-R01",
            "reason": "One cancelled, two returned damaged",
            "allocation_amount": "20.00",
        },
        "r01-credit",
    )
    credit_note_id = _document_id(credited)
    _reviewed(
        session,
        business,
        "customer_refund_post",
        {"credit_note_id": credit_note_id, "amount": "10.00"},
        "r01-refund",
    )

    # Every quantity reconciles.
    assert core.commitment_quantity(session, tenant, commitment.id) == 9
    assert core.fulfilled_quantity(session, tenant, commitment.id) == 9
    assert core.fulfilled_quantity(session, tenant, purchase.id) == 5
    assert core.open_quantity(session, tenant, purchase.id) == 1
    for location in (business.location, returns_area):
        assert core.stock_at(session, tenant, business.item.id, location.id) == 0
    # Every euro reconciles: 80 paid less 10 refunded pays the 7 kept at 10.
    assert core.open_invoice_amount(session, tenant, invoice_id) == 0
    assert core.open_invoice_amount(session, tenant, credit_note_id) == 0


# --- N04 (spec 295) ------------------------------------------------------------


def _dunning_fee_account(session, business):

    tenant = business.tenant.id
    account = reviewed_create_account(
        session,
        tenant,
        code="4740",
        name="Dunning fees",
        role="dunning_fee_revenue",
        expected_revision=_revision(session, business),
    )
    reviewed_set_default_account(
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
    reviewed_post_sales_invoice(session, business.tenant.id, invoice.id)
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
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        ).output
    )


def test_three_levels_of_dunning_then_collection(session, business):
    """N04: a company schedule, runs over three customers, escalation and collection."""
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    _dunning_fee_account(session, business)
    weber = reviewed_create_party(session, tenant, "Weber AG", "customer")
    klein = reviewed_create_party(session, tenant, "Klein KG", "customer")
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
    reviewed_post_customer_payment(session, tenant, klein_invoice.id, "400.00")
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
    reviewed_post_customer_payment(session, tenant, weber_invoice.id, "400.00")
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

    tenant = business.tenant.id
    if "payment_fee_expense" in list_accounts(session, tenant)["defaults"]:
        return
    account = reviewed_create_account(
        session,
        tenant,
        code="6855",
        name="Payment fees",
        role="payment_fee_expense",
        expected_revision=_revision(session, business),
    )
    reviewed_set_default_account(
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
    reviewed_initialize_accounts(session, tenant)
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
    reviewed_post_sales_invoice(session, tenant, invoice.id)
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
    reviewed_initialize_accounts(session, tenant)
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
    invoice_id = json.loads(confirm_tool(session, tenant, recording.id, confirmed=True).output)[
        "document_id"
    ]
    confirm_tool(
        session,
        tenant,
        propose_tool(
            session, tenant, "sales_invoice_post", {"document_id": invoice_id}
        ).id,
        confirmed=True,
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


# --- Automatic credit hold: C07, C08, R08 (spec 298) ------------------------------


def _limited_customer(session, business, name, limit="1000", roles=None):
    return reviewed_create_party(
        session,
        business.tenant.id,
        name,
        "customer",
        credit_limit=limit,
        default_currency="EUR",
        payment_term_code="NET30",
        roles=roles or ["customer"],
    )


def _posted(session, business, kind, number, party, amount, day):
    document = core.create_document(
        session, business.tenant.id, kind, number, party.id, amount, document_date=day
    )
    post = {
        "sales_invoice": reviewed_post_sales_invoice,
        "credit_note": reviewed_post_sales_credit_note,
        "supplier_invoice": reviewed_post_supplier_invoice,
    }[kind]
    post(session, business.tenant.id, document.id)
    return document


def _order_through_the_tool(session, business, party, number, quantity, price):
    gross = str(Decimal(quantity) * Decimal(price))
    receipt = _reviewed(
        session,
        business,
        "order_create",
        {
            "direction": "sales",
            "number": number,
            "company_party_id": business.company.id,
            "counterparty_id": party.id,
            "location_id": business.location.id,
            "currency": "EUR",
            "gross_amount": gross,
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": quantity,
                    "unit_price": price,
                    "gross_amount": gross,
                }
            ],
        },
        number,
    )
    return receipt["document_id"], receipt["commitment_ids"]


def _credit_holds(session, business, commitment_ids):
    from reality.services.credit_exposure import active_credit_holds

    return active_credit_holds(session, business.tenant.id, list(commitment_ids))


def test_an_order_over_the_limit_is_held_and_released_by_an_owner(session, business):
    """C07: the order is held at entry; an owner releases it and says why."""
    from reality.db.core import AppUser, BusinessEvent, TenantMembership, uid
    from reality.services.decision_attribution import record_decisions
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    reviewed_create_payment_term(session, tenant, "NET30", "Net 30", 30)
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    party = _limited_customer(session, business, "Radhaus Weber")
    _posted(
        session, business, "sales_invoice", "RE-C07-1", party, "700.00", "2026-07-01"
    )

    # Positive control: an order that stays within the limit is not held.
    _, within = _order_through_the_tool(
        session, business, party, "SO-C07-OK", "2", "100.00"
    )
    assert _credit_holds(session, business, within) == []
    core.cancel_commitment(
        session, tenant, within[0], reason="Superseded by the next order"
    )

    order_id, held = _order_through_the_tool(
        session, business, party, "SO-C07", "4", "100.00"
    )
    (hold,) = _credit_holds(session, business, held)
    assert hold.note.startswith("Credit limit 1000.00 EUR exceeded by 100.00")
    assert "overdue RE-C07-1 700.00" in hold.note
    assert (
        "commitment_hold"
        in fulfillment_readiness(session, tenant, held[0]).blocker_codes
    )

    def person(role):
        user = AppUser(
            id=uid("usr"),
            email=f"{uid('m')}@example.test",
            password_hash="x",
            display_name=role,
            status="active",
            email_verified_at=core.now(),
        )
        session.add(user)
        session.flush()
        session.add(
            TenantMembership(
                id=uid("mem"),
                tenant_id=tenant,
                user_id=user.id,
                role=role,
                status="active",
            )
        )
        session.flush()
        return Principal(user.id)

    reason = "Paid by bank transfer this morning, confirmed with the bank"
    proposal = prepare_delivery_action(
        session,
        tenant,
        "credit_hold_release",
        {"document_id": order_id, "reason": reason},
        request_id="c07-release",
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    # A member who is not an owner cannot release it.
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session,
            tenant,
            proposal.id,
            review_token=token,
            confirmed=True,
            confirming_principal=person("member"),
        )
    assert refused.value.code == "company_owner_access_required"

    approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        review_token=token,
        confirmed=True,
        confirming_principal=person("owner"),
    )

    assert _credit_holds(session, business, held) == []
    released = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.event_type == "commitment.hold_released",
            BusinessEvent.action_id == proposal.id,
        )
    ).one()
    assert json.loads(released.payload)["reason"] == reason
    assert (proposal.id, "credit_hold_release") in {
        (row["id"], row["tool"])
        for row in record_decisions(session, tenant, "commitment", held[0])
    }
    reviewed_reserve(session, tenant, held[0])
    assert fulfillment_readiness(session, tenant, held[0]).ship_ready


def test_the_credit_hold_names_the_overdue_items_behind_it(session, business):
    """C08: overdue invoices are named apart from the ones not yet due."""
    from reality.services.credit_exposure import credit_exposure
    from reality.services.exceptions import operational_exceptions

    tenant = business.tenant.id
    reviewed_create_payment_term(session, tenant, "NET30", "Net 30", 30)
    party = _limited_customer(session, business, "Velo Nord")
    late = [
        _posted(session, business, "sales_invoice", number, party, amount, day)
        for number, amount, day in (
            ("RE-C08-1", "400.00", "2026-07-01"),
            ("RE-C08-2", "200.00", "2026-07-15"),
        )
    ]
    due_today = _posted(
        session,
        business,
        "sales_invoice",
        "RE-C08-3",
        party,
        "300.00",
        core.now().date().isoformat(),
    )

    _, held = _order_through_the_tool(session, business, party, "SO-C08", "2", "100.00")

    (hold,) = _credit_holds(session, business, held)
    assert "overdue RE-C08-1 400.00, RE-C08-2 200.00)" in hold.note
    # The invoice not yet due counts in the exposure but is not named overdue.
    exposure = credit_exposure(session, tenant, party.id)
    assert due_today.id in {
        row["document_id"] for row in exposure["open_invoices"]["rows"]
    }
    assert due_today.id not in {
        row["document_id"] for row in exposure["overdue_invoices"]["rows"]
    }
    finding = next(
        row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "credit_limit_exceeded" and row.record_id == party.id
    )
    assert finding.causal_values["overdue_document_ids"] == [doc.id for doc in late]
    assert finding.causal_values["overdue_amount"] == Decimal("600.0000")


def test_a_customer_who_is_also_a_supplier_is_held_with_every_fact(session, business):
    """R08: overdue receivable, open credit, payable and a new order, all named."""
    from reality.services.credit_exposure import credit_exposure

    tenant = business.tenant.id
    reviewed_create_payment_term(session, tenant, "NET30", "Net 30", 30)
    party = _limited_customer(
        session, business, "Kurbelwerk GmbH", roles=["customer", "supplier"]
    )
    _posted(
        session, business, "sales_invoice", "RE-R08-1", party, "800.00", "2026-07-01"
    )
    _posted(session, business, "credit_note", "GS-R08-1", party, "100.00", "2026-08-15")
    _posted(
        session, business, "supplier_invoice", "ER-R08-1", party, "500.00", "2026-09-01"
    )

    _, held = _order_through_the_tool(session, business, party, "SO-R08", "4", "100.00")

    (hold,) = _credit_holds(session, business, held)
    # 800 overdue + 400 ordered - 100 credit = 1,100; the payable is not netted.
    assert hold.note.startswith("Credit limit 1000.00 EUR exceeded by 100.00")
    assert "exposure 1100.00" in hold.note
    assert "overdue RE-R08-1 800.00" in hold.note
    assert "credits 100.00" in hold.note
    assert "payables 500.00 EUR named, not netted" in hold.note
    exposure = credit_exposure(session, tenant, party.id)
    assert [row["number"] for row in exposure["payables"]["rows"]] == ["ER-R08-1"]
    assert [row["number"] for row in exposure["available_credits"]["rows"]] == [
        "GS-R08-1"
    ]


# --- E03, Q01, E11, C14 (spec 299) ----------------------------------------------


def _stocked_order(session, business, number, *, prepay=False, quantity="10"):
    tenant = business.tenant.id
    if prepay:
        reviewed_create_payment_term(
            session, tenant, f"PRE-{number}", "Prepayment", 0, requires_prepayment=True
        )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )
    _, order, lines, commitments = _sales_order(
        session,
        business,
        number,
        [_order_line(business, quantity, "100.00", f"{quantity}00.00")],
        f"{quantity}00.00",
        **({"payment_term_code": f"PRE-{number}"} if prepay else {}),
    )
    reviewed_reserve(session, tenant, commitments[0].id)
    return order, lines[0], commitments[0]


def _dispatch(business, commitment, quantity):
    return (
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": quantity,
                }
            ],
        },
    )


def _down_payment_invoice(session, business, order, amount, number):
    receipt = _reviewed(
        session,
        business,
        "down_payment_invoice_record",
        {
            "order_id": order.id,
            "number": number,
            "gross_amount": amount,
            "effective_at": "2026-09-01T10:00:00Z",
        },
        number,
    )
    return receipt["document_id"]


def _classes(session, business):
    from reality.services.exceptions import operational_exceptions

    return {
        (row.class_id, row.record_id)
        for row in operational_exceptions(session, business.tenant.id)
    }


def test_a_proforma_and_an_early_invoice_are_visible_until_the_goods_ship(
    session, business
):
    """E03: a pro-forma, then the invoice before delivery; invoiced but not
    shipped is reported until the goods leave."""
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    order, line, commitment = _stocked_order(session, business, "SO-E03")

    proforma = _reviewed(
        session,
        business,
        "proforma_invoice_record",
        {"order_id": order.id, "number": "PF-E03", "gross_amount": "1000.00"},
        "PF-E03",
    )
    # The pro-forma is evidence for the order only: no open item, nothing billed.
    assert proforma["document_id"] not in {
        row["document_id"] for row in core.financial_open_items(session, tenant)
    }
    assert ("billed_not_shipped", line.id) not in _classes(session, business)

    invoice_id, _ = _invoice_line(session, business, line.id, "10", "1000.00", "RE-E03")
    assert ("billed_not_shipped", line.id) in _classes(session, business)
    assert core.open_invoice_amount(session, tenant, invoice_id) == Decimal("1000.00")

    _reviewed(session, business, *_dispatch(business, commitment, "10"), "E03-ship")
    assert ("billed_not_shipped", line.id) not in _classes(session, business)
    assert ("shipped_not_billed", line.id) not in _classes(session, business)


def test_the_month_end_lists_both_directions_from_the_same_findings(session, business):
    """Q01: shipped and not invoiced, invoiced and not shipped, at one instant."""
    from reality.services.month_end_billing import month_end_billing

    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    _, shipped_line, shipped = _stocked_order(session, business, "SO-Q01-A")
    _, billed_line, billed = _stocked_order(session, business, "SO-Q01-B")
    _reviewed(session, business, *_dispatch(business, shipped, "4"), "Q01-ship-a")
    _invoice_line(session, business, billed_line.id, "5", "500.00", "RE-Q01-B")

    lists = month_end_billing(session, tenant)
    assert [
        (row["order_number"], row["quantity"]) for row in lists["shipped_not_billed"]
    ] == [("SO-Q01-A", "4.0000")]
    assert [
        (row["order_number"], row["quantity"]) for row in lists["billed_not_shipped"]
    ] == [("SO-Q01-B", "5.0000")]
    # The lists are the findings: the same order lines, under the same identities.
    findings = _classes(session, business)
    assert ("shipped_not_billed", shipped_line.id) in findings
    assert ("billed_not_shipped", billed_line.id) in findings

    # Next month the four are invoiced and the five shipped: both lists are empty.
    _invoice_line(session, business, shipped_line.id, "4", "400.00", "RE-Q01-A")
    _reviewed(session, business, *_dispatch(business, billed, "5"), "Q01-ship-b")
    lists = month_end_billing(session, tenant)
    assert (lists["shipped_not_billed"], lists["billed_not_shipped"]) == ([], [])


def test_the_final_invoice_states_the_down_payment_it_deducts(session, business):
    """E11: a 30 % down-payment invoice, paid, offset in the final invoice."""
    from reality.web.api import document_inspector

    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    order, line, _ = _stocked_order(session, business, "SO-E11")
    down_payment = _down_payment_invoice(session, business, order, "300.00", "AR-E11")
    reviewed_post_customer_payment(
        session, tenant, down_payment, "300.00", payment_number="PAY-E11"
    )

    proposal = prepare_delivery_action(
        session,
        tenant,
        "sales_invoice_record",
        {
            "order_line_id": line.id,
            "quantity": "10",
            "gross_amount": "1000.00",
            "number": "RE-E11",
            "down_payment_offsets": [
                {"down_payment_document_id": down_payment, "amount": "300.00"}
            ],
        },
        request_id="RE-E11",
    )
    review = json.loads(proposal.input)["_delivery_review"]
    # The person sees what was paid and what the invoice leaves open.
    (offer,) = review["state"]["down_payment_offers"]
    assert (offer["number"], offer["paid"], offer["offsettable"]) == (
        "AR-E11",
        "300.0000",
        "300.0000",
    )
    assert review["state"]["open_after_offsets"] == "700.00"
    executed = approve_and_execute_proposal(
        session, tenant, proposal.id, review_token=review["token"], confirmed=True
    )
    final = _document_id(json.loads(executed.output))

    assert core.open_invoice_amount(session, tenant, final) == Decimal("700.00")
    assert core.account_balance(session, tenant, "customer_down_payments") == 0
    # The final invoice names the down payment it deducts, and the down payment
    # names the final invoice, each with the stated amount.
    for document, other in ((final, "AR-E11"), (down_payment, "RE-E11")):
        sections = {
            section["title"]: section["rows"]
            for section in document_inspector(session, tenant, document)["sections"]
        }
        (row,) = sections["Down-payment offsets"]
        assert row["label"] == other
    order_rows = {
        section["title"]: section["rows"]
        for section in document_inspector(session, tenant, order.id)["sections"]
    }["Down-payment and pro-forma invoices"]
    assert [row.get("meta") for row in order_rows] == ["Paid 300.00 · offset 300.00"]


def test_a_30_percent_down_payment_holds_the_shipment_until_the_rest_is_paid(
    session, business
):
    """C14: the down payment counts, the rest is required, then it ships."""
    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    order, line, commitment = _stocked_order(session, business, "SO-C14", prepay=True)
    readiness = fulfillment_readiness(session, tenant, commitment.id)
    assert "prepayment_invoice_missing" in readiness.blocker_codes

    down_payment = _down_payment_invoice(session, business, order, "300.00", "AR-C14")
    reviewed_post_customer_payment(
        session, tenant, down_payment, "300.00", payment_number="PAY-C14-1"
    )
    readiness = fulfillment_readiness(session, tenant, commitment.id)
    assert (readiness.received_amount, readiness.remaining_amount) == (
        Decimal("300.00"),
        Decimal("700.0000"),
    )
    assert readiness.blocker_codes == ("prepayment_required",)
    with pytest.raises(core.InvalidOperation) as refused:
        prepare_delivery_action(
            session, tenant, *_dispatch(business, commitment, "10"), request_id="c14-1"
        )
    assert refused.value.code == "shipment_blocked_readiness"

    final, _ = _invoice_line(
        session,
        business,
        line.id,
        "10",
        "1000.00",
        "RE-C14",
        down_payment_offsets=[
            {"down_payment_document_id": down_payment, "amount": "300.00"}
        ],
    )
    # Still 700 to pay: the offset is not a second payment.
    assert fulfillment_readiness(session, tenant, commitment.id).remaining_amount == (
        Decimal("700.0000")
    )
    reviewed_post_customer_payment(
        session, tenant, final, "700.00", payment_number="PAY-C14-2"
    )

    readiness = fulfillment_readiness(session, tenant, commitment.id)
    assert readiness.ship_ready and readiness.received_amount == Decimal("1000.00")
    _reviewed(session, business, *_dispatch(business, commitment, "10"), "C14-ship")
    assert core.fulfilled_quantity(session, tenant, commitment.id) == 10


# --- E07 ---------------------------------------------------------------------


def test_an_invoice_that_differs_from_the_order_is_reported_each_way(session, business):
    """E07: billed more, billed less and billed at another price are each reported."""
    from reality.services.exceptions import operational_exceptions

    tenant = business.tenant.id
    _, _document, lines, promises = _sales_order(
        session,
        business,
        "SO-E07",
        [
            _order_line(business, "12", "10", "120"),
            _order_line(business, "10", "10", "100"),
            _order_line(business, "10", "10", "100"),
        ],
        "320",
    )
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "30",
        to_location_id=business.location.id,
    )
    for promise in promises:
        core.record_movement(
            session,
            tenant,
            "shipment",
            business.item.id,
            "10",
            from_location_id=business.location.id,
            commitment_id=promise.id,
        )
    over, under, priced = lines
    # Positive control: shipped and not yet billed is the ordinary state.
    before = {
        (row.class_id, row.record_id)
        for row in operational_exceptions(
            session, tenant, as_of=datetime(2027, 1, 31, tzinfo=UTC)
        )
    }
    assert ("billed_not_shipped", over.id) not in before

    _invoice_line(session, business, over.id, "12", "120", "RE-E07-1")
    _invoice_line(session, business, under.id, "8", "80", "RE-E07-2")
    reviewed_manual_document_with_lines(
        session,
        tenant,
        "sales_invoice",
        "RE-E07-3",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "11",
                "gross_amount": "110",
                "billed_document_line_id": priced.id,
            }
        ],
        "110",
    )

    found = {
        (row.class_id, row.record_id): row
        for row in operational_exceptions(
            session, tenant, as_of=datetime(2027, 1, 31, tzinfo=UTC)
        )
    }
    assert (
        found[("billed_not_shipped", over.id)].causal_values["unshipped_quantity"] == 2
    )
    assert ("shipped_not_billed", under.id) in found
    assert any(
        class_id == "invoice_price_differs"
        and row.causal_values["agreed_unit_price"] == Decimal(10)
        and row.causal_values["billed_unit_price"] == Decimal(11)
        for (class_id, _), row in found.items()
    )


# --- Payouts and authorizations: L03, R04, C09, C10, C13 (spec 336) -----------

R04_ORDERS = 400


def _provider(session, business, name, account_name):
    """A provider as a business partner, with its own cash account beside the bank."""

    tenant = business.tenant.id
    reviewed_initialize_accounts(session, tenant)
    _payment_fee_account(session, business)
    provider = reviewed_create_party(session, tenant, name, "supplier")
    account = reviewed_create_account(
        session,
        tenant,
        code=f"13{core.uid('x')[-6:]}",
        name=account_name,
        role="cash",
        expected_revision=_revision(session, business),
    )
    return provider, account["id"]


def _billed_order(session, business, number, amount, party=None):
    """A sales order of one line and its posted invoice, written directly for scale."""
    tenant = business.tenant.id
    party = party or business.customer
    line = {
        "item_id": business.item.id,
        "quantity": "1",
        "unit_price": amount,
        "gross_amount": amount,
        "unit": "pcs",
        "source_line_id": "1",
    }
    _, (order_line,) = reviewed_manual_document_with_lines(
        session, tenant, "sales_order", number, party.id, [line], amount, _commit=False
    )
    invoice, (invoice_line,) = reviewed_manual_document_with_lines(
        session,
        tenant,
        "sales_invoice",
        f"RE-{number}",
        party.id,
        [{**line, "billed_document_line_id": order_line.id}],
        amount,
        document_date="2026-09-20",
        _commit=False,
    )
    reviewed_post_sales_invoice(session, tenant, invoice.id, _commit=False)
    return invoice, invoice_line


def _payout(provider, account, reference, amount, lines, paid_on="2026-09-30"):
    return {
        "provider_party_id": provider.id,
        "payout_reference": reference,
        "paid_on": paid_on,
        "currency": "EUR",
        "amount": amount,
        "clearing_account_id": account,
        "lines": lines,
    }


def _charge(line_id, kind, amount, order=None, reference_type="shop_order_number"):
    return {
        "line_id": line_id,
        "kind": kind,
        "amount": amount,
        "references": [{"type": reference_type, "value": order}] if order else [],
    }


def _cash_on(session, business, account_id):
    total = Decimal(0)
    for entry in session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == business.tenant.id,
            LedgerEntry.account_id == account_id,
        )
    ):
        total += entry.amount if entry.debit_credit == "debit" else -entry.amount
    return total


def test_a_marketplace_payout_settles_each_order_and_books_the_fees(session, business):
    """L03: one payment for many orders minus fees and a refund: each order settled,
    the refund settles its credit note, the fees are charges."""
    tenant = business.tenant.id
    amazon, account = _provider(
        session, business, "Amazon EU S.a.r.l.", "Amazon Payments"
    )
    invoices = [
        _billed_order(session, business, f"AMZ-L03-{n}", "39.90")[0] for n in range(5)
    ]
    refunded, refunded_line = _billed_order(session, business, "AMZ-L03-R", "20.00")
    reviewed_manual_document_with_lines(
        session,
        tenant,
        "credit_note",
        "GS-L03",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "20.00",
                "gross_amount": "20.00",
                "billed_document_line_id": refunded_line.id,
            }
        ],
        "20.00",
        _commit=False,
    )
    note = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant, Document.number == "GS-L03"
        )
    )
    reviewed_post_sales_credit_note(session, tenant, note.id, _commit=False)
    bank = list_accounts(session, tenant)["defaults"]["cash"]
    bank_before = _cash_on(session, business, bank)

    lines = [_charge(str(n), "charge", "39.90", f"AMZ-L03-{n}") for n in range(5)] + [
        _charge("R", "charge", "20.00", "AMZ-L03-R"),
        _charge("R-refund", "refund", "20.00", "AMZ-L03-R"),
        _charge("fees", "fee", "29.93"),
    ]
    review, _ = _finance(
        session,
        business,
        "finance.payout.settle",
        _payout(amazon, account, "AMZ-PAYOUT-0930", "169.57", lines),
    )

    assert review["payout"]["unmatched_line_ids"] == []
    assert [core.open_invoice_amount(session, tenant, i.id) for i in invoices] == [
        0
    ] * 5
    assert core.open_invoice_amount(session, tenant, refunded.id) == 0
    assert core.open_invoice_amount(session, tenant, note.id) == 0
    assert core.account_balance(session, tenant, "payment_fee_expense") == Decimal(
        "29.93"
    )
    assert _cash_on(session, business, bank) - bank_before == Decimal("169.57")
    assert _cash_on(session, business, account) == 0
    # Positive control: nothing of the payout is reported as unbooked.
    assert not _findings(session, business, "payout_line_unmatched")


def test_a_payout_of_400_orders_with_refunds_chargebacks_and_fees_books_every_line(
    session, business
):
    """R04: 400 orders, 12 refunds, 3 chargebacks and fees in one payout; every
    position is allocated, and the settlement grows linearly with its lines."""
    from sqlalchemy import event

    tenant = business.tenant.id
    amazon, account = _provider(
        session, business, "Amazon EU S.a.r.l.", "Amazon Payments"
    )
    # Three orders paid in an earlier payout come back as chargebacks.
    earlier = [
        _billed_order(session, business, f"AMZ-R04-E{n}", "40.00")[0] for n in range(3)
    ]
    _finance(
        session,
        business,
        "finance.payout.settle",
        _payout(
            amazon,
            account,
            "AMZ-R04-0915",
            "120.00",
            [_charge(f"E{n}", "charge", "40.00", f"AMZ-R04-E{n}") for n in range(3)],
            paid_on="2026-09-15",
        ),
    )
    billed = [
        _billed_order(session, business, f"AMZ-R04-{n:03d}", "25.00")
        for n in range(R04_ORDERS)
    ]
    for n, (_, line) in enumerate(billed[:12]):
        note, _ = reviewed_manual_document_with_lines(
            session,
            tenant,
            "credit_note",
            f"GS-R04-{n:03d}",
            business.customer.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit_price": "25.00",
                    "gross_amount": "25.00",
                    "billed_document_line_id": line.id,
                }
            ],
            "25.00",
            _commit=False,
        )
        reviewed_post_sales_credit_note(session, tenant, note.id, _commit=False)
    session.commit()
    lines = (
        [
            _charge(f"C{n:03d}", "charge", "25.00", f"AMZ-R04-{n:03d}")
            for n in range(R04_ORDERS)
        ]
        + [
            _charge(f"R{n:03d}", "refund", "25.00", f"AMZ-R04-{n:03d}")
            for n in range(12)
        ]
        + [_charge(f"B{n}", "chargeback", "40.00", f"AMZ-R04-E{n}") for n in range(3)]
        + [_charge("commission", "fee", "1500.00"), _charge("ads", "fee", "80.00")]
    )
    statements = []

    def count(*_):
        statements.append(1)

    event.listen(session.bind, "before_cursor_execute", count)
    try:
        review, receipt = _finance(
            session,
            business,
            "finance.payout.settle",
            _payout(
                amazon,
                account,
                "AMZ-R04-0930",
                f"{R04_ORDERS * 25 - 300 - 120 - 1580:.2f}",
                lines,
            ),
        )
    finally:
        event.remove(session.bind, "before_cursor_execute", count)

    assert review["payout"]["unmatched_line_ids"] == []
    assert receipt["unmatched_line_ids"] == []
    assert len(receipt["lines"]) == R04_ORDERS + 17
    assert all(
        core.open_invoice_amount(session, tenant, invoice.id) == 0
        for invoice, _ in billed
    )
    assert [core.open_invoice_amount(session, tenant, i.id) for i in earlier] == [
        Decimal(40)
    ] * 3
    assert {
        row.record_id for row in _findings(session, business, "payment_returned")
    } == {invoice.id for invoice in earlier}
    assert core.account_balance(session, tenant, "payment_fee_expense") == Decimal(
        "1580.00"
    )
    # The provider's account is empty after both payouts: everything was booked.
    assert _cash_on(session, business, account) == 0
    # Review and settlement take a bounded number of statements per line; the
    # lines are booked as one batch (spec 342: about 16 per line, 83 before).
    assert len(statements) < (R04_ORDERS + 17) * 20, len(statements)


def test_cash_on_delivery_is_tied_to_the_parcel_it_was_collected_for(session, business):
    """C13: the carrier remits the collected amount minus its fee; the line names
    the parcel's tracking number, which leads to the order and its invoice."""
    tenant = business.tenant.id
    dhl, account = _provider(session, business, "DHL Paket GmbH", "DHL Nachnahme")
    _, order_line, commitment = _stocked_order(
        session, business, "SO-C13", quantity="1"
    )
    tool, arguments = _dispatch(business, commitment, "1")
    shipped = _reviewed(
        session,
        business,
        tool,
        {**arguments, "carrier": "DHL", "tracking_number": "00340434161094042557"},
        "c13-dispatch",
    )
    invoice_id, _ = _invoice_line(
        session, business, order_line.id, "1", "100.00", "RE-C13"
    )

    review, receipt = _finance(
        session,
        business,
        "finance.payout.settle",
        _payout(
            dhl,
            account,
            "DHL-COD-2026-09-30",
            "97.50",
            [
                _charge(
                    "1",
                    "charge",
                    "100.00",
                    "00340434161094042557",
                    reference_type="tracking_number",
                ),
                _charge("cod-fee", "fee", "2.50"),
            ],
        ),
    )

    (line,) = [row for row in review["payout"]["lines"] if row["kind"] == "charge"]
    assert (line["outcome"], line["invoice_id"]) == ("allocate", invoice_id)
    assert core.open_invoice_amount(session, tenant, invoice_id) == 0
    paid = next(row for row in receipt["lines"] if row["line_id"] == "1")
    assert paid["allocated_to"] == [invoice_id]
    assert paid["shipment_ids"] == [shipped["shipment_id"]]


def _authorization(session, business, order, amount, valid_days, reference, at=None):
    from datetime import timedelta

    at = at or core.now() - timedelta(days=10)
    _, receipt = _finance(
        session,
        business,
        "finance.payment.authorization.record",
        {
            "order_document_id": order.id,
            "amount": amount,
            "currency": "EUR",
            "authorized_at": at.isoformat(),
            "valid_until": (at + timedelta(days=valid_days)).isoformat(),
            "reference": reference,
        },
    )
    return receipt


def _capture(session, business, authorization, amount, at):
    return _finance(
        session,
        business,
        "finance.payment.capture.record",
        {
            "authorization_id": authorization["id"],
            "amount": amount,
            "captured_at": at.isoformat(),
            "reference": f"CAP-{amount}",
        },
    )[1]


def test_authorization_and_capture_are_separate_facts(session, business):
    """C09: a card authorization of 100 is captured in two parts as the goods ship;
    authorized, captured and left are read apart, and nothing beyond is captured."""
    from datetime import timedelta

    from reality.services.payment_authorizations import authorizations

    tenant = business.tenant.id
    order, _, _ = _stocked_order(session, business, "SO-C09", quantity="1")
    authorized = _authorization(
        session,
        business,
        order,
        "100.00",
        30,
        "pi_3Q0C09",
        at=core.now() - timedelta(days=2),
    )
    first = _capture(
        session, business, authorized, "60.00", core.now() - timedelta(days=1)
    )
    assert (first["captured"], first["remaining"], first["state"]) == (
        "60",
        "40",
        "live",
    )

    second = _capture(session, business, authorized, "40.00", core.now())

    (row,) = authorizations(session, tenant, order_document_id=order.id)
    assert (row["amount"], row["captured"], row["remaining"], row["state"]) == (
        "100",
        "100",
        "0",
        "captured",
    )
    assert second["state"] == "captured"
    with pytest.raises(core.InvalidOperation) as refused:
        _capture(session, business, authorized, "0.01", core.now())
    assert refused.value.code == "payment_capture_exceeds_authorization"
    assert not _findings(session, business, "payment_authorization_expired")


def test_an_expired_authorization_shows_the_uncovered_rest_of_a_late_shipment(
    session, business
):
    """C10: 60 of 100 were captured with the first parcel; the authorization lapses
    before the late rest ships, and the uncovered 40 are visible until re-authorized."""
    from datetime import timedelta

    from reality.services.exceptions import operational_exceptions

    tenant = business.tenant.id
    order, _, commitment = _stocked_order(session, business, "SO-C10")
    authorized = _authorization(session, business, order, "1000.00", 7, "pi_3Q0C10")
    tool, arguments = _dispatch(business, commitment, "6")
    _reviewed(session, business, tool, arguments, "c10-first")
    _capture(session, business, authorized, "600.00", core.now() - timedelta(days=9))

    found = {
        row.record_id: row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "payment_authorization_expired"
    }
    assert found[order.id].causal_values["uncovered_amount"] == 400
    assert found[order.id].causal_values["captured_amount"] == 600

    _authorization(session, business, order, "400.00", 7, "pi_3Q0C10-re", at=core.now())

    assert order.id not in {
        row.record_id
        for row in operational_exceptions(session, tenant)
        if row.class_id == "payment_authorization_expired"
    }


from intake_review_support import (
    reviewed_create_account,
    reviewed_create_location,
    reviewed_create_party,
    reviewed_initialize_accounts,
    reviewed_set_default_account,
)
