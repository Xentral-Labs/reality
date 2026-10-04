"""Spec 333: kits, their availability, assembly and the bundle split."""

import json
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import KitComponent, Movement
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.kits import (
    assemble_kit,
    define_kit,
    kit_availability,
    kit_split,
    kits,
    review_kit,
)


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code
    return refused.value


def _bike(session, business, shares=("0.6", "0.4")):
    """A kit of one frame and two wheels."""
    tenant = business.tenant.id
    kit = reviewed_create_item(session, tenant, "KIT-BIKE", "Bike kit")
    frame = reviewed_create_item(session, tenant, "FRAME", "Frame")
    wheel = reviewed_create_item(session, tenant, "WHEEL", "Wheel")
    define_kit(
        session,
        tenant,
        kit.id,
        [
            {"item_id": frame.id, "quantity": "1", "share": shares[0]},
            {"item_id": wheel.id, "quantity": "2", "share": shares[1]},
        ]
        if shares
        else [
            {"item_id": frame.id, "quantity": "1"},
            {"item_id": wheel.id, "quantity": "2"},
        ],
    )
    return kit, frame, wheel


def _stock(session, business, item, quantity, location=None):
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        item.id,
        quantity,
        to_location_id=(location or business.location).id,
    )


def _on_hand(session, business, item):
    return core.stock_at(session, business.tenant.id, item.id, business.location.id)


def test_availability_is_the_minimum_the_free_components_build(session, business):
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "3")
    _stock(session, business, wheel, "4")

    (here,) = kit_availability(session, business.tenant.id, kit.id)

    assert (here["buildable"], here["available"], here["limited_by"]) == (
        "2",
        "2",
        ["WHEEL"],
    )
    # Positive control: a wheel reserved for another order is not free.
    order = core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-333-W",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": wheel.id,
                "quantity": "1",
                "unit_price": "5",
                "gross_amount": "5",
            }
        ],
        "5",
    )
    core.reserve(session, business.tenant.id, order[3][0].id)
    (here,) = kit_availability(session, business.tenant.id, kit.id)
    assert (here["buildable"], here["components"][1]["free"]) == ("1", "3")


def test_an_assembly_consumes_and_produces_under_one_statement(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "3")
    _stock(session, business, wheel, "6")

    result = assemble_kit(session, tenant, kit.id, business.location.id, "3")

    movements = list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == tenant,
                Movement.source_record_id == result["source_record_id"],
            )
        )
    )
    assert sorted((m.type, m.item_id, m.quantity) for m in movements) == sorted(
        [
            ("assembly_input", frame.id, Decimal("3.0000")),
            ("assembly_input", wheel.id, Decimal("6.0000")),
            ("assembly_output", kit.id, Decimal("3.0000")),
        ]
    )
    assert len({m.occurred_at for m in movements}) == 1
    assert (_on_hand(session, business, frame), _on_hand(session, business, wheel)) == (
        0,
        0,
    )
    assert _on_hand(session, business, kit) == 3
    # The kits on hand count as available, without components left to build more.
    (here,) = kit_availability(session, tenant, kit.id)
    assert (here["kits_on_hand"], here["buildable"], here["available"]) == (
        "3",
        "0",
        "3",
    )


def test_a_short_component_refuses_the_whole_assembly(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "2")
    _stock(session, business, wheel, "3")

    refusal = _refused(
        "kit_component_short",
        lambda: assemble_kit(session, tenant, kit.id, business.location.id, "2"),
    )
    assert refusal.values["sku"] == "WHEEL"
    assert (refusal.values["needed"], refusal.values["free"]) == ("4", "3")
    # The review refuses alike, and nothing left stock.
    _refused(
        "kit_component_short",
        lambda: review_kit(
            session,
            tenant,
            "kit_assemble",
            {
                "kit_item_id": kit.id,
                "location_id": business.location.id,
                "quantity": "2",
            },
        ),
    )
    session.rollback()
    assert (_on_hand(session, business, frame), _on_hand(session, business, wheel)) == (
        2,
        3,
    )
    # Positive control: one kit is there to build.
    assemble_kit(session, tenant, kit.id, business.location.id, "1")
    assert _on_hand(session, business, kit) == 1


