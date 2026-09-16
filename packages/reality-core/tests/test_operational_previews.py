from decimal import Decimal

import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy import event
from unified_fixtures import delivery_fixture

from reality.services.core import (
    NotFound,
    create_manual_document_with_lines,
    create_tenant,
    post_customer_payment,
    post_sales_invoice,
    record_movement,
    reserve,
)
from reality.services.operational_previews import operational_preview


def fields(sections):
    return {r["label"]: r for s in sections for r in s["rows"]}


def document(session, business, kind="sales_order", count=1):
    return create_manual_document_with_lines(
        session,
        business.tenant.id,
        kind,
        "ORDER-209",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "sku": "ORIGINAL-SKU",
                "description": "Original lamp description",
                "quantity": "2",
                "unit_price": "12.3456",
                "gross_amount": "30.17",
            }
            for _ in range(count)
        ],
        "77.77",
        document_date="2026-09-16",
    )


@pytest.mark.parametrize("kind", ["sales_order", "purchase_order", "sales_invoice"])
def test_document_keeps_description_sku_and_received_totals(session, business, kind):
    doc, lines = document(session, business, kind)
    result = operational_preview(session, business.tenant.id, "document", doc.id)
    rows = fields(result)
    assert (
        rows["Supplier" if kind == "purchase_order" else "Customer"]["value"]
        == business.customer.name
    )
    assert rows["Gross amount"]["display_parts"][0]["value"] == str(doc.gross_amount)
    position = next(s for s in result if s["title"] == "Lines")["rows"][0]
    assert lines[0].sku in position["label"]
    assert "Original lamp description" in position["label"]
    assert position["display_parts"][2]["value"] == str(lines[0].gross_amount)
    assert position["link"] == {"kind": "document_line", "id": lines[0].id}
    assert "Correction" not in [s["title"] for s in result]


def test_missing_description_uses_labeled_current_name_and_bounds_lines(
    session, business
):
    doc, lines = document(session, business, count=21)
    # Fixture a legacy record without a source description, without changing the source.
    for line in lines:
        line.description = ""
    session.flush()
    result = operational_preview(session, business.tenant.id, "document", doc.id)
    positions = next(s for s in result if s["title"] == "Lines")
    assert len(positions["rows"]) == 20
    assert positions["has_more"]
    row = positions["rows"][0]
    assert business.item.name in row["label"]
    assert row["hint"] == "Current item name"


def test_partial_delivery_and_warehouse_reads_agree_and_do_not_write(session, business):
    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    reservation = reserve(session, tid, cid, "12").reservation
    movement = record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=cid,
    )
    writes = []

    def observe(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE"}:
            writes.append(statement)

    connection = session.connection()
    event.listen(connection, "before_cursor_execute", observe)
    try:
        delivery = fields(operational_preview(session, tid, "commitment", cid))
        assert Decimal(delivery["Open"]["display_parts"][0]["value"]) == 7
        assert Decimal(delivery["Fulfilled"]["display_parts"][0]["value"]) == 5
        stock = fields(operational_preview(session, tid, "item", business.item.id))
        assert Decimal(stock["Physical"]["display_parts"][0]["value"]) == 15
        assert Decimal(stock["Available"]["display_parts"][0]["value"]) == 8
        reserved = fields(
            operational_preview(session, tid, "reservation", reservation.id)
        )
        assert reserved["Location"]["value"] == business.location.name
        moved = fields(operational_preview(session, tid, "movement", movement.id))
        assert moved["From"]["value"] == business.location.name
        assert moved["Customer"]["value"] == business.customer.name
        assert writes == []
    finally:
        event.remove(connection, "before_cursor_execute", observe)
    foreign = create_tenant(session, "Other preview company")
    for kind, rid in [
        ("commitment", cid),
        ("item", business.item.id),
        ("movement", movement.id),
        ("reservation", reservation.id),
    ]:
        with pytest.raises(NotFound):
            operational_preview(session, foreign.id, kind, rid)


def test_invoice_partial_payment_and_journal_share_financial_authority(
    session, business
):
    doc, _ = document(session, business, "sales_invoice")
    tid = business.tenant.id
    entries = post_sales_invoice(session, tid, doc.id)
    payment = post_customer_payment(session, tid, doc.id, "20")
    cash = next(e for e in payment if e.account == "cash")
    invoice = fields(operational_preview(session, tid, "document", doc.id))
    assert Decimal(invoice["Open amount"]["display_parts"][0]["value"]) == Decimal(
        "57.77"
    )
    assert invoice["Due"]["display_parts"] == [{"type": "date", "value": "2026-09-16"}]
    paid = fields(operational_preview(session, tid, "payment", cash.id))
    assert Decimal(paid["Allocated"]["display_parts"][0]["value"]) == 20
    assert Decimal(paid["Unallocated"]["display_parts"][0]["value"]) == 0
    assert any(
        r.get("link") == {"kind": "document", "id": doc.id}
        for s in operational_preview(session, tid, "payment", cash.id)
        for r in s["rows"]
    )
    journal = fields(operational_preview(session, tid, "ledger_entry", entries[0].id))
    assert journal["Document"]["value"] == doc.number
    foreign = create_tenant(session, "Other finance company")
    for kind, rid in [
        ("document", doc.id),
        ("payment", cash.id),
        ("ledger_entry", entries[0].id),
    ]:
        with pytest.raises(NotFound):
            operational_preview(session, foreign.id, kind, rid)


def test_shipment_has_named_party_tracking_and_no_invented_contents(session, business):
    from reality.services.shipments import record_shipment_notice

    shipment, package, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
        carrier="DHL",
        tracking_number="TRACK-209",
    )
    for kind, rid in [("shipment", shipment.id), ("shipment_package", package.id)]:
        result = operational_preview(session, business.tenant.id, kind, rid)
        rows = fields(result)
        assert rows["Supplier"]["value"] == business.supplier.name
        assert "TRACK-209" in str(result)
        assert (
            next(s for s in result if s["title"] == "Effective physical contents")[
                "rows"
            ]
            == []
        )
        jsonable_encoder(result)


