"""Marketplace and payment-provider payouts (spec 336).

A provider pays one net amount for many orders, minus refunds, chargebacks and
its fees. The statement it states is kept as a source record, and so is each of
its lines; every line is booked through the existing primitives on a cash
account the person names for the provider:

* a charge is a customer payment, allocated to the one posted invoice its
  references name, or recorded for the customer when they name no single one;
* a refund is a customer refund, allocated to the order's open credit note;
* a chargeback returns the order's payment held on that account (spec 297);
* a fee is payment-fee expense.

The deposit moves the stated net payout from the provider's account to the bank.
A line whose references lead nowhere stays unbooked and is reported; settling
the same statement again books only such lines. Nothing here recomputes what
the provider stated: a statement whose lines do not add up is refused.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, time
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    LedgerReversal,
    Party,
    PaymentReturn,
    SettlementAllocation,
    ShipmentPackage,
    SourceRecord,
)
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.finance.accounts import lock_finance, resolve_account
from reality.services.payment_intake import (
    Reference,
    _invoices_billing,
    _orders_by,
    _orders_shipped_under,
    _posted_control,
    resolve_references,
)

SOURCE_SYSTEM = "payout_statement"
STATEMENT_TYPE = "payout_statement"
LINE_TYPE = "payout_line"
#: Booked in this order, so a chargeback finds the charge of the same statement.
KINDS = ("charge", "refund", "chargeback", "fee")
SIGN = {"charge": 1, "refund": -1, "chargeback": -1, "fee": -1}
MAX_LINES = 2000
AMOUNT_EXPONENT = -4


def _amount(value: Any) -> Decimal | None:
    """A positive amount with at most four decimals, or None."""
    try:
        amount = Decimal(str(value))
    except (TypeError, ValueError, DecimalInvalid):
        return None
    if (
        not amount.is_finite()
        or amount <= 0
        or amount.as_tuple().exponent < AMOUNT_EXPONENT
    ):
        return None
    return amount


def _text(amount: Decimal) -> str:
    """Normalized text, so the review and the event state the same number."""
    return format(amount.normalize(), "f")


def _statement(values: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    """The stated payout, checked and normalized; nothing is looked up yet."""
    reference = str(values.get("payout_reference") or "").strip()
    if not reference:
        raise core.InvalidOperation(code="payout_reference_missing")
    try:
        paid_on = date.fromisoformat(str(values.get("paid_on")))
    except ValueError as error:
        raise core.InvalidOperation(code="payout_paid_on_invalid") from error
    if paid_on > (today or core.now().date()):
        raise core.InvalidOperation(code="payout_paid_on_future")
    currency = str(values.get("currency") or "")
    if len(currency) != 3 or not currency.isupper():
        raise core.InvalidOperation(code="payout_currency_invalid")
    amount = _amount(values.get("amount"))
    if amount is None:
        raise core.InvalidOperation(code="payout_amount_invalid")
    lines = values.get("lines") or []
    if not lines or len(lines) > MAX_LINES:
        raise core.InvalidOperation(code="payout_lines_invalid")
    seen: set[str] = set()
    normalized = []
    for line in lines:
        line_id = str(line.get("line_id") or "").strip()
        if not line_id or line_id in seen:
            raise core.InvalidOperation(code="payout_line_duplicate")
        seen.add(line_id)
        kind = line.get("kind")
        if kind not in KINDS:
            raise core.InvalidOperation(code="payout_line_kind_invalid")
        try:
            references = [
                Reference.model_validate(item).model_dump()
                for item in line.get("references") or []
            ]
        except ValidationError as error:
            raise core.InvalidOperation(code="payout_line_reference_invalid") from error
        if kind != "fee" and not references:
            raise core.InvalidOperation(code="payout_line_reference_missing")
        line_amount = _amount(line.get("amount"))
        if line_amount is None:
            raise core.InvalidOperation(code="payout_line_amount_invalid")
        normalized.append(
            {
                "line_id": line_id,
                "kind": kind,
                "amount": _text(line_amount),
                "references": references,
                "reason": str(line.get("reason") or "").strip(),
            }
        )
    lines_total = sum(
        (SIGN[line["kind"]] * Decimal(line["amount"]) for line in normalized),
        Decimal(0),
    )
    if lines_total != amount:
        raise core.InvalidOperation(
            code="payout_total_mismatch",
            values={"stated": _text(amount), "lines": _text(lines_total)},
        )
    return {
        "provider_party_id": str(values.get("provider_party_id") or ""),
        "payout_reference": reference,
        "paid_on": paid_on.isoformat(),
        "currency": currency,
        "amount": _text(amount),
        "clearing_account_id": str(values.get("clearing_account_id") or ""),
        "bank_account_id": values.get("bank_account_id") or None,
        "lines": normalized,
    }


def _accounts(session: Session, tenant_id: str, statement: dict[str, Any]) -> None:
    """The provider's account and the bank are two distinct active cash accounts."""
    if not statement["clearing_account_id"]:
        raise core.InvalidOperation(code="payout_clearing_account_invalid")
    try:
        clearing = resolve_account(
            session, tenant_id, "cash", statement["clearing_account_id"]
        )
    except (core.InvalidOperation, core.NotFound) as error:
        raise core.InvalidOperation(code="payout_clearing_account_invalid") from error
    bank = resolve_account(session, tenant_id, "cash", statement["bank_account_id"])
    if bank.id == clearing.id:
        raise core.InvalidOperation(code="payout_clearing_is_bank")
    statement["bank_account_id"] = bank.id
    if any(line["kind"] == "fee" for line in statement["lines"]):
        resolve_account(session, tenant_id, "payment_fee_expense")


