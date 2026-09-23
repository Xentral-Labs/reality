"""Explicit selectors and identity for bounded retained costing answers."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class CostQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    kind: Literal["inventory", "contribution"]
    scope_id: str = Field(min_length=1)
    review_id: str | None = Field(default=None, min_length=1)
    effective_at: AwareDatetime | None = None
    knowledge_at: AwareDatetime | None = None
    policy_revision_id: str | None = Field(default=None, min_length=1)

    @field_validator("effective_at", "knowledge_at")
    @classmethod
    def utc(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None


CostGuidanceStage = Literal["uninitialized", "pending", "stale", "failed", "complete"]


def cost_guidance(
    *,
    kind: Literal["inventory", "contribution"],
    scope_id: str,
    stage: CostGuidanceStage,
    missing_basis: list[str] | tuple[str, ...] = (),
    review_state: str | None = None,
    explanation_links: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
) -> dict[str, Any]:
    """Describe a supported next step without calculating or authorizing cost."""
    operation = "inventory_review" if kind == "inventory" else "contribution_review"
    reasons = {
        "uninitialized": "No retained owner-reviewed cost basis exists for this scope.",
        "pending": "Required evidence or owner review is incomplete.",
        "stale": "Newer relevant business evidence exists after the retained review.",
        "failed": "The last supported cost preparation did not produce a usable retained basis.",
        "complete": "The retained cost basis is current for this bounded scope.",
    }
    if stage == "complete":
        next_action = None
    elif stage == "pending":
        next_action = {
            "tool": "cost_query_get",
            "operation": "reconcile_pending_review",
            "required_principal": "authorized_reader",
        }
    elif stage == "failed":
        next_action = {
            "tool": "cost_evidence_get",
            "operation": "inspect_failed_basis",
            "required_principal": "authorized_reader",
        }
    else:
        next_action = {
            "tool": "cost_change_propose",
            "operation": operation,
            "required_principal": "authenticated_active_owner",
        }
    return {
        "stage": stage,
        "scope": {"kind": kind, "id": scope_id},
        "review_state": review_state or stage,
        "missing_basis": list(missing_basis),
        "reason": reasons[stage],
        "next_action": next_action,
        "explanation_links": list(explanation_links),
    }


def compatible_contexts(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare initialized retained bases, not claims of current completeness."""
    return bool(
        left.get("context_id")
        and left["context_id"] == right.get("context_id")
        and left.get("resolved") == right.get("resolved")
    )


def context_envelope(
    *,
    requested: dict[str, Any],
    resolved: dict[str, Any] | None,
    freshness: dict[str, Any],
) -> dict[str, Any]:
    """Give every cost read the same authority identity and freshness shape."""
    identity = (
        sha256(
            json.dumps(resolved, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if resolved is not None
        else None
    )
    return {
        "requested": requested,
        "resolved": resolved,
        "context_id": identity,
        "freshness_context": freshness,
    }
