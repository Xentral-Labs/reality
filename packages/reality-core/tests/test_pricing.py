from decimal import Decimal

import pytest

from reality.services.core import (
    InvalidOperation,
    NotFound,
    add_party_group_member,
    assign_group_price_list,
    assign_party_price_list,
    correct_manual_document_lines,
    create_manual_document_with_lines,
    create_party_group,
    create_price_list,
    create_price_list_entry,
    create_tenant,
    historical_pricing_explanation,
    manual_document_line_snapshot,
    resolve_price,
    update_price_list,
)


def add_tiers(session, business, price_list, low, high):
    create_price_list_entry(
        session, business.tenant.id, price_list.id, business.item.id, 1, low, "pcs"
    )
    return create_price_list_entry(
        session, business.tenant.id, price_list.id, business.item.id, 10, high, "pcs"
    )


def test_pricing_resolves_direct_group_default_and_quantity_tiers(session, business):
    default = create_price_list(
        session,
        business.tenant.id,
        "SALES",
        "Standard Sales",
        "sales",
        "EUR",
        is_default=True,
    )
    default_tier = add_tiers(session, business, default, "12", "10")
    result = resolve_price(
        session,
        business.tenant.id,
        business.customer.id,
        business.item.id,
        12,
        "sales",
        "EUR",
        "pcs",
    )
    assert result is not None
    assert result.unit_price == Decimal("10.0000")
    assert result.price_list_entry_id == default_tier.id
    assert result.source == "default"

    group_list = create_price_list(
        session, business.tenant.id, "GOLD", "Gold", "sales", "EUR"
    )
    add_tiers(session, business, group_list, "9", "8")
    group = create_party_group(
        session, business.tenant.id, "DEALER_GOLD", "Gold dealers"
    )
    add_party_group_member(
        session, business.tenant.id, group.id, business.customer.id
    )
    assign_group_price_list(session, business.tenant.id, group.id, group_list.id)
    assert resolve_price(
        session, business.tenant.id, business.customer.id, business.item.id,
        12, "sales", "EUR", "pcs"
    ).unit_price == Decimal("8.0000")

    direct = create_price_list(
        session, business.tenant.id, "CUSTOMER", "Customer", "sales", "EUR"
    )
    add_tiers(session, business, direct, "7", "6")
    assign_party_price_list(
        session, business.tenant.id, business.customer.id, direct.id
    )
    selected = resolve_price(
        session, business.tenant.id, business.customer.id, business.item.id,
        12, "sales", "EUR", "pcs"
    )
    assert selected.unit_price == Decimal("6.0000")
    assert selected.source == "party"


def test_sales_and_purchase_lists_do_not_mix(session, business):
    purchase = create_price_list(
        session,
        business.tenant.id,
        "PURCHASE",
        "Purchase",
        "purchase",
        "EUR",
        is_default=True,
    )
    create_price_list_entry(
        session, business.tenant.id, purchase.id, business.item.id, 1, 4, "pcs"
    )
    assert resolve_price(
        session, business.tenant.id, business.supplier.id, business.item.id,
        1, "sales", "EUR", "pcs"
    ) is None
    assert resolve_price(
        session, business.tenant.id, business.supplier.id, business.item.id,
        1, "purchase", "EUR", "pcs"
    ).unit_price == Decimal("4.0000")


