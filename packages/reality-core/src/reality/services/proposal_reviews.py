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
from reality.services.memberships import Principal
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
_PRIVATE_CARRIERS = frozenset({"private_report_change", "requested_analysis"})
_PRIVATE_REPORT_TOOLS = frozenset({"graph.reports.change", "analytics.reports.change"})


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
        return {
            str(k): _safe(v, str(k))
            for k, v in value.items()
            if str(k) not in _PRIVATE_CARRIERS
        }
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
    stored_arguments = _stored_object(proposal.input)
    arguments = stored_arguments or {}
    tool = proposal.type.removeprefix("tool:")
    from reality.catalogs import runtime_application_catalog_section
    from reality.services.proposal_decisions import resolve_decision_policy

    guidance = runtime_application_catalog_section("capability_guidance")
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
    policy = resolve_decision_policy(
        tool, arguments, available=stored_arguments is not None
    )
    if tool == "email_dispatch_authorize":
        from reality.services.emails import _hash

    return {
        "review_required": True,
        "review_read": "proposal_review",
        "decision_handoff": "proposal-review",
        "required_principal": policy.required_principal,
        "decision_policy": policy.as_dict(),
        "explicit_confirmation": True,
        "confirmation_tool": "proposal_approve_and_execute",
        "reconciliation_read": "proposal_execution_status",
        "verification_reads": verification_reads,
        **(
            {
                "external_approval": {
                    "tool": "email_dispatch_accept_grant",
                    "proposal_id": proposal.id,
                    "approval_digest": _hash(arguments),
                    "requires": "issuer-signed v1 JWS; configured company/subject mandate; exact reviewed preview",
                }
            }
            if tool == "email_dispatch_authorize"
            and proposal.status == "proposed"
            and stored_arguments is not None
            and not arguments.get("retry_acknowledgements")
            else {}
        ),
    }


def proposal_review(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    *,
    principal: Principal | None = None,
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
    from reality.services.decision_attribution import UNKNOWN, decision_attributions

    attribution = decision_attributions(session, tenant_id, [proposal.id])
    private_review = None
    if tool in _PRIVATE_REPORT_TOOLS or tool == "graph.requests.create":
        private_review = _private_review(session, tenant_id, proposal, principal)
    private_hidden = (
        private_review is not None and private_review["state"] != "readable"
    )
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
        "decider": attribution.get(proposal.id, {}).get("decider", dict(UNKNOWN)),
        "input": _safe(arguments or {}),
        "preview": _safe(output or {})
        if proposal.status == "proposed" and not private_hidden
        else {},
        "receipt": _safe(output or {})
        if proposal.status != "proposed" and not private_hidden
        else {},
        **({"private_review": private_review} if private_review is not None else {}),
        "next_step": proposal_next_step(proposal),
        "confirmable": proposal.status == "proposed"
        and kind != "retired"
        and not private_hidden,
        "rejectable": proposal.status == "proposed",
        "message": (
            "This stored proposal is malformed and cannot be approved. You may reject it."
            if malformed
            else "This retired tool can no longer be approved. You may reject the proposal."
            if kind == "retired"
            else ""
        ),
    }


def _private_review(
    session: Session,
    tenant_id: str,
    proposal: ChangeProposal,
    principal: Principal | None,
) -> dict[str, Any]:
    from reality.services.analytics.errors import AnalyticsError
    from reality.services.analytics.proposals import preview, preview_request
    from reality.services.core import InvalidOperation

    hidden = {
        "state": "hidden",
        "message": "This change is private. Only its original author can view its contents.",
    }
    if principal is None:
        return hidden
    try:
        details = (
            preview(session, tenant_id, principal, proposal.id)
            if proposal.type.removeprefix("tool:") in _PRIVATE_REPORT_TOOLS
            else preview_request(
                session, tenant_id, principal, json.loads(proposal.input)
            )
        )
        if (
            proposal.type.removeprefix("tool:") in _PRIVATE_REPORT_TOOLS
            and details["kind"] != "graph"
        ):
            raise AnalyticsError(
                "Private report kind is retired.", "unsupported_report_kind"
            )
    except AnalyticsError as error:
        if error.code == "user_context_required":
            return hidden
        return {
            "state": "unavailable",
            "message": "The private change cannot be read. It may be rejected, but cannot be approved here.",
        }
    except (NotFound, InvalidOperation):
        return hidden
    except (KeyError, TypeError, ValueError):
        return {
            "state": "unavailable",
            "message": "The private change cannot be read. It may be rejected, but cannot be approved here.",
        }
    return {"state": "readable", "details": _safe(details)}


def proposal_mcp_review(
    session: Session, tenant_id: str, proposal_id: str
) -> dict[str, Any]:
    """Read exact shared review without changing or refreshing the stored proposal."""
    from reality.mcp.principal import current_mcp_principal
    from reality.services.core import get_tenant
    from reality.services.delivery_actions import REVIEW_KEY

    actor = current_mcp_principal()
    if actor is not None and actor.tenant_id != tenant_id:
        raise NotFound("Proposal not found.")
    principal = Principal(actor.user_id) if actor and actor.user_id else None
    with session.no_autoflush:
        result = proposal_review(session, tenant_id, proposal_id, principal=principal)
        tenant = get_tenant(session, tenant_id)
        result["company"] = {
            "id": tenant.id,
            "name": tenant.name,
            "purpose": tenant.purpose,
        }
        proposal = session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == proposal_id,
            )
        )
        arguments = _stored_object(proposal.input) or {}
        retained = arguments.get(REVIEW_KEY)
        # This fingerprint proves the retained business review; it is not a credential.
        # All other token fields and private carriers remain redacted by the shared reader.
        review_token = (
            retained.get("token")
            if isinstance(retained, dict)
            and result["review_kind"] == "delivery"
            and result["confirmable"]
            else None
        )
        from reality.catalogs import runtime_tool_catalog
        from reality.mcp.catalog import MCP_TOOL_REGISTRY

        basis = result["next_step"]["verification_reads"]
        callable_reads: set[str] = set()
        unavailable: list[str] = []
        catalog = runtime_tool_catalog()
        for name in basis:
            candidates = {name}
            for entry in catalog["entries"]:
                if any(
                    name in entry[key] for key in ("commands", "views", "projections")
                ):
                    candidates.update(entry["mcp"])
            matches = {
                candidate
                for candidate in candidates
                if candidate in MCP_TOOL_REGISTRY
                and MCP_TOOL_REGISTRY[candidate].access == "read"
            }
            callable_reads.update(matches)
            if not matches:
                unavailable.append(name)
        result["next_step"]["verification_basis"] = basis
        result["next_step"]["verification_reads"] = sorted(callable_reads)
        result["next_step"]["unavailable_verification_reads"] = unavailable
        result["confirmation"] = {
            "tool": "proposal_approve_and_execute",
            "proposal_id": proposal_id,
            "explicit_approval_required": True,
            "review_token": review_token if isinstance(review_token, str) else None,
        }
        return result
