from datetime import timedelta
from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    correct_movement,
    create_commitment,
    create_manual_document_with_lines,
    fulfilled_quantity,
    open_quantity,
    record_movement,
    returned_quantity,
)
from reality.services.exceptions import operational_exceptions


def stocked(session, business, quantity=50):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
    )


def delivery(session, business, quantity=10):
    """A customer delivery promise with the goods already gone out."""
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-12-01",
    )
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    return commitment


def send_back(session, business, commitment, quantity):
    return record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )


def test_a_return_may_name_the_delivery_it_reverses(session, business):
    stocked(session, business)
    commitment = delivery(session, business)

    movement = send_back(session, business, commitment, 4)

    assert movement.commitment_id == commitment.id
    assert movement.type == "return"

    # And it is no longer a movement nobody can explain.
    classes = [
        row.class_id for row in operational_exceptions(session, business.tenant.id)
    ]
    assert "unexplained_movement" not in classes


def test_a_return_is_refused_against_a_supplier_promise(session, business):
    stocked(session, business)
    supplier_promise = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        10,
        "2026-12-01",
    )

    # Goods going back to a supplier are a different flow with a different owner.
    with pytest.raises(InvalidOperation, match="commitment"):
        send_back(session, business, supplier_promise, 2)


def test_a_return_may_not_exceed_what_went_out(session, business):
    stocked(session, business)
    commitment = delivery(session, business, 10)

    # Everything that went out may come back.
    send_back(session, business, commitment, 10)

    # Nothing beyond it can, which is what makes the acceptance above a rule.
    with pytest.raises(InvalidOperation, match="shipped|went out|exceeds"):
        send_back(session, business, commitment, 1)


def test_a_return_leaves_the_promise_kept(session, business):
    stocked(session, business)
    commitment = delivery(session, business, 10)
    before = fulfilled_quantity(session, business.tenant.id, commitment.id)

    send_back(session, business, commitment, 10)

    # The promise was kept when the goods went out. A return does not undo that,
    # or a fully returned order would reopen as overdue and undelivered.
    assert fulfilled_quantity(session, business.tenant.id, commitment.id) == before
    assert open_quantity(session, business.tenant.id, commitment.id) == Decimal(0)
    classes = [
        row.class_id for row in operational_exceptions(session, business.tenant.id)
    ]
    assert "overdue_outgoing_customer_commitment" not in classes
    assert "outgoing_commitment_at_risk" not in classes


def test_a_returned_movement_is_still_correctable(session, business):
    stocked(session, business)
    commitment = delivery(session, business)
    movement = send_back(session, business, commitment, 3)

    result = correct_movement(
        session,
        business.tenant.id,
        movement.id,
        reason="Recorded against the wrong order",
    )

    assert result.original_movement_id == movement.id
    assert result.compensating_movement_id

    # And the voided return stops counting, so nothing has come back after all.
    assert returned_quantity(session, business.tenant.id, commitment.id) == Decimal(0)


def test_a_credit_note_line_credits_an_order_line(session, business):
    _, order_lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-CREDIT",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "90.00",
            }
        ],
        "90.00",
    )
    _, credit_lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "credit_note",
        "GS-1",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "4",
                "unit": "pcs",
                "unit_price": "9.00",
                "gross_amount": "36.00",
                "billed_document_line_id": order_lines[0].id,
            }
        ],
        "36.00",
    )

    assert credit_lines[0].billed_document_line_id == order_lines[0].id

    # A credit note is a sales-side document, so a purchase order line is not
    # something it can credit.
    _, purchase_lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "purchase_order",
        "PO-CREDIT",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit": "pcs",
                "unit_price": "5.00",
                "gross_amount": "50.00",
            }
        ],
        "50.00",
    )
    with pytest.raises(InvalidOperation, match="side"):
        create_manual_document_with_lines(
            session,
            business.tenant.id,
            "credit_note",
            "GS-WRONG",
            business.customer.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": "5.00",
                    "gross_amount": "5.00",
                    "billed_document_line_id": purchase_lines[0].id,
                }
            ],
            "5.00",
        )


