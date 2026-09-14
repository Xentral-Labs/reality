from datetime import UTC, datetime
from decimal import Decimal

from test_unified_source_api import client_for
from unified_fixtures import delivery_fixture

from reality.services.core import (
    cancel_commitment,
    correct_movement,
    create_commitment,
    create_document,
    create_manual_document_with_lines,
    create_tenant,
    preview_movement_correction,
    record_movement,
    revise_commitment,
)
from reality.services.delivery_reads import delivery_case, delivery_work


def test_incoming_register_uses_supplier_effective_values_and_corrected_receipts(
    session, business
):
    tid = business.tenant.id
    outgoing = delivery_fixture(session, business).commitment
    incoming = create_commitment(
        session,
        tid,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "10",
        "2026-09-10T12:00:00Z",
    )
    revise_commitment(session, tid, incoming.id, "2026-09-12T12:00:00Z", quantity="14")
    receipt = record_movement(
        session,
        tid,
        "receipt",
        business.item.id,
        "4",
        to_location_id=business.location.id,
        commitment_id=incoming.id,
    )
    result = delivery_work(
        session, tid, commitment_type="supplier_delivery", query="Bike Parts", size=1
    )
    row = result["items"][0]
    assert result["page"]["total"] == 1
    assert row["type"] == "supplier_delivery"
    assert row["party_id"] == business.supplier.id
    assert row["counterparty"] == business.supplier.name
    assert row["unit"] == business.item.unit
    assert row["due_at"] == datetime(2026, 9, 12, 12, tzinfo=UTC)
    assert [Decimal(row[key]) for key in ("promised", "fulfilled", "open")] == [
        14,
        4,
        10,
    ]
    assert delivery_work(session, tid)["items"][0]["id"] == outgoing.id
    # Spec 116 adds shared incoming case context for reviewed receipts.
    assert delivery_case(session, tid, incoming.id)["case"]["party_id"] == business.supplier.id
    preview = preview_movement_correction(
        session, tid, receipt.id, reason="Duplicate receipt"
    )
    correct_movement(
        session,
        tid,
        receipt.id,
        reason="Duplicate receipt",
        expected_revision=preview["revision"],
        preview_fingerprint=preview["request_fingerprint"],
    )
    corrected = delivery_work(session, tid, commitment_type="supplier_delivery")[
        "items"
    ][0]
    assert Decimal(corrected["fulfilled"]) == 0
    assert Decimal(corrected["open"]) == 14
    record_movement(
        session,
        tid,
        "receipt",
        business.item.id,
        "14",
        to_location_id=business.location.id,
        commitment_id=incoming.id,
    )
    assert (
        delivery_work(session, tid, commitment_type="supplier_delivery")["page"][
            "total"
        ]
        == 0
    )
    assert (
        delivery_work(session, tid, commitment_type="supplier_delivery", status="all")[
            "page"
        ]["total"]
        == 1
    )

    cancelled = create_commitment(
        session,
        tid,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "2",
        None,
    )
    cancel_commitment(session, tid, cancelled.id)
    assert (
        delivery_work(session, tid, commitment_type="supplier_delivery")["page"][
            "total"
        ]
        == 0
    )
    history = delivery_work(
        session, tid, commitment_type="supplier_delivery", status="all"
    )
    assert {row["status"] for row in history["items"]} == {"fulfilled", "cancelled"}


def test_order_document_scope_uses_exact_lines_before_paging_and_is_tenant_scoped(
    session, business
):
    tid = business.tenant.id
    document, lines = create_manual_document_with_lines(
        session,
        tid,
        "sales_order",
        "SAME-NUMBER",
        business.customer.id,
        [
            {
                "quantity": "1",
                "unit": "pcs",
                "unit_price": "10",
                "gross_amount": "10",
                "item_id": business.item.id,
            }
            for _ in range(3)
        ],
        "30",
    )
    commitments = [
        create_commitment(
            session,
            tid,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "1",
            None,
            document_id=document.id if index < 2 else None,
            document_line_id=line.id,
        )
        for index, line in enumerate(lines)
    ]
    line_only = commitments[-1]
    assert line_only.document_id is None
    other = create_document(
        session, tid, "sales_order", "SAME-NUMBER", business.customer.id, "99"
    )
    create_commitment(
        session,
        tid,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "9",
        None,
        document_id=other.id,
    )
    assert delivery_work(session, tid, document_id=other.id)["page"]["total"] == 1
    expected = {c.id for c in commitments}
    found = set()
    for page in (1, 2, 3):
        result = delivery_work(
            session, tid, document_id=document.id, status="all", page=page, size=1
        )
        assert result["page"]["total"] == 3
        found.add(result["items"][0]["id"])
    assert found == expected
    foreign = create_tenant(session, "Foreign orders")
    assert (
        delivery_work(session, foreign.id, document_id=document.id)["page"]["total"]
        == 0
    )
    assert delivery_work(session, tid, document_id="missing")["page"]["total"] == 0


def test_orders_api_keeps_direction_validation_defaults_and_exact_evidence_types(
    session, business
):
    tid = business.tenant.id
    delivery_fixture(session, business)
    incoming = create_commitment(
        session,
        tid,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "3",
        None,
    )
    documents = [
        create_document(session, tid, kind, "SAME", business.customer.id, "123.45")
        for kind in ("sales_order", "purchase_order", "sales_invoice")
    ]
    with client_for(session) as client:
        base = f"/api/tenants/{tid}"
        response = client.get(base + "/delivery-work?commitment_type=supplier_delivery")
        assert response.status_code == 200
        assert response.json()["items"][0]["id"] == incoming.id
        assert (
            client.get(base + "/delivery-work?commitment_type=invented").status_code
            == 400
        )
        assert client.get(base + "/delivery-work?status=invented").status_code == 400
        assert client.get(base + "/delivery-work?size=101").status_code == 422
        assert (
            client.get(base + "/delivery-work?document_id=missing").json()["page"][
                "total"
            ]
            == 0
        )
        for document in documents[:2]:
            result = client.get(
                base + f"/evidence-documents?document_type={document.type}&size=1"
            ).json()
            assert result["page"]["total"] == 1
            assert result["items"][0]["id"] == document.id
            assert Decimal(result["items"][0]["gross_amount"]) == Decimal("123.45")
