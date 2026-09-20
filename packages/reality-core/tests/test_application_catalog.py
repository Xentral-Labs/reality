import pathlib
import re

import pytest
import yaml

from reality import catalogs
from reality.catalogs import load_application_catalog, validate_tenant_isolation_catalog
from reality.config import config_text
from reality.services.projections import OPERATIONAL_PROJECTIONS


def test_split_catalog_is_complete_and_composed():
    catalog = load_application_catalog()

    assert catalog["command_count"] == 92
    assert catalog["event_count"] == 60
    assert catalog["projection_count"] == len(OPERATIONAL_PROJECTIONS) == 13
    assert catalog["fact_predicate_count"] == 7
    assert catalog["operational_exception_classes"] == [
        "overdue_outgoing_customer_commitment",
        "outgoing_commitment_at_risk",
        "order_stalled",
        "overdue_incoming_supplier_commitment",
        "shipped_not_billed",
        "billed_not_received",
        "invoice_price_differs",
        "sold_below_purchase_price",
        "returned_not_credited",
        "credited_not_returned",
        "supplier_return_not_credited",
        "supplier_credit_not_returned",
        "return_unresolved",
        "receipt_unbilled",
        "units_not_comparable",
        "reservation_exceeds_stock",
        "silent_source",
        "source_interpretation_failure",
        "unexplained_movement",
        "sales_invoice_unposted",
        "supplier_invoice_unposted",
        "credit_note_unposted",
        "credit_note_unsettled",
        "supplier_credit_unposted",
        "supplier_credit_unclaimed",
        "overdue_receivable",
        "credit_limit_exceeded",
        "overdue_payable",
        "purchase_discount_available",
        "duplicate_supplier_invoice",
        "unmatched_financial_event",
        "announced_return_not_arrived",
        "commitment_hold_unreleased",
        "party_hold_unreleased",
        "stock_expired",
    ]
    assert {entry["materialized_as"] for entry in catalog["projections"]} == set(
        OPERATIONAL_PROJECTIONS
    )
    assert [workspace["key"] for workspace in catalog["workspaces"]] == [
        "company",
        "operations",
        "warehouse",
        "finance",
        "data",
    ]
    company = catalog["workspaces"][0]
    operations = catalog["workspaces"][1]
    warehouse = catalog["workspaces"][2]
    assert [view["key"] for view in company["views"]].count("activity") == 1
    assert all(
        view["key"] != "activity"
        for workspace in catalog["workspaces"][1:]
        for view in workspace["views"]
    )
    assert [view["key"] for view in warehouse["views"]][:3] == [
        "inventory",
        "warehouse_queue",
        "reservations",
    ]
    operation_views = {view["key"]: view for view in operations["views"]}
    warehouse_views = {view["key"]: view for view in warehouse["views"]}
    assert operation_views["orders"]["projection"] == "fulfillment_queue"
    assert warehouse_views["warehouse_queue"]["projection"] == "fulfillment_queue"
    assert operation_views["fulfillment_blockers"]["projection"] == (
        "fulfillment_blockers"
    )
    assert warehouse_views["supply_demand"]["projection"] == "item_supply_demand"
    classified_projections = {
        view.get("projection")
        for workspace in catalog["workspaces"]
        for view in workspace["views"]
    }
    assert "tenant_usage" not in classified_projections
    assert "price_resolution" not in classified_projections
    assert {action["command"] for action in warehouse["actions"]} >= {
        "reserve",
        "record_movement",
        "correct_movement",
        "hold_commitment",
    }
    assert [action["command"] for action in operations["actions"]] == [
        "create_manual_order",
        "reserve",
        "hold_commitment",
        "hold_document_commitments",
        "hold_party_delivery",
    ]
    assert [action["command"] for action in operations["actions"][:2]] == [
        "create_manual_order",
        "reserve",
    ]
    assert [action["command"] for action in company["actions"]] == ["observe_fact"]
    assert [action["command"] for action in catalog["workspaces"][3]["actions"]] == [
        "post_customer_payment",
        "post_supplier_payment",
    ]
    # Data Management is a set of registers and commands nothing.
    assert catalog["workspaces"][4]["actions"] == []
    command_effects = {
        command["service"]: command["effect"] for command in catalog["commands"]
    }
    assert all(
        action["description"] == command_effects[action["command"]]
        for workspace in catalog["workspaces"]
        for action in workspace["actions"]
    )
    web_missing = {
        command["service"]
        for command in catalog["commands"]
        if "Web" not in command["adapters"]
    }
    assert web_missing == set()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda payload: payload["workspaces"].append(payload["workspaces"][0]),
            "Duplicate workspace",
        ),
        (lambda payload: payload["views"][0].update(route="missing"), "unknown route"),
        (
            lambda payload: payload["views"].append(
                {
                    "key": "unknown_projection",
                    "label": "Unknown projection",
                    "route": "orders",
                    "kind": "materialized_projection",
                    "projection": "not_registered",
                    "description": "Invalid fixture",
                }
            ),
            "unknown projection",
        ),
        (
            lambda payload: payload["actions"][0].update(command="missing"),
            "unknown command",
        ),
        (
            lambda payload: payload["actions"][0].update(confirmation="none"),
            "confirmation",
        ),
        (
            lambda payload: payload["workspaces"][0].update(complete_navigation="yes"),
            "complete_navigation",
        ),
    ],
)
def test_workspace_catalog_rejects_drift(change, message):
    payload = yaml.safe_load(catalogs.config_text("workspace_catalog.yaml"))
    change(payload)
    commands = load_application_catalog()["commands"]
    projections = load_application_catalog()["projections"]

    with pytest.raises((TypeError, ValueError), match=message):
        catalogs.validate_workspace_catalog(
            payload, commands=commands, projections=projections
        )


