"""Narrow exact successor adapters; generic confirmation never owns these effects."""

from reality.services.shopify_order_acceptance import (
    accept_order,
    order_acceptance_status,
    prepare_order_acceptance,
    review_order_acceptance,
)


def prepare(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Prepare one exact complete source-backed order review without accepting it.

    BUSINESS RULE shopify_order_acceptance.prepare_tool:
    Delegate explicit source/reference/profile terms to canonical preparation only.
    """
    # reality-rule: shopify_order_acceptance.prepare_tool
    return prepare_order_acceptance(session, tenant_id, arguments)


def review(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read retained exact order meaning and current evidence before authorization.

    BUSINESS RULE shopify_order_acceptance.review_tool:
    Return only same-tenant exact retained successor evidence, never approval.
    """
    # reality-rule: shopify_order_acceptance.review_tool
    return review_order_acceptance(session, tenant_id, arguments)


def accept(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Apply the exact source-backed order through verified external human or finite mandate authority.

    BUSINESS RULE shopify_order_acceptance.accept_tool:
    Delegate the original compact signed exact proof to canonical atomic acceptance; a model or token never becomes a human approver.
    """
    # reality-rule: shopify_order_acceptance.accept_tool
    return accept_order(session, tenant_id, arguments)


def status(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Reconcile a known order acceptance receipt without repeating effects.

    BUSINESS RULE shopify_order_acceptance.status_tool:
    Read scoped historical original proof identity and canonical results; never dispatch or renew authority.
    """
    # reality-rule: shopify_order_acceptance.status_tool
    return order_acceptance_status(session, tenant_id, arguments)
