"""Validated deployment vocabulary for Business Journey Guide claims."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

JourneyStatus = Literal[
    "supported", "partial", "recognition_only", "missing", "out_of_scope"
]
EvidenceLevel = Literal["executable", "reviewed", "inferred", "none"]


class JourneyCatalogError(ValueError):
    """A deployment catalog is inconsistent and must not be published."""


class JourneyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: str = Field(min_length=1, max_length=2000)
    note: str = Field(default="", max_length=4000)


class JourneyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[A-R]\d{2}$")
    section: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    question: str = Field(min_length=1, max_length=500)
    status: JourneyStatus
    evidence_level: EvidenceLevel
    summary: str = Field(min_length=1, max_length=1000)
    limitations: tuple[str, ...] = Field(default=(), max_length=20)
    keywords: tuple[str, ...] = Field(default=(), max_length=40)
    question_examples: tuple[str, ...] = Field(default=(), max_length=20)
    tools: tuple[str, ...] = Field(default=(), max_length=30)
    demo_references: tuple[str, ...] = Field(default=(), max_length=30)
    product_paths: tuple[str, ...] = Field(default=(), max_length=20)
    related_journeys: tuple[str, ...] = Field(default=(), max_length=30)
    internal_evidence: tuple[JourneyEvidence, ...] = Field(default=(), max_length=30)

    @model_validator(mode="after")
    def evidence_matches_status(self) -> JourneyEntry:
        if self.status == "supported" and self.evidence_level != "executable":
            raise ValueError(f"{self.id}: supported requires executable evidence")
        if self.status != "supported" and not self.limitations:
            raise ValueError(f"{self.id}: non-supported status requires a limitation")
        return self

    def public_payload(self) -> dict[str, object]:
        return self.model_dump(
            mode="json",
            exclude={"internal_evidence"},
        )


class JourneyCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(ge=1)
    entries: tuple[JourneyEntry, ...]

    @model_validator(mode="after")
    def references_resolve(self) -> JourneyCatalog:
        identifiers = [entry.id for entry in self.entries]
        if len(identifiers) != len(set(identifiers)):
            duplicate = next(value for value in identifiers if identifiers.count(value) > 1)
            raise ValueError(f"Duplicate journey id: {duplicate}")
        known = set(identifiers)
        for entry in self.entries:
            for related in entry.related_journeys:
                if related not in known:
                    raise ValueError(f"{entry.id}: related journey {related} does not exist")
        return self

    def public_payload(self) -> dict[str, object]:
        return {
            "version": self.version,
            "statuses": {
                "supported": "Proven end to end by executable evidence.",
                "partial": "Only part of the journey is currently proven.",
                "recognition_only": "Related evidence is recognizable; the full journey is not proven.",
                "missing": "The current model or services do not support the complete journey.",
                "out_of_scope": "Deliberately outside the current product scope.",
            },
            "entries": [entry.public_payload() for entry in self.entries],
        }


def load_journey_catalog(payload: dict[str, Any]) -> JourneyCatalog:
    """Validate a catalog and present stable, actionable validation failures."""
    try:
        return JourneyCatalog.model_validate(payload)
    except ValueError as error:
        message = str(error)
        match = re.search(r"Value error, (.+)", message)
        raise JourneyCatalogError(match.group(1) if match else message) from error
