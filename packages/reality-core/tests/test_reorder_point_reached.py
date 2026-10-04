"""Reorder point reached (spec 302 FR-002, FR-003)."""

from decimal import Decimal

from intake_review_support import (
    reviewed_add_party_group_member,
    reviewed_assign_group_price_list,
    reviewed_assign_party_price_list,
    reviewed_create_party_group,
    reviewed_create_price_list,
    reviewed_create_price_list_entry,
    reviewed_manual_document_with_lines,
    reviewed_manual_order,
    reviewed_release_reservation,
    reviewed_reserve,
    reviewed_set_master_data_active,
)
from sqlalchemy import event

from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.reorder_points import set_reorder_point


def _reached(session, tenant_id):
    rows = [
        row
        for row in operational_exceptions(session, tenant_id)
        if row.class_id == "reorder_point_reached"
    ]
    # One entry per point: a duplicate would hide in the dict below.
    assert len({row.id for row in rows}) == len(rows)
    return {(row.trace["item_id"], row.trace["location_id"]): row for row in rows}


def _stock(session, business, quantity, location=None, item=None):
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        (item or business.item).id,
        quantity,
        to_location_id=(location or business.location).id,
    )


def _point(session, business, point="20", quantity="48", location=None, item=None):
    return set_reorder_point(
        session,
        business.tenant.id,
        (item or business.item).id,
        (location or business.location).id,
        point,
        quantity,
    )


def _order(session, business, direction, number, quantity, unit=None, location=None):
    _, _, _, promises = reviewed_manual_order(
        session,
        business.tenant.id,
        direction,
        number,
        business.company.id,
        business.customer.id if direction == "sales" else business.supplier.id,
        (location or business.location).id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit_price": "5",
                "gross_amount": str(Decimal(quantity) * 5),
                **({"unit": unit} if unit else {}),
            }
        ],
        str(Decimal(quantity) * 5),
    )
    return promises[0]


def _purchase_list(
    session, business, supplier=None, price="4.50", unit="pcs", code="PL"
):
    tenant = business.tenant.id
    price_list = reviewed_create_price_list(session, tenant, code, code, "purchase", "EUR")
    reviewed_create_price_list_entry(
        session, tenant, price_list.id, business.item.id, "1", price, unit
    )
    if supplier is not None:
        reviewed_assign_party_price_list(session, tenant, supplier.id, price_list.id)
    return price_list


def _cartons(session, business):
    business.item.purchase_unit = "box"
    business.item.conversion_factor = Decimal(12)
    session.commit()


# --- the condition ---------------------------------------------------------------------


def test_at_or_below_the_point_is_reported_and_above_is_not(session, business):
    tenant = business.tenant.id
    _point(session, business, point="20")
    _stock(session, business, "21")
    # Control: one above the point is not reported.
    assert _reached(session, tenant) == {}

    core.record_movement(
        session,
        tenant,
        "adjustment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        reason="count",
    )
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.severity == "normal"
    assert row.record_type == "reorder_point"
    assert (
        row.causal_values["reorder_point"],
        row.causal_values["available_quantity"],
        row.causal_values["incoming_quantity"],
        row.causal_values["proposed_quantity"],
        row.causal_values["proposed_unit"],
    ) == (Decimal(20), Decimal(20), Decimal(0), Decimal(48), "pcs")


def test_only_the_location_below_its_point_is_reported(session, business):
    tenant = business.tenant.id
    munich = reviewed_create_location(session, tenant, "Munich")
    _stock(session, business, "12")
    _stock(session, business, "100", location=munich)
    _point(session, business)
    _point(session, business, location=munich)

    assert set(_reached(session, tenant)) == {(business.item.id, business.location.id)}


def test_an_item_without_a_point_is_never_reported(session, business):
    tenant = business.tenant.id
    _order(session, business, "sales", "SO-NP", "5")
    assert _reached(session, tenant) == {}
    # Positive control: the same empty stock with a point is reported.
    _point(session, business, point="0")
    assert set(_reached(session, tenant)) == {(business.item.id, business.location.id)}


def test_active_reservations_reduce_what_is_available(session, business):
    tenant = business.tenant.id
    _stock(session, business, "30")
    _point(session, business, point="20")
    sale = _order(session, business, "sales", "SO-R", "15")
    # Control: an unreserved sale does not touch the stock at the location.
    assert _reached(session, tenant) == {}

    reserved = reviewed_reserve(session, tenant, sale.id)
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["available_quantity"] == Decimal(15)

    reviewed_release_reservation(session, tenant, reserved.reservation.id)
    assert _reached(session, tenant) == {}


