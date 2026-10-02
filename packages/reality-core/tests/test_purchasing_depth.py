"""Spec 310: confirmed prices, supplier item terms, cancellation charges, three-way match."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from reality.db.core import DocumentLine, SourceRecord
from reality.services import core
from reality.services.exceptions import operational_exceptions
from reality.services.invoice_actions import record_free_supplier_invoice
from reality.services.purchase_match import purchase_match
from reality.services.supplier_item_terms import (
    order_terms_check,
    remove_supplier_item_terms,
    set_supplier_item_terms,
    supplier_item_terms,
)


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _purchase(session, business, number, quantity="100", price="10"):
    gross = str(Decimal(quantity) * Decimal(price))
    _, document, (line,), (promise,) = core.create_manual_order(
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
                "unit_price": price,
                "gross_amount": gross,
            }
        ],
        gross,
    )
    return document, line, promise


def _receive(session, business, promise, quantity):
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        quantity,
        to_location_id=business.location.id,
        commitment_id=promise.id,
    )


def _invoice(session, business, line, quantity, gross, number):
    receipt = core.record_supplier_invoice(
        session, business.tenant.id, line.id, quantity, gross, number
    )
    return next(row["id"] for row in receipt["records"] if row["family"] == "document")


def _findings(session, business, class_id):
    return {
        row.record_id: row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == class_id
    }


# --- Confirmed price (FR-001) ------------------------------------------------------


def test_a_supplier_confirms_quantity_date_and_price(session, business):
    tenant = business.tenant.id
    document, line, promise = _purchase(session, business, "PO-310-1")

    core.revise_commitment(
        session,
        tenant,
        promise.id,
        "2026-11-10T00:00:00Z",
        quantity="90",
        unit_price="10.50",
        note="Supplier confirmation AB-1",
    )

    assert core._agreed_line_prices(session, tenant, [line])[line.id] == Decimal("10.5")
    assert (
        core.commitment_terms(session, tenant, [promise.id])[promise.id].quantity == 90
    )
    _receive(session, business, promise, "90")
    invoice = _invoice(session, business, line, "90", "945", "INV-310-1")
    billed = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == invoice
        )
    )
    # The guided invoice takes the confirmed price; nothing differs.
    assert billed.unit_price == Decimal("10.5")
    assert billed.id not in _findings(session, business, "invoice_price_differs")
    match = purchase_match(session, tenant, document.id)
    assert match["matched"] is True
    (row,) = match["lines"]
    assert (
        row["ordered"],
        row["in_force"],
        row["ordered_unit_price"],
        row["agreed_unit_price"],
    ) == (
        "100",
        "90",
        "10",
        "10.5",
    )


def test_an_invoice_above_the_confirmed_price_is_reported_against_it(session, business):
    from reality.services.invoice_actions import record_free_supplier_invoice

    tenant = business.tenant.id
    _, line, promise = _purchase(session, business, "PO-310-2")
    core.revise_commitment(session, tenant, promise.id, unit_price="10.50")
    _receive(session, business, promise, "100")
    receipt = record_free_supplier_invoice(
        session,
        tenant,
        supplier_id=business.supplier.id,
        number="INV-310-2",
        currency="EUR",
        gross_amount="1100",
        lines=[
            {
                "item_id": business.item.id,
                "quantity": "100",
                "unit_price": "11",
                "gross_amount": "1100",
                "billed_document_line_id": line.id,
            }
        ],
    )
    billed_line = next(
        r["id"] for r in receipt["records"] if r["family"] == "document_line"
    )

    finding = _findings(session, business, "invoice_price_differs")[billed_line]
    assert finding.causal_values["agreed_unit_price"] == Decimal("10.5")


def test_a_price_is_confirmed_for_purchases_only(session, business):
    tenant = business.tenant.id
    _, _, _, (customer_promise,) = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-310",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "10",
                "gross_amount": "10",
            }
        ],
        "10",
    )
    _refused(
        "commitment_price_purchase_only",
        lambda: core.revise_commitment(
            session, tenant, customer_promise.id, unit_price="9"
        ),
    )
    _, _, promise = _purchase(session, business, "PO-310-3")
    _refused(
        "commitment_price_invalid",
        lambda: core.revise_commitment(session, tenant, promise.id, unit_price="-1"),
    )
    # Positive control: a purchase price alone is a revision.
    assert core.revise_commitment(session, tenant, promise.id, unit_price="9.9")


def test_the_review_shows_the_ordered_and_the_confirmed_price(session, business):
    from reality.services.commitment_actions import _review_commitment_revision

    _, _, promise = _purchase(session, business, "PO-310-4")
    review = _review_commitment_revision(
        session, business.tenant.id, {"commitment_id": promise.id, "unit_price": "10.5"}
    )
    assert review["state"]["price"]["ordered_unit_price"] == "10"
    assert review["effect"]["confirmed_unit_price"] == "10.5"


# --- Supplier item terms (FR-005) ---------------------------------------------------


def test_terms_name_a_quantity_below_the_minimum_or_off_the_multiple(session, business):
    tenant = business.tenant.id
    set_supplier_item_terms(
        session, tenant, business.supplier.id, business.item.id, "50", "12"
    )

    below = order_terms_check(
        session, tenant, business.supplier.id, business.item.id, Decimal(30)
    )
    assert (
        below["below_minimum"],
        below["off_multiple"],
        below["suggested_quantity"],
    ) == (
        True,
        True,
        "60",
    )
    # Positive control: 60 meets both.
    fine = order_terms_check(
        session, tenant, business.supplier.id, business.item.id, Decimal(60)
    )
    assert (fine["below_minimum"], fine["off_multiple"]) == (False, False)
    # Another supplier has no terms.
    other = core.create_party(session, tenant, "Other Supplier", "supplier")
    assert (
        order_terms_check(session, tenant, other.id, business.item.id, Decimal(1))
        is None
    )


def test_the_order_review_names_the_terms(session, business):
    from reality.services.order_actions import review_order

    tenant = business.tenant.id
    set_supplier_item_terms(
        session, tenant, business.supplier.id, business.item.id, "50", None
    )
    review = review_order(
        session,
        tenant,
        {
            "direction": "purchase",
            "number": "PO-310-T",
            "company_party_id": business.company.id,
            "counterparty_id": business.supplier.id,
            "location_id": business.location.id,
            "gross_amount": "300",
            "lines": [
                {
                    "item_id": business.item.id,
                    "quantity": "30",
                    "unit_price": "10",
                    "gross_amount": "300",
                }
            ],
        },
    )
    assert review["state"]["supplier_terms"]["0"]["suggested_quantity"] == "50"


def test_terms_are_versions_and_refuse_nonsense(session, business):
    tenant = business.tenant.id
    first = set_supplier_item_terms(
        session, tenant, business.supplier.id, business.item.id, "50"
    )
    second = set_supplier_item_terms(
        session, tenant, business.supplier.id, business.item.id, None, "6"
    )
    assert first.id == second.id
    (row,) = supplier_item_terms(session, tenant, party_id=business.supplier.id)
    assert (row["minimum_quantity"], row["order_multiple"]) == (None, "6")
    remove_supplier_item_terms(session, tenant, business.supplier.id, business.item.id)
    assert supplier_item_terms(session, tenant) == []
    versions = session.scalars(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.source_system == "internal_supplier_item_terms",
        )
    ).all()
    assert len(versions) == 3
    for code, call in (
        (
            "supplier_item_terms_party_not_supplier",
            lambda: set_supplier_item_terms(
                session, tenant, business.customer.id, business.item.id, "1"
            ),
        ),
        (
            "supplier_item_terms_empty",
            lambda: set_supplier_item_terms(
                session, tenant, business.supplier.id, business.item.id
            ),
        ),
        (
            "supplier_item_terms_invalid",
            lambda: set_supplier_item_terms(
                session, tenant, business.supplier.id, business.item.id, "0"
            ),
        ),
        (
            "supplier_item_terms_not_found",
            lambda: remove_supplier_item_terms(
                session, tenant, business.supplier.id, business.item.id
            ),
        ),
    ):
        _refused(code, call)


def test_another_company_cannot_state_or_read_terms(session, business):
    tenant = business.tenant.id
    set_supplier_item_terms(
        session, tenant, business.supplier.id, business.item.id, "5"
    )
    other = core.create_tenant(session, "Other GmbH")
    assert supplier_item_terms(session, other.id) == []
    with pytest.raises((core.InvalidOperation, core.NotFound)):
        set_supplier_item_terms(
            session, other.id, business.supplier.id, business.item.id, "5"
        )


# --- Cancellation charge (FR-006) ---------------------------------------------------


def _charge(session, business, line, amount="40.00", number="CXL-310"):
    return record_free_supplier_invoice(
        session,
        business.tenant.id,
        supplier_id=business.supplier.id,
        number=number,
        currency="EUR",
        gross_amount=amount,
        lines=[
            {
                "description": "Cancellation charge",
                "quantity": "1",
                "unit": "pcs",
                "unit_price": amount,
                "gross_amount": amount,
                "line_type": "charge",
                "billed_document_line_id": line.id,
            }
        ],
    )


def test_a_cancellation_charge_raises_no_purchase_finding(session, business):
    tenant = business.tenant.id
    document, line, promise = _purchase(session, business, "PO-310-C", "20")
    core.cancel_commitment(
        session, tenant, promise.id, reason="Supplier had produced; agreed charge"
    )

    _charge(session, business, line)

    assert line.id not in _findings(session, business, "billed_not_received")
    match = purchase_match(session, tenant, document.id)
    (row,) = match["lines"]
    assert row["cancelled"] is True and row["matched"] is True
    assert [charge["amount"] for charge in row["charges"]] == ["40"]
    # Positive control: goods billed on the cancelled line are still reported.
    record_free_supplier_invoice(
        session,
        tenant,
        supplier_id=business.supplier.id,
        number="INV-310-C",
        currency="EUR",
        gross_amount="50",
        lines=[
            {
                "item_id": business.item.id,
                "quantity": "5",
                "unit_price": "10",
                "gross_amount": "50",
                "billed_document_line_id": line.id,
            }
        ],
    )
    assert line.id in _findings(session, business, "billed_not_received")
    assert (
        "billed_over"
        in purchase_match(session, tenant, document.id)["lines"][0]["differences"]
    )


# --- Three-way match (FR-002) --------------------------------------------------------


def test_a_line_received_short_or_billed_at_another_price_is_not_matched(
    session, business
):
    tenant = business.tenant.id
    document, line, promise = _purchase(session, business, "PO-310-M")
    _receive(session, business, promise, "95")
    assert purchase_match(session, tenant, document.id)["lines"][0]["differences"] == [
        "received_short",
        "billed_short",
    ]
    _invoice(session, business, line, "95", "950", "INV-310-M")
    row = purchase_match(session, tenant, document.id)["lines"][0]
    assert row["differences"] == ["received_short"]
    # Revising the promise to what arrived matches the line.
    core.revise_commitment(session, tenant, promise.id, quantity="95")
    assert purchase_match(session, tenant, document.id)["matched"] is True


def test_returns_and_credits_count_on_both_sides(session, business):
    tenant = business.tenant.id
    document, line, promise = _purchase(session, business, "PO-310-R", "10")
    _receive(session, business, promise, "10")
    invoice = _invoice(session, business, line, "10", "100", "INV-310-R")
    core.record_movement(
        session,
        tenant,
        "supplier_return",
        business.item.id,
        "2",
        from_location_id=business.location.id,
        commitment_id=promise.id,
        reason="Damaged",
    )
    row = purchase_match(session, tenant, document.id)["lines"][0]
    assert row["received"] == "8" and "billed_over" in row["differences"]
    assert invoice


def test_the_match_is_read_for_purchase_orders_only(session, business):
    tenant = business.tenant.id
    _, _, _, _ = core.create_manual_order(
        session,
        tenant,
        "sales",
        "SO-310-M",
        business.company.id,
        business.customer.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "10",
                "gross_amount": "10",
            }
        ],
        "10",
    )
    sales = session.scalar(
        select(core.Document).where(
            core.Document.tenant_id == tenant, core.Document.number == "SO-310-M"
        )
    )
    _refused(
        "purchase_match_order_required",
        lambda: purchase_match(session, tenant, sales.id),
    )
    assert json.dumps(
        purchase_match(session, tenant, _purchase(session, business, "PO-310-Z")[0].id)
    )


def test_the_migration_guards_its_downgrade(postgres_database, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_database)
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        # Positive control: nothing stated, so the downgrade and upgrade pass.
        command.downgrade(config, "0116_company_currency")
        command.upgrade(config, "head")
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Migration 310")
            supplier = core.create_party(session, tenant.id, "Supplier", "supplier")
            item = core.create_item(session, tenant.id, "M310", "Item 310")
            set_supplier_item_terms(session, tenant.id, supplier.id, item.id, "5")
        with pytest.raises(Exception, match="supplier item terms"):
            command.downgrade(config, "0116_company_currency")
    finally:
        engine.dispose()
        command.upgrade(config, "head")


def test_a_charge_on_a_received_line_leaves_its_goods_billable(session, business):
    tenant = business.tenant.id
    document, line, promise = _purchase(session, business, "PO-310-H", "10")
    _receive(session, business, promise, "10")
    _charge(session, business, line, amount="15.00", number="EXP-310")

    # The goods are still billable in full, and the line matches once billed.
    _invoice(session, business, line, "10", "100", "INV-310-H")
    row = purchase_match(session, tenant, document.id)["lines"][0]
    assert row["matched"] is True and [c["amount"] for c in row["charges"]] == ["15"]


def test_a_partly_received_line_cancelled_for_the_rest_matches_what_arrived(
    session, business
):
    tenant = business.tenant.id
    document, line, promise = _purchase(session, business, "PO-310-P", "100")
    _receive(session, business, promise, "60")
    core.cancel_commitment(session, tenant, promise.id, reason="Rest not needed")
    _invoice(session, business, line, "60", "600", "INV-310-P")

    row = purchase_match(session, tenant, document.id)["lines"][0]
    assert (row["cancelled"], row["matched"], row["differences"]) == (True, True, [])


def test_terms_compare_a_line_in_the_stock_unit_through_the_items_factor(
    session, business
):
    tenant = business.tenant.id
    item = core.create_item(session, tenant, "BOX-310", "Boxed 310")
    item.purchase_unit, item.conversion_factor = "box", Decimal(12)
    session.flush()
    set_supplier_item_terms(session, tenant, business.supplier.id, item.id, "5")

    fine = order_terms_check(
        session, tenant, business.supplier.id, item.id, Decimal(60), "pcs"
    )
    assert (fine["below_minimum"], fine["suggested_quantity"]) == (False, "60")
    short = order_terms_check(
        session, tenant, business.supplier.id, item.id, Decimal(24), "pcs"
    )
    assert (short["below_minimum"], short["suggested_quantity"]) == (True, "60")
    other = order_terms_check(
        session, tenant, business.supplier.id, item.id, Decimal(1), "pallet"
    )
    assert other["units_not_comparable"] is True


def test_a_price_is_confirmed_after_everything_arrived(session, business):
    tenant = business.tenant.id
    _, line, promise = _purchase(session, business, "PO-310-F", "10")
    _receive(session, business, promise, "10")
    session.refresh(promise)
    assert promise.status == "fulfilled"

    core.revise_commitment(session, tenant, promise.id, unit_price="9.5")

    assert core._agreed_line_prices(session, tenant, [line])[line.id] == Decimal("9.5")
    # Positive control: a quantity is still not revised on a fulfilled promise.
    _refused(
        "commitment_revise_not_open",
        lambda: core.revise_commitment(session, tenant, promise.id, quantity="9"),
    )
    _refused(
        "commitment_price_invalid",
        lambda: core.revise_commitment(session, tenant, promise.id, unit_price="1e15"),
    )
