"""Read-time steps that would make a missing cost basis available (spec 279).

Guidance is an observation derived from held evidence, reviews and proposals at read
time. It is never stored and never authorizes anything: each step points at an
existing path (a form, the chat preview/confirmation flow, or a decision review).
"""

import json
from typing import Any

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, DocumentLine, Movement, MovementCorrection
from reality.domain.resolution_guidance import catalog_key, guidance_step
from reality.services import core
from reality.services.inventory_costing import MAX_RECEIPTS

#: How many incomplete receipts a step names; the count still covers all of them.
TARGET_LIMIT = 10
#: Pending cost proposals examined for one scope; companies hold very few at once.
PROPOSAL_LIMIT = 50

INVENTORY_GAPS = frozenset({"inventory_scope_not_reviewed", "inventory_review_stale"})
CONSUMPTION_GAPS = frozenset({"consumption_not_reviewed", "consumption_after_cutoff"})
INVENTORY_OPERATIONS = frozenset({"inventory_review", "inventory_batch_review"})
CONTRIBUTION_OPERATIONS = frozenset(
    {"contribution_review", "contribution_batch_review"}
)


def _writable(session: Session, tenant: str) -> bool:
    """Whether a confirmed cost decision could run in this company at all."""
    from reality.services.tenant_policy import business_operation_allowed

    return business_operation_allowed(session, tenant, "execute_cost_change")


def _receipt_gaps(
    session: Session, tenant: str, item_id: str
) -> tuple[int, list[str], int]:
    """Count receipts and name those whose cost is not yet complete."""
    from reality.services.costing import receipt_cost

    current = (
        Movement.tenant_id == tenant,
        Movement.item_id == item_id,
        Movement.type == "receipt",
        ~exists().where(
            MovementCorrection.tenant_id == tenant,
            MovementCorrection.original_movement_id == Movement.id,
        ),
    )
    total = session.scalar(select(func.count()).select_from(Movement).where(*current))
    if not total:
        return 0, [], 0
    receipts = session.scalars(
        select(Movement.id)
        .where(*current)
        .order_by(Movement.occurred_at, Movement.id)
        .limit(MAX_RECEIPTS)
    ).all()
    incomplete = [
        receipt
        for receipt in receipts
        if set(receipt_cost(session, tenant, receipt)["missing_basis"])
        - {"review_stale"}
    ]
    # Receipts beyond the review bound cannot be confirmed in one review either.
    unexamined = max(0, total - len(receipts))
    return total, incomplete[:TARGET_LIMIT], len(incomplete) + unexamined


def _pending_proposal(
    session: Session,
    tenant: str,
    *,
    item_id: str | None = None,
    line_id: str | None = None,
) -> str | None:
    """Return the newest proposed cost decision for this scope, if one waits."""
    rows = session.execute(
        select(ChangeProposal.id, ChangeProposal.input)
        .where(
            ChangeProposal.tenant_id == tenant,
            ChangeProposal.type == "tool:cost.change",
            ChangeProposal.status == "proposed",
        )
        .order_by(ChangeProposal.created_at.desc(), ChangeProposal.id.desc())
        .limit(PROPOSAL_LIMIT)
    ).all()
    for proposal_id, raw in rows:
        try:
            arguments = json.loads(raw or "{}")
        except ValueError:
            continue
        operation = arguments.get("operation")
        if item_id and operation in INVENTORY_OPERATIONS:
            scopes = arguments.get("scopes") or [arguments]
            if any(scope.get("item_id") == item_id for scope in scopes):
                return proposal_id
        if line_id and operation in CONTRIBUTION_OPERATIONS:
            scopes = arguments.get("positions") or [arguments]
            if any(scope.get("document_line_id") == line_id for scope in scopes):
                return proposal_id
    return None


def _inventory_path(
    session: Session, tenant: str, item_id: str, *, renew: bool
) -> tuple[list[dict[str, Any]], str | None]:
    """Receipt and item-review steps, without the owner step, plus a waiting proposal."""
    total, targets, incomplete = _receipt_gaps(session, tenant, item_id)
    proposal = _pending_proposal(session, tenant, item_id=item_id)
    steps = []
    if total:
        steps.append(
            guidance_step(
                "receipt_cost_evidence",
                "open" if incomplete else "done",
                targets=targets,
                target_count=incomplete,
            )
        )
    review = "inventory_review_renew" if renew else "inventory_review"
    state = "done" if proposal else "blocked" if incomplete else "open"
    steps.append(guidance_step(review, state))
    return steps, proposal


