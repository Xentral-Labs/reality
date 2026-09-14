from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import LedgerEntry, LedgerReversal, SettlementAllocation
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    account_balance,
    create_document,
    create_tenant,
    ledger_reversal_snapshot,
    open_invoice_amount,
    payment_rows,
    post_customer_payment,
    post_sales_invoice,
    preview_ledger_reversal,
    reverse_ledger_posting_group,
)


def _sales_invoice(session, business, amount="100"):
    document = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "REV-INV",
        business.customer.id,
        amount,
    )
    entries = post_sales_invoice(session, business.tenant.id, document.id)
    return document, entries


def test_reversal_appends_exact_inverse_and_preserves_original(session, business):
    invoice, entries = _sales_invoice(session, business)
    original_values = [
        (row.id, row.account, row.amount, row.debit_credit, row.document_id)
        for row in entries
    ]
    preview = preview_ledger_reversal(
        session,
        business.tenant.id,
        entries[0].posting_group_id,
        reason="Invoice was posted in error",
    )

    result = reverse_ledger_posting_group(
        session,
        business.tenant.id,
        entries[0].posting_group_id,
        reason="Invoice was posted in error",
        expected_revision=preview["revision"],
        preview_fingerprint=preview["request_fingerprint"],
        actor_context={"surface": "test"},
    )

    inverse = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.posting_group_id == result.reversing_posting_group_id
            )
        )
    )
    relation = session.get(LedgerReversal, result.reversal_id)
    assert [
        (row.id, row.account, row.amount, row.debit_credit, row.document_id)
        for row in entries
    ] == original_values
    assert sorted((row.account, row.amount, row.debit_credit) for row in inverse) == sorted(
        (
            row.account,
            row.amount,
            "credit" if row.debit_credit == "debit" else "debit",
        )
        for row in entries
    )
    assert all(row.document_id is None and row.source_record_id is None for row in inverse)
    assert relation.reason == "Invoice was posted in error"
    assert account_balance(session, business.tenant.id, "accounts_receivable") == 0
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == 0


def test_payment_reversal_preserves_allocation_history_and_reopens_invoice(
    session, business
):
    invoice, _ = _sales_invoice(session, business)
    payment = post_customer_payment(
        session, business.tenant.id, invoice.id, Decimal(40)
    )
    allocation = session.scalar(select(SettlementAllocation))
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(60)

    reverse_ledger_posting_group(
        session,
        business.tenant.id,
        payment[0].posting_group_id,
        reason="Payment belongs to another customer",
    )

    assert session.get(SettlementAllocation, allocation.id) is allocation
    assert open_invoice_amount(session, business.tenant.id, invoice.id) == Decimal(100)
    reversed_payment = next(
        row for row in payment_rows(session, business.tenant.id) if row["document"].id == payment[0].document_id
    )
    assert reversed_payment["allocated"] == 0
    assert reversed_payment["unallocated"] == 0
    assert reversed_payment["reversal_role"] == "reversed_original"


def test_identical_retry_replays_and_divergent_request_conflicts(session, business):
    _, entries = _sales_invoice(session, business)
    first = reverse_ledger_posting_group(
        session,
        business.tenant.id,
        entries[0].posting_group_id,
        reason="Duplicate invoice",
        actor_context={"surface": "web"},
    )
    replay = reverse_ledger_posting_group(
        session,
        business.tenant.id,
        entries[0].posting_group_id,
        reason="Duplicate invoice",
        actor_context={"surface": "cli"},
    )
    assert replay.reversal_id == first.reversal_id
    assert replay.replayed is True
    with pytest.raises(Conflict, match="already reversed"):
        reverse_ledger_posting_group(
            session,
            business.tenant.id,
            entries[0].posting_group_id,
            reason="Different reason",
        )


def test_reversing_group_is_rejected_and_foreign_group_is_not_found(session, business):
    _, entries = _sales_invoice(session, business)
    result = reverse_ledger_posting_group(
        session,
        business.tenant.id,
        entries[0].posting_group_id,
        reason="Wrong posting",
    )
    with pytest.raises(InvalidOperation, match="cannot be reversed"):
        reverse_ledger_posting_group(
            session,
            business.tenant.id,
            result.reversing_posting_group_id,
            reason="No",
        )
    foreign = create_tenant(session, "Foreign")
    with pytest.raises(NotFound, match="posting group not found"):
        ledger_reversal_snapshot(session, foreign.id, entries[0].posting_group_id)
