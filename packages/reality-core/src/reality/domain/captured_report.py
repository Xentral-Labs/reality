"""Captured diagnostic publication is distinct from historical financial admission."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from reality.domain.cost_census import digest

KIND = "captured_review_selection_v1"
ALGORITHM = "captured-report-v1"


class CapturedPublication(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tenant_id: str = Field(min_length=1, strict=True)
    generation_id: str = Field(min_length=1, strict=True)
    basis_id: str = Field(min_length=1, strict=True)
    scope_key: str = Field(min_length=1, strict=True)
    kind: Literal["captured_review_selection_v1"] = KIND
    effective_at: AwareDatetime
    event_sequence: int = Field(ge=0, strict=True)

    @field_validator("effective_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


def scope_key(tenant: str, effective_at: datetime) -> str:
    if effective_at.tzinfo is None:
        raise ValueError("Aware cutoff required")
    return digest([tenant, KIND, effective_at.astimezone(UTC).isoformat()])


def decide(
    tenant: str,
    candidate: CapturedPublication,
    published: CapturedPublication | None,
    expected_previous: str | None,
    cursor: int,
) -> dict:
    """Trusted sealed storage facts only; this does not verify or write any rows."""
    if candidate.tenant_id != tenant or (published and published.tenant_id != tenant):
        raise ValueError("Captured report unavailable")
    if type(cursor) is not int or cursor < candidate.event_sequence:
        raise ValueError("Invalid event cursor")
    if published:
        if (published.scope_key, published.kind, published.effective_at) != (
            candidate.scope_key,
            candidate.kind,
            candidate.effective_at,
        ):
            raise ValueError("Incompatible captured report scope")
        if cursor < published.event_sequence:
            raise ValueError("Invalid event cursor")
        if (
            published.generation_id == candidate.generation_id
            and published != candidate
        ):
            raise ValueError("Generation identity mismatch")
        if published.event_sequence > candidate.event_sequence:
            raise ValueError("Obsolete captured report")
        if (
            published.event_sequence == candidate.event_sequence
            and published.basis_id != candidate.basis_id
        ):
            raise ValueError("Ambiguous captured basis at equal cursor")
    unchanged = bool(published and published.generation_id == candidate.generation_id)
    if (
        not unchanged
        and (published.generation_id if published else None) != expected_previous
    ):
        raise ValueError("Captured publication changed")
    return {
        "generation_id": candidate.generation_id,
        "change_pointer": not unchanged,
        "processed_event_sequence": candidate.event_sequence,
        "target_event_sequence": cursor,
        "freshness": "ready" if cursor == candidate.event_sequence else "pending",
        "financial_publication_eligible": False,
    }
