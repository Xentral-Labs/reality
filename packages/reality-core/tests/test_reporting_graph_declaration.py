"""The declaration must refuse anything that could produce a confident wrong number.

Each test here names the wrong number it prevents, because a validation rule
without that is indistinguishable from bureaucracy.
"""

from __future__ import annotations

import copy

import pytest
import yaml

from reality.config import config_text
from reality.db.core import Base
from reality.services.analytics.graph_model import (
    REPORTING_GRAPH_FILE,
    ReportingGraphError,
    parse_reporting_graph,
    reporting_catalog,
    reporting_graph,
)


@pytest.fixture(scope="module")
def payload() -> dict:
    return yaml.safe_load(config_text(REPORTING_GRAPH_FILE))


def broken(payload: dict, mutate) -> dict:
    copied = copy.deepcopy(payload)
    mutate(copied)
    return copied


# --- the declaration that ships ------------------------------------------------


def test_shipped_declaration_loads_and_agrees_with_the_schema():
    graph = reporting_graph()
    assert graph.nodes and graph.edges and graph.measures
    assert graph.limits.statements_per_traversal == 1


def test_every_declared_table_and_column_exists():
    graph = reporting_graph()
    tables = {
        t.name: {c.name for c in t.columns} for t in Base.metadata.tables.values()
    }
    for name, node in graph.nodes.items():
        if node.table is None:
            continue
        assert node.table in tables, name
        assert node.key in tables[node.table], name
        for prop in node.properties:
            column = node.column_of(prop)
            assert column in tables[node.table], f"{name}.{prop} -> {column}"


def test_catalog_is_generated_from_the_declaration():
    catalog = reporting_catalog("order")
    entry = catalog["nodes"][0]
    assert entry["key"] == "order"
    assert {m["key"] for m in entry["measures"]} >= {
        "stated_order_amount",
        "order_count",
    }
    edges = {e["key"]: e["multiplicity"] for e in entry["edges"]}
    assert edges["ordered_by"] == "n:1"
    assert edges["contains"] == "1:n", "the fan-out has to be visible in the catalog"


def test_the_catalog_says_what_sort_of_value_each_field_holds():
    """A filter row has to choose an editor, and the schema already knows.

    Guessing from the column name works until a company names a text column
    `ordered_at_note`, so the kind comes from the declared table rather than
    from the word.
    """
    kinds = {
        prop["key"]: prop["kind"]
        for prop in reporting_catalog("order")["nodes"][0]["properties"]
    }
    assert kinds["ordered_at"] == "time"
    assert kinds["currency"] == "text"
    assert set(kinds.values()) <= {"time", "number", "boolean", "text"}


def test_unknown_node_is_refused_by_the_catalog():
    with pytest.raises(ReportingGraphError):
        reporting_catalog("not_a_node")


# --- grain, key and correction semantics --------------------------------------


def test_node_without_correction_semantics_is_refused(payload):
    """Without it a reversal is either counted twice or dropped, silently."""

    def mutate(doc):
        del doc["nodes"]["order"]["corrections"]

    with pytest.raises(ValueError, match="corrections"):
        parse_reporting_graph(broken(payload, mutate))


def test_revised_node_without_its_revision_table_is_refused(payload):
    """Summing every revision multiplies the promise by the times it changed."""

    def mutate(doc):
        del doc["nodes"]["commitment"]["revision_table"]

    with pytest.raises(ValueError, match="revision table"):
        parse_reporting_graph(broken(payload, mutate))


def test_compensating_node_without_its_correction_table_is_refused(payload):
    """A row count cannot then tell one corrected event from three separate ones."""

    def mutate(doc):
        del doc["nodes"]["movement"]["correction_table"]

    with pytest.raises(ValueError, match="correction table"):
        parse_reporting_graph(broken(payload, mutate))


def test_node_without_grain_is_refused(payload):
    def mutate(doc):
        del doc["nodes"]["order"]["grain"]

    with pytest.raises(ValueError):
        parse_reporting_graph(broken(payload, mutate))


def test_unsupported_temporal_coverage_cannot_be_declared(payload):
    """An as-of claim without a history model would answer with today's rows."""

    def mutate(doc):
        doc["nodes"]["order"]["coverage"] = ["current", "as_of_effective"]

    with pytest.raises(ValueError, match="history model"):
        parse_reporting_graph(broken(payload, mutate))


