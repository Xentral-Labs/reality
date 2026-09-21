"""Spec 234: actual matched margins preserve independent coverage and context."""

from datetime import UTC, date, datetime
from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from reality.domain.contribution import (
    MAX_SLICES,
    CommercialInventoryPart,
    CommercialMatchLine,
    ContributionContext,
    ContributionInput,
    ContributionRefusal,
    MatchedSlice,
    admit_commercial_matches,
    aggregate_contribution,
)

D = Decimal
CONTEXT = ContributionContext(
    tenant_id="tenant",
    generation_id="generation",
    policy_revision_id="policy",
    profile_revision_id="profile",
    profile="commercial_v1",
    effective_at=datetime(2026, 9, 1, tzinfo=UTC),
    knowledge_at=datetime(2026, 9, 2, tzinfo=UTC),
)


def value(amount="0", state="reviewed"):
    return ContributionInput(amount=amount, state=state, references=("evidence",))


def row(identity="a", **changes):
    data = {
        "slice_id": identity,
        "context": CONTEXT,
        "currency": "EUR",
        "base_unit": "pc",
        "quantity": "60",
        "economic_date": date(2026, 9, 1),
        "revenue": value("1200"),
        "goods_cost": value("630"),
        "direct_selling_cost": value("100"),
        "allocated_selling_cost": value("14"),
    }
    return MatchedSlice(**(data | changes))


def group(rows, **kwargs):
    return aggregate_contribution(rows, context=CONTEXT, **kwargs).groups[0]


def commercial_part(identity, quantity, *, original_issue=None):
    return CommercialInventoryPart(
        member_id=identity,
        entry_basis_id=f"entry-{identity}",
        receipt_basis_id=f"receipt-{identity}",
        original_issue_member_id=original_issue,
        quantity=quantity,
    )


def commercial_line(identity="line-a", **changes):
    data = {
        "line_id": identity,
        "flow": "sale",
        "stated_net": "1200",
        "stated_quantity": "60",
        "disposition": "inventory",
        "inventory_parts": [commercial_part("member-a", "60")],
    }
    return CommercialMatchLine(**(data | changes))


def test_partial_commercial_matches_conserve_shared_inventory_capacity():
    first = commercial_line(
        stated_net="800",
        stated_quantity="40",
        inventory_parts=[commercial_part("member-a", "40")],
    )
    second = commercial_line(
        "line-b",
        stated_net="1200",
        stated_quantity="60",
        inventory_parts=[commercial_part("member-a", "60")],
    )

    result = admit_commercial_matches(
        [first, second], {first.inventory_parts[0].key: D("100")}
    )

    assert [row.stated_net for row in result] == [D("800"), D("1200")]
    assert [row.revenue_parts[0].amount for row in result] == [D("800"), D("1200")]


def test_commercial_match_revenue_allocation_is_deterministic_read_time_only():
    parts = [commercial_part(f"member-{suffix}", "1") for suffix in ("c", "a", "b")]
    result = admit_commercial_matches(
        [commercial_line(stated_net="100", stated_quantity="3", inventory_parts=parts)],
        {part.key: D(1) for part in parts},
    )[0]

    assert [part.amount for part in result.revenue_parts] == [
        D("33.3333"),
        D("33.3334"),
        D("33.3333"),
    ]
    assert sum((part.amount for part in result.revenue_parts), D(0)) == D(100)


def test_signed_credit_requires_exact_original_return_portions():
    returned = commercial_part("return", "10", original_issue="original-issue")
    credit = commercial_line(
        flow="credit",
        stated_net="-200",
        stated_quantity="-10",
        inventory_parts=[returned],
    )

    result = admit_commercial_matches([credit], {returned.key: D(10)})[0]

    assert result.stated_net == D(-200)
    assert result.stated_quantity == D(-10)
    assert result.revenue_parts[0].amount == D(-200)
    with pytest.raises(ValidationError, match="original issue"):
        commercial_line(
            flow="credit",
            stated_net="-200",
            stated_quantity="-10",
            inventory_parts=[commercial_part("return", "10")],
        )


@pytest.mark.parametrize(
    "changes,match",
    [
        ({"stated_quantity": "59"}, "conserve"),
        (
            {
                "inventory_parts": [
                    commercial_part("member-a", "30"),
                    commercial_part("member-a", "30"),
                ]
            },
            "Duplicate",
        ),
        (
            {
                "flow": "sale",
                "stated_net": "-1",
                "stated_quantity": "60",
            },
            "sign",
        ),
    ],
)
def test_commercial_match_line_refuses_ambiguous_shape(changes, match):
    with pytest.raises(ValidationError, match=match):
        commercial_line(**changes)


