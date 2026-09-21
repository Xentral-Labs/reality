"""State-bound review and verification for explicit supply assignments."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, SourceRecord, SupplyAssignment
from reality.services import core
from reality.services.supply_assignments import (
    preview_supply_assignment,
    supply_coverage,
)

SUPPLY_ASSIGNMENT_TOOLS = {"supply_assign"}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def review_supply_assignment(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) != {
        "supplier_commitment_id",
        "quantity",
        "purpose",
        "customer_commitment_id",
    } and set(arguments) != {"supplier_commitment_id", "quantity", "purpose"}:
        raise core.InvalidOperation(
            "Supply assignment fields are incomplete or unsupported."
        )
    intent = {
        **arguments,
        "customer_commitment_id": arguments.get("customer_commitment_id"),
    }
    state = json.loads(_json(preview_supply_assignment(session, tenant_id, **intent)))
    normalized = {
        "supplier_commitment_id": state["supplier_commitment_id"],
        "customer_commitment_id": state["customer_commitment_id"],
        "purpose": state["purpose"],
        "quantity": str(state["quantity"]),
    }
    return {
        "version": 1,
        "tool": "supply_assign",
        "intent": normalized,
        "state": state,
        "effect": {
            "assigned": normalized["quantity"],
            "purpose": normalized["purpose"],
            "unassigned_after": str(state["supplier_after"]["unassigned"]),
        },
        "token": hashlib.sha256(
            _json([tenant_id, "supply_assign", normalized, state]).encode()
        ).hexdigest(),
    }


def assert_no_unresolved_supply_assignment(
    session: Session,
    tenant_id: str,
    arguments: dict[str, Any],
    exclude: str | None,
) -> None:
    for proposal in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:supply_assign",
            ChangeProposal.status == "executing",
        )
    ):
        saved = json.loads(proposal.input)
        if proposal.id != exclude and saved.get(
            "supplier_commitment_id"
        ) == arguments.get("supplier_commitment_id"):
            raise core.InvalidOperation(
                "An earlier supply assignment is unresolved. Check its outcome first."
            )


def supply_assignment_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input).get("_delivery_review")
    result = {
        "id": proposal.id,
        "tool": "supply_assign",
        "status": proposal.status,
        "review": review,
        "receipt": json.loads(proposal.output)
        if proposal.status == "executed"
        else None,
        "verification": "pending" if proposal.status == "proposed" else "unresolved",
        "links": [],
        "observation": None,
        "observation_error": None,
    }
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == "manual",
            SourceRecord.source_type == "supply_assignment",
            SourceRecord.external_id == proposal.id,
        )
    )
    row = (
        session.scalar(
            select(SupplyAssignment).where(
                SupplyAssignment.tenant_id == tenant_id,
                SupplyAssignment.source_record_id == source.id,
            )
        )
        if source
        else None
    )
    if row and review:
        observation = supply_coverage(
            session, tenant_id, supplier_commitment_id=row.supplier_commitment_id
        )
        receipt = {"supply_assignment_id": row.id, "source_record_id": source.id}
        if proposal.status != "executed" or result["receipt"] == receipt:
            result.update(
                verification=(
                    "verified"
                    if proposal.status == "executed"
                    else "recorded_unsettled"
                ),
                recorded_receipt=receipt,
                links=[
                    {"kind": "supply_assignment", "id": row.id},
                    {"kind": "source_record", "id": source.id},
                ],
                observation=observation,
            )
    return result
