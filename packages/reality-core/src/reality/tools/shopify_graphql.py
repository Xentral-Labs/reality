"""Narrow original-source capture adapter, independent of generic approval."""

from typing import Any

from sqlalchemy.orm import Session

from reality.services.shopify_graphql import capture_shopify_graphql_source


def capture(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Return retained original source/job identities without granting or accepting business effects.

    BUSINESS RULE shopify_graphql.capture_tool:
    Delegate the authenticated tenant and exact input to canonical capture, returning only retained identities and explicit no-effect status.
    """
    # reality-rule: shopify_graphql.capture_tool
    source, job = capture_shopify_graphql_source(session, tenant_id, **arguments)
    return {
        "source_record_id": source.id,
        "import_job_id": job.id,
        "status": job.status,
        "business_effects_accepted": False,
    }