def _external_id(statement: dict[str, Any]) -> str:
    return f"{statement['provider_party_id']}/{statement['payout_reference']}"


def _held_statement(
    session: Session, tenant_id: str, statement: dict[str, Any]
) -> SourceRecord | None:
    """The statement already settled under this reference, if any; refused if changed."""
    held = session.scalar(
        select(SourceRecord)
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == SOURCE_SYSTEM,
            SourceRecord.source_type == STATEMENT_TYPE,
            SourceRecord.external_id == _external_id(statement),
        )
        .order_by(SourceRecord.version.desc())
        .limit(1)
    )
    if held is not None and held.payload_hash != core.canonical_payload_hash(statement):
        raise core.InvalidOperation(code="payout_statement_changed")
    return held


def _line_external_id(statement_source_id: str, line_id: str) -> str:
    return f"{statement_source_id}/{line_id}"


def _line_sources(
    session: Session, tenant_id: str, statement_source: SourceRecord | None
) -> dict[str, SourceRecord]:
    """Each stated line's own source record, by line id."""
    if statement_source is None:
        return {}
    prefix = f"{statement_source.id}/"
    return {
        source.external_id.removeprefix(prefix): source
        for source in session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.source_type == LINE_TYPE,
                SourceRecord.external_id.in_(
                    [
                        _line_external_id(statement_source.id, line["line_id"])
                        for line in json.loads(statement_source.payload)["lines"]
                    ]
                ),
            )
        )
    }


def _bookings(
    session: Session, tenant_id: str, source_ids: set[str]
) -> dict[str, dict[str, str]]:
    """What carries each line source: a document or a payment return."""
    if not source_ids:
        return {}
    booked: dict[str, dict[str, str]] = {}
    for source_id, document_id, document_type, number in session.execute(
        select(
            Document.source_record_id, Document.id, Document.type, Document.number
        ).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id.in_(source_ids),
        )
    ):
        booked[source_id] = {
            "document_id": document_id,
            "document_type": document_type,
            "number": number,
        }
    for source_id, return_id, payment_id in session.execute(
        select(
            PaymentReturn.source_record_id,
            PaymentReturn.id,
            PaymentReturn.payment_document_id,
        ).where(
            PaymentReturn.tenant_id == tenant_id,
            PaymentReturn.source_record_id.in_(source_ids),
        )
    ):
        booked[source_id] = {
            "payment_return_id": return_id,
            "payment_document_id": payment_id,
        }
    return booked


# ---------------------------------------------------------------------------
# Resolution


def _customers(
    session: Session, tenant_id: str, references: list[Reference]
) -> set[str]:
    """The customers the stated references name, across all customers."""
    memo = core._batch_memo(session)
    parties: set[str] = set()
    for reference in references:
        key = ("customers", tenant_id, reference.type, reference.value)
        if memo is not None and key in memo:
            parties |= memo[key]
        else:
            parties |= _customers_of(session, tenant_id, reference)
    parties.discard(None)
    return parties


def _customers_of(session: Session, tenant_id: str, reference: Reference) -> set[str]:
    if reference.type == "invoice_number":
        return set(
            session.scalars(
                select(Document.party_id).where(
                    Document.tenant_id == tenant_id,
                    Document.type == "sales_invoice",
                    Document.number == reference.value,
                )
            )
        )
    if reference.type in {"shop_order_number", "customer_reference"}:
        column = (
            Document.number
            if reference.type == "shop_order_number"
            else Document.customer_reference
        )
        return set(
            session.scalars(
                select(Document.party_id).where(
                    Document.tenant_id == tenant_id,
                    Document.type == "sales_order",
                    column == reference.value,
                )
            )
        )
    if reference.type == "shop_id":
        return set(
            session.scalars(
                select(Document.party_id)
                .join(
                    SourceRecord,
                    (SourceRecord.tenant_id == Document.tenant_id)
                    & (SourceRecord.id == Document.source_record_id),
                )
                .where(
                    Document.tenant_id == tenant_id,
                    Document.type == "sales_order",
                    SourceRecord.source_type == "order",
                    SourceRecord.external_id == reference.value,
                )
            )
        )
    if reference.type == "tracking_number":
        return {
            order.party_id
            for order in _orders_shipped_under(
                session, tenant_id, reference.value, None
            )
        }
    if reference.type == "customer_number":
        return set(
            session.scalars(
                select(Party.id).where(
                    Party.tenant_id == tenant_id,
                    Party.accounting_code == reference.value,
                )
            )
        )
    return set()


def _orders_named(
    session: Session, tenant_id: str, party_id: str, references: list[Reference]
) -> list[Document]:
    """The customer's sales orders the references name, for credit notes and shipments."""
    orders: dict[str, Document] = {}
    for reference in references:
        if reference.type == "tracking_number":
            found = _orders_shipped_under(session, tenant_id, reference.value, party_id)
        elif reference.type in {"shop_order_number", "customer_reference"}:
            column = (
                "number"
                if reference.type == "shop_order_number"
                else "customer_reference"
            )
            found = _orders_by(
                session, tenant_id, party_id, **{column: reference.value}
            )
        else:
            found = []
        orders.update({order.id: order for order in found})
    return list(orders.values())


