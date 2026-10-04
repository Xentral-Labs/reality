"""Later Shopify order versions: apply reductions of unshipped quantity, hold the rest (spec 296).

A version is compared with the order's current Reality, not with the previous
payload, so a replayed version asks for what already holds and a version that
arrives after a person's revision does not undo it. Only reductions of open,
unshipped quantity are applied, through the same revision and cancellation
services a person uses; everything else waits for review with a coded reason.
A version is applied completely or not at all.
"""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    InterpretationOutcome,
    Reservation,
    SourceRecord,
    SourceStream,
)
from reality.services import core

#: Reason codes a held version can carry, in the order a summary names them.
HELD_CODES = (
    "cancelled_after_shipment",
    "reduces_shipped_quantity",
    "quantity_increased",
    "line_added",
    "price_changed",
    "address_changed",
    "currency_changed",
    "closed_line_changed",
    "reservation_choice_required",
    "unassigned_line_changed",
)
SEVERAL_CODES = "shopify_changes_require_review"


@dataclass
class VersionPlan:
    """What one version would do: operations to apply, or codes that hold it."""

    revisions: list[tuple[Commitment, Decimal]] = field(default_factory=list)
    cancellations: list[Commitment] = field(default_factory=list)
    held: list[tuple[str, str]] = field(default_factory=list)
    cancel_reason: str = ""

    @property
    def reason_code(self) -> str:
        codes = {code for code, _ in self.held}
        return next(iter(codes)) if len(codes) == 1 else SEVERAL_CODES

    @property
    def summary(self) -> str:
        parts = [
            f"{code} (line {line})" if line else code
            for code in HELD_CODES
            for held_code, line in self.held
            if held_code == code
        ]
        next_step = (
            " Next step: confirm a return announcement (return_announce) for what shipped."
            if any(code == "cancelled_after_shipment" for code, _ in self.held)
            else ""
        )
        return (
            "Shopify change not applied: "
            + ", ".join(parts)
            + "."
            + next_step
            + " Only reductions of unshipped quantity apply automatically; "
            "the order is unchanged."
        )


def stated_lines(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Each line the version states, by Shopify line id, with its current quantity.

    Shopify lowers `current_quantity` on an edit or a cancelling refund and keeps
    `quantity` as ordered; older payloads carry `quantity` alone.
    """
    lines = {}
    for raw in payload.get("line_items") or []:
        quantity = raw.get("current_quantity", raw.get("quantity"))
        lines[str(raw.get("id"))] = {
            "quantity": core.decimal(quantity if quantity is not None else 0),
            "price": core.decimal(raw["price"])
            if raw.get("price") is not None
            else None,
            "sku": str(raw.get("sku", "")),
        }
    return lines


def order_for_source(
    session: Session, tenant_id: str, source: SourceRecord
) -> Document | None:
    """The sales order an earlier version of the same Shopify order became."""
    versions = select(SourceRecord.id).where(
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == source.source_system,
        SourceRecord.source_type == source.source_type,
        SourceRecord.external_id == source.external_id,
    )
    return session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.type == "sales_order",
            Document.source_record_id.in_(versions),
        )
    )


def is_current_version(session: Session, tenant_id: str, source: SourceRecord) -> bool:
    """Whether this version is still the one the shop's order stands on."""
    current = session.scalar(
        select(SourceStream.current_source_record_id).where(
            SourceStream.tenant_id == tenant_id,
            SourceStream.source_system == source.source_system,
            SourceStream.source_type == source.source_type,
            SourceStream.external_id == source.external_id,
        )
    )
    return current in {None, source.id}


#: Fields Shopify adds to an address by itself (geocoding) rather than the customer.
_DERIVED_ADDRESS_FIELDS = {"latitude", "longitude"}
#: Refund restock types for goods that had shipped; they do not reduce the promise.
_SHIPPED_RESTOCK_TYPES = {"return", "no_restock", "legacy_restock"}


def _address(payload: dict[str, Any]) -> Any:
    address = payload.get("shipping_address") or None
    if isinstance(address, dict):
        return {
            key: value
            for key, value in address.items()
            if key not in _DERIVED_ADDRESS_FIELDS
        } or None
    return address


def _previous_payload(
    session: Session, tenant_id: str, source: SourceRecord
) -> dict[str, Any]:
    """What the shop stated just before this version, held or not.

    A change is reviewed once, when it appears; comparing every later version with
    the first one would hold them all for the same reviewed difference.
    """
    previous = None
    if source.supersedes_source_record_id:
        previous = session.get(
            SourceRecord, (tenant_id, source.supersedes_source_record_id)
        )
    if previous is None:
        previous = session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == source.source_system,
                SourceRecord.source_type == source.source_type,
                SourceRecord.external_id == source.external_id,
                SourceRecord.version < source.version,
            )
            .order_by(SourceRecord.version.desc())
        ).first()
    return json.loads(previous.payload) if previous else {}


