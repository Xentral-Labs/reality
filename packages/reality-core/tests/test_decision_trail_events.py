"""Spec 263 US2: every event a confirmed proposal writes references that proposal."""

from __future__ import annotations

import ast
import inspect

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent, ChangeProposal
from reality.services.core import (
    InvalidOperation,
    create_price_list,
    create_tenant,
    emit_business_event,
    executing_proposal,
)
from reality.tools import application as application_module
from reality.tools.application import (
    TOOLS,
    Tool,
    approve_and_execute_proposal,
    create_change_proposal,
)


def _events(session, tenant_id: str, since: int = 0) -> list[BusinessEvent]:
    return list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.sequence > since,
            )
            .order_by(BusinessEvent.sequence)
        )
    )


def _last_sequence(session, tenant_id: str) -> int:
    events = _events(session, tenant_id)
    return events[-1].sequence if events else 0


def _confirm(session, tenant_id: str, tool: str, arguments: dict) -> tuple:
    proposal = create_change_proposal(session, tenant_id, tool, arguments)
    since = _last_sequence(session, tenant_id)
    approve_and_execute_proposal(session, tenant_id, proposal.id, confirmed=True)
    return proposal, _events(session, tenant_id, since)


# --- The scope itself (FR-005) ---------------------------------------------------


def _stored(session, tenant_id: str, *ids: str) -> None:
    for proposal_id in ids:
        session.add(
            ChangeProposal(
                id=proposal_id,
                tenant_id=tenant_id,
                type="tool:probe_record",
                status="executing",
            )
        )
    session.flush()


def test_an_event_inside_the_scope_references_the_executing_proposal(session):
    tenant = create_tenant(session, "Scoped company")
    _stored(session, tenant.id, "act_scoped")

    with executing_proposal(tenant.id, "act_scoped"):
        event = emit_business_event(
            session, tenant.id, "probe.recorded", "probe", "p1", {}
        )

    assert event.action_id == "act_scoped"


def test_an_explicit_reference_is_kept_whatever_the_scope_says(session):
    """Costing and commercial matching thread their own action; nothing overrides it."""
    tenant = create_tenant(session, "Explicit company")
    _stored(session, tenant.id, "act_scoped", "act_own")

    with executing_proposal(tenant.id, "act_scoped"):
        same = emit_business_event(
            session,
            tenant.id,
            "probe.recorded",
            "probe",
            "p1",
            {},
            action_id="act_scoped",
        )
        other = emit_business_event(
            session, tenant.id, "probe.recorded", "probe", "p2", {}, action_id="act_own"
        )

    assert same.action_id == "act_scoped"
    assert other.action_id == "act_own"


def test_another_companys_scope_is_ignored(session):
    tenant = create_tenant(session, "Writing company")
    other = create_tenant(session, "Executing company")

    with executing_proposal(other.id, "act_elsewhere"):
        event = emit_business_event(
            session, tenant.id, "probe.recorded", "probe", "p1", {}
        )

    assert event.action_id is None


def test_the_scope_ends_with_its_block_even_after_a_failure(session):
    tenant = create_tenant(session, "Failing company")

    with (
        pytest.raises(InvalidOperation),
        executing_proposal(tenant.id, "act_failed"),
    ):
        raise InvalidOperation("handler refused")
    event = emit_business_event(session, tenant.id, "probe.recorded", "probe", "p1", {})

    assert event.action_id is None


def test_without_a_scope_an_event_references_nothing(session):
    """Positive control: seeding and source interpretation carry no decision."""
    tenant = create_tenant(session, "Unscoped company")

    event = emit_business_event(session, tenant.id, "probe.recorded", "probe", "p1", {})

    assert event.action_id is None


# --- The families that were never linked (FR-005, SC-002) ---------------------


def test_a_confirmed_payment_term_references_its_decision(session, business):
    proposal, events = _confirm(
        session,
        business.tenant.id,
        "payment_term_create",
        {"code": "NET14", "name": "Net 14", "due_days": 14},
    )

    assert [event.event_type for event in events] == ["payment_term.created"]
    assert {event.action_id for event in events} == {proposal.id}


def test_a_confirmed_price_list_references_its_decision(session, business):
    proposal, events = _confirm(
        session,
        business.tenant.id,
        "price_list_create",
        {"code": "VK", "name": "Sales", "direction": "sales", "currency": "EUR"},
    )

    assert "price_list.created" in {event.event_type for event in events}
    assert {event.action_id for event in events} == {proposal.id}