def _invoices_named(
    session: Session,
    tenant_id: str,
    party_id: str,
    currency: str,
    references: list[Reference],
) -> list[Document]:
    """Every posted invoice the references lead to, open or not."""
    invoices: dict[str, Document] = {
        invoice.id: invoice
        for invoice in resolve_references(
            session, tenant_id, party_id, currency, tuple(references)
        ).invoices
    }
    for order in _orders_named(session, tenant_id, party_id, references):
        for invoice in _invoices_billing(session, tenant_id, order):
            if (
                invoice.currency == currency
                and _posted_control(session, tenant_id, invoice) is not None
            ):
                invoices.setdefault(invoice.id, invoice)
    return list(invoices.values())


def _open_credit_note(
    session: Session, tenant_id: str, invoices: list[Document]
) -> Document | None:
    """The one posted credit note crediting these invoices that still owes money back."""
    if not invoices:
        return None
    invoice_lines = select(DocumentLine.id).where(
        DocumentLine.tenant_id == tenant_id,
        DocumentLine.document_id.in_([invoice.id for invoice in invoices]),
    )
    notes = list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.type == "credit_note",
                Document.id.in_(
                    select(DocumentLine.document_id).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.billed_document_line_id.in_(invoice_lines),
                    )
                ),
            )
        )
    )
    open_amounts = core.open_invoice_amounts(session, tenant_id, notes)
    open_notes = [note for note in notes if open_amounts.get(note.id, 0) > 0]
    return open_notes[0] if len(open_notes) == 1 else None


def _held_payment(
    session: Session,
    tenant_id: str,
    invoices: list[Document],
    clearing_account_id: str,
    amount: Decimal,
) -> str | None:
    """The one unreturned payment of this amount, on this account, that paid these invoices."""
    if not invoices:
        return None
    controls = select(LedgerEntry.id).where(
        LedgerEntry.tenant_id == tenant_id,
        LedgerEntry.document_id.in_([invoice.id for invoice in invoices]),
        LedgerEntry.account == "accounts_receivable",
    )
    payment_entries = list(
        session.scalars(
            select(LedgerEntry)
            .join(
                SettlementAllocation,
                (SettlementAllocation.tenant_id == LedgerEntry.tenant_id)
                & (SettlementAllocation.payment_ledger_entry_id == LedgerEntry.id),
            )
            .join(
                Document,
                (Document.tenant_id == LedgerEntry.tenant_id)
                & (Document.id == LedgerEntry.document_id),
            )
            .where(
                LedgerEntry.tenant_id == tenant_id,
                Document.type == "customer_payment",
                SettlementAllocation.invoice_ledger_entry_id.in_(controls),
                LedgerEntry.amount == amount,
            )
        )
    )
    reversed_groups = set(
        session.scalars(
            select(LedgerReversal.original_posting_group_id).where(
                LedgerReversal.tenant_id == tenant_id,
                LedgerReversal.original_posting_group_id.in_(
                    {entry.posting_group_id for entry in payment_entries}
                ),
            )
        )
    )
    on_account = set(
        session.scalars(
            select(LedgerEntry.posting_group_id).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.posting_group_id.in_(
                    {entry.posting_group_id for entry in payment_entries}
                ),
                LedgerEntry.account_id == clearing_account_id,
            )
        )
    )
    payments = {
        entry.document_id
        for entry in payment_entries
        if entry.posting_group_id in on_account
        and entry.posting_group_id not in reversed_groups
    }
    return next(iter(payments)) if len(payments) == 1 else None


