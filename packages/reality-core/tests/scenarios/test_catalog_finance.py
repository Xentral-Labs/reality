"""Scenario catalog: finance cases that were supported but never proven.

Each test names its catalog ID (C06, E09, E10, F13) and drives the business
through the same application services the web, CLI and agent use.
"""

import hashlib
import io
import json
from datetime import UTC, datetime
from decimal import Decimal

from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    SourceArtifact,
    SourceRecord,
)
from reality.services import core, payment_intake
from reality.services.artifacts import materialize_artifact, stage_artifact
from reality.services.finance.accounts import list_accounts
from reality.services.finance.balances import party_balance_rows
from reality.services.finance.credits import available_credit_items
from reality.services.finance.settlement_flows import settlement_context
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