def test_an_open_purchase_to_the_location_counts_as_incoming(session, business):
    tenant = business.tenant.id
    elsewhere = reviewed_create_location(session, tenant, "Munich")
    _stock(session, business, "12")
    _point(session, business, point="20")
    # A purchase to another location does not help this one.
    _order(session, business, "purchase", "PO-ELSE", "48", location=elsewhere)
    assert (business.item.id, business.location.id) in _reached(session, tenant)

    purchase = _order(session, business, "purchase", "PO-HERE", "48")
    assert _reached(session, tenant) == {}

    # Received, the goods count as stock instead of incoming: still covered.
    core.record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "48",
        to_location_id=business.location.id,
        commitment_id=purchase.id,
    )
    assert _reached(session, tenant) == {}


def test_a_cancelled_or_revised_purchase_counts_as_it_now_stands(session, business):
    tenant = business.tenant.id
    _stock(session, business, "12")
    _point(session, business, point="20")
    purchase = _order(session, business, "purchase", "PO-REV", "48")
    assert _reached(session, tenant) == {}

    core.revise_commitment(session, tenant, purchase.id, quantity="4")
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["incoming_quantity"] == Decimal(4)

    core.cancel_commitment(session, tenant, purchase.id, reason="supplier cannot")
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["incoming_quantity"] == Decimal(0)


