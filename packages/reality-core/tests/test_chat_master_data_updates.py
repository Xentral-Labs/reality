import json

import pytest
from sqlalchemy import select

from reality.db.core import BusinessEvent, Item, PartyRole
from reality.mcp.catalog import dispatch_tool
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_item,
    create_tenant,
    update_item,
)


def _item_record(item, **changes):
    record = {
        "id": item.id,
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "item_type": item.item_type,
        "tracking_type": item.tracking_type,
        "default_location_id": item.default_location_id,
        "purchase_unit": item.purchase_unit,
        "conversion_factor": str(item.conversion_factor),
        "lead_time_days": item.lead_time_days,
    }
    record.update(changes)
    return record


def test_item_update_proposal_previews_then_executes_with_action_link(
    session, business
):
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "item_update_propose",
        {"records": [_item_record(business.item, name="Updated by Chat")]},
        allowed_access=("propose",),
    )
    session.refresh(business.item)
    assert business.item.name != "Updated by Chat"
    assert (
        proposal["preview"]["records"][0]["changes"]["name"]["after"]
        == "Updated by Chat"
    )

    dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": proposal["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )
    session.refresh(business.item)
    assert business.item.name == "Updated by Chat"
    event = session.scalar(
        select(BusinessEvent)
        .where(BusinessEvent.subject_id == business.item.id)
        .order_by(BusinessEvent.sequence.desc())
    )
    assert event.action_id == proposal["proposal_id"]
    assert json.loads(event.payload)["changes"]["name"]["before"] != "Updated by Chat"


def test_item_update_proposal_rejects_stale_confirmation(session, business):
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "item_update_propose",
        {"records": [_item_record(business.item, name="Proposed Name")]},
        allowed_access=("propose",),
    )
    update_item(
        session,
        business.tenant.id,
        business.item.id,
        business.item.sku,
        "Concurrent Name",
        business.item.unit,
    )

    with pytest.raises(InvalidOperation, match="changed since proposal review"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal["proposal_id"], "approved": True},
            allowed_access=("confirm",),
        )
    session.refresh(business.item)
    assert business.item.name == "Concurrent Name"


def test_update_proposals_cover_party_and_location(session, business):
    roles = sorted(
        session.scalars(
            select(PartyRole.role).where(PartyRole.party_id == business.customer.id)
        ).all()
    )
    party = dispatch_tool(
        session,
        business.tenant.id,
        "party_update_propose",
        {
            "records": [
                {
                    "id": business.customer.id,
                    "name": "Updated Party",
                    "type": business.customer.type,
                    "roles": roles,
                }
            ]
        },
        allowed_access=("propose",),
    )
    location = dispatch_tool(
        session,
        business.tenant.id,
        "location_update_propose",
        {
            "records": [
                {
                    "id": business.location.id,
                    "name": "Updated Location",
                    "type": business.location.type,
                }
            ]
        },
        allowed_access=("propose",),
    )
    assert party["preview"]["records"][0]["changes"]["name"]["after"] == "Updated Party"
    assert (
        location["preview"]["records"][0]["changes"]["name"]["after"]
        == "Updated Location"
    )


def test_item_update_batch_is_atomic(session, business):
    second = Item(
        id="itm_atomic_second",
        tenant_id=business.tenant.id,
        sku="SECOND",
        name="Second",
        unit="pcs",
    )
    session.add(second)
    session.commit()
    first_name = business.item.name

    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "item_update_propose",
        {
            "records": [
                _item_record(business.item, name="Must Roll Back"),
                _item_record(second, name="Invalid", lead_time_days=-1),
            ]
        },
        allowed_access=("propose",),
    )
    with pytest.raises(InvalidOperation, match="Lead time days"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal["proposal_id"], "approved": True},
            allowed_access=("confirm",),
        )
    session.refresh(business.item)
    assert business.item.name == first_name


def test_update_proposal_does_not_disclose_foreign_target(session, business):
    other = create_tenant(session, "Other update tenant")
    foreign = create_item(session, other.id, "SECRET", "Foreign item")

    with pytest.raises(NotFound):
        dispatch_tool(
            session,
            business.tenant.id,
            "item_update_propose",
            {"records": [_item_record(foreign, name="Forbidden")]},
            allowed_access=("propose",),
        )
