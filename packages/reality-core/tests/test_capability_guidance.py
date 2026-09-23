import pytest
from sqlalchemy import func, select

from reality.catalogs import load_application_catalog, validate_capability_guidance
from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Fact,
    Movement,
    Reservation,
)
from reality.mcp.catalog import dispatch_tool, model_tool_schemas
from reality.services.core import InvalidOperation, NotFound
from reality.tools.application import run_read_tool

INITIAL_TOOLS = {
    "fact_observe_propose",
    "order_create_propose",
    "reservation_propose",
    "movement_create_propose",
}
COMMITMENT_ACTION_TOOLS = {
    "commitment_revise_propose": "commitment_revise",
    "commitment_cancel_propose": "commitment_cancel",
}
READ_TOOLS = {
    "interpretation_coverage",
    "business_records_discover",
    "order_explain",
    "commitments_list",
    "inventory_read",
    "exceptions_list",
    "fulfillment_queue",
    "fulfillment_blockers",
    "item_supply_demand",
    "exception_explain",
    "proposals_awaiting_approval",
    "proposal_execution_status",
    "finance_balances",
}


def test_capability_lookup_resolves_public_and_unique_application_names(session, business):
    public = run_read_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "reservation_propose"},
    )
    application = run_read_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "reserve"},
    )

    assert public == application
    assert public["canonical_public_name"] == "reservation_propose"

    with pytest.raises(NotFound, match="Capability not found"):
        run_read_tool(
            session,
            business.tenant.id,
            "capability_describe",
            {"tool_name": "not_a_capability"},
        )


def test_capability_lookup_refuses_ambiguous_application_identity(
    session, business, monkeypatch
):
    from reality import catalogs

    monkeypatch.setattr(
        catalogs,
        "load_application_catalog",
        lambda: {
            "capability_guidance": {
                "first_public": {"application_tool": "shared"},
                "second_public": {"application_tool": "shared"},
            }
        },
    )

    with pytest.raises(InvalidOperation, match="ambiguous.*first_public.*second_public"):
        run_read_tool(
            session,
            business.tenant.id,
            "capability_describe",
            {"tool_name": "shared"},
        )


def test_four_initial_capabilities_are_complete_and_distinct():
    guidance = load_application_catalog()["capability_guidance"]

    assert INITIAL_TOOLS <= set(guidance)
    for tool_name in INITIAL_TOOLS:
        entry = guidance[tool_name]
        assert entry["tool_name"] == tool_name
        assert entry["command"]
        assert entry["purpose"]
        assert entry["use_when"]
        assert entry["do_not_use_when"]
        assert entry["required_context"]
        assert entry["preconditions"]
        assert entry["confirmation"] == "required"
        assert entry["idempotency"]["mode"] in {
            "required",
            "supported",
            "unsafe_retry",
        }
        assert entry["idempotency"]["guidance"]
        assert entry["events"]
        assert entry["verification_reads"]
        assert entry["examples"]["use"]
        assert entry["examples"]["do_not_use"]

    assert "source_record" in guidance["fact_observe_propose"]["required_context"]
    verification_names = {
        tool_name: {item["name"] for item in guidance[tool_name]["verification_reads"]}
        for tool_name in INITIAL_TOOLS
    }
    assert "document_register" in verification_names["order_create_propose"]
    assert "inventory" in verification_names["reservation_propose"]
    assert "timeline" in verification_names["movement_create_propose"]


def test_commitment_action_guidance_distinguishes_revision_from_cancellation():
    guidance = load_application_catalog()["capability_guidance"]

    for tool_name, application_tool in COMMITMENT_ACTION_TOOLS.items():
        entry = guidance[tool_name]
        assert entry["application_tool"] == application_tool
        assert entry["confirmation"] == "required"
        assert entry["idempotency"]["mode"] == "required"
        assert entry["preconditions"]
        assert entry["refusals"]
        assert entry["events"]
        assert entry["verification_reads"]

    assert "retained_allocations" in " ".join(
        guidance["commitment_revise_propose"]["preconditions"]
    )
    assert "reason" in " ".join(
        guidance["commitment_cancel_propose"]["preconditions"]
    )


