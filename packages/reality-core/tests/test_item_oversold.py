"""Items oversold across channels (spec 300 FR-001).

Open customer demand above stock on hand plus open supplier supply is reported
per item, with the orders grouped by their stated sales channel.
"""

from decimal import Decimal

import pytest
from legacy_order_support import legacy_sales_order
from sqlalchemy import event
from sqlalchemy.orm import Session

from reality.services import core
from reality.services.exceptions import operational_exceptions


@pytest.fixture(autouse=True, params=[False, True])
def snapshot_mode(session, request):
    session.info["item_oversold_test_snapshot"] = request.param


def _stock(session, business, quantity, item=None):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=business.location.id,
    )


def _sell(session, business, number, quantity, channel, *, item=None, unit="pcs"):
    item = item or business.item
    record = legacy_sales_order if unit != item.unit else core.create_manual_order
    _, order, _, commitments = record(
        session,
        business.tenant.id,
        "sales",
        number,
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": item.id,
                "quantity": quantity,
                "unit": unit,
                "unit_price": "10.00",
                "gross_amount": str(Decimal(quantity) * 10),
            }
        ],
        str(Decimal(quantity) * 10),
        sales_channel=channel,
    )
    return order, commitments[0]


def _buy(session, business, number, quantity, *, unit="pcs"):
    _, order, _, commitments = core.create_manual_order(
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
                "unit": unit,
                "unit_price": "5.00",
                "gross_amount": str(Decimal(quantity) * 5),
            }
        ],
        str(Decimal(quantity) * 5),
    )
    return order, commitments[0]


def _oversold(session, tenant):
    if session.info.get("item_oversold_test_snapshot"):
        session.flush()
        at = core.now()
        expected = [
            row.to_dict()
            for row in operational_exceptions(
                session, tenant, as_of=at, classes=["item_oversold"]
            )
        ]
        with Session(session.connection(), autoflush=False) as reader:
            reader.info["operations_snapshot_consistent"] = True
            actual = operational_exceptions(
                reader, tenant, as_of=at, classes=["item_oversold"]
            )
        assert [row.to_dict() for row in actual] == expected
        return {row.record_id: row for row in actual}
    return {
        row.record_id: row
        for row in operational_exceptions(session, tenant)
        if row.class_id == "item_oversold"
    }


def test_orders_from_two_channels_above_stock_are_reported_by_channel(
    session, business
):
    tenant = business.tenant.id
    _stock(session, business, "4")
    shop, _ = _sell(session, business, "SO-SHOP-1", "4", "shopify")
    # Positive control: demand within stock is not oversold.
    assert business.item.id not in _oversold(session, tenant)

    market, _ = _sell(session, business, "SO-MKT-1", "2", "amazon")
    shop_two, _ = _sell(session, business, "SO-SHOP-2", "1", "shopify")
    row = _oversold(session, tenant)[business.item.id]

    assert (row.record_type, row.severity) == ("item", "high")
    values = row.causal_values
    assert (
        values["demand_quantity"],
        values["on_hand_quantity"],
        values["incoming_quantity"],
        values["shortfall_quantity"],
    ) == (Decimal("7.0000"), Decimal("4.0000"), Decimal(0), Decimal("3.0000"))
    assert row.trace["channels"] == {
        "amazon": {"quantity": Decimal("2.0000"), "orders": [market.id]},
        "shopify": {
            "quantity": Decimal("5.0000"),
            "orders": sorted([shop.id, shop_two.id]),
        },
    }
    assert set(row.trace["document_ids"]) == {shop.id, shop_two.id, market.id}
    # What a person reads in the explanation is one line, not a structure.
    assert values["channels"] == "amazon 2 (1 order) · shopify 5 (2 orders)"
    assert "not_comparable" not in values


def test_an_open_purchase_order_covering_the_shortfall_clears_it(session, business):
    tenant = business.tenant.id
    _stock(session, business, "4")
    _sell(session, business, "SO-1", "6", "shopify")
    assert business.item.id in _oversold(session, tenant)

    _buy(session, business, "PO-1", "1")
    assert _oversold(session, tenant)[business.item.id].causal_values[
        "shortfall_quantity"
    ] == Decimal("1.0000")
    _buy(session, business, "PO-2", "1")
    assert business.item.id not in _oversold(session, tenant)


def test_shipped_and_cancelled_quantity_no_longer_counts(session, business):
    tenant = business.tenant.id
    _stock(session, business, "4")
    _, shipped = _sell(session, business, "SO-S", "3", "shopify")
    _, cancelled = _sell(session, business, "SO-C", "3", "amazon")
    assert business.item.id in _oversold(session, tenant)

    # Shipping takes the goods out of stock and the promise out of demand alike.
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "3",
        from_location_id=business.location.id,
        commitment_id=shipped.id,
    )
    assert business.item.id in _oversold(session, tenant)
    core.cancel_commitment(session, tenant, cancelled.id, reason="Withdrawn")
    assert business.item.id not in _oversold(session, tenant)


