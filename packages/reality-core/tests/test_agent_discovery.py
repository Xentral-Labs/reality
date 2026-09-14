import pytest

from reality.mcp.catalog import dispatch_tool
from reality.services.core import NotFound, create_tenant, store_source_record


def test_discovery_returns_bounded_opaque_ids_and_current_values(session, business):
    result = dispatch_tool(
        session,
        business.tenant.id,
        "business_records_discover",
        {"family": "item", "query": "BIKE", "limit": 1},
        allowed_access=("read",),
    )

    assert result["records"] == [
        {
            "id": business.item.id,
            "sku": business.item.sku,
            "name": business.item.name,
            "unit": business.item.unit,
            "item_type": business.item.item_type,
            "tracking_type": business.item.tracking_type,
            "is_active": business.item.is_active,
        }
    ]


def test_discovery_hides_foreign_tenant_record(session, business):
    foreign = create_tenant(session, "Foreign")
    with pytest.raises(NotFound, match="Business record not found"):
        dispatch_tool(
            session,
            foreign.id,
            "business_records_discover",
            {"family": "item", "record_id": business.item.id},
            allowed_access=("read",),
        )


def test_discovery_returns_source_version_link_without_payload(session, business):
    first, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "discovery-regression",
        {"id": "discovery-regression", "state": "first"},
    )
    source, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "discovery-regression",
        {"id": "discovery-regression", "state": "changed"},
    )

    result = dispatch_tool(
        session,
        business.tenant.id,
        "business_records_discover",
        {"family": "source_record", "record_id": source.id},
        allowed_access=("read",),
    )

    assert result["records"] == [
        {
            "id": source.id,
            "source_system": "shopify",
            "source_type": "order",
            "external_id": "discovery-regression",
            "version": 2,
            "supersedes_source_record_id": first.id,
            "payload_hash": source.payload_hash,
            "received_at": source.received_at.isoformat(),
        }
    ]

    initial = dispatch_tool(
        session,
        business.tenant.id,
        "business_records_discover",
        {"family": "source_record", "record_id": first.id},
        allowed_access=("read",),
    )
    assert initial["records"][0]["supersedes_source_record_id"] is None
    assert "payload" not in result["records"][0]
