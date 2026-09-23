"""One tenant-scoped Web review classification for every application proposal."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal
from reality.services.core import NotFound
from reality.services.delivery_actions import eligible as delivery_review_eligible
from reality.tools.application import TOOLS

ReviewKind = Literal[
    "import", "reference", "analytics_report", "delivery", "common", "retired"
]

REFERENCE_TOOLS = frozenset(
    {
        "party_create",
        "party_update",
        "item_create",
        "item_update",
        "location_create",
        "location_update",
    }
)
_SENSITIVE_KEY = re.compile(
    r"(?:authorization|credential|password|secret|token|api[_-]?key|private[_-]?key)",
    re.IGNORECASE,
)


def classify_proposal(tool: str, arguments: dict[str, Any]) -> ReviewKind:
    """Choose presentation only; execution remains owned by the application tool."""
    if arguments.get("import_file"):
        return "import"
    if tool in REFERENCE_TOOLS:
        return "reference"
    if tool == "graph.reports.change":
        return "analytics_report"
    if delivery_review_eligible(tool, arguments):
        return "delivery"
    if tool in TOOLS:
        return "common"
    return "retired"


def _safe(value: Any, key: str = "") -> Any:
    if key and _SENSITIVE_KEY.search(key):
        return "[redacted]"
    if isinstance(value, dict):
        return {str(k): _safe(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def _stored_object(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _presentation(tool: str) -> tuple[str, str]:
    definition = TOOLS.get(tool)
    return (
        tool.replace("_", " ").replace(".", " ").capitalize(),
        definition.description if definition else "",
    )


def proposal_routing(proposal: ChangeProposal) -> dict[str, str]:
    arguments = _stored_object(proposal.input)
    tool = proposal.type.removeprefix("tool:")
    kind: ReviewKind = (
        classify_proposal(tool, arguments) if arguments is not None else "retired"
    )
    label, purpose = _presentation(tool)
    return {
        "review_kind": kind,
        "review_destination": "proposal-review",
        "review_label": label,
        "review_purpose": purpose,
    }


def proposal_next_step(proposal: ChangeProposal) -> dict[str, Any]:
    """Describe the existing decision boundary without granting decision authority."""
    arguments = _stored_object(proposal.input) or {}
    tool = proposal.type.removeprefix("tool:")
    from reality.catalogs import load_application_catalog
    from reality.tools.finance import FINANCE_COMMANDS

    guidance = load_application_catalog()["capability_guidance"]
    verification_reads: list[str] = []
    for entry in guidance.values():
        if entry.get("application_tool") != tool:
            continue
        verification_reads = [
            str(read["name"])
            for read in entry.get("verification_reads", [])
            if isinstance(read, dict) and read.get("name")
        ]
        break
    required_principal = "authorized_human"
    if tool in FINANCE_COMMANDS or tool == "cost.change":
        required_principal = "authenticated_active_owner"
    elif "_delivery_review" in arguments:
        required_principal = "authenticated_active_member"
    return {
        "review_required": True,
        "review_read": "proposal_review",
        "decision_handoff": "proposal-review",
        "required_principal": required_principal,
        "explicit_confirmation": True,
        "confirmation_tool": "proposal_approve_and_execute",
        "reconciliation_read": "proposal_execution_status",
        "verification_reads": verification_reads,
    }


def proposal_review(
    session: Session, tenant_id: str, proposal_id: str
) -> dict[str, Any]:
    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id
        )
    )
    if proposal is None:
        raise NotFound("Proposal not found.")
    tool = proposal.type.removeprefix("tool:")
    arguments = _stored_object(proposal.input)
    output = _stored_object(proposal.output)
    malformed = arguments is None or output is None
    kind: ReviewKind = "retired" if malformed else classify_proposal(tool, arguments)
    label, purpose = _presentation(tool)
    return {
        "id": proposal.id,
        "tool": tool,
        "label": label,
        "purpose": purpose,
        "review_kind": kind,
        "status": proposal.status,
        "actor_type": proposal.actor_type,
        "created_at": proposal.created_at.isoformat(),
        "decided_at": proposal.decided_at.isoformat() if proposal.decided_at else None,
        "input": _safe(arguments or {}),
        "preview": _safe(output or {}) if proposal.status == "proposed" else {},
        "receipt": _safe(output or {}) if proposal.status != "proposed" else {},
        "next_step": proposal_next_step(proposal),
        "confirmable": proposal.status == "proposed" and kind != "retired",
        "rejectable": proposal.status == "proposed",
        "message": (
            "This stored proposal is malformed and cannot be approved. You may reject it."
            if malformed
            else "This retired tool can no longer be approved. You may reject the proposal."
            if kind == "retired"
            else ""
        ),
    }
