"""Pure publication guards; storage must verify inputs and apply under a scoped lock.

These models carry trusted service facts, never user approval or financial authority.
A successful decision alone does not publish, establish isolation or fence a worker.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)

from reality.domain.cost_population import (
    EvaluatedPopulation,
    ExpectedPopulation,
    Fingerprint,
    PopulationBasis,
    PopulationRefusal,
    close_population,
)

Identity = Annotated[str, Field(min_length=1, strict=True)]
Count = Annotated[int, Field(ge=0, strict=True)]


class PublicationRefusal(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class GenerationBasis(_Frozen):
    tenant_id: Identity
    scope_key: Identity
    kind: Literal["inventory", "contribution"]
    manifest_id: Identity
    policy_revision_id: Identity
    profile_revision_id: Identity | None
    effective_at: AwareDatetime
    knowledge_at: AwareDatetime
    event_sequence: Count
    algorithm_version: Identity

    @field_validator("effective_at", "knowledge_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def profile_scope(self):
        if (self.kind == "contribution") != (self.profile_revision_id is not None):
            raise ValueError("Only contribution requires a retained profile revision.")
        return self


class CompanyGenerationBasis(PopulationBasis):
    """Trusted retained financial context, never a raw current discovery snapshot."""

    kind: Literal["company"] = "company"
    scope_key: Identity
    manifest_id: Identity
    population_hash: Fingerprint
    algorithm_version: Literal["company-v1"] = "company-v1"


def population_fingerprint(expected: ExpectedPopulation) -> str:
    """Bind exact expected inputs, independent of enumeration order.

    Storage must retain and verify the members behind this digest. Hashing does not
    establish census completeness, financial admission or immutable input retention.
    """
    content = expected.model_dump(mode="json")
    content["inventory"].sort(key=lambda row: row["item_id"])
    content["contribution"].sort(key=lambda row: row["document_line_id"])
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class Generation(_Frozen):
    id: Identity
    basis: GenerationBasis | CompanyGenerationBasis


class Completion(_Frozen):
    inputs_sealed: StrictBool
    content_verified: StrictBool
    planned_work: Count
    completed_work: Count
    expected_inventory_rows: Count
    inventory_rows: Count
    expected_contribution_rows: Count
    contribution_rows: Count
    expected_trace_rows: Count
    trace_rows: Count

    @model_validator(mode="after")
    def work_shape(self):
        if self.completed_work > self.planned_work:
            raise ValueError("Completed work exceeds planned work.")
        if self.planned_work == 0 and any(
            getattr(self, name)
            for name in (
                "expected_inventory_rows",
                "inventory_rows",
                "expected_contribution_rows",
                "contribution_rows",
                "expected_trace_rows",
                "trace_rows",
            )
        ):
            raise ValueError("A zero-work generation must have no output rows.")
        return self


class PublicationDecision(_Frozen):
    generation_id: Identity
    change_pointer: StrictBool
    processed_event_sequence: Count
    target_event_sequence: Count
    freshness: Literal["ready", "pending"]


def publication_decision(
    *,
    tenant_id: str,
    candidate: Generation,
    completion: Completion,
    published: Generation | None,
    expected_previous_id: str | None,
    target_event_sequence: int,
    expected_population: ExpectedPopulation | None = None,
    evaluated_population: EvaluatedPopulation | None = None,
) -> PublicationDecision:
    """Validate one observed pointer change without reading or mutating any state.

    The service must obtain both generations and completion facts with tenant-scoped
    queries, then retain the publication lock/CAS through commit. No untrusted API
    caller may assert that content is verified or a manifest is sealed.
    """
    basis = candidate.basis
    if basis.tenant_id != tenant_id or (
        published is not None and published.basis.tenant_id != tenant_id
    ):
        raise PublicationRefusal("cost_basis_unavailable")
    if (
        type(target_event_sequence) is not int
        or target_event_sequence < basis.event_sequence
    ):
        raise PublicationRefusal("cost_event_cursor_invalid")
    if published is not None:
        prior = published.basis
        fields = ("scope_key", "kind", "effective_at")
        if isinstance(basis, GenerationBasis):
            fields += ("policy_revision_id", "profile_revision_id")
        if type(prior) is not type(basis) or any(
            getattr(prior, field) != getattr(basis, field) for field in fields
        ):
            raise PublicationRefusal("cost_context_unsupported")
        if published.id == candidate.id and published != candidate:
            raise PublicationRefusal("cost_generation_identity_mismatch")
        if target_event_sequence < prior.event_sequence:
            raise PublicationRefusal("cost_event_cursor_invalid")
    if not completion.inputs_sealed:
        raise PublicationRefusal("cost_inputs_unsealed")
    if not completion.content_verified:
        raise PublicationRefusal("cost_content_unverified")
    if completion.completed_work != completion.planned_work:
        raise PublicationRefusal("cost_work_incomplete")
    if any(
        getattr(completion, name) != getattr(completion, f"expected_{name}")
        for name in ("inventory_rows", "contribution_rows", "trace_rows")
    ):
        raise PublicationRefusal("cost_row_count_mismatch")
    if isinstance(basis, CompanyGenerationBasis):
        if expected_population is None or evaluated_population is None:
            raise PublicationRefusal("cost_population_required")
        context = PopulationBasis.model_validate(
            {field: getattr(basis, field) for field in PopulationBasis.model_fields}
        )
        if expected_population.basis != context:
            raise PublicationRefusal("cost_population_context_mismatch")
        if population_fingerprint(expected_population) != basis.population_hash:
            raise PublicationRefusal("cost_population_manifest_mismatch")
        try:
            closure = close_population(
                tenant_id, expected_population, evaluated_population
            )
        except PopulationRefusal as error:
            raise PublicationRefusal(error.code) from error
        if (
            completion.inventory_rows != closure.inventory_rows
            or completion.contribution_rows != closure.contribution_rows
        ):
            raise PublicationRefusal("cost_population_row_count_mismatch")
    elif expected_population is not None or evaluated_population is not None:
        raise PublicationRefusal("cost_context_unsupported")
    unchanged = published is not None and published.id == candidate.id
    if not unchanged:
        actual_previous_id = published.id if published is not None else None
        if actual_previous_id != expected_previous_id:
            raise PublicationRefusal("cost_publication_changed")
        if (
            published is not None
            and published.basis.event_sequence > basis.event_sequence
        ):
            raise PublicationRefusal("cost_generation_obsolete")
    return PublicationDecision(
        generation_id=candidate.id,
        change_pointer=not unchanged,
        processed_event_sequence=basis.event_sequence,
        target_event_sequence=target_event_sequence,
        freshness="ready"
        if target_event_sequence == basis.event_sequence
        else "pending",
    )
