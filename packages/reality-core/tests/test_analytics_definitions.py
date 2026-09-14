"""Strict analytical requests and calendar boundaries, independent of storage."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from reality.domain.analytics import AnalyticsDefinition, AnalyticsQuery, resolve_window


def definition(**changes):
    return AnalyticsDefinition.model_validate(
        {
            "dataset": "sales_order_lines",
            "dimensions": ["customer_id"],
            "measures": ["ordered_quantity"],
            **changes,
        }
    )


def test_iso_year_week_and_dst_are_local_boundaries():
    d = definition(
        time={
            "field": "ordered_at",
            "timezone": "Europe/Berlin",
            "window": {"kind": "iso_week", "year": 2026, "week": 1},
        }
    )
    start, end = resolve_window(d.time, datetime(2026, 9, 13, tzinfo=UTC))
    assert start == datetime(2025, 12, 28, 23, tzinfo=UTC)
    assert end == datetime(2026, 1, 4, 23, tzinfo=UTC)
    d = definition(
        time={
            "timezone": "Europe/Berlin",
            "window": {"kind": "absolute", "start": "2026-03-29", "end": "2026-03-30"},
        }
    )
    start, end = resolve_window(d.time, datetime.now(UTC))
    assert (end - start).total_seconds() == 23 * 3600


@pytest.mark.parametrize(
    "changes",
    [
        {"tenant_id": "foreign"},
        {"sql": "select 1"},
        {"dimensions": ["a"] * 5},
        {"measures": []},
        {"where": {"field": "customer_id", "op": "eq", "value": "x", "all": []}},
        {"time": {"timezone": "not/a-zone"}},
        {"time": {"window": {"kind": "iso_week", "year": 2026, "week": 54}}},
        {"presentation": {"kind": "table", "rows": ["customer_id"]}},
    ],
)
def test_untrusted_or_ambiguous_definitions_are_refused(changes):
    with pytest.raises(ValidationError):
        definition(**changes)


def test_filter_tree_and_query_bounds():
    leaf = {"field": "product_id", "op": "in", "values": ["itm_a", "itm_b"]}
    definition(where={"all": [leaf, {"any": [leaf]}]})
    for _ in range(4):
        leaf = {"all": [leaf]}
    with pytest.raises(ValidationError):
        definition(where=leaf)
    with pytest.raises(ValidationError):
        AnalyticsQuery(definition=definition(), page_size=201)


def test_last_complete_weeks_do_not_include_partial_current_week():
    d = definition(
        time={"timezone": "UTC", "window": {"kind": "last_complete_weeks", "count": 2}}
    )
    assert resolve_window(d.time, datetime(2026, 9, 13, tzinfo=UTC)) == (
        datetime(2026, 8, 24, tzinfo=UTC),
        datetime(2026, 9, 7, tzinfo=UTC),
    )
