"""PostgreSQL contribution aggregates preserve the commercial domain contract."""

from decimal import Decimal
from itertools import product

import pytest
from sqlalchemy import Numeric, String, column, false, select, values
from test_contribution import CONTEXT, row, value

from reality.domain.contribution import aggregate_contribution
from reality.services.analytics.contribution_aggregates import (
    contribution_aggregate_columns,
)

INPUTS = ("revenue", "goods_cost", "direct_selling_cost", "allocated_selling_cost")
MEASURES = (*INPUTS, "db1", "db2")
STATS = ("known", "total", "required", "covered", "evidenced", "provisional")


def population(rows):
    columns = [column("group_id", String)]
    for name in INPUTS:
        columns.extend((column(name, Numeric()), column(f"{name}_state", String)))
    data = [
        (
            r.slice_id,
            *(
                v
                for name in INPUTS
                for v in (getattr(r, name).amount, getattr(r, name).state)
            ),
        )
        for r in rows
    ]
    return values(*columns, name="admitted_slices").data(data)


def sql_group(session, rows, *, reviewed=True, empty=False):
    source = population(rows)
    statement = select(
        *contribution_aggregate_columns(source, reviewed=reviewed)
    ).select_from(source)
    if empty:
        statement = statement.where(false())
    return session.execute(statement).mappings().one()


def assert_parity(actual, expected):
    for name in MEASURES:
        for stat in STATS:
            assert actual[f"{name}_{stat}"] == getattr(getattr(expected, name), stat), (
                name,
                stat,
            )
    for name in ("db1_rate", "db2_rate"):
        assert actual[name] == getattr(expected, name)
        assert actual[name] is None or isinstance(actual[name], Decimal)


def test_every_input_state_combination_matches_domain(session):
    rows = []
    for index, states in enumerate(
        product(("reviewed", "evidenced", "provisional", "unknown"), repeat=4)
    ):
        rows.append(
            row(
                str(index),
                **{
                    name: value(None if state == "unknown" else amount, state)
                    for name, amount, state in zip(
                        INPUTS, ("1200", "630", "100", "14"), states, strict=True
                    )
                },
            )
        )
    source = population(rows)
    actual = (
        session.execute(
            select(
                source.c.group_id,
                *contribution_aggregate_columns(source, reviewed=True),
            ).group_by(source.c.group_id)
        )
        .mappings()
        .all()
    )
    by_id = {r.slice_id: r for r in rows}
    assert len(actual) == 256
    for result in actual:
        assert_parity(
            result,
            aggregate_contribution([by_id[result["group_id"]]], context=CONTEXT).groups[
                0
            ],
        )


@pytest.mark.parametrize("missing", INPUTS)
def test_partial_population_never_subtracts_unrelated_subtotals(session, missing):
    first = row(
        revenue=value("100"),
        goods_cost=value("60"),
        direct_selling_cost=value("10"),
        allocated_selling_cost=value(),
    )
    second = first.model_copy(update={"slice_id": "b", missing: value(None, "unknown")})
    rows = [first, second]
    actual = sql_group(session, rows)
    assert_parity(actual, aggregate_contribution(rows, context=CONTEXT).groups[0])
    assert actual["db2_total"] is None
    assert actual["db2_known"] == 30
    if missing == "goods_cost":
        assert actual["revenue_total"] == 200
        assert actual["goods_cost_known"] == 60
        assert actual["db1_known"] == 40


def test_signed_slices_and_weighted_rate(session):
    rows = [
        row("a", revenue=value("1000"), goods_cost=value("500")),
        row("b", revenue=value("100"), goods_cost=value("90")),
        row(
            "c",
            revenue=value("-100"),
            goods_cost=value("-50"),
            direct_selling_cost=value(),
            allocated_selling_cost=value(),
        ),
    ]
    actual = sql_group(session, rows)
    assert_parity(actual, aggregate_contribution(rows, context=CONTEXT).groups[0])
    assert actual["db1_rate"] == 46


@pytest.mark.parametrize(
    "revenue,goods,expected",
    [
        ("2000000", "1999999", "0.0000"),
        ("2000000", "1999997", "0.0002"),
        ("2000000", "2000001", "0.0000"),
        ("2000000", "2000003", "-0.0002"),
        ("99999999999999.9999", "0.0001", "100.0000"),
        ("0.0001", "99999999999999.9999", "-99999999999999999800.0000"),
        ("0", "1", None),
        ("-100", "1", None),
    ],
)
def test_exact_half_even_and_nonpositive_denominator(session, revenue, goods, expected):
    rows = [row(revenue=value(revenue), goods_cost=value(goods))]
    actual = sql_group(session, rows)
    assert_parity(actual, aggregate_contribution(rows, context=CONTEXT).groups[0])
    assert actual["db1_rate"] == (None if expected is None else Decimal(expected))


def test_empty_population_does_not_claim_reviewed_zero(session):
    actual = sql_group(session, [row()], empty=True)
    for name in MEASURES:
        assert actual[f"{name}_total"] is None
        for stat in set(STATS) - {"total"}:
            assert actual[f"{name}_{stat}"] == 0
    assert actual["db1_rate"] is actual["db2_rate"] is None


def test_preview_keeps_known_amounts_without_final_values(session):
    preview = CONTEXT.model_copy(
        update={"mode": "preview", "generation_id": None, "profile_revision_id": None}
    )
    rows = [row(context=preview)]
    assert_parity(
        sql_group(session, rows, reviewed=False),
        aggregate_contribution(rows, context=preview).groups[0],
    )


def test_evidenced_zero_and_mixed_states_remain_independent(session):
    rows = [
        row("a", goods_cost=value("0")),
        row("b", goods_cost=value("0", "evidenced")),
        row("c", goods_cost=value("9", "provisional")),
    ]
    assert_parity(
        sql_group(session, rows),
        aggregate_contribution(rows, context=CONTEXT).groups[0],
    )


def test_population_filters_apply_before_coverage(session):
    source = population([row("a"), row("b", goods_cost=value(None, "unknown"))])
    result = (
        session.execute(
            select(*contribution_aggregate_columns(source, reviewed=True)).where(
                source.c.group_id == "a"
            )
        )
        .mappings()
        .one()
    )
    assert_parity(result, aggregate_contribution([row()], context=CONTEXT).groups[0])
