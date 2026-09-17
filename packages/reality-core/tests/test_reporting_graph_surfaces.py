"""Two surfaces, one question.

Whatever a person types and whatever the chat builds must arrive as the same
object, because that object is what is stored, fingerprinted and executed. If the
surfaces could disagree, the text would be a second implementation of the model.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from reality.domain.traversal import Traversal
from reality.services.analytics.cypher_surface import CypherRefused, parse
from reality.services.analytics.traversal import run_traversal
from reality.services.core import create_manual_order


@pytest.fixture
def sales(session, business):
    create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "AN-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "sku": business.item.sku,
                "quantity": "1",
                "unit_price": "1",
                "gross_amount": "250",
                "unit": "pcs",
            }
            for _ in range(4)
        ],
        "1000",
        currency="EUR",
        ordered_at="2026-03-10T10:00:00Z",
        document_date="2026-03-10",
    )
    session.flush()


# --- the two surfaces agree ----------------------------------------------------


def test_text_and_object_produce_the_same_question(business):
    text = parse(
        """
        MATCH (c:party {id: $customer})<-[:ordered_by]-(o:order)
        WHERE o.ordered_at >= $from AND o.ordered_at < $until
        RETURN month(o.ordered_at), o.currency, sum(stated_order_amount)
        """,
        {"customer": business.customer.id, "from": "2026-03-01", "until": "2026-04-01"},
    )
    obj = Traversal.model_validate(
        {
            "from": "party",
            "as": "c",
            "follow": [
                {"edge": "ordered_by", "direction": "in", "as": "o", "from": "c"}
            ],
            "filter": [
                {"field": "c.id", "op": "eq", "value": business.customer.id},
                {"field": "o.ordered_at", "op": "gte", "value": "2026-03-01"},
                {"field": "o.ordered_at", "op": "lt", "value": "2026-04-01"},
            ],
            "measures": ["stated_order_amount"],
            "group_by": [
                {"field": "o.ordered_at", "bucket": "month", "as": "month"},
                {"field": "o.currency"},
            ],
        }
    )
    assert text == obj


def test_both_surfaces_return_the_same_rows(session, business, sales):
    text = parse("MATCH (o:order) RETURN o.currency, sum(stated_order_amount)")
    obj = Traversal.model_validate(
        {
            "from": "order",
            "as": "o",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "o.currency"}],
        }
    )
    from_text = run_traversal(session, business.tenant.id, text)
    from_object = run_traversal(session, business.tenant.id, obj)
    assert from_text.rows == from_object.rows
    assert Decimal(from_text.rows[0]["stated_order_amount"]) == Decimal(1000)


# --- the path ------------------------------------------------------------------


def test_a_relationship_is_read_in_both_directions():
    outward = parse(
        "MATCH (o:order)-[:contains]->(l:order_line) RETURN sum(line_amount), o.currency"
    )
    assert outward.follow[0].direction == "out"
    inward = parse(
        "MATCH (p:party)<-[:ordered_by]-(o:order) RETURN sum(stated_order_amount), o.currency"
    )
    assert inward.follow[0].direction == "in"


def test_a_variable_depth_relationship_carries_its_bounds():
    query = parse("MATCH (l:location)<-[:within*1..6]-(sub:location) RETURN sub.name")
    assert query.follow[0].depth == (1, 6)


def test_an_anonymous_node_still_gets_an_alias():
    query = parse(
        "MATCH (o:order)-[:contains]->(:order_line) RETURN sum(line_amount), o.currency"
    )
    assert query.follow[0].as_.startswith("_")


def test_a_property_in_the_pattern_becomes_a_filter():
    query = parse(
        "MATCH (o:order {currency: 'EUR'}) RETURN sum(stated_order_amount), o.currency"
    )
    assert any(c.field == "o.currency" and c.value == "EUR" for c in query.filter)


def test_a_relationship_without_a_direction_is_refused():
    with pytest.raises(CypherRefused, match="one way"):
        parse("MATCH (o:order)-[:contains]-(l:order_line) RETURN sum(line_amount)")


def test_a_first_node_without_a_kind_is_refused():
    with pytest.raises(CypherRefused, match="names its kind"):
        parse("MATCH (o) RETURN sum(stated_order_amount)")


# --- the deliberate divergence --------------------------------------------------


def test_arithmetic_on_a_property_is_refused_with_the_reason():
    """Literal Cypher would return the multiplied total here without complaint."""
    with pytest.raises(CypherRefused) as refusal:
        parse(
            "MATCH (o:order)-[:contains]->(l:order_line) "
            "RETURN l.sku, sum(o.gross_amount)"
        )
    message = str(refusal.value)
    assert "multiplied total" in message
    assert "declared measures" in message


def test_a_declared_measure_is_accepted_bare_or_wrapped():
    wrapped = parse("MATCH (o:order) RETURN o.currency, sum(stated_order_amount)")
    bare = parse("MATCH (o:order) RETURN o.currency, stated_order_amount")
    assert wrapped.measures == bare.measures == ("stated_order_amount",)


# --- nothing but reading --------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "MATCH (o:order) DELETE o",
        "CREATE (o:order) RETURN o.currency",
        "MATCH (o:order) SET o.currency = 'USD' RETURN o.currency",
        "MATCH (o:order) CALL db.labels() RETURN o.currency",
        "MATCH (o:order) MERGE (p:party) RETURN o.currency",
    ],
)
def test_anything_that_writes_is_refused(text):
    with pytest.raises(CypherRefused, match="only reads"):
        parse(text)


def test_a_question_without_return_is_refused():
    with pytest.raises(CypherRefused, match="RETURN"):
        parse("MATCH (o:order)")


def test_a_question_without_match_is_refused():
    with pytest.raises(CypherRefused, match="MATCH"):
        parse("RETURN sum(stated_order_amount)")


def test_or_is_not_admitted():
    with pytest.raises(CypherRefused, match="OR"):
        parse(
            "MATCH (o:order) WHERE o.currency = 'EUR' OR o.currency = 'USD' "
            "RETURN sum(stated_order_amount), o.currency"
        )


def test_a_missing_parameter_is_named():
    with pytest.raises(CypherRefused, match=r"\$customer"):
        parse("MATCH (c:party {id: $customer}) RETURN c.name")


# --- ordering and limit ---------------------------------------------------------


def test_order_and_limit_are_carried():
    query = parse(
        "MATCH (o:order) RETURN o.currency, sum(stated_order_amount) "
        "ORDER BY sum(stated_order_amount) DESC LIMIT 10"
    )
    assert query.order_by[0].by == "stated_order_amount"
    assert query.order_by[0].descending is True
    assert query.limit == 10


# --- the model still decides ----------------------------------------------------


def test_the_text_surface_does_not_bypass_the_measure_rules(session, business, sales):
    """Whatever the surface, the fan-out rule is the model's to enforce."""
    from reality.services.analytics.traversal import TraversalRefused

    query = parse(
        "MATCH (o:order)-[:contains]->(l:order_line)-[:of_item]->(i:item) "
        "RETURN i.sku, sum(stated_order_amount)"
    )
    with pytest.raises(TraversalRefused, match="multiply"):
        run_traversal(session, business.tenant.id, query)


