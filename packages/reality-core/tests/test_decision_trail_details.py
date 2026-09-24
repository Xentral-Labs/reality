"""Spec 263 FR-013/FR-014: a record's detail view names every decision behind it."""

from __future__ import annotations

from sqlalchemy import select

from reality.db.core import BusinessEvent, ChangeProposal, now, uid
from reality.services.core import create_party, create_tenant, emit_business_event
from reality.services.decision_attribution import record_decisions
from tests.test_decision_trail_surfaces import _person, api_client, app


def _decision(session, tenant_id, user_id, tool="party_create"):
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=tenant_id,
        type=f"tool:{tool}",
        status="executed",
        decided_at=now(),
        decided_by_user_id=user_id,
    )
    session.add(proposal)
    session.flush()
    return proposal


def test_a_record_names_the_decision_that_created_it_and_those_that_changed_it(
    session, business
):
    anna = _person(session, "anna@example.com", "Anna Owner")
    created = _decision(session, business.tenant.id, anna.id)
    party = create_party(
        session, business.tenant.id, "Decided", "customer", action_id=created.id
    )
    changed = _decision(session, business.tenant.id, anna.id, "party_update")
    emit_business_event(
        session,
        business.tenant.id,
        "party.updated",
        "party",
        party.id,
        {},
        action_id=changed.id,
    )

    decisions = record_decisions(session, business.tenant.id, "party", party.id)

    assert [(item["role"], item["id"]) for item in decisions] == [
        ("created", created.id),
        ("changed", changed.id),
    ]
    assert decisions[0]["decider"] == {"kind": "person", "name": "Anna Owner"}


def test_a_hand_entered_record_changed_later_claims_no_creating_decision(
    session, business
):
    anna = _person(session, "anna@example.com", "Anna Owner")
    party = create_party(session, business.tenant.id, "Hand entered", "customer")
    changed = _decision(session, business.tenant.id, anna.id, "party_update")
    emit_business_event(
        session,
        business.tenant.id,
        "party.updated",
        "party",
        party.id,
        {},
        action_id=changed.id,
    )

    decisions = record_decisions(session, business.tenant.id, "party", party.id)

    assert [(item["role"], item["id"]) for item in decisions] == [
        ("changed", changed.id)
    ]


def test_an_event_names_the_decision_that_caused_it(session, business):
    anna = _person(session, "anna@example.com", "Anna Owner")
    created = _decision(session, business.tenant.id, anna.id)
    party = create_party(
        session, business.tenant.id, "Decided", "customer", action_id=created.id
    )
    event_id = session.scalar(
        select(BusinessEvent.id).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.subject_id == party.id,
        )
    )

    decisions = record_decisions(
        session, business.tenant.id, "business_event", event_id
    )

    assert [(item["role"], item["id"]) for item in decisions] == [
        ("caused", created.id)
    ]


def test_records_without_decisions_and_other_companies_read_nothing(
    session, business
):
    anna = _person(session, "anna@example.com", "Anna Owner")
    plain = create_party(session, business.tenant.id, "Plain", "customer")
    other = create_tenant(session, "Other company")
    theirs = _decision(session, other.id, anna.id)
    their_party = create_party(
        session, other.id, "Theirs", "customer", action_id=theirs.id
    )

    assert record_decisions(session, business.tenant.id, "party", plain.id) == []
    assert (
        record_decisions(session, business.tenant.id, "party", their_party.id) == []
    )


def test_the_inspector_carries_the_decisions_of_its_record(session, business):
    anna = _person(session, "anna@example.com", "Anna Owner")
    created = _decision(session, business.tenant.id, anna.id)
    party = create_party(
        session, business.tenant.id, "Decided", "customer", action_id=created.id
    )
    client = api_client(session)
    try:
        body = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/party/{party.id}"
        ).json()
        plain = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/party/{business.customer.id}"
        ).json()
    finally:
        app.dependency_overrides.clear()

    assert [(item["role"], item["id"]) for item in body["decisions"]] == [
        ("created", created.id)
    ]
    assert plain["decisions"] == []
