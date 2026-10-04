"""Closed delegated-review evidence and finite mandate scope (spec 355)."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal, get_args

from pydantic import Field, field_validator, model_validator

from reality.domain.intake import Effect, IntakeModel

PROFILES = frozenset(
    {
        "shopify.order",
        "demo.order",
        "shopify.order_change",
        "shopify.refund",
        "item_csv.v1",
        "customer_payment.v1",
        "supplier_payment.v1",
        "sales_invoice.v1",
        "artifact:item.v1",
        "artifact:party.v1",
        "artifact:location.v1",
        "artifact:sales_order.v1",
        "artifact:inventory_snapshot.v1",
        "artifact:external_stock.v1",
        "artifact:bank_statement.v1",
    }
)
MONEY_EFFECTS = frozenset(
    {
        "document",
        "customer_payment",
        "supplier_payment",
        "invoice_post",
        "source_document",
        "payment_allocation",
    }
)


class AmountRule(IntakeModel):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    max_amount_per_unit: str = Field(min_length=1, max_length=40)
    max_amount_per_day: str = Field(min_length=1, max_length=40)

    @field_validator("max_amount_per_unit", "max_amount_per_day")
    @classmethod
    def finite_positive(cls, value):
        try:
            amount = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(
                "Amount limits must be finite positive decimals."
            ) from error
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Amount limits must be finite positive decimals.")
        return value


class MandateScope(IntakeModel):
    schema_version: Literal[1] = 1
    source_system_id: str = Field(min_length=1, max_length=128)
    capability_ids: tuple[str, ...] = Field(min_length=1, max_length=50)
    profiles: tuple[str, ...] = Field(min_length=1, max_length=15)
    effects: tuple[str, ...] = Field(min_length=1, max_length=20)
    max_rows_per_unit: int = Field(ge=1, le=500, strict=True)
    max_units_per_day: int = Field(ge=1, le=100000, strict=True)
    amount_rule: AmountRule | None = None

    @model_validator(mode="after")
    def closed_scope(self):
        for values in (self.capability_ids, self.profiles, self.effects):
            if len(set(values)) != len(values):
                raise ValueError("Mandate selections must contain unique values.")
        if not set(self.profiles) <= PROFILES:
            raise ValueError("Unknown mandate profile.")
        if not set(self.effects) <= set(
            get_args(Effect.model_fields["operation"].annotation)
        ):
            raise ValueError("Unknown mandate effect.")
        if set(self.effects) & MONEY_EFFECTS and self.amount_rule is None:
            raise ValueError(
                "Commercial and financial effects require explicit stated-amount limits."
            )
        return self


class MandateGrant(IntakeModel):
    agent_token_id: str = Field(min_length=1, max_length=128)
    scope: MandateScope
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def aware_expiry(cls, value):
        if value.tzinfo is None:
            raise ValueError("Expiry must name a time zone.")
        return value


class ReviewCheck(IntakeModel):
    code: Literal[
        "exact_source",
        "exact_plan",
        "full_source_coverage",
        "closed_effects",
        "current_state",
        "uncertainties",
    ]
    result: Literal["pass", "fail", "uncertain"]


class AgentReviewEvidence(IntakeModel):
    schema_version: Literal[1] = 1
    mandate_id: str = Field(min_length=1, max_length=128)
    revision: int = Field(ge=1, strict=True)
    proposal_id: str = Field(min_length=1, max_length=128)
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_references: tuple[str, ...] = Field(min_length=1, max_length=1002)
    checks: tuple[ReviewCheck, ...] = Field(min_length=6, max_length=6)
    verdict: Literal["approve", "reject", "uncertain"]
    reasons: tuple[str, ...] = Field(min_length=1, max_length=25)

    @model_validator(mode="after")
    def exact_evidence(self):
        if len(set(self.reviewed_references)) != len(self.reviewed_references):
            raise ValueError("Coverage references must be unique.")
        if len({check.code for check in self.checks}) != 6:
            raise ValueError("Every deterministic check is required exactly once.")
        if any(not reason or len(reason) > 500 for reason in self.reasons):
            raise ValueError("Reasons must be bounded non-empty strings.")
        return self


class AgentBatchReviewEvidence(IntakeModel):
    schema_version: Literal[1] = 1
    batch_id: str = Field(min_length=1, max_length=128)
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_revision: int = Field(ge=1, strict=True)
    reviews: tuple[AgentReviewEvidence, ...] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def exact_unique_mandate(self):
        if len({review.proposal_id for review in self.reviews}) != len(self.reviews):
            raise ValueError("Every selected child requires one unique verdict.")
        if len({(review.mandate_id, review.revision) for review in self.reviews}) != 1:
            raise ValueError("One fixed batch requires one exact mandate revision.")
        return self
