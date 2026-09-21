"""T087 weighted allocation uses the existing confirmed costing boundary."""

from decimal import Decimal

import pytest
import test_contribution_reviews as revenue
import test_costing_services as costs
from sqlalchemy import select

from reality.db.contribution import CostSellingPart
from reality.db.core import TenantMembership
from reality.db.costing import CostAttributionPart
from reality.services import core
from reality.services.analytics.reports import caller
from reality.services.costing import preview_cost_change
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)

cost_owner = costs.cost_owner


def weighted(session, business, movements, document, **changes):
    context = costs.cost_evidence(session, business.tenant.id, document.id)
    arguments = {
        "operation": "allocate",
        "document_id": document.id,
        "expected_event_sequence": context["event_sequence"],
        "expected_evidence_hash": context["evidence_hash"],
        "basis": "net",
        "selected_basis_tax_inclusion": "excluded",
        "tax_treatment": "recoverable",
        "nonrecoverable_tax_amount": "0",
        "allocation_total": "100",
        "category": "inbound_freight",
        "cost_effect": 1,
        "amount_bucket": "selected_basis",
        "driver_kind": "manual",
        "targets": [
            {"movement_id": movements[0].id, "weight": "1"},
            {"movement_id": movements[1].id, "weight": "3"},
        ],
        "reason": "Allocate evidenced freight by reviewed weights",
    }
    arguments.update(changes)
    return arguments


