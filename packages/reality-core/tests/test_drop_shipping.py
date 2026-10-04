"""Spec 337: a supplier ships straight to the customer."""

from datetime import timedelta
from decimal import Decimal

import pytest
from intake_review_support import reviewed_manual_order

from reality.services import core
from reality.services.drop_shipping import (
    drop_shipments,
    preview_drop_shipment,
    record_drop_shipment,
)
from reality.services.exceptions import operational_exceptions
from reality.services.supply_assignments import assign_supply


def _orders(session, business, number, sold="4", bought="4"):
    tenant = business.tenant.id
    sale = reviewed_manual_order(
        session,
        tenant,
        "sales",
        f"SO-{number}",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": sold,
                "unit_price": "20",
                "gross_amount": str(Decimal(sold) * 20),
            }
        ],
        str(Decimal(sold) * 20),
    )[3][0]
    purchase = reviewed_manual_order(
        session,
        tenant,
        "purchase",
        f"PO-{number}",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": bought,
                "unit_price": "10",
                "gross_amount": str(Decimal(bought) * 10),
            }
        ],
        str(Decimal(bought) * 10),
        ship_to_party_id=business.customer.id,
    )[3][0]
    return sale, purchase


def _assign(session, business, sale, purchase, quantity, key):
    return assign_supply(
        session,
        business.tenant.id,
        purchase.id,
        quantity,
        purpose="customer_demand",
        customer_commitment_id=sale.id,
        request_id=f"drop-{key}",
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def test_the_supplier_ships_straight_to_the_customer(session, business):
    tenant = business.tenant.id
    sale, purchase = _orders(session, business, "337-1")
    _assign(session, business, sale, purchase, "4", "1")
    stock_before = core.stock_at(session, tenant, business.item.id)

    result = record_drop_shipment(
        session,
        tenant,
        supplier_commitment_id=purchase.id,
        quantity="4",
        carrier="DHL",
        tracking_number="DS-1",
    )

    session.refresh(sale)
    session.refresh(purchase)
    assert (sale.status, purchase.status) == ("fulfilled", "fulfilled")
    assert core.stock_at(session, tenant, business.item.id) == stock_before
    read = drop_shipments(session, tenant, commitment_id=sale.id)
    assert read["links"][0]["drop_shipped"] == Decimal(4)
    (shipped,) = read["drop_shipments"]
    assert (shipped["shipment_id"], shipped["tracking_number"]) == (
        result["shipment_id"],
        "DS-1",
    )


def test_it_ships_only_what_is_assigned_and_open(session, business):
    tenant = business.tenant.id
    sale, purchase = _orders(session, business, "337-2", sold="5", bought="5")
    _refused(
        "drop_ship_not_assigned",
        lambda: preview_drop_shipment(
            session, tenant, supplier_commitment_id=purchase.id, quantity="1"
        ),
    )
    _assign(session, business, sale, purchase, "3", "2")
    _refused(
        "drop_ship_exceeds_assigned",
        lambda: preview_drop_shipment(
            session, tenant, supplier_commitment_id=purchase.id, quantity="4"
        ),
    )
    _refused(
        "drop_ship_time_future",
        lambda: preview_drop_shipment(
            session,
            tenant,
            supplier_commitment_id=purchase.id,
            quantity="1",
            occurred_at=(core.now() + timedelta(days=1)).isoformat(),
        ),
    )
    _refused(
        "drop_ship_quantity_invalid",
        lambda: preview_drop_shipment(
            session, tenant, supplier_commitment_id=purchase.id, quantity="-1"
        ),
    )
    record_drop_shipment(
        session, tenant, supplier_commitment_id=purchase.id, quantity="2"
    )
    # What is left of the assignment, and nothing beyond it.
    _refused(
        "drop_ship_exceeds_assigned",
        lambda: preview_drop_shipment(
            session, tenant, supplier_commitment_id=purchase.id, quantity="2"
        ),
    )
    assert (
        preview_drop_shipment(
            session, tenant, supplier_commitment_id=purchase.id, quantity="1"
        )["customer_open_after"]
        == "2"
    )


def test_a_drop_shipment_is_not_stock_and_needs_none(session, business):
    """Nothing on hand, nothing reserved: the order is still kept."""
    tenant = business.tenant.id
    sale, purchase = _orders(session, business, "337-3", sold="2", bought="2")
    _assign(session, business, sale, purchase, "2", "3")
    record_drop_shipment(
        session, tenant, supplier_commitment_id=purchase.id, quantity="2"
    )

    assert core.stock_at(session, tenant, business.item.id, business.location.id) == 0
    assert not [
        row
        for row in operational_exceptions(session, tenant)
        if sale.id in (row.record_id, *row.cause_ids)
        or purchase.id in (row.record_id, *row.cause_ids)
    ]


def test_another_company_sees_nothing(session, business):
    tenant = business.tenant.id
    sale, purchase = _orders(session, business, "337-4", sold="1", bought="1")
    _assign(session, business, sale, purchase, "1", "4")
    record_drop_shipment(
        session, tenant, supplier_commitment_id=purchase.id, quantity="1"
    )
    other = core.create_tenant(session, "Other GmbH")

    _refused(
        "record_not_found",
        lambda: drop_shipments(session, other.id, commitment_id=sale.id),
    )


def test_only_a_purchase_order_shipping_to_the_customer_is_drop_shipped(
    session, business
):
    tenant = business.tenant.id
    sale, purchase = _orders(session, business, "337-5", sold="2", bought="2")
    ordinary = reviewed_manual_order(
        session,
        tenant,
        "purchase",
        "PO-337-5-OWN",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )[3][0]
    second_sale = reviewed_manual_order(
        session,
        tenant,
        "sales",
        "SO-337-5-B",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "20",
                "gross_amount": "40",
            }
        ],
        "40",
    )[3][0]
    _assign(session, business, second_sale, ordinary, "1", "5-own")
    # A purchase coming to the company's warehouse is received there, not drop-shipped.
    _refused(
        "drop_ship_purchase_not_to_customer",
        lambda: preview_drop_shipment(
            session, tenant, supplier_commitment_id=ordinary.id, quantity="1"
        ),
    )
    _assign(session, business, sale, purchase, "1", "5-a")
    _assign(session, business, second_sale, purchase, "1", "5-b")
    # Serving two customer lines, the supplier's dispatch names which one.
    _refused(
        "drop_ship_customer_promise_required",
        lambda: preview_drop_shipment(
            session, tenant, supplier_commitment_id=purchase.id, quantity="1"
        ),
    )
    assert (
        preview_drop_shipment(
            session,
            tenant,
            supplier_commitment_id=purchase.id,
            customer_commitment_id=second_sale.id,
            quantity="1",
        )["customer_open_after"]
        == "1"
    )


