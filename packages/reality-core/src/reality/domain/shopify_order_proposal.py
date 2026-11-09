"""Spec391: explicit proposed interpretation, never business acceptance."""

from typing import Any, Literal

from pydantic import Field, model_validator

from reality.domain.intake import PreparedIntake, content_digest
from reality.domain.shopify_buyer_mapping import HEX, Strict, nonce
from reality.domain.shopify_intake_preflight import (
    PreflightInput,
    SourceBinding,
    VerifiedMapping,
)

PURPOSE = "shopify_source_order_proposal_only/1"
ACTION_TYPE = "shopify_order_proposal/1"
MAX_WIRE_BYTES = 24000
MAX_PLAN_BYTES = 2 * 1024 * 1024


class LineSelection(Strict):
    source_line_id: str = Field(pattern=r"^gid://shopify/LineItem/[0-9]{1,32}$")
    item_id: str = Field(min_length=1, max_length=200)
    stock_unit: str = Field(min_length=1, max_length=100)
    quantity_semantics: Literal["one_source_count_is_one_stock_unit"]
    expected_item_digest: str | None = Field(default=None, pattern=HEX)


class OrderPrepareInput(PreflightInput):
    request_id: str = Field(min_length=36, max_length=36)
    buyer_review_id: str = Field(min_length=1, max_length=200)
    buyer_review_digest: str = Field(pattern=HEX)
    company_party_id: str = Field(min_length=1, max_length=200)
    location_id: str = Field(min_length=1, max_length=200)
    expected_company_digest: str | None = Field(default=None, pattern=HEX)
    expected_location_digest: str | None = Field(default=None, pattern=HEX)
    lines: list[LineSelection] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_lines(self):
        nonce(self.request_id)
        if len({line.source_line_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate_source_line_selection")
        return self


class OrderReviewInput(Strict):
    proposal_id: str = Field(min_length=1, max_length=200)


class StoredOrderProposal(Strict):
    purpose: Literal["shopify_source_order_proposal_only/1"]
    request: OrderPrepareInput
    source_binding: SourceBinding
    buyer_mapping: VerifiedMapping
    mapping_bundle: dict[str, Any]
    plan: PreparedIntake
    source_price_evidence: list[dict[str, str]]

    @model_validator(mode="after")
    def closed_meaning(self):
        if self.mapping_bundle.get("state") != "proposed":
            raise ValueError("mapping_not_authorized_here")
        if self.plan.mapping.get("origin") != ACTION_TYPE:
            raise ValueError("proposal_origin_mismatch")
        if self.plan.mapping.get("bundle_digest") != content_digest(
            self.mapping_bundle
        ):
            raise ValueError("bundle_digest_mismatch")
        if (
            self.plan.source_record_id != self.source_binding.source_record_id
            or self.plan.source_hash != self.source_binding.source_hash
            or self.plan.source_version != self.source_binding.source_version
            or self.plan.import_job_id != self.source_binding.import_job_id
        ):
            raise ValueError("source_binding_mismatch")
        if self.plan.tenant_id != self.source_binding.tenant_id:
            raise ValueError("tenant_mismatch")
        if (
            not self.plan.effects
            or self.plan.effects[0].operation != "document"
            or any(
                effect.operation not in {"document", "commitment", "credit_hold"}
                for effect in self.plan.effects
            )
        ):
            raise ValueError("unsupported_prospective_effect")
        if sum(effect.operation == "document" for effect in self.plan.effects) != 1:
            raise ValueError("one_order_document_required")
        return self


class OrderProposalReview(Strict):
    purpose: Literal["shopify_source_order_proposal_only/1"]
    proposal_id: str = Field(min_length=1, max_length=200)
    status: Literal["proposed", "stale"]
    request_id: str = Field(min_length=36, max_length=36)
    request_digest: str = Field(pattern=HEX)
    review_digest: str = Field(pattern=HEX)
    source_binding: SourceBinding
    buyer_mapping: VerifiedMapping
    mapping_bundle: dict[str, Any]
    plan_digest: str = Field(pattern=HEX)
    review_projection: PreparedIntake
    projection_scope: Literal[
        "all_business_effect_arguments_excluding_original_line_payloads"
    ]
    source_price_evidence: list[dict[str, str]] = Field(max_length=100)
    holds: list[str] = Field(max_length=20)
    application_allowed: Literal[False]
    generic_confirmation_allowed: Literal[False]
    business_effects_accepted: Literal[False]
    original_source_unchanged: Literal[True]
    import_job_input_unchanged: Literal[True]
