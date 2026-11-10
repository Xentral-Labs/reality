"""Spec390: ephemeral exact-source diagnosis, never preparation or authority."""

from typing import Literal

from pydantic import Field, model_validator

from reality.domain.shopify_buyer_mapping import (
    GID,
    HEX,
    SHOP,
    Strict,
    canonical,
    digest,
    instant,
)

PURPOSE = "shopify_source_intake_preflight_only/1"
MAX_REPORT_BYTES = 24000
NOT_ASSESSED = [
    "upstream_freshness",
    "payment",
    "credit_exposure",
    "inventory",
    "settlement",
    "full_intake",
    "business_acceptance",
]


def semantic_digest(value: dict) -> str:
    """Sorted compact JSON, literal Unicode, SHA256 UTF-8; no normalization."""
    return digest(
        {
            key: entry
            for key, entry in value.items()
            if key not in {"observed_at", "output_digest"}
        }
    )


class PreflightInput(Strict):
    source_record_id: str = Field(min_length=1, max_length=200)
    import_job_id: str = Field(min_length=1, max_length=200)
    source_hash: str = Field(pattern=HEX)
    source_version: int = Field(gt=0)


class SourceBinding(PreflightInput):
    tenant_id: str = Field(min_length=1, max_length=200)
    external_id: str = Field(min_length=1, max_length=32)
    order_id: str = Field(pattern=GID)
    order_label: str = Field(min_length=1, max_length=500)
    shop: str = Field(pattern=SHOP)
    query_digest: str = Field(pattern=HEX)

    @model_validator(mode="after")
    def order_identity(self):
        if self.order_id != f"gid://shopify/Order/{self.external_id}":
            raise ValueError("order_identity_mismatch")
        return self


class Customer(Strict):
    party_id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=500)
    digest: str = Field(pattern=HEX)


class CurrentBasis(Strict):
    source_current: bool
    customer_current: bool


class VerifiedMapping(Strict):
    mapping_state: Literal["applied_to_source"]
    customer: Customer
    approval_source_record_id: str = Field(min_length=1, max_length=200)
    review_id: str = Field(min_length=1, max_length=200)
    review_digest: str = Field(pattern=HEX)
    current_basis: CurrentBasis
    remaining_review: Literal["full_intake_review_not_prepared"]


class BuyerCheck(Strict):
    status: Literal["missing", "verified", "stale"]
    mapping: VerifiedMapping | None

    @model_validator(mode="after")
    def status_matches(self):
        expected = (
            "missing"
            if self.mapping is None
            else (
                "verified"
                if self.mapping.current_basis.source_current
                and self.mapping.current_basis.customer_current
                else "stale"
            )
        )
        if self.status != expected:
            raise ValueError("buyer_status_mismatch")
        return self


class ReferenceCheck(Strict):
    status: Literal[
        "missing",
        "matched",
        "not_found",
        "inactive",
        "role_mismatch",
        "stock_not_allowed",
    ]
    record_id: str | None = Field(min_length=1, max_length=200)
    label: str | None = Field(min_length=1, max_length=500)
    digest: str | None = Field(pattern=HEX)

    @model_validator(mode="after")
    def match_identity(self):
        if self.status == "matched" and not all(
            [self.record_id, self.label, self.digest]
        ):
            raise ValueError("matched_reference_incomplete")
        if self.status == "missing" and any([self.record_id, self.label, self.digest]):
            raise ValueError("missing_reference_has_identity")
        if self.status == "not_found" and (
            self.label is not None or self.digest is not None
        ):
            raise ValueError("unknown_reference_disclosure")
        return self


class LineCheck(Strict):
    source_line_id: str = Field(min_length=1, max_length=100)
    sku: str = Field(max_length=200)
    quantity: str = Field(pattern=r"^[1-9][0-9]*$", max_length=60)
    item_status: Literal["missing_sku", "not_found", "inactive", "ambiguous", "matched"]
    item_id: str | None = Field(min_length=1, max_length=200)
    item_digest: str | None = Field(pattern=HEX)
    stock_unit: str | None = Field(min_length=1, max_length=100)
    source_unit: None
    unit_status: Literal["not_interpreted"]

    @model_validator(mode="after")
    def item_identity(self):
        values = [self.item_id, self.item_digest, self.stock_unit]
        if self.item_status == "matched" and not all(values):
            raise ValueError("matched_item_incomplete")
        if self.item_status != "matched" and any(value is not None for value in values):
            raise ValueError("unselected_item_has_identity")
        return self