# --- What happened to the goods (spec 081) ---------------------------------


def returns_area(session, business):
    from reality.services.core import create_location

    return create_location(session, business.tenant.id, "Returns Area")


def came_back(session, business, commitment, quantity, area):
    return record_movement(
        session,
        business.tenant.id,
        "return",
        business.item.id,
        quantity,
        to_location_id=area.id,
        commitment_id=commitment.id,
    )


def resolve(
    session,
    business,
    goods_back,
    quantity,
    *,
    area,
    to_location=None,
    item_id=None,
    reason=None,
    occurred_at=None,
):
    """Put the goods back on a shelf, or write them off."""
    return record_movement(
        session,
        business.tenant.id,
        "transfer" if to_location else "adjustment",
        item_id or business.item.id,
        quantity,
        from_location_id=area.id,
        to_location_id=to_location.id if to_location else None,
        reason=reason or (None if to_location else "Damaged beyond resale"),
        resolves_movement_id=goods_back.id,
        occurred_at=occurred_at,
    )


def test_a_movement_may_resolve_a_return(session, business):
    stocked(session, business)
    area = returns_area(session, business)
    commitment = delivery(session, business, 10)
    goods_back = came_back(session, business, commitment, 6, area)

    restocked = resolve(
        session, business, goods_back, 4, area=area, to_location=business.location
    )

    assert restocked.resolves_movement_id == goods_back.id

    # A movement that names nothing settles nothing, which is a statement.
    plain = record_movement(
        session,
        business.tenant.id,
        "adjustment",
        business.item.id,
        1,
        from_location_id=area.id,
        reason="Counted short",
    )
    assert plain.resolves_movement_id is None


def test_a_resolution_is_validated(session, business):
    from reality.services.core import create_item, create_location, create_tenant

    stocked(session, business)
    area = returns_area(session, business)
    commitment = delivery(session, business, 10)
    goods_back = came_back(session, business, commitment, 6, area)

    # A shipment is a real movement and not a return, so it settles nothing.
    from sqlalchemy import select

    from reality.db.core import Movement

    shipment = session.scalars(
        select(Movement).where(
            Movement.tenant_id == business.tenant.id, Movement.type == "shipment"
        )
    ).first()
    with pytest.raises(InvalidOperation, match="return"):
        record_movement(
            session,
            business.tenant.id,
            "adjustment",
            business.item.id,
            1,
            from_location_id=area.id,
            reason="Nonsense",
            resolves_movement_id=shipment.id,
        )

    # Another tenant's return is not reachable at all.
    foreign = create_tenant(session, "Foreign resolution tenant")
    with pytest.raises(NotFound):
        record_movement(
            session,
            foreign.id,
            "adjustment",
            business.item.id,
            1,
            from_location_id=area.id,
            reason="Nonsense",
            resolves_movement_id=goods_back.id,
        )

    # Another item never came back in this return.
    other_item = create_item(session, business.tenant.id, "BIKE-BELL", "Bike Bell")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        other_item.id,
        10,
        to_location_id=area.id,
    )
    with pytest.raises(InvalidOperation, match="item"):
        resolve(
            session,
            business,
            goods_back,
            1,
            area=area,
            to_location=business.location,
            item_id=other_item.id,
        )

    # And a movement that does not leave the place the goods came back to.
    elsewhere = create_location(session, business.tenant.id, "Other Warehouse")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=elsewhere.id,
    )
    with pytest.raises(InvalidOperation, match="location|came back"):
        record_movement(
            session,
            business.tenant.id,
            "transfer",
            business.item.id,
            1,
            from_location_id=elsewhere.id,
            to_location_id=business.location.id,
            resolves_movement_id=goods_back.id,
        )