@pytest.mark.parametrize("effect", [None, "", "   "])
def test_workspace_catalog_rejects_actions_without_command_effect(effect):
    payload = yaml.safe_load(catalogs.config_text("workspace_catalog.yaml"))
    catalog = load_application_catalog()
    commands = [dict(command) for command in catalog["commands"]]
    observe_fact = next(
        command for command in commands if command["service"] == "observe_fact"
    )
    observe_fact["effect"] = effect

    with pytest.raises(ValueError, match="non-empty effect"):
        catalogs.validate_workspace_catalog(
            payload, commands=commands, projections=catalog["projections"]
        )


def test_only_the_reference_workspace_lists_its_whole_surface():
    """Progressive disclosure stays the rule; Data Management is the stated exception."""
    workspaces = load_application_catalog()["workspaces"]
    complete = {
        workspace["key"] for workspace in workspaces if workspace["complete_navigation"]
    }

    assert complete == {"data"}
    # Every workspace answers the question, so the browser never guesses a default.
    assert all("complete_navigation" in workspace for workspace in workspaces)


def test_event_catalog_contains_every_known_omission():
    event_types = {entry["type"] for entry in load_application_catalog()["events"]}

    assert {
        "fact.observed",
        "payment_term.updated",
        "price_list.updated",
        "party_group.updated",
    } <= event_types


def test_command_contracts_are_enriched_from_public_services():
    catalog = load_application_catalog()
    reserve = next(
        entry for entry in catalog["commands"] if entry["name"] == "Reserve stock"
    )

    assert reserve["service"] == "reserve"
    assert reserve["contracts"][0]["service"] == "reserve"
    assert all(item["description"] for item in reserve["contracts"][0]["inputs"])


def test_membership_commands_are_internal_and_require_confirmation():
    membership_services = {
        "create_invitation",
        "resend_invitation",
        "revoke_invitation",
        "remove_member",
    }
    commands = [
        command
        for command in load_application_catalog()["commands"]
        if command["service"] in membership_services
    ]

    assert {command["service"] for command in commands} == membership_services
    assert all(
        command["adapters"] == ["Web", "API", "MCP", "Chat"] for command in commands
    )
    assert all(command["confirmation"] == "required" for command in commands)


