from decimal import Decimal

import pytest
from unified_fixtures import delivery_fixture

from reality.services.core import (
    NotFound,
    create_tenant,
    record_movement,
    reserve,
    revise_commitment,
)
from reality.services.delivery_reads import delivery_case, delivery_work


def test_partial_and_final_delivery_keep_exact_case(session, business):
    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    reserve(session, tid, cid, "12")
    record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=cid,
    )
    case = delivery_case(session, tid, cid)
    assert Decimal(case["case"]["open"]) == 7
    assert Decimal(case["case"]["fulfilled"]) == 5
    assert {
        key: Decimal(case["inventory"][key])
        for key in ("physical", "reserved", "available")
    } == {
        "physical": 15,
        "reserved": 7,
        "available": 8,
    }
    record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "7",
        from_location_id=business.location.id,
        commitment_id=cid,
    )
    assert delivery_work(session, tid)["page"]["total"] == 0
    assert Decimal(delivery_case(session, tid, cid)["case"]["open"]) == 0


def test_effective_quantity_filters_before_paging(session, business):
    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    revise_commitment(session, tid, cid, quantity="15")
    result = delivery_work(session, tid, size=1)
    assert result["page"]["total"] == 1
    assert Decimal(result["items"][0]["promised"]) == 15
    assert Decimal(result["items"][0]["open"]) == 15
    assert result["items"][0]["unit"] == business.item.unit


def test_foreign_case_is_not_found_and_history_is_bounded(session, business):
    fixture = delivery_fixture(session, business)
    foreign = create_tenant(session, "Other company")
    with pytest.raises(NotFound):
        delivery_case(session, foreign.id, fixture.commitment.id)
    result = delivery_case(session, business.tenant.id, fixture.commitment.id)
    assert len(result["history"]["items"]) <= 20
    assert "has_more" in result["history"]
    assert result["links"] == []


def test_revisions_and_corrections_agree_with_inspector(session, business):
    from reality.services.core import correct_movement, preview_movement_correction
    from reality.web.api import commitment_inspector

    fixture = delivery_fixture(session, business)
    tid, cid = business.tenant.id, fixture.commitment.id
    revise_commitment(session, tid, cid, quantity="15")
    shipment = record_movement(
        session,
        tid,
        "shipment",
        business.item.id,
        "5",
        from_location_id=business.location.id,
        commitment_id=cid,
    )
    preview = preview_movement_correction(
        session, tid, shipment.id, reason="Wrong shipment"
    )
    correct_movement(
        session,
        tid,
        shipment.id,
        reason="Wrong shipment",
        expected_revision=preview["revision"],
        preview_fingerprint=preview["request_fingerprint"],
    )
    case = delivery_case(session, tid, cid)["case"]
    assert Decimal(case["fulfilled"]) == 0
    assert Decimal(case["open"]) == 15
    inspector = commitment_inspector(session, tid, cid)
    metrics = {row["label"]: Decimal(str(row["value"])) for row in inspector["metrics"]}
    assert metrics["Committed"] == 15
    assert metrics["Fulfilled"] == 0


def test_multiline_evidence_keeps_source_payload_and_shortest_links(session, business):
    import json

    from reality.services.core import ingest_shopify_order
    from reality.services.delivery_reads import delivery_evidence

    payload = {
        "id": "evidence-order",
        "name": "#EVIDENCE",
        "created_at": "2026-09-07T12:00:00Z",
        "currency": "EUR",
        "total_price": "120.00",
        "unknown_external": {"held": [1, "original"]},
        "line_items": [
            {
                "id": str(index),
                "sku": business.item.sku,
                "name": "Desk lamp",
                "quantity": 1,
                "price": "60.00",
            }
            for index in (1, 2)
        ],
    }
    _, _, _, commitments = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    assert len(commitments) == 2
    first = delivery_case(session, business.tenant.id, commitments[0].id)
    second = delivery_case(session, business.tenant.id, commitments[1].id)
    assert first["case"]["id"] != second["case"]["id"]
    assert first["links"][0]["id"] != second["links"][0]["id"]
    assert first["links"][1]["id"] == second["links"][1]["id"]
    source = next(link for link in first["links"] if link["kind"] == "source_record")
    business.item.source_record_id = source["id"]
    business.customer.source_record_id = source["id"]
    session.flush()
    inspected = delivery_evidence(
        session, business.tenant.id, source["kind"], source["id"]
    )
    assert (
        json.loads(inspected["source_payload"])["unknown_external"]
        == payload["unknown_external"]
    )
    linked = [
        row["link"]
        for section in inspected["sections"]
        for row in section["rows"]
        if row.get("link")
    ]
    assert {"kind": "document", "id": first["links"][1]["id"]} in linked
    assert any(link["kind"] == "business_event" for link in linked)
    assert {"kind": "item", "id": business.item.id} in linked
    assert {"kind": "party", "id": business.customer.id} in linked
    other = create_tenant(session, "Other source reader")
    with pytest.raises(NotFound):
        delivery_evidence(session, other.id, "source_record", source["id"])
    for link in first["links"]:
        if link["kind"] != "document":
            assert (
                delivery_evidence(
                    session, business.tenant.id, link["kind"], link["id"]
                )["id"]
                == link["id"]
            )


def test_source_links_are_bounded_and_tenant_scoped(session, business):
    from reality.db.core import BusinessEvent, SourceRecord
    from reality.services.delivery_reads import delivery_evidence

    source = SourceRecord(
        id="source-links",
        tenant_id=business.tenant.id,
        source_system="fixture",
        source_type="item",
        external_id="sku-1",
        payload='{"original": true}',
        payload_hash="a" * 64,
        version=1,
    )
    session.add(source)
    session.flush()
    empty = delivery_evidence(session, business.tenant.id, "source_record", source.id)
    assert empty["sections"][-1]["title"] == "Linked records"
    other = create_tenant(session, "Other events")
    session.add(
        BusinessEvent(
            id="foreign-event",
            tenant_id=other.id,
            sequence=1,
            event_type="Foreign",
            subject_type="item",
            subject_id="foreign-item",
            source_record_id=source.id,
        )
    )
    for index in range(101):
        session.add(
            BusinessEvent(
                id=f"linked-event-{index:03}",
                tenant_id=business.tenant.id,
                sequence=10000 + index,
                event_type="Observed",
                subject_type="item",
                subject_id=business.item.id,
                source_record_id=source.id,
            )
        )
    session.flush()
    result = delivery_evidence(session, business.tenant.id, "source_record", source.id)
    rows = result["sections"][-1]["rows"]
    assert len([row for row in rows if row["link"]]) == 100
    assert rows[-1]["label"] == "Only the first 100 linked records are shown."
    assert "foreign-event" not in str(rows)
    event = delivery_evidence(
        session, business.tenant.id, "business_event", rows[0]["link"]["id"]
    )
    assert any(
        row["link"] == {"kind": "item", "id": business.item.id}
        for row in event["sections"][0]["rows"]
    )
