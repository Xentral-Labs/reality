"""Immutable public evidence and claim rules for the Reality Product Advisor."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceKind = Literal[
    "journey", "executable_catalog", "public_document", "public_contract"
]
SourceAuthority = Literal[
    "capability", "executable_vocabulary", "technical_contract", "explanation"
]
EvidenceSupport = Literal[
    "proven", "limited", "unavailable", "explanatory", "vocabulary_only"
]
ClaimSupport = Literal["proven", "limited", "unavailable", "not_established"]
WorkflowRole = Literal[
    "native", "agent_proposal", "confirmed_execution", "manual", "workaround", "gap"
]
ValidationState = Literal["accepted", "weakened", "rejected"]

_PRIVATE_REFERENCE = re.compile(
    r"(?:^|/)(?:packages|specs|tests|\.git)(?:/|$)|(?:^|/)docs/(?!public/)",
    re.IGNORECASE,
)
_SUPPORT_CEILING: dict[EvidenceSupport, int] = {
    "proven": 3,
    "limited": 2,
    "unavailable": 1,
    "explanatory": 0,
    "vocabulary_only": 0,
}
_CLAIM_LEVEL: dict[ClaimSupport, int] = {
    "proven": 3,
    "limited": 2,
    "unavailable": 1,
    "not_established": 0,
}
_HIGH_RISK_TERMS = (
    "automatic",
    "automatisch",
    "fully supported",
    "vollstandig unterstutzt",
    "complete",
    "end to end",
    "end-to-end",
    "compliant",
    "migration",
)


def _normalized(value: str) -> str:
    return value.casefold().replace("ä", "a").replace("ö", "o").replace("ü", "u")


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^source_[a-z0-9_]+$")
    kind: SourceKind
    title: str = Field(min_length=1, max_length=300)
    visibility: Literal["public", "internal"]
    authority: SourceAuthority
    public_url: str | None = Field(default=None, max_length=1000)
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def public_location_is_safe(self) -> EvidenceSource:
        if self.visibility == "public" and (
            not self.public_url or _PRIVATE_REFERENCE.search(self.public_url)
        ):
            raise ValueError(f"{self.id}: public source needs a public-safe URL")
        return self


class EvidenceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^evidence_[a-z0-9_]+$")
    source_id: str = Field(pattern=r"^source_[a-z0-9_]+$")
    subject: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    search_text: str = Field(min_length=1, max_length=8000)
    claim_text: str = Field(min_length=1, max_length=8000)
    support: EvidenceSupport
    limitations: tuple[str, ...] = Field(default=(), max_length=20)
    references: tuple[str, ...] = Field(default=(), max_length=40)
    language: str = Field(default="en", min_length=2, max_length=35)
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def limitations_match_support(self) -> EvidenceUnit:
        if self.support in {"limited", "unavailable"} and not self.limitations:
            raise ValueError(f"{self.id}: {self.support} evidence needs a limitation")
        return self


class AdvisoryClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^claim_[a-z0-9_]+$")
    subject: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=2000)
    support: ClaimSupport
    evidence_ids: tuple[str, ...] = Field(default=(), max_length=12)
    limitations: tuple[str, ...] = Field(default=(), max_length=20)
    workflow_role: WorkflowRole
    tool_names: tuple[str, ...] = Field(default=(), max_length=8)
    validation: ValidationState = "accepted"
    reason_codes: tuple[str, ...] = Field(default=(), max_length=12)


class ProductAdvisorKnowledge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(ge=1)
    knowledge_version: str = Field(min_length=1, max_length=200)
    sources: tuple[EvidenceSource, ...]
    evidence: tuple[EvidenceUnit, ...]

    @model_validator(mode="after")
    def identities_and_references_resolve(self) -> ProductAdvisorKnowledge:
        source_ids = [item.id for item in self.sources]
        evidence_ids = [item.id for item in self.evidence]
        if len(source_ids) != len(set(source_ids)):
            duplicate = next(item for item in source_ids if source_ids.count(item) > 1)
            raise ValueError(f"Duplicate source id: {duplicate}")
        if len(evidence_ids) != len(set(evidence_ids)):
            duplicate = next(item for item in evidence_ids if evidence_ids.count(item) > 1)
            raise ValueError(f"Duplicate evidence id: {duplicate}")
        known_sources = set(source_ids)
        for unit in self.evidence:
            if unit.source_id not in known_sources:
                raise ValueError(
                    f"{unit.id}: source {unit.source_id} does not exist"
                )
        return self

    def public_payload(self) -> dict[str, object]:
        public_ids = {source.id for source in self.sources if source.visibility == "public"}
        return {
            "schema_version": self.schema_version,
            "knowledge_version": self.knowledge_version,
            "sources": [
                source.model_dump(mode="json")
                for source in self.sources
                if source.id in public_ids
            ],
            "evidence": [
                unit.model_dump(mode="json")
                for unit in self.evidence
                if unit.source_id in public_ids
            ],
        }


def validate_claim(
    claim: AdvisoryClaim, evidence_by_id: dict[str, EvidenceUnit]
) -> AdvisoryClaim:
    """Apply deterministic authority and support ceilings to one material claim."""
    if not claim.evidence_ids:
        if claim.support == "not_established":
            return claim
        return claim.model_copy(
            update={"validation": "rejected", "reason_codes": ("missing_evidence",)}
        )
    selected = [
        evidence_by_id[item]
        for item in claim.evidence_ids
        if item in evidence_by_id
    ]
    if len(selected) != len(claim.evidence_ids):
        return claim.model_copy(
            update={"validation": "rejected", "reason_codes": ("unknown_evidence",)}
        )
    ceiling = min(_SUPPORT_CEILING[item.support] for item in selected)
    if _CLAIM_LEVEL[claim.support] > ceiling:
        return claim.model_copy(
            update={"validation": "rejected", "reason_codes": ("support_ceiling",)}
        )
    statement = _normalized(claim.statement)
    evidence_text = " ".join(
        _normalized(f"{item.claim_text} {item.search_text}") for item in selected
    )
    unsupported_risk = tuple(
        term
        for term in _HIGH_RISK_TERMS
        if term in statement
        and (
            term not in evidence_text
            or not any(item.support in {"proven", "limited"} for item in selected)
        )
    )
    if unsupported_risk:
        return claim.model_copy(
            update={
                "validation": "rejected",
                "reason_codes": tuple(
                    f"unqualified_{term.replace(' ', '_').replace('-', '_')}"
                    for term in unsupported_risk
                ),
            }
        )
    if claim.workflow_role == "confirmed_execution" and "proposal" in evidence_text:
        return claim.model_copy(
            update={
                "validation": "rejected",
                "reason_codes": ("proposal_is_not_execution",),
            }
        )
    required_limits = tuple(
        dict.fromkeys(limit for item in selected for limit in item.limitations)
    )
    if required_limits and not set(required_limits).issubset(claim.limitations):
        return claim.model_copy(
            update={
                "validation": "weakened",
                "limitations": tuple(dict.fromkeys((*claim.limitations, *required_limits))),
                "reason_codes": ("limitations_restored",),
            }
        )
    return claim
