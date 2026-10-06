"""Source-stated dispatch inputs must have exact, closed business meaning."""

from datetime import date

import pytest
from pydantic import ValidationError

from reality.domain.shipping_performance import PlanInput


def test_reviewed_plan_is_lossless_replay_safe_and_preserves_versions(
    session, business, scheduled_owner
):
    import json

    from sqlalchemy import select

    from reality.db.core import ShippingPlanStatement, SourceRecord
    from reality.services import core
    from reality.services.memberships import Principal
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    _, _, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-378-PLAN",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )
    source, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity_confirmation",
        "source-v",
        {
            "unit": "site-cohort order completion",
            "completion_slots": 2,
            "work_mix": [commitments[0].id],
        },
    )
    original = payload()
    original["business_time_zone"] = "UTC"
    original["dispatch_location_id"] = business.location.id
    original["requirements"][0]["commitment_id"] = commitments[0].id
    original["capacity_windows"][0]["confirmation_source_record_id"] = source.id
    proposal = create_change_proposal(
        session, business.tenant.id, "shipping_plan_state", {"plan": original}
    )
    assert session.scalar(select(ShippingPlanStatement.id)) is None
    receipt = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(scheduled_owner.id),
        confirmed=True,
    )
    statement = session.scalar(select(ShippingPlanStatement))
    held = session.scalar(
        select(SourceRecord).where(SourceRecord.id == statement.source_record_id)
    )
    assert json.loads(held.payload)["plan"] == original
    receipt_again = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(scheduled_owner.id),
        confirmed=True,
    )
    assert receipt_again.id == receipt.id
    assert len(session.scalars(select(ShippingPlanStatement)).all()) == 1
    changed = json.loads(json.dumps(original))
    changed["capacity_windows"][0]["confirmation_state"] = "requested"
    revision = create_change_proposal(
        session,
        business.tenant.id,
        "shipping_plan_state",
        {
            "plan": changed,
            "plan_id": held.external_id,
            "prior_source_record_id": held.id,
        },
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        revision.id,
        confirming_principal=Principal(scheduled_owner.id),
        confirmed=True,
    )
    assert len(session.scalars(select(ShippingPlanStatement)).all()) == 2
    assert (
        json.loads(session.get(SourceRecord, (business.tenant.id, held.id)).payload)[
            "plan"
        ]
        == original
    )


def test_service_review_refuses_foreign_business_objects_before_writing(
    session, business
):
    from reality.services import core
    from reality.services.shipping_plans import review_plan

    value = payload()
    value["business_time_zone"] = "UTC"
    with pytest.raises(core.NotFound):
        review_plan(session, business.tenant.id, {"plan": value})


def staged_plan(session, business):
    from reality.services import core
    from reality.tools.application import create_change_proposal

    _, _, _, commitments = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-378",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )
    value = payload()
    value.update(
        business_time_zone="UTC",
        dispatch_location_id=business.location.id,
        capacity_windows=[],
    )
    value["requirements"][0]["commitment_id"] = commitments[0].id
    return (
        create_change_proposal(
            session, business.tenant.id, "shipping_plan_state", {"plan": value}
        ),
        value,
        commitments[0],
    )


def accept(session, business, owner, proposal):
    from reality.services.memberships import Principal
    from reality.tools.application import approve_and_execute_proposal

    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(owner.id),
        confirmed=True,
    )


def test_one_commitment_cannot_be_planned_at_two_current_sites(
    session, business, scheduled_owner
):
    from copy import deepcopy

    from reality.services import core
    from reality.services.shipping_plans import review_plan

    proposal, value, _ = staged_plan(session, business)
    accept(session, business, scheduled_owner, proposal)
    other = deepcopy(value)
    other["dispatch_location_id"] = core.create_location(
        session, business.tenant.id, "Second site"
    ).id
    with pytest.raises(core.InvalidOperation) as refusal:
        review_plan(session, business.tenant.id, {"plan": other})
    assert refusal.value.code == "shipping_plan_requirement_conflict"


def test_stale_quantity_cannot_be_accepted(session, business, scheduled_owner):
    from sqlalchemy import select

    from reality.db.core import ShippingPlanStatement
    from reality.services import core

    proposal, _, commitment = staged_plan(session, business)
    core.revise_commitment(session, business.tenant.id, commitment.id, quantity="3")
    with pytest.raises(core.InvalidOperation) as refusal:
        accept(session, business, scheduled_owner, proposal)
    assert refusal.value.code == "shipping_plan_quantity_changed"
    assert session.scalar(select(ShippingPlanStatement.id)) is None


