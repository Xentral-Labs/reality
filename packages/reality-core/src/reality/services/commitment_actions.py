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
        raise core.InvalidOperation("Unsupported commitment action.")
    if tool == "commitment_revise":
        return _review_commitment_revision(session, tenant_id, arguments)
    allowed = {"commitment_id", "reason", "source_record_id"}
    if set(arguments) - allowed or not {"commitment_id", "reason"} <= set(arguments):
        raise core.InvalidOperation("Commitment cancellation fields are incomplete or unsupported.")
    reason = str(arguments["reason"]).strip()
    if not reason:
        raise core.InvalidOperation("Commitment cancellation reason is required.")
    commitment = core._tenant_record(
        session, core.Commitment, tenant_id, arguments["commitment_id"]
    )
    if commitment.status != "open":
        raise core.InvalidOperation("Only an open commitment can be cancelled.")
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
    }
    if set(arguments) - allowed or "commitment_id" not in arguments:
        raise core.InvalidOperation("Commitment revision fields are incomplete or unsupported.")
    commitment = core._tenant_record(
        session, core.Commitment, tenant_id, arguments["commitment_id"]
    )
    if commitment.status != "open":
        raise core.InvalidOperation("Only an open commitment can be revised.")
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
        raise core.InvalidOperation("A revision must state a readable date.")
    stated_quantity = (
        core.positive(arguments["quantity"], "revised quantity")
        if arguments.get("quantity") is not None
        else None
    )
    if stated_due is None and stated_quantity is None:
        raise core.InvalidOperation("A revision must restate a date, a quantity, or both.")
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
                raise core.InvalidOperation(
                    "Each retained allocation must name only reservation_id and quantity."
                )
            reservation_id = str(value["reservation_id"])
            if reservation_id in selected_ids or reservation_id not in by_id:
                raise core.InvalidOperation(
                    "Retained allocations must name distinct active reservations for this commitment."
                )
            selected_ids.add(reservation_id)
            quantity = core.positive(value["quantity"], "retained allocation quantity")
            if quantity > core.decimal(by_id[reservation_id].quantity):
                raise core.InvalidOperation(
                    "A retained allocation cannot exceed its active reservation."
                )
            normalized_selected.append(
                {"reservation_id": reservation_id, "quantity": str(quantity)}
            )
        if sum(
            (Decimal(value["quantity"]) for value in normalized_selected), Decimal(0)
        ) > revised_open:
            raise core.InvalidOperation(
                "Retained allocation total cannot exceed revised open quantity."
            )
    intent = {
        key: value
        for key, value in arguments.items()
        if key != "retained_allocations" and value is not None
    }
    if stated_quantity is not None:
        intent["quantity"] = str(stated_quantity)
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
        raise core.InvalidOperation(
            "An earlier action for this commitment is unresolved. Check its outcome first."
        )


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