def test_an_old_purchase_in_cartons_counts_by_the_factor(session, business):
    tenant = business.tenant.id
    _cartons(session, business)
    _stock(session, business, "12")
    _point(session, business, point="20")
    # Recorded before spec 301: the promise holds the line's two cartons.
    document, lines = reviewed_manual_document_with_lines(
        session,
        tenant,
        "purchase_order",
        "PO-OLD",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit": "box",
                "unit_price": "60",
                "gross_amount": "120",
            }
        ],
        "120",
    )
    core.create_commitment(
        session,
        tenant,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "2",
        None,
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    # Two cartons are 24 pieces: 12 + 24 is above 20.
    assert _reached(session, tenant) == {}


# --- the proposal ----------------------------------------------------------------------


def test_the_quantity_is_proposed_in_cartons_when_it_divides(session, business):
    tenant = business.tenant.id
    _cartons(session, business)
    _point(session, business, point="20", quantity="48")
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert (
        row.causal_values["proposed_quantity"],
        row.causal_values["proposed_unit"],
    ) == (
        Decimal(4),
        "box",
    )

    _point(session, business, point="20", quantity="50")
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    # Fifty pieces are not a number of cartons; they are not rounded into five.
    assert (
        row.causal_values["proposed_quantity"],
        row.causal_values["proposed_unit"],
    ) == (
        Decimal(50),
        "pcs",
    )


def test_one_supplier_on_a_purchase_list_is_named_with_its_price(session, business):
    tenant = business.tenant.id
    _point(session, business)
    _purchase_list(session, business, business.supplier, price="4.50")

    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["supplier_choice"] == "single"
    assert row.causal_values["supplier"] == business.supplier.name
    assert row.causal_values["unit_price"] == Decimal("4.5000")
    assert row.trace["supplier_id"] == business.supplier.id
    assert row.trace["price_list_entry_id"]


def test_a_supplier_reached_through_its_group_is_named(session, business):
    tenant = business.tenant.id
    _point(session, business)
    price_list = _purchase_list(session, business, price="4.00")
    group = reviewed_create_party_group(session, tenant, "SUP", "Suppliers")
    reviewed_add_party_group_member(session, tenant, group.id, business.supplier.id)
    reviewed_assign_group_price_list(session, tenant, group.id, price_list.id)

    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert (row.causal_values["supplier_choice"], row.causal_values["unit_price"]) == (
        "single",
        Decimal("4.0000"),
    )


def test_a_price_in_cartons_prices_a_proposal_in_cartons(session, business):
    tenant = business.tenant.id
    _cartons(session, business)
    _point(session, business, point="20", quantity="48")
    _purchase_list(session, business, business.supplier, price="54", unit="box")

    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert (
        row.causal_values["proposed_quantity"],
        row.causal_values["proposed_unit"],
        row.causal_values["unit_price"],
    ) == (Decimal(4), "box", Decimal("54.0000"))


def test_several_or_no_suppliers_name_none(session, business):
    tenant = business.tenant.id
    _point(session, business)
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert (row.causal_values["supplier_choice"], row.causal_values["supplier"]) == (
        "none",
        "",
    )
    assert "unit_price" not in row.causal_values

    _purchase_list(session, business, business.supplier, code="PL-A")
    second = reviewed_create_party(session, tenant, "Lights Wholesale GmbH", "supplier")
    _purchase_list(session, business, second, price="4.20", code="PL-B")
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert (row.causal_values["supplier_choice"], row.causal_values["supplier"]) == (
        "several",
        "",
    )
    assert set(row.trace["supplier_ids"]) == {business.supplier.id, second.id}


def test_a_sales_list_never_names_a_supplier(session, business):
    tenant = business.tenant.id
    _point(session, business)
    sales = reviewed_create_price_list(session, tenant, "SL", "Retail", "sales", "EUR")
    reviewed_create_price_list_entry(
        session, tenant, sales.id, business.item.id, "1", "9.90", "pcs"
    )
    reviewed_assign_party_price_list(session, tenant, business.supplier.id, sales.id)

    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["supplier_choice"] == "none"
    # Positive control: the same assignment on a purchase list names the supplier.
    _purchase_list(session, business, business.supplier)
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["supplier_choice"] == "single"


def test_a_removed_point_reports_nothing(session, business):
    from reality.services.reorder_points import remove_reorder_point

    tenant = business.tenant.id
    _point(session, business)
    assert _reached(session, tenant)
    remove_reorder_point(session, tenant, business.item.id, business.location.id)
    assert _reached(session, tenant) == {}


# --- bounds and scope ------------------------------------------------------------------


def test_the_statement_count_does_not_grow_with_points(session, business):
    from reality.services.exceptions import _reorder_point_reached_exceptions

    tenant = business.tenant.id
    second = reviewed_create_party(session, tenant, "Lights Wholesale GmbH", "supplier")

    def statements(points):
        for index in range(points):
            item = reviewed_create_item(session, tenant, f"SKU-R-{points}-{index}", "R")
            _stock(session, business, "1", item=item)
            _point(session, business, point="5", quantity="10", item=item)
            # Two suppliers price each item: named as several, priced by nobody.
            for supplier in (business.supplier, second):
                price_list = reviewed_create_price_list(
                    session,
                    tenant,
                    f"PL-{points}-{index}-{supplier.id}",
                    "P",
                    "purchase",
                    "EUR",
                )
                reviewed_create_price_list_entry(
                    session, tenant, price_list.id, item.id, "1", "1", "pcs"
                )
                reviewed_assign_party_price_list(
                    session, tenant, supplier.id, price_list.id
                )
        count = 0

        def counter(*_):
            nonlocal count
            count += 1

        engine = session.get_bind()
        event.listen(engine, "before_cursor_execute", counter)
        try:
            found = _reorder_point_reached_exceptions(session, tenant, core.now())
        finally:
            event.remove(engine, "before_cursor_execute", counter)
        assert len(found) == points + (2 if points == 20 else 0)
        return count

    assert statements(2) == statements(20)


def test_another_company_sees_none_of_it(session, business):
    tenant = business.tenant.id
    _point(session, business)
    other = core.create_tenant(session, "Other GmbH")
    assert _reached(session, other.id) == {}
    assert _reached(session, tenant)


def test_the_stored_inbox_follows_a_purchase_and_a_price_list(session, business):
    """The refresh after each change is what the inbox shows (spec 181 narrowing)."""
    from reality.services import projections
    from reality.services.attention_reads import stored_exceptions

    tenant = business.tenant.id
    _stock(session, business, "12")
    _point(session, business, point="20")
    projections.refresh_operational_projections(session, tenant, force=True)

    def stored():
        rows, _ = stored_exceptions(session, tenant)
        return [row for row in rows if row["class_id"] == "reorder_point_reached"]

    (row,) = stored()
    assert row["causal_values"]["supplier_choice"] == "none"

    # A purchase price list is a change the entry has to follow.
    _purchase_list(session, business, business.supplier)
    projections.refresh_operational_projections(session, tenant)
    (row,) = stored()
    assert row["causal_values"]["supplier_choice"] == "single"

    _order(session, business, "purchase", "PO-STORED", "48")
    projections.refresh_operational_projections(session, tenant)
    assert stored() == []


# --- review round (T016) ---------------------------------------------------------------


def test_a_point_that_no_longer_qualifies_proposes_nothing(session, business):
    """An item made inactive or a service, or a place without stock, is not judged."""
    from reality.db.core import Item, Location
    from reality.services import projections
    from reality.services.attention_reads import stored_exceptions

    tenant = business.tenant.id
    _point(session, business)
    projections.refresh_operational_projections(session, tenant, force=True)
    key = (business.item.id, business.location.id)
    # Positive control: the qualifying point is reported, live and stored.
    assert key in _reached(session, tenant)

    reviewed_set_master_data_active(session, tenant, Item, business.item.id, False)
    assert _reached(session, tenant) == {}
    # The deactivation is a change the stored inbox follows.
    projections.refresh_operational_projections(session, tenant)
    rows, _ = stored_exceptions(session, tenant)
    assert not [row for row in rows if row["class_id"] == "reorder_point_reached"]

    reviewed_set_master_data_active(session, tenant, Item, business.item.id, True)
    assert key in _reached(session, tenant)
    reviewed_set_master_data_active(session, tenant, Location, business.location.id, False)
    assert _reached(session, tenant) == {}
    reviewed_set_master_data_active(session, tenant, Location, business.location.id, True)
    business.location.allows_stock = False
    session.commit()
    assert _reached(session, tenant) == {}
    business.location.allows_stock = True
    business.item.item_type = "service"
    session.commit()
    assert _reached(session, tenant) == {}


def test_an_inactive_supplier_is_not_named(session, business):
    from reality.db.core import Party

    tenant = business.tenant.id
    _point(session, business)
    _purchase_list(session, business, business.supplier)
    key = (business.item.id, business.location.id)
    assert _reached(session, tenant)[key].causal_values["supplier_choice"] == "single"

    reviewed_set_master_data_active(session, tenant, Party, business.supplier.id, False)
    assert _reached(session, tenant)[key].causal_values["supplier_choice"] == "none"


def test_the_supplier_own_list_is_priced_before_its_group_list(session, business):
    """The price rule tries a supplier's own lists first; so does the currency asked."""
    tenant = business.tenant.id
    _point(session, business)
    own = reviewed_create_price_list(session, tenant, "OWN", "Own", "purchase", "EUR")
    reviewed_create_price_list_entry(
        session, tenant, own.id, business.item.id, "1", "4.50", "pcs"
    )
    reviewed_assign_party_price_list(
        session, tenant, business.supplier.id, own.id, priority=5
    )
    shared = reviewed_create_price_list(session, tenant, "GRP", "Group", "purchase", "USD")
    reviewed_create_price_list_entry(
        session, tenant, shared.id, business.item.id, "1", "3.90", "pcs"
    )
    group = reviewed_create_party_group(session, tenant, "SUP", "Suppliers")
    reviewed_add_party_group_member(session, tenant, group.id, business.supplier.id)
    reviewed_assign_group_price_list(session, tenant, group.id, shared.id, priority=1)

    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert (row.causal_values["currency"], row.causal_values["unit_price"]) == (
        "EUR",
        Decimal("4.5000"),
    )


def test_a_purchase_the_item_cannot_convert_is_named_not_dropped(session, business):
    tenant = business.tenant.id
    _stock(session, business, "12")
    _point(session, business, point="20")
    document, lines = reviewed_manual_document_with_lines(
        session,
        tenant,
        "purchase_order",
        "PO-PALLET",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit": "pallet",
                "unit_price": "500",
                "gross_amount": "500",
            }
        ],
        "500",
    )
    core.create_commitment(
        session,
        tenant,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "1",
        None,
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    row = _reached(session, tenant)[(business.item.id, business.location.id)]
    assert row.causal_values["incoming_quantity"] == Decimal(0)
    assert row.causal_values["incoming_not_comparable"] == 1


def test_each_priced_entry_costs_the_same_fixed_price_lookup(session, business):
    """One supplier per item is priced by the shared rule: a fixed cost per entry.

    The rule reads each list assigned to the supplier, so the cost per entry is
    that of one supplier's lists; here the supplier has the usual one list.
    """
    from reality.services.exceptions import _reorder_point_reached_exceptions

    tenant = business.tenant.id
    price_list = reviewed_create_price_list(session, tenant, "PL-P", "P", "purchase", "EUR")
    reviewed_assign_party_price_list(session, tenant, business.supplier.id, price_list.id)
    made = 0

    def statements(points):
        nonlocal made
        for _ in range(points - made):
            item = reviewed_create_item(session, tenant, f"SKU-P-{made}", "P")
            _stock(session, business, "1", item=item)
            _point(session, business, point="5", quantity="10", item=item)
            reviewed_create_price_list_entry(
                session, tenant, price_list.id, item.id, "1", "1", "pcs"
            )
            made += 1
        count = 0

        def counter(*_):
            nonlocal count
            count += 1

        engine = session.get_bind()
        event.listen(engine, "before_cursor_execute", counter)
        try:
            found = _reorder_point_reached_exceptions(session, tenant, core.now())
        finally:
            event.remove(engine, "before_cursor_execute", counter)
        assert all(row.causal_values["supplier_choice"] == "single" for row in found)
        assert len(found) == points
        return count

    two, three, twenty = statements(2), statements(3), statements(20)
    per_entry = three - two
    # Linear in the priced entries and nothing more; the grouped reads stay fixed.
    assert twenty - two == 18 * per_entry
    # resolve_price: party, item, own links, group links, defaults, list, entries.
    assert per_entry == 7


from intake_review_support import (
    reviewed_create_item,
    reviewed_create_location,
    reviewed_create_party,
)
