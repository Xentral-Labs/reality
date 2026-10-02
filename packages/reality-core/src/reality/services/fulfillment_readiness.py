"""Explainable, tenant-scoped fulfillment readiness derived from Reality."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    CommitmentHold,
    Document,
    DocumentLine,
    LedgerEntry,
    PaymentTerm,
    Reservation,
)
from reality.services.core import (
    InvalidOperation,
    active_party_delivery_hold,
    active_settlement_allocations,
    blocked_quantity,
    commitment_quantity,
    movement_quantity,
    open_invoice_amount,
    stock_at,
)

ZERO = Decimal(0)


@dataclass(frozen=True)
class FulfillmentReadiness:
    commitment_id: str
    order_id: str | None
    ship_ready: bool
    blocker_codes: tuple[str, ...]
    currency: str
    required_amount: Decimal
    received_amount: Decimal
    remaining_amount: Decimal
    payment_term_id: str | None
    requires_prepayment: bool
    invoice_ids: tuple[str, ...]
    allocation_ids: tuple[str, ...]
    open_quantity: Decimal
    reserved_quantity: Decimal
    physical_quantity: Decimal
    commitment_hold_ids: tuple[str, ...]
    party_hold_ids: tuple[str, ...]
    #: Consolidated invoices billing this order that are still open, as
    #: (invoice id, invoice number, open amount); spec 283 FR-004.
    consolidated_open: tuple[tuple[str, str, Decimal], ...] = ()

    def as_dict(self) -> dict[str, object]:
        payment_policy = "prepayment" if self.requires_prepayment else "standard"
        blockers = [
            {
                "code": code,
                "detail": _blocker_detail(code, self),
                "links": _blocker_links(code, self),
            }
            for code in self.blocker_codes
        ]
        basis = {
            "commitment": {
                "id": self.commitment_id,
                "open_quantity": str(self.open_quantity),
            },
            "inventory": {
                "physical_quantity": str(self.physical_quantity),
                "reserved_quantity": str(self.reserved_quantity),
            },
            "commitment_hold_ids": list(self.commitment_hold_ids),
            "party_hold_ids": list(self.party_hold_ids),
            "invoice_ids": list(self.invoice_ids),
            "allocation_ids": list(self.allocation_ids),
        }
        return {
            "commitment_id": self.commitment_id,
            "document_id": self.order_id,
            "order_id": self.order_id,
            "ship_ready": self.ship_ready,
            "blocker_codes": list(self.blocker_codes),
            "blocking_reasons": list(self.blocker_codes),
            "blockers": blockers,
            "currency": self.currency,
            "required_amount": str(self.required_amount),
            "received_amount": str(self.received_amount),
            "remaining_amount": str(self.remaining_amount),
            "payment_term_id": self.payment_term_id,
            "requires_prepayment": self.requires_prepayment,
            "invoice_ids": list(self.invoice_ids),
            "allocation_ids": list(self.allocation_ids),
            "payment": {
                "policy": payment_policy,
                "required": str(self.required_amount),
                "received": str(self.received_amount),
                "remaining": str(self.remaining_amount),
                "payment_term_id": self.payment_term_id,
                "invoice_ids": list(self.invoice_ids),
                "allocation_ids": list(self.allocation_ids),
            },
            "lines": [
                {
                    "commitment_id": self.commitment_id,
                    "open_quantity": str(self.open_quantity),
                    "reserved_quantity": str(self.reserved_quantity),
                    "physical_quantity": str(self.physical_quantity),
                }
            ],
            "basis": basis,
            "links": [
                {"kind": kind, "id": identity}
                for kind, identities in (
                    (
                        "payment_term",
                        (self.payment_term_id,) if self.payment_term_id else (),
                    ),
                    ("invoice", self.invoice_ids),
                    ("settlement_allocation", self.allocation_ids),
                    ("commitment_hold", self.commitment_hold_ids),
                    ("party_hold", self.party_hold_ids),
                )
                for identity in identities
            ],
        }


def _blocker_detail(code: str, result: FulfillmentReadiness) -> str:
    if code == "prepayment_required":
        return (
            f"{result.required_amount} {result.currency} is required; "
            f"{result.received_amount} {result.currency} is allocated."
        )
    if code == "prepayment_consolidated_invoice_open":
        return "; ".join(
            f"Consolidated invoice {number} is open by {amount} {result.currency}; "
            "the order is released once it is settled in full."
            for _, number, amount in result.consolidated_open
        )
    return {
        "prepayment_invoice_missing": "No posted order-backed customer receivable proves the payment basis.",
        "prepayment_attribution_ambiguous": "Invoice evidence covers more than this order and cannot be attributed automatically.",
        "insufficient_reservation": "The open delivery quantity is not fully reserved.",
        "insufficient_stock": "Physical stock is below the open delivery quantity.",
        "commitment_hold": "The delivery commitment has an active hold.",
        "party_delivery_hold": "The customer has an active delivery hold.",
        "ship_complete_incomplete": "The order ships complete, and not every open line can ship its whole quantity yet.",
    }.get(code, code.replace("_", " "))


def _blocker_links(code: str, result: FulfillmentReadiness) -> list[dict[str, str]]:
    if code == "prepayment_consolidated_invoice_open":
        return [
            {"kind": "invoice", "id": identity}
            for identity, _, _ in result.consolidated_open
        ]
    if code.startswith("prepayment") and result.payment_term_id:
        return [{"kind": "payment_term", "id": result.payment_term_id}]
    if code == "commitment_hold":
        return [
            {"kind": "commitment_hold", "id": row} for row in result.commitment_hold_ids
        ]
    if code == "party_delivery_hold":
        return [{"kind": "party_hold", "id": row} for row in result.party_hold_ids]
    if code == "ship_complete_incomplete" and result.order_id:
        return [{"kind": "document", "id": result.order_id}]
    return [{"kind": "commitment", "id": result.commitment_id}]


def stock_cover(
    own_location_id: str | None,
    reserved_by_location: dict[str, Decimal],
    physical_at: Callable[[str | None], Decimal],
) -> tuple[Decimal, Decimal]:
    """What stock stands behind a promise, and how much of it is ready (spec 303).

    The promise's own location counts with all it holds, as it always has; a
    reservation at another location counts only with what that location still
    holds of it. The second figure is what could ship now: at every location,
    the reserved quantity that is physically there. With every reservation at
    home both are what they were before: the own location's stock, and the
    smaller of reserved and stock.
    """
    # A promise without a warehouse reads what the reader reads for "no
    # location", exactly as before.
    own = physical_at(own_location_id)
    basis = own
    ready = min(reserved_by_location.get(own_location_id or "", ZERO), own)
    for location_id, reserved in reserved_by_location.items():
        if location_id == own_location_id:
            continue
        here = min(reserved, physical_at(location_id))
        basis += here
        ready += here
    return basis, ready


def ready_by_location(
    own_location_id: str | None,
    reserved_by_location: dict[str, Decimal],
    physical_at: Callable[[str | None], Decimal],
) -> dict[str, Decimal]:
    """What could ship now from each warehouse: reserved there and on hand there.

    The parts add up to the ready quantity of `stock_cover`, so a person can
    prepare one shipment per warehouse for exactly what the promise shows as
    ready (spec 303).
    """
    return {
        location_id: here
        for location_id, reserved in reserved_by_location.items()
        if (here := min(reserved, physical_at(location_id))) > ZERO
    }


def fulfillment_readiness(
    session: Session,
    tenant_id: str,
    commitment_id: str,
    *,
    proposed_quantity: Decimal | None = None,
    from_location_id: str | None = None,
    _delivery_rule: bool = True,
) -> FulfillmentReadiness:
    """Derive payment readiness for one customer-delivery commitment.

    Amounts are stated document and allocation values. This function never creates
    payment or fulfillment authority and never infers policy from a term label.
    """
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == commitment_id,
        )
    )
    if commitment is None:
        raise InvalidOperation(code="fulfillment_commitment_not_found")
    if commitment.type != "customer_delivery":
        raise InvalidOperation(
            code="fulfillment_readiness_customer_commitment_required"
        )
    open_quantity = max(
        commitment_quantity(session, tenant_id, commitment.id)
        - movement_quantity(session, tenant_id, commitment.id, "shipment"),
        ZERO,
    )
    checked_quantity = open_quantity if proposed_quantity is None else proposed_quantity
    if proposed_quantity is not None and (
        checked_quantity <= ZERO or checked_quantity > open_quantity
    ):
        raise InvalidOperation(code="fulfillment_shipment_quantity_invalid")
    reserved_by_location = {
        location_id: Decimal(quantity)
        for location_id, quantity in session.execute(
            select(Reservation.location_id, func.sum(Reservation.quantity))
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
            .group_by(Reservation.location_id)
        )
    }

    def physical_at(location_id: str | None) -> Decimal:
        # Spec 304: blocked stock never ships, so it is not stock behind a
        # promise either.
        return (
            stock_at(session, tenant_id, commitment.item_id, location_id)
            - blocked_quantity(session, tenant_id, commitment.item_id, location_id)
            if commitment.item_id
            else ZERO
        )

    if from_location_id:
        # A shipment leaves from one place, and only what is reserved and on
        # hand there can go with it (spec 303).
        reserved_quantity = reserved_by_location.get(from_location_id, ZERO)
        physical_quantity = physical_at(from_location_id)
        ready_quantity = min(reserved_quantity, physical_quantity)
    else:
        reserved_quantity = sum(reserved_by_location.values(), ZERO)
        physical_quantity, ready_quantity = stock_cover(
            commitment.location_id, reserved_by_location, physical_at
        )
    commitment_hold_ids = tuple(
        session.scalars(
            select(CommitmentHold.id)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == commitment.id,
                CommitmentHold.released_at.is_(None),
            )
            .order_by(CommitmentHold.id)
        )
    )
    party_hold = (
        active_party_delivery_hold(session, tenant_id, commitment.to_party_id)
        if commitment.to_party_id
        else None
    )
    party_hold_ids = (party_hold.id,) if party_hold else ()
    operational_blockers: list[str] = []
    if commitment_hold_ids:
        operational_blockers.append("commitment_hold")
    if party_hold_ids:
        operational_blockers.append("party_delivery_hold")
    if reserved_quantity < checked_quantity:
        operational_blockers.append("insufficient_reservation")
    if physical_quantity < checked_quantity or (
        reserved_quantity >= checked_quantity > ready_quantity
    ):
        operational_blockers.append("insufficient_stock")
    if not commitment.document_id:
        return FulfillmentReadiness(
            commitment.id,
            None,
            open_quantity > ZERO and not operational_blockers,
            tuple(operational_blockers),
            commitment.currency,
            ZERO,
            ZERO,
            ZERO,
            None,
            False,
            (),
            (),
            open_quantity,
            reserved_quantity,
            physical_quantity,
            commitment_hold_ids,
            party_hold_ids,
        )
    order = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.id == commitment.document_id,
        )
    )
    if order is None or order.type != "sales_order":
        raise InvalidOperation(code="customer_delivery_order_not_found")
    if _delivery_rule:
        # Spec 306: under ship complete a line is ready only with the whole
        # order, every open line in full.
        from reality.services.delivery_rules import order_ships_complete

        if not order_ships_complete(
            session, tenant_id, order.id, commitment.id, checked_quantity, open_quantity
        ):
            operational_blockers.append("ship_complete_incomplete")
    term = (
        session.scalar(
            select(PaymentTerm).where(
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.id == order.payment_term_id,
            )
        )
        if order.payment_term_id
        else None
    )
    required = Decimal(order.gross_amount)
    if term is None or not term.requires_prepayment:
        return FulfillmentReadiness(
            commitment.id,
            order.id,
            open_quantity > ZERO and not operational_blockers,
            tuple(operational_blockers),
            order.currency,
            required,
            ZERO,
            ZERO,
            order.payment_term_id,
            False,
            (),
            (),
            open_quantity,
            reserved_quantity,
            physical_quantity,
            commitment_hold_ids,
            party_hold_ids,
        )

    order_line_ids = set(
        session.scalars(
            select(DocumentLine.id).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == order.id,
            )
        )
    )
    invoice_rows = list(
        session.execute(
            select(DocumentLine.document_id, DocumentLine.billed_document_line_id)
            .join(
                Document,
                (Document.tenant_id == DocumentLine.tenant_id)
                & (Document.id == DocumentLine.document_id),
            )
            .where(
                DocumentLine.tenant_id == tenant_id,
                Document.type == "sales_invoice",
                Document.party_id == order.party_id,
                Document.currency == order.currency,
                DocumentLine.billed_document_line_id.in_(order_line_ids),
            )
        )
    )
    candidate_invoice_ids = {row.document_id for row in invoice_rows}
    # A down-payment invoice is for the order, not for a line (spec 299), and its
    # payments count towards the prepayment like an invoice's.
    from reality.services.down_payments import (
        live_offsets,
        order_down_payment_invoice_ids,
    )

    down_payment_ids = order_down_payment_invoice_ids(session, tenant_id, order.id)
    candidate_invoice_ids |= down_payment_ids
    # An invoice that also bills other orders of this party in this currency is a
    # consolidated invoice (spec 283), not ambiguous: it counts for this order only
    # once it is settled in full, by what its own lines state for this order. A
    # line billing another party's or currency's order cannot be attributed.
    ambiguous = False
    consolidated: set[str] = set()
    for invoice_id in candidate_invoice_ids:
        billed_orders = session.execute(
            select(Document.party_id, Document.currency, DocumentLine.document_id)
            .select_from(DocumentLine)
            .join(
                Document,
                (Document.tenant_id == DocumentLine.tenant_id)
                & (Document.id == DocumentLine.document_id),
            )
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.id.in_(
                    select(DocumentLine.billed_document_line_id).where(
                        DocumentLine.tenant_id == tenant_id,
                        DocumentLine.document_id == invoice_id,
                        DocumentLine.billed_document_line_id.is_not(None),
                    )
                ),
            )
        ).all()
        if any(
            (party, currency) != (order.party_id, order.currency)
            for party, currency, _ in billed_orders
        ):
            ambiguous = True
        elif any(document_id != order.id for _, _, document_id in billed_orders):
            consolidated.add(invoice_id)

    invoice_entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id.in_(candidate_invoice_ids),
                LedgerEntry.account == "accounts_receivable",
                LedgerEntry.party_id == order.party_id,
                LedgerEntry.currency == order.currency,
            )
        )
    )
    invoice_ids = {entry.document_id for entry in invoice_entries if entry.document_id}
    entry_ids = {entry.id for entry in invoice_entries}
    allocations = active_settlement_allocations(session, tenant_id, entry_ids=entry_ids)
    payment_entry_ids = {row.payment_ledger_entry_id for row in allocations}
    valid_payments = {
        row.id
        for row in session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.id.in_(payment_entry_ids),
                LedgerEntry.party_id == order.party_id,
                LedgerEntry.currency == order.currency,
            )
        )
    }
    consolidated_entries = {
        entry.id for entry in invoice_entries if entry.document_id in consolidated
    }
    qualifying = (
        []
        if ambiguous
        else [
            row
            for row in allocations
            if row.invoice_ledger_entry_id in entry_ids
            and row.invoice_ledger_entry_id not in consolidated_entries
            and row.payment_ledger_entry_id in valid_payments
            and row.currency == order.currency
        ]
    )
    received = sum((Decimal(row.amount) for row in qualifying), ZERO)
    consolidated_open = []
    if not ambiguous:
        for invoice in session.scalars(
            select(Document)
            .where(Document.tenant_id == tenant_id, Document.id.in_(consolidated))
            .order_by(Document.number, Document.id)
        ):
            open_amount = open_invoice_amount(session, tenant_id, invoice.id)
            if open_amount > ZERO:
                consolidated_open.append((invoice.id, invoice.number, open_amount))
                continue
            received += sum(
                (
                    Decimal(line.gross_amount)
                    for line in session.scalars(
                        select(DocumentLine).where(
                            DocumentLine.tenant_id == tenant_id,
                            DocumentLine.document_id == invoice.id,
                            DocumentLine.billed_document_line_id.in_(order_line_ids),
                        )
                    )
                ),
                ZERO,
            )
            # Spec 299: what this settled invoice deducted of the order's own
            # down payments was counted when they were paid, not settled again.
            received -= sum(
                (
                    Decimal(row.amount)
                    for row in live_offsets(
                        session,
                        tenant_id,
                        down_payment_ids=down_payment_ids,
                        final_invoice_ids={invoice.id},
                    )
                ),
                ZERO,
            )
    remaining = max(required - received, ZERO)
    blockers = list(operational_blockers)
    if not invoice_ids:
        blockers.append("prepayment_invoice_missing")
    if ambiguous:
        blockers.append("prepayment_attribution_ambiguous")
    if consolidated_open:
        blockers.append("prepayment_consolidated_invoice_open")
    if remaining > ZERO:
        blockers.append("prepayment_required")
    return FulfillmentReadiness(
        commitment.id,
        order.id,
        open_quantity > ZERO and not blockers,
        tuple(blockers),
        order.currency,
        required,
        received,
        remaining,
        term.id,
        True,
        tuple(sorted(invoice_ids)),
        tuple(sorted(row.id for row in qualifying)),
        open_quantity,
        reserved_quantity,
        physical_quantity,
        commitment_hold_ids,
        party_hold_ids,
        tuple(consolidated_open),
    )


PAYMENT_BLOCKERS = (
    "prepayment_invoice_missing",
    "prepayment_attribution_ambiguous",
    "prepayment_consolidated_invoice_open",
    "prepayment_required",
)


def require_paid_prepayment(
    session: Session,
    tenant_id: str,
    movement_type: str | None,
    commitment_id: str | None,
    quantity: Decimal | str,
) -> None:
    """A shipment a person records obeys the same payment gate as a dispatched one.

    Spec 275 FR-005: a prepayment order stays non-shippable until paid, and every
    tool reads this shared decision (FR-008). Every person-facing way of recording
    a shipment calls this: the reviewed tool, its execution (also in practice
    companies), the CLI and the movement endpoint. Only the payment part is
    shared: recording goods that physically left needs no reservation. Importers
    record what a source states and do not come through here (spec 294 FR-006).
    """
    if movement_type != "shipment" or not commitment_id:
        return
    kind = session.scalar(
        select(Commitment.type).where(
            Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
        )
    )
    if kind != "customer_delivery":
        return
    readiness = fulfillment_readiness(
        session,
        tenant_id,
        commitment_id,
        proposed_quantity=Decimal(str(quantity)),
        # The order's rule is checked for the shipment as a whole below.
        _delivery_rule=False,
    )
    # Spec 306: the order's ship-complete rule binds the same paths.
    from reality.services.delivery_rules import require_delivery_rule

    require_delivery_rule(session, tenant_id, [(commitment_id, quantity)])
    payment = [code for code in readiness.blocker_codes if code in PAYMENT_BLOCKERS]
    if payment:
        raise InvalidOperation(
            code="shipment_blocked_readiness",
            values={
                "blockers": ", ".join(payment),
                "required_amount": readiness.required_amount,
                "required_currency": readiness.currency,
                "received_amount": readiness.received_amount,
                "received_currency": readiness.currency,
            },
        )
