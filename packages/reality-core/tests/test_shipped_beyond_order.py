"""Spec 313 FR-002: a line lowered below what was shipped reports the excess."""

from decimal import Decimal

from reality.services import core
from reality.services.exceptions import operational_exceptions


def _order(session, business, number, quantity="10"):
    _, _, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(Decimal(quantity) * 10),
            }
        ],
        str(Decimal(quantity) * 10),
    )
    return promise


def _ship(session, business, promise, quantity):
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=promise.id,
    )


def _beyond(session, business):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == "shipped_beyond_order"
    }


def test_a_line_lowered_below_what_shipped_is_reported(session, business):
    promise = _order(session, business, "SO-313-1")
    _ship(session, business, promise, "6")
    # Positive control: part of the order shipped is not beyond it.
    assert promise.id not in _beyond(session, business)

    core.revise_commitment(session, business.tenant.id, promise.id, quantity="4")

    finding = _beyond(session, business)[promise.id]
    assert finding.causal_values["excess_quantity"] == 2
    assert finding.causal_values["quantity_in_force"] == 4
    assert finding.causal_values["shipped_quantity"] == 6


def test_it_clears_by_a_return_or_a_revision_up(session, business):
    tenant = business.tenant.id
    returned = _order(session, business, "SO-313-2")
    raised = _order(session, business, "SO-313-3")
    for promise in (returned, raised):
        _ship(session, business, promise, "6")
        core.revise_commitment(session, tenant, promise.id, quantity="4")
    assert {returned.id, raised.id} <= set(_beyond(session, business))

    core.record_movement(
        session,
        tenant,
        "return",
        business.item.id,
        "2",
        to_location_id=business.location.id,
        commitment_id=returned.id,
        reason="Excess sent back",
    )
    # The customer keeps the excess: the line is raised again to what shipped.
    core.revise_commitment(session, tenant, raised.id, quantity="6")

    assert not {returned.id, raised.id} & set(_beyond(session, business))
    session.refresh(raised)
    assert raised.status == "fulfilled"
    # Positive control: raising beyond what shipped stays refused.
    import pytest

    with pytest.raises(core.InvalidOperation) as refused:
        core.revise_commitment(session, tenant, raised.id, quantity="7")
    assert refused.value.code == "revision_beyond_shipped"


def test_a_cancelled_rest_is_not_beyond_its_order(session, business):
    tenant = business.tenant.id
    promise = _order(session, business, "SO-313-4")
    _ship(session, business, promise, "6")
    core.cancel_commitment(session, tenant, promise.id, reason="Rest not wanted")

    assert promise.id not in _beyond(session, business)


def test_another_company_sees_nothing(session, business):
    promise = _order(session, business, "SO-313-5")
    _ship(session, business, promise, "6")
    core.revise_commitment(session, business.tenant.id, promise.id, quantity="5")
    other = core.create_tenant(session, "Other GmbH")

    assert promise.id in _beyond(session, business)
    assert not [
        row
        for row in operational_exceptions(session, other.id)
        if row.class_id == "shipped_beyond_order"
    ]
