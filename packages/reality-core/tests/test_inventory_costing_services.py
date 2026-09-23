"""Spec 234: confirmed inventory authority and frozen service replay."""

import json
from datetime import timedelta
from decimal import Decimal

import pytest
import test_costing_services as fixtures
from conftest import record_by_id
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Movement,
    MovementCorrection,
    TenantMembership,
)
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryOwnershipPart,
    CostInventoryReview,
    CostMovementBasis,
    CostOpeningBasis,
    CostOwnershipRevision,
    CostPolicyRevision,
)
from reality.domain.costing import InventoryReview
from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.costing import (
    execute_cost_change,
    inventory_cost,
    preview_cost_change,
    receipt_cost,
)
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)

cost_owner = fixtures.cost_owner


def test_inventory_ownership_parts_value_only_selected_owner(
    session, business, cost_owner
):
    opening = core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    transfer = core.record_movement(
        session,
        business.tenant.id,
        "transfer",
        business.item.id,
        "10",
        from_location_id=business.location.id,
        to_location_id=business.location.id,
    )
    issue = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
    )
    evidence = fixtures.evidence(session, business, "500", "0")
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (opening.occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [issue.id],
        "openings": [
            {
                "movement_id": opening.id,
                "evidence_source_record_id": evidence.source_record_id,
                "acquisition_cost": "500",
            }
        ],
        "ownership_parts": [
            {
                "movement_id": opening.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "6",
            },
            {
                "movement_id": opening.id,
                "owner_party_id": business.supplier.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "4",
            },
            {
                "movement_id": transfer.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "6",
            },
            {
                "movement_id": transfer.id,
                "owner_party_id": business.supplier.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "4",
            },
            {
                "movement_id": issue.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "5",
            },
        ],
        "reason": "Confirmed complete ownership partition",
    }

    preview = preview_cost_change(
        session, business.tenant.id, args, principal=Principal(cost_owner.id)
    )
    assert preview["review"]["acquisition_value"] == "50.0000"
    assert preview["review"]["consumption"][0]["cost"] == "250.0000"

    action, result = commit_review(session, business, cost_owner, args)

    assert result["remaining_quantity"] == "1.0000"
    assert result["acquisition_value"] == "50.0000"
    assert len(result["ownership_sources"]) == 5
    assert {row["owner_party_id"] for row in result["ownership_sources"]} == {
        business.company.id,
        business.supplier.id,
    }
    replay = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(replay.output) == result
    assert (
        session.scalar(select(func.count()).select_from(CostInventoryOwnershipPart))
        == 5
    )
    retained = session.scalars(
        select(CostInventoryOwnershipPart).order_by(
            CostInventoryOwnershipPart.movement_basis_id,
            CostInventoryOwnershipPart.owner_party_id,
        )
    ).all()
    assert sum((row.quantity for row in retained), Decimal(0)) == Decimal(25)
    retained[0].quantity = Decimal(1)
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        inventory_cost(
            session,
            business.tenant.id,
            business.item.id,
            review_id=result["review_id"],
        )


def test_inventory_ownership_parts_require_complete_conservation(
    session, business, cost_owner
):
    opening = core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    evidence = fixtures.evidence(session, business, "500", "0")
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (opening.occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [],
        "openings": [
            {
                "movement_id": opening.id,
                "evidence_source_record_id": evidence.source_record_id,
                "acquisition_cost": "500",
            }
        ],
        "ownership_parts": [
            {
                "movement_id": opening.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "9",
            }
        ],
        "reason": "Invalid incomplete ownership partition",
    }

    with pytest.raises(core.InvalidOperation, match="conserve movement quantity"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )

    args["ownership_parts"][0]["quantity"] = "11"
    with pytest.raises(core.InvalidOperation, match="conserve movement quantity"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )

    args["ownership_parts"][0]["quantity"] = "10"
    args["ownership_parts"][0]["evidence_source_record_id"] = "src_foreign"
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_ownership_parts_reject_duplicate_owner_portion():
    instant = core.now().isoformat()
    common = {
        "movement_id": "movement",
        "owner_party_id": "owner",
        "evidence_source_record_id": "source",
        "quantity": "1",
    }
    with pytest.raises(ValueError, match="Duplicate movement owner portion"):
        InventoryReview.model_validate(
            {
                "operation": "inventory_review",
                "expected_event_sequence": 1,
                "reason": "Duplicate ownership is ambiguous",
                "item_id": "item",
                "owner_party_id": "owner",
                "method": "fifo",
                "currency": "EUR",
                "base_unit": "pcs",
                "history_start": instant,
                "effective_at": instant,
                "history_complete_from_zero": True,
                "receipt_cost_scopes_confirmed": True,
                "economic_issue_ids": [],
                "ownership_parts": [common, common],
            }
        )


