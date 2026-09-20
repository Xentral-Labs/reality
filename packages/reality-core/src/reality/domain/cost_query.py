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
