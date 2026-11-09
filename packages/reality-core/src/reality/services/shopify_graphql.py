"""Spec 388: original Shopify entity capture and preparation, never acceptance."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import Document, ImportJob, SourceRecord
from reality.domain.intake import PreparedIntake
from reality.services import core


class ShopifyGraphQLNeedsReview(core.InterpretationNeedsReview):
    summary = "The original Shopify GraphQL entity is retained, but this observation is outside the supported complete first-order interpretation. No business effects were accepted."
    reason_code = "shopify_graphql_requires_review"


class ShopifyGraphQLMappingRequired(core.InterpretationNeedsReview):
    summary = "The original Shopify order is retained. Explicit existing company, customer and location mappings are required before a business-effect proposal can be prepared. No customer was invented and no business effects were accepted."
    reason_code = "shopify_graphql_mapping_required"


class ShopifyBuyerMappingRecorded(core.InterpretationNeedsReview):
    summary = "The reviewed existing buyer mapping is recorded for this original source. Full intake remains held for separate company/location and business-effect review; no order was created."
    reason_code = "buyer_mapping_recorded_intake_pending"


class Acquisition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    shop: str = Field(
        pattern=r"^[a-z0-9][a-z0-9-]{0,62}\.myshopify\.com$", max_length=253
    )
    api_version: str = Field(pattern=r"^[0-9]{4}-(01|04|07|10)$")
    query_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_at: str = Field(min_length=1, max_length=100)
    coverage: Literal["complete-selected-order"]


class CaptureInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    order: dict[str, Any]
    company_party_id: str | None = Field(default=None, min_length=1, max_length=200)
    customer_party_id: str | None = Field(default=None, min_length=1, max_length=200)
    location_id: str | None = Field(default=None, min_length=1, max_length=200)
    acquisition: Acquisition | None = None


class _Identity(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    id: str = Field(pattern=r"^gid://shopify/Order/[0-9]{1,32}$")
    updatedAt: str = Field(min_length=1, max_length=100)


def capture_shopify_graphql_source(
    session: Session, tenant_id: str, **arguments: Any
) -> tuple[SourceRecord, ImportJob]:
    """
    BUSINESS PURPOSE:
    Retain one original selected Shopify order entity and queue exact interpretation without accepting business effects.

    BUSINESS RULE shopify_graphql.capture_source:
    Validate the bounded capture, derive original identity and update time, and delegate only to canonical enqueue_source.
    """
    # reality-rule: shopify_graphql.capture_source
    try:
        value = CaptureInput.model_validate(arguments)
        identity = _Identity.model_validate(value.order)
        if datetime.fromisoformat(identity.updatedAt).utcoffset() is None:
            raise ValueError("timezone_required")
        version_at = core.utc_datetime(identity.updatedAt)
        if (
            not version_at
            or len(json.dumps(value.order, allow_nan=False).encode("utf-8")) > 1_000_000
        ):
            raise ValueError("invalid_source_boundary")
        if (
            value.acquisition
            and datetime.fromisoformat(value.acquisition.observed_at).utcoffset()
            is None
        ):
            raise ValueError("invalid_acquisition_time")
    except (ValidationError, ValueError, TypeError, OverflowError) as error:
        raise core.InvalidOperation(code="shopify_graphql_capture_invalid") from error
    context = value.model_dump(exclude={"order"}, exclude_none=True)
    source, job = core.enqueue_source(
        session,
        tenant_id,
        "shopify",
        "order_graphql",
        identity.id.rsplit("/", 1)[1],
        value.order,
        source_version_at=version_at,
        context=context,
    )
    existing = json.loads(job.input)
    if any(
        context.get(key) is not None and existing.get(key) != context[key]
        for key in ("company_party_id", "customer_party_id", "location_id")
    ):
        raise core.InvalidOperation(code="shopify_graphql_mapping_changed")
    return source, job


def prepare_graphql_order(
    session: Session, tenant_id: str, source: SourceRecord, job: ImportJob
) -> PreparedIntake:
    """Prepare supported received meaning against the original immutable source."""
    from reality.integrations.shopify.graphql import (
        GraphQLOrderNeedsReview,
        project_order,
    )
    from reality.services.shopify_intake import prepare_order

    source = core._tenant_record_read(session, SourceRecord, tenant_id, source.id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job.id)
    if job.source_record_id != source.id or (
        source.source_system,
        source.source_type,
    ) != ("shopify", "order_graphql"):
        raise core.NotFound(code="record_not_found", values={"record": "SourceRecord"})
    raw = json.loads(source.payload)
    try:
        projection = project_order(raw, source.external_id)
    except GraphQLOrderNeedsReview as error:
        raise ShopifyGraphQLNeedsReview() from error
    mapping = json.loads(job.input)
    if not mapping.get("customer_party_id"):
        from reality.services.shopify_buyer_mapping import get_verified_buyer_mapping

        reviewed = get_verified_buyer_mapping(session, tenant_id, source.id, job.id)
        if reviewed is not None:
            raise ShopifyBuyerMappingRecorded()
    if any(
        not mapping.get(key)
        for key in ("company_party_id", "customer_party_id", "location_id")
    ):
        raise ShopifyGraphQLMappingRequired()
    # A distinct raw shape is not a new external order identity. Refuse both
    # GraphQL updates and legacy accepted orders until their route is reviewed.
    prior = session.scalar(
        select(Document.id)
        .join(SourceRecord, Document.source_record_id == SourceRecord.id)
        .where(
            Document.tenant_id == tenant_id,
            SourceRecord.tenant_id == tenant_id,
            Document.type == "sales_order",
            SourceRecord.source_system == "shopify",
            SourceRecord.external_id == source.external_id,
        )
        .limit(1)
    )
    if prior:
        raise ShopifyGraphQLNeedsReview()
    return prepare_order(
        session,
        tenant_id,
        source,
        job,
        _payload=projection,
        _line_payloads=raw["lineItems"]["nodes"],
    )