def test_inventory_transfer_allocation_cannot_invent_owner_stock(
    session, business, cost_owner
):
    opening = core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    transfer = core.record_movement(
        session,
        business.tenant.id,
        "transfer",
        business.item.id,
        "10",
        from_location_id=business.location.id,
        to_location_id=business.location.id,
    )
    evidence = fixtures.evidence(session, business, "500", "0")
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "item_id": business.item.id,
        "owner_party_id": business.supplier.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (opening.occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [],
        "openings": [
            {
                "movement_id": opening.id,
                "evidence_source_record_id": evidence.source_record_id,
                "acquisition_cost": "500",
            }
        ],
        "ownership_parts": [
            {
                "movement_id": opening.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "6",
            },
            {
                "movement_id": opening.id,
                "owner_party_id": business.supplier.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "4",
            },
            {
                "movement_id": transfer.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "4",
            },
            {
                "movement_id": transfer.id,
                "owner_party_id": business.supplier.id,
                "evidence_source_record_id": evidence.source_record_id,
                "quantity": "6",
            },
        ],
        "reason": "Reject unsupported title invention during physical transfer",
    }

    with pytest.raises(core.InvalidOperation, match="insufficient_stock"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


@pytest.mark.parametrize(
    ("stated_cost", "expected_cost"), [("500", "250.0000"), ("0", "0.0000")]
)
def test_inventory_evidenced_opening_is_a_costed_layer(
    session, business, cost_owner, stated_cost, expected_cost
):
    opening = core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    issue = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
    )
    evidence = fixtures.evidence(session, business, "500", "0")
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (opening.occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [issue.id],
        "receipts": [],
        "openings": [
            {
                "movement_id": opening.id,
                "evidence_source_record_id": evidence.source_record_id,
                "acquisition_cost": stated_cost,
            }
        ],
        "reason": "Confirmed evidenced opening acquisition cost and ownership",
    }

    with pytest.raises(core.InvalidOperation, match="opening stock requires exact"):
        preview_cost_change(
            session,
            business.tenant.id,
            {**args, "openings": []},
            principal=Principal(cost_owner.id),
        )
    foreign = {
        **args,
        "openings": [
            {**args["openings"][0], "evidence_source_record_id": "src_foreign"}
        ],
    }
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session,
            business.tenant.id,
            foreign,
            principal=Principal(cost_owner.id),
        )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["consumption"][0]["cost"] == expected_cost
    assert result["remaining_quantity"] == "5.0000"
    assert result["acquisition_value"] == expected_cost
    assert (
        result["opening_sources"][0]["evidence_source_record_id"]
        == evidence.source_record_id
    )
    retained = session.scalar(select(CostOpeningBasis))
    retained.acquisition_cost = Decimal(999)
    retained.owner_party_id = business.supplier.id
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        inventory_cost(
            session,
            business.tenant.id,
            business.item.id,
            review_id=result["review_id"],
        )


@pytest.mark.parametrize(
    ("method", "expected_consumption"), [("fifo", "200.0000"), ("specific", "250.0000")]
)
def test_inventory_multiple_openings_support_fifo_and_specific(
    session, business, cost_owner, method, expected_consumption
):
    openings = [
        core.record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            business.item.id,
            "10",
            to_location_id=business.location.id,
        )
        for _ in range(2)
    ]
    issue = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "15",
        from_location_id=business.location.id,
    )
    evidence = [
        fixtures.evidence(session, business, amount, "0") for amount in ("100", "200")
    ]
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": method,
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (openings[0].occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [issue.id],
        "openings": [
            {
                "movement_id": movement.id,
                "evidence_source_record_id": source.source_record_id,
                "acquisition_cost": amount,
            }
            for movement, source, amount in zip(
                openings, evidence, ("100", "200"), strict=True
            )
        ],
        "specific_selections": (
            [
                {
                    "movement_id": issue.id,
                    "entry_movement_id": openings[1].id,
                    "receipt_movement_id": openings[1].id,
                    "quantity": "10",
                },
                {
                    "movement_id": issue.id,
                    "entry_movement_id": openings[0].id,
                    "receipt_movement_id": openings[0].id,
                    "quantity": "5",
                },
            ]
            if method == "specific"
            else []
        ),
        "reason": "Confirmed two evidenced opening layers",
    }

    _, result = commit_review(session, business, cost_owner, args)

    assert result["consumption"][0]["cost"] == expected_consumption
    assert result["remaining_quantity"] == "5.0000"


def test_inventory_corrected_opening_uses_only_replacement_identity(
    session, business, cost_owner
):
    original = core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    correction = core.correct_movement(
        session,
        business.tenant.id,
        original.id,
        reason="Replace opening identity",
        replacement={
            "type": "opening_stock",
            "item_id": business.item.id,
            "quantity": "10",
            "to_location_id": business.location.id,
            "occurred_at": original.occurred_at.isoformat(),
        },
    )
    replacement = record_by_id(session, Movement, correction.replacement_movement_id)
    issue = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
    )
    evidence = fixtures.evidence(session, business, "500", "0")
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == business.tenant.id
            )
        ),
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (original.occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [issue.id],
        "openings": [
            {
                "movement_id": replacement.id,
                "evidence_source_record_id": evidence.source_record_id,
                "acquisition_cost": "500",
            }
        ],
        "reason": "Confirmed corrected evidenced opening",
    }

    _, result = commit_review(session, business, cost_owner, args)

    assert result["consumption"][0]["cost"] == "250.0000"
    assert session.scalar(select(CostOpeningBasis)).movement_basis_id == session.scalar(
        select(CostMovementBasis.id).where(
            CostMovementBasis.movement_id == replacement.id
        )
    )


