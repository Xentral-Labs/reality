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


class SlowStatement(BaseModel):
    sql: str
    ms: float = Field(ge=0)
    count: int = Field(ge=1)
    span: Literal["interpreting", "sweep", "both"] = "both"


class StepResult(BaseModel):
    step: Literal["order", "invoice", "payment"]
    produced: int = Field(ge=0)
    queries: int = Field(ge=0)
    sql_ms: float = Field(ge=0)
    wall_ms: float = Field(ge=0)
    #: The part of the above that interpreted a record. The remainder is the
    #: sweep's own selection work, which for a synthetic company is the demo
    #: generator's and which no real intake runs.
    interpreting_queries: int = Field(default=0, ge=0)
    interpreting_ms: float = Field(default=0, ge=0)
    repeated_reads: list[RepeatedRead] = []
    #: The same, for the interpreting span alone — what one record costs, without
    #: the sweep that found it. The two differ by more than they look: a table the
    #: demo generator polls is not a table the intake reads.
    repeated_interpreting_reads: list[RepeatedRead] = []
    slowest_interpreting: list[SlowStatement] = []
    slowest_sweep: list[SlowStatement] = []


class TableSize(BaseModel):
    """What one table costs to keep, split by what the bytes are doing.

    The three are separated because they are three different decisions. The heap
    is the rows somebody's work produced. The indexes are a choice about reads,
    and in this schema they frequently outweigh the rows they point at. What sits
    out of line is the large text PostgreSQL moved aside on its own — the payload
    a tiered store would take over (spec 181 FR-005).
    """

    table_name: str
    estimated_rows: int = Field(ge=0)
    heap_bytes: int = Field(ge=0)
    index_bytes: int = Field(ge=0)
    out_of_line_bytes: int = Field(ge=0)

    @property
    def total_bytes(self) -> int:
        return self.heap_bytes + self.index_bytes + self.out_of_line_bytes


class TableBlocker(BaseModel):
    """A tenant-scoped table and the uniqueness promises that pin it to one cluster.

    PostgreSQL will not partition a table unless every unique constraint contains
    the partition key, so each name here is a constraint that would have to change
    before this table could be split by company.
    """

    table_name: str
    constraints: list[str] = Field(min_length=1)


class StorageShape(BaseModel):
    """Where a company's bytes went, and what the schema would allow (FR-005)."""

    orders: int = Field(ge=0)
    tables: list[TableSize] = []
    blocked_from_tenant_partitioning: list[TableBlocker] = []

    @property
    def total_bytes(self) -> int:
        return sum(table.total_bytes for table in self.tables)

    @property
    def bytes_per_order(self) -> int | None:
        """What one order to cash leaves behind, or None before there is one.

        The database's absolute size is a property of how far the fixture was
        driven. This is the figure that can be held against another run.
        """
        return round(self.total_bytes / self.orders) if self.orders else None


class SampleResult(BaseModel):
    orders_before: int = Field(ge=0)
    steps: list[StepResult]
    #: Absent in records written before storage was measured, so an older run
    #: still loads rather than becoming unreadable (spec 181 FR-005).
    storage: StorageShape | None = None

    @property
    def queries(self) -> int:
        return sum(step.queries for step in self.steps)

    @property
    def sql_ms(self) -> float:
        return sum(step.sql_ms for step in self.steps)

    @property
    def interpreting(self) -> int:
        """What a real intake pays, which is what SC-001 is about."""
        return sum(step.interpreting_queries for step in self.steps)


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
                (
                    "Table sizes include whatever autovacuum has not yet reclaimed, "
                    "so two runs can differ by the timing of a background process "
                    "and not by a byte of data."
                ),
                (
                    "The storage recorded here is the ingested half. This run never "
                    "refreshes a projection, so `projection_row` — the largest table "
                    "in a worked company — stays empty, and the job history never "
                    "reaches the size a company accumulates minute by minute."
                ),
            ],
            **meta,
        )

    def growth(self) -> float | None:
        """How much dearer one order to cash is at the largest size than the smallest.

        `None` when the samples do not hold the same steps. A sample whose payment
        step found no single-record sweep is not a cheaper order to cash, it is an
        incomplete measurement — and dividing one by the other produced a 0.53x
        "improvement" that was nothing but a missing step (spec 181 SC-005).
        """
        if len(self.samples) < 2:
            return None
        shapes = {tuple(step.step for step in sample.steps) for sample in self.samples}
        if len(shapes) > 1:
            return None
        first, last = self.samples[0].interpreting, self.samples[-1].interpreting
        return round(last / first, 2) if first else None

    def summary(self) -> str:
        lines = [
            f"{'orders':>8}  {'interp.':>8}  {'sweep':>8}  {'SQL ms':>8}   per step",
        ]
        for sample in self.samples:
            steps = "  ".join(
                f"{step.step} {step.queries}/{step.sql_ms:.0f}ms"
                for step in sample.steps
            )
            lines.append(
                f"{sample.orders_before:>8}  {sample.interpreting:>8}  "
                f"{sample.queries:>8}  {sample.sql_ms:>8.0f}   {steps}"
            )
        storage = [
            sample.storage for sample in self.samples if sample.storage is not None
        ]
        if storage:
            lines.append("")
            lines.append(
                f"{'orders':>8}  {'kept':>10}  {'per order':>10}   largest tables"
            )
            for shape in storage:
                largest = "  ".join(
                    f"{table.table_name} {human_bytes(table.total_bytes)}"
                    for table in shape.tables[:3]
                )
                per_order = shape.bytes_per_order
                lines.append(
                    f"{shape.orders:>8}  {human_bytes(shape.total_bytes):>10}  "
                    f"{(human_bytes(per_order) if per_order else '-'):>10}   {largest}"
                )
            blocked = storage[-1].blocked_from_tenant_partitioning
            lines.append("")
            lines.append(
                f"{len(blocked)} tenant-scoped tables cannot be partitioned by "
                "company: a unique constraint does not contain the tenant "
                "(spec 181 FR-005)."
                if blocked
                else "Every tenant-scoped table could be partitioned by company."
            )
        growth = self.growth()
        lines.append("")
        if growth is not None:
            lines.append(
                f"interpreting queries per order to cash, largest against smallest:"
                f" {growth}x (SC-001 allows 1.20)"
            )
        else:
            lines.append(
                "No ratio: the samples do not hold the same steps, so the largest "
                "and the smallest are not the same measurement."
            )
        return "\n".join(lines)


