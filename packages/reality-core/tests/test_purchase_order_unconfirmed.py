"""Spec 346: a purchase line the supplier has not confirmed in time is reported."""

from datetime import timedelta
from decimal import Decimal

from reality.services import core
from reality.services.exceptions import operational_exceptions


def _purchase(session, business, number, placed_days_ago, quantity="10"):
    _, _, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        business.supplier.id,
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
        ordered_at=core.now() - timedelta(days=placed_days_ago),
        requested_delivery_at=(core.now() + timedelta(days=20)).isoformat(),
    )
    return promise


def _unconfirmed(session, tenant_id, as_of=None):
    return {
        row.record_id: row
        for row in operational_exceptions(session, tenant_id, as_of=as_of)
        if row.class_id == "purchase_order_unconfirmed"
    }


def test_an_unconfirmed_line_is_reported_after_three_days(session, business):
    tenant = business.tenant.id
    fresh = _purchase(session, business, "PO-346-NEW", placed_days_ago=1)
    old = _purchase(session, business, "PO-346-OLD", placed_days_ago=5)

    found = _unconfirmed(session, tenant)

    # Positive control: an order placed yesterday is not yet worth asking about.
    assert fresh.id not in found
    finding = found[old.id]
    placed = finding.causal_values["placed_at"]
    assert finding.causal_values["confirmation_expected_by"] == placed + timedelta(
        days=3
    )
    assert finding.causal_values["ordered_quantity"] == 10
    assert finding.sort_at == placed + timedelta(days=3)
    assert "PO-346-OLD" in finding.impact


def test_a_confirmation_or_a_receipt_clears_it(session, business):
    tenant = business.tenant.id
    confirmed = _purchase(session, business, "PO-346-CONF", placed_days_ago=5)
    received = _purchase(session, business, "PO-346-RCV", placed_days_ago=5)
    cancelled = _purchase(session, business, "PO-346-CXL", placed_days_ago=5)
    waiting = _purchase(session, business, "PO-346-WAIT", placed_days_ago=5)
    before = core.now()

    # Confirmed exactly as ordered: the supplier restates the date.
    core.revise_commitment(
        session, tenant, confirmed.id, confirmed.due_at, note="Supplier confirmed"
    )
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "4",
        to_location_id=business.location.id,
        commitment_id=received.id,
    )
    core.cancel_commitment(session, tenant, cancelled.id, reason="Not needed")

    found = _unconfirmed(session, tenant)
    assert not {confirmed.id, received.id, cancelled.id} & set(found)
    # Positive control: the line nobody answered is still reported.
    assert waiting.id in found
    # Read as of before the confirmation, the confirmed line was still waiting.
    assert confirmed.id in _unconfirmed(session, tenant, as_of=before)


def test_another_company_sees_nothing(session, business):
    old = _purchase(session, business, "PO-346-ISO", placed_days_ago=5)
    other = core.create_tenant(session, "Other GmbH")

    assert old.id in _unconfirmed(session, business.tenant.id)
    assert _unconfirmed(session, other.id) == {}


def test_an_overdue_line_is_left_to_the_overdue_finding(session, business):
    tenant = business.tenant.id
    late = _purchase(session, business, "PO-346-LATE", placed_days_ago=10)
    late.due_at = core.now() - timedelta(days=1)
    session.flush()

    rows = operational_exceptions(session, tenant)
    assert late.id not in {
        row.record_id for row in rows if row.class_id == "purchase_order_unconfirmed"
    }
    # Positive control: it is reported, as overdue.
    assert late.id in {
        row.record_id
        for row in rows
        if row.class_id == "overdue_incoming_supplier_commitment"
    }