def test_resolutions_may_not_exceed_what_came_back(session, business):
    stocked(session, business)
    area = returns_area(session, business)
    commitment = delivery(session, business, 10)
    goods_back = came_back(session, business, commitment, 6, area)

    # Everything that came back may be settled.
    resolve(
        session, business, goods_back, 6, area=area, to_location=business.location
    )

    # Nothing beyond it can, which is what makes the acceptance above a rule.
    with pytest.raises(InvalidOperation, match="came back|exceed"):
        resolve(
            session, business, goods_back, 1, area=area, to_location=business.location
        )


def test_a_return_may_be_resolved_in_parts(session, business):
    stocked(session, business)
    area = returns_area(session, business)
    commitment = delivery(session, business, 10)
    goods_back = came_back(session, business, commitment, 5, area)

    # Three go back on the shelf and two are written off: one return, two
    # movements, and each says what happened by being what it is.
    restocked = resolve(
        session, business, goods_back, 3, area=area, to_location=business.location
    )
    scrapped = resolve(session, business, goods_back, 2, area=area)

    assert restocked.type == "transfer"
    assert scrapped.type == "adjustment"
    assert restocked.resolves_movement_id == goods_back.id
    assert scrapped.resolves_movement_id == goods_back.id


def test_a_backdated_resolution_is_accepted(session, business):
    stocked(session, business)
    area = returns_area(session, business)
    commitment = delivery(session, business, 10)
    goods_back = came_back(session, business, commitment, 4, area)

    # Movement instants are caller-supplied everywhere in this product and
    # nothing else polices their order, so this one does not either.
    settled = resolve(
        session,
        business,
        goods_back,
        4,
        area=area,
        to_location=business.location,
        occurred_at=goods_back.occurred_at - timedelta(days=3),
    )

    assert settled.resolves_movement_id == goods_back.id


# --- Goods going back the other way (spec 090) -----------------------------


def supplier_delivery(session, business, quantity=100, *, received=None):
    """A supplier delivery promise with the goods already arrived."""
    commitment = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        quantity,
        "2026-12-01",
    )
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity if received is None else received,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    return commitment


def send_back_to_supplier(session, business, commitment, quantity, **kwargs):
    return record_movement(
        session,
        business.tenant.id,
        "supplier_return",
        business.item.id,
        quantity,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        **kwargs,
    )


def test_goods_go_back_to_the_supplier(session, business):
    from reality.services.core import stock_at

    tenant_id = business.tenant.id
    commitment = supplier_delivery(session, business, 100)
    assert stock_at(session, tenant_id, business.item.id) == Decimal(100)

    send_back_to_supplier(session, business, commitment, 10)

    # The goods are gone, and the figure is the one that was recorded.
    assert stock_at(session, tenant_id, business.item.id) == Decimal(90)

    # The supplier kept its word when the goods arrived, and sending some back
    # does not unmake that — exactly as a customer return does not reopen a
    # delivery the company kept.
    assert fulfilled_quantity(session, tenant_id, commitment.id) == Decimal(100)
    assert open_quantity(session, tenant_id, commitment.id) == Decimal(0)
    assert session.get(type(commitment), commitment.id).status == "fulfilled"

    # A customer return is the other direction and stays its own kind.
    assert returned_quantity(session, tenant_id, commitment.id) == Decimal(0)


def test_a_supplier_return_is_refused_without_its_delivery(session, business):
    from reality.services.core import create_item

    tenant_id = business.tenant.id
    stocked(session, business, 50)
    outgoing = delivery(session, business, 10)
    incoming = supplier_delivery(session, business, 100)

    # A customer delivery is reversed by a customer return, never by this.
    with pytest.raises(InvalidOperation, match="does not match the commitment"):
        send_back_to_supplier(session, business, outgoing, 1)

    # A commitment for another item is not this item's delivery. The other item
    # is stocked first, so what refuses this is the commitment rule rather than
    # the physical-stock rule that would otherwise answer first.
    other = create_item(session, tenant_id, "BIKE-BELL-090", "Bike Bell")
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        other.id,
        5,
        to_location_id=business.location.id,
    )
    with pytest.raises(InvalidOperation, match="does not match the commitment"):
        record_movement(
            session,
            tenant_id,
            "supplier_return",
            other.id,
            1,
            from_location_id=business.location.id,
            commitment_id=incoming.id,
        )

    # Goods have to come out of somewhere.
    with pytest.raises(InvalidOperation, match="Locations are incomplete"):
        record_movement(
            session,
            tenant_id,
            "supplier_return",
            business.item.id,
            1,
            to_location_id=business.location.id,
            commitment_id=incoming.id,
        )

    # The positive control: the same movement, correctly formed, is recorded.
    assert send_back_to_supplier(session, business, incoming, 1) is not None