def _owner(proposal: str | None) -> dict[str, Any]:
    if proposal:
        return guidance_step("owner_confirmation", "open", proposal_id=proposal)
    return guidance_step("owner_confirmation", "blocked")


def _inventory(
    session: Session, tenant: str, item_id: str, result: dict[str, Any]
) -> tuple[str, list[dict[str, Any]]]:
    if result.get("review_state") == "reviewed_complete_at_cutoff":
        return "cost_complete", []
    stale = result.get("review_state") == "stale"
    steps, proposal = _inventory_path(session, tenant, item_id, renew=stale)
    gaps = list(result.get("missing_basis") or ())
    reason = catalog_key(gaps[0]) if gaps else "cost_pending"
    return reason, [*steps, _owner(proposal)]


def _contribution(
    session: Session, tenant: str, line_id: str, result: dict[str, Any]
) -> tuple[str, list[dict[str, Any]]]:
    from reality.services.costing import _row, contribution_preview, inventory_cost

    try:
        preview = contribution_preview(session, tenant, line_id)
    except core.Conflict:
        # Inputs moved during the read. The cost answer itself stays valid; guidance
        # falls back to the contribution-level gaps instead of failing the whole read.
        preview = {"state": "candidate", "missing_basis": []}
    upstream = list(preview.get("missing_basis") or ())
    if preview["state"] == "unavailable" and upstream:
        gap = upstream[0]
        if gap not in INVENTORY_GAPS | CONSUMPTION_GAPS:
            return catalog_key(gap), [guidance_step("source_data_limit", "open")]
        item_id = _row(session, DocumentLine, tenant, line_id).item_id
        if gap in INVENTORY_GAPS:
            inventory = inventory_cost(session, tenant, item_id)
            steps, proposal = _inventory_path(
                session, tenant, item_id, renew=inventory["review_state"] == "stale"
            )
        else:
            proposal = _pending_proposal(session, tenant, item_id=item_id)
            steps = [
                guidance_step("inventory_review_renew", "done" if proposal else "open")
            ]
        return gap, [
            *steps,
            guidance_step("contribution_review", "blocked"),
            _owner(proposal),
        ]
    gaps = [
        *(result.get("missing_basis") or ()),
        *(gap for gap in upstream if gap not in (result.get("missing_basis") or ())),
    ]
    if not gaps:
        return "cost_complete", []
    commercial = {
        "commercial_match_not_reviewed",
        "contribution_profile_not_reviewed",
        "contribution_review_stale",
    }
    steps = []
    if commercial & set(gaps):
        proposal = _pending_proposal(session, tenant, line_id=line_id)
        steps += [
            guidance_step("contribution_review", "done" if proposal else "open"),
            _owner(proposal),
        ]
    if any(
        catalog_key(gap) in {"selling_costs_unknown", "selling_category"}
        for gap in gaps
    ):
        # DB2 only: listed after the DB1 path and never blocked by it.
        steps.append(guidance_step("selling_cost_review", "open"))
    return catalog_key(gaps[0]), steps


def cost_resolution(
    session: Session,
    tenant: str,
    *,
    kind: str,
    scope_id: str,
    stage: str,
    result: dict[str, Any],
    historical: bool,
) -> dict[str, Any]:
    """Explain the stage with a catalog reason and the ordered steps to resolve it."""
    value_reasons = {}
    if (
        kind == "inventory"
        and result.get("carrying_value") is None
        and result.get("carrying_value_state")
        in {"assessment_missing", "assessment_not_supported"}
    ):
        value_reasons["carrying_value"] = result["carrying_value_state"]
    if historical or stage == "complete":
        reason, steps = f"cost_{stage}", []
    elif kind == "inventory":
        reason, steps = _inventory(session, tenant, scope_id, result)
    else:
        reason, steps = _contribution(session, tenant, scope_id, result)
    return {
        "reason_code": reason,
        "steps": steps,
        "writable": _writable(session, tenant),
        "value_reasons": value_reasons,
    }
