"""Spec 345 FR-002/FR-005: purchase orders and supplier invoices by the supplier's number."""

import json

import pytest
from intake_review_support import (
    reviewed_correct_manual_document_lines,
    reviewed_manual_document_with_lines,
    reviewed_manual_order,
)

from reality.services import core
from reality.services.operational_previews import operational_preview
from reality.services.purchase_match import purchase_match
from reality.services.supplier_item_numbers import set_supplier_item_number


def _map(session, business, number="LF900-12", name="Laufrad 28 Lindner", item=None):
    return set_supplier_item_number(
        session,
        business.tenant.id,
        business.supplier.id,
        (item or business.item).id,
        number,
        name,
    )


def _purchase_order(session, business, number, lines, supplier=None):
    return reviewed_manual_order(
        session,
        business.tenant.id,
        "purchase",
        number,
        business.company.id,
        (supplier or business.supplier).id,
        business.location.id,
        [
            {
                "quantity": quantity,
                "unit_price": "10",
                "gross_amount": str(int(quantity) * 10),
                **line,
            }
            for line, quantity in lines
        ],
        str(sum(int(quantity) * 10 for _, quantity in lines)),
    )


def _refused(code, call):
    with pytest.raises((core.InvalidOperation, core.NotFound)) as refused:
        call()
    assert refused.value.code == code, refused.value.code


def _line_labels(sections):
    return [
        row["label"]
        for section in sections
        if section["title"] == "Lines"
        for row in section["rows"]
    ]


def test_a_purchase_line_resolves_by_the_suppliers_number(session, business):
    _map(session, business)

    _, _document, lines, commitments = _purchase_order(
        session, business, "PO-345-1", [({"supplier_item_number": "lf 900-12"}, "4")]
    )

    (line,) = lines
    assert line.item_id == business.item.id
    assert json.loads(line.payload)["supplier_item_number"] == "lf 900-12"
    assert commitments[0].item_id == business.item.id
    assert commitments[0].type == "supplier_delivery"


def test_two_suppliers_name_the_same_item_by_their_own_numbers(session, business):
    tenant = business.tenant.id
    other = reviewed_create_party(session, tenant, "Velo Import AG", "supplier")
    _map(session, business)
    set_supplier_item_number(session, tenant, other.id, business.item.id, "VI-77", "")

    _, _, (first,), _ = _purchase_order(
        session, business, "PO-345-2", [({"supplier_item_number": "LF900-12"}, "1")]
    )
    _, _, (second,), _ = _purchase_order(
        session,
        business,
        "PO-345-3",
        [({"supplier_item_number": "VI-77"}, "1")],
        supplier=other,
    )

    assert first.item_id == second.item_id == business.item.id
    # One supplier's number means nothing at another supplier.
    _refused(
        "supplier_item_number_unknown",
        lambda: _purchase_order(
            session,
            business,
            "PO-345-4",
            [({"supplier_item_number": "VI-77"}, "1")],
        ),
    )


def test_an_unknown_or_conflicting_number_is_refused_in_entry(session, business):
    lamp = reviewed_create_item(session, business.tenant.id, "LAMP-345", "Lamp 345")
    _map(session, business)

    _refused(
        "supplier_item_number_unknown",
        lambda: _purchase_order(
            session, business, "PO-345-5", [({"supplier_item_number": "X-9"}, "1")]
        ),
    )
    _refused(
        "supplier_item_number_conflicts_with_item",
        lambda: _purchase_order(
            session,
            business,
            "PO-345-6",
            [({"supplier_item_number": "LF900-12", "item_id": lamp.id}, "1")],
        ),
    )
    # Positive control: our item and the matching number agree.
    _purchase_order(
        session,
        business,
        "PO-345-7",
        [({"supplier_item_number": "LF900-12", "item_id": business.item.id}, "1")],
    )


def test_a_sales_line_does_not_read_a_supplier_number(session, business):
    """A supplier's number never resolves a customer's order."""
    _map(session, business)

    # The line names no item of ours, so it is refused as itemless.
    with pytest.raises((core.InvalidOperation, core.NotFound)):
        reviewed_manual_order(
            session,
            business.tenant.id,
            "sales",
            "SO-345-1",
            business.company.id,
            business.customer.id,
            business.location.id,
            [
                {
                    "supplier_item_number": "LF900-12",
                    "quantity": "1",
                    "unit_price": "10",
                    "gross_amount": "10",
                }
            ],
            "10",
        )


def test_the_stated_number_shows_on_order_invoice_and_match(session, business):
    tenant = business.tenant.id
    _map(session, business)
    _, order, (line,), _ = _purchase_order(
        session, business, "PO-345-8", [({"supplier_item_number": "LF900-12"}, "2")]
    )

    labels = _line_labels(operational_preview(session, tenant, "document", order.id))
    assert any("LF900-12 Laufrad 28 Lindner" in label for label in labels)
    (row,) = purchase_match(session, tenant, order.id)["lines"]
    assert row["supplier_item_number"] == "LF900-12"
    # The supplier's invoice states its own number on its line, too.
    invoice = reviewed_manual_document_with_lines(
        session,
        tenant,
        "supplier_invoice",
        "LF-RE-345-1",
        business.supplier.id,
        [
            {
                "supplier_item_number": "lf900-12",
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
                "billed_document_line_id": line.id,
            }
        ],
        "20",
    )[0]
    invoice_labels = _line_labels(
        operational_preview(session, tenant, "document", invoice.id)
    )
    assert any("lf900-12 Laufrad 28 Lindner" in label for label in invoice_labels)


def test_a_changed_mapping_leaves_past_lines_as_stated(session, business):
    tenant = business.tenant.id
    lamp = reviewed_create_item(session, tenant, "LAMP-345C", "Lamp changed")
    _map(session, business)
    _, _, (line,), _ = _purchase_order(
        session, business, "PO-345-9", [({"supplier_item_number": "LF900-12"}, "1")]
    )

    _map(session, business, item=lamp, name="Lampe neu")

    session.refresh(line)
    assert (line.item_id, json.loads(line.payload)["supplier_item_number"]) == (
        business.item.id,
        "LF900-12",
    )


def test_a_correction_that_does_not_state_the_number_keeps_it(session, business):
    from reality.services.core import (
        manual_document_line_snapshot,
    )

    tenant = business.tenant.id
    _map(session, business)
    document, (line,) = reviewed_manual_document_with_lines(
        session,
        tenant,
        "supplier_invoice",
        "LF-RE-345-2",
        business.supplier.id,
        [
            {
                "supplier_item_number": "LF900-12",
                "quantity": "1",
                "unit_price": "10",
                "gross_amount": "10",
            }
        ],
        "10",
    )[:2]
    snapshot = manual_document_line_snapshot(session, tenant, document.id)
    # As the web form sends it: the line's columns, the number unstated.
    unchanged = {
        key: value
        for key, value in snapshot["lines"][0].items()
        if key != "supplier_item_number"
    }

    result = reviewed_correct_manual_document_lines(
        session,
        tenant,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[{**unchanged, "supplier_item_number": None}],
    )
    assert result["changed"] is False
    # Positive control: a real correction still keeps the stated number.
    reviewed_correct_manual_document_lines(
        session,
        tenant,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[{**unchanged, "description": "Corrected"}],
    )
    session.refresh(line)
    assert json.loads(line.payload)["supplier_item_number"] == "LF900-12"


from intake_review_support import reviewed_create_item, reviewed_create_party