def test_a_supplier_return_cannot_exceed_what_arrived(session, business):
    tenant_id = business.tenant.id
    commitment = supplier_delivery(session, business, 100)
    # Plenty of the same item from elsewhere, so the only rule that can refuse
    # anything below is the one this test is about: what arrived on *this*
    # delivery. Physical stock would otherwise answer first and say something
    # true but different.
    stocked(session, business, 500)

    # Everything promised has arrived, so the open quantity is zero — and a
    # return must still be possible, which is why the bound is what moved.
    assert open_quantity(session, tenant_id, commitment.id) == Decimal(0)
    send_back_to_supplier(session, business, commitment, 40)

    with pytest.raises(InvalidOperation, match="exceeds what was received"):
        send_back_to_supplier(session, business, commitment, 61)

    # The positive control: exactly what is left goes back.
    assert send_back_to_supplier(session, business, commitment, 60) is not None
    with pytest.raises(InvalidOperation, match="exceeds what was received"):
        send_back_to_supplier(session, business, commitment, 1)


def test_a_supplier_return_settles_a_customer_return(session, business):
    tenant_id = business.tenant.id
    stocked(session, business, 50)
    outgoing = delivery(session, business, 10)
    incoming = supplier_delivery(session, business, 100)
    came_back = record_movement(
        session,
        tenant_id,
        "return",
        business.item.id,
        4,
        to_location_id=business.location.id,
        commitment_id=outgoing.id,
    )

    # Spec 082 already named "a shipment to the supplier" as one of the things
    # that settles a return. This is that movement.
    send_back_to_supplier(
        session, business, incoming, 4, resolves_movement_id=came_back.id
    )

    from reality.services.core import movement_quantity_resolving

    assert movement_quantity_resolving(session, tenant_id, came_back.id) == Decimal(4)

    # Nothing may settle more than came back.
    with pytest.raises(InvalidOperation, match="exceed what came back"):
        send_back_to_supplier(
            session, business, incoming, 1, resolves_movement_id=came_back.id
        )


def test_a_corrected_supplier_return_stops_counting(session, business):
    from reality.services.core import movement_quantity

    tenant_id = business.tenant.id
    commitment = supplier_delivery(session, business, 100)
    wrong = send_back_to_supplier(session, business, commitment, 30)
    assert movement_quantity(
        session, tenant_id, commitment.id, "supplier_return"
    ) == Decimal(30)

    correct_movement(session, tenant_id, wrong.id, reason="recorded in error")

    # A voided movement stops counting here as everywhere else, so the whole
    # receipt can go back again.
    assert movement_quantity(
        session, tenant_id, commitment.id, "supplier_return"
    ) == Decimal(0)
    assert send_back_to_supplier(session, business, commitment, 100) is not None


def test_supplier_returns_are_tenant_scoped(session, business):
    from reality.services.core import create_tenant

    commitment = supplier_delivery(session, business, 10)
    foreign = create_tenant(session, "Foreign supplier return tenant")

    with pytest.raises(NotFound):
        record_movement(
            session,
            foreign.id,
            "supplier_return",
            business.item.id,
            1,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )

    # The positive control: its own tenant records it.
    assert send_back_to_supplier(session, business, commitment, 1) is not None
