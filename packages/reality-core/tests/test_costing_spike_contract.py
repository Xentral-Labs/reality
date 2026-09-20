"""Independent arithmetic proofs for the isolated costing experiment."""

from decimal import Decimal as D

import pytest

from benchmarks.large_tenant_registers.costing_kernel import (
    Event,
    acquisition_cost,
    allocate,
    replay,
)


def event(key, kind, quantity, cost=None, original=None):
    return Event(
        str(key), kind, D(quantity), None if cost is None else D(cost), original
    )


def test_received_cost_basis_and_discount():
    assert acquisition_cost(D(1000), [D(100), D(-50)], D(190), True) == D(1050)
    assert acquisition_cost(D(1000), [D(50)], D(190), False) == D(1240)
    assert acquisition_cost(D(1000), [D(50), D(-20)], D(190), True) == D(1030)
    assert acquisition_cost(D(1000), [], D(190), None) is None
    assert acquisition_cost(None, [], D(190), True) is None


def test_partial_nonrecoverable_tax_uses_the_supplied_amount():
    assert acquisition_cost(D(1000), [D(50)], D(90), False) == D(1140)


def test_signed_allocation_and_input_order_independence():
    weights = {"c": D(1), "a": D(1), "b": D(1)}
    assert allocate(D(".01"), weights) == {
        "a": D(".0034"),
        "b": D(".0033"),
        "c": D(".0033"),
    }
    assert allocate(D("-.01"), weights) == {
        "a": D("-.0034"),
        "b": D("-.0033"),
        "c": D("-.0033"),
    }
    with pytest.raises(ValueError):
        allocate(D(1), {"a": D(-1)})


def test_cumulative_cost_and_correction_are_filter_independent():
    for total, amounts in [
        ("1", [".3333", ".3334", ".3333"]),
        ("1.0001", [".3334", ".3333", ".3334"]),
    ]:
        result = replay(
            [event("r", "receipt", "3", total)]
            + [event(i, "issue", "1") for i in range(3)]
        )
        assert [r.cost for r in result.issues] == list(map(D, amounts))
        assert result.remaining_cost == 0
        assert sum(r.cost for r in result.issues) == D(total)
        assert result.issues[1].cost == D(amounts[1])


def test_fifo_return_is_new_arrival_at_original_consumed_cost():
    result = replay(
        [
            event("a", "receipt", "1", "10"),
            event("b", "receipt", "1", "14"),
            event("s1", "issue", "1"),
            event("ra", "return", "1", original="s1"),
            event("s2", "issue", "1"),
        ]
    )
    assert [row.cost for row in result.issues] == [D(10), D(14)]
    assert result.remaining_cost == 10
    assert result.remaining_quantity == 1


def test_partial_returns_preserve_consumed_slice_rounding():
    result = replay(
        [
            event("r", "receipt", "3", "1"),
            event("sale", "issue", "3"),
            event("r1", "return", "1", original="sale"),
            event("r2", "return", "1", original="sale"),
            event("r3", "return", "1", original="sale"),
            event("s1", "issue", "1"),
            event("s2", "issue", "1"),
            event("s3", "issue", "1"),
        ]
    )
    assert [x.cost for x in result.issues[1:]] == [D(".3333"), D(".3334"), D(".3333")]
    with pytest.raises(ValueError):
        replay(
            [
                event("r", "receipt", "1", "10"),
                event("s", "issue", "1"),
                event("back", "return", "2", original="s"),
            ]
        )


def test_missing_cost_does_not_become_zero():
    result = replay([event("r", "receipt", "2"), event("s", "issue", "1")])
    assert result.issues[0].cost is None
    assert result.remaining_cost is None
    assert result.remaining_quantity == 1
    assert result.unvalued_quantity == 1


def test_negative_stock_is_refused_and_transfer_preserves_cost():
    with pytest.raises(ValueError, match="stock"):
        replay([event("s", "issue", "1")])
    result = replay([event("r", "receipt", "2", "20"), event("t", "transfer", "1")])
    assert result.remaining_cost == 20


def test_receipt_cost_and_db_fixture_a():
    result = replay([event("r", "receipt", "100", "1050"), event("s", "issue", "60")])
    assert result.remaining_cost == 420
    cogs = result.issues[0].cost
    assert cogs == 630
    assert D(1200) - cogs == 570
    assert D(1200) - cogs - D(114) == 456


def test_specific_identity_and_duplicate_event_refusal():
    result = replay(
        [
            event("a", "receipt", "1", "10"),
            event("b", "receipt", "1", "14"),
            Event("sale", "issue", D(1), specific_layer="b"),
        ]
    )
    assert result.issues[0].cost == 14
    assert result.remaining_cost == 10
    with pytest.raises(ValueError, match="Duplicate"):
        replay(
            [event("same", "receipt", "1", "10"), event("same", "receipt", "1", "10")]
        )


def test_mixed_layer_partial_return_requires_exact_cost_identity():
    initial = [
        event("a", "receipt", "1", "10"),
        event("b", "receipt", "1", "14"),
        event("sale", "issue", "2"),
    ]
    with pytest.raises(ValueError, match="Ambiguous"):
        replay(initial + [event("back", "return", "1", original="sale")])
    result = replay(
        initial
        + [Event("back", "return", D(1), original_issue="sale", specific_layer="b")]
    )
    assert result.remaining_cost == 14
    result = replay(
        initial
        + [event("back", "return", "2", original="sale"), event("resale", "issue", "1")]
    )
    assert result.issues[-1].cost == 10
    assert result.remaining_cost == 14


def test_maximum_supported_precision_does_not_create_false_half_even_tie():
    # Exact fractional cost is just above the tie; default Decimal precision 28
    # would erase the distinction before four-place rounding.
    result = replay(
        [
            event("r", "receipt", "99999999999999.9997", "99999999999999.9999"),
            event("s", "issue", "25000000000000.0000"),
        ]
    )
    assert result.issues[0].cost == D("25000000000000.0001")
    assert result.remaining_cost + result.issues[0].cost == D("99999999999999.9999")


def test_finer_base_quantity_is_refused_not_silently_rounded():
    with pytest.raises(ValueError, match="precision"):
        replay([event("r", "receipt", ".00001", "1")])


def test_runner_refuses_non_postgres_shared_database_and_missing_confirmation():
    from benchmarks.large_tenant_registers.costing_runner import validate_target

    with pytest.raises(ValueError, match="PostgreSQL"):
        validate_target("sqlite:///reality_benchmark_234", confirmed=True)
    with pytest.raises(ValueError, match="begin"):
        validate_target(
            "postgresql+psycopg://localhost/ordinary_company", confirmed=True
        )
    with pytest.raises(ValueError, match="confirm"):
        validate_target(
            "postgresql+psycopg://localhost/reality_benchmark_234", confirmed=False
        )


def test_return_exposes_exact_cost_reversal_for_contribution():
    result = replay(
        [
            Event("receipt", "receipt", D(3), D(1)),
            Event("sale", "issue", D(1)),
            Event("returned", "return", D(1), original_issue="sale"),
        ]
    )
    assert result.returns[0].cost == D("-0.3333")
    assert result.returns[0].quantity == D(-1)
    assert result.remaining_cost == D(1)
