"""Spec 319: one inventory observation across services, Web and projections."""

from decimal import Decimal

import pytest
from intake_review_support import reviewed_reserve

from reality.catalogs import load_application_catalog
from reality.services import core
from reality.services.projections import _inventory_rows
from reality.services.stock_blocks import block_stock, release_stock_block
from reality.web.read_models import inventory_page

QUANTITIES = ("physical", "reserved", "blocked", "available", "incoming", "projected")


def _promise(session, business, kind, quantity, location=None):
    return core.create_commitment(
        session,
        business.tenant.id,
        kind,
        business.supplier.id if kind == "supplier_delivery" else business.company.id,
        business.company.id if kind == "supplier_delivery" else business.customer.id,
        business.item.id,
        (location or business.location).id,
        quantity,
        "2026-10-10",
    )


def _position(row):
    return tuple(Decimal(row[key]) for key in QUANTITIES)


def test_revised_partly_received_supply_agrees_on_every_surface(session, business):
    tenant = business.tenant.id
    supplier = _promise(session, business, "supplier_delivery", "12")
    core.revise_commitment(
        session, tenant, supplier.id, quantity="10", note="Supplier revision"
    )
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "3",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "17",
        to_location_id=business.location.id,
    )
    customer = _promise(session, business, "customer_delivery", "4")
    reviewed_reserve(session, tenant, customer.id)
    block = block_stock(
        session, tenant, business.item.id, business.location.id, "5", "quality"
    )
    release_stock_block(session, tenant, block.id, quantity="2", reason="Cleared two")
    (shared,) = core.inventory_rows(session, tenant, item_ids={business.item.id})
    (web,), pager = inventory_page(session, tenant, item_id=business.item.id)
    projection = _inventory_rows(session, tenant, {business.item.id})[business.item.id]
    assert _position(shared) == (20, 4, 3, 13, 7, 20)
    assert _position(web) == _position(shared) == _position(projection)
    assert pager.total == 1
    assert {row.id for row in shared["receipts"]}
    (filtered,), _ = inventory_page(
        session, tenant, projected_min=Decimal(20), projected_max=Decimal(20)
    )
    assert filtered["item"].id == business.item.id
    core.cancel_commitment(session, tenant, supplier.id, reason="Remainder cancelled")
    (web,), _ = inventory_page(session, tenant, item_id=business.item.id)
    assert web["incoming"] == 0


def test_location_scope_applies_to_every_contribution(session, business):
    tenant = business.tenant.id
    other = reviewed_create_location(session, tenant, "Other warehouse")
    for location, quantity in ((business.location, "20"), (other, "30")):
        core.record_movement(
            session,
            tenant,
            "opening_stock",
            business.item.id,
            quantity,
            to_location_id=location.id,
        )
    block_stock(session, tenant, business.item.id, business.location.id, "3", "quality")
    block_stock(session, tenant, business.item.id, other.id, "5", "quality")
    promise = _promise(session, business, "customer_delivery", "4")
    reviewed_reserve(session, tenant, promise.id)
    _promise(session, business, "supplier_delivery", "7")
    _promise(session, business, "supplier_delivery", "11", other)
    (web,), _ = inventory_page(session, tenant, location_id=business.location.id)
    assert _position(web) == (20, 4, 3, 13, 7, 20)
    (shared,) = core.inventory_rows(session, tenant, item_ids={business.item.id})
    assert _position(shared) == (50, 4, 8, 38, 18, 56)
    stranger = core.create_tenant(session, "Other tenant")
    rows, pager = inventory_page(session, stranger.id, item_id=business.item.id)
    assert rows == [] and pager.total == 0


def test_receipt_correction_restores_only_effective_incoming(session, business):
    tenant = business.tenant.id
    supplier = _promise(session, business, "supplier_delivery", "10")
    receipt = core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
    )
    core.correct_movement(
        session, tenant, receipt.id, reason="Receipt recorded in error"
    )
    (shared,) = core.inventory_rows(session, tenant, item_ids={business.item.id})
    (web,), _ = inventory_page(session, tenant, item_id=business.item.id)
    assert _position(web) == _position(shared) == (0, 0, 0, 0, 10, 10)
    core.revise_commitment(
        session, tenant, supplier.id, quantity="4", note="Only four agreed"
    )
    (web,), _ = inventory_page(session, tenant, item_id=business.item.id)
    assert web["incoming"] == 4


def test_transfer_conserves_stock_and_numeric_sort_precedes_pagination(
    session, business
):
    tenant = business.tenant.id
    other = reviewed_create_location(session, tenant, "Transfer destination")
    second = reviewed_create_item(session, tenant, "SECOND", "Second item")
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        second.id,
        "8",
        to_location_id=business.location.id,
    )
    core.record_movement(
        session,
        tenant,
        "transfer",
        business.item.id,
        "6",
        from_location_id=business.location.id,
        to_location_id=other.id,
    )
    block_stock(
        session, tenant, business.item.id, business.location.id, "10", "quality"
    )
    (row,), pager = inventory_page(
        session,
        tenant,
        location_id=business.location.id,
        available_min=Decimal(0),
        size=1,
        sort="available",
        sort_direction="asc",
    )
    assert row["item"].id == business.item.id and row["available"] == 4
    assert pager.total == 2 and pager.has_next
    (row,), pager = inventory_page(
        session,
        tenant,
        location_id=business.location.id,
        size=1,
        page=2,
        sort="available",
        sort_direction="asc",
    )
    assert row["item"].id == second.id and not pager.has_next
    (company,) = core.inventory_rows(session, tenant, item_ids={business.item.id})
    assert company["physical"] == 20 and company["available"] == 10


@pytest.mark.parametrize(
    "name",
    ["inventory", "fulfillment_queue", "fulfillment_blockers", "item_supply_demand"],
)
def test_projection_catalog_names_stock_block_input(name):
    projection = next(
        row
        for row in load_application_catalog()["projections"]
        if row["materialized_as"] == name
    )
    assert "stock_block" in projection["reads"]
    if name == "inventory":
        assert "blocked" in projection["outputs"]
        assert "block" in projection["calculation"].lower()


from intake_review_support import reviewed_create_item, reviewed_create_location
