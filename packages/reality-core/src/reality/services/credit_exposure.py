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
    """
    BUSINESS PURPOSE:
    Find how much of each sales-order line is already billed, using invoice-line references and reversal evidence.

    BUSINESS RULE credit_exposure._invoiced_quantities.guard-37:
    IF no order lines were supplied:
        Return no billed quantities.

    BUSINESS RULE credit_exposure._invoiced_quantities.guard-78:
    IF an invoice has posting groups AND every one of them was reversed:
        Do not count its billed quantity.

    BUSINESS RULE credit_exposure.invoiced_quantity:
    Add each remaining invoice line's quantity to the sales-order line it explicitly bills. Do not infer links from document numbers.
    """
    from reality.db.core import LedgerEntry, LedgerReversal

    # reality-rule: credit_exposure._invoiced_quantities.guard-37
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
    # reality-rule: credit_exposure._invoiced_quantities.guard-54
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
        # reality-rule: credit_exposure._invoiced_quantities.guard-78
        if posted and posted <= reversed_groups:
            continue
        # reality-rule: credit_exposure.invoiced_quantity
        invoiced[line_id] = invoiced.get(line_id, ZERO) + Decimal(quantity)
    return invoiced


def _order_rows(
    session: Session, tenant_id: str, parties: dict[str, Party]
) -> dict[str, tuple[list, list, list]]:
    """
    BUSINESS PURPOSE:
    Separate uninvoiced sales-order lines into counted values, unpriced lines and other currencies. Value uses the source-stated line amount, not quantity multiplied by price.

    BUSINESS RULE credit_exposure._order_rows.guard-107:
    IF the current company has no sales orders for these customers:
        Return empty order contributions.

    BUSINESS RULE credit_exposure._order_rows.guard-146:
    IF a line has delivery commitments:
        Use the sum of the currently agreed quantities of its non-cancelled commitments as the quantity still promised.

    BUSINESS RULE credit_exposure._order_rows.guard-151:
    IF a line has no own delivery commitments AND all commitments on its order are cancelled:
        Use zero quantity for that line.
    ELSE:
        Use the line's stated quantity.

    BUSINESS RULE credit_exposure.uninvoiced_quantity:
    Subtract the quantity already billed from the applicable promised or stated quantity. Never use a negative remaining quantity.

    BUSINESS RULE credit_exposure._order_rows.guard-158:
    IF no uninvoiced quantity remains:
        Do not include this line.

    BUSINESS RULE credit_exposure._order_rows.guard-170:
    IF the order's currency differs from the customer's currency:
        Name the line as not counted. Do not convert it.

    BUSINESS RULE credit_exposure._order_rows.guard-172:
    IF a same-currency line has no stated unit price:
        Name it as unpriced and assign no counted value.

    BUSINESS RULE credit_exposure.order_line_value:
    For a positive stated line quantity, value the remaining part as stated gross line amount * uninvoiced quantity / stated line quantity, rounded to four decimal places. Otherwise use zero.
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
    # reality-rule: credit_exposure._order_rows.guard-107
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
        # reality-rule: credit_exposure._order_rows.guard-129
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
        # reality-rule: credit_exposure._order_rows.guard-146
        if rows:
            # A promise says what is still agreed after revisions and cancellations.
            base = sum(
                (terms[c.id].quantity for c in rows if c.status != "cancelled"), ZERO
            )
        # reality-rule: credit_exposure._order_rows.guard-151
        elif order_promises and all(c.status == "cancelled" for c in order_promises):
            # A line the company promised nothing for (a service, a charge, an
            # unknown item) goes with its order: a cancelled order owes nothing.
            base = ZERO
        else:
            base = Decimal(line.quantity)
        # reality-rule: credit_exposure.uninvoiced_quantity
        uninvoiced = max(base - invoiced.get(line.id, ZERO), ZERO)
        # reality-rule: credit_exposure._order_rows.guard-158
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
        # reality-rule: credit_exposure._order_rows.guard-170
        if order.currency != party.default_currency:
            other.append(row)
        # reality-rule: credit_exposure._order_rows.guard-172
        elif line.unit_price is None:
            unpriced.append({**row, "value": ZERO})
        else:
            stated = Decimal(line.gross_amount)
            # reality-rule: credit_exposure.order_line_value
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
    """
    BUSINESS PURPOSE:
    Read each customer's credit exposure, limit and contributing records in the customer's currency. Supplier payables and excluded currencies remain visible separately.

    BUSINESS RULE credit_exposure.merged_customers:
    Include merged customer identities under their surviving requested customer.
    If a merged identity was explicitly requested separately, keep that requested identity separate.

    BUSINESS RULE credit_exposure.credit_exposures.guard-201:
    IF no customers were requested:
        Return no results.

    BUSINESS RULE credit_exposure.credit_exposures.guard-210:
    IF an open item has no requested customer or its remaining amount is zero or negative:
        Exclude it from this calculation.

    BUSINESS RULE credit_exposure.credit_exposures.guard-212:
    IF the document is neither a supported receivable nor a supported payable:
        Exclude it from the invoice amounts.

    BUSINESS RULE credit_exposure.credit_exposures.guard-223:
    IF the open item's currency differs from the customer's default currency:
        Name the item as not counted. Do not convert it.

    BUSINESS RULE credit_exposure.credit_exposures.guard-225:
    IF a same-currency item is a receivable:
        Include it among open customer invoices.
    ELSE:
        Name it as a supplier payable. Do not subtract payables from credit exposure.

    BUSINESS RULE credit_exposure.credit_exposures.guard-239:
    IF a customer credit has no requested customer or no positive available amount:
        Exclude it from available credits.

    BUSINESS RULE credit_exposure.credit_exposures.guard-248:
    IF an available credit uses a different currency:
        Name it as not counted.
    ELSE:
        Include it in available customer credits.

    BUSINESS RULE credit_exposure.credit_exposures.guard-264:
    IF an offsettable down payment uses a different currency:
        Name it as not counted.
    ELSE:
        Include its offsettable amount in available customer credits.

    BUSINESS RULE credit_exposure.overdue:
    Name open customer invoices whose days overdue are greater than zero. They remain part of open invoices and are not counted again.

    BUSINESS RULE credit_exposure.invoice_total:
    Add the remaining amounts of the customer's included receivables.

    BUSINESS RULE credit_exposure.order_total:
    Add the values of included order lines not yet invoiced.

    BUSINESS RULE credit_exposure.credit_total:
    Add the available amounts of included customer credits and offsettable down payments.

    BUSINESS RULE credit_exposure.amount:
    Calculate credit exposure = open invoices + uninvoiced orders - available credits.

    BUSINESS RULE credit_exposure.over_limit:
    IF the stated credit limit is greater than zero AND credit exposure is greater than that limit:
        Report that the limit is exceeded.
    ELSE:
        Report no limit breach. Equality is allowed; a zero limit records no limit.
    """
    parties = {
        party_id: core._tenant_record(session, Party, tenant_id, party_id)
        for party_id in dict.fromkeys(party_ids)
    }
    # Spec 339: the partners merged into a customer count under it.
    from reality.services.party_merges import merged_members

    # reality-rule: credit_exposure.merged_customers
    owner = {
        duplicate: survivor
        for duplicate, survivor in merged_members(session, tenant_id, parties).items()
        if duplicate not in parties
    }
    members = dict(parties)
    members.update(
        {duplicate: parties[survivor] for duplicate, survivor in owner.items()}
    )
    as_of = core.utc_datetime(as_of) or core.now()
    receivables: dict[str, list] = {pid: [] for pid in parties}
    payables: dict[str, list] = {pid: [] for pid in parties}
    not_counted: dict[str, list] = {pid: [] for pid in parties}
    # reality-rule: credit_exposure.credit_exposures.guard-201
    if not parties:
        return {}
    rows = core.financial_open_items(session, tenant_id, party_ids=set(members))
    for row in core.with_invoice_aging(
        rows,
        core._payment_terms_by_id(session, tenant_id),
        core._company_day(session, tenant_id, as_of),
    ):
        document = row["document"]
        party = members.get(document.party_id)
        open_amount = Decimal(row["open"])
        # reality-rule: credit_exposure.credit_exposures.guard-210
        if party is None or open_amount <= ZERO:
            continue
        # reality-rule: credit_exposure.credit_exposures.guard-212
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
        # reality-rule: credit_exposure.credit_exposures.guard-223
        if document.currency != party.default_currency:
            not_counted[party.id].append(entry)
        # reality-rule: credit_exposure.credit_exposures.guard-225
        elif document.type in RECEIVABLE_TYPES:
            receivables[party.id].append(entry)
        else:
            payables[party.id].append(entry)

    from reality.services.finance.credits import available_credit_rows

    credits: dict[str, list] = {pid: [] for pid in parties}
    items, _ = available_credit_rows(
        session, tenant_id, side="customer", party_ids=set(members)
    )
    for item in items:
        party = members.get(item["party_id"])
        available = Decimal(item["open"])
        # reality-rule: credit_exposure.credit_exposures.guard-239
        if party is None or available <= ZERO:
            continue
        entry = {
            "document_id": item["document_id"],
            "number": item["number"],
            "origin": item["origin"],
            "currency": item["currency"],
            "available": available,
        }
        # reality-rule: credit_exposure.credit_exposures.guard-248
        if item["currency"] != party.default_currency:
            not_counted[party.id].append(entry)
        else:
            credits[party.id].append(entry)

    from reality.services.down_payments import held_down_payments

    for row in held_down_payments(session, tenant_id, set(members)):
        party = members[row["party_id"]]
        entry = {
            "document_id": row["document_id"],
            "number": row["number"],
            "origin": "down_payment",
            "currency": row["currency"],
            "available": row["offsettable"],
        }
        # reality-rule: credit_exposure.credit_exposures.guard-264
        if row["currency"] != party.default_currency:
            not_counted[party.id].append(entry)
        else:
            credits[party.id].append(entry)

    orders = _order_rows(session, tenant_id, members)
    result = {}
    for party_id, party in parties.items():
        counted, unpriced, other = orders[party_id]
        not_counted[party_id].extend(other)
        # reality-rule: credit_exposure.overdue
        overdue = [row for row in receivables[party_id] if row["days_overdue"] > 0]
        # reality-rule: credit_exposure.invoice_total
        open_invoices = sum((row["open"] for row in receivables[party_id]), ZERO)
        # reality-rule: credit_exposure.order_total
        open_orders = sum((row["value"] for row in counted), ZERO)
        # reality-rule: credit_exposure.credit_total
        available_credits = sum((row["available"] for row in credits[party_id]), ZERO)
        # reality-rule: credit_exposure.amount
        exposure = open_invoices + open_orders - available_credits
        limit = Decimal(party.credit_limit)
        # Zero records no limit rather than a limit of nothing (spec 078).
        # reality-rule: credit_exposure.over_limit
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
    """
    BUSINESS PURPOSE:
    Read this customer's credit exposure in the customer's currency, with its contributing amounts and exclusions.

    BUSINESS RULE credit_exposure.single_customer:
    Read the shared multi-customer calculation for this customer and return that customer's result. The read does not place or release a credit hold.
    """
    # reality-rule: credit_exposure.single_customer
    return credit_exposures(session, tenant_id, [party_id], as_of=as_of)[party_id]


def _money(value: Decimal) -> str:
    return f"{Decimal(value).quantize(Decimal('0.01')):f}"


def credit_hold_note(exposure: dict[str, Any], order_value: Decimal) -> str:
    """
    BUSINESS PURPOSE:
    Describe the amounts on which an existing credit-hold explanation is based. Formatting this note does not create a hold.

    BUSINESS RULE credit_exposure.credit_hold_note.guard-340:
    IF overdue invoices are present:
        Name their invoice numbers and remaining amounts beside the open invoice total.

    BUSINESS RULE credit_exposure.credit_hold_note.guard-351:
    IF supplier payables are present:
        Name their total separately and state that they are not netted.

    BUSINESS RULE credit_exposure.credit_hold_note.guard-356:
    IF other-currency records were excluded:
        Name their document numbers as not counted.
    """
    currency = exposure["currency"]
    parts = [
        (
            f"Credit limit {_money(exposure['credit_limit'])} {currency} exceeded by "
            f"{_money(exposure['excess'])}: exposure {_money(exposure['exposure'])}"
            f" = open invoices {_money(exposure['open_invoices']['amount'])}"
        ),
    ]
    overdue = exposure["overdue_invoices"]["rows"]
    # reality-rule: credit_exposure.credit_hold_note.guard-340
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
    # reality-rule: credit_exposure.credit_hold_note.guard-351
    if exposure["payables"]["rows"]:
        parts.append(
            f"payables {_money(exposure['payables']['amount'])} {currency} named, "
            "not netted"
        )
    # reality-rule: credit_exposure.credit_hold_note.guard-356
    if exposure["not_counted"]:
        parts.append(
            "not counted (other currency): "
            + ", ".join(str(row["number"]) for row in exposure["not_counted"])
        )
    return "; ".join(parts)


def _json_exposure(exposure: dict[str, Any]) -> dict[str, Any]:
    def plain(value: Any) -> Any:
        # reality-rule: credit_exposure.plain.guard-366
        if isinstance(value, Decimal):
            return str(value)
        # reality-rule: credit_exposure.plain.guard-368
        if isinstance(value, datetime):
            return value.isoformat()
        # reality-rule: credit_exposure.plain.guard-370
        if isinstance(value, dict):
            return {key: plain(item) for key, item in value.items()}
        # reality-rule: credit_exposure.plain.guard-372
        if isinstance(value, list):
            return [plain(item) for item in value]
        # reality-rule: credit_exposure.plain.guard-374
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    return plain(exposure)


def active_credit_holds(
    session: Session, tenant_id: str, commitment_ids: list[str]
) -> list[Any]:
    from reality.db.core import CommitmentHold

    # reality-rule: credit_exposure.active_credit_holds.guard-386
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
    return _place_holds(
        session,
        tenant_id,
        commitments,
        credit_hold_note(exposure, order_value),
        {**_json_exposure(exposure), "order_value": str(order_value)},
        action_id=action_id,
    )


def credit_hold_currency_note(exposure: dict[str, Any], order_currency: str) -> str:
    """Why an order in another currency than the limit's waits for a person."""
    currency = exposure["currency"]
    return (
        f"Credit limit {_money(exposure['credit_limit'])} {currency} is stated in "
        f"{currency}; this order is in {order_currency}, which Reality does not "
        f"convert, so a person decides (exposure in {currency} "
        f"{_money(exposure['exposure'])})"
    )


