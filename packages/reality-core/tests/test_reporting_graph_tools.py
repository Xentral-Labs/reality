"""The graph as an agent tool, and the refusal it hands back.

A refusal is the most useful answer this feature produces: it names the edge that
fanned out, the unit that cannot be added, or the property that does not exist. A
model can act on that, where it cannot act on a wrong number — so the code travels
with it.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from reality.mcp.server import error_code
from reality.services.analytics.traversal import TraversalRefused
from reality.services.core import InvalidOperation, create_manual_order
from reality.tools.application import TOOLS, run_read_tool


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


def ask(session, tenant_id, **arguments):
    return run_read_tool(session, tenant_id, "graph.ask", arguments)


# --- registration ---------------------------------------------------------------


def test_both_tools_are_registered_and_read_only():
    for name in ("graph.catalog", "graph.ask"):
        assert name in TOOLS, name
        assert TOOLS[name].mutating is False, f"{name} must never mutate"


def test_the_catalog_tool_describes_what_can_be_asked(session, business):
    catalog = run_read_tool(session, business.tenant.id, "graph.catalog", {"node": "order"})
    entry = catalog["nodes"][0]
    assert entry["key"] == "order"
    assert {m["key"] for m in entry["measures"]} >= {"stated_order_amount", "order_count"}
    assert {e["key"]: e["multiplicity"] for e in entry["edges"]}["contains"] == "1:n"


# --- asking ---------------------------------------------------------------------


def test_the_object_surface_answers(session, business, sales):
    answer = ask(
        session,
        business.tenant.id,
        question={
            "from": "order",
            "measures": ["stated_order_amount"],
            "group_by": [{"field": "root.currency"}],
        },
    )
    assert Decimal(answer["rows"][0]["stated_order_amount"]) == Decimal(1000)
    assert answer["statements"] == 1
    assert answer["model_version"]


def test_the_path_surface_answers(session, business, sales):
    answer = ask(
        session,
        business.tenant.id,
        path="MATCH (o:order) RETURN o.currency, sum(stated_order_amount)",
    )
    assert Decimal(answer["rows"][0]["stated_order_amount"]) == Decimal(1000)


def test_the_answer_carries_the_question_back(session, business, sales):
    """What is echoed is what a saved report would hold, whichever surface asked."""
    answer = ask(
        session,
        business.tenant.id,
        path="MATCH (o:order)-[:contains]->(l:order_line) RETURN o.currency, sum(line_amount)",
    )
    assert answer["question"]["from"] == "order"
    assert answer["path"] == ["o-[contains]->l"]


def test_asking_with_both_surfaces_at_once_is_refused(session, business):
    with pytest.raises(ValueError, match="exactly one"):
        ask(
            session,
            business.tenant.id,
            question={"from": "order", "measures": ["order_count"]},
            path="MATCH (o:order) RETURN order_count",
        )


# --- the refusal is the answer ---------------------------------------------------


@pytest.mark.parametrize(
    ("question", "code"),
    [
        (
            {
                "from": "order",
                "follow": [{"edge": "contains", "as": "l"}, {"edge": "of_item", "as": "i"}],
                "measures": ["stated_order_amount"],
                "group_by": [{"field": "i.sku"}],
            },
            "fan_out",
        ),
        ({"from": "order", "measures": ["stated_order_amount"]}, "unit_mismatch"),
        ({"from": "order", "measures": ["profit"]}, "unknown_measure"),
        (
            {
                "from": "order",
                "follow": [{"edge": "invented", "as": "x"}],
                "measures": ["order_count"],
                "group_by": [{"field": "root.currency"}],
            },
            "unknown_edge",
        ),
        (
            {
                "from": "order",
                "measures": ["order_count"],
                "group_by": [{"field": "root.margin"}],
            },
            "unknown_property",
        ),
    ],
)
def test_a_refusal_carries_its_stable_code(session, business, question, code):
    with pytest.raises(TraversalRefused) as refusal:
        ask(session, business.tenant.id, question=question)
    assert refusal.value.code == code
    assert str(refusal.value), "a code without a sentence is not a refusal"


def test_a_refusal_reaches_the_agent_as_an_invalid_operation(session, business):
    """It is not an outage. The question was understood and cannot be answered."""
    with pytest.raises(InvalidOperation) as refusal:
        ask(session, business.tenant.id, question={"from": "order", "measures": ["profit"]})
    assert error_code(refusal.value) == "invalid_operation"


def test_a_write_attempt_through_the_path_surface_is_refused(session, business):
    with pytest.raises(InvalidOperation, match="only reads"):
        ask(session, business.tenant.id, path="MATCH (o:order) DELETE o")
