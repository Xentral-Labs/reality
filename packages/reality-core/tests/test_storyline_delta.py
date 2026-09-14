"""Spec 182 FR-005: the primitives a chapter's delta is read from."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent, Fact
from reality.services.core import (
    InvalidOperation,
    activity_signal,
    create_master_source_record,
    now,
    observe_fact,
    record_movement,
    timeline_activity,
)


def _movements(session, business, count):
    for index in range(count):
        record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            business.item.id,
            index + 1,
            to_location_id=business.location.id,
        )


def test_timeline_reads_forward_after_a_marker_in_ascending_order(session, business):
    tenant_id = business.tenant.id
    _movements(session, business, 2)
    marker = activity_signal(session, tenant_id)["latest_sequence"]
    _movements(session, business, 3)

    page = timeline_activity(session, tenant_id, after_sequence=marker, limit=2)
    sequences = [event["sequence"] for event in page["events"]]

    assert sequences == sorted(sequences)
    assert all(sequence > marker for sequence in sequences)
    assert len(sequences) == 2 and page["has_more"] is True

    rest = timeline_activity(session, tenant_id, after_sequence=sequences[-1], limit=50)
    assert rest["has_more"] is False
    assert next(event["sequence"] for event in rest["events"]) > sequences[-1]

    everything = timeline_activity(
        session, tenant_id, after_sequence=0, hours=0, limit=250
    )
    assert [event["sequence"] for event in everything["events"]] == sorted(
        session.scalars(
            select(BusinessEvent.sequence).where(BusinessEvent.tenant_id == tenant_id)
        )
    )


def test_forward_and_backward_cursors_exclude_each_other(session, business):
    with pytest.raises(InvalidOperation):
        timeline_activity(
            session, business.tenant.id, after_sequence=1, before_sequence=5
        )


def test_forward_read_ignores_the_time_window(session, business):
    tenant_id = business.tenant.id
    record_movement(
        session,
        tenant_id,
        "opening_stock",
        business.item.id,
        1,
        to_location_id=business.location.id,
        occurred_at=now() - timedelta(days=90),
    )
    backward = timeline_activity(session, tenant_id, hours=24)
    forward = timeline_activity(session, tenant_id, after_sequence=0)

    assert not any(e["type"].startswith("movement") for e in backward["events"])
    assert any(e["type"].startswith("movement") for e in forward["events"])


def test_facts_carry_a_recording_order_independent_of_business_time(session, business):
    tenant_id = business.tenant.id
    source = create_master_source_record(
        session, tenant_id, "note", "storyline-test", "n-1", {"note": "fact source"}
    )
    before = now()
    fact = observe_fact(
        session,
        tenant_id,
        source_record_id=source.id,
        subject_type="commitment",
        subject_id=_commitment(session, business).id,
        predicate="order.delivery_instruction",
        value="Leave at the gate",
        observed_at=now() - timedelta(days=30),
        idempotency_key="fact-1",
    )

    stored = session.get(Fact, fact.id)
    assert stored.recorded_at is not None
    assert stored.recorded_at >= before
    assert stored.observed_at < stored.recorded_at - timedelta(days=29)
    recent = session.scalars(
        select(Fact).where(Fact.tenant_id == tenant_id, Fact.recorded_at > before)
    ).all()
    assert [row.id for row in recent] == [fact.id]


def _commitment(session, business):
    from reality.services.core import create_commitment

    return create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        None,
    )