def test_an_undeclared_edge_in_text_is_refused_by_the_model(session, business, sales):
    from reality.services.analytics.traversal import TraversalRefused

    query = parse(
        "MATCH (o:order)-[:invented]->(x:party) RETURN x.name, sum(stated_order_amount)"
    )
    with pytest.raises(TraversalRefused, match="edge"):
        run_traversal(session, business.tenant.id, query)


# --- the terminal surface -------------------------------------------------------


def test_the_graph_commands_are_registered():
    """`reality graph catalog` and `reality graph ask` are how this is first touched."""
    from reality.cli.app import app

    groups = {group.name for group in app.registered_groups}
    assert "graph" in groups
    graph = next(group for group in app.registered_groups if group.name == "graph")
    assert {command.name for command in graph.typer_instance.registered_commands} == {
        "catalog",
        "ask",
    }


def test_the_terminal_accepts_either_syntax(session, business, sales, monkeypatch):
    """The CLI reads the path syntax or a stored object, and asks the same question."""
    from reality.domain.traversal import Traversal
    from reality.services.analytics.cypher_surface import parse

    text = parse("MATCH (o:order) RETURN o.currency, sum(stated_order_amount)")
    stored = Traversal.model_validate(
        {
            "from": "order",
            "as": "o",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "o.currency"}],
        }
    )
    assert text == stored, "what the terminal parses is what a saved report holds"
