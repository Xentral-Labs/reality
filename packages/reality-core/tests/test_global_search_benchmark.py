"""Early full-population risk probe; not the ten-user browser acceptance benchmark."""

import time

from sqlalchemy import insert

from reality.db.core import Item
from reality.domain.search import SearchRequest
from reality.services.global_search import search_company


def test_hundred_thousand_item_search_probe(session, business):
    for start in range(0, 100_000, 5000):
        session.execute(
            insert(Item),
            [
                {
                    "id": f"search_probe_{i:06}",
                    "tenant_id": business.tenant.id,
                    "sku": f"PROBE-{i:06}",
                    "name": f"Warehouse component {i:06}",
                }
                for i in range(start, start + 5000)
            ],
        )
    from reality.db.search_indexes import install_search_indexes

    install_search_indexes(session.connection())
    session.execute(__import__("sqlalchemy").text("ANALYZE item"))
    for query in ["PROBE-099999", "Warehouse", "warehose"]:
        started = time.perf_counter()
        result = search_company(
            session,
            business.tenant.id,
            None,
            SearchRequest(provider="items_locations", query=query),
        )
        elapsed = time.perf_counter() - started
        print(
            f"search probe query={query!r} seconds={elapsed:.3f} hits={len(result.items)}"
        )
        assert result.items


def test_benchmark_dataset_and_guards_are_explicit():
    import pytest

    from benchmarks.global_search.runner import (
        cases_for,
        counts_for,
        validate_database_target,
    )

    counts = counts_for(100000)
    assert sum(counts.values()) == 100000
    assert all(value > 0 for value in counts.values())
    assert {provider for _, provider, _ in cases_for(counts)} == {
        "partners",
        "items_locations",
        "orders",
        "finance",
        "shipping",
        "reality",
        "reports",
    }
    for name, confirmed, empty in [
        ("production", True, True),
        ("reality_benchmark_test", False, True),
        ("reality_benchmark_test", True, False),
    ]:
        with pytest.raises(ValueError):
            validate_database_target(name, confirmed=confirmed, is_empty=empty)