def test_event_drift_fails_with_missing_and_stale_names(monkeypatch):
    monkeypatch.setattr(
        catalogs,
        "_literal_business_events",
        lambda: {"implemented.only"},
    )

    with pytest.raises(
        ValueError,
        match=r"Business Event catalog drift: missing=\['implemented.only'\].*stale=",
    ):
        load_application_catalog()


def test_projection_drift_fails_with_missing_and_stale_names(monkeypatch):
    monkeypatch.setattr(
        catalogs.projection_service_module,
        "OPERATIONAL_PROJECTIONS",
        ("implemented_only",),
    )

    with pytest.raises(
        ValueError,
        match=r"Projection catalog drift: missing=\['implemented_only'\].*stale=",
    ):
        load_application_catalog()


def test_duplicate_category_names_are_rejected():
    with pytest.raises(ValueError, match="Duplicate test entries"):
        catalogs._unique([{"name": "same"}, {"name": "same"}], "name", "test entries")


def isolation_payload(*families, explicit_operations=None):
    return {
        "version": 1,
        "explicit_operations": explicit_operations or [],
        "families": list(families),
    }


def isolation_family(
    *operations,
    key="reads",
    classification="record_read",
    evidence_operations=None,
    evidence_id="test_contract.py::test_reads",
    **extra,
):
    return {
        "key": key,
        "description": f"Proof for {key}",
        "classification": classification,
        "operations": list(operations),
        "authority": "003/FR-012",
        "evidence": [
            {
                "id": evidence_id,
                "assertion": classification,
                "operations": list(
                    operations if evidence_operations is None else evidence_operations
                ),
            }
        ],
        **extra,
    }


def test_tenant_isolation_catalog_accepts_complete_contract():
    payload = isolation_payload(isolation_family("service:read"))

    catalog = validate_tenant_isolation_catalog(
        payload, discovered_operations=("service:read",)
    )

    assert catalog.version == 1
    assert catalog.discovered_operations == ("service:read",)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (isolation_payload(), "requires non-empty families"),
        (
            isolation_payload(
                isolation_family("service:read"),
                isolation_family(
                    "service:read", key="other", evidence_id="other::test"
                ),
            ),
            "Duplicate tenant isolation operation",
        ),
        (
            isolation_payload(
                isolation_family("service:read", classification="invalid")
            ),
            "Unknown tenant isolation classification",
        ),
        (
            isolation_payload(
                isolation_family("service:read", classification="global_admin")
            ),
            "missing reason",
        ),
        (
            isolation_payload(isolation_family("service:read", evidence_operations=[])),
            "requires covered operations",
        ),
    ],
)
def test_tenant_isolation_catalog_rejects_invalid_contracts(payload, message):
    with pytest.raises(ValueError, match=message):
        validate_tenant_isolation_catalog(
            payload, discovered_operations=("service:read",)
        )


def test_tenant_isolation_catalog_reports_missing_and_stale_operations():
    payload = isolation_payload(isolation_family("service:stale"))

    with pytest.raises(
        ValueError,
        match=r"missing=\['service:current'\], stale=\['service:stale'\]",
    ):
        validate_tenant_isolation_catalog(
            payload, discovered_operations=("service:current",)
        )


def test_tenant_isolation_catalog_rejects_unproven_operations():
    payload = isolation_payload(
        isolation_family(
            "service:first",
            "service:second",
            evidence_operations=["service:first"],
        )
    )

    with pytest.raises(ValueError, match=r"Unproven operations.*service:second"):
        validate_tenant_isolation_catalog(
            payload,
            discovered_operations=("service:first", "service:second"),
        )


def test_tenant_operation_discovery_includes_services_projections_and_tools():
    discovered = catalogs.discover_tenant_operations()

    assert "reality.services.core:commitments" in discovered
    assert {f"projection:{name}" for name in OPERATIONAL_PROJECTIONS} <= set(discovered)
    assert {f"tool:{name}" for name in catalogs.application_tool_module.TOOLS} <= set(
        discovered
    )
    assert tuple(sorted(discovered)) == discovered