def test_weighted_preview_and_confirmation_retain_exact_existing_parts(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    document = costs.evidence(session, business, "100", "0")
    arguments = weighted(session, business, movements, document)

    preview = preview_cost_change(
        session,
        business.tenant.id,
        arguments,
        principal=Principal(cost_owner.id),
    )
    assert preview["review"]["assigned_effect"] == "100.0000"
    assert preview["review"]["unassigned_basis"] == "0.0000"
    assert preview["review"]["allocation"] == {
        "driver_kind": "manual",
        "shares": [
            {"movement_id": movements[0].id, "source_share": "25.0000", "weight": "1"},
            {"movement_id": movements[1].id, "source_share": "75.0000", "weight": "3"},
        ],
    }

    result = costs.execute(session, business, cost_owner, arguments)
    assert result["assigned_effect"] == "100.0000"
    parts = session.scalars(
        select(CostAttributionPart).order_by(CostAttributionPart.receipt_basis_id)
    ).all()
    assert sorted(part.source_share for part in parts) == [
        Decimal("25.0000"),
        Decimal("75.0000"),
    ]
    assert {part.assignment_kind for part in parts} == {"allocated"}


def test_quantity_and_equal_drivers_ignore_caller_weights(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    document = costs.evidence(session, business, "10", "0")
    arguments = weighted(
        session,
        business,
        movements,
        document,
        allocation_total="10",
        driver_kind="equal",
        targets=[{"movement_id": movement.id} for movement in movements],
    )
    preview = preview_cost_change(
        session,
        business.tenant.id,
        arguments,
        principal=Principal(cost_owner.id),
    )
    assert [
        row["source_share"] for row in preview["review"]["allocation"]["shares"]
    ] == [
        "5.0000",
        "5.0000",
    ]

    arguments["driver_kind"] = "quantity"
    preview = preview_cost_change(
        session,
        business.tenant.id,
        arguments,
        principal=Principal(cost_owner.id),
    )
    assert [row["weight"] for row in preview["review"]["allocation"]["shares"]] == [
        "100.0000",
        "100.0000",
    ]


def test_weighted_allocation_refuses_invalid_driver_tax_and_foreign_target(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    document = costs.evidence(session, business, "100", "19")
    arguments = weighted(session, business, movements, document)
    arguments["targets"][0].pop("weight")
    with pytest.raises(core.InvalidOperation, match="manual"):
        preview_cost_change(
            session,
            business.tenant.id,
            arguments,
            principal=Principal(cost_owner.id),
        )

    arguments = weighted(
        session,
        business,
        movements,
        document,
        amount_bucket="nonrecoverable_tax",
        category="nonrecoverable_tax",
        nonrecoverable_tax_amount="19",
    )
    with pytest.raises(core.InvalidOperation, match="exceeds"):
        preview_cost_change(
            session,
            business.tenant.id,
            arguments,
            principal=Principal(cost_owner.id),
        )

    arguments = weighted(session, business, movements, document)
    arguments["targets"][0]["movement_id"] = "mov_foreign_or_missing"
    with pytest.raises(core.NotFound):
        preview_cost_change(
            session,
            business.tenant.id,
            arguments,
            principal=Principal(cost_owner.id),
        )


def test_weighted_selling_allocation_uses_exact_existing_selling_parts(
    session, business, cost_owner
):
    _, data = revenue.prepared(session, business, cost_owner)
    document = costs.evidence(session, business, "30", "0")
    context = costs.cost_evidence(session, business.tenant.id, document.id)
    arguments = {
        "operation": "selling_allocate",
        "document_id": document.id,
        "expected_event_sequence": context["event_sequence"],
        "expected_evidence_hash": context["evidence_hash"],
        "tax_treatment": "recoverable",
        "selling_expense_confirmed": True,
        "allocation_total": "30",
        "driver_kind": "manual",
        "targets": [
            {
                "document_line_id": data[0].id,
                "category": "outbound_freight",
                "weight": "1",
            },
            {
                "document_line_id": data[0].id,
                "category": "payment_fee",
                "weight": "2",
            },
        ],
        "reason": "Allocate evidenced selling cost by reviewed weights",
    }
    preview = preview_cost_change(
        session,
        business.tenant.id,
        arguments,
        principal=Principal(cost_owner.id),
    )
    assert [
        row["source_share"] for row in preview["review"]["allocation"]["shares"]
    ] == [
        "10.0000",
        "20.0000",
    ]
    result = costs.execute(session, business, cost_owner, arguments)
    assert result["assigned_effect"] == "30.0000"
    parts = session.scalars(select(CostSellingPart)).all()
    assert sorted(part.source_share for part in parts) == [
        Decimal("10.0000"),
        Decimal("20.0000"),
    ]
    assert {part.assignment_kind for part in parts} == {"allocated"}


def test_weighted_proposal_rechecks_staleness_and_owner_at_confirmation(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    document = costs.evidence(session, business, "100", "0")
    arguments = weighted(session, business, movements, document)
    principal = Principal(cost_owner.id)
    with caller(principal):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", arguments
        )
    core.emit_business_event(
        session,
        business.tenant.id,
        "source_record.stored",
        "source_record",
        "later_cost_evidence",
        {},
    )
    with pytest.raises(core.Conflict, match="stale"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=principal,
            confirmed=True,
        )

    arguments = weighted(session, business, movements, document)
    with caller(principal):
        proposal = create_change_proposal(
            session, business.tenant.id, "cost.change", arguments
        )
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == cost_owner.id,
        )
    )
    membership.role = "member"
    session.flush()
    with pytest.raises(core.InvalidOperation, match="owner"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=principal,
            confirmed=True,
        )


def test_payment_difference_is_not_admitted_as_skonto_evidence(
    session, business, cost_owner
):
    movements = [costs.receipt(session, business), costs.receipt(session, business)]
    document = costs.evidence(session, business, "-10", "0", "supplier_credit_note")
    arguments = weighted(
        session,
        business,
        movements,
        document,
        allocation_total="-10",
        category="purchase_reduction",
        cost_effect=-1,
    )
    arguments["payment_difference"] = "-10"
    with pytest.raises(core.InvalidOperation, match="extra"):
        preview_cost_change(
            session,
            business.tenant.id,
            arguments,
            principal=Principal(cost_owner.id),
        )
