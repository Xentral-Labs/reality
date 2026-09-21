"""T087 exact weighted allocation and source-backed conversion arithmetic."""

from decimal import Decimal

import pytest

from reality.domain.costing import (
    AllocationTarget,
    CostingRefusal,
    allocate_weighted,
    convert_amount,
    convert_quantity,
)

D = Decimal


def test_largest_remainder_uses_opaque_target_id_for_exact_ties():
    result = allocate_weighted(
        D("0.0003"),
        D("0.0002"),
        [
            AllocationTarget(target_id="target-c", weight=D("1")),
            AllocationTarget(target_id="target-a", weight=D("1")),
            AllocationTarget(target_id="target-b", weight=D("1")),
        ],
    )
    assert result.shares == {
        "target-a": D("0.0001"),
        "target-b": D("0.0001"),
        "target-c": D("0.0000"),
    }
    assert result.allocated == D("0.0002")
    assert result.unassigned == D("0.0001")


def test_negative_reduction_restores_sign_after_absolute_allocation():
    result = allocate_weighted(
        D("-10.0000"),
        D("-10.0000"),
        [
            AllocationTarget(target_id="a", weight=D("1")),
            AllocationTarget(target_id="b", weight=D("2")),
            AllocationTarget(target_id="c", weight=D("3")),
        ],
    )
    assert result.shares == {
        "a": D("-1.6667"),
        "b": D("-3.3333"),
        "c": D("-5.0000"),
    }
    assert sum(result.shares.values(), D("0")) == D("-10.0000")
    assert result.unassigned == D("0.0000")


@pytest.mark.parametrize(
    ("capacity", "total", "targets", "message"),
    [
        ("10", "11", [("a", "1")], "exceeds"),
        ("10", "-1", [("a", "1")], "sign"),
        ("10", "1", [("a", "0")], "positive"),
        ("10", "1", [("a", "-1")], "positive"),
        ("10", "1", [("a", "1"), ("a", "2")], "Duplicate"),
        ("10.00001", "1", [("a", "1")], "four decimal"),
    ],
)
def test_allocation_refuses_invalid_scope(capacity, total, targets, message):
    with pytest.raises(CostingRefusal, match=message):
        allocate_weighted(
            D(capacity),
            D(total),
            [
                AllocationTarget(target_id=target, weight=D(weight))
                for target, weight in targets
            ],
        )


def test_conversion_keeps_ratio_precision_and_distinguishes_amount_from_quantity():
    assert convert_amount(D("10.0000"), D("1"), D("3")) == D("3.3333")
    assert convert_amount(D("-10.0000"), D("1"), D("3")) == D("-3.3333")
    assert convert_quantity(D("2.5000"), D("4"), D("5")) == D("2.0000")
    with pytest.raises(CostingRefusal, match="four decimal"):
        convert_quantity(D("1.0000"), D("1"), D("3"))


@pytest.mark.parametrize(
    ("numerator", "denominator"), [("0", "1"), ("1", "0"), ("-1", "1")]
)
def test_conversion_refuses_nonpositive_ratio(numerator, denominator):
    with pytest.raises(CostingRefusal, match="positive"):
        convert_amount(D("1"), D(numerator), D(denominator))


def test_conversion_refuses_ratio_beyond_twelve_decimal_places():
    with pytest.raises(CostingRefusal, match="twelve decimal"):
        convert_amount(D("1"), D("1.0000000000001"), D("1"))