def _shipped_refunds(payload: dict[str, Any]) -> dict[str, Decimal]:
    """Per line, the refunded quantity of goods that had shipped (not a reduction)."""
    refunded: dict[str, Decimal] = {}
    for refund in payload.get("refunds") or []:
        for entry in (refund or {}).get("refund_line_items") or []:
            if entry.get("restock_type") in _SHIPPED_RESTOCK_TYPES:
                line_id = str(entry.get("line_item_id"))
                refunded[line_id] = refunded.get(line_id, Decimal(0)) + core.decimal(
                    entry.get("quantity") or 0
                )
    return refunded


def already_applied(session: Session, tenant_id: str, source: SourceRecord) -> bool:
    """Whether this version was interpreted before: it is never applied twice."""
    return (
        session.scalar(
            select(InterpretationOutcome.id).where(
                InterpretationOutcome.tenant_id == tenant_id,
                InterpretationOutcome.source_record_id == source.id,
                InterpretationOutcome.classification == "interpreted",
            )
        )
        is not None
    )


def _needs_reservation_choice(
    session: Session, tenant_id: str, commitment: Commitment, target: Decimal, shipped
) -> bool:
    """Mirror of `revise_commitment`'s refusal, asked before anything is applied."""
    active = list(
        session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
    )
    revised_open = max(Decimal(0), target - shipped)
    allocated = sum((core.decimal(row.quantity) for row in active), Decimal(0))
    identities = {
        (row.location_id, row.handling_unit_id, row.lot_id, row.serial_unit_id)
        for row in active
    }
    return allocated > revised_open > 0 and len(identities) > 1


def classify_order_version(
    session: Session,
    tenant_id: str,
    order: Document,
    payload: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> VersionPlan:
    """What a later version asks of the order's current Reality.

    Quantities are compared with Reality; stated fields Reality does not hold
    (address, price, an unassigned line) with the version before, so a change is
    held once, when it appears, and does not block every later version.
    """
    plan = VersionPlan()
    previous = previous or {}
    lines = list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == order.id,
            )
            .order_by(DocumentLine.source_line_id, DocumentLine.id)
        )
    )
    promises = {
        commitment.document_line_id: commitment
        for commitment in session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_line_id.in_([line.id for line in lines]),
                Commitment.type == "customer_delivery",
            )
        )
    }
    shipped = {
        commitment.id: core.fulfilled_quantity(session, tenant_id, commitment.id)
        for commitment in promises.values()
    }
    if payload.get("cancelled_at"):
        # A cancellation decides the whole order; nothing else it carries matters.
        if any(shipped.values()):
            plan.held.append(("cancelled_after_shipment", ""))
            return plan
        plan.cancellations = [
            commitment
            for commitment in promises.values()
            if commitment.status == "open"
        ]
        reason = str(payload.get("cancel_reason") or "").strip()
        plan.cancel_reason = (
            f"Cancelled in Shopify ({reason})" if reason else "Cancelled in Shopify"
        )
        return plan
    if payload.get("currency", order.currency) != order.currency:
        plan.held.append(("currency_changed", ""))
    if previous and _address(payload) != _address(previous):
        plan.held.append(("address_changed", ""))
    stated = stated_lines(payload)
    before = stated_lines(previous) if previous else {}
    refunded_shipped = _shipped_refunds(payload)
    known = {line.source_line_id for line in lines}
    plan.held.extend(
        ("line_added", line_id) for line_id in stated if line_id not in known
    )
    for line in lines:
        line_id = line.source_line_id or ""
        target = stated.get(line_id, {"quantity": Decimal(0)})["quantity"]
        prior_price = before[line_id]["price"] if line_id in before else line.unit_price
        if line_id in stated and stated[line_id]["price"] != prior_price:
            plan.held.append(("price_changed", line_id))
        commitment = promises.get(line.id)
        if commitment is None:
            prior_quantity = (
                before[line_id]["quantity"]
                if line_id in before
                else core.decimal(line.quantity)
            )
            if target != prior_quantity:
                plan.held.append(("unassigned_line_changed", line_id))
            continue
        fulfilled = shipped[commitment.id]
        if (
            target < fulfilled
            and target + refunded_shipped.get(line_id, 0) >= fulfilled
        ):
            # Shipped goods refunded afterwards: the promise was kept all the same.
            target = fulfilled
        current = core.commitment_quantity(session, tenant_id, commitment.id)
        if target == current or (commitment.status == "cancelled" and target == 0):
            # A cancelled line the shop still leaves out already says the same.
            continue
        if commitment.status == "fulfilled" and target == fulfilled:
            continue
        if commitment.status != "open":
            plan.held.append(("closed_line_changed", line_id))
        elif target > current:
            plan.held.append(("quantity_increased", line_id))
        elif target < fulfilled:
            plan.held.append(("reduces_shipped_quantity", line_id))
        elif target == 0:
            plan.cancellations.append(commitment)
        elif _needs_reservation_choice(
            session, tenant_id, commitment, target, fulfilled
        ):
            plan.held.append(("reservation_choice_required", line_id))
        else:
            plan.revisions.append((commitment, target))
    if not plan.cancel_reason:
        plan.cancel_reason = "Removed from the order in Shopify"
    return plan


def apply_order_version(
    session: Session, tenant_id: str, source: SourceRecord, order: Document
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Commitment]]:
    """Retired writer: prepare and confirm the canonical intake proposal instead."""
    raise core.InvalidOperation(code="intake_approval_required")