def _warm(session: Session, tenant_id: str, lines: list[dict[str, Any]]) -> None:
    """Read what the lines' order references lead to, for the whole statement at once.

    The same functions resolve each line afterwards; inside the batch they find
    what was read here instead of reading per line. Nothing a batch writes changes
    these orders, their lines, the invoices billing them or those invoices'
    control entries (spec 342).
    """
    memo = core._batch_memo(session)
    if memo is None:
        return
    columns = {
        "shop_order_number": "number",
        "customer_reference": "customer_reference",
    }
    wanted: dict[str, set[str]] = {column: set() for column in columns.values()}
    for line in lines:
        for reference in line["references"]:
            if reference["type"] in columns:
                wanted[columns[reference["type"]]].add(reference["value"])
    orders: dict[str, Document] = {}
    for reference_type, column in columns.items():
        if not wanted[column]:
            continue
        found = list(
            session.scalars(
                select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.type == "sales_order",
                    getattr(Document, column).in_(wanted[column]),
                )
            )
        )
        by_value: dict[str, list[Document]] = {value: [] for value in wanted[column]}
        for order in found:
            by_value[getattr(order, column)].append(order)
            orders[order.id] = order
        for value, group in by_value.items():
            memo[("customers", tenant_id, reference_type, value)] = {
                order.party_id for order in group
            }
            by_party: dict[str, list[Document]] = {}
            for order in group:
                by_party.setdefault(order.party_id, []).append(order)
            for party_id, party_orders in by_party.items():
                memo[("orders_by", tenant_id, party_id, column, value)] = party_orders
    if not orders:
        return
    order_lines: dict[str, list[DocumentLine]] = {order_id: [] for order_id in orders}
    for line in session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.document_id.in_(list(orders)),
        )
    ):
        order_lines[line.document_id].append(line)
    line_order = {
        line.id: order_id for order_id, rows in order_lines.items() for line in rows
    }
    billing_ids: dict[str, set[str]] = {order_id: set() for order_id in orders}
    if line_order:
        for invoice_id, billed_line_id in session.execute(
            select(
                DocumentLine.document_id, DocumentLine.billed_document_line_id
            ).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.billed_document_line_id.in_(list(line_order)),
            )
        ):
            billing_ids[line_order[billed_line_id]].add(invoice_id)
    invoice_ids = set().union(*billing_ids.values())
    invoices = (
        {
            invoice.id: invoice
            for invoice in session.scalars(
                select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.id.in_(list(invoice_ids)),
                    Document.type == "sales_invoice",
                )
            )
        }
        if invoice_ids
        else {}
    )
    for order_id in orders:
        memo[("lines_of", tenant_id, order_id)] = order_lines[order_id]
        memo[("invoices_billing", tenant_id, order_id)] = [
            invoices[invoice_id]
            for invoice_id in billing_ids[order_id]
            if invoice_id in invoices
        ]
    if not invoices:
        return
    invoice_line = aliased(DocumentLine)
    billed: dict[str, set[str]] = {invoice_id: set() for invoice_id in invoices}
    for invoice_id, order_id in session.execute(
        select(invoice_line.document_id, DocumentLine.document_id)
        .join(
            DocumentLine,
            (DocumentLine.tenant_id == invoice_line.tenant_id)
            & (DocumentLine.id == invoice_line.billed_document_line_id),
        )
        .where(
            invoice_line.tenant_id == tenant_id,
            invoice_line.document_id.in_(list(invoices)),
        )
    ):
        billed[invoice_id].add(order_id)
    for invoice_id, order_ids in billed.items():
        memo[("billed_orders", tenant_id, invoice_id)] = order_ids
    controls = core._settlement_control_entries(
        session, tenant_id, list(invoices.values())
    )
    for invoice_id, entry in controls.items():
        memo[("control", tenant_id, invoice_id)] = entry
    groups = {entry.posting_group_id for entry in controls.values()}
    roles = core._ledger_reversal_roles(session, tenant_id, groups)
    for group_id in groups:
        memo[("reversal", tenant_id, group_id)] = roles.get(group_id, (None, "normal"))


