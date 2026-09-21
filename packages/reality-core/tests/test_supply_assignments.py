from decimal import Decimal

import pytest
from reality.services import core
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
)
from reality.services.supply_assignments import (
    assign_supply,
    reverse_supply_assignment,
    supply_coverage,
)
from reality.tools.application import approve_and_execute_proposal, run_read_tool


def commitments(session, business):
    sales = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-SUPPLY-001",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "8",
                "unit_price": "20",
                "gross_amount": "160",
            }
        ],
        "160",
        document_date="2026-09-21",
    )[3][0]
    purchase = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        "PO-SUPPLY-001",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "12",
                "unit_price": "10",
                "gross_amount": "120",
            }
        ],
        "120",
        document_date="2026-09-21",
    )[3][0]
    return sales, purchase


def test_customer_and_stock_supply_reconcile_without_implying_receipt(
    session, business
):
    customer, supplier = commitments(session, business)
    customer_row = assign_supply(
        session,
        business.tenant.id,
        supplier.id,
        "7",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="assign-customer-001",
    )
    assign_supply(
        session,
        business.tenant.id,
        supplier.id,
        "3",
        purpose="stock_replenishment",
        request_id="assign-stock-001",
    )
    result = supply_coverage(
        session, business.tenant.id, supplier_commitment_id=supplier.id
    )["supplier"]
    assert result == {
        "commitment_id": supplier.id,
        "quantity": Decimal(12),
        "received": Decimal(0),
        "open": Decimal(12),
        "customer_assigned": Decimal(7),
        "stock_replenishment": Decimal(3),
        "unassigned": Decimal(2),
    }
    assert supply_coverage(
        session, business.tenant.id, customer_commitment_id=customer.id
    )["customer"]["protecting_supply"] == Decimal(7)
    assert (
        assign_supply(
            session,
            business.tenant.id,
            supplier.id,
            "7",
            purpose="customer_demand",
            customer_commitment_id=customer.id,
            request_id="assign-customer-001",
        ).id
        == customer_row.id
    )


def test_supply_assignment_enforces_bounds_shape_and_tenant(session, business):
    customer, supplier = commitments(session, business)
    with pytest.raises(core.InvalidOperation, match="exceeds open customer"):
        assign_supply(
            session,
            business.tenant.id,
            supplier.id,
            "9",
            purpose="customer_demand",
            customer_commitment_id=customer.id,
            request_id="too-much-demand",
        )
    with pytest.raises(core.InvalidOperation, match="requires none"):
        assign_supply(
            session,
            business.tenant.id,
            supplier.id,
            "1",
            purpose="stock_replenishment",
            customer_commitment_id=customer.id,
            request_id="wrong-shape",
        )
    foreign = core.create_tenant(session, "Foreign supply")
    with pytest.raises(core.NotFound):
        assign_supply(
            session,
            foreign.id,
            supplier.id,
            "1",
            purpose="stock_replenishment",
            request_id="foreign",
        )


def test_partial_reversal_is_append_only_and_idempotent(session, business):
    customer, supplier = commitments(session, business)
    assignment = assign_supply(
        session,
        business.tenant.id,
        supplier.id,
        "6",
        purpose="customer_demand",
        customer_commitment_id=customer.id,
        request_id="assignment-to-reverse",
    )
    reversal = reverse_supply_assignment(
        session,
        business.tenant.id,
        assignment.id,
        "2",
        reason="Customer reduced demand",
        request_id="assignment-reversal",
    )
    assert reversal.reverses_assignment_id == assignment.id
    assert assignment.quantity == Decimal(6)
    assert supply_coverage(
        session, business.tenant.id, supplier_commitment_id=supplier.id
    )["supplier"]["customer_assigned"] == Decimal(4)
    assert (
        reverse_supply_assignment(
            session,
            business.tenant.id,
            assignment.id,
            "2",
            reason="Customer reduced demand",
            request_id="assignment-reversal",
        ).id
        == reversal.id
    )
    with pytest.raises(core.InvalidOperation, match="exceeds"):
        reverse_supply_assignment(
            session,
            business.tenant.id,
            assignment.id,
            "5",
            reason="Too much",
            request_id="assignment-over-reversal",
        )


def test_supply_assignment_requires_current_review_and_replays(session, business):
    customer, supplier = commitments(session, business)
    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "supply_assign",
        {
            "supplier_commitment_id": supplier.id,
            "customer_commitment_id": customer.id,
            "purpose": "customer_demand",
            "quantity": "5",
        },
        request_id="reviewed-assignment",
    )
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["status"] == "proposed"
    assert detail["review"]["effect"] == {
        "assigned": "5",
        "purpose": "customer_demand",
        "unassigned_after": "7",
    }
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=detail["review"]["token"],
        confirmed=True,
    )
    assert executed.status == "executed"
    verified = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert verified["verification"] == "verified"
    assert verified["observation"]["supplier"]["customer_assigned"] == Decimal(5)
    assert (
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            review_token=detail["review"]["token"],
            confirmed=True,
        ).id
        == proposal.id
    )


def test_supply_assignment_http_and_shared_read_use_same_services(session, business):
    from fastapi.testclient import TestClient
    from reality.web.api import database_session
    from reality.web.app import app
    from sqlalchemy.orm import sessionmaker

    customer, supplier = commitments(session, business)
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            prepared = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "supply_assign",
                    "request_id": "http-supply-assignment",
                    "arguments": {
                        "supplier_commitment_id": supplier.id,
                        "customer_commitment_id": customer.id,
                        "purpose": "customer_demand",
                        "quantity": "4",
                    },
                },
            )
            assert prepared.status_code == 200, prepared.text
            preview = prepared.json()
            confirmed = client.post(
                f"{base}/change-proposals/{preview['id']}/approve",
                json={
                    "confirmed": True,
                    "review_token": preview["review"]["token"],
                },
            )
            assert confirmed.status_code == 200, confirmed.text
            response = client.get(
                f"{base}/supply-coverage",
                params={"supplier_commitment_id": supplier.id},
            )
            assert response.status_code == 200, response.text
            assert Decimal(
                str(response.json()["supplier"]["customer_assigned"])
            ) == Decimal("4.0000")
    finally:
        app.dependency_overrides.clear()
    shared = run_read_tool(
        session,
        business.tenant.id,
        "supply_coverage",
        {"supplier_commitment_id": supplier.id},
    )
    assert Decimal(shared["supplier"]["customer_assigned"]) == Decimal(4)
