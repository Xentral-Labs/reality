"""Narrow proposal-only adapters; no application/confirmation handler."""

from typing import Any

from sqlalchemy.orm import Session

from reality.services.shopify_order_proposal import (
    prepare_shopify_order,
    review_shopify_order,
)


def prepare(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Retain explicit order mapping and prospective meaning without accepting effects.

    BUSINESS RULE shopify_order_proposal.prepare_tool:
    Delegate exact typed selections to canonical proposal preparation, never generic execution or invented approval.
    """
    # reality-rule: shopify_order_proposal.prepare_tool
    return prepare_shopify_order(session, tenant_id, **arguments)


def review(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Read immutable order meaning and currentness for a later exact decision.

    BUSINESS RULE shopify_order_proposal.review_tool:
    Delegate tenant and exact proposal identity to canonical review without refresh, application or approval.
    """
    # reality-rule: shopify_order_proposal.review_tool
    return review_shopify_order(session, tenant_id, **arguments)