def test_drop_ship_supply_is_not_incoming_stock(session, business):
    from reality.services.inventory_reads import inventory_position_query, position_row

    tenant = business.tenant.id
    _orders(session, business, "337-6", sold="3", bought="3")

    def incoming():
        (row,) = [
            position_row(values[0], values[1:])
            for values in session.execute(
                inventory_position_query(tenant).where(core.Item.id == business.item.id)
            )
        ]
        return row["incoming"]

    # The drop-ship purchase brings nothing to the warehouse.
    assert incoming() == 0
    # Positive control: an ordinary purchase is incoming stock.
    reviewed_manual_order(
        session,
        tenant,
        "purchase",
        "PO-337-6-OWN",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit_price": "10",
                "gross_amount": "50",
            }
        ],
        "50",
    )
    assert incoming() == 5


def test_an_agent_records_a_drop_shipment_through_the_reviewed_tool(session, business):
    import json

    from reality.mcp.catalog import MCP_TOOL_REGISTRY
    from reality.mcp.server import _reject_unknown_fields
    from reality.services.delivery_actions import delivery_proposal_detail
    from reality.tools.application import approve_and_execute_proposal

    tenant = business.tenant.id
    sale, purchase = _orders(session, business, "337-7", sold="2", bought="2")
    _assign(session, business, sale, purchase, "2", "7")
    arguments = {
        "supplier_commitment_id": purchase.id,
        "quantity": "2",
        "carrier": "UPS",
        "tracking_number": "1Z-337",
        "occurred_at": (core.now() - timedelta(hours=3)).isoformat(),
    }
    definition = MCP_TOOL_REGISTRY["drop_shipment_record_propose"]
    _reject_unknown_fields(definition.input_schema, arguments)

    proposed = definition.handler(session, tenant, arguments)

    detail = delivery_proposal_detail(session, tenant, proposed["proposal_id"])
    assert detail["review"]["state"]["customer_commitment_id"] == sale.id
    assert detail["review"]["effect"]["stock_moves"] is False
    session.refresh(sale)
    assert sale.status == "open"  # Nothing happens before confirmation.
    approve_and_execute_proposal(
        session,
        tenant,
        proposed["proposal_id"],
        review_token=detail["review"]["token"],
        confirmed=True,
    )
    detail = delivery_proposal_detail(session, tenant, proposed["proposal_id"])
    assert detail["verification"] == "verified"
    assert json.dumps(detail["links"], default=str).count("commitment") == 2
    session.refresh(sale)
    assert sale.status == "fulfilled"