def test_commercial_match_refuses_overlap_or_foreign_capacity_key():
    line = commercial_line()
    with pytest.raises(ContributionRefusal, match="match_capacity_exceeded"):
        admit_commercial_matches([line], {line.inventory_parts[0].key: D("59.9999")})
    with pytest.raises(ContributionRefusal, match="match_capacity_missing"):
        admit_commercial_matches([line], {})


def test_non_inventory_match_dispositions_are_explicit():
    direct = CommercialMatchLine(
        line_id="service",
        flow="sale",
        stated_net="500",
        stated_quantity=None,
        disposition="direct_evidence",
        direct_revision_ids=("revision",),
        direct_cost_complete=True,
    )
    free = CommercialMatchLine(
        line_id="free-service",
        flow="sale",
        stated_net="0",
        stated_quantity=None,
        disposition="not_applicable",
    )
    unresolved = CommercialMatchLine(
        line_id="wip",
        flow="sale",
        stated_net="100",
        stated_quantity=None,
        disposition="unresolved",
    )

    assert admit_commercial_matches([direct, free, unresolved], {})[2].complete is False
    with pytest.raises(ValidationError):
        CommercialMatchLine(**(direct.model_dump() | {"direct_revision_ids": ()}))


def test_fixture_a_and_trace_are_exact():
    original = row()
    result = group([original])
    assert result.db1.total == D("570")
    assert result.db2.total == D("456")
    assert result.db1_rate == D("47.5000")
    assert result.db2_rate == D("38.0000")
    assert result.direct_selling_cost.total == D("100")
    assert result.allocated_selling_cost.total == D("14")
    assert result.slices == (original,)
    assert result.quantity == 60
    assert original.revenue.amount == 1200


def test_partial_scope_never_subtracts_incompatible_subtotals():
    a = row(
        revenue=value("100"),
        goods_cost=value("60"),
        direct_selling_cost=value("10"),
        allocated_selling_cost=value(),
    )
    b = row(
        "b",
        revenue=value("100"),
        goods_cost=value(None, "unknown"),
        direct_selling_cost=value("10"),
        allocated_selling_cost=value(),
    )
    result = group([a, b])
    assert result.revenue.total == 200
    assert result.goods_cost.known == 60
    assert result.db1.known == 40
    assert result.db2.known == 30
    assert result.db1.total is result.db2.total is result.db1_rate is None
    assert (result.db1.required, result.db1.covered) == (2, 1)


def test_selling_gap_does_not_hide_complete_db1():
    result = group([row(direct_selling_cost=value(None, "unknown"))])
    assert result.db1.total == 570
    assert result.db2.total is None
    assert result.db2.known == 0
    assert result.db1_rate == D("47.5")


@pytest.mark.parametrize(
    "state,known,complete",
    [
        ("reviewed", D("570"), D("570")),
        ("evidenced", D("570"), None),
        ("provisional", D("0"), None),
        ("unknown", D("0"), None),
    ],
)
def test_evidence_and_review_are_independent(state, known, complete):
    cost = value(None if state == "unknown" else "630", state)
    result = group([row(goods_cost=cost)])
    assert result.db1.known == known
    assert result.db1.total == complete
    assert result.goods_cost.provisional == int(state == "provisional")
    assert result.goods_cost.evidenced == int(state in ("evidenced", "reviewed"))


@pytest.mark.parametrize("revenue", ["0", "-100"])
def test_nonpositive_revenue_has_amount_but_no_rate(revenue):
    result = group([row(revenue=value(revenue))])
    assert result.db1.total == D(revenue) - 630
    assert result.db1_rate is result.db2_rate is None


def test_signed_return_shares_and_weighted_rates():
    a = row(revenue=value("1000"), goods_cost=value("500"))
    b = row("b", revenue=value("100"), goods_cost=value("90"))
    credit = row(
        "c",
        revenue=value("-100"),
        goods_cost=value("-50"),
        quantity="-5",
        direct_selling_cost=value(),
        allocated_selling_cost=value(),
    )
    result = group([a, b, credit])
    assert result.db1.total == 460
    assert result.db1_rate == D("46")
    assert result.quantity == 115


def test_currency_units_unassigned_and_month_partition():
    rows = [
        row(),
        row("b", currency="USD"),
        row("c", base_unit="kg"),
        row("d", customer_id="customer"),
        row("e", economic_date=date(2026, 8, 1)),
    ]
    groups = aggregate_contribution(
        rows, context=CONTEXT, group_by=("customer_id", "month")
    ).groups
    assert len(groups) == 5
    assert any(
        g.dimensions == (("customer_id", None), ("month", "2026-09")) for g in groups
    )
    assert (
        sum(g.db1.total for g in groups) == 2850
    )  # comparison only; no mixed total API


