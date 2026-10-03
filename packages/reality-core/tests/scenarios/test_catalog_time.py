"""Business journeys about time that are not accounting periods (spec 340)."""

from datetime import UTC, datetime

from conftest import record_by_id

from reality.db.core import Commitment
from reality.services import core


def _order(session, business, kind, number, party_id, ordered_at):
    _, _, _, (promise,) = core.create_manual_order(
        session,
        business.tenant.id,
        kind,
        number,
        business.company.id,
        party_id,
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
        ordered_at=ordered_at,
    )
    return promise


def _move(session, business, kind, promise, quantity, occurred_at):
    location = {
        "to_location_id"
        if kind == "receipt"
        else "from_location_id": business.location.id
    }
    core.record_movement(
        session,
        business.tenant.id,
        kind,
        business.item.id,
        quantity,
        commitment_id=promise.id,
        occurred_at=occurred_at,
        **location,
    )


def test_open_orders_and_purchases_carry_over_the_year_end(session, business):
    """Q04: there is no period to close, so open promises simply stay open."""
    tenant = business.tenant.id
    # Two years back, so January is in the past whenever the test runs.
    year = core.now().year - 2
    december = datetime(year, 12, 15, 10, tzinfo=UTC)
    sale = _order(session, business, "sales", "SO-Q04", business.customer.id, december)
    purchase = _order(
        session, business, "purchase", "PO-Q04", business.supplier.id, december
    )

    # December: part of the purchase arrives and ships on.
    _move(
        session,
        business,
        "receipt",
        purchase,
        "4",
        datetime(year, 12, 20, 9, tzinfo=UTC),
    )
    _move(
        session, business, "shipment", sale, "4", datetime(year, 12, 21, 9, tzinfo=UTC)
    )

    # Across the year end nothing resets: both promises keep what is still open.
    assert core.open_quantity(session, tenant, sale.id) == 6
    assert core.open_quantity(session, tenant, purchase.id) == 6
    assert record_by_id(session, Commitment, sale.id).status == "open"
    assert record_by_id(session, Commitment, purchase.id).status == "open"

    # January: the rest arrives and ships; December's delivery still counts.
    _move(
        session,
        business,
        "receipt",
        purchase,
        "6",
        datetime(year + 1, 1, 10, 9, tzinfo=UTC),
    )
    _move(
        session,
        business,
        "shipment",
        sale,
        "6",
        datetime(year + 1, 1, 11, 9, tzinfo=UTC),
    )

    assert core.fulfilled_quantity(session, tenant, sale.id) == 10
    assert core.fulfilled_quantity(session, tenant, purchase.id) == 10
    assert record_by_id(session, Commitment, sale.id).status == "fulfilled"
    assert record_by_id(session, Commitment, purchase.id).status == "fulfilled"
