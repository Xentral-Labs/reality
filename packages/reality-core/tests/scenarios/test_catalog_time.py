"""Business journeys about time that are not accounting periods (specs 340, 349)."""
from datetime import UTC, date, datetime

from conftest import record_by_id
from intake_review_support import accept_import_job, reviewed_manual_order

from reality.db.core import Commitment
from reality.services import core


def _order(session, business, kind, number, party_id, ordered_at):
    _, _, _, (promise,) = reviewed_manual_order(
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


def _shop_order_day(session, business, order_id, created_at):
    tenant = business.tenant.id
    payload = {
        "id": order_id,
        "name": f"#{order_id}",
        "currency": "USD",
        "total_price": "40.00",
        "created_at": created_at,
        "updated_at": created_at,
        "line_items": [
            {
                "id": order_id * 10,
                "sku": business.item.sku,
                "quantity": 4,
                "price": "10.00",
            }
        ],
    }
    _, job = core.enqueue_shopify_order(
        session,
        tenant,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    _, document, _, _ = accept_import_job(session, tenant, job.id)
    return document


def test_an_order_at_half_past_eleven_in_new_york_is_dated_that_day(session, business):
    """
    BUSINESS TEST:
    Q05: an order placed at 23:30 in New York is stored in UTC and dated on the
    company's own day.
    GIVEN:
    A company that states America/New_York, and a shop order created at 23:30 on
    31 October New York time, which is 03:30 UTC on 1 November.
    WHEN:
    The order is interpreted.
    THEN:
    Its instant is stored in UTC and it is dated 31 October; the same order in a
    company counting in UTC is dated 1 November.
    BUSINESS RULES:
    company_time_zone.day
    """
    from reality.services.company_time_zone import set_company_time_zone

    created = "2026-10-31T23:30:00-04:00"
    # Positive control: without a stated zone the UTC day is 1 November.
    utc_order = _shop_order_day(session, business, 3490, created)
    assert utc_order.document_date == date(2026, 11, 1)

    set_company_time_zone(session, business.tenant.id, "America/New_York")
    order = _shop_order_day(session, business, 3495, created)

    assert core.utc_datetime(order.ordered_at) == datetime(
        2026, 11, 1, 3, 30, tzinfo=UTC
    )
    assert order.document_date == date(2026, 10, 31)
