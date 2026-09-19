"""What one step of the intake costs, counted where the cost is.

Spec 181 FR-001 is about reads that grow with a company's history, and FR-006 says
the measurement must live in the repository rather than in somebody's scratch
directory. The numbers in `research.md` came from scripts that no longer exist,
which is why nobody can say today whether the ingest path got better or worse.

Two quantities matter and they do not age the same way. The **query count** means
the same on any machine and is what a regression test can hold. The **SQL time**
belongs to the host it was measured on. Both are recorded; only the first is worth
comparing across machines.

The per-table counts are the third column of the table in `research.md` — the one
that named `tenant` ×17 and `playground_run` ×12 per order and so said, without
any further analysis, where the cost was.
"""

from __future__ import annotations

import re
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import perf_counter

from sqlalchemy import event
from sqlalchemy.engine import Engine

#: True while the intake service is running, so a statement can be attributed to
#: interpreting a record rather than to the sweep that found it. Set by
#: `interpreting()`, which the fixture wraps around the two service calls.
_INTERPRETING: ContextVar[bool] = ContextVar("ingest_interpreting", default=False)


@contextmanager
def interpreting():
    """Mark the span that is the product's own work.

    A scheduler occurrence does two different things, and until they were told
    apart a reading of it could be — and was — mistaken for the first alone:
    it *selects* what to do, which for synthetic companies means the demo
    generator's own bookkeeping, and it *interprets* a record, which is the path
    every real intake takes and the one FR-001 is about.
    """
    token = _INTERPRETING.set(True)
    try:
        yield
    finally:
        _INTERPRETING.reset(token)


#: `FROM x`, `JOIN x`, `INTO x`, `UPDATE x`. Good enough to name the table a
#: statement touches, which is all the "largest repeated reads" column needs; a
#: real parser would buy nothing here and would have to be kept in step with SQL.
_TABLE = re.compile(
    r"\b(?:FROM|JOIN|INTO|UPDATE)\s+(?:ONLY\s+)?[\"']?([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)


def _shape(statement: str) -> str:
    """One statement without its parameters, so repetitions of it add up.

    Two executions of the same query with different values are the same shape and
    belong in one row; that is what makes "this statement is where the time went"
    a sentence somebody can act on.
    """
    collapsed = " ".join(statement.split())
    return collapsed[:400]


@dataclass
class StepCost:
    """One step of the intake: how many statements, how long, and against what."""

    name: str
    queries: int = 0
    sql_ms: float = 0.0
    wall_ms: float = 0.0
    #: How many records this sweep produced. The runner keeps only sweeps that
    #: produced exactly one, because a sweep's fixed cost divided by two records
    #: and by three are not two readings of the same thing — comparing them across
    #: checkpoints invents growth that is only the divisor moving.
    produced: int = 1
    #: The part of the above that was interpreting a record rather than selecting
    #: it. The difference is the sweep's own overhead — for a synthetic company,
    #: the demo generator's selection, throttle and idempotency checks, which no
    #: real intake runs.
    interpreting_queries: int = 0
    interpreting_ms: float = 0.0
    tables: Counter = field(default_factory=Counter)
    #: Milliseconds and count per statement shape, so a step whose statement count
    #: stays flat while its time grows can say which statement grew. That is the
    #: failure this column exists for: the same query reading more rows as the
    #: company fills up is invisible in a count and fatal at size.
    statements: dict = field(default_factory=dict)

    def repeated(self, limit: int = 6) -> list[tuple[str, int]]:
        """The tables this step read most, which is where its cost lives."""
        return [(table, n) for table, n in self.tables.most_common(limit) if n > 1]

    def slowest(self, limit: int = 5, interpreting: bool | None = True) -> list[dict]:
        """The statement shapes this step spent most of its time in.

        `interpreting` selects the span: True for the product's own work, False for
        the sweep's selection around it. Without that the list is dominated by
        whichever span is dearer, which is how a demo throttle came to look like an
        intake problem.
        """
        rows = [
            row
            for row in self.statements.values()
            if interpreting is None or row["interpreting"] in (interpreting, None)
        ]
        ranked = sorted(rows, key=lambda row: -row["ms"])
        return [
            {
                "sql": row["sql"],
                "ms": round(row["ms"], 1),
                "count": row["count"],
                "span": (
                    "both"
                    if row["interpreting"] is None
                    else ("interpreting" if row["interpreting"] else "sweep")
                ),
            }
            for row in ranked[:limit]
        ]

    def as_record(self) -> dict:
        produced = max(self.produced, 1)
        return {
            "step": self.name,
            "produced": self.produced,
            "queries": round(self.queries / produced),
            "sql_ms": round(self.sql_ms / produced, 1),
            "wall_ms": round(self.wall_ms / produced, 1),
            "interpreting_queries": round(self.interpreting_queries / produced),
            "interpreting_ms": round(self.interpreting_ms / produced, 1),
            "repeated_reads": [
                {"table": table, "count": n} for table, n in self.repeated()
            ],
            "slowest_interpreting": self.slowest(interpreting=True),
            "slowest_sweep": self.slowest(interpreting=False),
        }


@contextmanager
def measured(engine: Engine, name: str):
    """Count every statement one step issues, and say which table each touched."""
    cost = StepCost(name)
    started: dict[int, float] = {}

    def before(conn, cursor, statement, parameters, context, executemany):
        started[id(cursor)] = perf_counter()

    def after(conn, cursor, statement, parameters, context, executemany):
        began = started.pop(id(cursor), None)
        if began is None:
            return
        elapsed = (perf_counter() - began) * 1000
        cost.queries += 1
        cost.sql_ms += elapsed
        if _INTERPRETING.get():
            cost.interpreting_queries += 1
            cost.interpreting_ms += elapsed
        match = _TABLE.search(statement)
        if match:
            cost.tables[match.group(1).lower()] += 1
        shape = _shape(statement)
        row = cost.statements.setdefault(
            shape,
            {"sql": shape, "ms": 0.0, "count": 0, "interpreting": _INTERPRETING.get()},
        )
        row["ms"] += elapsed
        row["count"] += 1
        # A shape reached from both spans belongs to neither exclusively; saying so
        # is better than picking the span that happened to run it first.
        if row["interpreting"] != _INTERPRETING.get():
            row["interpreting"] = None

    event.listen(engine, "before_cursor_execute", before)
    event.listen(engine, "after_cursor_execute", after)
    wall = perf_counter()
    try:
        yield cost
    finally:
        cost.wall_ms = (perf_counter() - wall) * 1000
        event.remove(engine, "before_cursor_execute", before)
        event.remove(engine, "after_cursor_execute", after)