def test_all_public_business_read_capabilities_are_complete_and_distinct():
    guidance = load_application_catalog()["capability_guidance"]

    assert READ_TOOLS <= set(guidance)
    for tool_name in READ_TOOLS:
        entry = guidance[tool_name]
        assert entry["kind"] == "read"
        assert entry["tool_name"] == tool_name
        assert entry["application_tool"]
        assert entry["purpose"]
        for field in (
            "use_when",
            "do_not_use_when",
            "required_context",
            "data_basis",
            "limitations",
            "unknown_when",
            "next_steps",
        ):
            assert entry[field]
        assert entry["freshness"]
        assert entry["empty_result"]
        assert entry["refusal_behavior"]
        assert entry["confirmation"] == "none"
        assert entry["side_effects"] == "none"
        assert entry["verification"]["role"] in {"discovery", "context", "independent"}
        assert entry["verification"]["proves"]
        assert entry["verification"]["does_not_prove"]
        assert entry["examples"]["use"]
        assert entry["examples"]["do_not_use"]

    assert guidance["business_records_discover"]["verification"]["role"] == "discovery"
    assert guidance["inventory_read"]["verification"]["role"] == "independent"
    assert "interpretation_outcome" in guidance["interpretation_coverage"]["data_basis"]
    assert guidance["finance_balances"]["verification"]["role"] == "independent"
    assert guidance["fulfillment_blockers"]["verification"]["role"] == "context"


def _valid_read_guidance():
    return {
        "inventory": {
            "kind": "read",
            "application_tool": "inventory",
            "purpose": "Read derived stock.",
            "use_when": ["Stock consequence is needed."],
            "do_not_use_when": ["A promise is needed."],
            "required_context": ["item"],
            "data_basis": ["inventory"],
            "limitations": ["Does not prove delivery."],
            "freshness": "Projection version at read time.",
            "empty_result": "No projected rows.",
            "refusal_behavior": "Tenant scope is enforced.",
            "confirmation": "none",
            "side_effects": "none",
            "verification": {
                "role": "independent",
                "proves": ["Derived stock is visible."],
                "does_not_prove": ["External delivery."],
            },
            "unknown_when": ["The projection is stale."],
            "next_steps": ["Read commitments."],
            "examples": {
                "use": [
                    {"scenario": "Verify reservation.", "reason": "Stock is relevant."}
                ],
                "do_not_use": [
                    {
                        "scenario": "Prove delivery.",
                        "reason": "External state is absent.",
                    }
                ],
            },
        }
    }


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["inventory"].pop("limitations"), "missing limitations"),
        (
            lambda value: value["inventory"].update(application_tool="reserve"),
            "target is not read-only",
        ),
        (
            lambda value: value["inventory"].update(data_basis=["unknown"]),
            "unknown data basis",
        ),
        (
            lambda value: value["inventory"]["verification"].update(role="authority"),
            "invalid verification role",
        ),
        (
            lambda value: value["inventory"].update(side_effects="writes"),
            "side-effect mismatch",
        ),
    ],
)
def test_read_capability_guidance_rejects_planted_drift(mutate, message):
    value = _valid_read_guidance()
    mutate(value)
    with pytest.raises(ValueError, match=message):
        validate_capability_guidance(
            value,
            commands=[],
            agent_coverage={},
            event_types=set(),
            projection_names={"inventory"},
            read_tool_names={"inventory"},
            mutating_tool_names={"reserve"},
            proposal_targets={"inventory": "inventory"},
            public_tool_names={"inventory"},
            data_basis_names={"inventory"},
        )


def test_twelve_selection_examples_cover_observation_promise_allocation_and_movement():
    guidance = load_application_catalog()["capability_guidance"]
    examples = [
        (tool_name, kind, example["scenario"], example["reason"])
        for tool_name, entry in guidance.items()
        for kind in ("use", "do_not_use")
        for example in entry["examples"][kind]
    ]

    assert len(examples) >= 12
    assert all(
        kind in {"use", "do_not_use"} and scenario and reason
        for _, kind, scenario, reason in examples
    )
    text = " ".join(
        f"{tool} {kind} {scenario} {reason}"
        for tool, kind, scenario, reason in examples
    ).lower()
    for concept in (
        "source",
        "fact",
        "commitment",
        "reservation",
        "movement",
        "physical",
    ):
        assert concept in text