class _Planner:
    """Decides what each line does, reading open amounts once for the statement.

    A statement of hundreds of charges would otherwise measure each invoice on
    its own; the open amounts are read in one pass and lowered here as lines
    allocate, inside the one transaction that books them.
    """

    def __init__(
        self, session: Session, tenant_id: str, statement: dict[str, Any]
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.statement = statement
        self.pending: dict[tuple[str, str], list[str]] = {}
        self.open: dict[str, Decimal] = {}
        self.resolved: dict[str, tuple[set[str], Any]] = {}

    def prefetch(self, lines: list[dict[str, Any]]) -> None:
        _warm(self.session, self.tenant_id, lines)
        invoices: dict[str, Document] = {}
        for line in lines:
            if line["kind"] != "charge":
                continue
            references = [Reference.model_validate(item) for item in line["references"]]
            customers = _customers(self.session, self.tenant_id, references)
            resolution = (
                resolve_references(
                    self.session,
                    self.tenant_id,
                    next(iter(customers)),
                    self.statement["currency"],
                    tuple(references),
                )
                if len(customers) == 1
                else None
            )
            self.resolved[line["line_id"]] = (customers, resolution)
            if resolution is not None and resolution.unambiguous is not None:
                invoices[resolution.unambiguous.id] = resolution.unambiguous
        self.open.update(
            core.open_invoice_amounts(
                self.session, self.tenant_id, list(invoices.values())
            )
        )

    def _open(self, document: Document) -> Decimal:
        if document.id not in self.open:
            self.open[document.id] = core.open_invoice_amount(
                self.session, self.tenant_id, document.id
            )
        return self.open[document.id]

    def booked(self, plan: dict[str, Any]) -> None:
        """Lower the open amount a booked allocation settled."""
        target = plan.get("invoice_id") or plan.get("credit_note_id")
        if plan["outcome"] == "allocate" and target in self.open:
            self.open[target] -= Decimal(plan["allocate"])

    def plan(self, line: dict[str, Any]) -> dict[str, Any]:
        """What one line will do, read from what Reality holds now."""
        session, tenant_id, statement = self.session, self.tenant_id, self.statement
        plan: dict[str, Any] = {
            "line_id": line["line_id"],
            "kind": line["kind"],
            "amount": line["amount"],
            "outcome": "unmatched",
            "reasons": [],
        }
        if line["kind"] == "fee":
            plan["outcome"] = "expense"
            return plan
        references = [Reference.model_validate(item) for item in line["references"]]
        customers, resolution = self.resolved.pop(line["line_id"], (None, None))
        if customers is None:
            customers = _customers(session, tenant_id, references)
        if len(customers) != 1:
            plan["reasons"].append(
                "the references name no customer"
                if not customers
                else "the references name several customers"
            )
            return plan
        (party_id,) = customers
        plan["party_id"] = party_id
        currency = statement["currency"]
        amount = Decimal(line["amount"])
        if line["kind"] == "charge":
            resolution = resolution or resolve_references(
                session, tenant_id, party_id, currency, tuple(references)
            )
            invoice = resolution.unambiguous
            plan["reasons"] = list(resolution.reasons)
            plan["outcome"] = "record"
            if invoice is not None:
                open_amount = self._open(invoice)
                if open_amount > 0:
                    plan.update(
                        outcome="allocate",
                        invoice_id=invoice.id,
                        invoice_number=invoice.number,
                        allocate=_text(min(amount, open_amount)),
                    )
                    self.pending.setdefault((invoice.id, line["amount"]), []).append(
                        line["line_id"]
                    )
                else:
                    plan["reasons"].append(
                        f"invoice {invoice.number} is already settled"
                    )
            return plan
        invoices = _invoices_named(session, tenant_id, party_id, currency, references)
        if line["kind"] == "refund":
            note = _open_credit_note(session, tenant_id, invoices)
            plan["outcome"] = "record"
            if note is None:
                plan["reasons"].append("no open credit note for the order")
            else:
                plan.update(
                    outcome="allocate",
                    credit_note_id=note.id,
                    credit_note_number=note.number,
                    allocate=_text(min(amount, self._open(note))),
                )
            return plan
        # A chargeback returns a payment held on this provider's account, or the
        # payment a charge of the same statement is about to book.
        payment = _held_payment(
            session, tenant_id, invoices, statement["clearing_account_id"], amount
        )
        if payment is not None:
            plan.update(outcome="return", payment_document_id=payment)
            return plan
        for invoice in invoices:
            waiting = self.pending.get((invoice.id, line["amount"]))
            if waiting:
                plan.update(
                    outcome="return",
                    invoice_id=invoice.id,
                    charge_line_id=waiting.pop(0),
                )
                return plan
        plan["reasons"].append(
            "no payment of this amount on the provider account for the order"
        )
        return plan


def _plans(
    session: Session,
    tenant_id: str,
    statement: dict[str, Any],
    booked: set[str],
) -> list[dict[str, Any]]:
    planner = _Planner(session, tenant_id, statement)
    planner.prefetch(
        [line for line in statement["lines"] if line["line_id"] not in booked]
    )
    plans = []
    for kind in KINDS:
        for line in statement["lines"]:
            if line["kind"] != kind:
                continue
            if line["line_id"] in booked:
                plans.append(
                    {
                        "line_id": line["line_id"],
                        "kind": kind,
                        "amount": line["amount"],
                        "outcome": "booked",
                        "reasons": [],
                    }
                )
            else:
                plans.append(planner.plan(line))
    return plans


def _totals(statement: dict[str, Any]) -> dict[str, str]:
    return {
        kind: _text(
            sum(
                (
                    Decimal(line["amount"])
                    for line in statement["lines"]
                    if line["kind"] == kind
                ),
                Decimal(0),
            )
        )
        for kind in KINDS
    }


def preview_payout(
    session: Session, tenant_id: str, values: dict[str, Any]
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Preview the current payout statement line by line without recording business changes.

    BUSINESS RULE services.payouts.preview_payout.batch_route:
    Read the statement through the shared preview implementation, reusing stable reads for this batch. Inspect the called implementation for line matching, totals and unmatched amounts.
    """
    # reality-rule: services.payouts.preview_payout.batch_route
    with core._batch_reads(session):
        return _preview(session, tenant_id, values)


def _preview(
    session: Session, tenant_id: str, values: dict[str, Any]
) -> dict[str, Any]:
    """
    What settling this statement would do, line by line; records nothing.

    BUSINESS PURPOSE:
    What settling this statement would do, line by line; records nothing.

    BUSINESS RULE services.payouts.preview_payout.result:
    Return the current result with provider, settled_before, totals, lines, unmatched_line_ids, unmatched_amount.
    """
    statement = _statement(values, core._company_day(session, tenant_id, core.now()))
    provider = core._tenant_record(
        session, Party, tenant_id, statement["provider_party_id"]
    )
    _accounts(session, tenant_id, statement)
    held = _held_statement(session, tenant_id, statement)
    sources = _line_sources(session, tenant_id, held)
    bookings = _bookings(session, tenant_id, {s.id for s in sources.values()})
    booked = {line_id for line_id, s in sources.items() if s.id in bookings}
    plans = _plans(session, tenant_id, statement, booked)
    unbooked = [plan for plan in plans if plan["outcome"] == "unmatched"]
    # reality-rule: services.payouts.preview_payout.result
    return {
        **{key: statement[key] for key in statement if key != "lines"},
        "provider": provider.name,
        "settled_before": held is not None,
        "totals": _totals(statement),
        "lines": plans,
        "unmatched_line_ids": [plan["line_id"] for plan in unbooked],
        "unmatched_amount": _text(
            sum((Decimal(plan["amount"]) for plan in unbooked), Decimal(0))
        ),
    }


# ---------------------------------------------------------------------------
# Settlement


def _book(
    session: Session,
    tenant_id: str,
    statement: dict[str, Any],
    plan: dict[str, Any],
    source: SourceRecord,
    *,
    effective_at: datetime,
    action_id: str,
    actor_id: str | None,
) -> None:
    amount = Decimal(plan["amount"])
    number = f"{statement['payout_reference']}-{plan['line_id']}"
    clearing = statement["clearing_account_id"]
    currency = statement["currency"]
    kind = plan["kind"]
    if kind == "fee":
        document = core.create_document(
            session,
            tenant_id,
            "payout_fee",
            number,
            statement["provider_party_id"],
            amount,
            currency=currency,
            document_date=statement["paid_on"],
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        core.post_ledger(
            session,
            tenant_id,
            document.id,
            statement["provider_party_id"],
            [("payment_fee_expense", "debit", amount), ("cash", "credit", amount)],
            account_ids={"cash": clearing},
            currency=currency,
            source_record_id=source.id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
        return
    if kind == "chargeback":
        from reality.services.payment_returns import record_return

        payment = plan.get("payment_document_id")
        if payment is None:
            invoice = core._tenant_record(
                session, Document, tenant_id, plan["invoice_id"]
            )
            payment = _held_payment(session, tenant_id, [invoice], clearing, amount)
        record_return(
            session,
            tenant_id,
            payment_document_id=payment,
            kind="chargeback",
            returned_on=statement["paid_on"],
            reason=plan.get("reason")
            or f"Chargeback in payout {statement['payout_reference']}",
            reference=statement["payout_reference"],
            action_id=action_id,
            actor_id=actor_id,
            _source_record=source,
        )
        return
    target_id = plan.get("invoice_id") or plan.get("credit_note_id")
    target = (
        core._settlement_control_entry(session, tenant_id, target_id)
        if plan["outcome"] == "allocate"
        else None
    )
    record = (
        core.record_customer_payment
        if kind == "charge"
        else core.record_customer_refund
    )
    entries = record(
        session,
        tenant_id,
        plan["party_id"],
        amount,
        currency=currency,
        **{"payment_number" if kind == "charge" else "refund_number": number},
        source_record_id=source.id,
        effective_at=effective_at,
        action_id=action_id,
        _control_account_id=target.account_id if target else None,
        _cash_account_id=clearing,
        _commit=False,
    )
    if target is not None:
        core.allocate_settlement(
            session,
            tenant_id,
            next(e for e in entries if e.account == "accounts_receivable").id,
            target.id,
            Decimal(plan["allocate"]),
            action_id=action_id,
            _commit=False,
        )


def settle_payout(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    **values: Any,
) -> dict[str, Any]:
    """
    Book the statement's lines, once each, and its deposit; callers own the transaction.

    Every line is resolved again under the finance lock, so a payment or order
    recorded since the review is seen as it is now. The lines are booked as one
    batch: locks taken and stable reads made for the first line hold for the rest
    (spec 342).

    BUSINESS PURPOSE:
    Settle the payout statement's lines once each and record its deposit in the caller's transaction.

    BUSINESS RULE services.payouts.settle_payout.batch_route:
    Execute the shared settlement implementation within the statement's batch read scope. The called implementation owns current finance permission, line validation, records and posting; this wrapper preserves the caller's transaction.
    """
    # reality-rule: services.payouts.settle_payout.batch_route
    with core._batch_reads(session):
        return _settle(
            session, tenant_id, action_id=action_id, actor_id=actor_id, **values
        )


def _settle(
    session: Session,
    tenant_id: str,
    *,
    action_id: str,
    actor_id: str | None,
    **values: Any,
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Book the payout statement after checking its current line outcomes and finance permission.

    BUSINESS RULE services.payouts.settle_payout.step-13:
    Require the business permission for 'settle_payout' before changing company records.

    BUSINESS RULE services.payouts.settle_payout.step-114:
    Record the payout.settled audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.payouts.settle_payout.result:
    Return the result from payout detail; inspect that called function for its calculation and eligibility rules.

    BUSINESS RULE services.payouts.settle_payout.effect-51:
    IF no payout document has yet been recorded:
        Pass the stated inputs to the shared create document service. Its own source describes validation and record changes.
    """
    # reality-rule: services.payouts.settle_payout.step-13
    core._require_business_mutation(session, tenant_id, "settle_payout")
    lock_finance(session, tenant_id)
    statement = _statement(values, core._company_day(session, tenant_id, core.now()))
    core._tenant_record(session, Party, tenant_id, statement["provider_party_id"])
    _accounts(session, tenant_id, statement)
    held = _held_statement(session, tenant_id, statement)
    source = (
        held
        or core.store_source_record(
            session,
            tenant_id,
            SOURCE_SYSTEM,
            STATEMENT_TYPE,
            _external_id(statement),
            statement,
        )[0]
    )
    effective_at = datetime.combine(
        date.fromisoformat(statement["paid_on"]), time(), UTC
    )
    payout = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == source.id,
            Document.type == "payout",
        )
    )
    if payout is None:
        amount = Decimal(statement["amount"])
        # reality-rule: services.payouts.settle_payout.effect-51
        payout = core.create_document(
            session,
            tenant_id,
            "payout",
            statement["payout_reference"],
            statement["provider_party_id"],
            amount,
            currency=statement["currency"],
            document_date=statement["paid_on"],
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        core.post_ledger(
            session,
            tenant_id,
            payout.id,
            statement["provider_party_id"],
            [("cash", "debit", amount), ("cash", "credit", amount)],
            currency=statement["currency"],
            source_record_id=source.id,
            effective_at=effective_at,
            action_id=action_id,
            _line_account_ids=[
                statement["bank_account_id"],
                statement["clearing_account_id"],
            ],
            _commit=False,
        )
    lines = {line["line_id"]: line for line in statement["lines"]}
    stored = core._store_source_records(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        LINE_TYPE,
        {
            _line_external_id(source.id, line_id): {
                "payout_source_record_id": source.id,
                "provider_party_id": statement["provider_party_id"],
                "payout_reference": statement["payout_reference"],
                "paid_on": statement["paid_on"],
                "currency": statement["currency"],
                **line,
            }
            for line_id, line in lines.items()
        },
    )
    sources = {
        line_id: stored[_line_external_id(source.id, line_id)] for line_id in lines
    }
    bookings = _bookings(session, tenant_id, {s.id for s in sources.values()})
    booked = {line_id for line_id, s in sources.items() if s.id in bookings}
    planner = _Planner(session, tenant_id, statement)
    planner.prefetch([line for line_id, line in lines.items() if line_id not in booked])
    newly: list[str] = []
    unmatched: list[str] = []
    for kind in KINDS:
        for line_id, line in lines.items():
            if line["kind"] != kind or line_id in booked:
                continue
            plan = planner.plan(line)
            if plan["outcome"] == "unmatched":
                unmatched.append(line_id)
                continue
            _book(
                session,
                tenant_id,
                statement,
                {**plan, "reason": line["reason"]},
                sources[line_id],
                effective_at=effective_at,
                action_id=action_id,
                actor_id=actor_id,
            )
            planner.booked(plan)
            newly.append(line_id)
    session.flush()
    # reality-rule: services.payouts.settle_payout.step-114
    emit_business_event(
        session,
        tenant_id,
        "payout.settled",
        "document",
        payout.id,
        {
            "payout_reference": statement["payout_reference"],
            "provider_party_id": statement["provider_party_id"],
            "amount": statement["amount"],
            "currency": statement["currency"],
            "booked_line_ids": newly,
            "unmatched_line_ids": unmatched,
        },
        source_record_id=source.id,
        action_id=action_id,
    )
    # reality-rule: services.payouts.settle_payout.result
    return payout_detail(session, tenant_id, payout.id)


# ---------------------------------------------------------------------------
# Reads


def _payout(session: Session, tenant_id: str, payout_id: str) -> Document:
    payout = core._tenant_record(session, Document, tenant_id, payout_id)
    if payout.type != "payout":
        raise core.NotFound(code="payout_not_found")
    return payout


def _allocated_to(
    session: Session, tenant_id: str, document_ids: set[str]
) -> dict[str, list[str]]:
    """The invoices or credit notes each payment or refund document was allocated to."""
    if not document_ids:
        return {}
    entries = {
        entry.id: entry.document_id
        for entry in session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id.in_(document_ids),
                LedgerEntry.account == "accounts_receivable",
            )
        )
    }
    allocations = core.active_settlement_allocations(
        session, tenant_id, entry_ids=set(entries)
    )
    target_entries = {
        allocation.invoice_ledger_entry_id
        for allocation in allocations
        if allocation.payment_ledger_entry_id in entries
    }
    documents = (
        dict(
            session.execute(
                select(LedgerEntry.id, LedgerEntry.document_id).where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.id.in_(target_entries),
                )
            ).all()
        )
        if target_entries
        else {}
    )
    targets: dict[str, list[str]] = {}
    for allocation in allocations:
        document_id = entries.get(allocation.payment_ledger_entry_id)
        if document_id is not None:
            targets.setdefault(document_id, []).append(
                documents[allocation.invoice_ledger_entry_id]
            )
    return targets