def prepared(session, business, owner, *, same_instant=False):
    movement = fixtures.receipt(session, business)
    for amount, category in [
        ("1000", "goods"),
        ("100", "inbound_freight"),
        ("-50", "purchase_reduction"),
    ]:
        doc = fixtures.evidence(session, business, amount, "0")
        fixtures.execute(
            session,
            business,
            owner,
            fixtures.assignment(session, business, movement, doc, amount, category),
        )
    settled = fixtures.review(
        session,
        business,
        owner,
        movement,
        {"goods", "inbound_freight", "purchase_reduction"},
    )
    issue = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "60",
        from_location_id=business.location.id,
        occurred_at=movement.occurred_at if same_instant else None,
    )
    args = {
        "operation": "inventory_review",
        "expected_event_sequence": receipt_cost(
            session, business.tenant.id, movement.id
        )["event_sequence"],
        "item_id": business.item.id,
        "owner_party_id": business.company.id,
        "method": "fifo",
        "currency": "EUR",
        "base_unit": business.item.unit,
        "history_start": (movement.occurred_at - timedelta(seconds=1)).isoformat(),
        "effective_at": core.now().isoformat(),
        "history_complete_from_zero": True,
        "receipt_cost_scopes_confirmed": True,
        "economic_issue_ids": [issue.id],
        "receipts": [
            {
                "movement_id": movement.id,
                "manifest_id": settled["manifest_id"],
                "ownership_source_record_id": doc.source_record_id,
            }
        ],
        "reason": "Confirmed whole-item ownership, empty opening and retained receipt costs",
    }
    return args, movement, issue


def commit_review(session, business, owner, args):
    with caller(Principal(owner.id)):
        action = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    done = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(owner.id),
        confirmed=True,
    )
    return done, json.loads(done.output)


def test_inventory_two_owner_receipt_excludes_consigned_stock(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    evidence_id = args["receipts"][0]["ownership_source_record_id"]
    args["ownership_parts"] = [
        {
            "movement_id": receipt.id,
            "owner_party_id": business.company.id,
            "evidence_source_record_id": evidence_id,
            "quantity": "60",
        },
        {
            "movement_id": receipt.id,
            "owner_party_id": business.supplier.id,
            "evidence_source_record_id": evidence_id,
            "quantity": "40",
        },
        {
            "movement_id": issue.id,
            "owner_party_id": business.company.id,
            "evidence_source_record_id": evidence_id,
            "quantity": "60",
        },
    ]
    args["reason"] = "Confirmed company-owned and consigned receipt portions"

    _, result = commit_review(session, business, cost_owner, args)

    assert result["consumption"][0]["cost"] == "630.0000"
    assert result["remaining_quantity"] == "0.0000"
    assert result["acquisition_value"] == "0.0000"
    ownership = session.scalar(
        select(CostOwnershipRevision).where(
            CostOwnershipRevision.owner_party_id == business.company.id
        )
    )
    assert ownership.covered_quantity == Decimal(60)


def test_inventory_service_a_and_exact_history(session, business, cost_owner):
    args, movement, issue = prepared(session, business, cost_owner)
    before = session.scalar(select(func.count()).select_from(CostInventoryReview))
    preview = preview_cost_change(
        session, business.tenant.id, args, principal=Principal(cost_owner.id)
    )
    assert preview["review"]["movement_count"] == 2
    assert preview["review"]["acquisition_value"] == "420.0000"
    assert preview["review"]["consumption"][0]["cost"] == "630.0000"
    assert (
        session.scalar(select(func.count()).select_from(CostInventoryReview)) == before
    )
    action, result = commit_review(session, business, cost_owner, args)
    assert result["acquisition_value"] == "420.0000"
    assert result["consumption"][0]["cost"] == "630.0000"
    assert result["consumption"][0]["movement_id"] == issue.id
    assert result["remaining"][0]["receipt_movement_id"] == movement.id
    assert result["carrying_value"] is None
    assert result["owner_party_id"] == business.company.id
    assert result["policy_id"] and result["review_id"]
    assert result["action_id"] == action.id and result["reason"] == args["reason"]
    assert result["algorithm_version"] == "inventory-v1"
    assert result["persistence"] == {
        "business_writes": False,
        "projection_writes": False,
    }
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "cost.inventory.get",
            {"item_id": business.item.id},
        )
        == result
    )
    again = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(again.output) == result
    assert session.scalar(select(func.count()).select_from(CostInventoryReview)) == 1
    core.correct_movement(
        session, business.tenant.id, issue.id, reason="Wrong delivery"
    )
    current = inventory_cost(session, business.tenant.id, business.item.id)
    assert current["review_state"] == "stale" and current["acquisition_value"] is None
    assert current["remaining_quantity"] is None and current["consumption"] is None
    assert current["basis_remaining_quantity"] == "40.0000"
    assert current["basis_consumption"][0]["basis_cost"] == "630.0000"
    historical = inventory_cost(
        session, business.tenant.id, business.item.id, review_id=result["review_id"]
    )
    assert historical["acquisition_value"] == "420.0000"
    assert historical["consumption"][0]["cost"] == "630.0000"
    assert session.scalar(select(func.count()).select_from(CostMovementBasis)) == 2


@pytest.mark.parametrize("method", ["fifo", "specific"])
def test_inventory_customer_return_restores_original_issue_cost(
    session, business, cost_owner, method
):
    args, receipt, issue = prepared(session, business, cost_owner)
    returned = core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    args.update(
        method=method,
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        customer_return_ids=[returned.id],
        return_parts=[
            {
                "movement_id": returned.id,
                "issue_movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "10",
            }
        ],
        specific_selections=(
            [
                {
                    "movement_id": issue.id,
                    "entry_movement_id": receipt.id,
                    "receipt_movement_id": receipt.id,
                    "quantity": "60",
                }
            ]
            if method == "specific"
            else []
        ),
    )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["consumption"][0]["cost"] == "630.0000"
    assert result["returns"][0]["cost"] == "-105.0000"
    assert result["returns"][0]["parts"][0]["issue_movement_id"] == issue.id
    assert result["remaining_quantity"] == "50.0000"
    assert result["acquisition_value"] == "525.0000"