def test_tenant_operation_discovery_detects_registry_drift():
    discovered = catalogs.discover_tenant_operations(
        modules={},
        projection_names=("new_projection",),
        tool_names=("new_tool",),
    )

    assert discovered == ("projection:new_projection", "tool:new_tool")


def test_production_tenant_isolation_catalog_is_complete_and_resolvable():
    catalog = catalogs.load_tenant_isolation_catalog()

    assert len(catalog.families) == 31
    assert len(catalog.discovered_operations) == 500
    assert (
        "reality.services.projections:refresh_projection"
        in catalog.discovered_operations
    )
    assert "reality.services.playground:start_run" in catalog.discovered_operations
    assert sum(len(family["operations"]) for family in catalog.families) == 500
    assert (
        "reality.services.core:validate_commitment_movement_quantity"
        in catalog.discovered_operations
    )


def test_membership_access_operations_are_explicitly_classified():
    catalog = catalogs.load_tenant_isolation_catalog()
    classified = {
        operation: family["classification"]
        for family in catalog.families
        for operation in family["operations"]
    }

    assert classified["reality.services.memberships:access_summary"] == "collection"
    assert (
        classified["reality.services.memberships:inspect_invitation"] == "record_read"
    )
    for operation in (
        "accept_invitation",
        "create_invitation",
        "remove_member",
        "resend_invitation",
        "revoke_invitation",
    ):
        assert classified[f"reality.services.memberships:{operation}"] == (
            "mutation_relationship"
        )


def test_order_tool_requires_the_stated_total():
    from reality.mcp.catalog import MCP_TOOL_CATALOG

    order_tool = next(
        tool for tool in MCP_TOOL_CATALOG if tool.name == "order_create_propose"
    )

    # An agent creating an order is reading a source; the total comes from
    # there rather than from the core adding the lines up.
    assert "gross_amount" in order_tool.input_schema["properties"]
    assert "gross_amount" in order_tool.input_schema["required"]


# --- An operation nobody declared (spec 094) -------------------------------

SURFACE_MODULES = ("web/api.py", "tools/application.py", "cli/app.py")


def _surface_source() -> str:
    root = pathlib.Path(catalogs.__file__).parent
    return "\n".join(
        (root / name).read_text(encoding="utf-8") for name in SURFACE_MODULES
    )


def _reachable_mutations() -> set[str]:
    """Mutating services a person or an agent can actually invoke.

    Two facts that are each already gated, intersected: what mutates comes from
    the tenant isolation catalog, which is complete by discovery, and what is
    reachable comes from the surface modules. No third list of what exists,
    because a hand-maintained list falling behind is the failure this gate
    exists to prevent.
    """
    isolation = yaml.safe_load(config_text(catalogs.TENANT_ISOLATION_CATALOG_FILE))
    mutating = {
        operation.split(":", 1)[1]
        for family in isolation["families"]
        if family["key"] == "mutations_and_relationships"
        for operation in family["operations"]
        if operation.startswith("reality.services.core:")
    }
    called = set(re.findall(r"\b([a-z_][a-z_0-9]{3,})\(", _surface_source()))
    return mutating & called


def _declared_services(catalog: dict) -> set[str]:
    declared = set()
    for command in catalog.get("commands", []):
        declared.add(command["service"])
        declared.update(command.get("related_services", []))
    return declared


def test_every_reachable_mutation_is_declared_or_explained():
    """The gate spec 091 said was missing.

    An operation could be built, made tenant-safe, wired to a surface and never
    declared — which is how booking an invoice reached no surface at all and
    five shipped exception classes could never fire.
    """
    commands = yaml.safe_load(config_text(catalogs.CATALOG_FILES["commands"]))
    declared = _declared_services(commands)
    not_commands = commands.get("reachable_mutations_that_are_not_commands", {})
    population = _reachable_mutations()

    undeclared = sorted(population - declared - set(not_commands))
    assert not undeclared, (
        "These mutating services are reachable from a surface and are neither "
        f"declared as commands nor explained: {undeclared}. Declare each one, or "
        "record it under reachable_mutations_that_are_not_commands with the "
        "reason it is not something an operator asks the business to do."
    )


