"""Spec392 source-backed simple profile and exact external authorization contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, localcontext
from typing import Literal

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from reality.domain.intake import PreparedIntake, content_digest
from reality.domain.shopify_buyer_mapping import (
    HEX,
    SHOP,
    _strict_json,
    decode64,
    instant,
    nonce,
)
from reality.domain.shopify_intake_preflight import SourceBinding, VerifiedMapping
from reality.domain.shopify_order_proposal import OrderPrepareInput
from reality.integrations.shopify.graphql import (
    GraphQLOrderNeedsReview,
    _MoneySet,
    project_order,
)

PROFILE = "shopify_simple_undiscounted_order/1"
PURPOSE = "shopify_source_order_acceptance/1"
ACTION_TYPE = "shopify_order_acceptance/1"
TOTAL_FIELDS = ("subtotalPriceSet", "currentSubtotalPriceSet", "currentTotalPriceSet")
ZERO_FIELDS = (
    "totalDiscountsSet",
    "currentTotalDiscountsSet",
    "totalTaxSet",
    "currentTotalTaxSet",
    "totalShippingPriceSet",
    "currentShippingPriceSet",
    "totalRefundedSet",
    "totalTipReceivedSet",
)


def inspect_simple_source(raw: dict) -> dict:
    """Copy stated values only; arithmetic compares eligibility, never supplies money."""
    holds: list[str] = []
    result = {"profile": PROFILE, "holds": holds, "lines": [], "fees": {}, "duties": {}}

    def hold(reason: str) -> None:
        if reason not in holds:
            holds.append(reason)

    currency = raw.get("currencyCode")

    def money(container: dict, key: str, path: str) -> str | None:
        try:
            value = _MoneySet.model_validate(container[key]).shopMoney
            if value.currencyCode != currency or not Decimal(value.amount).is_finite():
                raise ValueError()
            return value.amount
        except (ValidationError, ValueError, KeyError, TypeError):
            hold("source_money_unknown_or_currency_mismatch:" + path)
            return None

    try:
        project_order(raw, str(raw.get("id", "")).rsplit("/", 1)[-1])
    except (GraphQLOrderNeedsReview, ValueError, TypeError):
        hold("complete_unchanged_first_order_required")
    if raw.get("edited") is not False:
        hold("unedited_source_required")
    try:
        processed = raw["processedAt"]
        if not isinstance(processed, str) or len(processed) > 100:
            raise ValueError()
        if datetime.fromisoformat(processed).utcoffset() is None:
            raise ValueError()
        result["processed_at"] = processed
    except (KeyError, ValueError, TypeError, OverflowError):
        hold("processed_at_unknown")
    totals = {
        field: money(raw, field, field) for field in (*TOTAL_FIELDS, "totalPriceSet")
    }
    zeros = {field: money(raw, field, field) for field in ZERO_FIELDS}
    for field, value in zeros.items():
        if value is not None and Decimal(value) != 0:
            hold("unsupported_nonzero:" + field)
    container = raw.get("lineItems")
    nodes = container.get("nodes", []) if isinstance(container, dict) else []
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 100:
        hold("complete_bounded_lines_required")
        nodes = []
    empty_duties = bool(nodes) and all(
        isinstance(line, dict) and line.get("duties") == [] for line in nodes
    )
    if not empty_duties:
        hold("complete_empty_line_duties_required")
    if raw.get("additionalFees") != []:
        hold("complete_empty_additional_fees_required")
    for name, fields, empty_evidence, absence in (
        (
            "fees",
            ("originalTotalAdditionalFeesSet", "currentTotalAdditionalFeesSet"),
            raw.get("additionalFees") == [],
            "not_applicable",
        ),
        (
            "duties",
            ("originalTotalDutiesSet", "currentTotalDutiesSet"),
            empty_duties
            and raw.get("edited") is False
            and zeros.get("totalRefundedSet") is not None
            and Decimal(zeros["totalRefundedSet"]) == 0,
            "not_applicable_no_line_duties",
        ),
    ):
        if (
            all(field in raw and raw[field] is None for field in fields)
            and empty_evidence
        ):
            result[name] = {
                "status": absence,
                "paths": list(fields),
                "list_evidence": "additionalFees"
                if name == "fees"
                else "lineItems.nodes[*].duties",
            }
        else:
            values = {field: money(raw, field, field) for field in fields}
            for field, value in values.items():
                if value is not None and Decimal(value) != 0:
                    hold("unsupported_nonzero:" + field)
            result[name] = {"status": "stated", "values": values}
    stated_line_totals: list[str] = []
    for line in nodes:
        if not isinstance(line, dict):
            hold("invalid_source_line")
            continue
        identity = line.get("id", "unknown")
        unit = money(
            line, "originalUnitPriceSet", str(identity) + ".originalUnitPriceSet"
        )
        total = money(line, "originalTotalSet", str(identity) + ".originalTotalSet")
        quantity = line.get("quantity")
        if (
            type(quantity) is not int
            or not 1 <= quantity <= 1_000_000_000
            or line.get("currentQuantity") != quantity
        ):
            hold("bounded_unchanged_quantity_required")
            continue
        if unit is not None and total is not None:
            with localcontext() as context:
                context.prec = 160
                if Decimal(unit) * quantity != Decimal(total):
                    hold("stated_unit_line_total_disagree:" + str(identity))
            stated_line_totals.append(total)
            result["lines"].append(
                {
                    "source_line_id": identity,
                    "quantity": str(quantity),
                    "unit_price": unit,
                    "line_total": total,
                    "currency": currency,
                }
            )
    if len(stated_line_totals) != len(nodes) or not nodes:
        hold("all_stated_line_amounts_required")
    elif all(value is not None for value in totals.values()):
        with localcontext() as context:
            context.prec = 160
            compared = sum((Decimal(value) for value in stated_line_totals), Decimal(0))
            if any(Decimal(value) != compared for value in totals.values()):
                hold("stated_line_subtotal_order_totals_disagree")
    # Canonical business columns are Numeric(18,4); PostgreSQL must not round
    # a received amount into a new authoritative value during acceptance.
    persisted = [value for value in totals.values() if value is not None]
    persisted.extend(
        value
        for line in result["lines"]
        for value in (line["unit_price"], line["line_total"])
    )
    with localcontext() as context:
        context.prec = 160
        if any(
            Decimal(value) >= Decimal(100000000000000)
            or Decimal(value).quantize(Decimal("0.0001")) != Decimal(value)
            for value in persisted
        ):
            hold("source_money_not_exactly_representable_by_canonical_storage")
    result["stated_totals"] = totals
    result["stated_zero_components"] = zeros
    result["currency"] = currency
    result["created_at"] = raw.get("createdAt")
    return result


# The successor deliberately has distinct immutable records and schemas from391.
AUDIENCE = "reality:shopify-source-order-acceptance/1"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AcceptancePrepareInput(OrderPrepareInput):
    interpretation_profile: Literal["shopify_simple_undiscounted_order/1"]
    delivery_terms: Literal["not_promised"]


class AcceptanceReviewInput(Strict):
    proposal_id: str = Field(min_length=1, max_length=200)


class AcceptanceCommitInput(AcceptanceReviewInput):
    review_digest: str = Field(pattern=HEX)
    approval_proof: str = Field(min_length=1, max_length=16384)


class StandingMandate(Strict):
    id: str = Field(min_length=1, max_length=200)
    revision: int = Field(gt=0)
    subject: str = Field(min_length=1, max_length=200)
    profile: Literal["shopify_simple_undiscounted_order/1"]
    delivery_terms: Literal["not_promised"]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    max_order_amount: str = Field(pattern=r"^(0|[1-9][0-9]{0,17})(\.[0-9]{1,6})?$")
    max_total_amount: str = Field(pattern=r"^(0|[1-9][0-9]{0,17})(\.[0-9]{1,6})?$")
    max_orders: int = Field(ge=1, le=10000)
    max_total_units: int = Field(ge=1, le=1_000_000_000)
    source_created_after: str = Field(min_length=1, max_length=100)
    expires_at: str = Field(min_length=1, max_length=100)


class AcceptancePolicy(Strict):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    purpose: Literal["shopify_source_order_acceptance/1"]
    tenant_id: str = Field(min_length=1, max_length=200)
    shop: str = Field(pattern=SHOP)
    query_digest: str = Field(pattern=HEX)
    issuer: str = Field(min_length=1, max_length=200)
    key_id: str = Field(min_length=1, max_length=200)
    public_key: str = Field(min_length=43, max_length=43)
    allowed_subjects: list[str] = Field(min_length=1, max_length=20)
    allowed_token_ids: list[str] = Field(min_length=1, max_length=20)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    max_order_amount: str = Field(pattern=r"^(0|[1-9][0-9]{0,17})(\.[0-9]{1,6})?$")
    max_order_units: int = Field(ge=1, le=1_000_000_000)
    max_effects: int = Field(ge=1, le=101)
    review_max_age_seconds: int = Field(ge=1, le=300)
    mandates: list[StandingMandate] = Field(default_factory=list, max_length=20)
    expires_at: str = Field(min_length=1, max_length=100)


class AcceptanceHeader(Strict):
    alg: Literal["EdDSA"]
    typ: Literal["tuesday-shopify-order-acceptance+jwt"]
    kid: str = Field(min_length=1, max_length=200)


class AcceptanceClaims(Strict):
    iss: str = Field(min_length=1, max_length=200)
    aud: Literal["reality:shopify-source-order-acceptance/1"]
    sub: str = Field(min_length=1, max_length=200)
    iat: int
    exp: int
    jti: str = Field(min_length=36, max_length=36)
    purpose: Literal["shopify_source_order_acceptance/1"]
    tenant_id: str = Field(min_length=1, max_length=200)
    proposal_id: str = Field(min_length=1, max_length=200)
    review_digest: str = Field(pattern=HEX)
    source_binding_digest: str = Field(pattern=HEX)
    mapping_bundle_digest: str = Field(pattern=HEX)
    plan_digest: str = Field(pattern=HEX)
    authorization_kind: Literal["human", "standing"]
    mandate_id: str | None = Field(default=None, min_length=1, max_length=200)
    mandate_revision: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def exact_authorization_kind(self):
        if self.authorization_kind == "human":
            if self.mandate_id is not None or self.mandate_revision is not None:
                raise ValueError("human_proof_cannot_claim_mandate")
        elif self.mandate_id is None or self.mandate_revision is None:
            raise ValueError("exact_standing_mandate_required")
        return self


def verify_acceptance_proof(
    value: str, policy: AcceptancePolicy, expected: dict, now: datetime
) -> AcceptanceClaims:
    parts = value.split(".")
    if len(parts) != 3 or len(value) > 16384:
        raise ValueError("invalid_compact_proof")
    header = AcceptanceHeader.model_validate(_strict_json(decode64(parts[0])))
    claims = AcceptanceClaims.model_validate(_strict_json(decode64(parts[1])))
    nonce(claims.jti)
    key = decode64(policy.public_key)
    if len(key) != 32 or header.kid != policy.key_id:
        raise ValueError("wrong_issuer_key")
    Ed25519PublicKey.from_public_bytes(key).verify(
        decode64(parts[2]), f"{parts[0]}.{parts[1]}".encode("ascii")
    )
    at = int(now.timestamp())
    if (
        claims.iss != policy.issuer
        or claims.sub not in policy.allowed_subjects
        or claims.tenant_id != policy.tenant_id
        or claims.iat > at + 30
        or claims.exp <= at
        or claims.exp <= claims.iat
        or claims.exp > claims.iat + 300
        or instant(policy.expires_at) <= now
    ):
        raise ValueError("approval_binding_or_expiry_changed")
    if any(getattr(claims, field) != wanted for field, wanted in expected.items()):
        raise ValueError("exact_order_review_required")
    if claims.authorization_kind == "standing":
        matches = [
            entry
            for entry in policy.mandates
            if entry.id == claims.mandate_id
            and entry.revision == claims.mandate_revision
            and entry.subject == claims.sub
            and instant(entry.expires_at) > now
        ]
        if len(matches) != 1:
            raise ValueError("standing_mandate_unavailable")
    return claims


class StoredAcceptanceProposal(Strict):
    purpose: Literal["shopify_source_order_acceptance/1"]
    request: AcceptancePrepareInput
    source_binding: SourceBinding
    buyer_mapping: VerifiedMapping
    mapping_bundle: dict
    plan: PreparedIntake
    readiness: dict
    policy_digest: str = Field(pattern=HEX)
    observed_at: str = Field(min_length=1, max_length=100)
    submitter_token_id: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def exact_closed_successor(self):
        if self.plan.mapping.get("origin") != ACTION_TYPE or self.plan.mapping.get(
            "bundle_digest"
        ) != content_digest(self.mapping_bundle):
            raise ValueError("successor_origin_or_bundle_changed")
        if (
            self.mapping_bundle.get("state") != "proposed"
            or self.plan.tenant_id != self.source_binding.tenant_id
            or self.plan.source_record_id != self.source_binding.source_record_id
            or self.plan.source_hash != self.source_binding.source_hash
            or self.plan.source_version != self.source_binding.source_version
            or self.plan.import_job_id != self.source_binding.import_job_id
        ):
            raise ValueError("successor_source_changed")
        if (
            sum(effect.operation == "document" for effect in self.plan.effects) != 1
            or self.plan.effects[0].operation != "document"
            or any(
                effect.operation not in {"document", "commitment"}
                for effect in self.plan.effects
            )
        ):
            raise ValueError("closed_order_effects_required")
        if (
            self.readiness.get("profile") != PROFILE
            or self.readiness.get("delivery_terms") != "not_promised"
        ):
            raise ValueError("successor_terms_changed")
        return self


class BuyerMappingBasis(Strict):
    mapping_state: Literal["applied_to_source"]
    customer: dict
    approval_source_record_id: str = Field(min_length=1, max_length=200)
    review_id: str = Field(min_length=1, max_length=200)
    review_digest: str = Field(pattern=HEX)


class AcceptanceReviewResult(Strict):
    purpose: Literal["shopify_source_order_acceptance/1"]
    proposal_id: str = Field(min_length=1, max_length=200)
    status: Literal["proposed", "stale", "rejected", "executed"]
    request_id: str = Field(min_length=36, max_length=36)
    review_digest: str = Field(pattern=HEX)
    source_binding: SourceBinding
    buyer_mapping: BuyerMappingBasis
    buyer_mapping_scope: Literal["existing_buyer_mapping_evidence_at_order_review"]
    evidence_observed_at: str = Field(min_length=1, max_length=100)
    readiness_evidence_scope: Literal["frozen_at_order_review"]
    currentness: Literal[
        "historical_accepted_only", "changed", "unchanged_since_review"
    ]
    mapping_bundle: dict
    plan_digest: str = Field(pattern=HEX)
    review_projection: PreparedIntake
    readiness: dict
    holds: list[str] = Field(max_length=500)
    eligible_for_exact_authorization: bool
    generic_confirmation_allowed: Literal[False]
    business_effects_accepted: bool
    original_source_unchanged: Literal[True]
    import_job_input_unchanged: Literal[True]

    @model_validator(mode="after")
    def exact_outcome(self):
        if (
            self.business_effects_accepted != (self.status == "executed")
            or self.eligible_for_exact_authorization
            and (
                self.holds
                or self.status != "proposed"
                or self.currentness != "unchanged_since_review"
            )
        ):
            raise ValueError("review_outcome_contradiction")
        if self.status == "executed" and self.currentness != "historical_accepted_only":
            raise ValueError("historical_outcome_is_not_new_readiness")
        return self


class CanonicalOrderRecord(Strict):
    type: Literal["document", "document_line", "commitment"]
    id: str = Field(min_length=1, max_length=200)


class ApprovalIdentity(Strict):
    issuer: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=200)
    jti: str = Field(min_length=36, max_length=36)
    proof_digest: str = Field(pattern=HEX)
    authorization_kind: Literal["human", "standing"]
    mandate_id: str | None
    mandate_revision: int | None


class AcceptanceReceipt(Strict):
    purpose: Literal["shopify_source_order_acceptance/1"]
    proposal_id: str = Field(min_length=1, max_length=200)
    review_digest: str = Field(pattern=HEX)
    source_binding: SourceBinding
    mapping_bundle_digest: str = Field(pattern=HEX)
    plan_digest: str = Field(pattern=HEX)
    verification: Literal["applied"]
    authorized_at: str = Field(min_length=1, max_length=100)
    records: list[CanonicalOrderRecord] = Field(min_length=1, max_length=201)
    approval_source_record_id: str = Field(min_length=1, max_length=200)
    approval_source_hash: str = Field(pattern=HEX)
    source_stated_order_amount: str = Field(min_length=1, max_length=60)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    admitted_source_units: int = Field(ge=1, le=1_000_000_000)
    approval: ApprovalIdentity
    original_source_unchanged: Literal[True]
    import_job_input_unchanged: Literal[True]
    payment_recorded: Literal[False]
    stock_moved: Literal[False]
    fulfillment_dispatched: Literal[False]


class AcceptanceStatusResult(Strict):
    purpose: Literal["shopify_source_order_acceptance/1"]
    proposal_id: str = Field(min_length=1, max_length=200)
    status: Literal["proposed", "rejected", "executed"]
    receipt: AcceptanceReceipt | None
    dispatch_performed: Literal[False]

    @model_validator(mode="after")
    def exact_receipt(self):
        if (
            (self.status == "executed") != (self.receipt is not None)
            or self.receipt is not None
            and self.receipt.proposal_id != self.proposal_id
        ):
            raise ValueError("status_receipt_contradiction")
        return self
