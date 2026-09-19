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
from dataclasses import dataclass, field
from time import perf_counter

from sqlalchemy import event
from sqlalchemy.engine import Engine

#: `FROM x`, `JOIN x`, `INTO x`, `UPDATE x`. Good enough to name the table a
#: statement touches, which is all the "largest repeated reads" column needs; a
#: real parser would buy nothing here and would have to be kept in step with SQL.
_TABLE = re.compile(
    r"\b(?:FROM|JOIN|INTO|UPDATE)\s+(?:ONLY\s+)?[\"']?([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)


@dataclass
class StepCost:
    """One step of the intake: how many statements, how long, and against what."""

    name: str
    queries: int = 0
    sql_ms: float = 0.0
    wall_ms: float = 0.0
    #: How many records this sweep produced. One sweep is not one order: the demo
    #: profile delivers several at once, and a cost reported per sweep would be a
    #: different number every time the profile changed its delivery size.
    produced: int = 1
    tables: Counter = field(default_factory=Counter)

    def repeated(self, limit: int = 6) -> list[tuple[str, int]]:
        """The tables this step read most, which is where its cost lives."""
        return [(table, n) for table, n in self.tables.most_common(limit) if n > 1]

    def as_record(self) -> dict:
        produced = max(self.produced, 1)
        return {
            "step": self.name,
            "produced": self.produced,
            "queries": round(self.queries / produced),
            "sql_ms": round(self.sql_ms / produced, 1),
            "wall_ms": round(self.wall_ms / produced, 1),
            "repeated_reads": [
                {"table": table, "count": n} for table, n in self.repeated()
            ],
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
        cost.queries += 1
        cost.sql_ms += (perf_counter() - began) * 1000
        match = _TABLE.search(statement)
        if match:
            cost.tables[match.group(1).lower()] += 1

    event.listen(engine, "before_cursor_execute", before)
    event.listen(engine, "after_cursor_execute", after)
    wall = perf_counter()
    try:
        yield cost
    finally:
        cost.wall_ms = (perf_counter() - wall) * 1000
        event.remove(engine, "before_cursor_execute", before)
        event.remove(engine, "after_cursor_execute", after)