def payout_detail(session: Session, tenant_id: str, payout_id: str) -> dict[str, Any]:
    """
    One payout: the stated statement and what each line booked or why it did not.

    BUSINESS PURPOSE:
    One payout: the stated statement and what each line booked or why it did not.

    BUSINESS RULE services.payouts.payout_detail.result:
    Return the current result with id, payout_reference, provider_party_id, paid_on, currency, amount, clearing_account_id, bank_account_id, totals, lines, unmatched_line_ids, unmatched_amount, source_record_id.
    """
    payout = _payout(session, tenant_id, payout_id)
    source = core._tenant_record(
        session, SourceRecord, tenant_id, payout.source_record_id
    )
    statement = json.loads(source.payload)
    sources = _line_sources(session, tenant_id, source)
    bookings = _bookings(session, tenant_id, {s.id for s in sources.values()})
    booked_documents = {
        booking["document_id"]
        for booking in bookings.values()
        if "document_id" in booking
    }
    allocated = _allocated_to(session, tenant_id, booked_documents)
    unbooked = {
        line["line_id"]
        for line in statement["lines"]
        if line["line_id"] not in sources or sources[line["line_id"]].id not in bookings
    }
    plans = (
        {
            plan["line_id"]: plan
            for plan in _plans(
                session,
                tenant_id,
                statement,
                {line["line_id"] for line in statement["lines"]} - unbooked,
            )
        }
        if unbooked
        else {}
    )
    tracking = {
        reference["value"]
        for line in statement["lines"]
        for reference in line["references"]
        if reference["type"] == "tracking_number"
    }
    shipments: dict[str, set[str]] = {}
    if tracking:
        for number, shipment_id in session.execute(
            select(ShipmentPackage.tracking_number, ShipmentPackage.shipment_id).where(
                ShipmentPackage.tenant_id == tenant_id,
                ShipmentPackage.tracking_number.in_(tracking),
            )
        ):
            shipments.setdefault(number, set()).add(shipment_id)
    rows = []
    for line in statement["lines"]:
        line_source = sources.get(line["line_id"])
        booking = bookings.get(line_source.id, {}) if line_source else {}
        row = {
            **line,
            "state": "unmatched" if line["line_id"] in unbooked else "booked",
            "source_record_id": line_source.id if line_source else None,
            **booking,
            "allocated_to": allocated.get(booking.get("document_id"), []),
            "shipment_ids": sorted(
                {
                    shipment
                    for reference in line["references"]
                    if reference["type"] == "tracking_number"
                    for shipment in shipments.get(reference["value"], ())
                }
            ),
        }
        if line["line_id"] in unbooked:
            row["reasons"] = plans.get(line["line_id"], {}).get("reasons", [])
        rows.append(row)
    # reality-rule: services.payouts.payout_detail.result
    return {
        "id": payout.id,
        "payout_reference": statement["payout_reference"],
        "provider_party_id": statement["provider_party_id"],
        "paid_on": statement["paid_on"],
        "currency": statement["currency"],
        "amount": statement["amount"],
        "clearing_account_id": statement["clearing_account_id"],
        "bank_account_id": statement["bank_account_id"],
        "totals": _totals(statement),
        "lines": rows,
        "unmatched_line_ids": sorted(unbooked),
        "unmatched_amount": _text(
            sum(
                (
                    Decimal(line["amount"])
                    for line in statement["lines"]
                    if line["line_id"] in unbooked
                ),
                Decimal(0),
            )
        ),
        "source_record_id": source.id,
    }


