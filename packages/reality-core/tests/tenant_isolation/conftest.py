from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from reality.services.core import (
    create_chat_session,
    create_commitment,
    create_document,
    create_item,
    create_location,
    create_master_source_record,
    create_party,
    create_source_capability,
    create_source_system,
    create_tenant,
    post_sales_invoice,
    record_movement,
)


@dataclass(frozen=True)
class TenantGraph:
    tenant: object
    company: object
    customer: object
    item: object
    location: object
    source: object
    document: object
    commitment: object
    invoice: object
    chat_session: object
    source_system: object


@dataclass(frozen=True)
class TwoTenantGraph:
    local: TenantGraph
    foreign: TenantGraph


def _graph(session, label: str, quantity: Decimal) -> TenantGraph:
    tenant = create_tenant(session, f"{label} Company")
    company = create_party(session, tenant.id, "Shared Company", "company")
    customer = create_party(session, tenant.id, "Shared Customer", "customer")
    item = create_item(session, tenant.id, "SHARED-SKU", "Shared Item")
    location = create_location(session, tenant.id, "Shared Warehouse")
    source = create_master_source_record(
        session,
        tenant.id,
        "sales_order",
        "isolation-fixture",
        "SHARED-ORDER",
        {"external_id": "SHARED-ORDER", "tenant_marker": label, "unknown": {"x": 1}},
    )
    document = create_document(
        session,
        tenant.id,
        "sales_order",
        "SHARED-ORDER",
        customer.id,
        "100.00",
        source_record_id=source.id,
    )
    commitment = create_commitment(
        session,
        tenant.id,
        "customer_delivery",
        company.id,
        customer.id,
        item.id,
        location.id,
        quantity,
        "2026-09-03",
        document_id=document.id,
    )
    record_movement(
        session,
        tenant.id,
        "opening_stock",
        item.id,
        quantity,
        to_location_id=location.id,
        source_record_id=source.id,
    )
    invoice = create_document(
        session,
        tenant.id,
        "sales_invoice",
        "SHARED-INVOICE",
        customer.id,
        "100.00",
        source_record_id=source.id,
    )
    post_sales_invoice(session, tenant.id, invoice.id)
    chat_session = create_chat_session(session, tenant.id)
    source_system = create_source_system(
        session, tenant.id, "shared-shop", "Shared Shop"
    )
    create_source_capability(
        session, tenant.id, source_system.id, "order", "sales_order"
    )
    return TenantGraph(
        tenant,
        company,
        customer,
        item,
        location,
        source,
        document,
        commitment,
        invoice,
        chat_session,
        source_system,
    )


@pytest.fixture
def two_tenant_graph(session) -> TwoTenantGraph:
    return TwoTenantGraph(
        local=_graph(session, "Local", Decimal(3)),
        foreign=_graph(session, "Foreign", Decimal(11)),
    )
