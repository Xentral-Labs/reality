"""What the compiler must get right, stated before the compiler exists.

Every case here is a number somebody could ship with confidence and be wrong
about. The fan-out cases carry the answer hand-written SQL gives beside the answer
the graph gives, so the guarantee is visible rather than asserted.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from reality.domain.traversal import Traversal
from reality.services.analytics.traversal import (
    TraversalRefused,
    run_traversal,
)
from reality.services.core import create_manual_order, create_party


def line(item, quantity: str, amount: str) -> dict:
    return {
        "item_id": item.id,
        "sku": item.sku,
        "quantity": quantity,
        "unit_price": "1",
        "gross_amount": amount,
        "unit": "pcs",
    }


@pytest.fixture
def sales(session, business):
    """One order of EUR 1,000 with four lines, and company beside it.

    The four lines are the whole point: an order-grain amount summed along them
    returns 4,000 in hand-written SQL and in Cypher, without complaint.
    """
    item = business.item
    orders = {}
    orders["four_lines"] = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [line(item, "1", "250") for _ in range(4)],
        "1000",
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
        sales_channel="web",
    )
    orders["one_line"] = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-002",
        business.company.id,
        business.customer.id,
        business.location.id,
        [line(item, "2", "500")],
        "500",
        currency="EUR",
        ordered_at="2026-03-20T10:00:00Z",
        document_date="2026-03-20",
        sales_channel="phone",
    )
    orders["dollars"] = create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-003",
        business.company.id,
        business.customer.id,
        business.location.id,
        [line(item, "1", "300")],
        "300",
        currency="USD",
        ordered_at="2026-04-02T10:00:00Z",
        document_date="2026-04-02",
        sales_channel="web",
    )
    session.flush()
    return orders


@pytest.fixture
def neighbour(session, business):
    """A second company with a distinctive amount, to prove it never appears."""
    from reality.services.core import create_item, create_location, create_tenant

    tenant = create_tenant(session, "Nachbar GmbH")
    company = create_party(session, tenant.id, "Nachbar GmbH", "company")
    customer = create_party(session, tenant.id, "Müller GmbH", "customer")
    item = create_item(session, tenant.id, "BIKE-LIGHT", "Bike Light")
    location = create_location(session, tenant.id, "Fremdlager")
    create_manual_order(
        session,
        tenant.id,
        "sales",
        "AN-001",
        company.id,
        customer.id,
        location.id,
        [line(item, "1", "999999")],
        "999999",
        currency="EUR",
        ordered_at="2026-03-15T10:00:00Z",
        document_date="2026-03-15",
    )
    session.flush()
    return tenant


def ask(session, tenant_id, **query):
    return run_traversal(session, tenant_id, Traversal.model_validate(query))


def total(result, key="stated_order_amount") -> Decimal:
    return sum((Decimal(row[key]) for row in result.rows), Decimal(0))


# --- the number the whole design exists for -----------------------------------


def test_order_value_at_order_grain_counts_each_order_once(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    by_currency = {
        row["root.currency"]: Decimal(row["stated_order_amount"]) for row in result.rows
    }
    assert by_currency["EUR"] == Decimal(1500)
    assert by_currency["USD"] == Decimal(300)


def test_order_value_per_article_is_refused_and_names_the_edge(
    session, business, sales
):
    """Hand-written SQL returns 4,000 here. The graph refuses instead.

    An order's value cannot be attributed to one of its articles. The question is
    not slow or unsupported, it is unanswerable, and the refusal says which edge
    made it so and which measure lives at the grain that was reached.
    """
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "follow": [
                    {"edge": "contains", "as": "l"},
                    {"edge": "of_item", "as": "i"},
                ],
                "measures": ["stated_order_amount"],
                "group_by": [{"field": "i.sku"}],
            },
        )
    assert "contains" in str(refusal.value), (
        "the refusal must name the edge that fanned out"
    )
    assert "line_amount" in str(refusal.value), (
        "and offer the measure that fits the grain"
    )


def test_line_amount_along_the_lines_is_correct(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "follow": [{"edge": "contains", "as": "l"}],
            "measures": ["line_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    by_currency = {
        row["root.currency"]: Decimal(row["line_amount"]) for row in result.rows
    }
    assert by_currency["EUR"] == Decimal(1500)


def test_a_hop_used_only_to_filter_does_not_fan_out(session, business, sales):
    """The EUR 1,000 order reached through its four lines still counts once.

    A hop the result never refers to is narrowed to an existence test rather than
    joined, so it filters without multiplying. That is the optimisation a person
    writing this by hand forgets, and it is also the honest reading of the
    question: orders that have such a line, valued at order grain.
    """
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "follow": [{"edge": "contains", "as": "l"}],
            "filter": [{"field": "l.sku", "op": "eq", "value": business.item.sku}],
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.sales_channel"}, {"field": "root.currency"}],
        },
    )
    rows = {
        (row["root.sales_channel"], row["root.currency"]): Decimal(
            row["stated_order_amount"]
        )
        for row in result.rows
    }
    assert rows[("web", "EUR")] == Decimal(1000), "once, not four times"
    assert rows[("web", "USD")] == Decimal(300)
    assert rows[("phone", "EUR")] == Decimal(500)


def test_counting_orders_after_fan_out_counts_orders(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "follow": [{"edge": "contains", "as": "l"}],
            "measures": ["order_count"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    by_currency = {row["root.currency"]: int(row["order_count"]) for row in result.rows}
    assert by_currency["EUR"] == 2, "two orders, not six lines"


# --- units --------------------------------------------------------------------


def test_summing_two_currencies_without_grouping_by_currency_is_refused(
    session, business, sales
):
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            **{"from": "order", "measures": ["stated_order_amount"]},
        )
    assert "currency" in str(refusal.value)


def test_quantity_across_articles_is_refused(session, business, sales):
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "follow": [{"edge": "contains", "as": "l"}],
                "measures": ["ordered_quantity"],
                "group_by": [{"field": "root.currency"}],
            },
        )
    assert "unit" in str(refusal.value) or "item" in str(refusal.value)


# --- additivity ---------------------------------------------------------------


def test_open_balance_grouped_over_time_is_refused(session, business, sales):
    """A balance is a state, not a flow. Summing it across months means nothing."""
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "party",
                "follow": [{"edge": "ordered_by", "direction": "in", "as": "o"}],
                "measures": ["open_balance"],
                "group_by": [
                    {"field": "root.name"},
                    {"field": "o.ordered_at", "bucket": "month", "as": "month"},
                ],
            },
        )
    assert "time" in str(refusal.value) or "additive" in str(refusal.value)


# --- filters, periods and paths ------------------------------------------------


def test_a_period_filter_uses_half_open_bounds(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "filter": [
                {
                    "field": "root.ordered_at",
                    "op": "gte",
                    "value": "2026-03-01T00:00:00Z",
                },
                {
                    "field": "root.ordered_at",
                    "op": "lt",
                    "value": "2026-04-01T00:00:00Z",
                },
            ],
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    assert total(result) == Decimal(1500), "April is excluded by the upper bound"


def test_grouping_by_month_buckets_the_timestamp(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["stated_order_amount"],
            "group_by": [
                {"field": "root.ordered_at", "bucket": "month", "as": "month"},
                {"field": "root.currency"},
            ],
        },
    )
    months = {
        (row["month"], row["root.currency"]): Decimal(row["stated_order_amount"])
        for row in result.rows
    }
    assert months[("2026-03", "EUR")] == Decimal(1500)
    assert months[("2026-04", "USD")] == Decimal(300)


def test_one_currency_may_be_summed_once_the_question_says_which(
    session, business, sales
):
    """The refusal said "filter the question down to one", and following that
    advice changed nothing: the check looked only at the axes. A question pinned
    to a single currency is exactly the case where a sum is meaningful."""
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "filter": [{"field": "root.currency", "op": "eq", "value": "EUR"}],
            "measures": ["stated_order_amount"],
        },
    )
    assert total(result) == Decimal(1500)


def test_two_currencies_are_still_refused_however_they_are_named(
    session, business, sales
):
    """The positive control: narrowing is not the same as pinning."""
    for condition in (
        {"field": "root.currency", "op": "ne", "value": "USD"},
        {"field": "root.currency", "op": "in", "value": ["EUR", "USD"]},
    ):
        with pytest.raises(TraversalRefused) as refusal:
            ask(
                session,
                business.tenant.id,
                **{
                    "from": "order",
                    "filter": [condition],
                    "measures": ["stated_order_amount"],
                },
            )
        assert refusal.value.code == "unit_mismatch", condition


def test_a_date_kept_as_text_cannot_be_folded_into_months(session, business, sales):
    """Found by asking it: `document_date` is a varchar on this table.

    PostgreSQL answers `date_trunc(varchar, varchar) does not exist`, which
    names two types and no question, and arrived at the reader as a 500. The
    refusal is made against the declared column instead.
    """
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "measures": ["order_count"],
                "group_by": [
                    {"field": "root.document_date", "bucket": "month", "as": "month"}
                ],
            },
        )
    assert refusal.value.code == "not_temporal"
    assert "document_date" in str(refusal.value)


def test_following_an_edge_backwards_reaches_the_customer(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "party",
            "follow": [{"edge": "ordered_by", "direction": "in", "as": "o"}],
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.name"}, {"field": "o.currency"}],
        },
    )
    rows = {
        (row["root.name"], row["o.currency"]): Decimal(row["stated_order_amount"])
        for row in result.rows
    }
    assert rows[("Müller GmbH", "EUR")] == Decimal(1500)


# --- the boundary --------------------------------------------------------------


def test_another_company_is_never_reached(session, business, sales, neighbour):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    assert Decimal(999999) not in {
        Decimal(row["stated_order_amount"]) for row in result.rows
    }
    assert total(result) == Decimal(1800)


def test_every_traversal_emits_exactly_one_statement(session, business, sales):
    """An eleven-thousand-query builder is the failure mode this could reproduce."""
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "follow": [{"edge": "contains", "as": "l"}, {"edge": "of_item", "as": "i"}],
            "filter": [{"field": "i.sku", "op": "eq", "value": business.item.sku}],
            "measures": ["order_count"],
            "group_by": [{"field": "root.sales_channel"}],
        },
    )
    assert result.statements == 1


def test_the_tenant_predicate_is_on_every_node_of_the_statement(
    session, business, sales
):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "follow": [{"edge": "contains", "as": "l"}, {"edge": "of_item", "as": "i"}],
            "measures": ["line_amount"],
            "group_by": [{"field": "i.sku"}, {"field": "root.currency"}],
        },
    )
    sql = result.sql.lower()
    assert sql.count("tenant_id") >= 3, "one per node, never fewer"
    assert business.tenant.id not in sql, (
        "the tenant is bound, not written into the text"
    )


# --- refusals that name what is wrong -----------------------------------------


def test_an_undeclared_edge_is_refused(session, business, sales):
    with pytest.raises(TraversalRefused, match="edge"):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "follow": [{"edge": "invented_by", "as": "x"}],
                "measures": ["stated_order_amount"],
                "group_by": [{"field": "root.currency"}],
            },
        )


def test_an_undeclared_measure_is_refused(session, business, sales):
    with pytest.raises(TraversalRefused, match="measure"):
        ask(session, business.tenant.id, **{"from": "order", "measures": ["profit"]})


def test_a_measure_that_does_not_live_on_the_path_is_refused(session, business, sales):
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "measures": ["allocated_amount"],
                "group_by": [{"field": "root.currency"}],
            },
        )
    assert "allocation" in str(refusal.value), (
        "the refusal must say which node it needs"
    )


def test_an_unknown_property_is_refused(session, business, sales):
    with pytest.raises(TraversalRefused, match="property"):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "measures": ["stated_order_amount"],
                "group_by": [{"field": "root.margin"}],
            },
        )


# --- filtering on an aggregate, and on a sub-path that must exist ----------------


def test_having_filters_on_the_aggregate(session, business, sales):
    """Customers with at least two orders — the count decides, not the rows."""
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "party",
            "follow": [{"edge": "ordered_by", "direction": "in", "as": "o"}],
            "measures": ["order_count"],
            "group_by": [{"field": "root.name"}],
            "having": [{"measure": "order_count", "op": "gte", "value": 2}],
        },
    )
    assert [row["root.name"] for row in result.rows] == ["Müller GmbH"]
    assert int(result.rows[0]["order_count"]) == 3


def test_having_below_the_threshold_returns_nothing(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "party",
            "follow": [{"edge": "ordered_by", "direction": "in", "as": "o"}],
            "measures": ["order_count"],
            "group_by": [{"field": "root.name"}],
            "having": [{"measure": "order_count", "op": "gte", "value": 99}],
        },
    )
    assert result.rows == ()


def test_having_on_a_measure_the_question_does_not_ask_for_is_refused(
    session, business, sales
):
    with pytest.raises(ValueError, match="does not ask for"):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "party",
                "follow": [{"edge": "ordered_by", "direction": "in", "as": "o"}],
                "measures": ["order_count"],
                "group_by": [{"field": "root.name"}],
                "having": [{"measure": "stated_order_amount", "op": "gte", "value": 1}],
            },
        )


def test_an_existence_test_narrows_without_multiplying(session, business, sales):
    """The order still counts once, although the test walks its four lines."""
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
            "exists": [
                {
                    "follow": [{"edge": "contains", "as": "l"}],
                    "filter": [
                        {"field": "l.sku", "op": "eq", "value": business.item.sku}
                    ],
                }
            ],
        },
    )
    by_currency = {
        row["root.currency"]: Decimal(row["stated_order_amount"]) for row in result.rows
    }
    assert by_currency["EUR"] == Decimal(1500), "1000 + 500, never 4000"
    assert result.statements == 1


def test_a_negated_existence_test_finds_what_is_missing(session, business, sales):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["order_count"],
            "group_by": [{"field": "root.currency"}],
            "exists": [
                {
                    "follow": [{"edge": "contains", "as": "l"}],
                    "filter": [{"field": "l.sku", "op": "eq", "value": "NOT-A-SKU"}],
                    "negated": True,
                }
            ],
        },
    )
    assert sum(int(row["order_count"]) for row in result.rows) == 3, (
        "every order qualifies"
    )


def test_an_existence_test_on_an_undeclared_edge_is_refused(session, business, sales):
    with pytest.raises((TraversalRefused, ValueError)):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "measures": ["order_count"],
                "group_by": [{"field": "root.currency"}],
                "exists": [{"follow": [{"edge": "invented", "as": "x"}]}],
            },
        )
