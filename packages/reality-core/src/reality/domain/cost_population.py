"""Exact population closure for a trusted company-generation builder.

This proves membership against a supplied frozen census, not that the census covers
all company evidence. It performs no financial calculation, authorization, persisted
content verification or publication. Report readers must never build this population.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

Identity = Annotated[str, Field(strict=True, min_length=1, max_length=128)]
Fingerprint = Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
Support = Literal["known", "unknown"]


class PopulationRefusal(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class PopulationBasis(_Frozen):
    """Trusted census context; each subject retains its own policy/review basis."""

    tenant_id: Identity
    effective_at: AwareDatetime
    knowledge_at: AwareDatetime
    event_sequence: int = Field(ge=0, strict=True)
    inventory_algorithm: Literal["inventory-v1"] = "inventory-v1"
    contribution_algorithm: Literal["commercial-v1"] = "commercial-v1"

    @field_validator("effective_at", "knowledge_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class InventoryExpectation(_Frozen):
    """One item in the supported single-ownership-pool inventory model."""

    item_id: Identity
    input_fingerprint: Fingerprint


class ContributionExpectation(_Frozen):
    """One line in the supported whole-line commercial matching model."""

    document_line_id: Identity
    input_fingerprint: Fingerprint


class InventoryObservation(InventoryExpectation):
    acquisition: Support
    carrying: Support

    @model_validator(mode="after")
    def support(self) -> Self:
        if self.carrying == "known" and self.acquisition != "known":
            raise ValueError("Carrying support requires supported acquisition cost.")
        return self


class ContributionObservation(ContributionExpectation):
    db1: Support
    db2: Support

    @model_validator(mode="after")
    def support(self) -> Self:
        if self.db2 == "known" and self.db1 != "known":
            raise ValueError("DB2 support requires supported DB1 inputs.")
        return self


class ExpectedPopulation(_Frozen):
    basis: PopulationBasis
    inventory: tuple[InventoryExpectation, ...] = ()
    contribution: tuple[ContributionExpectation, ...] = ()


class EvaluatedPopulation(_Frozen):
    basis: PopulationBasis
    inventory: tuple[InventoryObservation, ...] = ()
    contribution: tuple[ContributionObservation, ...] = ()


@dataclass(frozen=True)
class Coverage:
    expected: int
    covered: int

    @property
    def unknown(self) -> int:
        return self.expected - self.covered

    @property
    def state(self) -> Literal["empty", "partial", "complete"]:
        if not self.expected:
            return "empty"
        return "complete" if self.covered == self.expected else "partial"


@dataclass(frozen=True)
class PopulationClosure:
    basis: PopulationBasis
    inventory_rows: int
    contribution_rows: int
    acquisition: Coverage
    carrying: Coverage
    db1: Coverage
    db2: Coverage

    @property
    def has_financial_gaps(self) -> bool:
        return any(
            part.unknown
            for part in (self.acquisition, self.carrying, self.db1, self.db2)
        )


def _close_family(
    expected: tuple[InventoryExpectation, ...] | tuple[ContributionExpectation, ...],
    evaluated: tuple[InventoryObservation, ...] | tuple[ContributionObservation, ...],
    key: Literal["item_id", "document_line_id"],
) -> None:
    """O(n) builder work; equal counts alone cannot prove exact membership."""
    identities = {}
    for member in expected:
        identity = getattr(member, key)
        if identity in identities:
            raise PopulationRefusal("cost_population_duplicate")
        identities[identity] = member.input_fingerprint
    seen = set()
    for member in evaluated:
        identity = getattr(member, key)
        if identity in seen:
            raise PopulationRefusal("cost_population_duplicate")
        seen.add(identity)
        if identity not in identities:
            raise PopulationRefusal("cost_population_unexpected")
        if member.input_fingerprint != identities[identity]:
            raise PopulationRefusal("cost_population_input_mismatch")
    if len(seen) != len(identities):
        raise PopulationRefusal("cost_population_missing")


def close_population(
    tenant_id: str, expected: ExpectedPopulation, evaluated: EvaluatedPopulation
) -> PopulationClosure:
    """Close exact trusted input/output membership while retaining financial gaps.

    The service must construct these objects from retained scoped records, never API
    claims. Successful closure grants neither monetary integrity nor publication;
    output checksums, work/trace completion and atomic fencing remain separate gates.
    """
    if expected.basis.tenant_id != tenant_id or evaluated.basis != expected.basis:
        raise PopulationRefusal("cost_population_context_mismatch")
    _close_family(expected.inventory, evaluated.inventory, "item_id")
    _close_family(expected.contribution, evaluated.contribution, "document_line_id")
    inventory_rows, contribution_rows = (
        len(expected.inventory),
        len(expected.contribution),
    )
    return PopulationClosure(
        basis=expected.basis,
        inventory_rows=inventory_rows,
        contribution_rows=contribution_rows,
        acquisition=Coverage(
            inventory_rows,
            sum(row.acquisition == "known" for row in evaluated.inventory),
        ),
        carrying=Coverage(
            inventory_rows, sum(row.carrying == "known" for row in evaluated.inventory)
        ),
        db1=Coverage(
            contribution_rows, sum(row.db1 == "known" for row in evaluated.contribution)
        ),
        db2=Coverage(
            contribution_rows, sum(row.db2 == "known" for row in evaluated.contribution)
        ),
    )
