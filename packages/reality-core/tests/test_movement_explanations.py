import json

import pytest

from reality.db.core import MovementCorrection, SourceRecord, uid
from reality.services.core import NotFound, create_commitment, record_movement
from reality.services.movement_explanations import movement_explanation


def test_commitment_is_the_shortest_explanation(session, business):
    incoming = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        1,
        None,
    )
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
        commitment_id=incoming.id,
    )

    result = movement_explanation(session, business.tenant.id, movement.id)

    assert result["kind"] == "commitment"
    assert result["explained"] is True
    assert result["links"][0] == {
        "kind": "commitment",
        "id": incoming.id,
        "label": "Delivery commitment",
    }


def test_source_provenance_is_exposed_and_tenant_scoped(session, business):
    source = SourceRecord(
        id=uid("src"),
        tenant_id=business.tenant.id,
        source_system="warehouse",
        source_type="receipt",
        external_id="GR-2026-0001",
        payload=json.dumps({"reference": "GR-2026-0001"}),
        payload_hash="e" * 64,
        version=1,
    )
    session.add(source)
    session.flush()
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
        source_record_id=source.id,
    )

    result = movement_explanation(session, business.tenant.id, movement.id)

    assert result["kind"] == "source"
    assert result["links"][0]["label"] == "GR-2026-0001"
    with pytest.raises(NotFound):
        movement_explanation(session, "tenant_other", movement.id)


def test_correction_takes_precedence_over_original_business_link(session, business):
    incoming = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        1,
        None,
    )
    original = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
        commitment_id=incoming.id,
    )
    compensation = record_movement(
        session,
        business.tenant.id,
        "adjustment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        reason="Reverse erroneous receipt",
    )
    relation = MovementCorrection(
        id=uid("mvc"),
        tenant_id=business.tenant.id,
        original_movement_id=original.id,
        compensating_movement_id=compensation.id,
        replacement_movement_id=None,
        reason="Wrong warehouse receipt",
        actor_context="{}",
        request_fingerprint="f" * 64,
    )
    session.add(relation)
    session.flush()

    result = movement_explanation(session, business.tenant.id, original.id)

    assert result["kind"] == "correction"
    assert result["reason"] == "Wrong warehouse receipt"
    assert result["links"][0]["kind"] == "movement_correction"


def test_unlinked_movement_is_explicitly_unexplained(session, business):
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        1,
        to_location_id=business.location.id,
    )

    result = movement_explanation(session, business.tenant.id, movement.id)

    assert result["explained"] is False
    assert result["kind"] == "unexplained"
    assert result["links"] == []
