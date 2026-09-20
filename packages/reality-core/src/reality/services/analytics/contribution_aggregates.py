"""Internal SQL arithmetic over an already admitted contribution population.

This module does not load or authorize slices. The caller owns tenant/context
admission, unique slice grain, currency/unit partitions and cache protection.
Never pass unreviewed source evidence as an admitted population or paginate it
before aggregation. No compiler or transport may invent a second DB definition.
"""

from decimal import Decimal

from sqlalchemy import Numeric, and_, case, cast, func, literal, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import FromClause

from reality.domain.contribution import CONTRIBUTION_TERMS


def _rate(margin: ColumnElement, revenue: ColumnElement) -> ColumnElement:
    """Exact signed half-even percentage, avoiding PostgreSQL round's tie rule."""
    # Multiplication converts the percentage to units of its four-place display.
    numerator = func.abs(margin) * 1_000_000
    denominator = func.nullif(revenue, 0)
    whole = func.div(numerator, denominator)
    remainder = func.mod(numerator, denominator)
    increment = case(
        (remainder * 2 > denominator, 1),
        (and_(remainder * 2 == denominator, func.mod(whole, 2) == 1), 1),
        else_=0,
    )
    rounded = cast(
        func.sign(margin) * (whole + increment) * Decimal("0.0001"), Numeric()
    )
    return case((revenue > 0, rounded))


def contribution_aggregate_columns(
    source: FromClause, *, reviewed: bool
) -> tuple[ColumnElement, ...]:
    """Build fixed commercial_v1 aggregates, with independent coverage counters.

    Each input has a numeric column named by CONTRIBUTION_TERMS and a companion
    `<name>_state` in reviewed/evidenced/provisional/unknown. Input admission must
    validate that known states carry amounts; defensive SQL also excludes nulls.
    An empty aggregate has zero counters/known amounts, never a final zero.
    `reviewed=False` keeps preview actual subtotals but suppresses final values.
    """
    if type(reviewed) is not bool:
        raise ValueError("Reviewed context must be explicit boolean.")
    required = func.count()
    output = []
    totals = {}
    for name, fields in CONTRIBUTION_TERMS.items():
        amounts = [source.c[field] for field in fields]
        states = [source.c[f"{field}_state"] for field in fields]
        present = and_(*(amount.is_not(None) for amount in amounts))
        actual = and_(
            present, *(state.in_(("reviewed", "evidenced")) for state in states)
        )
        confirmed = and_(present, *(state == "reviewed" for state in states))
        provisional = or_(*(state == "provisional" for state in states))
        expression = amounts[0]
        for amount in amounts[1:]:
            expression = expression - amount
        known = func.coalesce(func.sum(case((actual, expression), else_=0)), 0)
        covered = func.count().filter(confirmed)
        total = case(
            (and_(literal(reviewed), required > 0, covered == required), known)
        )
        totals[name] = total
        stats = {
            "known": known,
            "total": total,
            "required": required,
            "covered": covered,
            "evidenced": func.count().filter(actual),
            "provisional": func.count().filter(provisional),
        }
        output.extend(
            expression.label(f"{name}_{stat}") for stat, expression in stats.items()
        )
    output.extend(
        _rate(totals[name], totals["revenue"]).label(f"{name}_rate")
        for name in ("db1", "db2")
    )
    return tuple(output)
