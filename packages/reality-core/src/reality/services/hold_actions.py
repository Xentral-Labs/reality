"""Exact hold snapshots and attributable delivery action receipts."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, ChangeProposal, CommitmentHold
from reality.services.core import InvalidOperation, _validate_commitment_hold

HOLD_TOOLS = {"commitment_hold", "commitment_hold_release"}


def snapshot(hold: CommitmentHold) -> dict[str, Any]:
    return {
        "id": hold.id,
        "commitment_id": hold.commitment_id,
        "reason_code": hold.reason_code,
        "note": hold.note,
        "created_by": hold.created_by,
        "created_at": str(hold.created_at),
    }


def review_hold(
    session: Session, tenant_id: str, tool: str, intent: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    cid = str(intent.get("commitment_id", ""))
    holds = list(
        session.scalars(
            select(CommitmentHold)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == cid,
                CommitmentHold.released_at.is_(None),
            )
            .order_by(CommitmentHold.id)
            .execution_options(populate_existing=True)
        )
    )
    if tool == "commitment_hold":
        _validate_commitment_hold(
            session, tenant_id, cid, intent.get("reason_code", "")
        )
        if holds:
            raise InvalidOperation(
                "This delivery is already on hold. Prepare a fresh review."
            )
        note = intent.get("note", "")
        if not isinstance(note, str):
            raise InvalidOperation("A hold note must be text.")
        intent["note"] = note.strip()
        effect = {"holds_set": "1"}
    else:
        if not holds:
            raise InvalidOperation(
                "This delivery has no active own hold. Prepare a fresh review."
            )
        effect = {"holds_released": str(len(holds))}
    return [snapshot(hold) for hold in holds], effect


def hold_receipt(event: BusinessEvent) -> dict[str, Any]:
    payload = json.loads(event.payload)
    ids = (
        [payload["hold_id"]]
        if event.event_type == "commitment.held"
        else payload["hold_ids"]
    )
    return {
        "records": [{"family": "commitment_hold", "id": identity} for identity in ids]
    }


def verify_hold(
    session: Session, tenant_id: str, proposal: ChangeProposal, result: dict[str, Any]
) -> None:
    review = result["review"]
    intent = review["intent"]
    placing = result["tool"] == "commitment_hold"
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type
                == ("commitment.held" if placing else "commitment.hold_released"),
            )
            .limit(2)
        )
    )
    if len(events) != 1:
        return
    event = events[0]
    if (
        event.subject_type != "commitment"
        or event.subject_id != intent["commitment_id"]
    ):
        return
    payload = json.loads(event.payload)
    ids = [payload.get("hold_id")] if placing else payload.get("hold_ids", [])
    if (
        not ids
        or not all(isinstance(value, str) for value in ids)
        or len(set(ids)) != len(ids)
    ):
        return
    holds = list(
        session.scalars(
            select(CommitmentHold)
            .where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == intent["commitment_id"],
                CommitmentHold.id.in_(ids),
            )
            .order_by(CommitmentHold.id)
            .execution_options(populate_existing=True)
        )
    )
    if len(holds) != len(ids):
        return
    if placing:
        hold = holds[0]
        if (
            len(holds) != 1
            or hold.reason_code != intent["reason_code"]
            or payload.get("reason_code") != intent["reason_code"]
            or hold.note != intent.get("note", "")
            or hold.created_by != "human"
        ):
            return
    elif [snapshot(hold) for hold in holds] != review["state"]["holds"] or any(
        hold.released_at is None for hold in holds
    ):
        return
    if proposal.status == "executed" and result["receipt"] != hold_receipt(event):
        return
    result["verification"] = (
        "verified" if proposal.status == "executed" else "recorded_unsettled"
    )
    result["links"] = [
        {"kind": "commitment", "id": event.subject_id},
        {"kind": "business_event", "id": event.id},
    ]