def test_a_revised_promise_counts_its_quantity_in_force(session, business):
    tenant = business.tenant.id
    _stock(session, business, "4")
    _, promise = _sell(session, business, "SO-R", "6", "shopify")
    assert business.item.id in _oversold(session, tenant)

    core.revise_commitment(session, tenant, promise.id, quantity="4", note="Less")
    assert business.item.id not in _oversold(session, tenant)


def test_a_promise_in_another_unit_is_named_not_summed(session, business):
    tenant = business.tenant.id
    _stock(session, business, "4")
    _sell(session, business, "SO-PCS", "5", "shopify")
    boxes, _ = _sell(session, business, "SO-BOX", "2", "amazon", unit="box")

    row = _oversold(session, tenant)[business.item.id]
    assert row.causal_values["demand_quantity"] == Decimal("5.0000")
    assert row.trace["not_comparable"] == [
        {"document_id": boxes.id, "unit": "box", "quantity": Decimal("2.0000")}
    ]


def test_another_company_never_counts(session, business):
    tenant = business.tenant.id
    other = core.create_tenant(session, "Other GmbH")
    _stock(session, business, "4")
    _sell(session, business, "SO-OWN", "4", "shopify")
    stranger = core.create_party(session, other.id, "Fremd GmbH", "customer")
    company = core.create_party(session, other.id, "Other GmbH", "company")
    location = core.create_location(session, other.id, "Other Lager")
    item = core.create_item(session, other.id, business.item.sku, "Same SKU")
    core.create_manual_order(
        session,
        other.id,
        "sales",
        "SO-OTHER",
        company.id,
        stranger.id,
        location.id,
        [{"item_id": item.id, "quantity": "9", "unit_price": "1", "gross_amount": "9"}],
        "9",
    )

    assert _oversold(session, tenant) == {}
    assert set(_oversold(session, other.id)) == {item.id}


def test_the_statement_count_does_not_grow_with_items(session, business):
    tenant = business.tenant.id

    def statements(items):
        for index in range(items):
            item = core.create_item(session, tenant, f"SKU-N-{items}-{index}", "N")
            _stock(session, business, "1", item=item)
            _sell(session, business, f"SO-N-{items}-{index}", "2", "shopify", item=item)
        count = 0

        def counter(*_):
            nonlocal count
            count += 1

        engine = session.get_bind()
        event.listen(engine, "before_cursor_execute", counter)
        try:
            from reality.services.exceptions import _item_oversold_exceptions

            found = _item_oversold_exceptions(session, tenant, core.now())
        finally:
            event.remove(engine, "before_cursor_execute", counter)
        assert len(found) == items + (2 if items == 40 else 0)
        return count

    assert statements(2) == statements(40)


def test_the_finding_agrees_with_the_supply_and_demand_view(session, business):
    """One truth: the shortfall is the view's demand less stock and supply."""
    from reality.services import projections

    tenant = business.tenant.id
    _stock(session, business, "4")
    _sell(session, business, "SO-V1", "5", "shopify")
    _sell(session, business, "SO-V2", "2", "amazon")
    _buy(session, business, "PO-V", "1")
    projections.refresh_operational_projections(session, tenant)

    (view,) = [
        row
        for row in projections.projection_rows(
            session, tenant, projections.ITEM_SUPPLY_DEMAND
        )
        if row["item_id"] == business.item.id
    ]
    shortfall = _oversold(session, tenant)[business.item.id].causal_values[
        "shortfall_quantity"
    ]
    assert (
        Decimal(view["open_customer_demand"])
        - Decimal(view["physical"])
        - Decimal(view["incoming"])
        == shortfall
        == Decimal("2.0000")
    )


def test_supply_in_the_purchase_unit_counts_by_the_items_factor(session, business):
    tenant = business.tenant.id
    business.item.purchase_unit = "box"
    business.item.conversion_factor = Decimal(12)
    session.commit()
    _sell(session, business, "SO-F", "20", "shopify")
    assert business.item.id in _oversold(session, tenant)

    # Two boxes of twelve are 24 pieces, as the item states.
    _buy(session, business, "PO-BOX", "2", unit="box")
    assert business.item.id not in _oversold(session, tenant)


def test_a_service_is_never_oversold(session, business):
    tenant = business.tenant.id
    service = core.create_item(
        session, tenant, "SRV-INSTALL", "Installation", item_type="service"
    )
    _stock(session, business, "1")
    _sell(session, business, "SO-SRV", "3", "shopify", item=service)
    # Control: a stocked item sold beyond stock is reported.
    _sell(session, business, "SO-STK", "2", "shopify")

    assert set(_oversold(session, tenant)) == {business.item.id}


def test_every_finding_appears_once(session, business):
    """Review: due soon was derived twice when every class was asked for."""
    from datetime import timedelta

    tenant = business.tenant.id
    _stock(session, business, "1")
    _, promise = _sell(session, business, "SO-ONCE", "3", "shopify")
    core.revise_commitment(
        session, tenant, promise.id, core.now() + timedelta(hours=5), note="Soon"
    )

    rows = operational_exceptions(session, tenant)
    ids = [row.id for row in rows]
    assert len(ids) == len(set(ids))
    assert {"item_oversold", "outgoing_commitment_due_soon"} <= {
        row.class_id for row in rows
    }