def human_bytes(count: int) -> str:
    """Bytes in the unit a reader can hold in their head."""
    size = float(count)
    for unit in ("B", "kB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


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
        "Two numbers per step. **Interpreting** is what a real intake pays for one",
        "record: `enqueue_source` and `process_import_job_bound`, the path SC-001 is",
        "about. **Sweep** is the whole scheduler occurrence, which for a synthetic",
        "company also carries the demo generator's selection, throttle and idempotency",
        "work — cost no customer's company runs.",
        "",
        "| Orders before | Step | Records | Interpreting | Sweep | ms (interp./sweep) | Largest repeated reads |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for sample in result.samples:
        for step in sample.steps:
            repeated = (
                ", ".join(f"`{row.table}` ×{row.count}" for row in step.repeated_reads)
                or "—"
            )
            lines.append(
                f"| {sample.orders_before} | {step.step} | {step.produced} "
                f"| {step.interpreting_queries} | {step.queries} "
                f"| {step.interpreting_ms:.0f} / {step.sql_ms:.0f} | {repeated} |"
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

    def statement_rows(attribute: str):
        return [
            (sample.orders_before, step.step, row)
            for sample in result.samples
            for step in sample.steps
            for row in getattr(step, attribute)[:2]
        ]

    def statement_table(title: str, explanation: str, rows) -> None:
        if not rows:
            return
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                explanation,
                "",
                "| Orders before | Step | ms | Runs | Span | Statement |",
                "|---:|---|---:|---:|---|---|",
            ]
        )
        for orders, step, row in rows:
            sql = row.sql[:150].replace("|", "\\|")
            lines.append(
                f"| {orders} | {step} | {row.ms:.0f} | {row.count} | {row.span} "
                f"| `{sql}` |"
            )

    statement_table(
        "Where the interpreting time went",
        "Only the product's own span. A step whose statement count stays flat while "
        "its time grows has one query reading more rows, and this names it.",
        statement_rows("slowest_interpreting"),
    )
    statement_table(
        "Where the sweep time went",
        "Selection, throttle and idempotency around the interpreting. For a "
        "synthetic company this is the demo generator, which no customer's company "
        "runs — listing it beside the product's own work is how a demo throttle "
        "once looked like an intake problem.",
        statement_rows("slowest_sweep"),
    )
    storage = [
        sample.storage for sample in result.samples if sample.storage is not None
    ]
    if storage:
        latest = storage[-1]
        lines += [
            "",
            "## What the data costs to keep",
            "",
            (
                "Three columns, because they are three different decisions. **Rows** "
                "is the work somebody did. **Indexes** is a choice about reads, and "
                "in this schema it frequently outweighs the rows it points at. **Out "
                "of line** is the large text PostgreSQL moved aside by itself — the "
                "payload spec 181 FR-005 would give to a tiered store. A small "
                "figure repeated across tables is that store existing and standing "
                "empty, not payload sitting in it: nothing here is large enough for "
                "PostgreSQL to move, so the payloads are in the rows."
            ),
            "",
            f"At {latest.orders} orders the company keeps "
            f"**{human_bytes(latest.total_bytes)}**"
            + (
                f", or **{human_bytes(latest.bytes_per_order)} per order to cash**."
                if latest.bytes_per_order
                else "."
            ),
            "",
            "| Table | Rows | Rows (bytes) | Indexes | Out of line | Total |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for table in latest.tables[:15]:
            lines.append(
                f"| `{table.table_name}` | {table.estimated_rows} "
                f"| {human_bytes(table.heap_bytes)} "
                f"| {human_bytes(table.index_bytes)} "
                f"| {human_bytes(table.out_of_line_bytes)} "
                f"| {human_bytes(table.total_bytes)} |"
            )
        blocked = latest.blocked_from_tenant_partitioning
        lines += ["", "## What the keys would allow", ""]
        if blocked:
            lines += [
                (
                    "PostgreSQL refuses to partition a table unless every unique "
                    "constraint contains the partition key, the primary key "
                    f"included. **{len(blocked)} tenant-scoped tables** are held "
                    "back by a constraint that does not name the company, so "
                    "FR-005's first clause is a list of constraints to change "
                    "rather than a partitioning strategy to choose."
                ),
                "",
                "| Table | Constraints that do not contain the tenant |",
                "|---|---|",
            ]
            for entry in blocked:
                names = ", ".join(f"`{name}`" for name in entry.constraints)
                lines.append(f"| `{entry.table_name}` | {names} |")
        else:
            lines.append(
                "Every tenant-scoped table's uniqueness promises contain the "
                "company, so each could be partitioned by tenant."
            )
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
