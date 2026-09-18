"""Nothing business-relevant is undeclared by accident.

The return path from a movement back to the customer was found by reading, and
reading is not a method. This holds the declaration against the schema on the two
axes that matter, and an omission has to be named with a reason before it passes.

The second axis is the one that is easy to forget: the purchase side lives in the
*same tables* as the sales side under different type values, so a foreign-key
audit alone reports `document` as fully covered and is wrong.
"""

from __future__ import annotations

import pytest
import yaml

from reality.config import config_text
from reality.db.core import Base
from reality.services.analytics.graph_model import reporting_graph

# Tables that are not business data. Named rather than pattern-matched, so adding
# one is a decision somebody makes and not a regex that quietly widens.
INFRASTRUCTURE = {
    "tenant",
    "app_user",
    "user_session",
    "email_verification_code",
    "tenant_membership",
    "access_application",
    "access_admission_counter",
    "security_audit_event",
    "company_invitation",
    "invitation_delivery",
    "chat_session",
    "chat_message",
    "ai_settings",
    "secret",
    "secret_audit_event",
    "mcp_access_token",
    "playground_run",
    "playground_step",
    "storyline_trace_entry",
    "storyline_package",
    "analytics_report",
    "analytics_report_draft",
    # A requested analysis holds a question and the answer it was given, which is
    # how somebody used the model — not a business record the model describes.
    "analysis_request",
    "business_event",
    "projection_row",
    "projection_checkpoint",
    "action",
    "reality_gap",
    "reality_gap_entry",
    "interpretation_rule",
    "rule_interpretation_outcome",
    "import_job",
    "source_system",
    "source_capability",
    "source_stream",
    "source_artifact",
    "interpretation_outcome",
    "interpretation_record_reference",
    "scheduled_job",
    "scheduled_job_run",
    "demo_data_connection",
    "ordinary_company_creation",
    "source_classification_mapping_revision",
}

# Slices this feature deliberately leaves for later. Each names why, so a deferral
# stays distinguishable from a gap — the distinction the audit was written to make.
DEFERRED = {
    "finance_detail": (
        (
            "Accounts, components and targets are the finance slice; the first "
            "slice reaches finance only through postings and allocations."
        ),
        {
            "finance_state",
            "finance_role_destination",
            "finance_reference",
            "component_assignment_revision",
            "component_assignment_part",
            "accounting_target",
            "accounting_target_reference",
            "finance_target_mapping_revision",
        },
        set(),
    ),
}

DEFERRED_TABLES = {t for _, tables, _ in DEFERRED.values() for t in tables}
DEFERRED_VALUES = {v for _, _, values in DEFERRED.values() for v in values}

# Values of the discriminating columns, each with the number of occurrences in the
# package that is the evidence it is real. There is no vocabulary catalog to read
# this from yet; see specs/224-native-reporting-platform/coverage.md, finding 4.
VOCABULARY = {
    ("document", "type"): {
        "sales_order",
        "purchase_order",
        "sales_invoice",
        "supplier_invoice",
        "credit_note",
        "supplier_credit_note",
        "customer_payment",
        "supplier_payment",
        "customer_refund",
        "supplier_refund",
        "customer_settlement_adjustment",
        "supplier_settlement_adjustment",
        "opening_customer_debt",
        "opening_supplier_debt",
    },
    ("commitment", "type"): {"customer_delivery", "supplier_delivery"},
    ("movement", "type"): {
        "opening_stock",
        "receipt",
        "shipment",
        "return",
        "supplier_return",
        "transfer",
        "adjustment",
        "correction",
    },
}


@pytest.fixture(scope="module")
def graph():
    return reporting_graph()


@pytest.fixture(scope="module")
def business_tables() -> set[str]:
    return {t.name for t in Base.metadata.tables.values()} - INFRASTRUCTURE


def declared_tables(graph) -> set[str]:
    tables = {n.table for n in graph.nodes.values() if n.table}
    for node in graph.nodes.values():
        for spec in (node.correction_table, node.revision_table):
            if spec:
                tables.add(spec.table)
    return tables


# --- axis 1: structure ---------------------------------------------------------


def test_every_business_table_is_declared_or_deferred_with_a_reason(
    graph, business_tables
):
    undeclared = business_tables - declared_tables(graph) - DEFERRED_TABLES
    assert not undeclared, (
        f"{sorted(undeclared)} is neither declared nor named as deferred. "
        "Add a node, or name the slice it belongs to with a reason."
    )


def test_a_deferral_is_removed_once_it_is_declared(graph):
    """A stale exemption hides the next real gap, so it fails like a missing one."""
    stale = declared_tables(graph) & DEFERRED_TABLES
    assert not stale, f"{sorted(stale)} is declared but still listed as deferred"


def test_every_foreign_key_between_two_declared_nodes_is_an_edge(graph):
    """This is where a real gap hides: both ends present, the link forgotten."""
    by_table = {n.table: name for name, n in graph.nodes.items() if n.table}
    declared = {e.via for e in graph.edges.values() if e.via}
    missing = []
    for table in Base.metadata.tables.values():
        if table.name not in by_table:
            continue
        for column in table.columns:
            if column.name == "tenant_id":
                continue
            for key in column.foreign_keys:
                target = key.column.table.name
                if target not in by_table or target == table.name:
                    continue
                reference = f"{table.name}.{column.name}"
                if reference not in declared:
                    missing.append(f"{reference} -> {target}")
    assert not missing, (
        "both ends are declared nodes but the link is not an edge: "
        f"{sorted(missing)}. Declare it with its multiplicity, or add the column "
        "to a deferred slice."
    )


# --- axis 2: vocabulary --------------------------------------------------------


def test_every_type_value_is_covered_by_a_node_or_deferred(graph):
    """The axis a foreign-key audit cannot see, and the one the purchase side hid in."""
    for (table, column), values in VOCABULARY.items():
        covered: set[str] = set()
        catch_all = False
        for node in graph.nodes.values():
            if node.table != table:
                continue
            selector = (node.where or {}).get(column)
            if selector is None:
                catch_all = True
            elif isinstance(selector, list):
                covered |= set(selector)
            else:
                covered.add(selector)
        if catch_all:
            continue
        open_values = values - covered - DEFERRED_VALUES
        assert not open_values, (
            f"{table}.{column} values {sorted(open_values)} are not reachable "
            "through any node. A question about them would silently return nothing."
        )


def test_a_node_only_discriminates_on_known_values(graph):
    for name, node in graph.nodes.items():
        for column, selector in (node.where or {}).items():
            known = VOCABULARY.get((node.table, column))
            if known is None:
                continue
            chosen = set(selector) if isinstance(selector, list) else {selector}
            unknown = chosen - known
            assert not unknown, (
                f"node {name} selects {sorted(unknown)} for {node.table}.{column}, "
                "which no code in this package produces"
            )


# --- axis 3: the repository's own data model catalog ---------------------------


def test_declared_nodes_appear_in_the_data_model_catalog(graph):
    """The declaration must not describe business concepts the catalog omits.

    `config/data_model.yaml` is where tables and columns are systematically
    recorded. Where it has drifted, that is its own work rather than something to
    route around here — but it may not drift further because of this feature.
    """
    catalog = set(yaml.safe_load(config_text("data_model.yaml"))["tables"])
    known_drift = {"shipment", "return_announcement"}
    undocumented = {n.table for n in graph.nodes.values() if n.table} - catalog
    assert undocumented <= known_drift, (
        f"{sorted(undocumented - known_drift)} is declared as a reporting node but "
        "is not in config/data_model.yaml"
    )
