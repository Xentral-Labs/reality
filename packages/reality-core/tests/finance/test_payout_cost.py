"""Spec 342: a payout statement is booked as one batch at a bounded cost per line."""

import json
from contextlib import nullcontext
from decimal import Decimal

from sqlalchemy import event, func, select

from reality.db.core import (
    BusinessEvent,
    Document,
    FinanceState,
    LedgerEntry,
    PaymentReturn,
    SettlementAllocation,
    SourceRecord,
)
from reality.services import core
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from tests.finance.test_payouts import (
    _accounts,
    _credit_note,
    _invoiced_order,
    _line,
    _statement,
)

#: Measured 15 statements per further line to book and under 1 to review
#: (82 and 10 before the batch); the margin absorbs flush order.
SETTLE_PER_LINE = 18
REVIEW_PER_LINE = 2


def _payout(session, business, clearing, prefix, orders, reference):
    """Charges, refunds of credit notes, chargebacks of same-statement charges, fees."""
    lines, total = [], Decimal(0)
    for n in range(orders):
        number = f"{prefix}-{n:04d}"
        _, invoice = _invoiced_order(session, business, number, "25")
        lines.append(_line(f"c{n}", "charge", "25", number))
        total += 25
        if n % 20 == 1:
            _credit_note(session, business, invoice, "5")
            lines.append(_line(f"r{n}", "refund", "5", number))
            total -= 5
        if n % 50 == 2:
            lines.append(_line(f"b{n}", "chargeback", "25", number))
            total -= 25
        if n % 10 == 3:
            lines.append(_line(f"f{n}", "fee", "0.75"))
            total -= Decimal("0.75")
    return _statement(business, clearing, lines, str(total), reference=reference)


def _counted(session, call):
    statements = []

    def count(*_):
        statements.append(1)

    event.listen(session.bind, "before_cursor_execute", count)
    try:
        result = call()
    finally:
        event.remove(session.bind, "before_cursor_execute", count)
    return len(statements), result


def _settle_counted(session, tenant, values):
    reviewed, proposal = _counted(
        session,
        lambda: create_change_proposal(
            session, tenant, "finance.payout.settle", values, actor_type="human"
        ),
    )
    settled, executed = _counted(
        session, lambda: approve_and_execute_proposal(session, tenant, proposal.id)
    )
    assert json.loads(executed.output)["unmatched_line_ids"] == []
    return reviewed, settled


def test_booking_a_line_costs_a_bounded_number_of_statements(session, business):
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    small = _payout(session, business, clearing, "S342", 15, "PO-342-S")
    large = _payout(session, business, clearing, "L342", 75, "PO-342-L")

    small_review, small_settle = _settle_counted(session, tenant, small)
    large_review, large_settle = _settle_counted(session, tenant, large)

    added = len(large["lines"]) - len(small["lines"])
    assert (large_settle - small_settle) / added <= SETTLE_PER_LINE, (
        small_settle,
        large_settle,
    )
    assert (large_review - small_review) / added <= REVIEW_PER_LINE, (
        small_review,
        large_review,
    )


def _effects(session, tenant, payout_reference, before_sequence):
    """What a settlement wrote, with every generated identity replaced by its role."""
    payout = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant,
            Document.type == "payout",
            Document.number == payout_reference,
        )
    )
    statement = session.get(SourceRecord, (tenant, payout.source_record_id))
    prefix = f"{payout_reference}-"
    documents = {
        document.id: document
        for document in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant, Document.number.startswith(prefix)
            )
        )
    }
    names = {
        document.id: document.number.removeprefix(prefix)
        for document in documents.values()
    }
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant,
                LedgerEntry.document_id.in_(list(documents) + [payout.id]),
            )
        )
    )
    entry_names = {
        entry.id: f"{names.get(entry.document_id, 'payout')}:{entry.account}:{entry.debit_credit}"
        for entry in entries
    }
    allocations = sorted(
        (
            entry_names[row.payment_ledger_entry_id],
            Decimal(row.amount),
        )
        for row in session.scalars(
            select(SettlementAllocation).where(
                SettlementAllocation.tenant_id == tenant,
                SettlementAllocation.payment_ledger_entry_id.in_(list(entry_names)),
            )
        )
    )
    events = sorted(
        session.scalars(
            select(BusinessEvent.event_type).where(
                BusinessEvent.tenant_id == tenant,
                BusinessEvent.sequence > before_sequence,
            )
        )
    )
    returns = session.scalar(
        select(func.count())
        .select_from(PaymentReturn)
        .where(
            PaymentReturn.tenant_id == tenant,
            PaymentReturn.payment_document_id.in_(list(documents)),
        )
    )
    line_sources = session.scalar(
        select(func.count())
        .select_from(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.external_id.startswith(f"{statement.id}/"),
        )
    )
    return {
        "documents": sorted(
            (names[d.id], d.type, Decimal(d.gross_amount), d.party_id)
            for d in documents.values()
        ),
        "entries": sorted(
            (entry_names[e.id], Decimal(e.amount), e.account_id, e.party_id)
            for e in entries
        ),
        "allocations": allocations,
        "events": events,
        "returns": returns,
        "line_sources": line_sources,
    }


def _sequence(session, tenant):
    return session.scalar(
        select(func.coalesce(func.max(BusinessEvent.sequence), 0)).where(
            BusinessEvent.tenant_id == tenant
        )
    )


def _revision(session, tenant):
    return session.scalar(
        select(FinanceState.revision).where(FinanceState.tenant_id == tenant)
    )


def test_the_batch_books_exactly_what_line_by_line_booking_books(
    session, business, monkeypatch
):
    """The same statement shape, once with the batch switched off, once with it."""
    tenant = business.tenant.id
    clearing, _ = _accounts(session, tenant)
    results, costs = [], []
    for prefix, batched in (("ONE", False), ("ALL", True)):
        values = _payout(session, business, clearing, prefix, 12, f"PO-{prefix}")
        # The orders differ only by prefix; name them alike for the comparison.
        sequence, revision = _sequence(session, tenant), _revision(session, tenant)
        with monkeypatch.context() as patch:
            if not batched:
                patch.setattr(core, "_batch_reads", lambda _session: nullcontext())
            costs.append(_settle_counted(session, tenant, values)[1])
        effects = _effects(session, tenant, f"PO-{prefix}", sequence)
        effects["revision_raised"] = _revision(session, tenant) - revision
        results.append(effects)

    line_by_line, batched = results
    assert batched == line_by_line
    # Positive controls: the first run really booked line by line, and the
    # comparison sees what was booked.
    assert costs[0] > 2 * costs[1], costs
    assert line_by_line["allocations"] and line_by_line["returns"] == 1
    assert "settlement.allocated" in line_by_line["events"]