def test_inventory_accepts_transfer_that_resolves_reviewed_customer_return(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    returned = core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "transfer",
        business.item.id,
        "10",
        from_location_id=business.location.id,
        to_location_id=business.location.id,
        resolves_movement_id=returned.id,
    )
    args.update(
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        customer_return_ids=[returned.id],
        return_parts=[
            {
                "movement_id": returned.id,
                "issue_movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "10",
            }
        ],
        reason="Reviewed return remains valued after its physical transfer",
    )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["remaining_quantity"] == "50.0000"
    assert result["acquisition_value"] == "525.0000"


@pytest.mark.parametrize("method", ["fifo", "specific"])
def test_inventory_partial_owner_issue_return_and_loss_conserve_cost(
    session, business, cost_owner, method
):
    args, receipt, issue = prepared(session, business, cost_owner)
    returned = core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    loss = core.record_movement(
        session,
        business.tenant.id,
        "adjustment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        reason="Confirmed damaged owned stock",
    )
    evidence_id = args["receipts"][0]["ownership_source_record_id"]
    args.update(
        method=method,
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        customer_return_ids=[returned.id],
        loss_movement_ids=[loss.id],
        return_parts=[
            {
                "movement_id": returned.id,
                "issue_movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "10",
            }
        ],
        specific_selections=(
            [
                {
                    "movement_id": movement_id,
                    "entry_movement_id": receipt.id,
                    "receipt_movement_id": receipt.id,
                    "quantity": quantity,
                }
                for movement_id, quantity in ((issue.id, "60"), (loss.id, "5"))
            ]
            if method == "specific"
            else []
        ),
        ownership_parts=[
            {
                "movement_id": movement_id,
                "owner_party_id": owner_id,
                "evidence_source_record_id": evidence_id,
                "quantity": quantity,
            }
            for movement_id, owner_id, quantity in (
                (receipt.id, business.company.id, "70"),
                (receipt.id, business.supplier.id, "30"),
                (issue.id, business.company.id, "60"),
                (returned.id, business.company.id, "10"),
                (loss.id, business.company.id, "5"),
            )
        ],
        reason="Confirmed partial-owner issue, return and loss",
    )

    _, result = commit_review(session, business, cost_owner, args)

    observations = {row["movement_id"]: row for row in result["consumption"]}
    assert observations[issue.id]["cost"] == "630.0000"
    assert observations[loss.id]["cost"] == "52.5000"
    assert result["returns"][0]["cost"] == "-105.0000"
    assert result["remaining_quantity"] == "15.0000"
    assert result["acquisition_value"] == "157.5000"


def test_inventory_supplier_return_and_confirmed_loss_are_explicit(
    session, business, cost_owner
):
    args, receipt, _ = prepared(session, business, cost_owner)
    supplier_return = core.record_movement(
        session,
        business.tenant.id,
        "supplier_return",
        business.item.id,
        "10",
        from_location_id=business.location.id,
    )
    loss = core.record_movement(
        session,
        business.tenant.id,
        "adjustment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        reason="Confirmed damaged stock",
    )
    args.update(
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        supplier_return_ids=[supplier_return.id],
        loss_movement_ids=[loss.id],
        specific_selections=[
            {
                "movement_id": supplier_return.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "10",
            }
        ],
    )

    _, result = commit_review(session, business, cost_owner, args)

    observations = {row["movement_id"]: row for row in result["consumption"]}
    assert observations[supplier_return.id]["kind"] == "supplier_return"
    assert observations[supplier_return.id]["cost"] == "105.0000"
    assert observations[loss.id]["kind"] == "loss"
    assert observations[loss.id]["cost"] == "52.5000"
    assert result["remaining_quantity"] == "25.0000"
    assert result["acquisition_value"] == "262.5000"


