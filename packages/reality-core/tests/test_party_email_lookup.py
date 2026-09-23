import json

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent
from reality.mcp.catalog import dispatch_tool
from reality.services.core import (
    InvalidOperation,
    create_party,
    create_tenant,
    update_party,
)


def discover(session, tenant_id, query=""):
    return dispatch_tool(
        session,
        tenant_id,
        "business_records_discover",
        {"family": "party", "query": query},
    )["records"]


def test_party_discovery_matches_normalized_email_and_returns_labels(session, business):
    create_party(
        session,
        business.tenant.id,
        "Email customer",
        "customer",
        emails=[{"email": " Orders@Example.com ", "label": "Orders"}],
    )

    rows = discover(session, business.tenant.id, "orders@example.com")

    assert [(row["name"], row["emails"]) for row in rows] == [
        (
            "Email customer",
            [{"email": "Orders@Example.com", "label": "Orders"}],
        )
    ]


def test_shared_email_is_ambiguous_inside_tenant_and_isolated_across_tenants(
    session, business
):
    for name in ("First", "Second"):
        create_party(
            session,
            business.tenant.id,
            name,
            "customer",
            emails=[{"email": "shared@example.com"}],
        )
    foreign = create_tenant(session, "Foreign")
    create_party(
        session,
        foreign.id,
        "Foreign match",
        "customer",
        emails=[{"email": "shared@example.com"}],
    )

    assert {
        row["name"]
        for row in discover(session, business.tenant.id, "SHARED@example.com")
    } == {
        "First",
        "Second",
    }
    assert [
        row["name"] for row in discover(session, foreign.id, "shared@example.com")
    ] == ["Foreign match"]


def test_party_update_replaces_and_removes_emails(session, business):
    party = create_party(
        session,
        business.tenant.id,
        "Mutable",
        "customer",
        emails=[{"email": "old@example.com"}],
    )

    update_party(
        session,
        business.tenant.id,
        party.id,
        party.name,
        party.type,
        emails=[{"email": "new@example.com", "label": "New"}],
    )
    assert discover(session, business.tenant.id, "old@example.com") == []
    assert discover(session, business.tenant.id, "new@example.com")[0]["emails"] == [
        {"email": "new@example.com", "label": "New"}
    ]

    update_party(
        session,
        business.tenant.id,
        party.id,
        party.name,
        party.type,
        emails=[],
    )
    assert discover(session, business.tenant.id, "new@example.com") == []

    event = session.scalar(
        select(BusinessEvent)
        .where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.subject_id == party.id,
        )
        .order_by(BusinessEvent.sequence.desc())
    )
    assert json.loads(event.payload)["changes"]["emails"] == {
        "before": [{"email": "new@example.com", "label": "New"}],
        "after": [],
    }


def test_confirmed_party_proposals_persist_and_replace_emails(session, business):
    proposed = dispatch_tool(
        session,
        business.tenant.id,
        "party_create_propose",
        {
            "records": [
                {
                    "name": "Proposal customer",
                    "roles": ["customer"],
                    "emails": [{"email": "proposal@example.com", "label": "Orders"}],
                }
            ]
        },
        allowed_access=("propose",),
    )
    assert discover(session, business.tenant.id, "proposal@example.com") == []

    created = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": proposed["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )
    party_id = created["output"]["records"][0]["id"]
    row = discover(session, business.tenant.id, "proposal@example.com")[0]
    assert row["id"] == party_id

    update = dispatch_tool(
        session,
        business.tenant.id,
        "party_update_propose",
        {
            "records": [
                {
                    "id": party_id,
                    "name": "Proposal customer",
                    "type": "customer",
                    "roles": ["customer"],
                    "emails": [{"email": "replacement@example.com"}],
                }
            ]
        },
        allowed_access=("propose",),
    )
    dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": update["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )
    assert discover(session, business.tenant.id, "proposal@example.com") == []
    assert (
        discover(session, business.tenant.id, "replacement@example.com")[0]["id"]
        == party_id
    )


@pytest.mark.parametrize(
    "emails, message",
    [
        ([{"email": "not-an-email"}], "valid email"),
        (
            [{"email": "DUP@example.com"}, {"email": "dup@example.com"}],
            "duplicate",
        ),
        ([{"email": "ü@example.com"}], "ASCII"),
    ],
)
def test_invalid_party_email_lists_are_refused(session, business, emails, message):
    with pytest.raises(InvalidOperation, match=message):
        create_party(session, business.tenant.id, "Invalid", "customer", emails=emails)