def unmatched_lines(
    session: Session, tenant_id: str, *, as_of: datetime | None = None
) -> list[dict[str, Any]]:
    """Every payout with lines nothing booked, read with one anti-join.

    Only unbooked line sources come back, so a company with many settled
    payouts pays for what is still open, not for every line it ever settled.
    """
    unbooked = list(
        session.execute(
            select(SourceRecord.external_id).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.source_type == LINE_TYPE,
                ~select(Document.id)
                .where(
                    Document.tenant_id == tenant_id,
                    Document.source_record_id == SourceRecord.id,
                )
                .exists(),
                ~select(PaymentReturn.id)
                .where(
                    PaymentReturn.tenant_id == tenant_id,
                    PaymentReturn.source_record_id == SourceRecord.id,
                )
                .exists(),
            )
        ).scalars()
    )
    if not unbooked:
        return []
    open_lines: dict[str, set[str]] = {}
    for external_id in unbooked:
        statement_id, _, line_id = external_id.partition("/")
        open_lines.setdefault(statement_id, set()).add(line_id)
    rows = []
    for payout, source in session.execute(
        select(Document, SourceRecord)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(
            Document.tenant_id == tenant_id,
            Document.type == "payout",
            Document.source_record_id.in_(open_lines),
        )
    ):
        statement = json.loads(source.payload)
        if as_of is not None and date.fromisoformat(
            statement["paid_on"]
        ) > core._company_day(session, tenant_id, as_of):
            continue
        lines = [
            line
            for line in statement["lines"]
            if line["line_id"] in open_lines[source.id]
        ]
        rows.append(
            {
                "payout": payout,
                "statement": statement,
                "lines": lines,
                "amount": sum((Decimal(line["amount"]) for line in lines), Decimal(0)),
            }
        )
    return rows


