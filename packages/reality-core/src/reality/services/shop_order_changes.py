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
            "price": core.decimal(raw.get("price", 0)),
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


def _address(payload: dict[str, Any]) -> Any:
    return payload.get("shipping_address") or None


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
) -> VersionPlan:
    """What a later version asks of the order's current Reality."""
    plan = VersionPlan()
    original = core._tenant_record(
        session, SourceRecord, tenant_id, order.source_record_id
    )
    original_payload = json.loads(original.payload)
    if payload.get("currency", order.currency) != order.currency:
        plan.held.append(("currency_changed", ""))
    if _address(payload) != _address(original_payload):
        plan.held.append(("address_changed", ""))
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
                Commitment.document_id == order.id,
                Commitment.type == "customer_delivery",
            )
        )
    }
    stated = stated_lines(payload)
    known = {line.source_line_id for line in lines}
    plan.held.extend(
        ("line_added", line_id) for line_id in stated if line_id not in known
    )
    cancelled = bool(payload.get("cancelled_at"))
    shipped = {
        commitment.id: core.fulfilled_quantity(session, tenant_id, commitment.id)
        for commitment in promises.values()
    }
    if cancelled:
        if any(shipped.values()):
            plan.held.append(("cancelled_after_shipment", ""))
        else:
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
    for line in lines:
        line_id = line.source_line_id or ""
        target = stated.get(line_id, {"quantity": Decimal(0)})["quantity"]
        if line_id in stated and stated[line_id]["price"] != core.decimal(
            line.unit_price
        ):
            plan.held.append(("price_changed", line_id))
        commitment = promises.get(line.id)
        if commitment is None:
            if target != core.decimal(line.quantity):
                plan.held.append(("unassigned_line_changed", line_id))
            continue
        current = core.commitment_quantity(session, tenant_id, commitment.id)
        if target == current:
            continue
        if commitment.status != "open":
            plan.held.append(("closed_line_changed", line_id))
        elif target > current:
            plan.held.append(("quantity_increased", line_id))
        elif target < shipped[commitment.id]:
            plan.held.append(("reduces_shipped_quantity", line_id))
        elif target == 0:
            plan.cancellations.append(commitment)
        elif _needs_reservation_choice(
            session, tenant_id, commitment, target, shipped[commitment.id]
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
    """Apply a later version's reductions, or raise to hold it with its codes.

    Callers own the transaction: nothing here commits, and a held version raises
    before anything was changed.
    """
    if not is_current_version(session, tenant_id, source):
        # A newer version already stands for the order and states all of it.
        return source, order, [], []
    payload = json.loads(source.payload)
    plan = classify_order_version(session, tenant_id, order, payload)
    if plan.held:
        raise core.ShopifyUpdateNeedsReview(
            codes=[code for code, _ in plan.held],
            reason_code=plan.reason_code,
            summary=plan.summary,
        )
    changed: list[Commitment] = []
    for commitment, quantity in plan.revisions:
        core.revise_commitment(
            session,
            tenant_id,
            commitment.id,
            quantity=quantity,
            note="Quantity lowered in Shopify",
            source_record_id=source.id,
            _commit=False,
        )
        changed.append(commitment)
    for commitment in plan.cancellations:
        core.cancel_commitment(
            session,
            tenant_id,
            commitment.id,
            reason=plan.cancel_reason,
            source_record_id=source.id,
            _commit=False,
        )
        changed.append(commitment)
    return source, order, [], changed