class Interpretation(Strict):
    status: Literal["supported", "requires_review"]
    reason_codes: list[Literal["unsupported_selected_first_order"]] = Field(
        max_length=1
    )

    @model_validator(mode="after")
    def reason(self):
        if self.reason_codes != (
            [] if self.status == "supported" else ["unsupported_selected_first_order"]
        ):
            raise ValueError("support_reason_mismatch")
        return self


class Coverage(Strict):
    scope: Literal["retained_selected_entity"]
    line_count: int = Field(ge=0, le=500)
    returned_line_count: int = Field(ge=0, le=100)
    lines_complete: bool


class Financial(Strict):
    currency: str | None = Field(pattern=r"^[A-Z]{3}$")
    order_total: str | None = Field(max_length=60)
    line_totals: Literal["not_interpreted"]
    payment: Literal["not_assessed"]
    credit_exposure: Literal["not_assessed"]
    settlement: Literal["not_assessed"]


BlockerCode = Literal[
    "source_requires_review",
    "buyer_mapping_missing",
    "buyer_mapping_stale",
    "company_mapping_missing",
    "company_reference_unavailable",
    "location_mapping_missing",
    "location_reference_unavailable",
    "shipping_location_not_allowed",
    "sku_missing",
    "item_not_found",
    "item_inactive",
    "item_ambiguous",
    "unit_mapping_not_proved",
    "line_coverage_incomplete",
]


class Blocker(Strict):
    code: BlockerCode
    affected_line_count: int = Field(ge=0, le=500)


class ReviewIssue(Strict):
    code: Literal["line_totals_not_interpreted", "delivery_date_not_interpreted"]
    affected_line_count: int = Field(ge=0, le=500)


class PreflightReport(Strict):
    purpose: Literal["shopify_source_intake_preflight_only/1"]
    source_binding: SourceBinding
    observed_at: str = Field(min_length=1, max_length=100)
    output_digest: str = Field(pattern=HEX)
    buyer: BuyerCheck
    company: ReferenceCheck
    location: ReferenceCheck
    source_interpretation: Interpretation
    coverage: Coverage
    lines: list[LineCheck] = Field(max_length=100)
    financial: Financial
    blockers: list[Blocker] = Field(max_length=14)
    review_issues: list[ReviewIssue] = Field(max_length=2)
    not_assessed: list[str] = Field(min_length=7, max_length=7)
    preparation_performed: Literal[False]
    business_effects_accepted: Literal[False]
    original_source_unchanged: Literal[True]
    import_job_input_unchanged: Literal[True]

    @model_validator(mode="after")
    def semantic_consistency(self):
        instant(self.observed_at)
        if self.not_assessed != NOT_ASSESSED:
            raise ValueError("assessment_scope_changed")
        if len({line.source_line_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate_source_line")
        coverage = self.coverage
        supported = self.source_interpretation.status == "supported"
        if (
            coverage.returned_line_count != len(self.lines)
            or len(self.lines) > coverage.line_count
        ):
            raise ValueError("line_count_mismatch")
        if coverage.lines_complete != (
            supported and len(self.lines) == coverage.line_count
        ):
            raise ValueError("coverage_mismatch")
        if not supported and (
            self.lines
            or self.financial.currency is not None
            or self.financial.order_total is not None
        ):
            raise ValueError("unsupported_source_interpreted")
        for issues in [self.blockers, self.review_issues]:
            if len({issue.code for issue in issues}) != len(issues):
                raise ValueError("duplicate_issue")
            if any(issue.affected_line_count > coverage.line_count for issue in issues):
                raise ValueError("issue_count_mismatch")
        value = self.model_dump()
        if semantic_digest(value) != self.output_digest:
            raise ValueError("semantic_digest_mismatch")
        if len(canonical(value).encode("utf-8")) > MAX_REPORT_BYTES:
            raise ValueError("preflight_report_too_large")
        return self
