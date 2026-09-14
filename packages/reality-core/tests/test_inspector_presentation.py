from datetime import UTC, date, datetime
from decimal import Decimal

from reality.services.inspector_presentation import display_parts, display_text, money


def test_composite_preserves_received_values_and_marks_only_numeric_parts():
    value = display_text(
        Decimal("10.0000"), " pcs · ", money(Decimal("120.0000"), "EUR")
    )
    assert str(value) == "10.0000 pcs · EUR 120.0000"
    assert display_parts(value) == [
        {"type": "number", "value": "10.0000"},
        {"type": "text", "value": " pcs · "},
        {"type": "money", "value": "120.0000", "currency": "EUR"},
    ]


def test_identifiers_and_unqualified_decimals_do_not_gain_currency():
    assert display_parts("001234.5000") is None
    assert display_parts("INV-120.0000") is None
    assert display_parts({"original": "120.0000"}) is None
    assert display_parts(Decimal("0.0000")) == [{"type": "number", "value": "0.0000"}]
    assert display_parts(True) is None


def test_dates_and_instants_keep_exact_values_with_typed_presentation():
    day = date(2026, 9, 9)
    instant = datetime(2026, 9, 9, 19, 9, 54, tzinfo=UTC)
    assert display_parts(day) == [{"type": "date", "value": "2026-09-09"}]
    assert display_parts(instant) == [
        {"type": "datetime", "value": "2026-09-09T19:09:54+00:00"}
    ]
    combined = display_text(Decimal(2), " · ", instant)
    assert str(combined) == "2 · 2026-09-09 19:09:54+00:00"
    assert display_parts(combined)[2]["type"] == "datetime"


def test_unit_price_preserves_four_decimal_precision():
    value = display_text(
        "agreed ", money(Decimal("12.3456"), "EUR", precision=4), "/pcs"
    )
    assert display_parts(value)[1]["precision"] == 4
    assert str(value) == "agreed EUR 12.3456/pcs"


def test_document_and_line_contract_keep_raw_values_and_currency(session, business):
    import pytest
    from fastapi.encoders import jsonable_encoder

    from reality.services.core import (
        NotFound,
        create_manual_document_with_lines,
        create_tenant,
    )
    from reality.services.delivery_reads import delivery_evidence
    from reality.web.api import complete_inspector, document_inspector, party_inspector

    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "001234.5000",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "10",
                "unit_price": "12.3456",
                "gross_amount": "123.4560",
            }
        ],
        "123.4560",
    )
    payload = jsonable_encoder(
        complete_inspector(document_inspector(session, business.tenant.id, document.id))
    )
    assert "001234.5000" in payload["title"]
    sections = {section["title"]: section["rows"] for section in payload["sections"]}
    line = sections["Lines"][0]
    assert line["display_parts"][0]["value"] == str(lines[0].quantity)
    assert line["display_parts"][2]["currency"] == document.currency
    price = sections["Historical pricing"][0]["display_parts"][1]
    assert price["value"] == str(lines[0].unit_price)
    assert price["precision"] == 4
    evidence = delivery_evidence(
        session, business.tenant.id, "document_line", lines[0].id
    )
    fields = {row["label"]: row for row in evidence["sections"][0]["rows"]}
    assert fields["Gross Amount"]["value"] == str(lines[0].gross_amount)
    assert fields["Gross Amount"]["display_parts"][0]["currency"] == document.currency
    assert "display_parts" not in fields["Document"]
    party = party_inspector(session, business.tenant.id, business.customer.id)
    credit = next(
        row
        for section in party["sections"]
        for row in section["rows"]
        if row["label"] == "Credit limit"
    )
    assert credit["value"] == str(business.customer.credit_limit)
    foreign = create_tenant(session, "Foreign inspector")
    with pytest.raises(NotFound):
        delivery_evidence(session, foreign.id, "document_line", lines[0].id)


def test_heading_and_fallback_meaning_keep_numeric_parts():
    from fastapi.encoders import jsonable_encoder

    from reality.web.api import complete_inspector

    payload = jsonable_encoder(
        complete_inspector(
            {"title": money(Decimal("1234.5000"), "EUR"), "subtitle": "Party 00123"}
        )
    )
    assert payload["title"] == "EUR 1234.5000"
    assert payload["title_parts"][0]["type"] == "money"
    assert payload["meaning_parts"][0]["type"] == "money"
    assert payload["meaning_parts"][2]["value"] == "Party 00123"
