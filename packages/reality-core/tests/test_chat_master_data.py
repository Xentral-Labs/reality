import json

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Item,
    Location,
    Party,
    PartyRole,
    SourceRecord,
)
from reality.mcp.catalog import dispatch_tool
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_location,
    create_tenant,
)


def _count(session, model, tenant_id):
    return session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant_id)
    )


@pytest.mark.parametrize(
    ("tool_name", "record", "model"),
    [
        (
            "party_create_propose",
            {"name": "New Customer", "roles": ["customer"]},
            Party,
        ),
        ("item_create_propose", {"sku": "SAMPLE-1", "name": "Sample Item"}, Item),
        ("location_create_propose", {"name": "Sample Warehouse"}, Location),
    ],
)
def test_master_data_tools_only_create_after_confirmation(
    session, business, tool_name, record, model
):
    before = _count(session, model, business.tenant.id)

    proposed = dispatch_tool(
        session,
        business.tenant.id,
        tool_name,
        {"records": [record]},
        allowed_access=("propose",),
    )

    assert proposed["status"] == "proposed"
    assert proposed["requires_confirmation"] is True
    assert _count(session, model, business.tenant.id) == before

    executed = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": proposed["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )

    assert executed["status"] == "executed"
    assert len(executed["output"]["records"]) == 1
    assert executed["output"]["records"][0]["id"]
    assert _count(session, model, business.tenant.id) == before + 1


def test_item_batch_confirmation_uses_defaults_and_is_atomic(session, business):
    before_items = _count(session, Item, business.tenant.id)
    before_events = _count(session, BusinessEvent, business.tenant.id)
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "item_create_propose",
        {
            "records": [
                {"sku": "SAMPLE-1", "name": "Sample One"},
                {"sku": "SAMPLE-2", "name": ""},
            ]
        },
        allowed_access=("propose",),
    )

    with pytest.raises(InvalidOperation, match="SKU, name, and unit"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal["proposal_id"], "approved": True},
            allowed_access=("confirm",),
        )

    assert _count(session, Item, business.tenant.id) == before_items
    assert _count(session, BusinessEvent, business.tenant.id) == before_events

    valid = dispatch_tool(
        session,
        business.tenant.id,
        "item_create_propose",
        {
            "records": [
                {"sku": "SAMPLE-1", "name": "Sample One"},
                {"sku": "SAMPLE-2", "name": "Sample Two"},
                {"sku": "SAMPLE-3", "name": "Sample Three"},
            ]
        },
        allowed_access=("propose",),
    )
    dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": valid["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )
    rows = session.scalars(
        select(Item).where(
            Item.tenant_id == business.tenant.id,
            Item.sku.in_(["SAMPLE-1", "SAMPLE-2", "SAMPLE-3"]),
        )
    ).all()
    assert len(rows) == 3
    assert {row.unit for row in rows} == {"pcs"}
    assert {row.source_record_id for row in rows} == {None}


def test_party_and_location_defaults_and_optional_source_are_preserved(
    session, business
):
    party_proposal = dispatch_tool(
        session,
        business.tenant.id,
        "party_create_propose",
        {
            "records": [
                {
                    "name": "Imported Supplier",
                    "roles": ["supplier"],
                    "source_system": "erp",
                    "external_id": "SUP-42",
                    "source_payload": {
                        "name": "Imported Supplier",
                        "unknown": {"kept": True},
                    },
                }
            ]
        },
        allowed_access=("propose",),
    )
    party_result = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": party_proposal["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )
    party = record_by_id(session, Party, party_result["output"]["records"][0]["id"])
    source = record_by_id(session, SourceRecord, party.source_record_id)
    assert json.loads(source.payload)["unknown"] == {"kept": True}
    assert (
        session.scalar(select(PartyRole.role).where(PartyRole.party_id == party.id))
        == "supplier"
    )

    location_proposal = dispatch_tool(
        session,
        business.tenant.id,
        "location_create_propose",
        {"records": [{"name": "Overflow"}]},
        allowed_access=("propose",),
    )
    location_result = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": location_proposal["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )
    location = record_by_id(
        session, Location, location_result["output"]["records"][0]["id"]
    )
    assert location.type == "warehouse"
    assert location.source_record_id is None


def test_incomplete_source_identity_rejects_complete_batch(session, business):
    before_items = _count(session, Item, business.tenant.id)
    before_sources = _count(session, SourceRecord, business.tenant.id)
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "item_create_propose",
        {
            "records": [
                {"sku": "LOCAL-1", "name": "Local Item"},
                {"sku": "ERP-1", "name": "Incomplete Source", "source_system": "erp"},
            ]
        },
        allowed_access=("propose",),
    )

    with pytest.raises(InvalidOperation, match="must be provided together"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal["proposal_id"], "approved": True},
            allowed_access=("confirm",),
        )

    assert _count(session, Item, business.tenant.id) == before_items
    assert _count(session, SourceRecord, business.tenant.id) == before_sources


def test_foreign_location_relationship_rejects_complete_batch(session, business):
    foreign = create_tenant(session, "Foreign company")
    foreign_parent = create_location(session, foreign.id, "Foreign warehouse")
    before = _count(session, Location, business.tenant.id)
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "location_create_propose",
        {
            "records": [
                {"name": "Local child"},
                {"name": "Invalid child", "parent_location_id": foreign_parent.id},
            ]
        },
        allowed_access=("propose",),
    )

    with pytest.raises(NotFound, match="not found"):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal["proposal_id"], "approved": True},
            allowed_access=("confirm",),
        )

    assert _count(session, Location, business.tenant.id) == before


def test_location_batch_resolves_local_parent_references(session, business):
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "location_create_propose",
        {
            "records": [
                {"ref": "berlin", "name": "Lager Berlin", "type": "warehouse"},
                {
                    "ref": "zone-1",
                    "name": "Zone 1",
                    "type": "zone",
                    "parent_ref": "berlin",
                },
                {"name": "1-001", "type": "shelf", "parent_ref": "zone-1"},
            ]
        },
        allowed_access=("propose",),
    )
    result = dispatch_tool(
        session,
        business.tenant.id,
        "proposal_approve_and_execute",
        {"proposal_id": proposal["proposal_id"], "approved": True},
        allowed_access=("confirm",),
    )

    warehouse_id, zone_id, shelf_id = [row["id"] for row in result["output"]["records"]]
    assert record_by_id(session, Location, warehouse_id).parent_location_id is None
    assert record_by_id(session, Location, zone_id).parent_location_id == warehouse_id
    assert record_by_id(session, Location, shelf_id).parent_location_id == zone_id


@pytest.mark.parametrize(
    "records",
    [
        [{"name": "Orphan", "parent_ref": "missing"}],
        [{"ref": "same", "name": "One"}, {"ref": "same", "name": "Two"}],
        [
            {"ref": "parent", "name": "Parent"},
            {
                "name": "Child",
                "parent_ref": "parent",
                "parent_location_id": "loc_other",
            },
        ],
    ],
)
def test_invalid_location_local_references_reject_complete_batch(
    session, business, records
):
    before = _count(session, Location, business.tenant.id)
    proposal = dispatch_tool(
        session,
        business.tenant.id,
        "location_create_propose",
        {"records": records},
        allowed_access=("propose",),
    )

    with pytest.raises(InvalidOperation):
        dispatch_tool(
            session,
            business.tenant.id,
            "proposal_approve_and_execute",
            {"proposal_id": proposal["proposal_id"], "approved": True},
            allowed_access=("confirm",),
        )

    assert _count(session, Location, business.tenant.id) == before