def payouts(session: Session, tenant_id: str) -> list[dict[str, Any]]:
    """
    Payouts newest first, with how many lines are booked and what is not.

    BUSINESS PURPOSE:
    Payouts newest first, with how many lines are booked and what is not.

    BUSINESS RULE services.payouts.payouts.result:
    Return rows, as prepared by the preceding checks and service calls.
    """
    core.get_tenant(session, tenant_id)
    open_by_payout = {
        row["payout"].id: row for row in unmatched_lines(session, tenant_id)
    }
    rows = []
    for payout, source in session.execute(
        select(Document, SourceRecord)
        .join(
            SourceRecord,
            (SourceRecord.tenant_id == Document.tenant_id)
            & (SourceRecord.id == Document.source_record_id),
        )
        .where(Document.tenant_id == tenant_id, Document.type == "payout")
        .order_by(Document.document_date.desc(), Document.number)
    ):
        statement = json.loads(source.payload)
        unmatched = open_by_payout.get(payout.id)
        rows.append(
            {
                "id": payout.id,
                "payout_reference": statement["payout_reference"],
                "provider_party_id": statement["provider_party_id"],
                "paid_on": statement["paid_on"],
                "currency": statement["currency"],
                "amount": statement["amount"],
                "lines": len(statement["lines"]),
                "unmatched_lines": len(unmatched["lines"]) if unmatched else 0,
                "unmatched_amount": _text(unmatched["amount"]) if unmatched else "0",
            }
        )
    # reality-rule: services.payouts.payouts.result
    return rows