def test_new_quantity_statement_requires_fresh_review_even_when_amount_returns(
    session, business, scheduled_owner
):
    from reality.services import core
    from reality.services.shipping_plans import review_plan

    proposal, value, commitment = staged_plan(session, business)
    core.revise_commitment(
        session,
        business.tenant.id,
        commitment.id,
        quantity="3",
        stated_at="2026-10-06T12:00:00Z",
    )
    latest = core.revise_commitment(
        session,
        business.tenant.id,
        commitment.id,
        quantity="2",
        stated_at="2026-10-06T12:01:00Z",
    )
    normalized, _ = review_plan(session, business.tenant.id, {"plan": value})
    assert (
        normalized["reviewed"]["commitments"][commitment.id]["quantity_revision_id"]
        == latest.id
    )
    with pytest.raises(core.InvalidOperation) as refused:
        accept(session, business, scheduled_owner, proposal)
    assert refused.value.code == "shipping_plan_basis_changed"


def test_withdrawal_preserves_history_and_releases_requirement_scope(
    session, business, scheduled_owner
):
    import json

    from reality.services.shipping_plans import current_statements, review_plan
    from reality.tools.application import create_change_proposal

    proposal, value, _ = staged_plan(session, business)
    accept(session, business, scheduled_owner, proposal)
    statement, source = current_statements(session, business.tenant.id)[0]
    withdrawal = value | {
        "statement_kind": "withdrawal",
        "requirements": [],
        "capacity_windows": [],
    }
    proposed = create_change_proposal(
        session,
        business.tenant.id,
        "shipping_plan_state",
        {
            "plan": withdrawal,
            "plan_id": source.external_id,
            "prior_source_record_id": source.id,
        },
    )
    accept(session, business, scheduled_owner, proposed)
    current, current_source = current_statements(session, business.tenant.id)[0]
    assert current.statement_kind == "withdrawal"
    assert current_source.version == source.version + 1
    assert json.loads(source.payload)["plan"] == value
    assert current.id != statement.id
    review_plan(session, business.tenant.id, {"plan": value})


def test_shipping_input_requires_owner_even_in_trusted_local_mode(session, business):
    from reality.services import core
    from reality.tools.application import approve_and_execute_proposal

    proposal, _, _ = staged_plan(session, business)
    with pytest.raises(core.InvalidOperation):
        approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirmed=True
        )


def test_inactive_owner_cannot_accept_previously_reviewed_shipping_plan(
    session, business, scheduled_owner
):
    from reality.services import core

    proposal, _, _ = staged_plan(session, business)
    scheduled_owner.status = "inactive"
    session.flush()
    with pytest.raises(core.NotFound):
        accept(session, business, scheduled_owner, proposal)


def test_all_shipping_plan_boundaries_refuse_foreign_references_without_writes(
    session, business, scheduled_owner
):
    import json

    from sqlalchemy import select

    from reality.db.core import BusinessEvent, ShippingPlanStatement
    from reality.services import core
    from reality.services.case_action_guards import execution_context
    from reality.services.memberships import Principal
    from reality.services.shipping_plans import (
        current_statements,
        review_plan,
        source_basis,
    )
    from reality.tools.application import TOOLS, create_change_proposal

    foreign = core.create_tenant(session, "Foreign plan")
    foreign_location = core.create_location(session, foreign.id, "Foreign site")
    source, _, _ = core.store_source_record(
        session, foreign.id, "carrier", "confirmation", "foreign", {"slots": 1}
    )
    proposal, value, _ = staged_plan(session, business)
    before = session.scalars(select(BusinessEvent.id)).all()
    for foreign_id in (source.id, "src_unknown"):
        with pytest.raises(core.NotFound) as refused:
            source_basis(session, business.tenant.id, {foreign_id})
        assert refused.value.code == "shipping_plan_reference_unavailable"
    for location_id in (foreign_location.id, "loc_unknown"):
        with pytest.raises(core.NotFound):
            review_plan(
                session,
                business.tenant.id,
                {"plan": value | {"dispatch_location_id": location_id}},
            )
    foreign_confirmation = json.loads(json.dumps(value))
    foreign_confirmation["capacity_windows"] = payload()["capacity_windows"]
    foreign_confirmation["capacity_windows"][0]["confirmation_source_record_id"] = (
        source.id
    )
    with pytest.raises(core.NotFound):
        create_change_proposal(
            session,
            business.tenant.id,
            "shipping_plan_state",
            {"plan": foreign_confirmation},
        )
    assert current_statements(session, foreign.id) == []
    with (
        execution_context(
            session,
            business.tenant.id,
            automatic=False,
            principal=Principal(scheduled_owner.id),
        ),
        pytest.raises(core.NotFound),
    ):
        TOOLS["shipping_plan_state"].handler(
            session, business.tenant.id, {"_action_id": "foreign_proposal"}
        )
    assert session.scalar(select(ShippingPlanStatement.id)) is None
    assert session.scalars(select(BusinessEvent.id)).all() == before
    assert proposal.status == "proposed"


