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
from reality.services import core

ZERO = Decimal(0)
RECEIVABLE_TYPES = {"sales_invoice", "opening_customer_debt"}
PAYABLE_TYPES = {"supplier_invoice", "opening_supplier_debt"}


def _open_documents(
    session: Session, tenant_id: str, party: Party, as_of: datetime
) -> list[dict[str, Any]]:
    rows = core.financial_open_items(session, tenant_id, party_ids={party.id})
    return core.with_invoice_aging(
        rows, core._payment_terms_by_id(session, tenant_id), as_of
    )


def _order_rows(
    session: Session, tenant_id: str, party: Party
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Uninvoiced order lines in the party's currency, unpriced ones, and others."""
    orders = list(
        session.scalars(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.party_id == party.id,
                Document.type == "sales_order",
            )
            .order_by(Document.number, Document.id)
        )
    )
    if not orders:
        return [], [], []
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
    for commitment in session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_line_id.in_([line.id for line in lines]),
            Commitment.type == "customer_delivery",
        )
    ):
        promises.setdefault(commitment.document_line_id, []).append(commitment)
    live = [
        commitment
        for rows in promises.values()
        for commitment in rows
        if commitment.status != "cancelled"
    ]
    terms = core.commitment_terms(session, tenant_id, [c.id for c in live])
    by_id = {order.id: order for order in orders}
    counted, unpriced, other = [], [], []
    for line in lines:
        order = by_id[line.document_id]
        rows = promises.get(line.id)
        # A promise says what is still agreed after revisions and cancellations;
        # a line the company promised nothing for (an unknown item, a service)
        # is agreed as the order states it.
        base = (
            sum((terms[c.id].quantity for c in rows if c.status != "cancelled"), ZERO)
            if rows
            else Decimal(line.quantity)
        )
        invoiced = core._order_line_billing(session, tenant_id, line.id)["invoiced"]
        uninvoiced = max(base - Decimal(invoiced), ZERO)
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
            counted.append({**row, "value": uninvoiced * Decimal(line.unit_price)})
    return counted, unpriced, other


def credit_exposure(
    session: Session,
    tenant_id: str,
    party_id: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """What the company carries for this customer now, part by part."""
    party = core._tenant_record(session, Party, tenant_id, party_id)
    as_of = core.utc_datetime(as_of) or core.now()
    currency = party.default_currency
    receivables, payables, not_counted = [], [], []
    for row in _open_documents(session, tenant_id, party, as_of):
        document = row["document"]
        open_amount = Decimal(row["open"])
        if open_amount <= ZERO:
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
        if document.type not in RECEIVABLE_TYPES | PAYABLE_TYPES:
            continue
        if document.currency != currency:
            not_counted.append(entry)
        elif document.type in RECEIVABLE_TYPES:
            receivables.append(entry)
        else:
            payables.append(entry)
    overdue = [row for row in receivables if row["days_overdue"] > 0]

    from reality.services.finance.credits import available_credit_rows

    credits = []
    items, _ = available_credit_rows(
        session, tenant_id, side="customer", party_id=party.id
    )
    for item in items:
        available = Decimal(item["open"])
        if available <= ZERO:
            continue
        entry = {
            "document_id": item["document_id"],
            "number": item["number"],
            "origin": item["origin"],
            "currency": item["currency"],
            "available": available,
        }
        if item["currency"] != currency:
            not_counted.append(entry)
        else:
            credits.append(entry)

    orders, unpriced, other_orders = _order_rows(session, tenant_id, party)
    not_counted.extend(other_orders)

    open_invoices = sum((row["open"] for row in receivables), ZERO)
    open_orders = sum((row["value"] for row in orders), ZERO)
    available_credits = sum((row["available"] for row in credits), ZERO)
    exposure = open_invoices + open_orders - available_credits
    limit = Decimal(party.credit_limit)
    # Zero records no limit rather than a limit of nothing (spec 078).
    over_limit = limit > ZERO and exposure > limit
    return {
        "party_id": party.id,
        "party": party.name,
        "currency": currency,
        "as_of": as_of,
        "credit_limit": limit,
        "exposure": exposure,
        "over_limit": over_limit,
        "excess": exposure - limit if over_limit else ZERO,
        "open_invoices": {"amount": open_invoices, "rows": receivables},
        "overdue_invoices": {
            "amount": sum((row["open"] for row in overdue), ZERO),
            "rows": overdue,
        },
        "open_orders": {"amount": open_orders, "rows": orders, "unpriced": unpriced},
        "available_credits": {"amount": available_credits, "rows": credits},
        "payables": {
            "amount": sum((row["open"] for row in payables), ZERO),
            "rows": payables,
        },
        "not_counted": not_counted,
    }


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