def test_assembly_refusals(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "5")
    _stock(session, business, wheel, "10")
    loose = reviewed_create_item(session, tenant, "LOOSE", "Not a kit")
    location = business.location.id
    _refused(
        "kit_not_defined",
        lambda: assemble_kit(session, tenant, loose.id, location, "1"),
    )
    _refused(
        "kit_assembly_quantity_invalid",
        lambda: assemble_kit(session, tenant, kit.id, location, "1.5"),
    )
    _refused(
        "kit_assembly_quantity_invalid",
        lambda: assemble_kit(session, tenant, kit.id, location, "0"),
    )
    _refused(
        "kit_assembly_time_future",
        lambda: assemble_kit(
            session,
            tenant,
            kit.id,
            location,
            "1",
            occurred_at=(core.now() + timedelta(days=1)).isoformat(),
        ),
    )
    # A stated earlier time dates every movement of the assembly.
    earlier = core.now() - timedelta(minutes=30)
    result = assemble_kit(session, tenant, kit.id, location, "1", occurred_at=earlier)
    (output,) = session.scalars(
        select(Movement).where(
            Movement.tenant_id == tenant,
            Movement.source_record_id == result["source_record_id"],
            Movement.type == "assembly_output",
        )
    )
    assert core.utc_datetime(output.occurred_at) == earlier


def test_definition_refusals(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    other = reviewed_create_item(session, tenant, "KIT-2", "Second kit")
    service = reviewed_create_item(session, tenant, "SRV", "Assembly", item_type="service")
    lot = reviewed_create_item(session, tenant, "LOT", "Lot item", tracking_type="lot")

    def define(target, components):
        return lambda: define_kit(session, tenant, target.id, components)

    _refused(
        "kit_already_defined", define(kit, [{"item_id": frame.id, "quantity": "1"}])
    )
    _refused(
        "kit_component_is_kit", define(other, [{"item_id": kit.id, "quantity": "1"}])
    )
    _refused(
        "kit_component_is_kit", define(frame, [{"item_id": other.id, "quantity": "1"}])
    )
    _refused(
        "kit_component_is_kit", define(other, [{"item_id": other.id, "quantity": "1"}])
    )
    _refused("kit_components_required", define(other, []))
    _refused(
        "kit_component_not_stocked",
        define(other, [{"item_id": service.id, "quantity": "1"}]),
    )
    _refused("kit_item_tracked", define(other, [{"item_id": lot.id, "quantity": "1"}]))
    _refused(
        "kit_component_quantity_invalid",
        define(other, [{"item_id": wheel.id, "quantity": "0"}]),
    )
    _refused(
        "kit_component_repeated",
        define(
            other,
            [
                {"item_id": wheel.id, "quantity": "1"},
                {"item_id": wheel.id, "quantity": "1"},
            ],
        ),
    )
    _refused(
        "kit_shares_invalid",
        define(
            other,
            [
                {"item_id": wheel.id, "quantity": "1", "share": "0.5"},
                {"item_id": frame.id, "quantity": "1", "share": "0.4"},
            ],
        ),
    )
    _refused(
        "kit_shares_invalid",
        define(
            other,
            [
                {"item_id": wheel.id, "quantity": "1", "share": "1"},
                {"item_id": frame.id, "quantity": "1"},
            ],
        ),
    )
    # Positive control: the same components with shares that add up to one.
    define_kit(
        session,
        tenant,
        other.id,
        [
            {"item_id": wheel.id, "quantity": "1", "share": "0.5"},
            {"item_id": frame.id, "quantity": "1", "share": "0.5"},
        ],
    )
    assert {row["sku"] for row in kits(session, tenant, item_id=wheel.id)} == {
        "KIT-BIKE",
        "KIT-2",
    }


def test_assembly_movements_are_not_corrected_or_costed_one_by_one(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "1")
    _stock(session, business, wheel, "2")
    result = assemble_kit(session, tenant, kit.id, business.location.id, "1")
    movement_id = result["movement_ids"][0]

    _refused(
        "movement_assembly_not_correctable",
        lambda: core.preview_movement_correction(
            session, tenant, movement_id, reason="Miscounted"
        ),
    )
    _refused(
        "movement_assembly_not_correctable",
        lambda: core.correct_movement(
            session, tenant, movement_id, reason="Miscounted"
        ),
    )
    # The assembly movement types are not open to a plain movement.
    _refused(
        "movement_assembly_shape_invalid",
        lambda: core.record_movement(
            session,
            tenant,
            "assembly_output",
            kit.id,
            "1",
            to_location_id=business.location.id,
        ),
    )


def test_the_inventory_review_refuses_an_item_with_assembly_movements(
    session, business
):
    from reality.domain.costing import InventoryReview
    from reality.services import inventory_costing

    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "1")
    _stock(session, business, wheel, "2")
    assemble_kit(session, tenant, kit.id, business.location.id, "1")
    session.commit()

    def review(item):
        return InventoryReview(
            operation="inventory_review",
            item_id=item.id,
            owner_party_id=business.company.id,
            method="fifo",
            currency="EUR",
            base_unit="pcs",
            history_start=core.now() - timedelta(days=1),
            effective_at=core.now(),
            history_complete_from_zero=True,
            receipt_cost_scopes_confirmed=True,
            economic_issue_ids=[],
            expected_event_sequence=0,
            reason="Month end",
        )

    for item in (frame, kit):
        _refused(
            "inventory_assembly_not_costed",
            lambda item=item: inventory_costing._check(session, tenant, review(item)),
        )
    # Positive control: an item no assembly touched gets past the guard.
    with pytest.raises(core.InvalidOperation) as other:
        inventory_costing._check(session, tenant, review(business.item))
    assert other.value.code != "inventory_assembly_not_costed"


