from __future__ import annotations

import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .cases import CaseObservation
from .dataset import DatasetHandle


class EnvironmentResult(BaseModel):
    python: str
    platform: str
    postgresql: str
    working_tree_digest: str = Field(min_length=64, max_length=64)


class DatasetResult(BaseModel):
    definition_version: str
    profile: Literal["reduced", "full"]
    seed: int
    business_date: str
    tenant_id: str
    control_tenant_id: str
    cardinalities: dict[str, int]


class CaseResult(BaseModel):
    case_id: str
    register_family: str
    duration_ms: float = Field(ge=0)
    outcome: Literal["passed", "failed"]
    requirements: list[str]
    observations: dict[str, Any]
    query_evidence: list[dict[str, Any]]


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(title="Large-Tenant Register Benchmark Result")

    result_version: Literal["1"]
    created_at: datetime
    git_revision: str = Field(min_length=7)
    schema_revision: str = Field(min_length=1)
    environment: EnvironmentResult
    dataset: DatasetResult
    cases: list[CaseResult] = Field(min_length=9)
    outcome: Literal["passed", "failed"]
    limitations: list[str] = Field(min_length=1)

    @classmethod
    def from_run(
        cls,
        dataset: DatasetHandle,
        observations: list[CaseObservation],
        *,
        git_revision: str,
        schema_revision: str = "metadata-current",
        postgresql: str = "test PostgreSQL",
        working_tree_digest: str = "0" * 64,
    ) -> BenchmarkResult:
        return cls(
            result_version="1",
            created_at=datetime.now(UTC),
            git_revision=git_revision,
            schema_revision=schema_revision,
            environment=EnvironmentResult(
                python=sys.version.split()[0],
                platform=platform.platform(),
                postgresql=postgresql,
                working_tree_digest=working_tree_digest,
            ),
            dataset=DatasetResult(
                definition_version=dataset.definition_version,
                profile=dataset.profile.name,
                seed=dataset.profile.seed,
                business_date=dataset.profile.business_date.isoformat(),
                tenant_id=dataset.tenant_id,
                control_tenant_id=dataset.control_tenant_id,
                cardinalities=dataset.cardinalities,
            ),
            cases=[CaseResult.model_validate(vars(row)) for row in observations],
            outcome="passed"
            if all(row.outcome == "passed" for row in observations)
            else "failed",
            limitations=[
                "Durations are observations for the recorded environment, not universal latency guarantees.",
                "This result proves bounded reads at recorded cardinality, not ingestion throughput or concurrent production capacity.",
                "Initial projection construction is excluded from register timings and remains future capacity-work evidence, not a proven production throughput path.",
            ],
        )


def semantic_result(observations: list[CaseObservation]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": row.case_id,
            "register_family": row.register_family,
            "outcome": row.outcome,
            "requirements": list(row.requirements),
            "observations": row.observations,
            "query_evidence": row.query_evidence,
        }
        for row in observations
    ]


def render_markdown(result: BenchmarkResult) -> str:
    lines = [
        "# Large-Tenant Register Benchmark Result",
        "",
        f"- Outcome: **{result.outcome.upper()}**",
        f"- Revision: `{result.git_revision}`",
        f"- Schema revision: `{result.schema_revision}`",
        f"- Profile: `{result.dataset.profile}`",
        f"- Business date: `{result.dataset.business_date}`",
        f"- Orders: `{result.dataset.cardinalities['orders']}`",
        f"- PostgreSQL: `{result.environment.postgresql}`",
        f"- Tested-content SHA-256: `{result.environment.working_tree_digest}`",
        "",
        "## Dataset cardinalities",
        "",
        "| Record family | Count |",
        "|---|---:|",
        *(
            f"| {name.replace('_', ' ').title()} | {count} |"
            for name, count in result.dataset.cardinalities.items()
        ),
        "",
        "## Cases",
        "",
        "| Family | Outcome | Duration (ms) | Rows / total |",
        "|---|---|---:|---:|",
    ]
    for case in result.cases:
        rows = case.observations.get("default_count", "—")
        total = case.observations.get("default_total", "—")
        lines.append(
            f"| {case.register_family} | {case.outcome} | {case.duration_ms:.3f} | {rows} / {total} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in result.limitations)
    return "\n".join(lines) + "\n"


def write_result(result: BenchmarkResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(render_markdown(result), encoding="utf-8")


def write_schema(output: Path) -> None:
    output.write_text(
        json.dumps(BenchmarkResult.model_json_schema(), indent=2) + "\n",
        encoding="utf-8",
    )
