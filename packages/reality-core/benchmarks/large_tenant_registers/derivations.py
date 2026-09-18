"""What the canonical derivations cost, measured where the registers cannot see it.

The register cases read projections: work a worker already did, so their cost says
nothing about the derivation behind them. Analysis has no projection to read. Its
balance, open-item and stock objects run the canonical service at request time, over
the whole company unless the question narrows it, and that is the cost the register
benchmark is structurally blind to.

Each observation records the wall time, the number of statements and the rows
returned. The statement count is the part that means the same thing on any machine;
the milliseconds are for the recorded environment, like every other number here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from reality.services import core
from reality.services.finance.balances import party_balance_rows
from reality.services.inventory_positions import inventory_detail_rows

from .dataset import DatasetHandle

REPEATS = 3


@dataclass(frozen=True)
class DerivationObservation:
    name: str
    duration_ms: float
    statements: int
    rows: int
    per_input_us: float | None
    samples: int = REPEATS


def _count_statements(session: Session):
    """Count the reads one derivation issues, without changing what it does."""
    counter = {"n": 0}
    connection = session.connection()

    def listener(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            counter["n"] += 1

    event.listen(connection, "before_cursor_execute", listener)
    return counter, lambda: event.remove(connection, "before_cursor_execute", listener)


def _measure(
    session: Session, name: str, call: Callable[[], list[Any]], inputs: int | None
) -> DerivationObservation:
    """The fastest of several runs, because the slowest is the machine, not the code.

    A single sample of this taken on a loaded host reported a derivation as slower
    at half the data, which is not a thing that can be true. The minimum is the
    reading least contaminated by whatever else the host was doing; the statement
    count, which does not move between samples, is the part that means the same
    everywhere.
    """
    best: float | None = None
    statements = 0
    rows = 0
    for _ in range(REPEATS):
        counter, stop = _count_statements(session)
        try:
            started = perf_counter()
            result = call()
            duration = (perf_counter() - started) * 1000
        finally:
            stop()
        if best is None or duration < best:
            best = duration
        statements = counter["n"]
        rows = len(result)
    assert best is not None
    return DerivationObservation(
        name=name,
        duration_ms=best,
        statements=statements,
        rows=rows,
        per_input_us=(best * 1000 / inputs) if inputs else None,
    )


def run_derivations(
    session: Session, dataset: DatasetHandle
) -> list[DerivationObservation]:
    """Every canonical derivation an analysis object rests on, at this company's size.

    Run in the order a page would reach them, each in its own measurement, with no
    cache between them: this is what one request pays, not what a warm process does.
    """
    tenant_id = dataset.tenant_id
    finance_inputs = dataset.profile.financial_count
    # The inventory reads are not bounded by the article count: they fold movements,
    # reservations and open supplier promises, which grow with orders. Dividing by
    # 150 articles would report a number that means nothing, so they report none.
    item_inputs = None
    return [
        _measure(
            session,
            "financial_open_items",
            lambda: core.financial_open_items(session, tenant_id),
            finance_inputs,
        ),
        _measure(
            session,
            "aging_register",
            lambda: core.aging_register(session, tenant_id),
            finance_inputs,
        ),
        _measure(
            session,
            "party_balance_rows.customer",
            lambda: party_balance_rows(session, tenant_id, side="customer"),
            finance_inputs,
        ),
        _measure(
            session,
            "party_balance_rows.supplier",
            lambda: party_balance_rows(session, tenant_id, side="supplier"),
            finance_inputs,
        ),
        _measure(
            session,
            "inventory_rows",
            lambda: core.inventory_rows(session, tenant_id),
            item_inputs,
        ),
        _measure(
            session,
            "inventory_detail_rows",
            lambda: inventory_detail_rows(session, tenant_id),
            item_inputs,
        ),
    ]