def _place_holds(
    session: Session,
    tenant_id: str,
    commitments: list[Commitment],
    note: str,
    facts: dict[str, Any],
    *,
    action_id: str | None = None,
) -> list[Any]:
    from reality.db.core import CommitmentHold

    held = {
        hold.commitment_id
        for hold in active_credit_holds(session, tenant_id, [c.id for c in commitments])
    }
    placed = []
    for commitment in commitments:
        # reality-rule: credit_exposure.place_credit_holds.guard-423
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
    person, who sees why (spec 298 FR-002, FR-003). An order in another currency
    than the limit's cannot be counted without converting, so it waits for a
    person too rather than passing unchecked (spec 341).
    """
    # reality-rule: credit_exposure.hold_if_over_credit_limit.guard-463
    if order.type != "sales_order" or not order.party_id:
        return []
    party = core._tenant_record(session, Party, tenant_id, order.party_id)
    if Decimal(party.credit_limit) <= ZERO:
        return []
    promises = [c for c in commitments if c.type == "customer_delivery"]
    # reality-rule: credit_exposure.hold_if_over_credit_limit.guard-469
    if not promises:
        return []
    session.flush()
    exposure = credit_exposure(session, tenant_id, party.id)
    if order.currency != party.default_currency:
        # Only an order with something still to invoice adds credit.
        if not any(row["document_id"] == order.id for row in exposure["not_counted"]):
            return []
        return _place_holds(
            session,
            tenant_id,
            promises,
            credit_hold_currency_note(exposure, order.currency),
            {
                **_json_exposure(exposure),
                "order_currency": order.currency,
                "not_counted_order_id": order.id,
            },
            action_id=action_id,
        )
    order_value = sum(
        (
            row["value"]
            for row in exposure["open_orders"]["rows"]
            if row["document_id"] == order.id
        ),
        ZERO,
    )
    # reality-rule: credit_exposure.hold_if_over_credit_limit.guard-481
    if order_value <= ZERO or not exposure["over_limit"]:
        return []
    return place_credit_holds(
        session, tenant_id, promises, exposure, order_value, action_id=action_id
    )
