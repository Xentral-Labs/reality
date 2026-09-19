"""The machine-readable record spec 181 User Story 5 asks the measurement to leave."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RepeatedRead(BaseModel):
    table: str
    count: int = Field(ge=2)


class StepResult(BaseModel):
    step: Literal["order", "invoice", "payment"]
    produced: int = Field(ge=0)
    queries: int = Field(ge=0)
    sql_ms: float = Field(ge=0)
    wall_ms: float = Field(ge=0)
    repeated_reads: list[RepeatedRead] = []


class SampleResult(BaseModel):
    orders_before: int = Field(ge=0)
    steps: list[StepResult]

    @property
    def queries(self) -> int:
        return sum(step.queries for step in self.steps)

    @property
    def sql_ms(self) -> float:
        return sum(step.sql_ms for step in self.steps)


class IngestResult(BaseModel):
    """One run: the same order to cash, measured at a series of company sizes."""

    model_config = ConfigDict(title="Ingest Cost Measurement")

    result_version: Literal["1"] = "1"
    created_at: datetime
    git_revision: str = Field(min_length=7)
    python: str
    platform: str
    postgresql: str
    tenant_id: str
    samples: list[SampleResult] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @classmethod
    def from_samples(cls, samples: list[dict[str, Any]], **meta: Any) -> IngestResult:
        return cls(
            samples=[SampleResult.model_validate(row) for row in samples],
            limitations=[
                "Query counts mean the same on any host; the milliseconds do not.",
                (
                    "One intake process, no competing worker: this is the cost of "
                    "the path, not the throughput of a deployment."
                ),
                (
                    "SC-001 is a statement about a curve. A single checkpoint cannot "
                    "answer it, and the ratio is only as good as the largest size "
                    "measured."
                ),
            ],
            **meta,
        )

    def growth(self) -> float | None:
        """How much dearer one order to cash is at the largest size than the smallest."""
        if len(self.samples) < 2:
            return None
        first, last = self.samples[0].queries, self.samples[-1].queries
        return round(last / first, 2) if first else None

    def summary(self) -> str:
        lines = [
            f"{'orders':>8}  {'queries':>8}  {'SQL ms':>8}   per step",
        ]
        for sample in self.samples:
            steps = "  ".join(
                f"{step.step} {step.queries}/{step.sql_ms:.0f}ms"
                for step in sample.steps
            )
            lines.append(
                f"{sample.orders_before:>8}  {sample.queries:>8}  "
                f"{sample.sql_ms:>8.0f}   {steps}"
            )
        growth = self.growth()
        if growth is not None:
            lines.append("")
            lines.append(
                f"queries per order to cash, largest against smallest: {growth}x"
                " (SC-001 allows 1.20)"
            )
        return "\n".join(lines)


def render_markdown(result: IngestResult) -> str:
    lines = [
        "# Ingest Cost Measurement",
        "",
        f"- Revision: `{result.git_revision}`",
        f"- PostgreSQL: `{result.postgresql}`",
        f"- Python: `{result.python}` on `{result.platform}`",
        "",
        "## One order to cash, as the company grows",
        "",
        "| Orders before | Step | Records | Queries each | SQL ms each | Largest repeated reads |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for sample in result.samples:
        for step in sample.steps:
            repeated = (
                ", ".join(f"`{row.table}` ×{row.count}" for row in step.repeated_reads)
                or "—"
            )
            lines.append(
                f"| {sample.orders_before} | {step.step} | {step.produced} "
                f"| {step.queries} | {step.sql_ms:.0f} | {repeated} |"
            )
    growth = result.growth()
    if growth is not None:
        lines += [
            "",
            (
                f"Queries per order to cash grow **{growth}×** from the smallest "
                "measured company to the largest. SC-001 allows 1.20."
            ),
        ]
    lines += ["", "## Limitations", ""]
    lines += [f"- {limitation}" for limitation in result.limitations]
    return "\n".join(lines) + "\n"


def write_result(result: IngestResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(render_markdown(result), encoding="utf-8")


def write_schema(output: Path) -> None:
    output.write_text(
        json.dumps(IngestResult.model_json_schema(), indent=2) + "\n", encoding="utf-8"
    )