def test_manual_agent_may_propose_but_cannot_confirm_its_own_shipping_plan(
    session, business
):
    from sqlalchemy import select

    from reality.db.core import ShippingPlanStatement
    from reality.mcp.catalog import dispatch_tool
    from reality.mcp.principal import MCPPrincipal
    from reality.services import core

    _, value, _ = staged_plan(session, business)
    authority = MCPPrincipal(
        "manual",
        "agent_credential",
        None,
        None,
        business.tenant.id,
        "manual",
        frozenset(),
        frozenset({"*"}),
    )
    drafted = dispatch_tool(
        session,
        business.tenant.id,
        "shipping_plan_propose",
        {"plan": value},
        principal=authority,
    )
    assert drafted["requires_confirmation"] is True
    with pytest.raises(core.InvalidOperation):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": drafted["proposal_id"], "approved": True},
            principal=authority,
        )
    assert session.scalar(select(ShippingPlanStatement.id)) is None


def test_cli_prepares_the_same_review_without_accepting_evidence(
    session, business, monkeypatch, tmp_path
):
    import json

    from sqlalchemy import select
    from test_cli import runner_for

    from reality.cli import app as cli_module
    from reality.db.core import ShippingPlanStatement

    _, value, _ = staged_plan(session, business)
    file = tmp_path / "exact-plan.json"
    file.write_text(json.dumps({"plan": value}), encoding="utf-8")
    result = runner_for(session, monkeypatch).invoke(
        cli_module.app,
        ["shipping-plan-propose", str(file), "--tenant", business.tenant.id],
    )
    assert result.exit_code == 0, result.output
    assert '"requires_confirmation": true' in result.output
    assert session.scalar(select(ShippingPlanStatement.id)) is None


def test_shipping_mcp_schemas_are_closed_and_require_exact_prior_version():
    from reality.mcp.catalog import MCP_TOOL_REGISTRY

    for name in (
        "shipping_plan_propose",
        "shipping_plan_revise_propose",
        "shipping_plan_withdraw_propose",
    ):
        schema = MCP_TOOL_REGISTRY[name].input_schema
        assert schema["additionalProperties"] is False
        assert schema["properties"]["plan"]["additionalProperties"] is False
        assert (
            schema["$defs"]["RequirementInput"]["properties"]["quantity"]["type"]
            == "string"
        )
        if name != "shipping_plan_propose":
            assert set(schema["required"]) == {
                "plan",
                "plan_id",
                "prior_source_record_id",
            }


@pytest.mark.parametrize(
    "tool", ["shipping_plan_revise_propose", "shipping_plan_withdraw_propose"]
)
def test_shipping_mcp_revision_modes_cannot_create_a_new_plan(session, business, tool):
    from reality.mcp.catalog import dispatch_tool
    from reality.services import core

    _, value, _ = staged_plan(session, business)
    with pytest.raises(core.InvalidOperation):
        dispatch_tool(session, business.tenant.id, tool, {"plan": value})


def test_newer_unreviewed_confirmation_source_invalidates_input_review(
    session, business
):
    from reality.services import core
    from reality.services.shipping_plans import review_plan

    _, value, _ = staged_plan(session, business)
    older, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity",
        "window",
        {"completion_slots": 2},
    )
    core.store_source_record(
        session,
        business.tenant.id,
        "carrier",
        "capacity",
        "window",
        {"completion_slots": 1},
    )
    value["capacity_windows"] = payload()["capacity_windows"]
    value["capacity_windows"][0]["confirmation_source_record_id"] = older.id
    with pytest.raises(core.InvalidOperation) as refused:
        review_plan(session, business.tenant.id, {"plan": value})
    assert refused.value.code == "shipping_plan_source_unresolved"


