"""Normal read adapter for exact retained Shopify intake diagnosis."""

from typing import Any

from sqlalchemy.orm import Session

from reality.services.shopify_intake_preflight import shopify_source_intake_preflight


def read(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Return exact retained source intake diagnosis without preparation or acceptance.

    BUSINESS RULE shopify_intake_preflight.read_tool:
    Delegate the authenticated tenant and strict input to the canonical read service; never choose or alter mappings or dispatch effects.
    """
    # reality-rule: shopify_intake_preflight.read_tool
    return shopify_source_intake_preflight(session, tenant_id, **arguments)