def test_inventory_cumulative_returns_cannot_exceed_original_issue(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    returns = [
        core.record_movement(
            session,
            business.tenant.id,
            "return",
            business.item.id,
            quantity,
            to_location_id=business.location.id,
        )
        for quantity in ("40", "21")
    ]
    args.update(
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        customer_return_ids=[row.id for row in returns],
        return_parts=[
            {
                "movement_id": row.id,
                "issue_movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": quantity,
            }
            for row, quantity in zip(returns, ("40", "21"), strict=True)
        ],
    )

    with pytest.raises(
        core.InvalidOperation, match="original_portion_required|portion_exceeded"
    ):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_late_cost_requires_receipt_review_and_preserves_old_basis(
    session, business, cost_owner
):
    args, movement, _ = prepared(session, business, cost_owner)
    _, first = commit_review(session, business, cost_owner, args)
    doc = fixtures.evidence(session, business, "50", "0")
    fixtures.execute(
        session,
        business,
        cost_owner,
        fixtures.assignment(session, business, movement, doc, "50", "inbound_freight"),
    )
    args["expected_event_sequence"] = receipt_cost(
        session, business.tenant.id, movement.id
    )["event_sequence"]
    with pytest.raises(core.InvalidOperation, match="receipt review"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )
    review = fixtures.review(
        session,
        business,
        cost_owner,
        movement,
        {"goods", "inbound_freight", "purchase_reduction"},
    )
    args["receipts"][0]["manifest_id"] = review["manifest_id"]
    args["expected_event_sequence"] = receipt_cost(
        session, business.tenant.id, movement.id
    )["event_sequence"]
    _, second = commit_review(session, business, cost_owner, args)
    assert second["acquisition_value"] == "440.0000"
    assert second["consumption"][0]["cost"] == "660.0000"
    assert (
        inventory_cost(
            session, business.tenant.id, business.item.id, review_id=first["review_id"]
        )["acquisition_value"]
        == "420.0000"
    )
    policies = list(
        session.scalars(
            select(CostPolicyRevision).order_by(CostPolicyRevision.revision)
        )
    )
    assert len(policies) == 2 and policies[1].supersedes_id == policies[0].id
    owners = list(
        session.scalars(
            select(CostOwnershipRevision).order_by(CostOwnershipRevision.revision)
        )
    )
    assert owners[1].supersedes_id == owners[0].id


@pytest.mark.parametrize(
    "change",
    [
        {"receipts": []},
        {"economic_issue_ids": []},
        {"history_complete_from_zero": False},
        {"receipt_cost_scopes_confirmed": False},
        {"method": "specific"},
        {"currency": "USD"},
        {"base_unit": "different-unit"},
    ],
)
def test_inventory_refuses_incomplete_or_unsupported_scope(
    session, business, cost_owner, change
):
    args, _, _ = prepared(session, business, cost_owner)
    with pytest.raises(core.InvalidOperation):
        preview_cost_change(
            session,
            business.tenant.id,
            args | change,
            principal=Principal(cost_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(CostInventoryReview)) == 0


def test_specific_policy_uses_confirmed_exact_layer_selection_and_replays_history(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    args |= {
        "method": "specific",
        "specific_selections": [
            {
                "movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "60",
            }
        ],
    }
    preview = preview_cost_change(
        session, business.tenant.id, args, principal=Principal(cost_owner.id)
    )
    assert preview["review"]["consumption"][0]["cost"] == "630.0000"
    _, result = commit_review(session, business, cost_owner, args)
    assert result["method"] == "specific"
    assert result["consumption"][0]["parts"] == [
        {
            "entry_movement_id": receipt.id,
            "receipt_movement_id": receipt.id,
            "quantity": "60.0000",
            "cost": "630.0000",
            "issue_movement_id": None,
        }
    ]
    assert (
        inventory_cost(
            session,
            business.tenant.id,
            business.item.id,
            review_id=result["review_id"],
        )["consumption"]
        == result["consumption"]
    )


@pytest.mark.parametrize(
    "method,selections",
    [
        ("specific", []),
        (
            "specific",
            [
                {
                    "movement_id": "wrong-issue",
                    "entry_movement_id": "receipt",
                    "receipt_movement_id": "receipt",
                    "quantity": "60",
                }
            ],
        ),
        (
            "specific",
            [
                {
                    "movement_id": "issue",
                    "entry_movement_id": "missing-layer",
                    "receipt_movement_id": "missing-layer",
                    "quantity": "60",
                }
            ],
        ),
        (
            "fifo",
            [
                {
                    "movement_id": "issue",
                    "entry_movement_id": "receipt",
                    "receipt_movement_id": "receipt",
                    "quantity": "60",
                }
            ],
        ),
    ],
)
def test_specific_selection_must_exactly_cover_held_issue_and_available_layer(
    session, business, cost_owner, method, selections
):
    args, receipt, issue = prepared(session, business, cost_owner)
    encoded = [
        {
            **row,
            "movement_id": issue.id
            if row["movement_id"] == "issue"
            else row["movement_id"],
            "entry_movement_id": receipt.id
            if row["entry_movement_id"] == "receipt"
            else row["entry_movement_id"],
            "receipt_movement_id": receipt.id
            if row["receipt_movement_id"] == "receipt"
            else row["receipt_movement_id"],
        }
        for row in selections
    ]
    with pytest.raises(core.InvalidOperation):
        preview_cost_change(
            session,
            business.tenant.id,
            args | {"method": method, "specific_selections": encoded},
            principal=Principal(cost_owner.id),
        )


def test_inventory_foreign_scope_and_actual_read_tool(session, business, cost_owner):
    args, _, _ = prepared(session, business, cost_owner)
    other = core.create_tenant(session, "Unrelated inventory company")
    with pytest.raises(core.NotFound):
        inventory_cost(session, other.id, business.item.id)
    with pytest.raises(core.NotFound):
        preview_cost_change(session, other.id, args, principal=Principal(cost_owner.id))
    args["expected_event_sequence"] = receipt_cost(
        session, business.tenant.id, args["receipts"][0]["movement_id"]
    )["event_sequence"]
    _, result = commit_review(session, business, cost_owner, args)
    assert MCP_TOOL_REGISTRY["cost_inventory_get"].input_schema["properties"][
        "review_id"
    ]
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "cost.inventory.get",
            {"item_id": business.item.id},
        )["review_id"]
        == result["review_id"]
    )
    with pytest.raises(core.NotFound):
        inventory_cost(
            session, other.id, business.item.id, review_id=result["review_id"]
        )


def test_unrelated_finance_event_does_not_stale_reviewed_inventory(
    session, business, cost_owner
):
    arguments, _, _ = prepared(session, business, cost_owner)
    _, reviewed = commit_review(session, business, cost_owner, arguments)
    core.emit_business_event(
        session,
        business.tenant.id,
        "payment.recorded",
        "tenant",
        business.tenant.id,
        {"amount": "1"},
    )

    current = inventory_cost(session, business.tenant.id, business.item.id)

    assert current["review_id"] == reviewed["review_id"]
    assert current["acquisition_value"] == reviewed["acquisition_value"]
    assert current["missing_basis"] == []


def test_inventory_owner_confirmation_stale_and_rollback(
    session, business, cost_owner, monkeypatch
):
    args, _, _ = prepared(session, business, cost_owner)
    with caller(Principal(cost_owner.id)):
        action = create_change_proposal(
            session, business.tenant.id, "cost.change", args
        )
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
        )
    from reality.services import inventory_costing

    original = inventory_costing._new

    def fail(session, model, tenant, **values):
        if model is CostInventoryMember:
            raise RuntimeError("Injected member failure")
        return original(session, model, tenant, **values)

    monkeypatch.setattr(inventory_costing, "_new", fail)
    with pytest.raises(RuntimeError, match="Injected"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    assert session.scalar(select(func.count()).select_from(CostPolicyRevision)) == 0
    assert session.scalar(select(func.count()).select_from(CostMovementBasis)) == 0
    assert record_by_id(session, ChangeProposal, action.id).status == "proposed"
    monkeypatch.setattr(inventory_costing, "_new", original)
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
    )
    with pytest.raises(core.Conflict, match="stale"):
        execute_cost_change(
            session,
            business.tenant.id,
            arguments=args,
            action_id=action.id,
            actor_id=cost_owner.id,
            confirmed=True,
        )
    membership = session.scalar(
        select(TenantMembership).where(TenantMembership.user_id == cost_owner.id)
    )
    membership.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="owner"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_manifest_integrity_and_read_never_flushes(
    session, business, cost_owner
):
    args, _, _ = prepared(session, business, cost_owner)
    _, result = commit_review(session, business, cost_owner, args)
    basis = session.scalar(select(CostMovementBasis))
    original = basis.base_quantity
    basis.base_quantity = Decimal(999)
    with pytest.raises(core.InvalidOperation, match="integrity"):
        inventory_cost(
            session, business.tenant.id, business.item.id, review_id=result["review_id"]
        )
    assert basis in session.dirty
    basis.base_quantity = original
    session.flush()
    member = session.scalar(select(CostInventoryMember))
    session.delete(member)
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        inventory_cost(
            session, business.tenant.id, business.item.id, review_id=result["review_id"]
        )