def test_a_confirmed_price_tier_and_assignment_reference_their_decisions(
    session, business
):
    price_list = create_price_list(
        session, business.tenant.id, "VK", "Sales", "sales", "EUR"
    )
    tier, tier_events = _confirm(
        session,
        business.tenant.id,
        "price_tier_create",
        {
            "price_list_id": price_list.id,
            "item_id": business.item.id,
            "min_quantity": "1",
            "unit_price": "9.90",
            "unit": "pcs",
        },
    )
    assignment, assignment_events = _confirm(
        session,
        business.tenant.id,
        "party_price_list_assign",
        {"party_id": business.customer.id, "price_list_id": price_list.id},
    )

    assert tier_events and {event.action_id for event in tier_events} == {tier.id}
    assert assignment_events and {event.action_id for event in assignment_events} == {
        assignment.id
    }


# --- The catalog guard (FR-006) -------------------------------------------------


def _emitting_handler(event_type: str):
    def handler(session, tenant_id, arguments):
        # Deliberately passes no action_id, as the unlinked handlers did.
        event = emit_business_event(session, tenant_id, event_type, "probe", "p1", {})
        return {"event_id": event.id}

    return handler


def test_a_new_tool_on_the_generic_path_is_linked_without_being_listed(
    session, business, monkeypatch
):
    monkeypatch.setitem(
        TOOLS,
        "probe_record",
        Tool("probe_record", "Probe.", True, _emitting_handler("probe.recorded")),
    )
    proposal = ChangeProposal(
        id="act_probe",
        tenant_id=business.tenant.id,
        type="tool:probe_record",
        status="proposed",
        input="{}",
        output="{}",
    )
    session.add(proposal)
    session.commit()
    since = _last_sequence(session, business.tenant.id)

    approve_and_execute_proposal(session, business.tenant.id, proposal.id)

    events = _events(session, business.tenant.id, since)
    assert [event.action_id for event in events] == ["act_probe"]


def test_the_master_data_path_is_linked(session, business, monkeypatch):
    original = TOOLS["location_create"]
    monkeypatch.setitem(
        TOOLS,
        "location_create",
        Tool(
            "location_create",
            original.description,
            True,
            _emitting_handler("location.created"),
        ),
    )
    proposal = create_change_proposal(
        session, business.tenant.id, "location_create", {"name": "Probe store"}
    )
    since = _last_sequence(session, business.tenant.id)

    approve_and_execute_proposal(session, business.tenant.id, proposal.id)

    events = _events(session, business.tenant.id, since)
    assert events and {event.action_id for event in events} == {proposal.id}


def test_the_finance_path_is_linked(session, business, monkeypatch):
    from reality.tools.finance import FINANCE_COMMANDS

    name = min(FINANCE_COMMANDS - {"cost.change"})

    def execute(session, tenant_id, _name, _arguments, *, action_id, actor_id=None):
        return _emitting_handler("probe.recorded")(session, tenant_id, {})

    monkeypatch.setattr(application_module, "execute_finance_command", execute)
    monkeypatch.setitem(TOOLS, name, Tool(name, "Probe.", True, lambda *args: {}))
    proposal = ChangeProposal(
        id="act_finance_probe",
        tenant_id=business.tenant.id,
        type=f"tool:{name}",
        status="proposed",
        input="{}",
        output="{}",
    )
    session.add(proposal)
    session.commit()
    since = _last_sequence(session, business.tenant.id)

    approve_and_execute_proposal(session, business.tenant.id, proposal.id)

    events = _events(session, business.tenant.id, since)
    assert [event.action_id for event in events] == ["act_finance_probe"]


EXECUTION_CALLS = {
    "handler",
    "execute_finance_command",
    "execute_request",
    "execute_change",
}


def _called_name(call: ast.Call) -> str | None:
    function = call.func
    if isinstance(function, ast.Attribute):
        return function.attr
    if isinstance(function, ast.Name):
        return function.id
    return None


def _module_functions() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(inspect.getsource(application_module))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_every_way_a_proposal_executes_runs_inside_the_scope():
    """A future branch that calls a handler outside the scope fails here."""
    function = _module_functions()["approve_and_execute_proposal"]
    scoped: set[int] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.With) and any(
            isinstance(item.context_expr, ast.Call)
            and _called_name(item.context_expr) == "executing_proposal"
            for item in node.items
        ):
            scoped.update(id(child) for child in ast.walk(node))
    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and _called_name(node) in EXECUTION_CALLS
    ]

    assert {_called_name(call) for call in calls} == EXECUTION_CALLS
    assert [ast.unparse(call) for call in calls if id(call) not in scoped] == []


def test_no_other_function_executes_a_mutating_handler():
    """The only other handler call is the read path, which refuses mutating tools."""
    assert any(tool.mutating for tool in TOOLS.values())
    callers = sorted(
        name
        for name, function in _module_functions().items()
        if any(
            isinstance(node, ast.Call) and _called_name(node) == "handler"
            for node in ast.walk(function)
        )
    )

    assert callers == ["approve_and_execute_proposal", "run_read_tool"]
    with pytest.raises(InvalidOperation, match="confirmed proposal"):
        application_module.run_read_tool(None, "ten_any", "payment_term_create")
