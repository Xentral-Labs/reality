"""The credit a company carries for one customer, and holding orders past it (spec 298).

The exposure is derived at read time and never stored: open invoices, plus the
value of open orders not yet invoiced, minus the credits the customer can still
use, in the customer's own currency. Overdue invoices are named among the open
ones; payables to the same party are named but never subtracted, because netting
needs an agreement; amounts in another currency are named as not counted,
because converting would guess.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, Document, DocumentLine, Party
from reality.domain.finance import FEE_RECEIVABLE_TYPES
from reality.services import core

ZERO = Decimal(0)
AMOUNT_SCALE = Decimal("0.0001")
RECEIVABLE_TYPES = {"sales_invoice", "opening_customer_debt", *FEE_RECEIVABLE_TYPES}
PAYABLE_TYPES = {"supplier_invoice", "opening_supplier_debt"}


def _invoiced_quantities(
    session: Session, tenant_id: str, line_ids: list[str]
) -> dict[str, Decimal]:
    """`_order_line_billing(...)["invoiced"]` for many sales-order lines at once.

    Four reads instead of three per line: an invoice line bills its order line
    unless every posting of its invoice was reversed.
    """
    from reality.db.core import LedgerEntry, LedgerReversal

    if not line_ids:
        return {}
    rows = session.execute(
        select(DocumentLine.billed_document_line_id, DocumentLine.quantity, Document.id)
        .join(
            Document,
            (Document.tenant_id == DocumentLine.tenant_id)
            & (Document.id == DocumentLine.document_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.billed_document_line_id.in_(line_ids),
            Document.type == "sales_invoice",
        )
    ).all()
    invoice_ids = {invoice_id for _, _, invoice_id in rows}
    groups: dict[str, set[str]] = {}
    if invoice_ids:
        for document_id, group in session.execute(
            select(LedgerEntry.document_id, LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id.in_(invoice_ids),
            )
        ):
            groups.setdefault(document_id, set()).add(group)
    all_groups = {group for values in groups.values() for group in values}
    reversed_groups = (
        set(
            session.scalars(
                select(LedgerReversal.original_posting_group_id).where(
                    LedgerReversal.tenant_id == tenant_id,
                    LedgerReversal.original_posting_group_id.in_(all_groups),
                )
            )
        )
        if all_groups
        else set()
    )
    invoiced: dict[str, Decimal] = {}
    for line_id, quantity, invoice_id in rows:
        posted = groups.get(invoice_id, set())
        if posted and posted <= reversed_groups:
            continue
        invoiced[line_id] = invoiced.get(line_id, ZERO) + Decimal(quantity)
    return invoiced


def _order_rows(
    session: Session, tenant_id: str, parties: dict[str, Party]
) -> dict[str, tuple[list, list, list]]:
    """Per party: uninvoiced order lines in its currency, unpriced ones, and others.

    The value of a line is its stated amount for the part not yet invoiced —
    never quantity times unit price, which a rebate or the source's own
    rounding makes wrong (Constitution VIII).
    """
    result: dict[str, tuple[list, list, list]] = {
        party_id: ([], [], []) for party_id in parties
    }
    orders = list(
        session.scalars(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.party_id.in_(list(parties)),
                Document.type == "sales_order",
            )
            .order_by(Document.number, Document.id)
        )
    )
    if not orders:
        return result
    lines = list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id.in_([order.id for order in orders]),
            )
            .order_by(DocumentLine.id)
        )
    )
    promises: dict[str, list[Commitment]] = {}
    by_order: dict[str, list[Commitment]] = {}
    for commitment in session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_id.in_([order.id for order in orders]),
            Commitment.type == "customer_delivery",
        )
    ):
        by_order.setdefault(commitment.document_id, []).append(commitment)
        if commitment.document_line_id:
            promises.setdefault(commitment.document_line_id, []).append(commitment)
    live = [
        commitment
        for rows in by_order.values()
        for commitment in rows
        if commitment.status != "cancelled"
    ]
    terms = core.commitment_terms(session, tenant_id, [c.id for c in live])
    invoiced = _invoiced_quantities(session, tenant_id, [line.id for line in lines])
    by_id = {order.id: order for order in orders}
    for line in lines:
        order = by_id[line.document_id]
        party = parties[order.party_id]
        counted, unpriced, other = result[party.id]
        rows = promises.get(line.id)
        order_promises = by_order.get(order.id, [])
        if rows:
            # A promise says what is still agreed after revisions and cancellations.
            base = sum(
                (terms[c.id].quantity for c in rows if c.status != "cancelled"), ZERO
            )
        elif order_promises and all(c.status == "cancelled" for c in order_promises):
            # A line the company promised nothing for (a service, a charge, an
            # unknown item) goes with its order: a cancelled order owes nothing.
            base = ZERO
        else:
            base = Decimal(line.quantity)
        uninvoiced = max(base - invoiced.get(line.id, ZERO), ZERO)
        if uninvoiced <= ZERO:
            continue
        row = {
            "document_id": order.id,
            "number": order.number,
            "document_line_id": line.id,
            "currency": order.currency,
            "uninvoiced_quantity": uninvoiced,
            "unit_price": Decimal(line.unit_price)
            if line.unit_price is not None
            else None,
        }
        if order.currency != party.default_currency:
            other.append(row)
        elif line.unit_price is None:
            unpriced.append({**row, "value": ZERO})
        else:
            stated = Decimal(line.gross_amount)
            value = (
                (stated * uninvoiced / Decimal(line.quantity)).quantize(AMOUNT_SCALE)
                if Decimal(line.quantity) > ZERO
                else ZERO
            )
            counted.append({**row, "value": value})
    return result


def credit_exposures(
    session: Session,
    tenant_id: str,
    party_ids: list[str],
    *,
    as_of: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """What the company carries for each of these customers, part by part."""
    parties = {
        party_id: core._tenant_record(session, Party, tenant_id, party_id)
        for party_id in dict.fromkeys(party_ids)
    }
    as_of = core.utc_datetime(as_of) or core.now()
    receivables: dict[str, list] = {pid: [] for pid in parties}
    payables: dict[str, list] = {pid: [] for pid in parties}
    not_counted: dict[str, list] = {pid: [] for pid in parties}
    if not parties:
        return {}
    rows = core.financial_open_items(session, tenant_id, party_ids=set(parties))
    for row in core.with_invoice_aging(
        rows, core._payment_terms_by_id(session, tenant_id), as_of
    ):
        document = row["document"]
        party = parties.get(document.party_id)
        open_amount = Decimal(row["open"])
        if party is None or open_amount <= ZERO:
            continue
        if document.type not in RECEIVABLE_TYPES | PAYABLE_TYPES:
            continue
        entry = {
            "document_id": document.id,
            "number": document.number,
            "type": document.type,
            "currency": document.currency,
            "open": open_amount,
            "due_date": row.get("due_date"),
            "days_overdue": row.get("days_overdue") or 0,
        }
        if document.currency != party.default_currency:
            not_counted[party.id].append(entry)
        elif document.type in RECEIVABLE_TYPES:
            receivables[party.id].append(entry)
        else:
            payables[party.id].append(entry)

    from reality.services.finance.credits import available_credit_rows

    credits: dict[str, list] = {pid: [] for pid in parties}
    items, _ = available_credit_rows(
        session, tenant_id, side="customer", party_ids=set(parties)
    )
    for item in items:
        party = parties.get(item["party_id"])
        available = Decimal(item["open"])
        if party is None or available <= ZERO:
            continue
        entry = {
            "document_id": item["document_id"],
            "number": item["number"],
            "origin": item["origin"],
            "currency": item["currency"],
            "available": available,
        }
        if item["currency"] != party.default_currency:
            not_counted[party.id].append(entry)
        else:
            credits[party.id].append(entry)

    from reality.services.down_payments import held_down_payments

    for row in held_down_payments(session, tenant_id, set(parties)):
        party = parties[row["party_id"]]
        entry = {
            "document_id": row["document_id"],
            "number": row["number"],
            "origin": "down_payment",
            "currency": row["currency"],
            "available": row["offsettable"],
        }
        if row["currency"] != party.default_currency:
            not_counted[party.id].append(entry)
        else:
            credits[party.id].append(entry)

    orders = _order_rows(session, tenant_id, parties)
    result = {}
    for party_id, party in parties.items():
        counted, unpriced, other = orders[party_id]
        not_counted[party_id].extend(other)
        overdue = [row for row in receivables[party_id] if row["days_overdue"] > 0]
        open_invoices = sum((row["open"] for row in receivables[party_id]), ZERO)
        open_orders = sum((row["value"] for row in counted), ZERO)
        available_credits = sum((row["available"] for row in credits[party_id]), ZERO)
        exposure = open_invoices + open_orders - available_credits
        limit = Decimal(party.credit_limit)
        # Zero records no limit rather than a limit of nothing (spec 078).
        over_limit = limit > ZERO and exposure > limit
        result[party_id] = {
            "party_id": party.id,
            "party": party.name,
            "currency": party.default_currency,
            "as_of": as_of,
            "credit_limit": limit,
            "exposure": exposure,
            "over_limit": over_limit,
            "excess": exposure - limit if over_limit else ZERO,
            "open_invoices": {"amount": open_invoices, "rows": receivables[party_id]},
            "overdue_invoices": {
                "amount": sum((row["open"] for row in overdue), ZERO),
                "rows": overdue,
            },
            "open_orders": {
                "amount": open_orders,
                "rows": counted,
                "unpriced": unpriced,
            },
            "available_credits": {
                "amount": available_credits,
                "rows": credits[party_id],
            },
            "payables": {
                "amount": sum((row["open"] for row in payables[party_id]), ZERO),
                "rows": payables[party_id],
            },
            "not_counted": not_counted[party_id],
        }
    return result


def credit_exposure(
    session: Session,
    tenant_id: str,
    party_id: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """What the company carries for this customer now, part by part."""
    return credit_exposures(session, tenant_id, [party_id], as_of=as_of)[party_id]


def _money(value: Decimal) -> str:
    return f"{Decimal(value).quantize(Decimal('0.01')):f}"


def credit_hold_note(exposure: dict[str, Any], order_value: Decimal) -> str:
    """The facts a credit hold was placed on, in one line a clerk can read."""
    currency = exposure["currency"]
    parts = [
        (
            f"Credit limit {_money(exposure['credit_limit'])} {currency} exceeded by "
            f"{_money(exposure['excess'])}: exposure {_money(exposure['exposure'])}"
            f" = open invoices {_money(exposure['open_invoices']['amount'])}"
        ),
    ]
    overdue = exposure["overdue_invoices"]["rows"]
    if overdue:
        parts[0] += (
            " (overdue "
            + ", ".join(f"{row['number']} {_money(row['open'])}" for row in overdue)
            + ")"
        )
    parts[0] += (
        f" + open orders {_money(exposure['open_orders']['amount'])}"
        f" (this order {_money(order_value)})"
        f" - credits {_money(exposure['available_credits']['amount'])}"
    )
    if exposure["payables"]["rows"]:
        parts.append(
            f"payables {_money(exposure['payables']['amount'])} {currency} named, "
            "not netted"
        )
    if exposure["not_counted"]:
        parts.append(
            "not counted (other currency): "
            + ", ".join(str(row["number"]) for row in exposure["not_counted"])
        )
    return "; ".join(parts)


def _json_exposure(exposure: dict[str, Any]) -> dict[str, Any]:
    def plain(value: Any) -> Any:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: plain(item) for key, item in value.items()}
        if isinstance(value, list):
            return [plain(item) for item in value]
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    return plain(exposure)


def active_credit_holds(
    session: Session, tenant_id: str, commitment_ids: list[str]
) -> list[Any]:
    from reality.db.core import CommitmentHold

    if not commitment_ids:
        return []
    return list(
        session.scalars(
            select(CommitmentHold)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id.in_(commitment_ids),
                CommitmentHold.reason_code == "credit_check",
                CommitmentHold.created_by == "credit_limit",
                CommitmentHold.released_at.is_(None),
            )
            .order_by(CommitmentHold.created_at, CommitmentHold.id)
        )
    )


def place_credit_holds(
    session: Session,
    tenant_id: str,
    commitments: list[Commitment],
    exposure: dict[str, Any],
    order_value: Decimal,
    *,
    action_id: str | None = None,
) -> list[Any]:
    """One credit hold per promise that has none, beside any other hold."""
    from reality.db.core import CommitmentHold

    held = {
        hold.commitment_id
        for hold in active_credit_holds(session, tenant_id, [c.id for c in commitments])
    }
    note = credit_hold_note(exposure, order_value)
    facts = {**_json_exposure(exposure), "order_value": str(order_value)}
    placed = []
    for commitment in commitments:
        if commitment.id in held or commitment.status == "cancelled":
            continue
        hold = CommitmentHold(
            id=core.uid("hld"),
            tenant_id=tenant_id,
            commitment_id=commitment.id,
            reason_code="credit_check",
            note=note,
            created_by="credit_limit",
        )
        session.add(hold)
        core.emit_business_event(
            session,
            tenant_id,
            "commitment.held",
            "commitment",
            commitment.id,
            {"hold_id": hold.id, "reason_code": "credit_check", "credit": facts},
            action_id=action_id,
            correlation_id=action_id,
        )
        placed.append(hold)
    session.flush()
    return placed


def hold_if_over_credit_limit(
    session: Session,
    tenant_id: str,
    order: Document,
    commitments: list[Commitment],
    *,
    action_id: str | None = None,
) -> list[Any]:
    """Hold a new sales order that would take its customer past the credit limit.

    Called by every path that records a sales order, inside its transaction. It
    never refuses the order: the order is recorded as stated and waits for a
    person, who sees why (spec 298 FR-002, FR-003).
    """
    if order.type != "sales_order" or not order.party_id:
        return []
    party = core._tenant_record(session, Party, tenant_id, order.party_id)
    if Decimal(party.credit_limit) <= ZERO or order.currency != party.default_currency:
        return []
    promises = [c for c in commitments if c.type == "customer_delivery"]
    if not promises:
        return []
    session.flush()
    exposure = credit_exposure(session, tenant_id, party.id)
    order_value = sum(
        (
            row["value"]
            for row in exposure["open_orders"]["rows"]
            if row["document_id"] == order.id
        ),
        ZERO,
    )
    if order_value <= ZERO or not exposure["over_limit"]:
        return []
    return place_credit_holds(
        session, tenant_id, promises, exposure, order_value, action_id=action_id
    )