def test_inventory_bounds_and_correction_without_replacement_is_normalized(
    session, business, cost_owner, monkeypatch
):
    args, _, issue = prepared(session, business, cost_owner)
    from reality.services import inventory_costing

    monkeypatch.setattr(inventory_costing, "MAX_MOVEMENTS", 1)
    with pytest.raises(core.InvalidOperation, match="bound"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )
    monkeypatch.setattr(inventory_costing, "MAX_MOVEMENTS", 100)
    core.correct_movement(session, business.tenant.id, issue.id, reason="Wrong issue")
    args["expected_event_sequence"] = receipt_cost(
        session, business.tenant.id, args["receipts"][0]["movement_id"]
    )["event_sequence"]
    args["economic_issue_ids"] = []
    preview = preview_cost_change(
        session, business.tenant.id, args, principal=Principal(cost_owner.id)
    )
    assert preview["review"]["remaining_quantity"] == "100.0000"
    assert preview["review"]["acquisition_value"] == "1050.0000"
    assert preview["review"]["consumption"] == []


def test_inventory_correction_replacement_is_the_only_effective_issue(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner, same_instant=True)
    correction = core.correct_movement(
        session,
        business.tenant.id,
        issue.id,
        reason="Correct shipped quantity",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "50",
            "from_location_id": business.location.id,
            "occurred_at": issue.occurred_at.isoformat(),
        },
    )
    args.update(
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        economic_issue_ids=[correction.replacement_movement_id],
    )

    action, result = commit_review(session, business, cost_owner, args)

    assert result["remaining_quantity"] == "50.0000"
    assert result["acquisition_value"] == "525.0000"
    assert result["consumption"][0]["movement_id"] == correction.replacement_movement_id
    assert result["consumption"][0]["cost"] == "525.0000"
    replay = approve_and_execute_proposal(
        session,
        business.tenant.id,
        action.id,
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    assert json.loads(replay.output) == result
    retained = record_by_id(session, MovementCorrection, correction.correction_id)
    retained.reason = "tampered"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="integrity"):
        inventory_cost(
            session,
            business.tenant.id,
            business.item.id,
            review_id=result["review_id"],
        )


def test_inventory_ownership_parts_follow_only_correction_replacement(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner, same_instant=True)
    correction = core.correct_movement(
        session,
        business.tenant.id,
        issue.id,
        reason="Correct partially owned shipment",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "50",
            "from_location_id": business.location.id,
            "occurred_at": issue.occurred_at.isoformat(),
        },
    )
    evidence_id = args["receipts"][0]["ownership_source_record_id"]
    args.update(
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        economic_issue_ids=[correction.replacement_movement_id],
        ownership_parts=[
            {
                "movement_id": receipt.id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence_id,
                "quantity": "70",
            },
            {
                "movement_id": receipt.id,
                "owner_party_id": business.supplier.id,
                "evidence_source_record_id": evidence_id,
                "quantity": "30",
            },
            {
                "movement_id": correction.replacement_movement_id,
                "owner_party_id": business.company.id,
                "evidence_source_record_id": evidence_id,
                "quantity": "50",
            },
        ],
        reason="Confirmed replacement-only ownership partition",
    )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["remaining_quantity"] == "20.0000"
    assert result["acquisition_value"] == "210.0000"
    assert result["consumption"][0]["movement_id"] == correction.replacement_movement_id
    assert result["consumption"][0]["cost"] == "525.0000"
    assert {row["movement_id"] for row in result["ownership_sources"]} == {
        receipt.id,
        correction.replacement_movement_id,
    }