def test_document_line_retains_agreed_entry_when_current_price_changes(session, business):
    original = create_price_list(
        session, business.tenant.id, "OLD", "Old", "sales", "EUR", is_default=True
    )
    original_entry = create_price_list_entry(
        session, business.tenant.id, original.id, business.item.id, 1, 10, "pcs"
    )
    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-HISTORICAL-1",
        business.customer.id,
        [{
            "item_id": business.item.id,
            "quantity": "2",
            "unit": "pcs",
            "unit_price": "10",
            "gross_amount": "20",
            "price_list_entry_id": original_entry.id,
        }],
        "20",
        ordered_at="2026-01-01T10:00:00Z",
    )

    update_price_list(
        session, business.tenant.id, original.id, "OLD", "Old", "sales", "EUR"
    )
    current = create_price_list(
        session, business.tenant.id, "NEW", "New", "sales", "EUR", is_default=True
    )
    current_entry = create_price_list_entry(
        session, business.tenant.id, current.id, business.item.id, 1, 12, "pcs"
    )

    explanation = historical_pricing_explanation(
        session, business.tenant.id, lines[0].id
    )
    assert explanation["document_id"] == document.id
    assert explanation["agreed"]["unit_price"] == Decimal("10.0000")
    assert explanation["agreed"]["price_list_entry_id"] == original_entry.id
    assert explanation["current_resolution"]["price_list_entry_id"] == current_entry.id
    assert explanation["current_resolution"]["unit_price"] == Decimal("12.0000")
    assert explanation["changed_since_agreement"] is True
    session.refresh(lines[0])
    assert lines[0].unit_price == Decimal("10.0000")


def test_selected_entry_must_reproduce_document_context_atomically(session, business):
    price_list = create_price_list(
        session, business.tenant.id, "VALID", "Valid", "sales", "EUR", is_default=True
    )
    entry = create_price_list_entry(
        session, business.tenant.id, price_list.id, business.item.id, 1, 10, "pcs"
    )
    with pytest.raises(InvalidOperation, match="does not reproduce"):
        create_manual_document_with_lines(
            session,
            business.tenant.id,
            "sales_order",
            "SO-BAD-PRICE",
            business.customer.id,
            [{
                "item_id": business.item.id,
                "quantity": "1",
                "unit_price": "11",
                "gross_amount": "11",
                "price_list_entry_id": entry.id,
            }],
            "11",
        )


def test_manual_agreement_remains_valid_without_pricing_entry(session, business):
    _, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-MANUAL-PRICE",
        business.customer.id,
        [{
            "item_id": business.item.id,
            "quantity": "1",
            "unit_price": "9",
            "gross_amount": "9",
        }],
        "9",
    )
    explanation = historical_pricing_explanation(
        session, business.tenant.id, lines[0].id
    )
    assert explanation["agreed"]["price_list_entry_id"] is None
    foreign = create_tenant(session, "Foreign historical pricing")
    with pytest.raises(NotFound):
        historical_pricing_explanation(session, foreign.id, lines[0].id)


def test_manual_price_without_entry_keeps_legacy_free_form_document_date(session, business):
    document, _ = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "note",
        "MANUAL-DATE",
        business.customer.id,
        [{
            "item_id": business.item.id,
            "quantity": "1",
            "unit_price": "9",
            "gross_amount": "9",
        }],
        "9",
        document_date="legacy-period-label",
    )
    assert document.document_date == "legacy-period-label"


def test_presentation_correction_keeps_historical_entry_after_default_changes(
    session, business
):
    price_list = create_price_list(
        session, business.tenant.id, "HISTORY", "History", "sales", "EUR",
        is_default=True,
    )
    entry = create_price_list_entry(
        session, business.tenant.id, price_list.id, business.item.id, 1, 10, "pcs"
    )
    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-HISTORY-CORRECTION",
        business.customer.id,
        [{
            "item_id": business.item.id,
            "quantity": "1",
            "unit_price": "10",
            "gross_amount": "10",
            "price_list_entry_id": entry.id,
        }],
        "10",
    )
    update_price_list(
        session, business.tenant.id, price_list.id, "HISTORY", "History",
        "sales", "EUR", is_default=False,
    )
    snapshot = manual_document_line_snapshot(session, business.tenant.id, document.id)
    corrected_line = {**snapshot["lines"][0], "description": "Corrected label"}
    result = correct_manual_document_lines(
        session,
        business.tenant.id,
        document.id,
        expected_revision=snapshot["revision"],
        lines=[corrected_line],
    )
    assert result["changed"] is True
    session.refresh(lines[0])
    assert lines[0].price_list_entry_id == entry.id
    assert lines[0].unit_price == Decimal("10.0000")
