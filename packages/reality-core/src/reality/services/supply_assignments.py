"""Tenant-scoped statements connecting supplier supply to demand or stock."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reality.db.core import Commitment, SupplyAssignment, uid
from reality.domain.supply import (
    assignable_demand_quantity,
    available_assignment_quantity,
    validate_assignment_quantity,
)
from reality.services import core


def _decimal(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise core.InvalidOperation(
            "Supply assignment quantity must be a decimal."
        ) from error
    if not result.is_finite() or result != result.quantize(Decimal("0.0001")):
        raise core.InvalidOperation(
            "Supply assignment quantity must fit four decimal places without rounding."
        )
    return result


def _effective_rows(
    session: Session,
    tenant_id: str,
    *,
    supplier_id: str | None = None,
    customer_id: str | None = None,
) -> list[SupplyAssignment]:
    query = select(SupplyAssignment).where(SupplyAssignment.tenant_id == tenant_id)
    if supplier_id:
        query = query.where(SupplyAssignment.supplier_commitment_id == supplier_id)
    if customer_id:
        query = query.where(SupplyAssignment.customer_commitment_id == customer_id)
    rows = list(
        session.scalars(
            query.order_by(SupplyAssignment.created_at, SupplyAssignment.id)
        )
    )
    reversed_quantities = {
        identity: _decimal(value)
        for identity, value in session.execute(
            select(
                SupplyAssignment.reverses_assignment_id,
                func.sum(SupplyAssignment.quantity),
            )
            .where(
                SupplyAssignment.tenant_id == tenant_id,
                SupplyAssignment.reverses_assignment_id.is_not(None),
            )
            .group_by(SupplyAssignment.reverses_assignment_id)
        )
    }
    # A cancelled promise on either side ends the assignment: a promise that is off
    # neither needs supply nor gives any. The statement itself stays as it was said.
    cancelled = set(
        session.scalars(
            select(Commitment.id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.status == "cancelled",
                Commitment.id.in_(
                    {row.supplier_commitment_id for row in rows}
                    | {
                        row.customer_commitment_id
                        for row in rows
                        if row.customer_commitment_id
                    }
                ),
            )
        )
    )
    return [
        row
        for row in rows
        if row.reverses_assignment_id is None
        and row.quantity > reversed_quantities.get(row.id, Decimal(0))
        and row.supplier_commitment_id not in cancelled
        and row.customer_commitment_id not in cancelled
    ]


def supply_coverage(
    session: Session,
    tenant_id: str,
    *,
    supplier_commitment_id: str | None = None,
    customer_commitment_id: str | None = None,
) -> dict[str, Any]:
    supplier = (
        core._tenant_record(session, Commitment, tenant_id, supplier_commitment_id)
        if supplier_commitment_id
        else None
    )
    customer = (
        core._tenant_record(session, Commitment, tenant_id, customer_commitment_id)
        if customer_commitment_id
        else None
    )
    if supplier and supplier.type != "supplier_delivery":
        raise core.InvalidOperation("Supply coverage requires a supplier commitment.")
    if customer and customer.type != "customer_delivery":
        raise core.InvalidOperation("Demand coverage requires a customer commitment.")
    rows = _effective_rows(
        session,
        tenant_id,
        supplier_id=supplier_commitment_id,
        customer_id=customer_commitment_id,
    )
    reversals = {
        identity: _decimal(value)
        for identity, value in session.execute(
            select(
                SupplyAssignment.reverses_assignment_id,
                func.sum(SupplyAssignment.quantity),
            )
            .where(
                SupplyAssignment.tenant_id == tenant_id,
                SupplyAssignment.reverses_assignment_id.is_not(None),
            )
            .group_by(SupplyAssignment.reverses_assignment_id)
        )
    }
    items = []
    for row in rows:
        effective = row.quantity - reversals.get(row.id, Decimal(0))
        items.append(
            {
                "id": row.id,
                "supplier_commitment_id": row.supplier_commitment_id,
                "customer_commitment_id": row.customer_commitment_id,
                "purpose": row.purpose,
                "quantity": effective,
                "source_record_id": row.source_record_id,
            }
        )
    result: dict[str, Any] = {"items": items}
    if supplier:
        terms = core.commitment_terms(session, tenant_id, [supplier.id])[supplier.id]
        assigned = sum((item["quantity"] for item in items), Decimal(0))
        result["supplier"] = {
            "commitment_id": supplier.id,
            "quantity": terms.quantity,
            "received": terms.fulfilled,
            "open": terms.open,
            "customer_assigned": sum(
                item["quantity"]
                for item in items
                if item["purpose"] == "customer_demand"
            ),
            "stock_replenishment": sum(
                item["quantity"]
                for item in items
                if item["purpose"] == "stock_replenishment"
            ),
            "unassigned": available_assignment_quantity(terms.quantity, assigned),
        }
    if customer:
        terms = core.commitment_terms(session, tenant_id, [customer.id])[customer.id]
        result["customer"] = {
            "commitment_id": customer.id,
            "quantity": terms.quantity,
            "delivered": terms.fulfilled,
            "open": terms.open,
            "protecting_supply": sum(
                item["quantity"]
                for item in items
                if item["purpose"] == "customer_demand"
            ),
        }
    return result


def preview_supply_assignment(
    session: Session,
    tenant_id: str,
    supplier_commitment_id: str,
    quantity: Decimal | str,
    *,
    purpose: str,
    customer_commitment_id: str | None = None,
) -> dict[str, Any]:
    if purpose not in {"customer_demand", "stock_replenishment"}:
        raise core.InvalidOperation("Unsupported supply assignment purpose.")
    if (purpose == "customer_demand") != bool(customer_commitment_id):
        raise core.InvalidOperation(
            "Customer demand requires one customer commitment; stock replenishment requires none."
        )
    qty = _decimal(quantity)
    supplier = core._tenant_record(
        session, Commitment, tenant_id, supplier_commitment_id
    )
    if supplier.type != "supplier_delivery" or supplier.status != "open":
        raise core.InvalidOperation("Select an open supplier commitment.")
    customer = None
    if customer_commitment_id:
        customer = core._tenant_record(
            session, Commitment, tenant_id, customer_commitment_id
        )
        if customer.type != "customer_delivery" or customer.status != "open":
            raise core.InvalidOperation("Select an open customer commitment.")
        if supplier.item_id != customer.item_id:
            raise core.InvalidOperation("Supply and demand items must match.")
        if (
            supplier.location_id
            and customer.location_id
            and supplier.location_id != customer.location_id
        ):
            raise core.InvalidOperation("Supply and demand locations must match.")
    supplier_view = supply_coverage(
        session, tenant_id, supplier_commitment_id=supplier.id
    )["supplier"]
    customer_view = (
        supply_coverage(session, tenant_id, customer_commitment_id=customer.id)[
            "customer"
        ]
        if customer
        else None
    )
    try:
        validate_assignment_quantity(
            qty,
            supplier_view["unassigned"],
            assignable_demand_quantity(
                customer_view["quantity"],
                customer_view["open"],
                customer_view["protecting_supply"],
            )
            if customer_view
            else None,
        )
    except ValueError as error:
        raise core.InvalidOperation(str(error)) from error
    return {
        "supplier_commitment_id": supplier.id,
        "customer_commitment_id": customer.id if customer else None,
        "purpose": purpose,
        "quantity": qty,
        "supplier_before": supplier_view,
        "customer_before": customer_view,
        "supplier_after": {
            **supplier_view,
            "customer_assigned": supplier_view["customer_assigned"]
            + (qty if purpose == "customer_demand" else Decimal(0)),
            "stock_replenishment": supplier_view["stock_replenishment"]
            + (qty if purpose == "stock_replenishment" else Decimal(0)),
            "unassigned": supplier_view["unassigned"] - qty,
        },
    }


def assign_supply(
    session: Session,
    tenant_id: str,
    supplier_commitment_id: str,
    quantity: Decimal | str,
    *,
    purpose: str,
    customer_commitment_id: str | None = None,
    request_id: str,
    _commit: bool = True,
) -> SupplyAssignment:
    core._require_business_mutation(session, tenant_id, "assign_supply")
    if purpose not in {"customer_demand", "stock_replenishment"}:
        raise core.InvalidOperation("Unsupported supply assignment purpose.")
    if (purpose == "customer_demand") != bool(customer_commitment_id):
        raise core.InvalidOperation(
            "Customer demand requires one customer commitment; stock replenishment requires none."
        )
    qty = _decimal(quantity)
    with session.begin_nested():
        supplier = session.scalar(
            select(Commitment)
            .where(
                Commitment.tenant_id == tenant_id,
                Commitment.id == supplier_commitment_id,
            )
            .with_for_update()
        )
        if supplier is None:
            raise core.NotFound("Supplier commitment was not found.")
        if supplier.type != "supplier_delivery" or supplier.status != "open":
            raise core.InvalidOperation("Select an open supplier commitment.")
        customer = None
        if customer_commitment_id:
            customer = session.scalar(
                select(Commitment)
                .where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.id == customer_commitment_id,
                )
                .with_for_update()
            )
            if customer is None:
                raise core.NotFound("Customer commitment was not found.")
            if customer.type != "customer_delivery" or customer.status != "open":
                raise core.InvalidOperation("Select an open customer commitment.")
            if supplier.item_id != customer.item_id:
                raise core.InvalidOperation("Supply and demand items must match.")
            if (
                supplier.location_id
                and customer.location_id
                and supplier.location_id != customer.location_id
            ):
                raise core.InvalidOperation("Supply and demand locations must match.")
        existing_source = session.scalar(
            select(core.SourceRecord).where(
                core.SourceRecord.tenant_id == tenant_id,
                core.SourceRecord.source_system == "manual",
                core.SourceRecord.source_type == "supply_assignment",
                core.SourceRecord.external_id == request_id,
            )
        )
        if existing_source:
            existing = session.scalar(
                select(SupplyAssignment).where(
                    SupplyAssignment.tenant_id == tenant_id,
                    SupplyAssignment.source_record_id == existing_source.id,
                )
            )
            if existing:
                stated = existing_source.payload
                expected = {
                    "supplier_commitment_id": supplier.id,
                    "customer_commitment_id": customer.id if customer else None,
                    "purpose": purpose,
                    "quantity": str(qty),
                }
                if json.loads(stated) != expected:
                    raise core.InvalidOperation(
                        "Request identity already belongs to another supply assignment."
                    )
                return existing
        preview_supply_assignment(
            session,
            tenant_id,
            supplier.id,
            qty,
            purpose=purpose,
            customer_commitment_id=customer.id if customer else None,
        )
        payload = {
            "supplier_commitment_id": supplier.id,
            "customer_commitment_id": customer.id if customer else None,
            "purpose": purpose,
            "quantity": str(qty),
        }
        source = core.create_master_source_record(
            session,
            tenant_id,
            "supply_assignment",
            "manual",
            request_id,
            payload,
            _commit=False,
        )
        row = SupplyAssignment(
            id=uid("sas"),
            tenant_id=tenant_id,
            supplier_commitment_id=supplier.id,
            customer_commitment_id=customer.id if customer else None,
            purpose=purpose,
            quantity=qty,
            source_record_id=source.id,
        )
        session.add(row)
        session.flush()
    if _commit:
        session.commit()
    return row


def reverse_supply_assignment(
    session: Session,
    tenant_id: str,
    assignment_id: str,
    quantity: Decimal | str,
    *,
    reason: str,
    request_id: str,
) -> SupplyAssignment:
    """Append a partial or full reversal without rewriting the stated assignment."""
    core._require_business_mutation(session, tenant_id, "reverse_supply_assignment")
    qty = _decimal(quantity)
    stated_reason = reason.strip()
    if qty <= 0 or not stated_reason:
        raise core.InvalidOperation("A positive reversal and reason are required.")
    with session.begin_nested():
        original = session.scalar(
            select(SupplyAssignment)
            .where(
                SupplyAssignment.tenant_id == tenant_id,
                SupplyAssignment.id == assignment_id,
            )
            .with_for_update()
        )
        if original is None or original.reverses_assignment_id is not None:
            raise core.NotFound("Effective supply assignment was not found.")
        existing_source = session.scalar(
            select(core.SourceRecord).where(
                core.SourceRecord.tenant_id == tenant_id,
                core.SourceRecord.source_system == "manual",
                core.SourceRecord.source_type == "supply_assignment_reversal",
                core.SourceRecord.external_id == request_id,
            )
        )
        if existing_source:
            existing = session.scalar(
                select(SupplyAssignment).where(
                    SupplyAssignment.tenant_id == tenant_id,
                    SupplyAssignment.source_record_id == existing_source.id,
                )
            )
            if existing:
                return existing
        reversed_quantity = _decimal(
            session.scalar(
                select(func.coalesce(func.sum(SupplyAssignment.quantity), 0)).where(
                    SupplyAssignment.tenant_id == tenant_id,
                    SupplyAssignment.reverses_assignment_id == original.id,
                )
            )
            or 0
        )
        if qty > original.quantity - reversed_quantity:
            raise core.InvalidOperation(
                "Supply assignment reversal exceeds its effective quantity."
            )
        payload = {
            "assignment_id": original.id,
            "quantity": str(qty),
            "reason": stated_reason,
        }
        source = core.create_master_source_record(
            session,
            tenant_id,
            "supply_assignment_reversal",
            "manual",
            request_id,
            payload,
            _commit=False,
        )
        reversal = SupplyAssignment(
            id=uid("sas"),
            tenant_id=tenant_id,
            supplier_commitment_id=original.supplier_commitment_id,
            customer_commitment_id=original.customer_commitment_id,
            purpose=original.purpose,
            quantity=qty,
            source_record_id=source.id,
            reverses_assignment_id=original.id,
        )
        session.add(reversal)
        session.flush()
    session.commit()
    return reversal
