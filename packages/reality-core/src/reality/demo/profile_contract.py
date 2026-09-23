"""Bounded manifest validation for the versioned canonical profile."""

import json
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseReference(BaseModel):
    model_config = ConfigDict(extra="allow")
    source_id: str
    document_id: str
    line_id: str
    commitment_id: str


class ProfileManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parties: dict[str, str]
    items: dict[str, str]
    locations: dict[str, str]
    cases: dict[str, dict[str, str]]
    windows: dict[str, str]
    capabilities: dict[str, str]
    costing_cases: dict[str, dict] = Field(default_factory=dict)
    cost_readiness: dict = Field(default_factory=dict)
    execution: bool = Field(exclude=True)

    @model_validator(mode="after")
    def validate_references(self):
        expected = (2, 2, 1) if self.execution else (24, 18, 2)
        for references, count in zip(
            (self.parties, self.items, self.locations), expected, strict=True
        ):
            if len(references) != count or len(set(references.values())) != count:
                raise ValueError("Profile references are incomplete or duplicated.")
        keys = (
            {"E01", "E02"}
            if self.execution
            else {f"O{i:02}" for i in range(1, 11)} | {"S01", "S02", "S03"}
        )
        for key in keys:
            CaseReference.model_validate(self.cases[key])
        prior = datetime.fromisoformat(self.windows["prior_start"])
        current = datetime.fromisoformat(self.windows["current_start"])
        end = datetime.fromisoformat(self.windows["end"])
        if current - prior != timedelta(days=42) or end - current != timedelta(days=42):
            raise ValueError("Profile comparison windows must be adjacent and equal.")
        if len(json.dumps(self.model_dump()).encode()) > 60000:
            raise ValueError("Profile manifest exceeds its bound.")
        return self
