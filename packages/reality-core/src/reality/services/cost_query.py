"""One context envelope around existing admitted cost reads; no new arithmetic."""

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from reality.db.contribution import CostContributionReview
from reality.db.inventory_costing import CostInventoryReview, CostPolicyRevision
from reality.domain.contribution import ALGORITHM_VERSION
from reality.domain.cost_query import CostQueryRequest, context_envelope, cost_guidance
from reality.services import core
from reality.services.cost_resolution import cost_resolution
from reality.services.costing import (
    _row,
    _sequence,
    inventory_cost,
    reviewed_contribution,
)


def _utc(value: str) -> str:
    return datetime.fromisoformat(value).astimezone(UTC).isoformat()


def _read(session: Session, tenant: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        request = CostQueryRequest.model_validate(arguments)
    except ValidationError as error:
        raise core.InvalidOperation(str(error)) from error
    historical = request.review_id is not None
    with session.no_autoflush:
        if (
            not historical
            and session.connection().get_isolation_level() != "READ COMMITTED"
        ):
            raise core.InvalidOperation("Current cost queries require READ COMMITTED.")
        reader = (
            inventory_cost if request.kind == "inventory" else reviewed_contribution
        )
        result = reader(session, tenant, request.scope_id, review_id=request.review_id)
        requested = request.model_dump(mode="json")
        resolved = None
        sequence = result.get("event_sequence")
        if historical:
            target = None
        elif result["review_id"] is not None:
            from reality.services.inventory_costing import _relevant_event_sequence

            target = _relevant_event_sequence(
                session,
                tenant,
                (
                    request.scope_id
                    if request.kind == "inventory"
                    else result["trace"]["item_id"]
                ),
                int(sequence),
            )
        else:
            target = _sequence(session, tenant)
        if result["review_id"] is not None:
            inventory_id = (
                result["review_id"]
                if request.kind == "inventory"
                else result["trace"]["inventory_review_id"]
            )
            inventory = _row(session, CostInventoryReview, tenant, inventory_id)
            policy = _row(session, CostPolicyRevision, tenant, inventory.policy_id)
            resolved = {
                "tenant_id": tenant,
                "kind": request.kind,
                "scope_id": request.scope_id,
                "basis_kind": "retained_scope_review",
                "review_id": result["review_id"],
                "inventory_review_id": inventory.id,
                "generation_id": None,
                "profile_revision_id": None,
                "scope_profile_review_id": result["review_id"]
                if request.kind == "contribution"
                else None,
                "profile": result.get("profile"),
                "policy_revision_id": policy.id,
                "method": policy.method,
                "owner_party_id": policy.owner_party_id,
                "currency": policy.currency,
                "base_unit": policy.base_unit,
                "effective_at": inventory.effective_at.astimezone(UTC).isoformat(),
                "knowledge_at": _utc(result["knowledge_at"]),
                "inventory_knowledge_at": inventory.knowledge_at.astimezone(
                    UTC
                ).isoformat(),
                "inventory_algorithm_version": inventory.algorithm_version,
                "contribution_algorithm_version": ALGORITHM_VERSION
                if request.kind == "contribution"
                else None,
                "event_sequence": sequence,
                "inventory_event_sequence": inventory.target_event_sequence,
                "inventory_content_hash": inventory.content_hash,
            }
            if request.kind == "contribution":
                review = _row(
                    session, CostContributionReview, tenant, result["review_id"]
                )
                resolved["contribution_content_hash"] = review.content_hash
        for field in ("effective_at", "knowledge_at", "policy_revision_id"):
            expected = getattr(request, field)
            if expected is not None:
                actual = resolved.get(field) if resolved else None
                if isinstance(expected, datetime):
                    expected = expected.isoformat()
                if expected != actual:
                    raise core.InvalidOperation("cost_context_unsupported")
        state = (
            "uninitialized"
            if resolved is None
            else "historical"
            if historical
            else "stale"
            if target > sequence or result["review_state"] == "stale"
            else "ready"
        )
        freshness = {
            "state": state,
            "processed_event_sequence": sequence,
            "target_event_sequence": target,
        }
        missing_basis = list(result.get("missing_basis") or ())
        guidance_stage = (
            "uninitialized"
            if state == "uninitialized"
            else "stale"
            if state == "stale"
            else "pending"
            if missing_basis
            or result.get("review_state") in {"unreviewed", "incomplete"}
            else "complete"
        )
        explanation_links = []
        if resolved:
            explanation_links.append(
                {
                    "kind": "cost_inventory_review"
                    if request.kind == "inventory"
                    else "cost_contribution_review",
                    "id": str(result["review_id"]),
                }
            )
        return {
            **context_envelope(
                requested=requested, resolved=resolved, freshness=freshness
            ),
            "freshness": {
                **freshness,
            },
            "result": result if state in {"ready", "historical"} else None,
            "basis_result": result,
            "guidance": cost_guidance(
                kind=request.kind,
                scope_id=request.scope_id,
                stage=guidance_stage,
                missing_basis=missing_basis,
                review_state=result.get("review_state"),
                explanation_links=explanation_links,
                resolution=cost_resolution(
                    session,
                    tenant,
                    kind=request.kind,
                    scope_id=request.scope_id,
                    stage=guidance_stage,
                    result=result,
                    historical=historical,
                ),
            ),
            "persistence": {"business_writes": False, "projection_writes": False},
        }
