"""Purchasing in a purchase unit (spec 301).

A purchase order line keeps the cartons it states; its promise, every receipt
and stock are in the item's stock unit, by the item's stated factor.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from reality.domain.units import (
    decline_reason,
    in_unit,
    line_in_promise,
    promise_held_unit,
    promise_in_line,
)

CARTONS = SimpleNamespace(
    unit="pcs", purchase_unit="box", conversion_factor=Decimal(12)
)


# --- T004: the shared rule, now in the domain --------------------------------------


@pytest.mark.parametrize(
    ("quantity", "recorded", "target", "expected"),
    [
        ("5", "box", "pcs", Decimal(60)),
        ("60", "pcs", "box", Decimal(5)),
        ("7", "pcs", "pcs", Decimal(7)),
        ("61", "pcs", "box", None),
        ("1", "pallet", "pcs", None),
    ],
)
def test_the_shared_rule_converts_only_what_the_item_states(
    quantity, recorded, target, expected
):
    assert in_unit(CARTONS, Decimal(quantity), recorded, target) == expected


def test_a_refusal_says_which_statement_is_missing():
    assert decline_reason(CARTONS, "pallet", "pcs") == "no_stated_relation"
    assert decline_reason(CARTONS, "pcs", "box") == "conversion_leaves_a_remainder"
    without = SimpleNamespace(unit="pcs", purchase_unit="box", conversion_factor=0)
    assert decline_reason(without, "box", "pcs") == "no_stated_relation"


def test_a_promise_says_which_unit_it_is_held_in():
    line = SimpleNamespace(unit="box", quantity=Decimal(5))
    # New: the promise recorded the stock unit it was made in.
    assert promise_held_unit("pcs", line, "pcs") == "pcs"
    # Recorded before spec 301: the promise took the line's cartons as stated.
    assert promise_held_unit(None, line, "pcs") == "box"
    # A promise without a line was always in the item's unit.
    assert promise_held_unit(None, None, "pcs") == "pcs"


def test_the_relation_fixed_at_ordering_converts_line_quantities():
    line = SimpleNamespace(unit="box", quantity=Decimal(5))
    # Five cartons promised as sixty pieces: twelve a carton, whatever the item
    # says today.
    assert line_in_promise(Decimal(3), line, Decimal(60), "pcs") == Decimal(36)
    assert promise_in_line(Decimal(36), line, Decimal(60), "pcs") == Decimal(3)
    # Half a carton is not a number of cartons.
    assert promise_in_line(Decimal(30), line, Decimal(60), "pcs") is None
    # A promise in its line's unit is read unchanged.
    assert line_in_promise(Decimal(3), line, Decimal(5), "box") == Decimal(3)
    assert promise_in_line(Decimal(3), line, Decimal(5), "box") == Decimal(3)


# --- T004: schema ---------------------------------------------------------------------


def test_a_stated_receipt_keeps_both_values_or_neither(session, business):
    from reality.db.core import Movement, uid

    tenant = business.tenant.id

    def insert(**stated):
        with session.begin_nested():
            session.add(
                Movement(
                    id=uid("mov"),
                    tenant_id=tenant,
                    type="receipt",
                    item_id=business.item.id,
                    quantity=Decimal(60),
                    to_location_id=business.location.id,
                    **stated,
                )
            )
            session.flush()

    # Positive control: both stated values together are accepted.
    insert(stated_quantity=Decimal(5), stated_unit="box")
    with pytest.raises(IntegrityError, match="ck_movement_stated_unit"):
        insert(stated_quantity=Decimal(5))


def test_the_migration_upgrades_downgrades_and_keeps_stated_receipts(
    postgres_database, monkeypatch
):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)

    def columns():
        return (
            {column["name"] for column in inspect(engine).get_columns("movement")}
            & {"stated_quantity", "stated_unit"}
        ) | {
            f"commitment.{column['name']}"
            for column in inspect(engine).get_columns("commitment")
            if column["name"] == "unit"
        }

    added = {"stated_quantity", "stated_unit", "commitment.unit"}

    try:
        assert columns() == added
        # Positive control: with nothing stated the downgrade removes them.
        command.downgrade(config, "0105_down_payments")
        assert columns() == set()
        command.upgrade(config, "head")

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tenant (id, name, purpose, created_at) "
                    "VALUES ('ten_m301', 'Migration 301', 'business', now())"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item (id, tenant_id, sku, name, unit, is_active, "
                    "item_type, tracking_type, purchase_unit, conversion_factor) "
                    "VALUES ('itm_m301', 'ten_m301', 'M301', 'Box item', 'pcs', true, "
                    "'stocked', 'none', 'box', 12)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO movement (id, tenant_id, type, item_id, quantity, "
                    "occurred_at, stated_quantity, stated_unit) VALUES ('mov_m301', "
                    "'ten_m301', 'receipt', 'itm_m301', 60, now(), 5, 'box')"
                )
            )
        with pytest.raises(RuntimeError, match="stated in a purchase unit"):
            command.downgrade(config, "0105_down_payments")
        assert columns() == added

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO commitment (id, tenant_id, type, item_id, quantity, "
                    "amount, currency, status, created_at, priority, unit) VALUES "
                    "('com_m301', 'ten_m301', 'supplier_delivery', 'itm_m301', 60, "
                    "0, 'EUR', 'open', now(), 'normal', 'pcs')"
                )
            )
        with pytest.raises(RuntimeError, match="held in the stock unit"):
            command.downgrade(config, "0105_down_payments")
        assert columns() == added
    finally:
        engine.dispose()


# --- T006: purchase orders and receipts in the purchase unit --------------------------


def _cartons(session, business):
    business.item.purchase_unit = "box"
    business.item.conversion_factor = Decimal(12)
    session.commit()
    return business.item


def _purchase(session, business, quantity, unit, number="PO-301"):
    from reality.services import core

    return core.create_manual_order(
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
                "unit_price": "60.00",
                "gross_amount": str(Decimal(quantity) * 60),
            }
        ],
        str(Decimal(quantity) * 60),
    )


def _receive(session, business, commitment, quantity, unit=None):
    from reality.services import core

    return core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=commitment.id,
        unit=unit,
    )


def test_a_purchase_in_cartons_keeps_the_line_and_promises_pieces(session, business):
    _cartons(session, business)

    _, _, lines, commitments = _purchase(session, business, "5", "box")

    assert (lines[0].quantity, lines[0].unit) == (Decimal("5.0000"), "box")
    assert (commitments[0].quantity, commitments[0].unit) == (
        Decimal("60.0000"),
        "pcs",
    )


def test_a_purchase_in_the_stock_unit_is_unchanged(session, business):
    _cartons(session, business)

    _, _, lines, commitments = _purchase(session, business, "7", "pcs")

    assert (lines[0].quantity, commitments[0].quantity) == (
        Decimal("7.0000"),
        Decimal("7.0000"),
    )


def test_a_purchase_in_a_unit_without_a_conversion_is_refused(session, business):
    from reality.services import core

    _cartons(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        _purchase(session, business, "1", "pallet")
    assert refused.value.code == "purchase_unit_not_convertible"


def test_a_receipt_in_cartons_records_pieces_and_keeps_what_was_stated(
    session, business
):
    from reality.services import core

    tenant = business.tenant.id
    _cartons(session, business)
    _, _, _, commitments = _purchase(session, business, "5", "box")

    movement = _receive(session, business, commitments[0], "5", unit="box")

    assert (movement.quantity, movement.stated_quantity, movement.stated_unit) == (
        Decimal("60.0000"),
        Decimal("5.0000"),
        "box",
    )
    assert core.stock_at(session, tenant, business.item.id) == Decimal("60.0000")
    assert core.open_quantity(session, tenant, commitments[0].id) == 0


def test_a_receipt_in_the_stock_unit_is_unchanged(session, business):
    _cartons(session, business)
    _, _, _, commitments = _purchase(session, business, "5", "box")

    movement = _receive(session, business, commitments[0], "24")

    assert (movement.quantity, movement.stated_quantity, movement.stated_unit) == (
        Decimal("24.0000"),
        None,
        None,
    )


def test_a_receipt_in_a_unit_without_a_conversion_is_refused(session, business):
    from reality.services import core

    _cartons(session, business)
    _, _, _, commitments = _purchase(session, business, "5", "box")

    with pytest.raises(core.InvalidOperation) as refused:
        _receive(session, business, commitments[0], "1", unit="pallet")
    assert refused.value.code == "movement_unit_not_convertible"
    # A shipment is not a purchase: no unit other than the stock unit.
    with pytest.raises(core.InvalidOperation) as refused:
        core.record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            business.item.id,
            "1",
            to_location_id=business.location.id,
            unit="box",
        )
    assert refused.value.code == "movement_unit_not_convertible"


def test_more_cartons_than_ordered_are_refused_in_pieces(session, business):
    from reality.services import core

    _cartons(session, business)
    _, _, _, commitments = _purchase(session, business, "5", "box")
    # Positive control: exactly the ordered cartons are accepted.
    _receive(session, business, commitments[0], "4", unit="box")

    with pytest.raises(core.InvalidOperation) as refused:
        _receive(session, business, commitments[0], "2", unit="box")
    assert refused.value.code == "movement_exceeds_commitment_open_quantity"


def test_sales_purchase_unit_needs_its_own_supported_conversion(session, business):
    from reality.services import core

    _cartons(session, business)
    # Spec 379 supersedes the earlier permissive sales control: the purchase
    # relation does not authorize interpreting a sales box count as stock pieces.
    with pytest.raises(core.InvalidOperation) as refused:
        core.create_manual_order(
            session,
            business.tenant.id,
            "sales",
            "SO-301",
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "2",
                    "unit": "box",
                    "unit_price": "100",
                    "gross_amount": "200",
                }
            ],
            "200",
        )
    assert refused.value.code == "source_quantity_unit_unsupported"


# --- T008: readers --------------------------------------------------------------------


def _supplier_invoice(session, business, line, quantity, number):
    from reality.services import core

    return core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_invoice",
        number,
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": quantity,
                "unit": "box",
                "unit_price": "60.00",
                "gross_amount": str(Decimal(quantity) * 60),
                "billed_document_line_id": line.id,
            }
        ],
        str(Decimal(quantity) * 60),
    )


def _classes(session, business, class_id):
    from reality.services.exceptions import operational_exceptions

    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


def test_an_invoice_in_cartons_matches_the_pieces_received(session, business):
    _cartons(session, business)
    _, _, lines, commitments = _purchase(session, business, "5", "box")
    _receive(session, business, commitments[0], "3", unit="box")
    _supplier_invoice(session, business, lines[0], "5", "ER-301")

    # Control: 5 cartons billed against 3 received is 24 pieces not received.
    row = _classes(session, business, "billed_not_received")[lines[0].id]
    assert (row.causal_values["unreceived_quantity"], row.causal_values["unit"]) == (
        Decimal("24.0000"),
        "pcs",
    )

    _receive(session, business, commitments[0], "2", unit="box")
    assert lines[0].id not in _classes(session, business, "billed_not_received")
    assert lines[0].id not in _classes(session, business, "receipt_unbilled")


def test_an_oversold_item_counts_a_purchase_in_cartons_once(session, business):
    from reality.services import core

    _cartons(session, business)
    _purchase(session, business, "2", "box")
    core.create_manual_order(
        session,
        business.tenant.id,
        "sales",
        "SO-301-O",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "25",
                "unit_price": "10",
                "gross_amount": "250",
            }
        ],
        "250",
    )

    row = _classes(session, business, "item_oversold")[business.item.id]
    # Two cartons are 24 pieces on their way, not 288.
    assert (
        row.causal_values["incoming_quantity"],
        row.causal_values["shortfall_quantity"],
    ) == (
        Decimal("24.0000"),
        Decimal("1.0000"),
    )


def test_a_purchase_recorded_before_in_cartons_is_named(session, business):
    from reality.services import core

    tenant = business.tenant.id
    _cartons(session, business)
    # Control: a purchase recorded now in cartons is held in pieces, nothing named.
    _purchase(session, business, "5", "box", number="PO-NEW")
    assert business.item.id not in _classes(session, business, "units_not_comparable")

    document, lines = core.create_manual_document_with_lines(
        session,
        tenant,
        "purchase_order",
        "PO-OLD",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit": "box",
                "unit_price": "60",
                "gross_amount": "300",
            }
        ],
        "300",
    )
    core.create_commitment(
        session,
        tenant,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "5",
        None,
        document_id=document.id,
        document_line_id=lines[0].id,
    )

    row = _classes(session, business, "units_not_comparable")[business.item.id]
    assert row.causal_values["reason"] == "promise_in_purchase_unit"
    assert lines[0].id in row.trace["document_line_ids"]


def test_the_delivery_case_reads_a_purchase_in_both_units(session, business):
    from reality.services.delivery_reads import delivery_case

    tenant = business.tenant.id
    _cartons(session, business)
    _, _, _, commitments = _purchase(session, business, "5", "box")
    _receive(session, business, commitments[0], "2", unit="box")

    case = delivery_case(session, tenant, commitments[0].id)["case"]
    assert (case["promised"], case["open"], case["unit"]) == (
        "60.0000",
        "36.0000",
        "pcs",
    )
    assert case["purchase_unit"] == {
        "unit": "box",
        "conversion_factor": "12",
        "ordered": "5",
        "open": "3",
        "received": "2",
    }

    # Control: a purchase in the stock unit has no second view.
    _, _, _, plain = _purchase(session, business, "7", "pcs", number="PO-PCS")
    assert "purchase_unit" not in delivery_case(session, tenant, plain[0].id)["case"]


# --- T016: review fixes ---------------------------------------------------------------


def _legacy_purchase(session, business, number="PO-OLD"):
    """A purchase in cartons recorded before spec 301: promised as stated."""
    from reality.services import core

    tenant = business.tenant.id
    document, lines = core.create_manual_document_with_lines(
        session,
        tenant,
        "purchase_order",
        number,
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit": "box",
                "unit_price": "60",
                "gross_amount": "300",
            }
        ],
        "300",
    )
    commitment = core.create_commitment(
        session,
        tenant,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "5",
        None,
        document_id=document.id,
        document_line_id=lines[0].id,
    )
    return lines[0], commitment


def test_a_factor_changed_after_ordering_changes_no_promise(session, business):
    from reality.services.delivery_reads import delivery_case

    tenant = business.tenant.id
    _cartons(session, business)
    _, _, lines, commitments = _purchase(session, business, "5", "box")
    _receive(session, business, commitments[0], "3", unit="box")
    _supplier_invoice(session, business, lines[0], "5", "ER-301-F")

    # The company now buys cartons of ten. The order was placed for twelve.
    business.item.conversion_factor = Decimal(10)
    session.commit()

    row = _classes(session, business, "billed_not_received")[lines[0].id]
    assert (row.causal_values["unreceived_quantity"], row.causal_values["unit"]) == (
        Decimal("24.0000"),
        "pcs",
    )
    purchase = delivery_case(session, tenant, commitments[0].id)["case"][
        "purchase_unit"
    ]
    assert (purchase["conversion_factor"], purchase["open"]) == ("12", "2")
    # Nor does it make the new promise look recorded the old way.
    assert business.item.id not in _classes(session, business, "units_not_comparable")


def test_an_order_recorded_before_cannot_take_a_receipt_in_cartons(session, business):
    from reality.services import core

    _cartons(session, business)
    _, commitment = _legacy_purchase(session, business)

    with pytest.raises(core.InvalidOperation) as refused:
        _receive(session, business, commitment, "5", unit="box")
    assert refused.value.code == "movement_promise_in_line_unit"
    # Positive control: received as its line states, as before.
    assert _receive(session, business, commitment, "5").quantity == Decimal("5.0000")


def test_billable_positions_of_a_purchase_in_cartons_are_in_cartons(
    session, business
):
    from reality.services.invoice_billing import billable_positions

    _cartons(session, business)
    _, _, lines, commitments = _purchase(session, business, "5", "box")
    _receive(session, business, commitments[0], "3", unit="box")

    def position():
        orders = billable_positions(
            session,
            business.tenant.id,
            direction="purchase",
            party_id=business.supplier.id,
            currency="EUR",
        )["orders"]
        return [row for order in orders for row in order["positions"]]

    (row,) = position()
    assert (row["unit"], row["delivered"], row["billable"]) == (
        "box",
        Decimal("3.0000"),
        Decimal("3.0000"),
    )
    _supplier_invoice(session, business, lines[0], "3", "ER-301-B")
    # Three cartons received and three billed leaves nothing, not 33.
    assert position() == []
    # Half a carton is not offered rather than rounded.
    _receive(session, business, commitments[0], "6")
    assert position() == []


def test_the_purchase_view_reads_the_promise_in_force(session, business):
    from reality.services import core
    from reality.services.delivery_reads import delivery_case

    tenant = business.tenant.id
    _cartons(session, business)
    _, _, _, commitments = _purchase(session, business, "5", "box")
    core.revise_commitment(session, tenant, commitments[0].id, quantity="48")

    purchase = delivery_case(session, tenant, commitments[0].id)["case"][
        "purchase_unit"
    ]
    assert (purchase["ordered"], purchase["open"]) == ("4", "4")


def test_a_conversion_that_does_not_divide_is_named_before_an_old_purchase(
    session, business
):
    from reality.services import core

    _cartons(session, business)
    line, _ = _legacy_purchase(session, business)
    # Control: the old purchase alone is named as such.
    assert (
        _classes(session, business, "units_not_comparable")[business.item.id]
        .causal_values["reason"]
        == "promise_in_purchase_unit"
    )

    core.create_manual_document_with_lines(
        session,
        business.tenant.id,
        "supplier_invoice",
        "ER-301-R",
        business.supplier.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "61",
                "unit": "pcs",
                "unit_price": "5",
                "gross_amount": "305",
                "billed_document_line_id": line.id,
            }
        ],
        "305",
    )

    row = _classes(session, business, "units_not_comparable")[business.item.id]
    # The one that asks for a decision is what the entry says.
    assert row.causal_values["reason"] == "conversion_leaves_a_remainder"
