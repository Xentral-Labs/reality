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
    other_item = core.create_item(session, business.tenant.id, "OTHER", "Other item")
    mismatched = core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        other_item.id,
        business.location.id,
        "1",
        "2026-09-21",
    )
    with pytest.raises(core.InvalidOperation, match="items must match"):
        assign_supply(
            session,
            business.tenant.id,
            supplier.id,
            "1",
            purpose="customer_demand",
            customer_commitment_id=mismatched.id,
            request_id="wrong-item",
        )


def test_assignments_together_never_protect_more_than_the_demand(session, business):
    """FR-009: the total, not each statement, stays within the customer's demand."""
    customer, supplier = commitments(session, business)
    second = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        "PO-SUPPLY-002",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "10",
                "gross_amount": "100",
            }
        ],
        "100",
        document_date="2026-09-21",
    )[3][0]

    def assign(supply, quantity, request_id):
        return assign_supply(
            session,
            business.tenant.id,
            supply.id,
            quantity,
            purpose="customer_demand",
            customer_commitment_id=customer.id,
            request_id=request_id,
        )

    first = assign(supplier, "5", "demand-first")
    with pytest.raises(core.InvalidOperation, match="exceeds open customer"):
        assign(supplier, "4", "demand-same-supplier-over")
    with pytest.raises(core.InvalidOperation, match="exceeds open customer"):
        assign(second, "4", "demand-second-supplier-over")
    assign(second, "3", "demand-second-supplier")
    demand = supply_coverage(
        session, business.tenant.id, customer_commitment_id=customer.id
    )["customer"]
    assert demand["open"] == Decimal(8)
    assert demand["protecting_supply"] == Decimal(8)
    with pytest.raises(core.InvalidOperation, match="exceeds open customer"):
        assign(second, "1", "demand-fully-protected")

    reverse_supply_assignment(
        session,
        business.tenant.id,
        first.id,
        "2",
        reason="Supplier cannot deliver all",
        request_id="demand-freed",
    )
    assign(second, "2", "demand-reassigned")
    assert supply_coverage(
        session, business.tenant.id, customer_commitment_id=customer.id
    )["customer"]["protecting_supply"] == Decimal(8)


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
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

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


def test_concurrent_assignments_cannot_exceed_supplier_quantity(postgres_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace

    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Base, SupplyAssignment, build_engine

    engine = build_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = core.create_tenant(session, "Concurrent supply")
            company = core.create_party(session, tenant.id, "Company", "company")
            customer_party = core.create_party(
                session, tenant.id, "Customer", "customer"
            )
            supplier_party = core.create_party(
                session, tenant.id, "Supplier", "supplier"
            )
            item = core.create_item(session, tenant.id, "SKU", "Item")
            location = core.create_location(session, tenant.id, "Warehouse")
            business = SimpleNamespace(
                tenant=tenant,
                company=company,
                customer=customer_party,
                supplier=supplier_party,
                item=item,
                location=location,
            )
            first_customer, supplier = commitments(session, business)
            second_customer = core.create_commitment(
                session,
                tenant.id,
                "customer_delivery",
                company.id,
                customer_party.id,
                item.id,
                location.id,
                "8",
                "2026-09-21",
            )
            tenant_id = tenant.id
            supplier_id = supplier.id
            customer_ids = [first_customer.id, second_customer.id]
        gate = Barrier(2)

        def execute(index: int) -> bool:
            with factory() as connection:
                gate.wait(timeout=10)
                try:
                    assign_supply(
                        connection,
                        tenant_id,
                        supplier_id,
                        "7",
                        purpose="customer_demand",
                        customer_commitment_id=customer_ids[index],
                        request_id=f"concurrent-assignment-{index}",
                    )
                    return True
                except core.InvalidOperation as error:
                    assert "exceeds unassigned supplier quantity" in str(error)
                    return False

        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(execute, range(2))) == [False, True]
        with factory() as session:
            assert session.scalar(
                select(func.sum(SupplyAssignment.quantity)).where(
                    SupplyAssignment.tenant_id == tenant_id,
                    SupplyAssignment.reverses_assignment_id.is_(None),
                )
            ) == Decimal(7)
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