def test_inspector_opt_in_keeps_full_sections_and_is_scoped(session, business):
    from reality.web.api import get_inspector

    doc, _ = document(session, business)
    full = get_inspector("document", doc.id, business.tenant.id, session)
    assert "preview_sections" not in full
    compact = get_inspector(
        "document", doc.id, business.tenant.id, session, preview=True
    )
    assert compact["sections"] == full["sections"]
    assert compact["preview_sections"]
    assert any(s["title"] == "Correction" for s in full["sections"])


def test_reversed_payment_has_no_available_money_and_invoice_reopens(session, business):
    from reality.services.core import reverse_ledger_posting_group

    doc, _ = document(session, business, "sales_invoice")
    tid = business.tenant.id
    post_sales_invoice(session, tid, doc.id)
    payment = post_customer_payment(session, tid, doc.id, "20")
    cash = next(e for e in payment if e.account == "cash")
    reverse_ledger_posting_group(
        session, tid, cash.posting_group_id, reason="Wrong payment"
    )
    rows = fields(operational_preview(session, tid, "payment", cash.id))
    assert rows["Status"]["value"] == "Reversed"
    assert Decimal(rows["Unallocated"]["display_parts"][0]["value"]) == 0
    invoice = fields(operational_preview(session, tid, "document", doc.id))
    assert Decimal(invoice["Open amount"]["display_parts"][0]["value"]) == Decimal(
        "77.77"
    )


def test_revised_held_order_keeps_requested_and_effective_due_dates(session, business):
    from reality.services.core import (
        create_commitment,
        hold_commitment,
        revise_commitment,
    )

    doc, lines = document(session, business)
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "2",
        "2026-09-20T12:00:00Z",
        document_id=doc.id,
        document_line_id=lines[0].id,
    )
    revise_commitment(
        session,
        business.tenant.id,
        commitment.id,
        quantity="3",
        due_at="2026-09-22T12:00:00Z",
    )
    hold_commitment(
        session, business.tenant.id, commitment.id, "manual_review", "Check destination"
    )
    result = operational_preview(session, business.tenant.id, "document", doc.id)
    operational = next(s for s in result if s["title"] == "Operational Reality")
    assert operational["rows"][0]["display_parts"][0]["value"] == "3.0000"
    assert fields(result)["Due"]["value"].startswith("2026-09-22")
    assert fields(result)["Holds"]["value"] == "manual_review"


def test_shipment_physical_contents_and_tracking_dates_remain_separate(
    session, business
):
    from datetime import UTC, datetime

    from reality.services.shipments import (
        record_packaged_execution,
        record_shipment_event,
    )

    result = record_packaged_execution(
        session,
        business.tenant.id,
        direction="inbound",
        purpose="supplier_delivery",
        counterparty_id=business.supplier.id,
        movements=[
            {
                "item_id": business.item.id,
                "quantity": "2",
                "to_location_id": business.location.id,
            }
        ],
    )
    shipment_id = result["shipment_id"]
    record_shipment_event(
        session,
        business.tenant.id,
        shipment_id,
        event_type="delivered",
        reporter_type="carrier",
        occurred_at=datetime(2026, 9, 16, 12, tzinfo=UTC),
    )
    preview = operational_preview(session, business.tenant.id, "shipment", shipment_id)
    contents = next(s for s in preview if s["title"] == "Effective physical contents")[
        "rows"
    ]
    assert business.item.name in contents[0]["label"]
    events = next(s for s in preview if s["title"] == "Current tracking observations")[
        "rows"
    ]
    delivered = next(r for r in events if r["label"] == "Delivered")
    assert delivered["display_parts"][0]["type"] == "datetime"
    foreign = create_tenant(session, "Other logistics company")
    with pytest.raises(NotFound):
        operational_preview(session, foreign.id, "shipment", shipment_id)


def test_preview_http_contract_and_foreign_tenant(session, business):
    from fastapi.testclient import TestClient

    from reality.web.api import database_session
    from reality.web.app import app

    doc, _ = document(session, business)
    foreign = create_tenant(session, "Other HTTP company")

    def database():
        yield session

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            path = f"/api/tenants/{business.tenant.id}/inspector/document/{doc.id}"
            assert "preview_sections" not in client.get(path).json()
            response = client.get(path + "?preview=true")
            assert response.status_code == 200
            assert response.json()["preview_sections"][1]["title"] == "Lines"
            response = client.get(
                f"/api/tenants/{foreign.id}/inspector/document/{doc.id}?preview=true"
            )
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