def _valid_guidance():
    return {
        "reservation_propose": {
            "application_tool": "reserve",
            "purpose": "Allocate stock.",
            "use_when": ["A commitment needs allocation."],
            "do_not_use_when": ["Goods moved physically."],
            "required_context": ["commitment"],
            "preconditions": ["The commitment exists."],
            "confirmation": "required",
            "idempotency": {
                "mode": "unsafe_retry",
                "guidance": "Reconcile before retry.",
            },
            "refusals": [
                {"code": "insufficient_stock", "description": "Stock is unavailable."}
            ],
            "events": ["reservation.created"],
            "verification_reads": [
                {"name": "inventory", "proves": "Allocation reduces availability."}
            ],
            "examples": {
                "use": [
                    {"scenario": "Allocate stock.", "reason": "Allocation is intended."}
                ],
                "do_not_use": [
                    {"scenario": "Ship stock.", "reason": "A Movement is intended."}
                ],
            },
        }
    }


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["reservation_propose"].pop("use_when"),
            "missing use_when",
        ),
        (
            lambda value: value["reservation_propose"].update(events=["unknown.event"]),
            "unknown events",
        ),
        (
            lambda value: value["reservation_propose"].update(
                verification_reads=[{"name": "unknown", "proves": "Nothing."}]
            ),
            "unknown verification reads",
        ),
        (
            lambda value: value["reservation_propose"].update(confirmation="none"),
            "confirmation mismatch",
        ),
    ],
)
def test_capability_guidance_rejects_planted_drift(mutate, message):
    value = _valid_guidance()
    mutate(value)
    with pytest.raises(ValueError, match=message):
        validate_capability_guidance(
            value,
            commands=[{"name": "Reserve stock", "service": "reserve"}],
            agent_coverage={
                "reserve": {
                    "classification": "eligible",
                    "tools": ["reservation_propose"],
                }
            },
            event_types={"reservation.created"},
            projection_names={"inventory"},
            read_tool_names={"inventory"},
            mutating_tool_names={"reserve"},
            proposal_targets={"reservation_propose": "reserve"},
        )


def test_capability_guidance_rejects_duplicate_public_tool_identity():
    entry = {
        "tool_name": "reservation_propose",
        **_valid_guidance()["reservation_propose"],
    }
    with pytest.raises(ValueError, match="Duplicate capability guidance"):
        validate_capability_guidance(
            [entry, entry],
            commands=[{"name": "Reserve stock", "service": "reserve"}],
            agent_coverage={
                "reserve": {
                    "classification": "eligible",
                    "tools": ["reservation_propose"],
                }
            },
            event_types={"reservation.created"},
            projection_names={"inventory"},
            read_tool_names={"inventory"},
            mutating_tool_names={"reserve"},
            proposal_targets={"reservation_propose": "reserve"},
        )


def test_capability_describe_is_shared_read_only_and_bounded(session, business):
    before = {
        model.__name__: session.scalar(select(func.count()).select_from(model))
        for model in (
            ChangeProposal,
            Fact,
            Commitment,
            Reservation,
            Movement,
            BusinessEvent,
        )
    }

    application_result = run_read_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "reservation_propose"},
    )
    mcp_result = dispatch_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "reservation_propose"},
        allowed_access=("read",),
    )

    assert application_result == mcp_result
    assert application_result["tool_name"] == "reservation_propose"
    after = {
        model.__name__: session.scalar(select(func.count()).select_from(model))
        for model in (
            ChangeProposal,
            Fact,
            Commitment,
            Reservation,
            Movement,
            BusinessEvent,
        )
    }
    assert after == before

    read_result = run_read_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "inventory_read"},
    )
    assert read_result["kind"] == "read"
    assert read_result["verification"]["does_not_prove"]

    confirmation = run_read_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "proposal_approve_and_execute"},
    )
    assert confirmation["kind"] == "confirm"
    assert "authenticated principal" in confirmation["principal_semantics"]
    assert confirmation["idempotency"]["mode"] == "single_use_replay"
    assert confirmation["retry_behavior"]
    assert confirmation["unknown_behavior"]
    assert "proposal_id" in confirmation["receipt"]["fields"]
    assert confirmation == dispatch_tool(
        session,
        business.tenant.id,
        "capability_describe",
        {"tool_name": "proposal_approve_and_execute"},
        allowed_access=("read",),
    )

    with pytest.raises(NotFound, match="Capability not found"):
        run_read_tool(
            session,
            business.tenant.id,
            "capability_describe",
            {"tool_name": "tenant_delete"},
        )


def test_capability_describe_schema_is_read_only_and_strict():
    schemas = {
        entry["function"]["name"]: entry["function"]
        for entry in model_tool_schemas(access=("read",))
    }
    schema = schemas["capability_describe"]["parameters"]

    assert schema["required"] == ["tool_name"]
    assert schema["additionalProperties"] is False
    default_exposed = {entry["function"]["name"] for entry in model_tool_schemas()}
    assert "proposal_approve_and_execute" not in default_exposed
    assert "proposal_execution_status" in default_exposed
