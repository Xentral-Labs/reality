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
    Location,
    PartyHold,
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
from reality.services.read_interpretation import (
    blocker_kind,
    historical_fulfillment_cause,
    payment_interpretation,
)

ZERO = Decimal(0)


@dataclass(frozen=True)
class FulfillmentReadiness:
    commitment_id: str
    order_id: str | None
    ship_ready: bool
    blocker_codes: tuple[str, ...]
    currency: str
    required_amount: Decimal | None
    received_amount: Decimal
    remaining_amount: Decimal | None
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
    #: The owner's release that lets the order ship before it is paid (spec 347).
    prepayment_release_id: str | None = None

    def as_dict(self, *, include_interpretation: bool = True) -> dict[str, object]:
        payment_policy = "prepayment" if self.requires_prepayment else "standard"
        blockers = [
            {
                "code": code,
                "detail": _blocker_detail(code, self),
                "links": _blocker_links(code, self),
                **(
                    {"blocker_kind": blocker_kind(code)}
                    if include_interpretation
                    else {}
                ),
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
        result = {
            "commitment_id": self.commitment_id,
            "document_id": self.order_id,
            "order_id": self.order_id,
            "ship_ready": self.ship_ready,
            **(
                {"unfulfilled_cause": historical_fulfillment_cause(self.open_quantity)}
                if include_interpretation
                else {}
            ),
            "blocker_codes": list(self.blocker_codes),
            "blocking_reasons": list(self.blocker_codes),
            "blockers": blockers,
            "currency": self.currency,
            "required_amount": str(self.required_amount)
            if self.required_amount is not None
            else None,
            "received_amount": str(self.received_amount),
            "remaining_amount": str(self.remaining_amount)
            if self.remaining_amount is not None
            else None,
            "payment_term_id": self.payment_term_id,
            "requires_prepayment": self.requires_prepayment,
            "invoice_ids": list(self.invoice_ids),
            "allocation_ids": list(self.allocation_ids),
            "payment": {
                "policy": payment_policy,
                "required": str(self.required_amount)
                if self.required_amount is not None
                else None,
                "received": str(self.received_amount),
                "remaining": str(self.remaining_amount)
                if self.remaining_amount is not None
                else None,
                "payment_term_id": self.payment_term_id,
                "invoice_ids": list(self.invoice_ids),
                "allocation_ids": list(self.allocation_ids),
                "prepayment_release_id": self.prepayment_release_id,
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
                    (
                        "prepayment_release",
                        (self.prepayment_release_id,)
                        if self.prepayment_release_id
                        else (),
                    ),
                )
                for identity in identities
            ],
        }

        if include_interpretation:
            result["payment_interpretation"] = payment_interpretation(result)
        return result


def _blocker_detail(code: str, result: FulfillmentReadiness) -> str:
    # reality-rule: fulfillment_readiness._blocker_detail.guard-134
    if code == "prepayment_required":
        return (
            f"{result.required_amount} {result.currency} is required; "
            f"{result.received_amount} {result.currency} is allocated."
        )
    # reality-rule: fulfillment_readiness._blocker_detail.guard-139
    if code == "prepayment_consolidated_invoice_open":
        return "; ".join(
            f"Consolidated invoice {number} is open by {amount} {result.currency}; "
            "the order is released once it is settled in full."
            for _, number, amount in result.consolidated_open
        )
    return {
        "prepayment_amount_unstated": "The source states no order total; prepayment readiness needs a reviewed stated amount.",
        "prepayment_invoice_missing": "No posted order-backed customer receivable proves the payment basis.",
        "prepayment_attribution_ambiguous": "Invoice evidence covers more than this order and cannot be attributed automatically.",
        "insufficient_reservation": "The open delivery quantity is not fully reserved.",
        "insufficient_stock": "Physical stock is below the open delivery quantity.",
        "commitment_hold": "The delivery commitment has an active hold.",
        "party_delivery_hold": "The customer has an active delivery hold.",
        "ship_complete_incomplete": "The order ships complete, and not every open line can ship its whole quantity yet.",
    }.get(code, code.replace("_", " "))


def _blocker_links(code: str, result: FulfillmentReadiness) -> list[dict[str, str]]:
    # reality-rule: fulfillment_readiness._blocker_links.guard-156
    if code == "prepayment_consolidated_invoice_open":
        return [
            {"kind": "invoice", "id": identity}
            for identity, _, _ in result.consolidated_open
        ]
    # reality-rule: fulfillment_readiness._blocker_links.guard-161
    if code.startswith("prepayment") and result.payment_term_id:
        return [{"kind": "payment_term", "id": result.payment_term_id}]
    # reality-rule: fulfillment_readiness._blocker_links.guard-163
    if code == "commitment_hold":
        return [
            {"kind": "commitment_hold", "id": row} for row in result.commitment_hold_ids
        ]
    # reality-rule: fulfillment_readiness._blocker_links.guard-167
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
    """
    What stock stands behind a promise, and how much of it is ready (spec 303).

    The promise's own location counts with all it holds, as it always has; a
    reservation at another location counts only with what that location still
    holds of it. The second figure is what could ship now: at every location,
    the reserved quantity that is physically there. With every reservation at
    home both are what they were before: the own location's stock, and the
    smaller of reserved and stock.

    BUSINESS PURPOSE:
    Calculate stock backing a delivery promise and its quantity ready to ship across reservation locations.

    BUSINESS RULE readiness.stock_cover.home:
    Count all physical stock reported for the promise's own warehouse as its initial stock basis. Ready quantity there is the smaller of its active reserved quantity and that physical stock.

    BUSINESS RULE fulfillment_readiness.stock_cover.guard-192:
    IF a reservation belongs to the promise's own warehouse, skip it here because that warehouse was already counted.

    BUSINESS RULE readiness.stock_cover.other:
    For every other reservation warehouse, add only the smaller of reserved quantity and physical stock to both the stock basis and ready quantity. Return both totals.
    """
    # A promise without a warehouse reads what the reader reads for "no
    # location", exactly as before.
    # reality-rule: readiness.stock_cover.home
    own = physical_at(own_location_id)
    basis = own
    ready = min(reserved_by_location.get(own_location_id or "", ZERO), own)
    for location_id, reserved in reserved_by_location.items():
        # reality-rule: fulfillment_readiness.stock_cover.guard-192
        if location_id == own_location_id:
            continue
        # reality-rule: readiness.stock_cover.other
        here = min(reserved, physical_at(location_id))
        basis += here
        ready += here
    return basis, ready


def ready_by_location(
    own_location_id: str | None,
    reserved_by_location: dict[str, Decimal],
    physical_at: Callable[[str | None], Decimal],
) -> dict[str, Decimal]:
    """
    What could ship now from each warehouse: reserved there and on hand there.

    The parts add up to the ready quantity of `stock_cover`, so a person can
    prepare one shipment per warehouse for exactly what the promise shows as
    ready (spec 303).

    BUSINESS PURPOSE:
    Show how much of this promise can ship from each warehouse with a reservation.

    BUSINESS RULE readiness.ready_by_location.quantities:
    For each reservation warehouse, ready quantity is the smaller of its reserved quantity and physical stock reported there. Return only warehouses with a positive ready quantity; no reservation is moved or created.
    """
    # reality-rule: readiness.ready_by_location.quantities
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
    _inputs: dict | None = None,
) -> FulfillmentReadiness:
    """
    Derive payment readiness for one customer-delivery commitment.

    Amounts are stated document and allocation values. This function never creates
    payment or fulfillment authority and never infers policy from a term label.

    BUSINESS PURPOSE:
    Derive whether a customer delivery can ship from held reservations, unblocked stock, delivery policy and qualifying prepayment evidence. This read creates no shipment or payment.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-237:
    IF the commitment is absent from this company, refuse with fulfillment_commitment_not_found.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-239:
    IF the commitment is not a customer delivery, refuse with fulfillment_readiness_customer_commitment_required.

    BUSINESS RULE readiness.open_quantity:
    Open delivery quantity is revised commitment quantity minus qualifying shipped quantity, with a minimum of zero.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-249:
    IF a proposed shipment quantity is zero, negative or greater than the open quantity, refuse with fulfillment_shipment_quantity_invalid. Without a proposal, check the whole open quantity.

    BUSINESS RULE readiness.reservations:
    Read this company's active reservations for this commitment, summing quantities separately for each warehouse.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-276:
    IF a departure warehouse is supplied, use only its reservation and physical stock less stock blocks; ready quantity is their smaller value. ELSE combine reservation quantities and the shared stock-cover calculation across warehouses.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-305:
    IF the commitment has active holds, report commitment_hold.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-307:
    IF the customer has an active delivery hold, report party_delivery_hold.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-309:
    IF reserved quantity is below the checked delivery quantity, report insufficient_reservation.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-311:
    IF stock backing the promise is below the checked quantity, or total reservation is sufficient but ready quantity at those warehouses is insufficient, report insufficient_stock.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-315:
    IF no order is linked, return only operational readiness: a positive open quantity and no operational blockers are required; no prepayment policy is inferred.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-341:
    IF the linked document is absent from this company or is not a sales order, refuse with customer_delivery_order_not_found.

    BUSINESS RULE readiness.delivery_policy:
    When delivery-policy checking is enabled, use the shared ship-complete check. IF it fails, report ship_complete_incomplete.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-354:
    IF no payment term requires prepayment, return operational readiness without a payment blocker. The stated order gross amount is shown; no received payment is claimed by this branch.

    BUSINESS RULE readiness.invoice_candidates:
    Find sales invoices for this company, the order's customer and currency, linked through billed order lines. Include the order's down-payment invoices through their shared service.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-436:
    IF an invoice also bills an order of another customer or currency, mark payment attribution ambiguous; no allocation is counted automatically.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-441:
    ELSE IF an invoice also bills another order of the same customer and currency, treat it as consolidated.

    BUSINESS RULE readiness.qualifying_allocations:
    Count active settlement allocations only for candidate receivable entries and payment entries of this company, customer and currency. Exclude consolidated invoice entries from this direct sum, and count nothing if attribution is ambiguous.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-494:
    IF a consolidated invoice is still open, retain its identity, number and open amount as a blocker. ELSE add its stated line amounts for this order, subtracting live offsets of this order's down payments to avoid counting those amounts twice.

    BUSINESS RULE readiness.remaining_payment:
    Remaining prepayment is stated order gross amount minus qualifying received amount, with a minimum of zero.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-526:
    IF no candidate receivable invoice entries exist, report prepayment_invoice_missing.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-528:
    IF attribution is ambiguous, report prepayment_attribution_ambiguous.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-530:
    IF a consolidated invoice remains open, report prepayment_consolidated_invoice_open.

    BUSINESS RULE fulfillment_readiness.fulfillment_readiness.guard-532:
    IF required prepayment remains positive, report prepayment_required.

    BUSINESS RULE readiness.unstated_prepayment:
    IF prepayment is required and the order source states no gross amount, retain unknown required and remaining amounts and block shipment; never infer an amount from quantity and price.

    BUSINESS RULE readiness.prepayment_release:
    IF the order is not (fully) paid and a company owner released its prepayment for at least the order's stated gross amount, drop prepayment_required and prepayment_invoice_missing and name the release. An invoice shared with other orders still blocks. An order raised past the released amount is blocked again.

    BUSINESS RULE readiness.result:
    Return quantities, payment amounts, invoice/allocation identities, active hold identities and consolidated invoice evidence. Ship-ready requires positive open quantity and no blockers.
    """
    commitment = (
        _inputs["commitments"].get(commitment_id)
        if _inputs
        else session.scalar(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
            )
        )
    )
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-237
    if commitment is None:
        raise InvalidOperation(code="fulfillment_commitment_not_found")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-239
    if commitment.type != "customer_delivery":
        raise InvalidOperation(
            code="fulfillment_readiness_customer_commitment_required"
        )
    # reality-rule: readiness.open_quantity
    open_quantity = (
        _inputs["terms"][commitment.id].open
        if _inputs
        else max(
            commitment_quantity(session, tenant_id, commitment.id)
            - movement_quantity(session, tenant_id, commitment.id, "shipment"),
            ZERO,
        )
    )
    checked_quantity = open_quantity if proposed_quantity is None else proposed_quantity
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-249
    if proposed_quantity is not None and (
        checked_quantity <= ZERO or checked_quantity > open_quantity
    ):
        raise InvalidOperation(code="fulfillment_shipment_quantity_invalid")
    # reality-rule: readiness.reservations
    reserved_by_location = (
        _inputs["reservations"].get(commitment.id, {})
        if _inputs
        else {
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
    )

    def physical_at(location_id: str | None) -> Decimal:
        # Spec 304: blocked stock never ships, so it is not stock behind a
        # promise either.
        if _inputs:
            if not commitment.item_id:
                return ZERO
            if location_id and location_id not in _inputs["locations"]:
                from reality.services.core import NotFound

                raise NotFound(code="record_not_found", values={"record": "Location"})
            return _inputs["stock"].get(
                (commitment.item_id, location_id), ZERO
            ) - _inputs["blocked"].get((commitment.item_id, location_id), ZERO)
        return (
            stock_at(session, tenant_id, commitment.item_id, location_id)
            - blocked_quantity(session, tenant_id, commitment.item_id, location_id)
            if commitment.item_id
            else ZERO
        )

    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-276
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
    commitment_hold_ids = (
        _inputs["holds"].get(commitment.id, ())
        if _inputs
        else tuple(
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
    )
    party_hold = (
        (
            _inputs["party_holds"].get(commitment.to_party_id)
            if _inputs
            else active_party_delivery_hold(session, tenant_id, commitment.to_party_id)
        )
        if commitment.to_party_id
        else None
    )
    party_hold_ids = (party_hold.id,) if party_hold else ()
    operational_blockers: list[str] = []
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-305
    if commitment_hold_ids:
        operational_blockers.append("commitment_hold")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-307
    if party_hold_ids:
        operational_blockers.append("party_delivery_hold")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-309
    if reserved_quantity < checked_quantity:
        operational_blockers.append("insufficient_reservation")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-311
    if physical_quantity < checked_quantity or (
        reserved_quantity >= checked_quantity > ready_quantity
    ):
        operational_blockers.append("insufficient_stock")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-315
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
    order = (
        _inputs["orders"].get(commitment.document_id)
        if _inputs
        else session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.id == commitment.document_id,
            )
        )
    )
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-341
    if order is None or order.type != "sales_order":
        raise InvalidOperation(code="customer_delivery_order_not_found")
    # reality-rule: readiness.delivery_policy
    if _delivery_rule:
        # Spec 306: under ship complete a line is ready only with the whole
        # order, every open line in full.
        from reality.services.delivery_rules import order_ships_complete

        if not order_ships_complete(
            session,
            tenant_id,
            order.id,
            commitment.id,
            checked_quantity,
            open_quantity,
            _effective_rule=_inputs["rules"][order.id] if _inputs else None,
        ):
            operational_blockers.append("ship_complete_incomplete")
    term = (
        (
            _inputs["payment_terms"].get(order.payment_term_id)
            if _inputs
            else session.scalar(
                select(PaymentTerm).where(
                    PaymentTerm.tenant_id == tenant_id,
                    PaymentTerm.id == order.payment_term_id,
                )
            )
        )
        if order.payment_term_id
        else None
    )
    required = Decimal(order.gross_amount) if order.gross_amount is not None else None
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-354
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

    # reality-rule: readiness.unstated_prepayment
    if required is None:
        return FulfillmentReadiness(
            commitment.id,
            order.id,
            False,
            (*operational_blockers, "prepayment_amount_unstated"),
            order.currency,
            None,
            ZERO,
            None,
            order.payment_term_id,
            True,
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
    # reality-rule: readiness.invoice_candidates
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
        # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-436
        if any(
            (party, currency) != (order.party_id, order.currency)
            for party, currency, _ in billed_orders
        ):
            ambiguous = True
        # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-441
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
    # reality-rule: readiness.qualifying_allocations
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
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-487
    if not ambiguous:
        for invoice in session.scalars(
            select(Document)
            .where(Document.tenant_id == tenant_id, Document.id.in_(consolidated))
            .order_by(Document.number, Document.id)
        ):
            open_amount = open_invoice_amount(session, tenant_id, invoice.id)
            # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-494
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
    # reality-rule: readiness.remaining_payment
    remaining = max(required - received, ZERO)
    blockers = list(operational_blockers)
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-526
    if not invoice_ids:
        blockers.append("prepayment_invoice_missing")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-528
    if ambiguous:
        blockers.append("prepayment_attribution_ambiguous")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-530
    if consolidated_open:
        blockers.append("prepayment_consolidated_invoice_open")
    # reality-rule: fulfillment_readiness.fulfillment_readiness.guard-532
    if remaining > ZERO:
        blockers.append("prepayment_required")
    release_id = None
    # reality-rule: readiness.prepayment_release
    if {"prepayment_required", "prepayment_invoice_missing"} & set(blockers):
        release_id = covering_prepayment_release(session, tenant_id, order.id, required)
        if release_id:
            blockers = [code for code in blockers if code not in RELEASABLE_BLOCKERS]
    # reality-rule: readiness.result
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
        release_id,
    )