# --- multiplicity and direction -----------------------------------------------


def test_reversed_multiplicity_is_refused(payload):
    """The EUR 1,000 order with four lines returning 4,000 starts here."""

    def mutate(doc):
        doc["edges"]["contains"]["multiplicity"] = "n:1"

    with pytest.raises(ReportingGraphError, match="wrong way round"):
        parse_reporting_graph(broken(payload, mutate))


def test_edge_without_multiplicity_is_refused(payload):
    def mutate(doc):
        del doc["edges"]["contains"]["multiplicity"]

    with pytest.raises(ValueError):
        parse_reporting_graph(broken(payload, mutate))


def test_edge_carried_by_a_column_that_points_elsewhere_is_refused(payload):
    def mutate(doc):
        doc["edges"]["ordered_by"]["via"] = "document.payment_term_id"

    with pytest.raises(ReportingGraphError, match="foreign key"):
        parse_reporting_graph(broken(payload, mutate))


def test_edge_to_an_unknown_node_is_refused(payload):
    def mutate(doc):
        doc["edges"]["ordered_by"]["to"] = "supplier"

    with pytest.raises(ValueError, match="unknown node"):
        parse_reporting_graph(broken(payload, mutate))


def test_edge_on_a_missing_column_is_refused(payload):
    def mutate(doc):
        doc["edges"]["ordered_by"]["via"] = "document.no_such_column"

    with pytest.raises(ReportingGraphError, match="does not exist"):
        parse_reporting_graph(broken(payload, mutate))


# --- recursion ----------------------------------------------------------------


def test_recursive_edge_must_be_self_referencing(payload):
    def mutate(doc):
        doc["edges"]["ordered_by"]["recursive"] = {"max_depth": 3, "on_cycle": "stop"}

    with pytest.raises(ValueError, match="self-referencing"):
        parse_reporting_graph(broken(payload, mutate))


def test_recursive_edge_without_a_depth_bound_is_refused(payload):
    """Unbounded traversal is a way to exhaust a connection, not a question."""

    def mutate(doc):
        del doc["edges"]["within"]["recursive"]["max_depth"]

    with pytest.raises(ValueError):
        parse_reporting_graph(broken(payload, mutate))


def test_recursive_depth_beyond_the_model_limit_is_refused(payload):
    def mutate(doc):
        doc["edges"]["within"]["recursive"]["max_depth"] = 12
        doc["limits"]["max_recursive_depth"] = 6

    with pytest.raises(ValueError, match="beyond the model"):
        parse_reporting_graph(broken(payload, mutate))


# --- units and additivity -----------------------------------------------------


def test_currency_measure_without_its_unit_column_is_refused(payload):
    """Otherwise euros and dollars add up to a number that means nothing."""

    def mutate(doc):
        doc["measures"]["stated_order_amount"]["unit"] = {"kind": "currency"}

    with pytest.raises(ValueError, match="unit"):
        parse_reporting_graph(broken(payload, mutate))


def test_measure_without_additivity_is_refused(payload):
    def mutate(doc):
        del doc["measures"]["stated_order_amount"]["additive_over"]

    with pytest.raises(ValueError):
        parse_reporting_graph(broken(payload, mutate))


def test_measure_cannot_be_additive_and_never_additive_over_the_same_axis(payload):
    def mutate(doc):
        doc["measures"]["stated_order_amount"]["additive_over"] = ["time", "currency"]

    with pytest.raises(ValueError, match="never additive"):
        parse_reporting_graph(broken(payload, mutate))


def test_open_balance_is_declared_non_additive_over_time():
    """A balance is a state, not a flow. Summing it across months is meaningless."""
    graph = reporting_graph()
    assert "time" in graph.measures["open_balance"].never_across


def test_quantity_is_never_additive_across_units():
    graph = reporting_graph()
    for key in ("ordered_quantity", "moved_quantity"):
        assert "unit" in graph.measures[key].never_across, key


def test_measure_on_an_unknown_node_is_refused(payload):
    def mutate(doc):
        doc["measures"]["stated_order_amount"]["node"] = "invoice_header"

    with pytest.raises(ValueError, match="unknown node"):
        parse_reporting_graph(broken(payload, mutate))


