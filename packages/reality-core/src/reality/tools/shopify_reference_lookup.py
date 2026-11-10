"""Normal read adapter for exact-source reference choices."""

from typing import Any

from sqlalchemy.orm import Session

from reality.services.shopify_reference_lookup import shopify_source_reference_lookup


def read(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Expose bounded existing reference observations through the normal tenant-scoped read tool.

    BUSINESS RULE shopify_reference_lookup.read_tool:
    Delegate strict input and authenticated tenant to the shared read service; never prepare, choose or write a mapping.
    """
    # reality-rule: shopify_reference_lookup.read_tool
    return shopify_source_reference_lookup(session, tenant_id, **arguments)