def test_the_split_adds_up_to_the_stated_line(session, business):
    tenant = business.tenant.id
    kit, _frame, _wheel = _bike(session, business, shares=("0.6", "0.4"))
    _, _, (line,), _ = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-333-S",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": kit.id,
                "quantity": "3",
                "unit_price": "33.33",
                "gross_amount": "99.99",
            }
        ],
        "99.99",
    )

    split = kit_split(session, tenant, line.id)

    parts = {part["sku"]: part for part in split["split"]}
    assert (parts["FRAME"]["gross"], parts["WHEEL"]["gross"]) == ("59.99", "40")
    assert sum(Decimal(part["gross"]) for part in split["split"]) == Decimal("99.99")
    assert (parts["FRAME"]["quantity"], parts["WHEEL"]["quantity"]) == ("3", "6")
    assert parts["WHEEL"]["gross_per_piece"] == "6.67"


def test_a_kit_without_shares_has_no_split(session, business):
    tenant = business.tenant.id
    kit, _, _ = _bike(session, business, shares=None)
    _, _, (line,), _ = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-333-N",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": kit.id,
                "quantity": "1",
                "unit_price": "50",
                "gross_amount": "50",
            }
        ],
        "50",
    )
    split = kit_split(session, tenant, line.id)
    assert split["split"] is None
    assert split["stated"] == {"gross": "50"}
    # A line of an item that is not a kit is refused.
    _, _, (plain,), _ = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-333-P",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "5",
                "gross_amount": "5",
            }
        ],
        "5",
    )
    _refused("kit_split_line_not_kit", lambda: kit_split(session, tenant, plain.id))


def test_a_kit_the_components_build_is_not_oversold(session, business):
    tenant = business.tenant.id
    kit, frame, wheel = _bike(session, business)
    _stock(session, business, frame, "2")
    _stock(session, business, wheel, "4")
    core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-333-O",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": kit.id,
                "quantity": "2",
                "unit_price": "50",
                "gross_amount": "100",
            }
        ],
        "100",
    )

    def oversold():
        return {
            row.record_id
            for row in operational_exceptions(session, tenant)
            if row.class_id == "item_oversold"
        }

    assert kit.id not in oversold()
    # Positive control: a third kit no component builds is oversold.
    core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-333-O2",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": kit.id,
                "quantity": "1",
                "unit_price": "50",
                "gross_amount": "50",
            }
        ],
        "50",
    )
    assert kit.id in oversold()


def test_another_company_sees_no_kit(session, business):
    tenant = business.tenant.id
    kit, frame, _ = _bike(session, business)
    other = core.create_tenant(session, "Other GmbH")

    assert kits(session, other.id) == []
    _refused("record_not_found", lambda: kit_availability(session, other.id, kit.id))
    _refused(
        "record_not_found",
        lambda: define_kit(
            session, other.id, kit.id, [{"item_id": frame.id, "quantity": "1"}]
        ),
    )
    assert (
        session.scalar(
            select(KitComponent.id).where(KitComponent.tenant_id == other.id)
        )
        is None
    )
    assert len(kits(session, tenant)) == 1
    assert json.dumps(kits(session, tenant), default=str)


from intake_review_support import reviewed_create_item