def test_measure_on_a_missing_column_is_refused(payload):
    def mutate(doc):
        doc["measures"]["stated_order_amount"]["source"] = "no_such_column"

    with pytest.raises(ReportingGraphError, match="does not exist"):
        parse_reporting_graph(broken(payload, mutate))


# --- a forgotten measure and a deliberate one must not look alike -------------


def test_node_without_a_measure_must_say_so(payload):
    def mutate(doc):
        doc["nodes"]["item"].pop("measures", None)

    with pytest.raises(ValueError, match="measures: none"):
        parse_reporting_graph(broken(payload, mutate))


def test_node_claiming_no_measure_while_carrying_one_is_refused(payload):
    def mutate(doc):
        doc["nodes"]["order"]["measures"] = "none"

    with pytest.raises(ValueError, match="says it has no measure"):
        parse_reporting_graph(broken(payload, mutate))


# --- stored edges -------------------------------------------------------------


def test_a_fact_edge_is_declared_like_any_other(payload):
    graph = reporting_graph()
    edge = graph.edges["belongs_to_campaign"]
    assert edge.fact is not None and edge.via is None
    assert edge.multiplicity == "n:1", "a stored edge fans out like any other"
    assert edge.writable is not None


def test_a_column_edge_cannot_be_written(payload):
    """The column already holds the link; writing one would be a second truth."""

    def mutate(doc):
        doc["edges"]["ordered_by"]["writable"] = {"by": ["member"]}

    with pytest.raises(ValueError, match="already holds the link"):
        parse_reporting_graph(broken(payload, mutate))


def test_an_edge_needs_exactly_one_carrier(payload):
    def mutate(doc):
        doc["edges"]["ordered_by"]["fact"] = {"predicate": "ordered_by"}

    with pytest.raises(ValueError, match="exactly one"):
        parse_reporting_graph(broken(payload, mutate))


# --- unknown keys -------------------------------------------------------------


def test_an_unknown_key_is_refused_rather_than_ignored(payload):
    """A typo that is silently ignored is a declaration nobody can trust."""

    def mutate(doc):
        doc["nodes"]["order"]["multiplicty"] = "n:1"

    with pytest.raises(ValueError):
        parse_reporting_graph(broken(payload, mutate))


# --- the words a person reads -----------------------------------------------


def test_every_node_edge_and_measure_has_a_business_label():
    """Keys are how the model talks to itself; nobody should have to learn them."""
    graph = reporting_graph()
    for name, node in graph.nodes.items():
        assert node.label, f"node {name} has no label"
    for name, edge in graph.edges.items():
        assert edge.label, f"edge {name} has no label"
    for name, measure in graph.measures.items():
        assert measure.label, f"measure {name} has no label"


def test_the_catalog_speaks_the_language_it_is_asked_for():
    german = reporting_catalog("order", "de")["nodes"][0]
    assert german["label"] == "Auftrag"
    assert {m["label"] for m in german["measures"]} >= {"Auftragswert"}
    assert {e["label"] for e in german["edges"]} >= {"enthält"}
    assert {p["label"] for p in german["properties"]} >= {"Währung"}


def test_an_unknown_language_falls_back_rather_than_failing():
    """A missing translation shows the English word, which is never a lie."""
    assert reporting_catalog("order", "fr")["nodes"][0]["label"] == "Sales order"


def test_the_identity_is_offered_for_grouping():
    """Two customers with the same name are two customers.

    The executor has always accepted the key; the catalog did not publish it, so
    neither surface offered it and every grouped report silently merged them.
    Found by an acceptance run: a saved customer report grouped by name.
    """
    party = reporting_catalog("party")["nodes"][0]
    identity = [prop for prop in party["properties"] if prop.get("identity")]
    assert [prop["key"] for prop in identity] == ["id"]
    assert identity[0]["label"] == "Identity"
    assert reporting_catalog("party", "de")["nodes"][0]["properties"]
    german = {
        prop["key"]: prop["label"]
        for prop in reporting_catalog("party", "de")["nodes"][0]["properties"]
    }
    assert german["id"] == "Kennung"