def test_the_command_gate_fails_in_both_directions():
    """A stale exemption is how a list like this rots.

    The operation it named stops being reachable, the entry stays, and the next
    operation with that name inherits a silence nobody chose.
    """
    commands = yaml.safe_load(config_text(catalogs.CATALOG_FILES["commands"]))
    declared = _declared_services(commands)
    not_commands = commands.get("reachable_mutations_that_are_not_commands", {})
    population = _reachable_mutations()

    # Every reason is present and says something.
    empty = sorted(
        name for name, reason in not_commands.items() if not str(reason).strip()
    )
    assert not empty, f"These exemptions carry no reason: {empty}"

    # Nothing is both a command and not a command.
    both = sorted(set(not_commands) & declared)
    assert not both, f"These are declared as commands and also exempt: {both}"

    # No exemption outlives the operation it excused.
    stale = sorted(set(not_commands) - population)
    assert not stale, (
        f"These exemptions name services that are no longer reachable mutations: {stale}. "
        "Remove them; a stale entry hides the next real one."
    )

    # The positive control: the population is not empty, so the three checks
    # above are answering a real question rather than an absent one.
    assert len(population) > 50


def test_the_eight_operations_the_gate_found_are_declared():
    """What the gate found the first time it ran.

    Releasing a reservation is the one worth naming: it has had the
    `reservation_release` agent tool since reservations existed and has never
    been in the catalog. An agent could do it and the catalog said the product
    could not.
    """
    commands = yaml.safe_load(config_text(catalogs.CATALOG_FILES["commands"]))
    declared = _declared_services(commands)

    assert "release_reservation" in declared
    assert "update_party_group" in declared
    assert {
        "create_items",
        "create_parties",
        "create_locations",
        "update_items",
        "update_parties",
        "update_locations",
    } <= declared


def test_runtime_catalog_reuses_successful_snapshot_without_shared_mutability(
    monkeypatch,
):
    calls = []

    def build():
        calls.append(True)
        return {"projections": [{"name": "Inventory"}]}

    catalogs.clear_runtime_application_catalog()
    monkeypatch.setattr(catalogs, "load_application_catalog", build)
    monkeypatch.setattr(
        "reality.tool_catalog.build_tool_catalog", lambda _: {"entries": []}
    )
    try:
        first = catalogs.runtime_application_catalog()
        first["projections"][0]["name"] = "Corrupted"
        assert (
            catalogs.runtime_application_catalog()["projections"][0]["name"]
            == "Inventory"
        )
        assert len(calls) == 1
    finally:
        catalogs.clear_runtime_application_catalog()


def test_runtime_catalog_retries_failed_validation(monkeypatch):
    calls = []

    def build():
        calls.append(True)
        if len(calls) == 1:
            raise ValueError("Catalog drift")
        return {"version": 1}

    catalogs.clear_runtime_application_catalog()
    monkeypatch.setattr(catalogs, "load_application_catalog", build)
    monkeypatch.setattr(
        "reality.tool_catalog.build_tool_catalog", lambda _: {"entries": []}
    )
    try:
        with pytest.raises(ValueError, match="Catalog drift"):
            catalogs.runtime_application_catalog()
        result = catalogs.runtime_application_catalog()
        vocabulary = result.pop("search_vocabulary")
        assert vocabulary and all(
            "key" in row and "labels" in row for row in vocabulary
        )
        assert result == {
            "version": 1,
            "tool_catalog": {"entries": []},
        }
        assert len(calls) == 2
    finally:
        catalogs.clear_runtime_application_catalog()
