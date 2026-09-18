"""Search ordering is a contract shared by PostgreSQL and the palette."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reality.domain.search import SearchRequest, edit_one, match_tier, normalize

CASES = json.loads(
    (Path(__file__).parent / "fixtures/global_search_matching.json").read_text()
)


@pytest.mark.parametrize("case", CASES, ids=lambda row: row["query"])
def test_matching_corpus(case):
    assert (
        match_tier(case["query"], [case["label"]], case["references"]) == case["tier"]
    )


def test_normalization_preserves_original_and_combining_forms():
    value = "MÜLLER Straße Café"
    assert normalize(value) == "muller strasse cafe"
    assert normalize("Cafe\u0301") == "cafe"
    assert value == "MÜLLER Straße Café"


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("abc", "acb", True),
        ("abc", "axc", True),
        ("abc", "ab", True),
        ("ab", "abc", True),
        ("ab", "abcd", False),
        ("abc", "xyz", False),
    ],
)
def test_single_edit(a, b, expected):
    assert edit_one(a, b) is expected


@pytest.mark.parametrize(
    "values",
    [
        {"provider": "unknown"},
        {"provider": "orders", "family": "item"},
        {"provider": "finance", "limit": 51},
        {"provider": "finance", "query": "x" * 501},
        {"provider": "finance", "tenant_id": "other"},
    ],
)
def test_request_rejects_untrusted_bounds(values):
    with pytest.raises(ValidationError):
        SearchRequest.model_validate(values)


@pytest.mark.parametrize("case", CASES, ids=lambda row: row["query"])
def test_staged_sql_predicates_match_the_authoritative_corpus(session, case):
    from sqlalchemy import literal, select

    from reality.db.search import _tier_match

    if not case["query"].strip():
        return
    tiers = [
        tier
        for tier in range(4)
        if session.scalar(
            select(
                _tier_match(
                    case["query"],
                    [literal(case["label"])],
                    [literal(ref) for ref in case["references"]],
                    tier,
                )
            )
        )
    ]
    assert tiers == ([] if case["tier"] is None else [case["tier"]])


@pytest.mark.parametrize("query,tier", [("Warehouse", 2), ("warehose", 3)])
def test_nullable_identifiers_do_not_remove_name_matches(session, query, tier):
    from sqlalchemy import String, literal, select

    from reality.db.search import _tier_match

    actual = [
        level
        for level in range(4)
        if session.scalar(
            select(
                _tier_match(
                    query,
                    [literal("Warehouse component")],
                    [literal(None, type_=String)],
                    level,
                )
            )
        )
    ]
    assert actual == [tier]


def test_latin1_sql_fast_path_is_equivalent(session):
    from sqlalchemy import func, select

    for value in [chr(code) for code in range(1, 256)] + [
        "MÜLLER Straße Café",
        "Æther ¼ Café",
    ]:
        assert session.scalar(
            select(func.reality_search_normalize_v1(value))
        ) == normalize(value)
