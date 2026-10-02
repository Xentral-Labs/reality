"""State-bound review and verification for commitment lifecycle actions."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, ChangeProposal, CommitmentHold, Reservation
from reality.services import core

COMMITMENT_ACTION_TOOLS = {"commitment_cancel", "commitment_revise"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_commitment_action(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if tool not in COMMITMENT_ACTION_TOOLS:
        raise core.InvalidOperation(code="commitment_action_unsupported")
    if tool == "commitment_revise":
        return _review_commitment_revision(session, tenant_id, arguments)
    allowed = {"commitment_id", "reason", "source_record_id"}
    if set(arguments) - allowed or not {"commitment_id", "reason"} <= set(arguments):
        raise core.InvalidOperation(code="commitment_cancellation_fields_invalid")
    reason = str(arguments["reason"]).strip()
    if not reason:
        raise core.InvalidOperation(code="commitment_cancellation_reason_required")
    commitment = core._tenant_record(
        session, core.Commitment, tenant_id, arguments["commitment_id"]
    )
    if commitment.status != "open":
        raise core.InvalidOperation(code="commitment_cancel_not_open")
    if arguments.get("source_record_id"):
        core._tenant_record(
            session, core.SourceRecord, tenant_id, arguments["source_record_id"]
        )
    terms = core.commitment_terms(session, tenant_id, {commitment.id})[commitment.id]
    reservations = list(
        session.scalars(
            select(Reservation)
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
            .order_by(Reservation.id)
        )
    )
    holds = list(
        session.scalars(
            select(CommitmentHold)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == commitment.id,
                CommitmentHold.released_at.is_(None),
            )
            .order_by(CommitmentHold.id)
        )
    )
    intent = {
        "commitment_id": commitment.id,
        "reason": reason,
        **(
            {"source_record_id": arguments["source_record_id"]}
            if arguments.get("source_record_id")
            else {}
        ),
    }
    state = {
        "commitment_id": commitment.id,
        "status": commitment.status,
        "quantity": str(terms.quantity),
        "fulfilled": str(terms.fulfilled),
        "open": str(terms.open),
        "active_reservations": [
            {"id": row.id, "quantity": str(core.decimal(row.quantity))}
            for row in reservations
        ],
        "active_hold_ids": [row.id for row in holds],
    }
    effect = {
        "cancelled_open": str(terms.open),
        "fulfilled_retained": str(terms.fulfilled),
        "released_reservation_ids": [row.id for row in reservations],
        "released_hold_ids": [row.id for row in holds],
        "stock_changes": False,
        "document_changes": False,
    }
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "state": state,
        "effect": effect,
        "token": hashlib.sha256(
            _json([tenant_id, tool, intent, state]).encode()
        ).hexdigest(),
    }


def _review_commitment_revision(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    allowed = {
        "commitment_id",
        "due_at",
        "quantity",
        "note",
        "stated_at",
        "source_record_id",
        "retained_allocations",
        "unit_price",
    }
    if set(arguments) - allowed or "commitment_id" not in arguments:
        raise core.InvalidOperation(code="commitment_revision_fields_invalid")
    commitment = core._tenant_record(
        session, core.Commitment, tenant_id, arguments["commitment_id"]
    )
    # Spec 310: a supplier may confirm a price after delivering everything; a
    # price-only statement is the one revision a fulfilled purchase takes.
    price_only = arguments.get("unit_price") is not None and all(
        arguments.get(key) is None for key in ("due_at", "quantity")
    )
    if (
        commitment.status != "open"
        and not (price_only and commitment.status == "fulfilled")
        and not core._keeps_what_was_shipped(
            session,
            tenant_id,
            commitment,
            arguments.get("due_at"),
            arguments.get("quantity"),
            arguments.get("unit_price"),
        )
    ):
        raise core.InvalidOperation(code="commitment_revise_not_open")
    if arguments.get("source_record_id"):
        core._tenant_record(
            session, core.SourceRecord, tenant_id, arguments["source_record_id"]
        )
    stated_due = (
        core.utc_datetime(arguments["due_at"])
        if arguments.get("due_at") is not None
        else None
    )
    if arguments.get("due_at") is not None and stated_due is None:
        raise core.InvalidOperation(code="revision_date_unreadable")
    stated_quantity = (
        core.positive(arguments["quantity"], "revised quantity")
        if arguments.get("quantity") is not None
        else None
    )
    stated_price = None
    if arguments.get("unit_price") is not None:
        # Spec 310: a supplier confirms a price; a customer promise takes none.
        if commitment.type != "supplier_delivery":
            raise core.InvalidOperation(code="commitment_price_purchase_only")
        if not commitment.document_line_id:
            raise core.InvalidOperation(code="commitment_price_needs_order_line")
        try:
            stated_price = core.decimal(arguments["unit_price"])
        except (ArithmeticError, ValueError, TypeError) as error:
            raise core.InvalidOperation(code="commitment_price_invalid") from error
        if (
            stated_price < 0
            or stated_price >= Decimal(10) ** 14
            or stated_price != stated_price.quantize(Decimal("0.0001"))
        ):
            raise core.InvalidOperation(code="commitment_price_invalid")
    if stated_due is None and stated_quantity is None and stated_price is None:
        raise core.InvalidOperation(code="revision_needs_date_or_quantity")
    terms = core.commitment_terms(session, tenant_id, {commitment.id})[commitment.id]
    reservations = list(
        session.scalars(
            select(Reservation)
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
            .order_by(Reservation.reserved_at, Reservation.id)
        )
    )
    revised_open = (
        max(Decimal(0), stated_quantity - terms.fulfilled)
        if stated_quantity is not None
        else terms.open
    )
    allocated = sum((core.decimal(row.quantity) for row in reservations), Decimal(0))
    choices = [
        {
            "reservation_id": row.id,
            "quantity": str(core.decimal(row.quantity)),
            "location_id": row.location_id,
            "handling_unit_id": row.handling_unit_id,
            "lot_id": row.lot_id,
            "serial_unit_id": row.serial_unit_id,
        }
        for row in reservations
    ]
    identities = {
        (row.location_id, row.handling_unit_id, row.lot_id, row.serial_unit_id)
        for row in reservations
    }
    selection_required = allocated > revised_open > 0 and len(identities) > 1
    selected = arguments.get("retained_allocations")
    normalized_selected: list[dict[str, str]] | None = None
    if selected is not None:
        by_id = {row.id: row for row in reservations}
        normalized_selected = []
        selected_ids: set[str] = set()
        for value in selected:
            if set(value) != {"reservation_id", "quantity"}:
                raise core.InvalidOperation(code="retained_allocation_fields_invalid")
            reservation_id = str(value["reservation_id"])
            if reservation_id in selected_ids or reservation_id not in by_id:
                raise core.InvalidOperation(code="retained_allocations_not_distinct")
            selected_ids.add(reservation_id)
            quantity = core.positive(value["quantity"], "retained allocation quantity")
            if quantity > core.decimal(by_id[reservation_id].quantity):
                raise core.InvalidOperation(code="retained_allocation_exceeds_reservation")
            normalized_selected.append(
                {"reservation_id": reservation_id, "quantity": str(quantity)}
            )
        if sum(
            (Decimal(value["quantity"]) for value in normalized_selected), Decimal(0)
        ) > revised_open:
            raise core.InvalidOperation(code="retained_allocation_exceeds_open_quantity")
    intent = {
        key: value
        for key, value in arguments.items()
        if key != "retained_allocations" and value is not None
    }
    if stated_quantity is not None:
        intent["quantity"] = str(stated_quantity)
    if stated_price is not None:
        intent["unit_price"] = format(stated_price.normalize(), "f")
    if normalized_selected is not None:
        intent["retained_allocations"] = normalized_selected
    state = {
        "commitment_id": commitment.id,
        "status": commitment.status,
        "quantity": str(terms.quantity),
        "fulfilled": str(terms.fulfilled),
        "open": str(terms.open),
        "active_reserved": str(allocated),
        "eligible_retained_allocations": choices,
    }
    if stated_price is not None:
        line = core._tenant_record(
            session, core.DocumentLine, tenant_id, commitment.document_line_id
        )
        agreed = core._agreed_line_prices(session, tenant_id, [line])[line.id]
        state["price"] = {
            "unit": line.unit,
            "ordered_unit_price": (
                format(core.decimal(line.unit_price).normalize(), "f")
                if line.unit_price is not None
                else None
            ),
            "agreed_unit_price": (
                format(agreed.normalize(), "f") if agreed is not None else None
            ),
        }
    retained = (
        sum((Decimal(value["quantity"]) for value in normalized_selected), Decimal(0))
        if normalized_selected is not None
        else min(allocated, revised_open)
    )
    effect = {
        "revised_open": str(revised_open),
        "retained_reservation_quantity": str(retained),
        "released_reservation_quantity": str(max(Decimal(0), allocated - retained)),
        "selection_required": selection_required,
        **(
            {"confirmed_unit_price": format(stated_price.normalize(), "f")}
            if stated_price is not None
            else {}
        ),
        "document_changes": False,
        "movement_changes": False,
    }
    return {
        "version": 1,
        "tool": "commitment_revise",
        "intent": intent,
        "state": state,
        "effect": effect,
        "token": hashlib.sha256(
            _json([tenant_id, "commitment_revise", intent, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_commitment_action(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    unresolved = next(
        (
            proposal.id
            for proposal in session.scalars(
                select(ChangeProposal).where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.type == f"tool:{tool}",
                    ChangeProposal.status == "executing",
                    ChangeProposal.id != exclude if exclude else True,
                )
            )
            if json.loads(proposal.input).get("commitment_id")
            == arguments.get("commitment_id")
        ),
        None,
    )
    if unresolved:
        raise core.InvalidOperation(code="commitment_action_unresolved")


def commitment_action_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    tool = proposal.type.removeprefix("tool:")
    result = {
        "id": proposal.id,
        "tool": tool,
        "status": proposal.status,
        "review": review,
        "receipt": json.loads(proposal.output) if proposal.status == "executed" else None,
        "verification": "pending" if proposal.status == "proposed" else "unresolved",
        "links": [],
        "observation": None,
        "observation_error": None,
    }
    event_type = (
        "commitment.cancelled"
        if tool == "commitment_cancel"
        else "commitment.revised"
    )
    events = list(
        session.scalars(
            select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == event_type,
            )
        ).all()
    )
    event = events[0] if len(events) == 1 else None
    if event and review and event.subject_id == review["intent"]["commitment_id"]:
        payload = json.loads(event.payload)
        intent_matches = (
            payload.get("reason") == review["intent"]["reason"]
            and payload.get("released_reservation_ids")
            == review["effect"]["released_reservation_ids"]
            and payload.get("released_hold_ids")
            == review["effect"]["released_hold_ids"]
            if tool == "commitment_cancel"
            else payload.get("quantity") == review["intent"].get("quantity")
            and payload.get("unit_price") == review["intent"].get("unit_price")
            and payload.get("due_at")
            == (
                core.utc_datetime(review["intent"]["due_at"]).isoformat()
                if review["intent"].get("due_at")
                else None
            )
        )
        receipt = (
            {"commitment_id": event.subject_id, "event_id": event.id}
            if tool == "commitment_cancel"
            else {
                "records": [
                    {
                        "family": "commitment_revision",
                        "id": payload["commitment_revision_id"],
                    }
                ]
            }
        )
        if intent_matches and (
            proposal.status != "executed" or result["receipt"] == receipt
        ):
            commitment = core._tenant_record(
                session, core.Commitment, tenant_id, event.subject_id
            )
            result.update(
                verification="verified" if proposal.status == "executed" else "recorded_unsettled",
                recorded_receipt=receipt,
                links=[
                    {"kind": "commitment", "id": commitment.id},
                    {"kind": "business_event", "id": event.id},
                    *(
                        [
                            {
                                "kind": "commitment_revision",
                                "id": payload["commitment_revision_id"],
                            }
                        ]
                        if tool == "commitment_revise"
                        else []
                    ),
                ],
                observation=(
                    {
                        "commitment_id": commitment.id,
                        "status": commitment.status,
                    }
                    if tool == "commitment_cancel"
                    else {
                        "commitment_id": commitment.id,
                        "status": commitment.status,
                        "quantity": str(
                            core.commitment_quantity(session, tenant_id, commitment.id)
                        ),
                        "open": str(
                            core.open_quantity(session, tenant_id, commitment.id)
                        ),
                    }
                ),
            )
    result["lifecycle"] = proposal.status
    result["recorded_effect"] = result.get("recorded_receipt")
    result["current_observation"] = result["observation"]
    if proposal.status == "proposed":
        result["remaining_work"] = ["Confirm the unchanged reviewed action."]
        result["safe_next_action"] = "confirm"
    elif result["verification"] == "recorded_unsettled":
        result["remaining_work"] = [
            "Settle the proposal receipt from the exact recorded effect."
        ]
        result["safe_next_action"] = "reconcile"
    elif result["verification"] == "verified":
        result["remaining_work"] = []
        result["safe_next_action"] = "none"
    else:
        result["remaining_work"] = [
            "Reconcile exact tenant, proposal, and intent evidence; do not retry blindly."
        ]
        result["safe_next_action"] = "reconcile"
    return result
