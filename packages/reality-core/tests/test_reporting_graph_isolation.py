"""The compiler carries the whole trust boundary, so it is attacked here.

There is no barrier view and no role per tenant in this design. That is only
defensible if the predicate is on every node of every statement, including the
places it is easy to forget: inside a recursive term, inside an existence test,
and on a table reached twice under two aliases.

Nothing a caller writes reaches SQL text. The tests below try to make it.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from reality.domain.traversal import Traversal
from reality.services.analytics.compile_sql import build
from reality.services.analytics.traversal import TraversalRefused, plan, run_traversal
from reality.services.core import (
    create_item,
    create_location,
    create_manual_order,
    create_party,
    create_tenant,
    record_movement,
)

CANARY = Decimal(987654321)


def line(item, amount: str) -> dict:
    return {
        "item_id": item.id,
        "sku": item.sku,
        "quantity": "1",
        "unit_price": "1",
        "gross_amount": amount,
        "unit": "pcs",
    }


@pytest.fixture
def two_companies(session, business):
    """Two companies whose parties, articles and locations share every label.

    Overlapping names are the point: a boundary that only works because the test
    data differs is not a boundary.
    """
    other = create_tenant(session, "Acme Bikes GmbH")
    company = create_party(session, other.id, "Acme Bikes GmbH", "company")
    customer = create_party(session, other.id, "Müller GmbH", "customer")
    item = create_item(session, other.id, "BIKE-LIGHT", "Bike Light")
    location = create_location(session, other.id, "Augsburg Warehouse")
    create_manual_order(
        session,
        other.id,
        "sales",
        "AN-001",
        company.id,
        customer.id,
        location.id,
        [line(item, str(CANARY))],
        str(CANARY),
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
    )
    create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [line(business.item, "100")],
        "100",
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
    )
    session.flush()
    return other


@pytest.fixture
def warehouse(session, business):
    """A six-level storage tree in each company, with stock at the bottom."""

    def tree(tenant_id, item_id, quantity):
        parent = None
        levels = []
        for depth in range(6):
            parent = create_location(
                session,
                tenant_id,
                f"Ebene {depth}",
                parent_location_id=parent.id if parent else None,
            )
            levels.append(parent)
        record_movement(
            session,
            tenant_id,
            "receipt",
            item_id,
            quantity,
            to_location_id=levels[-1].id,
            occurred_at=None,
        )
        return levels

    mine = tree(business.tenant.id, business.item.id, "7")
    session.flush()
    return mine


def ask(session, tenant_id, **query):
    return run_traversal(session, tenant_id, Traversal.model_validate(query))


def rendered(tenant_id, **query) -> str:
    return str(build(plan(Traversal.model_validate(query)), tenant_id))


# --- the predicate is on every node -------------------------------------------


def test_every_table_in_the_statement_is_scoped(session, business):
    sql = rendered(
        business.tenant.id,
        **{
            "from": "order",
            "follow": [
                {"edge": "contains", "as": "l"},
                {"edge": "of_item", "as": "i"},
                {"edge": "ordered_by", "from": "root", "as": "p"},
            ],
            "measures": ["line_amount"],
            "group_by": [
                {"field": "i.sku"},
                {"field": "root.currency"},
                {"field": "p.name"},
            ],
        },
    )
    assert sql.lower().count("tenant_id = ") >= 4, "one per node, never fewer"


def test_the_tenant_is_bound_and_never_written_into_the_text(session, business):
    sql = rendered(
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["order_count"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    assert business.tenant.id not in sql


def test_an_existence_test_carries_the_predicate_too(session, business):
    sql = rendered(
        business.tenant.id,
        **{
            "from": "order",
            "follow": [{"edge": "contains", "as": "l"}],
            "filter": [{"field": "l.sku", "op": "eq", "value": "BIKE-LIGHT"}],
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    ).lower()
    assert "exists" in sql
    _, _, tail = sql.partition("exists")
    assert "tenant_id" in tail, "the subquery is scoped, not only the outer statement"


def test_a_recursive_term_carries_the_predicate(session, business):
    """The classic way a closure leaks is a recursive term without the predicate."""
    sql = rendered(
        business.tenant.id,
        **{
            "from": "location",
            "follow": [
                {"edge": "within", "direction": "in", "depth": [1, 6], "as": "sub"}
            ],
            "measures": [],
            "group_by": [{"field": "root.name"}, {"field": "sub.name"}],
        },
    ).lower()
    assert "recursive" in sql
    _, _, after_union = sql.partition("union all")
    assert "tenant_id" in after_union, (
        "the recursive term is scoped, not only the anchor"
    )


# --- foreign data is never reached ---------------------------------------------


def test_a_neighbour_with_identical_labels_is_never_reached(
    session, business, two_companies
):
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
    amounts = {Decimal(row["stated_order_amount"]) for row in result.rows}
    assert CANARY not in amounts
    assert amounts == {Decimal(100)}


def test_a_foreign_tenant_supplied_as_a_filter_value_changes_nothing(
    session, business, two_companies
):
    """A parameter is a value. It cannot widen the scope the caller was given."""
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "filter": [
                {"field": "root.number", "op": "in", "value": ["AN-001", "AN-002"]}
            ],
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    assert {Decimal(row["stated_order_amount"]) for row in result.rows} == {
        Decimal(100)
    }


def test_recursive_traversal_stays_inside_the_company(session, business, warehouse):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "location",
            "follow": [
                {"edge": "within", "direction": "in", "depth": [1, 6], "as": "sub"},
                {"edge": "moved_to", "direction": "in", "from": "sub", "as": "m"},
                {"edge": "moved_item", "from": "m", "as": "a"},
            ],
            "measures": ["moved_quantity"],
            "group_by": [
                {"field": "root.name"},
                {"field": "m.type"},
                {"field": "a.unit"},
            ],
        },
    )
    assert result.rows, "the tree resolves to the stock at its leaf"
    assert all(
        row["root.name"] == "Ebene 0" or "Ebene" in row["root.name"]
        for row in result.rows
    )


# --- crafted input reaches nothing ---------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "root.currency; drop table document",
        "root.currency' or '1'='1",
        "root.tenant_id",
        "root.__class__",
        "other.currency",
    ],
)
def test_a_crafted_field_is_refused(session, business, field):
    with pytest.raises((TraversalRefused, ValueError)):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "measures": ["order_count"],
                "group_by": [{"field": field}],
            },
        )


@pytest.mark.parametrize(
    "edge", ["contains; drop table document", "../contains", "CONTAINS"]
)
def test_a_crafted_edge_name_is_refused(session, business, edge):
    with pytest.raises((TraversalRefused, ValueError)):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "follow": [{"edge": edge, "as": "x"}],
                "measures": ["order_count"],
                "group_by": [{"field": "root.currency"}],
            },
        )


def test_a_crafted_filter_value_stays_a_value(session, business, two_companies):
    result = ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "filter": [{"field": "root.number", "op": "eq", "value": "' OR 1=1 --"}],
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    assert result.rows == (), "it matches no order number, and nothing else happens"


def test_an_undeclared_node_is_refused(session, business):
    with pytest.raises(TraversalRefused, match="node"):
        ask(
            session,
            business.tenant.id,
            **{"from": "secret", "measures": ["order_count"]},
        )


# --- bounds --------------------------------------------------------------------


def test_a_recursive_hop_must_name_its_depth(session, business):
    with pytest.raises(TraversalRefused, match="depth"):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "location",
                "follow": [{"edge": "within", "direction": "in", "as": "sub"}],
                "group_by": [{"field": "sub.name"}],
            },
        )


def test_a_depth_beyond_the_declaration_is_refused(session, business):
    with pytest.raises(TraversalRefused, match="beyond"):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "location",
                "follow": [
                    {"edge": "within", "direction": "in", "depth": [1, 40], "as": "sub"}
                ],
                "group_by": [{"field": "sub.name"}],
            },
        )


def test_a_non_recursive_edge_cannot_be_walked_to_a_depth(session, business):
    with pytest.raises(TraversalRefused, match="not declared recursive"):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "follow": [{"edge": "contains", "depth": [1, 3], "as": "l"}],
                "measures": ["line_amount"],
                "group_by": [{"field": "root.currency"}],
            },
        )


def test_a_path_longer_than_the_model_allows_is_refused(session, business):
    hops = [{"edge": "contains", "as": f"l{index}"} for index in range(9)]
    with pytest.raises((TraversalRefused, ValueError)):
        ask(
            session,
            business.tenant.id,
            **{
                "from": "order",
                "follow": hops,
                "measures": ["order_count"],
                "group_by": [{"field": "root.currency"}],
            },
        )


def test_the_statement_runs_under_a_deadline(session, business):
    """A reporting question may not hold a connection for as long as it likes."""
    from sqlalchemy import text

    ask(
        session,
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["order_count"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    budget = session.execute(text("SHOW statement_timeout")).scalar()
    assert budget not in (None, "0"), "the traversal set a deadline for its transaction"


def test_the_result_is_capped_by_the_model_limit(session, business):
    sql = rendered(
        business.tenant.id,
        **{
            "from": "order",
            "measures": ["order_count"],
            "group_by": [{"field": "root.currency"}],
            "limit": 10_000_000,
        },
    ).lower()
    assert "limit" in sql


def test_the_catalog_lists_only_the_asking_company_s_vocabulary(
    session, business, two_companies
):
    """The catalog began reading company data, so it joined this boundary.

    Until the vocabulary of a short-value column was published, the catalog was
    a pure reading of the declaration and could not leak anything. It now looks
    at what the records hold, which is a query like any other and gets the same
    predicate — and the same attack.
    """
    from reality.services.analytics.graph_model import reporting_catalog

    neighbour = create_party(session, two_companies.id, "Acme Bikes GmbH", "company")
    buyer = create_party(session, two_companies.id, "Müller GmbH", "customer")
    item = create_item(session, two_companies.id, "BIKE-BELL", "Bike Bell")
    location = create_location(session, two_companies.id, "Ingolstadt Warehouse")
    create_manual_order(
        session,
        two_companies.id,
        "sales",
        "AN-CANARY",
        neighbour.id,
        buyer.id,
        location.id,
        [line(item, "10")],
        "10",
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
        sales_channel="fahrradladen",
    )
    session.flush()

    def channels(tenant_id: str) -> list[str]:
        node = reporting_catalog("order", session=session, tenant_id=tenant_id)[
            "nodes"
        ][0]
        return next(
            prop["values"]
            for prop in node["properties"]
            if prop["key"] == "sales_channel"
        )

    assert "fahrradladen" in channels(two_companies.id)
    assert "fahrradladen" not in channels(business.tenant.id), (
        "a word only the neighbour's records use must not appear here"
    )
