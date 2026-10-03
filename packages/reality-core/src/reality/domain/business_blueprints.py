"""Read-only explanation contracts; none of these values is business authority."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceEvidence(EvidenceModel):
    id: str
    path: str
    function: str
    start_line: int
    end_line: int
    digest: str
    code: str
    limitations: tuple[str, ...] = ()


class RuleNode(EvidenceModel):
    id: str
    function: str
    kind: str
    text: str
    expression: str
    evidence_id: str
    line: int
    end_line: int
    predicates: tuple[str, ...] = ()
    durable: bool = False
    context: tuple[str, ...] = ()


class RuleEdge(EvidenceModel):
    source: str
    target: str
    outcome: str = "next"


class TestFact(EvidenceModel):
    name: str
    value: Any
    origin: str
    currency: str | None = None
    unit: str | None = None


class TestScenario(EvidenceModel):
    id: str
    name: str
    path: str
    line: int
    digest: str
    setup: tuple[str, ...] = ()
    action: tuple[str, ...] = ()
    expectations: tuple[str, ...] = ()
    facts: tuple[TestFact, ...] = ()
    assumptions: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()
    relationship: Literal["candidate", "assertion_linked"] = "candidate"
    test_type: str = "service"
    parameters: dict[str, Any] = Field(default_factory=dict)
    code: str = ""
    helpers: tuple[SourceEvidence, ...] = ()
    run: dict[str, Any] = Field(
        default_factory=lambda: {"outcome": "unknown", "revision_match": False}
    )


class BusinessStep(EvidenceModel):
    id: str
    function: str
    kind: str
    text: str
    rule_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    line: int


class BusinessScenario(EvidenceModel):
    id: str
    title: str
    given: tuple[str, ...] = ()
    when: tuple[str, ...] = ()
    then: tuple[str, ...] = ()
    notice: str
    unexplained_assertions: int = 0
    assertion_indices: tuple[int, ...] = ()


class BusinessOverview(EvidenceModel):
    text: str
    evidence_ids: tuple[str, ...]


class BusinessPresentation(EvidenceModel):
    language: str
    heading: str
    notice: str
    mode: Literal["llm", "unavailable", "outdated"] = "unavailable"
    model: str | None = None
    overview: BusinessOverview | None = None
    diagram_notice: str = ""
    steps: tuple[BusinessStep, ...] = ()
    edges: tuple[RuleEdge, ...] = ()
    scenarios: tuple[BusinessScenario, ...] = ()
    unexplained_rules: int = 0


class Blueprint(EvidenceModel):
    contract_version: int = 1
    kind: str
    key: str
    label: str
    purpose: str
    release: dict[str, Any]
    status: Literal["complete", "partial", "missing", "outdated"]
    limitations: tuple[str, ...] = ()
    nodes: tuple[RuleNode, ...] = ()
    edges: tuple[RuleEdge, ...] = ()
    sources: tuple[SourceEvidence, ...] = ()
    scenarios: tuple[TestScenario, ...] = ()
    test_gaps: tuple[str, ...] = ()
    requirements: tuple[str, ...] = ()
    consumers: tuple[str, ...] = ()
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    runtime_values: dict[str, Any] = Field(default_factory=dict)
    evidence_digest: str = ""
    presentation_language: str = "en"
    context: str = "running_implementation"
    business: BusinessPresentation | None = None


class CaseFact(EvidenceModel):
    name: str = Field(min_length=1, max_length=150)
    value: str | bool | None
    currency: str | None = Field(default=None, max_length=3)
    unit: str | None = Field(default=None, max_length=30)


class RecordReference(EvidenceModel):
    kind: Literal["party", "order", "commitment"]
    id: str = Field(min_length=1, max_length=150)


class CompareInput(EvidenceModel):
    kind: str = Field(max_length=30)
    key: str = Field(max_length=150)
    evidence_digest: str | None = Field(default=None, max_length=64)
    scenario_ids: list[str] = Field(default_factory=list, max_length=20)
    facts: list[CaseFact] = Field(default_factory=list, max_length=100)
    record: RecordReference | None = None
    language: str = Field(default="en", max_length=5)


class DiscoveryInput(EvidenceModel):
    query: str = Field(default="", max_length=200)
    kind: (
        Literal["command", "tool", "action", "view", "projection", "exception"] | None
    ) = None
    cursor: int = Field(default=0, ge=0)
    limit: int = Field(default=25, ge=1, le=100)