@pytest.mark.parametrize(
    "field,changed",
    [
        ("tenant_id", "other"),
        ("generation_id", "other"),
        ("policy_revision_id", "other"),
        ("profile_revision_id", "other"),
        ("effective_at", datetime(2026, 8, 1, tzinfo=UTC)),
        ("knowledge_at", datetime(2026, 9, 3, tzinfo=UTC)),
    ],
)
def test_mixed_context_refuses_without_partial_output(field, changed):
    other = ContributionContext(**(CONTEXT.model_dump() | {field: changed}))
    with pytest.raises(ContributionRefusal, match="context_mismatch"):
        aggregate_contribution([row(), row("b", context=other)], context=CONTEXT)


def test_duplicate_scope_and_grouping_refuse():
    for rows, kwargs, code in [
        ([row(), row()], {}, "duplicate_slice"),
        ([row()], {"group_by": ("amount",)}, "unsupported_grouping"),
        ([row()], {"group_by": ("month", "month")}, "unsupported_grouping"),
    ]:
        with pytest.raises(ContributionRefusal, match=code):
            aggregate_contribution(rows, context=CONTEXT, **kwargs)


def test_bound_stops_consuming_infinite_input():
    count = 0

    def rows():
        nonlocal count
        while True:
            count += 1
            yield row(str(count))

    with pytest.raises(ContributionRefusal, match="slice_bound"):
        aggregate_contribution(rows(), context=CONTEXT)
    assert count == MAX_SLICES + 1


def test_empty_scope_is_not_evidenced_zero():
    result = aggregate_contribution([], context=CONTEXT)
    assert result.state == "no_activity"
    assert result.groups == ()


def test_decimal_context_independence_and_input_immutability():
    a = row(revenue=value("99999999999999.9999"), goods_cost=value("0.0001"))
    with localcontext() as ctx:
        ctx.prec = 6
        result = group([a])
    assert result.db1.total == D("99999999999999.9998")
    with pytest.raises(ValidationError):
        a.quantity = D(5)


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": None, "state": "reviewed"},
        {"amount": "1", "state": "unknown"},
        {"amount": "NaN"},
        {"amount": "1.00001"},
        {"references": ()},
    ],
)
def test_invalid_value_shapes_refuse(changes):
    with pytest.raises(ValidationError):
        ContributionInput(
            **({"amount": "1", "state": "reviewed", "references": ("e",)} | changes)
        )


def test_reviewed_zero_is_complete_and_missing_revenue_is_not_zero():
    zero = row(
        revenue=value(),
        goods_cost=value(),
        direct_selling_cost=value(),
        allocated_selling_cost=value(),
    )
    result = aggregate_contribution([zero], context=CONTEXT)
    assert result.state == "complete"
    assert result.groups[0].db2.total == 0
    unknown = group([row(revenue=value(None, "unknown"))])
    assert unknown.revenue.total is unknown.db1.total is unknown.db2.total is None
    assert unknown.goods_cost.total == 630


def test_group_totals_reconcile_and_order_is_irrelevant():
    rows = [row(item_id="one"), row("b", item_id="two")]
    grouped = aggregate_contribution(rows, context=CONTEXT, group_by=("item_id",))
    reverse = aggregate_contribution(
        reversed(rows), context=CONTEXT, group_by=("item_id",)
    )
    assert grouped == reverse
    assert sum(g.db2.total for g in grouped.groups) == group(rows).db2.total


def test_half_even_rates_do_not_round_source_amounts():
    result = group([row(revenue=value("200"), goods_cost=value("199.9999"))])
    assert result.db1.total == D("0.0001")
    assert result.db1_rate == D("0.0000")
    result = group([row(revenue=value("200"), goods_cost=value("199.9997"))])
    assert result.db1_rate == D("0.0002")


def test_unsupported_profile_is_not_implicitly_commercial():
    with pytest.raises(ValidationError):
        ContributionContext(**(CONTEXT.model_dump() | {"profile": "fixed_cost_db2"}))


def test_economic_date_after_cutoff_refuses():
    with pytest.raises(ContributionRefusal, match="economic_date_after_cutoff"):
        aggregate_contribution([row(economic_date=date(2026, 9, 2))], context=CONTEXT)


def test_preview_context_has_no_invented_authority_or_final_amount():
    context = ContributionContext(
        **(
            CONTEXT.model_dump()
            | {
                "mode": "preview",
                "generation_id": None,
                "profile_revision_id": None,
            }
        )
    )
    result = aggregate_contribution([row(context=context)], context=context)
    assert result.groups[0].db1.known == 570
    assert result.groups[0].db1.total is result.groups[0].db2.total is None
    assert result.groups[0].db1_rate is None
    with pytest.raises(ValidationError):
        ContributionContext(**(CONTEXT.model_dump() | {"profile_revision_id": None}))