def test_inventory_incomplete_correction_chain_refuses_atomically(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    correction = core.correct_movement(
        session, business.tenant.id, issue.id, reason="Wrong issue"
    )
    compensation = record_by_id(session, Movement, correction.compensating_movement_id)
    compensation.quantity = Decimal(59)
    session.flush()
    args.update(
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        economic_issue_ids=[],
    )

    with pytest.raises(core.InvalidOperation, match="correction chain"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_foreign_tenant_correction_chain_refuses_atomically(
    session, business, cost_owner
):
    _args, _receipt, issue = prepared(session, business, cost_owner)
    correction = core.correct_movement(
        session, business.tenant.id, issue.id, reason="Wrong issue"
    )
    # Moving the correction into another company used to be possible, and the
    # preview had to refuse the chain it then found. Since spec 181 FR-005 the
    # correction carries its company in every reference it makes, so the move
    # itself is refused — atomically, by the database, before any reader has to
    # reason about a chain that spans two companies.
    other = core.create_tenant(session, "Foreign correction owner")
    relation = record_by_id(session, MovementCorrection, correction.correction_id)
    with pytest.raises(IntegrityError), session.begin_nested():
        relation.tenant_id = other.id
        session.flush()


def test_inventory_corrected_customer_return_uses_replacement_identity(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    returned = core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    correction = core.correct_movement(
        session,
        business.tenant.id,
        returned.id,
        reason="Correct returned quantity",
        replacement={
            "type": "return",
            "item_id": business.item.id,
            "quantity": "5",
            "to_location_id": business.location.id,
            "occurred_at": returned.occurred_at.isoformat(),
        },
    )
    args.update(
        effective_at=core.now().isoformat(),
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        customer_return_ids=[correction.replacement_movement_id],
        return_parts=[
            {
                "movement_id": correction.replacement_movement_id,
                "issue_movement_id": issue.id,
                "entry_movement_id": receipt.id,
                "receipt_movement_id": receipt.id,
                "quantity": "5",
            }
        ],
    )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["returns"][0]["movement_id"] == correction.replacement_movement_id
    assert result["returns"][0]["cost"] == "-52.5000"
    assert result["remaining_quantity"] == "45.0000"


def test_inventory_corrected_receipt_requires_fresh_cost_and_ownership_evidence(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    core.correct_movement(
        session, business.tenant.id, issue.id, reason="Remove dependent issue"
    )
    correction = core.correct_movement(
        session,
        business.tenant.id,
        receipt.id,
        reason="Replace receipt identity",
        replacement={
            "type": "receipt",
            "item_id": business.item.id,
            "quantity": "100",
            "to_location_id": business.location.id,
            "occurred_at": receipt.occurred_at.isoformat(),
        },
    )
    replacement = record_by_id(session, Movement, correction.replacement_movement_id)
    args.update(
        expected_event_sequence=receipt_cost(
            session, business.tenant.id, replacement.id
        )["event_sequence"],
        economic_issue_ids=[],
    )
    with pytest.raises(core.InvalidOperation, match="Every receipt requires exact"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )

    ownership_source = None
    for amount, category in (
        ("1000", "goods"),
        ("100", "inbound_freight"),
        ("-50", "purchase_reduction"),
    ):
        document = fixtures.evidence(session, business, amount, "0")
        ownership_source = document.source_record_id
        fixtures.execute(
            session,
            business,
            cost_owner,
            fixtures.assignment(
                session, business, replacement, document, amount, category
            ),
        )
    settled = fixtures.review(
        session,
        business,
        cost_owner,
        replacement,
        {"goods", "inbound_freight", "purchase_reduction"},
    )
    args.update(
        expected_event_sequence=receipt_cost(
            session, business.tenant.id, replacement.id
        )["event_sequence"],
        receipts=[
            {
                "movement_id": replacement.id,
                "manifest_id": settled["manifest_id"],
                "ownership_source_record_id": ownership_source,
            }
        ],
    )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["remaining_quantity"] == "100.0000"
    assert result["acquisition_value"] == "1050.0000"
    assert result["receipt_sources"][0]["movement_id"] == replacement.id


def test_inventory_correction_can_explicitly_reclassify_replacement_as_loss(
    session, business, cost_owner
):
    args, receipt, issue = prepared(session, business, cost_owner)
    correction = core.correct_movement(
        session,
        business.tenant.id,
        issue.id,
        reason="Shipment was damaged stock",
        replacement={
            "type": "adjustment",
            "item_id": business.item.id,
            "quantity": "60",
            "from_location_id": business.location.id,
            "reason": "Confirmed damaged stock",
            "occurred_at": issue.occurred_at.isoformat(),
        },
    )
    args.update(
        expected_event_sequence=receipt_cost(session, business.tenant.id, receipt.id)[
            "event_sequence"
        ],
        economic_issue_ids=[],
        loss_movement_ids=[correction.replacement_movement_id],
    )

    _, result = commit_review(session, business, cost_owner, args)

    assert result["consumption"][0]["kind"] == "loss"
    assert result["consumption"][0]["cost"] == "630.0000"
    assert result["remaining_quantity"] == "40.0000"


def test_original_event_order_survives_simultaneous_movements_and_readmission(
    session, business, cost_owner, monkeypatch
):
    original_uid = core.uid
    movement_ids = iter(["mov_z_receipt", "mov_a_issue"])
    monkeypatch.setattr(
        core,
        "uid",
        lambda prefix: next(movement_ids) if prefix == "mov" else original_uid(prefix),
    )
    args, receipt, issue = prepared(session, business, cost_owner, same_instant=True)
    assert receipt.occurred_at == issue.occurred_at and issue.id < receipt.id
    _, first = commit_review(session, business, cost_owner, args)
    args["expected_event_sequence"] = first["event_sequence"]
    _, second = commit_review(session, business, cost_owner, args)
    assert first["acquisition_value"] == second["acquisition_value"] == "420.0000"
    assert second["consumption"][0]["cost"] == "630.0000"
    assert session.scalar(select(func.count()).select_from(CostMovementBasis)) == 2


def test_retained_unit_and_mcp_scope_after_master_data_change(
    session, business, cost_owner
):
    args, _, _ = prepared(session, business, cost_owner)
    command = MCP_TOOL_REGISTRY["cost_change_propose"]
    with caller(Principal(cost_owner.id)):
        proposal = command.handler(session, business.tenant.id, args)
    approved = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal["proposal_id"],
        confirming_principal=Principal(cost_owner.id),
        confirmed=True,
    )
    result = json.loads(approved.output)
    tool = MCP_TOOL_REGISTRY["cost_inventory_get"]
    assert (
        tool.handler(session, business.tenant.id, {"item_id": business.item.id})
        == result
    )
    core.update_item(
        session,
        business.tenant.id,
        business.item.id,
        business.item.sku,
        business.item.name,
        "box",
    )
    assert (
        tool.handler(session, business.tenant.id, {"item_id": business.item.id})[
            "review_state"
        ]
        == "stale"
    )
    old = tool.handler(
        session,
        business.tenant.id,
        {"item_id": business.item.id, "review_id": result["review_id"]},
    )
    assert (
        old["base_unit"] == args["base_unit"] and old["acquisition_value"] == "420.0000"
    )


def test_missing_original_event_or_ownership_evidence_cannot_be_admitted(
    session, business, cost_owner
):
    args, movement, _ = prepared(session, business, cost_owner)
    args["receipts"][0]["ownership_source_record_id"] = "not-held"
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )
    from reality.db.core import BusinessEvent

    original = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.subject_id == movement.id,
            BusinessEvent.event_type == "movement.recorded",
        )
    )
    original.event_type = "fixture.missing_recorded_event"
    session.flush()
    source = fixtures.evidence(session, business, "0", "0")
    args["receipts"][0]["ownership_source_record_id"] = source.source_record_id
    args["expected_event_sequence"] = receipt_cost(
        session, business.tenant.id, movement.id
    )["event_sequence"]
    with pytest.raises(core.InvalidOperation, match="exact recorded event"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_refuses_held_movements_before_zero_opening(
    session, business, cost_owner
):
    args, movement, _ = prepared(session, business, cost_owner)
    args["history_start"] = (
        movement.occurred_at + timedelta(microseconds=1)
    ).isoformat()
    with pytest.raises(core.InvalidOperation, match="empty opening"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_unsupported_return_is_not_silently_omitted(
    session, business, cost_owner
):
    args, movement, _ = prepared(session, business, cost_owner)
    core.record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        "1",
        to_location_id=business.location.id,
    )
    args["effective_at"] = core.now().isoformat()
    args["expected_event_sequence"] = receipt_cost(
        session, business.tenant.id, movement.id
    )["event_sequence"]
    with pytest.raises(core.InvalidOperation, match="unsupported movement"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_admission_refuses_old_repeatable_read_snapshot(
    session, business, cost_owner, monkeypatch
):
    from types import SimpleNamespace

    args, _, _ = prepared(session, business, cost_owner)
    monkeypatch.setattr(
        session,
        "connection",
        lambda: SimpleNamespace(get_isolation_level=lambda: "REPEATABLE READ"),
    )
    with pytest.raises(core.InvalidOperation, match="READ COMMITTED"):
        preview_cost_change(
            session, business.tenant.id, args, principal=Principal(cost_owner.id)
        )


def test_inventory_read_does_not_enumerate_live_movement_history(
    session, business, cost_owner
):
    from sqlalchemy import event

    args, _, _ = prepared(session, business, cost_owner)
    commit_review(session, business, cost_owner, args)
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        result = inventory_cost(session, business.tenant.id, business.item.id)
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert result["acquisition_value"] == "420.0000"
    assert not any(
        s.lstrip().startswith(("insert", "update", "delete")) for s in statements
    )
    movement_reads = [
        s for s in statements if "from movement " in s or "from movement\n" in s
    ]
    assert all(
        "movement.id =" in s and "movement.item_id =" not in s for s in movement_reads
    )


def test_inventory_cutoff_offsets_are_canonical_and_foreign_review_is_hidden(
    session, business, cost_owner
):
    from datetime import datetime, timezone

    from sqlalchemy.exc import IntegrityError

    args, _, _ = prepared(session, business, cost_owner)
    for key in ("history_start", "effective_at"):
        args[key] = (
            datetime.fromisoformat(args[key])
            .astimezone(timezone(timedelta(hours=2)))
            .isoformat()
        )
    _, result = commit_review(session, business, cost_owner, args)
    assert result["effective_at"].endswith("+00:00")
    assert inventory_cost(session, business.tenant.id, business.item.id) == result
    other = core.create_tenant(session, "Other reviewed inventory")
    item = core.create_item(session, other.id, "other", "Other item", "piece")
    with pytest.raises(core.NotFound):
        MCP_TOOL_REGISTRY["cost_inventory_get"].handler(
            session, other.id, {"item_id": item.id, "review_id": result["review_id"]}
        )
    basis = session.scalar(
        select(CostMovementBasis).where(
            CostMovementBasis.tenant_id == business.tenant.id
        )
    )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            CostInventoryMember(
                id=core.uid("cst"),
                tenant_id=other.id,
                review_id=result["review_id"],
                movement_basis_id=basis.id,
                kind="issue",
            )
        )
        session.flush()
