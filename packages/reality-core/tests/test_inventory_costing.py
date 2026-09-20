"""Spec 234: production inventory arithmetic, not policy/ownership certification."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from reality.domain.inventory_costing import (
    MAX_EVENTS,
    MAX_PORTIONS,
    InventoryEvent,
    InventoryRefusal,
    calculate_inventory,
)

D = Decimal
START = datetime(2026, 1, 1, tzinfo=UTC)


def event(identity, kind, quantity, order, cost=None, **kwargs):
    return InventoryEvent(
        movement_id=identity,
        kind=kind,
        quantity=D(str(quantity)),
        occurred_at=START + timedelta(seconds=order),
        sequence=order,
        acquisition_cost=None if cost is None else D(str(cost)),
        **kwargs,
    )


def selection(entry, receipt, quantity):
    return {
        "entry_movement_id": entry,
        "receipt_movement_id": receipt,
        "quantity": D(str(quantity)),
    }


def returned(issue, entry, receipt, quantity):
    return dict(issue_movement_id=issue, **selection(entry, receipt, quantity))


def replay(events, method="fifo"):
    return calculate_inventory(events, method=method)


def test_receipt_a_and_fifo_b_preserve_acquisition_cost():
    a = replay([event("a", "receipt", 100, 1, 1050), event("sale", "issue", 60, 2)])
    assert a.issues[0].cost == D(630)
    assert a.remaining_cost == D(420)
    b = replay(
        [
            event("a", "receipt", 100, 1, 1000),
            event("b", "receipt", 100, 2, 1400),
            event("sale", "issue", 120, 3),
            event("transfer", "transfer", 30, 4),
        ]
    )
    assert b.issues[0].cost == D(1280)
    assert (b.remaining_quantity, b.remaining_cost) == (D(80), D(1120))
    assert [(p.receipt_movement_id, p.quantity) for p in b.issues[0].parts] == [
        ("a", D(100)),
        ("b", D(20)),
    ]


def test_return_enters_at_return_time_and_retains_receipt_on_resale():
    events = [
        event("a", "receipt", 1, 1, 10),
        event("b", "receipt", 1, 2, 14),
        event("sale", "issue", 1, 3),
        event(
            "return",
            "customer_return",
            1,
            4,
            return_parts=[returned("sale", "a", "a", 1)],
        ),
        event("resale", "issue", 1, 5),
        event("resale2", "issue", 1, 6),
        event(
            "return2",
            "customer_return",
            1,
            7,
            return_parts=[returned("resale2", "return", "a", 1)],
        ),
    ]
    result = replay(events)
    assert [i.cost for i in result.issues] == [D(10), D(14), D(10)]
    assert result.issues[2].parts[0].entry_movement_id == "return"
    assert result.issues[2].parts[0].receipt_movement_id == "a"
    assert result.remaining[0].receipt_movement_id == "a"
    assert result.remaining[0].entry_movement_id == "return2"
    assert result.remaining_cost == D(10)
    assert result.returns[1].parts[0].issue_movement_id == "resale2"


def test_specific_method_requires_and_consumes_exact_portions():
    result = replay(
        [
            event("a", "receipt", 1, 1, 10),
            event("b", "receipt", 1, 2, 14),
            event("sale", "issue", 1, 3, selections=[selection("b", "b", 1)]),
        ],
        method="specific",
    )
    assert result.issues[0].cost == D(14)
    assert result.remaining_cost == D(10)
    with pytest.raises(InventoryRefusal, match="specific_selection_required"):
        replay(
            [event("a", "receipt", 1, 1, 10), event("sale", "issue", 1, 2)], "specific"
        )
    with pytest.raises(InventoryRefusal, match="fifo_selection_forbidden"):
        replay(
            [
                event("a", "receipt", 1, 1, 10),
                event("sale", "issue", 1, 2, selections=[selection("a", "a", 1)]),
            ]
        )


def test_supplier_return_and_loss_are_separate_from_sales():
    result = replay(
        [
            event("a", "receipt", 2, 1, 20),
            event("b", "receipt", 1, 2, 14),
            event(
                "supplier", "supplier_return", 1, 3, selections=[selection("b", "b", 1)]
            ),
            event("loss", "loss", 1, 4),
            event("sale", "issue", 1, 5),
        ]
    )
    assert [(i.kind, i.cost) for i in result.issues] == [
        ("supplier_return", D(14)),
        ("loss", D(10)),
        ("issue", D(10)),
    ]
    assert result.remaining_cost == 0
    with pytest.raises(InventoryRefusal, match="specific_selection_required"):
        replay([event("a", "receipt", 1, 1, 10), event("s", "supplier_return", 1, 2)])


def test_rounding_conserves_residuals_before_filtering_and_under_low_precision():
    events = [event("a", "receipt", 3, 1, 1)] + [
        event(f"sale-{i}", "issue", 1, i + 2) for i in range(3)
    ]
    with localcontext() as context:
        context.prec = 6
        result = replay(events)
    assert [i.cost for i in result.issues] == [D("0.3333"), D("0.3334"), D("0.3333")]
    assert result.remaining_cost == 0
    assert result.issues[1].cost == D("0.3334")  # Filter after calculation.
    assert sum(i.cost for i in result.issues) == D(1)


def test_partial_returns_conserve_original_issue_rounding():
    result = replay(
        [
            event("a", "receipt", 3, 1, 1),
            event("sale", "issue", 3, 2),
            *[
                event(
                    f"return-{i}",
                    "customer_return",
                    1,
                    i + 3,
                    return_parts=[returned("sale", "a", "a", 1)],
                )
                for i in range(3)
            ],
        ]
    )
    assert [r.cost for r in result.returns] == [
        D("-0.3333"),
        D("-0.3334"),
        D("-0.3333"),
    ]
    assert result.remaining_cost == D(1)
    assert sum(r.quantity for r in result.returns) == D(-3)
    assert all(p.quantity < 0 for r in result.returns for p in r.parts)


def test_split_return_merges_same_receipt_but_preserves_issue_trace():
    result = replay(
        [
            event("a", "receipt", 2, 1, 1),
            event("s1", "issue", 1, 2),
            event("s2", "issue", 1, 3),
            event(
                "r",
                "customer_return",
                2,
                4,
                return_parts=[
                    returned("s1", "a", "a", 1),
                    returned("s2", "a", "a", 1),
                ],
            ),
            event("s3", "issue", 1, 5),
        ]
    )
    assert len(result.returns[0].parts) == 2
    assert result.issues[-1].parts[0].receipt_movement_id == "a"
    assert result.remaining_cost == D("0.5")


def test_unknown_is_not_zero_and_partial_known_amounts_remain_visible():
    result = replay(
        [
            event("a", "receipt", 2, 1),
            event("b", "receipt", 2, 2, 10),
            event("sale", "issue", 3, 3),
            event(
                "return",
                "customer_return",
                1,
                4,
                return_parts=[returned("sale", "a", "a", 1)],
            ),
        ]
    )
    assert (
        result.issues[0].cost,
        result.issues[0].known_cost,
        result.issues[0].unvalued_quantity,
    ) == (None, D(5), D(2))
    assert (
        result.remaining_cost,
        result.known_remaining_cost,
        result.unvalued_quantity,
    ) == (None, D(5), D(1))
    assert result.returns[0].cost is None
    assert result.returns[0].unvalued_quantity == D(1)
    zero = replay([event("zero", "receipt", 1, 1, 0)])
    assert (zero.remaining_cost, zero.unvalued_quantity) == (D(0), D(0))


def test_late_cost_replay_changes_consumed_and_remaining_without_mutation():
    original = event("a", "receipt", 100, 1, 1000)
    sale = event("sale", "issue", 60, 2)
    before = replay([original, sale])
    after = replay([event("a", "receipt", 100, 1, 1050), sale])
    assert (before.issues[0].cost, before.remaining_cost) == (D(600), D(400))
    assert (after.issues[0].cost, after.remaining_cost) == (D(630), D(420))
    assert original.acquisition_cost == D(1000)
    with pytest.raises(ValidationError):
        original.quantity = D(1)
    with pytest.raises((AttributeError, TypeError)):
        before.remaining_cost = D(1)


def test_canonical_order_uses_economic_time_then_sequence_then_opaque_identity():
    a = event("a", "receipt", 1, 1, 10)
    b = event("b", "receipt", 1, 1, 14)
    sale = event("sale", "issue", 1, 2)
    assert replay([sale, b, a]) == replay([a, b, sale])
    assert replay([b, a, sale]).issues[0].cost == D(10)
    offset = a.model_dump()
    offset["occurred_at"] = a.occurred_at.astimezone(timezone(timedelta(hours=2)))
    assert replay([InventoryEvent(**offset), b, sale]) == replay([a, b, sale])


@pytest.mark.parametrize("kind", ["issue", "loss", "transfer"])
def test_shortages_refuse_even_when_later_receipt_would_cover(kind):
    with pytest.raises(InventoryRefusal, match="insufficient_stock"):
        replay([event("out", kind, 1, 1), event("later", "receipt", 2, 2, 20)])


@pytest.mark.parametrize(
    "bad_return",
    [
        returned("missing", "a", "a", 1),
        returned("sale", "wrong", "a", 1),
        returned("sale", "a", "wrong", 1),
        returned("sale", "a", "a", 2),
    ],
)
def test_returns_require_exact_available_original_issue(bad_return):
    with pytest.raises(InventoryRefusal):
        replay(
            [
                event("a", "receipt", 1, 1, 10),
                event("sale", "issue", 1, 2),
                event(
                    "r",
                    "customer_return",
                    bad_return["quantity"],
                    3,
                    return_parts=[bad_return],
                ),
            ]
        )


def test_return_cannot_exceed_original_issue_across_multiple_returns():
    with pytest.raises(InventoryRefusal, match="portion_exceeded"):
        replay(
            [
                event("a", "receipt", 1, 1, 10),
                event("sale", "issue", 1, 2),
                event(
                    "r1",
                    "customer_return",
                    1,
                    3,
                    return_parts=[returned("sale", "a", "a", 1)],
                ),
                event(
                    "r2",
                    "customer_return",
                    1,
                    4,
                    return_parts=[returned("sale", "a", "a", 1)],
                ),
            ]
        )


def test_loss_cannot_be_reclassified_as_customer_return():
    with pytest.raises(InventoryRefusal, match="original_sale_required"):
        replay(
            [
                event("a", "receipt", 1, 1, 10),
                event("loss", "loss", 1, 2),
                event(
                    "r",
                    "customer_return",
                    1,
                    3,
                    return_parts=[returned("loss", "a", "a", 1)],
                ),
            ]
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity": D(0)},
        {"quantity": D(-1)},
        {"quantity": D("0.00001")},
        {"quantity": D("NaN")},
        {"acquisition_cost": D("Infinity")},
        {"acquisition_cost": D(-1)},
        {"acquisition_cost": D("0.00001")},
        {"movement_id": ""},
        {"sequence": -1},
        {"occurred_at": START.replace(tzinfo=None)},
        {"kind": "correction"},
        {"selections": [selection("a", "a", 1)]},
    ],
)
def test_invalid_inputs_are_refused(changes):
    data = event("a", "receipt", 1, 1, 10).model_dump()
    with pytest.raises(ValidationError):
        InventoryEvent(**(data | changes))


def test_invalid_method_duplicate_ids_and_portion_totals_refuse():
    with pytest.raises(InventoryRefusal, match="unsupported_method"):
        replay([], "weighted_average")
    with pytest.raises(TypeError):
        calculate_inventory([])
    with pytest.raises(InventoryRefusal, match="duplicate_movement"):
        replay([event("a", "receipt", 1, 1, 10)] * 2)
    with pytest.raises(ValidationError):
        event("s", "issue", 2, 2, selections=[selection("a", "a", 1)])
    with pytest.raises(ValidationError):
        event("r", "customer_return", 1, 2)
    with pytest.raises(ValidationError):
        event("s", "issue", 1, 2, cost=1)


def test_input_bound_consumes_only_one_extra_event():
    count = 0

    def events():
        nonlocal count
        while True:
            count += 1
            yield event(str(count), "receipt", 1, count, 1)

    with pytest.raises(InventoryRefusal, match="event_limit"):
        replay(events())
    assert count == MAX_EVENTS + 1


def test_trace_bound_refuses_before_publishing_truncated_result(monkeypatch):
    monkeypatch.setattr("reality.domain.inventory_costing.MAX_PORTIONS", 2)
    with pytest.raises(InventoryRefusal, match="portion_limit"):
        replay(
            [
                event("a", "receipt", 1, 1, 1),
                event("b", "receipt", 1, 2, 1),
                event("sale", "issue", 2, 3),
            ]
        )
    assert MAX_PORTIONS >= MAX_EVENTS


@pytest.mark.parametrize("amount", ["0.0001", "0.9999", "12345678901234.1234"])
@pytest.mark.parametrize("quantity", [3, 7, 23])
def test_many_partial_consumptions_and_returns_conserve_exactly(amount, quantity):
    events = [event("a", "receipt", quantity, 1, amount)]
    events.extend(event(f"s{i}", "issue", 1, i + 2) for i in range(quantity))
    events.extend(
        event(
            f"r{i}",
            "customer_return",
            1,
            quantity + i + 2,
            return_parts=[returned(f"s{i}", "a", "a", 1)],
        )
        for i in range(quantity)
    )
    with localcontext() as context:
        context.prec = 6
        result = replay(events)
    assert sum(i.cost for i in result.issues) == D(amount)
    assert sum(r.cost for r in result.returns) == -D(amount)
    assert result.remaining_cost == D(amount)
    assert result.remaining_quantity == D(quantity)


def test_maximum_precision_half_even_boundary():
    result = replay(
        [
            event("a", "receipt", "99999999999999.9997", 1, "99999999999999.9999"),
            event("s", "issue", "25000000000000.0000", 2),
        ]
    )
    assert result.issues[0].cost == D("25000000000000.0001")
    assert result.remaining_cost == D("74999999999999.9998")


def test_fractional_quantity_return_selection_and_loss_conserve():
    result = replay(
        [
            event("a", "receipt", "0.0003", 1, "0.0002"),
            event("s", "issue", "0.0002", 2),
            event(
                "r",
                "customer_return",
                "0.0001",
                3,
                return_parts=[returned("s", "a", "a", "0.0001")],
            ),
            event("loss", "loss", "0.0001", 4),
        ]
    )
    assert result.remaining_quantity == D("0.0001")
    assert sum(i.cost for i in result.issues) + sum(
        r.cost for r in result.returns
    ) + result.remaining_cost == D("0.0002")


def test_return_of_split_issue_requires_exact_receipt_portion():
    result = replay(
        [
            event("a", "receipt", 1, 1, 10),
            event("b", "receipt", 1, 2, 14),
            event("s", "issue", 2, 3),
            event(
                "r", "customer_return", 1, 4, return_parts=[returned("s", "b", "b", 1)]
            ),
        ]
    )
    assert result.returns[0].cost == D(-14)
    assert result.remaining_cost == D(14)
    assert result.remaining[0].receipt_movement_id == "b"


def test_specific_selection_cannot_exceed_one_layer_even_with_sufficient_pool_stock():
    with pytest.raises(InventoryRefusal, match="portion_exceeded"):
        replay(
            [
                event("a", "receipt", 1, 1, 10),
                event("b", "receipt", 2, 2, 20),
                event("s", "issue", 2, 3, selections=[selection("a", "a", 2)]),
            ],
            "specific",
        )
    with pytest.raises(InventoryRefusal, match="specific_layer_unavailable"):
        replay(
            [
                event("a", "receipt", 1, 1, 10),
                event("s", "issue", 1, 2, selections=[selection("other", "a", 1)]),
            ],
            "specific",
        )


def test_duplicate_selection_and_return_portions_are_rejected():
    with pytest.raises(ValidationError):
        event(
            "s",
            "issue",
            2,
            2,
            selections=[selection("a", "a", 1), selection("a", "a", 1)],
        )
    with pytest.raises(ValidationError):
        event(
            "r",
            "customer_return",
            2,
            3,
            return_parts=[returned("s", "a", "a", 1), returned("s", "a", "a", 1)],
        )


def test_input_portion_bound_refuses_before_attempting_unknown_references(monkeypatch):
    monkeypatch.setattr("reality.domain.inventory_costing.MAX_PORTIONS", 1)
    with pytest.raises(InventoryRefusal, match="portion_limit"):
        replay(
            [
                event(
                    "r",
                    "customer_return",
                    2,
                    1,
                    return_parts=[
                        returned("s1", "a", "a", 1),
                        returned("s2", "a", "a", 1),
                    ],
                )
            ]
        )


def test_no_implicit_input_conversion_or_empty_pool_valuation_gap():
    with pytest.raises(InventoryRefusal, match="typed_event_required"):
        replay([{"movement_id": "a"}])
    result = replay([])
    assert result.remaining_cost == result.remaining_quantity == 0
    assert result.issues == result.returns == result.remaining == ()
