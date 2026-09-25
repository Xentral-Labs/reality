"""Spec 270: an agent can ask what Reality can do, and what it may use of it."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from reality.catalogs import (
    CATALOG_READ_TOOLS,
    runtime_application_catalog,
    runtime_tool_catalog,
)
from reality.mcp.catalog import (
    MCP_TOOL_CATALOG,
    MCP_TOOL_NAMES,
    MCP_TOOL_REGISTRY,
    dispatch_mcp_tool,
    model_tool_schemas,
)
from reality.mcp.principal import MCPPrincipal, mcp_principal_context
from reality.services.capability_catalog import topic_capabilities, topic_index
from reality.services.core import InvalidOperation
from reality.services.mcp_authorization import approve_interaction, create_interaction
from reality.tools.application import TOOLS, run_read_tool

DUNNING_TOOLS = {
    "finance_dunning_context",
    "finance_dunning_notices",
    "finance_dunning_notice",
    "finance_dunning_record_propose",
    "finance_dunning_reverse_propose",
}


def _manual(tenant_id: str, tools: set[str]) -> MCPPrincipal:
    return MCPPrincipal(
        "manual",
        "manual_1",
        None,
        None,
        tenant_id,
        "manual_1",
        frozenset({"reality:read", *[f"reality:tool:{name}" for name in tools]}),
        frozenset(tools),
    )


def _interactive_grant(session, business, owner, *, tools, scopes):
    """Approve a real grant, so the row the service reads is the row consent wrote."""
    interaction = create_interaction(
        session,
        client_id="https://client.example/metadata.json",
        client_metadata={"client_name": "Example client"},
        redirect_uri="https://client.example/callback",
        resource="https://mcp.example/",
        requested_scopes=list(scopes),
        code_challenge="c" * 43,
        state="opaque",
    )
    grant, _ = approve_interaction(
        session,
        interaction.id,
        user_id=owner.id,
        tenant_id=business.tenant.id,
        allowed_tools=list(tools),
    )
    return grant


def _principal_for(grant, *, allowed: set[str]) -> MCPPrincipal:
    """The principal the verifier builds: already intersected with the grant scopes."""
    return MCPPrincipal(
        "interactive",
        "credential_1",
        grant.id,
        grant.user_id,
        grant.tenant_id,
        grant.client_id,
        frozenset(grant.scopes),
        frozenset(allowed),
    )


# --- Coverage and catalog access (T005, T006) --------------------------------


def test_every_mcp_tool_is_reachable_through_exactly_the_known_topics(
    session, business
):
    index = topic_index(session, business.tenant.id)
    keys = [row["topic"] for row in index["topics"]]
    configured = {row["key"] for row in runtime_tool_catalog()["topics"]}

    assert set(keys) <= configured
    assert len(keys) == len(set(keys)) == 11

    reached: set[str] = set()
    for key in keys:
        for capability in topic_capabilities(session, business.tenant.id, key)[
            "capabilities"
        ]:
            reached.update(tool["name"] for tool in capability["tools"])

    assert reached == MCP_TOOL_NAMES

    # Eleven tools are bound to more than one capability entry. A topic's tool count
    # counts each once, so coverage cannot be inflated by a duplicate binding.
    for row in index["topics"]:
        capabilities = topic_capabilities(session, business.tenant.id, row["topic"])[
            "capabilities"
        ]
        names = [
            tool["name"] for capability in capabilities for tool in capability["tools"]
        ]
        assert row["tools"] == len(set(names))
        assert row["capabilities"] == len(capabilities)


def test_narrow_catalog_accessor_is_isolated_and_reads_one_section():
    first = runtime_tool_catalog()
    first["entries"].clear()
    assert runtime_tool_catalog()["entries"], "the accessor must return a copy"

    assert set(runtime_tool_catalog()) == {
        "version",
        "topics",
        "entries",
        "mcp_tools",
    }
    # Positive control: the full accessor still carries every section.
    assert len(runtime_application_catalog()) > 10


# --- User story 1: an entry point (T009, T010, T011, T012, T013) -------------


def test_topic_index_names_every_area_with_its_counts(session, business):
    index = topic_index(session, business.tenant.id)

    assert index["credential"] == {"kind": "none", "limits_tools": False}
    payments = next(row for row in index["topics"] if row["topic"] == "payments")
    assert payments["label"] == "Invoices and payments"
    assert payments["capabilities"] > 0 and payments["tools"] > 0
    assert len(json.dumps(index)) < 2_000


def test_one_topic_answers_its_capabilities_and_refuses_an_unknown_key(
    session, business
):
    answer = topic_capabilities(session, business.tenant.id, "payments")

    assert answer["label"] == "Invoices and payments"
    capability = answer["capabilities"][0]
    assert set(capability) == {
        "capability",
        "label_de",
        "purpose",
        "description",
        "tools",
    }
    assert capability["purpose"] in {"read", "understand", "change"}
    assert set(capability["tools"][0]) == {"name", "access", "callable", "reason"}
    assert len(json.dumps(answer)) < 16_000

    with pytest.raises(InvalidOperation) as refused:
        topic_capabilities(session, business.tenant.id, "mahnwesen")
    assert "Unknown capability topic" in str(refused.value)
    assert "payments" in str(refused.value)

    # Positive control: a valid key beside the refused one still answers.
    assert topic_capabilities(session, business.tenant.id, "stock")["capabilities"]


def test_two_calls_reach_the_dunning_tools_through_the_mcp_runtime(session, business):
    """The reported regression: an agent concluded these tools did not exist."""
    principal = _manual(business.tenant.id, {"capability_catalog"})

    index = dispatch_mcp_tool(session, principal, "capability_catalog", {})
    topic = next(
        row["topic"]
        for row in index["topics"]
        if row["label"] == "Invoices and payments"
    )
    answer = dispatch_mcp_tool(
        session, principal, "capability_catalog", {"topic": topic}
    )

    reached = {
        tool["name"]
        for capability in answer["capabilities"]
        for tool in capability["tools"]
    }
    assert DUNNING_TOOLS <= reached


def test_server_instructions_name_the_entry_point():
    from reality.mcp.server import build_server

    assert "capability_catalog" in build_server().instructions


def test_the_tool_is_a_read_and_reveals_no_tenant_business_record(session, business):
    definition = MCP_TOOL_REGISTRY["capability_catalog"]
    assert definition.access == "read"
    assert not definition.mutating
    assert not TOOLS["capability_catalog"].mutating
    assert definition.name in CATALOG_READ_TOOLS

    answer = json.dumps(
        [
            topic_index(session, business.tenant.id),
            topic_capabilities(session, business.tenant.id, "stock"),
        ]
    )
    for opaque_id in (business.item.id, business.customer.id, business.location.id):
        assert opaque_id not in answer

    # Positive control: a business read of the same company does carry those ids.
    records = json.dumps(
        run_read_tool(
            session,
            business.tenant.id,
            "business_discover",
            {"family": "item", "response_format": "page"},
        )
    )
    assert business.item.id in records


# --- User story 2: granted, or simply absent (T017, T018, T019, T020) --------


def _state_of(answer, name):
    for capability in answer["capabilities"]:
        for tool in capability["tools"]:
            if tool["name"] == name:
                return tool["callable"], tool["reason"]
    raise AssertionError(f"{name} is not listed")


def test_no_credential_reports_no_limit(session, business):
    answer = topic_capabilities(session, business.tenant.id, "payments")

    assert answer["credential"] == {"kind": "none", "limits_tools": False}
    assert all(
        tool["callable"] and tool["reason"] is None
        for capability in answer["capabilities"]
        for tool in capability["tools"]
    )


def test_a_manual_token_reports_what_its_tool_list_omits(session, business):
    principal = _manual(business.tenant.id, {"finance_dunning_notices"})

    with mcp_principal_context(principal):
        answer = topic_capabilities(session, business.tenant.id, "payments")

    assert answer["credential"] == {"kind": "manual", "limits_tools": True}
    assert _state_of(answer, "finance_dunning_notices") == (True, None)
    assert _state_of(answer, "finance_dunning_context") == (False, "not_in_token")


def test_an_interactive_grant_separates_an_omission_from_an_excluded_scope(
    session, business, scheduled_owner
):
    """A read-only client: the propose tools were never offered to it at all.

    `approve_interaction` refuses tools outside the requested scopes, so an access
    class the client never asked for is absent from the grant for that reason. The
    two refusals are actionable in different ways: ask for more tools, or ask for a
    broader scope.
    """
    grant = _interactive_grant(
        session,
        business,
        scheduled_owner,
        tools=["finance_dunning_notices"],
        scopes=["reality:read"],
    )
    principal = _principal_for(grant, allowed={"finance_dunning_notices"})

    with mcp_principal_context(principal):
        answer = topic_capabilities(session, business.tenant.id, "payments")

    assert answer["credential"] == {"kind": "interactive", "limits_tools": True}
    assert _state_of(answer, "finance_dunning_notices") == (True, None)
    assert _state_of(answer, "finance_dunning_context") == (False, "not_in_grant")
    assert _state_of(answer, "finance_dunning_record_propose") == (
        False,
        "scope_excluded",
    )


def test_scope_exclusion_cannot_arise_for_a_manual_token(
    session, business, scheduled_owner
):
    """Manual credentials model no access-class scopes, so only one reason applies."""
    manual = _manual(business.tenant.id, {"finance_dunning_notices"})

    with mcp_principal_context(manual):
        answer = topic_capabilities(session, business.tenant.id, "payments")
    reasons = {
        tool["reason"]
        for capability in answer["capabilities"]
        for tool in capability["tools"]
    }
    assert "scope_excluded" not in reasons
    assert "not_in_token" in reasons

    # Positive control: the same tool under a read-only grant does produce it.
    grant = _interactive_grant(
        session,
        business,
        scheduled_owner,
        tools=["finance_dunning_notices"],
        scopes=["reality:read"],
    )
    with mcp_principal_context(
        _principal_for(grant, allowed={"finance_dunning_notices"})
    ):
        interactive = topic_capabilities(session, business.tenant.id, "payments")
    assert _state_of(interactive, "finance_dunning_record_propose") == (
        False,
        "scope_excluded",
    )


def test_callable_means_the_dispatch_boundary_does_not_refuse_it(
    session, business, scheduled_owner, monkeypatch
):
    """Execute the permission path rather than compare two copies of one rule.

    Every handler in the topic is replaced by a no-op, so the dispatch runs its real
    checks and no business effect can follow.
    """
    grant = _interactive_grant(
        session,
        business,
        scheduled_owner,
        tools=["finance_dunning_notices", "finance_dunning_record_propose"],
        scopes=["reality:read", "reality:propose"],
    )
    credentials = [
        _manual(business.tenant.id, {"finance_dunning_notices", "capability_catalog"}),
        _principal_for(
            grant,
            allowed={"finance_dunning_notices", "finance_dunning_record_propose"},
        ),
    ]
    for definition in MCP_TOOL_CATALOG:
        monkeypatch.setitem(
            MCP_TOOL_REGISTRY,
            definition.name,
            replace(definition, handler=lambda *_args, **_kwargs: {"ok": True}),
        )

    for principal in credentials:
        with mcp_principal_context(principal):
            answer = topic_capabilities(session, business.tenant.id, "payments")
        refused = []
        for capability in answer["capabilities"]:
            for tool in capability["tools"]:
                try:
                    dispatch_mcp_tool(session, principal, tool["name"], {})
                except PermissionError:
                    refused.append(tool["name"])
                    assert not tool["callable"], (
                        f"{tool['name']} was reported callable and then refused"
                    )
                else:
                    assert tool["callable"], (
                        f"{tool['name']} was reported not callable and then allowed"
                    )
        assert refused, "the test credential must not reach every tool"


def test_a_grant_of_another_company_is_never_read(session, business, scheduled_owner):
    grant = _interactive_grant(
        session,
        business,
        scheduled_owner,
        tools=["finance_dunning_notices"],
        scopes=["reality:read"],
    )
    foreign = replace(
        _principal_for(grant, allowed={"finance_dunning_notices"}),
        tenant_id="tenant_elsewhere",
    )

    with mcp_principal_context(foreign):
        answer = topic_capabilities(session, "tenant_elsewhere", "payments")

    # The grant row does not match that tenant, so the answer falls back to the
    # principal's own reach and discloses nothing about the other company's grant.
    assert _state_of(answer, "finance_dunning_notices") == (True, None)
    assert _state_of(answer, "finance_dunning_context") == (False, "not_in_grant")

    # Positive control: within its own company the grant row is read, and it can
    # say the one thing the principal alone never could.
    with mcp_principal_context(
        _principal_for(grant, allowed={"finance_dunning_notices"})
    ):
        own = topic_capabilities(session, business.tenant.id, "payments")
    assert _state_of(own, "finance_dunning_record_propose") == (
        False,
        "scope_excluded",
    )


# --- User story 3: the business name (T023) ----------------------------------


def test_a_capability_carries_its_german_label_or_falls_back_to_english(
    session, business
):
    answer = topic_capabilities(session, business.tenant.id, "payments")
    by_tool = {
        tool["name"]: capability
        for capability in answer["capabilities"]
        for tool in capability["tools"]
    }

    recording = by_tool["finance_dunning_record_propose"]
    assert recording["label_de"] == "Mahnung erfassen"
    assert by_tool["finance_dunning_reverse_propose"]["label_de"] == (
        "Mahnung stornieren"
    )

    without = [
        capability
        for capability in answer["capabilities"]
        if capability["label_de"] is None
    ]
    assert without, "the fallback must be exercised by a real capability"
    # Positive control: every capability carries an English name either way.
    assert all(capability["capability"] for capability in answer["capabilities"])


# --- Surfaces that inherit the tool (T031) -----------------------------------


def test_chat_inherits_the_tool_and_reports_no_credential_limit(session, business):
    assert any(
        schema["function"]["name"] == "capability_catalog"
        for schema in model_tool_schemas()
    )

    # Chat dispatches without an MCP credential, so nothing limits the answer.
    assert topic_index(session, business.tenant.id)["credential"] == {
        "kind": "none",
        "limits_tools": False,
    }

    # Positive control: under a manual token the same call does report limits.
    with mcp_principal_context(_manual(business.tenant.id, {"capability_catalog"})):
        assert topic_index(session, business.tenant.id)["credential"] == {
            "kind": "manual",
            "limits_tools": True,
        }
