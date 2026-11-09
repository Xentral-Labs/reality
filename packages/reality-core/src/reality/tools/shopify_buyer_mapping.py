"""Narrow mapping-only adapters; commit requires an exact issuer-signed human review."""

from typing import Any

from sqlalchemy.orm import Session

from reality.services.shopify_buyer_mapping import (
    buyer_candidates,
    buyer_mapping_status,
    commit_buyer_mapping,
    prepare_buyer_mapping,
)


def candidates(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Delegate exact source buyer mapping evidence to canonical tenant services without business order effects.

    BUSINESS RULE shopify_buyer_mapping.tool_candidates:
    Preserve authenticated tenant and strict input; the canonical service alone validates the live source, existing customer and human proof.
    """
    # reality-rule: shopify_buyer_mapping.tool_candidates
    return buyer_candidates(session, tenant_id, arguments)


def prepare(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Delegate exact source buyer mapping evidence to canonical tenant services without business order effects.

    BUSINESS RULE shopify_buyer_mapping.tool_prepare:
    Preserve authenticated tenant and strict input; the canonical service alone validates the live source, existing customer and human proof.
    """
    # reality-rule: shopify_buyer_mapping.tool_prepare
    return prepare_buyer_mapping(session, tenant_id, arguments)


def commit(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Delegate exact source buyer mapping evidence to canonical tenant services without business order effects.

    BUSINESS RULE shopify_buyer_mapping.tool_commit:
    Preserve authenticated tenant and strict input; the canonical service alone validates the live source, existing customer and human proof.
    """
    # reality-rule: shopify_buyer_mapping.tool_commit
    return commit_buyer_mapping(session, tenant_id, arguments)


def status(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Delegate exact source buyer mapping evidence to canonical tenant services without business order effects.

    BUSINESS RULE shopify_buyer_mapping.tool_status:
    Preserve authenticated tenant and strict input; the canonical service alone validates the live source, existing customer and human proof.
    """
    # reality-rule: shopify_buyer_mapping.tool_status
    return buyer_mapping_status(session, tenant_id, arguments)