#: What an owner's prepayment release lifts: the order is not (fully) paid. An
#: invoice that also bills other orders stays a blocker, because it leaves open
#: what was paid for this one (spec 347).
RELEASABLE_BLOCKERS = frozenset({"prepayment_required", "prepayment_invoice_missing"})


def covering_prepayment_release(
    session: Session, tenant_id: str, order_id: str, required: Decimal
) -> str | None:
    """The owner's release that still covers this order's stated amount (spec 347).

    A release covers the order's gross amount as it stood when the owner decided;
    an order raised past it, by a larger quantity or a new line, asks again.
    """
    from reality.db.core import PrepaymentRelease

    return session.scalar(
        select(PrepaymentRelease.id)
        .where(
            PrepaymentRelease.tenant_id == tenant_id,
            PrepaymentRelease.document_id == order_id,
            PrepaymentRelease.covered_amount >= required,
        )
        .order_by(PrepaymentRelease.created_at.desc(), PrepaymentRelease.id)
        .limit(1)
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
    # reality-rule: fulfillment_readiness.require_paid_prepayment.guard-580
    if movement_type != "shipment" or not commitment_id:
        return
    kind = session.scalar(
        select(Commitment.type).where(
            Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
        )
    )
    # reality-rule: fulfillment_readiness.require_paid_prepayment.guard-587
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
    # reality-rule: fulfillment_readiness.require_paid_prepayment.guard-593
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


def fulfillment_readiness_batch(
    session: Session,
    tenant_id: str,
    dispatch_locations: dict[str, str | None],
    *,
    _terms: dict | None = None,
    _commitments: dict | None = None,
    _orders: dict | None = None,
) -> dict[str, FulfillmentReadiness]:
    """
    BUSINESS PURPOSE:
    Reuse exact canonical readiness for a complete dispatch cohort with grouped
    snapshot inputs instead of repeating stable quantity/stock/hold/policy reads.

    BUSINESS RULE readiness.batch.shared:
    Restrict every input to the requested company and its commitments; preload
    canonical terms, recorded physical stock and open-block quantities. No input
    or result survives this call. Every result still runs fulfillment_readiness,
    including complete-order and qualifying prepayment rules.
    """
    from collections import defaultdict

    from reality.services import core, delivery_rules

    # reality-rule: readiness.batch.shared
    ids = set(dispatch_locations)
    if not ids:
        return {}
    narrow = bool(session.info.get("operations_snapshot_consistent"))
    commitment_query = select(
        *(
            Commitment.id,
            Commitment.tenant_id,
            Commitment.type,
            Commitment.document_id,
            Commitment.item_id,
            Commitment.location_id,
            Commitment.to_party_id,
            Commitment.currency,
        )
        if narrow
        else (Commitment,)
    ).where(Commitment.tenant_id == tenant_id, core._id_cohort(Commitment.id, ids))
    commitments = (
        {
            identity: row
            for identity, row in _commitments.items()
            if identity in ids and row.id == identity and row.tenant_id == tenant_id
        }
        if narrow and _commitments is not None
        else {
            row.id: row
            for row in (
                core._metadata_rows(session.execute(commitment_query))
                if narrow
                else session.scalars(commitment_query)
            )
        }
    )
    if len(commitments) != len(ids):
        raise InvalidOperation(code="fulfillment_commitment_not_found")
    order_query = select(
        *(
            Document.id,
            Document.tenant_id,
            Document.type,
            Document.party_id,
            Document.payment_term_id,
            Document.gross_amount,
            Document.currency,
        )
        if narrow
        else (Document,)
    ).where(
        Document.tenant_id == tenant_id,
        core._id_cohort(Document.id, {row.document_id for row in commitments.values()}),
    )
    document_ids = {row.document_id for row in commitments.values()}
    orders = (
        {
            identity: row
            for identity, row in _orders.items()
            if identity in document_ids
            and row.id == identity
            and row.tenant_id == tenant_id
        }
        if narrow and _orders is not None
        else {
            row.id: row
            for row in (
                core._metadata_rows(session.execute(order_query))
                if narrow
                else session.scalars(order_query)
            )
        }
    )
    reservations = defaultdict(dict)
    for identity, location, amount in session.execute(
        select(
            Reservation.commitment_id,
            Reservation.location_id,
            func.sum(Reservation.quantity),
        )
        .where(
            Reservation.tenant_id == tenant_id,
            core._id_cohort(Reservation.commitment_id, ids),
            Reservation.status == "active",
        )
        .group_by(Reservation.commitment_id, Reservation.location_id)
    ):
        reservations[identity][location] = Decimal(amount)
    items = {row.item_id for row in commitments.values() if row.item_id}
    stock = core._physical_stock_by_location(session, tenant_id, items)
    blocks = core._open_stock_blocks(tenant_id)
    blocked = defaultdict(lambda: ZERO)
    for item, location, amount in session.execute(
        select(blocks.c.item_id, blocks.c.location_id, func.sum(blocks.c.quantity))
        .where(blocks.c.item_id.in_(items))
        .group_by(blocks.c.item_id, blocks.c.location_id)
    ):
        if location is not None:
            blocked[item, location] += Decimal(amount)
        blocked[item, None] += Decimal(amount)
    holds = defaultdict(list)
    for identity, hold in session.execute(
        select(CommitmentHold.commitment_id, CommitmentHold.id)
        .where(
            CommitmentHold.tenant_id == tenant_id,
            core._id_cohort(CommitmentHold.commitment_id, ids),
            CommitmentHold.released_at.is_(None),
        )
        .order_by(CommitmentHold.id)
    ):
        holds[identity].append(hold)
    party_holds = {}
    for hold in session.scalars(
        select(PartyHold)
        .where(
            PartyHold.tenant_id == tenant_id,
            PartyHold.party_id.in_({row.to_party_id for row in commitments.values()}),
            PartyHold.hold_type == "delivery",
            PartyHold.released_at.is_(None),
        )
        .order_by(PartyHold.created_at.desc())
    ):
        party_holds.setdefault(hold.party_id, hold)
    inputs = {
        "commitments": commitments,
        "orders": orders,
        "terms": _terms
        if _terms is not None
        else core.commitment_terms(session, tenant_id, ids),
        "reservations": reservations,
        "stock": stock,
        "blocked": blocked,
        "holds": {identity: tuple(value) for identity, value in holds.items()},
        "party_holds": party_holds,
        "rules": delivery_rules.effective_rules(
            session, tenant_id, list(orders), _orders=orders if narrow else None
        ),
        "payment_terms": {
            row.id: row
            for row in session.scalars(
                select(PaymentTerm).where(
                    PaymentTerm.tenant_id == tenant_id,
                    PaymentTerm.id.in_(
                        {row.payment_term_id for row in orders.values()}
                    ),
                )
            )
        },
        "locations": set(
            session.scalars(
                select(Location.id).where(
                    Location.tenant_id == tenant_id,
                    Location.id.in_(
                        {
                            *dispatch_locations.values(),
                            *(
                                location
                                for locations in reservations.values()
                                for location in locations
                            ),
                        }
                    ),
                )
            )
        ),
    }
    return {
        identity: fulfillment_readiness(
            session, tenant_id, identity, from_location_id=location, _inputs=inputs
        )
        for identity, location in dispatch_locations.items()
    }