def test_accepted_newer_order_source_is_resolved_but_pending_source_blocks_plan(
    session, business
):
    import json

    from test_operational_cases import FIXTURE, order

    from reality.services import core
    from reality.services.intake import (
        apply_prepared_intake,
        prepare_intake,
        review_intake,
    )
    from reality.services.shipping_plans import review_plan

    commitment = order(session, business)
    value = payload() | {
        "business_time_zone": "UTC",
        "dispatch_location_id": business.location.id,
        "capacity_windows": [],
    }
    value["requirements"][0].update(
        commitment_id=commitment.id,
        quantity=str(
            core.commitment_quantity(session, business.tenant.id, commitment.id)
        ),
    )
    review_plan(session, business.tenant.id, {"plan": value})
    changed = json.loads(FIXTURE.read_text())
    changed.update(
        updated_at="2026-10-06T13:00:00Z",
        note="Another received statement; same promised quantity.",
    )
    source, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        changed,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    with pytest.raises(core.InvalidOperation) as refused:
        review_plan(session, business.tenant.id, {"plan": value})
    assert refused.value.code == "shipping_plan_source_unresolved"
    proposal = prepare_intake(session, business.tenant.id, job.id)
    reviewed = review_intake(session, business.tenant.id, proposal.id)
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, reviewed["digest"], confirmed=True
    )
    normalized, _ = review_plan(session, business.tenant.id, {"plan": value})
    assert source.id in {
        row["current_source_record_id"]
        for row in normalized["reviewed"]["sources"].values()
    }


def test_current_owner_still_must_explicitly_confirm_shipping_plan(
    session, business, scheduled_owner
):
    from reality.services import core
    from reality.services.memberships import Principal
    from reality.tools.application import approve_and_execute_proposal

    proposal, _, _ = staged_plan(session, business)
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(scheduled_owner.id),
            confirmed=False,
        )
    assert refused.value.code == "review_confirmation_required"
    assert proposal.status == "proposed"


def payload():
    return {
        "statement_kind": "plan",
        "dispatch_location_id": "location-v",
        "business_day": "2026-10-06",
        "business_time_zone": "Europe/Berlin",
        "site_time_zone": "Europe/Amsterdam",
        "requirements": [
            {
                "commitment_id": "commitment-b",
                "quantity": "2.0000",
                "dispatch_due_at": "2026-10-06T14:00:00Z",
                "planned_handover_at": "2026-10-06T13:00:00Z",
            }
        ],
        "capacity_windows": [
            {
                "starts_at": "2026-10-06T12:30:00Z",
                "ends_at": "2026-10-06T14:00:00Z",
                "collection_cutoff_at": "2026-10-06T14:00:00Z",
                "completion_slots": 2,
                "confirmation_state": "confirmed",
                "confirmation_source_record_id": "confirmation-v",
            }
        ],
    }


def test_explicit_inputs_preserve_quantity_and_company_calendar():
    plan = PlanInput.model_validate(payload())
    assert plan.business_day == date(2026, 10, 6)
    assert str(plan.requirements[0].quantity) == "2.0000"
    assert plan.capacity_windows[0].completion_slots == 2


@pytest.mark.parametrize(
    "change",
    [
        {"business_time_zone": "Unknown/Zone"},
        {"requirements": []},
        {"invented_daily_total": 1200},
        {"statement_kind": "withdrawal"},
    ],
)
def test_reject_unknown_zones_empty_plans_extra_authority_and_withdrawal_children(
    change,
):
    with pytest.raises(ValidationError):
        PlanInput.model_validate(payload() | change)


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", "0"),
        ("quantity", "NaN"),
        ("quantity", 2.1),
        ("dispatch_due_at", "2026-10-07T14:00:00Z"),
        ("dispatch_due_at", "2026-10-06T14:00:00"),
        ("planned_handover_at", "2026-10-06T15:00:00Z"),
    ],
)
def test_reject_invalid_quantity_naive_time_wrong_day_or_late_plan(field, value):
    value_payload = payload()
    value_payload["requirements"][0][field] = value
    with pytest.raises(ValidationError):
        PlanInput.model_validate(value_payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("completion_slots", True),
        ("completion_slots", -1),
        ("completion_slots", 2.5),
        ("confirmation_source_record_id", None),
        ("collection_cutoff_at", "2026-10-06T14:30:00Z"),
    ],
)
def test_capacity_requires_declared_integer_slots_and_exact_confirmation(field, value):
    value_payload = payload()
    value_payload["capacity_windows"][0][field] = value
    with pytest.raises(ValidationError):
        PlanInput.model_validate(value_payload)


def test_duplicate_requirements_and_overlapping_windows_refuse():
    value = payload()
    value["requirements"].append(value["requirements"][0].copy())
    with pytest.raises(ValidationError):
        PlanInput.model_validate(value)
    value = payload()
    value["capacity_windows"].append(value["capacity_windows"][0].copy())
    with pytest.raises(ValidationError):
        PlanInput.model_validate(value)


def test_withdrawal_is_an_immutable_header_without_children():
    value = payload() | {
        "statement_kind": "withdrawal",
        "requirements": [],
        "capacity_windows": [],
    }
    assert PlanInput.model_validate(value).statement_kind == "withdrawal"
