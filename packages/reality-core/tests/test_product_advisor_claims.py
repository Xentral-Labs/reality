import pytest
from pydantic import ValidationError
from reality.domain.product_advisor import (
    AdvisoryClaim,
    EvidenceSource,
    EvidenceUnit,
    validate_claim,
)


def test_public_claim_cannot_exceed_limited_evidence() -> None:
    source = EvidenceSource(
        id="source_journey_c07",
        kind="journey",
        title="Credit limit exceeded",
        visibility="public",
        authority="capability",
        public_url="https://docs.example/#C07",
        fingerprint="a" * 64,
    )
    evidence = EvidenceUnit(
        id="evidence_journey_c07",
        source_id=source.id,
        subject="credit limit",
        title=source.title,
        search_text="credit limit hold manual release",
        claim_text="The credit-limit exception and a manual release both work.",
        support="limited",
        limitations=("There is no automatic credit hold.",),
        references=("C07",),
        fingerprint="b" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_credit_hold",
        subject="credit limit",
        statement="Reality automatically holds orders above the credit limit.",
        support="proven",
        evidence_ids=(evidence.id,),
        workflow_role="native",
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "rejected"
    assert "support_ceiling" in result.reason_codes


def test_material_claim_needs_eligible_evidence() -> None:
    claim = AdvisoryClaim(
        id="claim_migration",
        subject="migration",
        statement="Reality supports complete SAP migration.",
        support="proven",
        evidence_ids=(),
        workflow_role="native",
    )

    result = validate_claim(claim, {})

    assert result.validation == "rejected"
    assert result.reason_codes == ("missing_evidence",)


def test_public_evidence_rejects_internal_location() -> None:
    with pytest.raises(ValidationError):
        EvidenceSource(
            id="source_private_spec",
            kind="public_contract",
            title="Private specification",
            visibility="public",
            authority="technical_contract",
            public_url="specs/291-reality-product-advisor/spec.md",
            fingerprint="c" * 64,
        )


def test_high_risk_end_to_end_wording_needs_exact_capability_evidence() -> None:
    evidence = EvidenceUnit(
        id="evidence_order_primitive",
        source_id="source_order",
        subject="orders",
        title="Order creation",
        search_text="create customer order",
        claim_text="Reality creates a customer order.",
        support="proven",
        fingerprint="d" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_complete_b2b",
        subject="B2B",
        statement="Reality provides complete end-to-end B2B automation.",
        support="proven",
        evidence_ids=(evidence.id,),
        workflow_role="native",
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "rejected"
    assert any(code.startswith("unqualified_") for code in result.reason_codes)


def test_high_risk_gap_wording_may_be_grounded_by_an_evidence_limitation() -> None:
    evidence = EvidenceUnit(
        id="evidence_partial_delivery_rule",
        source_id="source_partial_delivery_rule",
        subject="partial delivery",
        title="Partial delivery rule",
        search_text="partial delivery hold",
        claim_text="A hold can explain why reserved goods are not shipped.",
        support="limited",
        limitations=("There is no ship-complete rule.",),
        fingerprint="f" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_ship_complete_gap",
        subject="partial delivery",
        statement="Reality has no ship-complete rule.",
        support="limited",
        evidence_ids=(evidence.id,),
        limitations=evidence.limitations,
        workflow_role="gap",
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "accepted"


def test_negative_high_risk_wording_does_not_require_positive_capability_evidence() -> None:
    evidence = EvidenceUnit(
        id="evidence_no_automatic_rule",
        source_id="source_no_automatic_rule",
        subject="partial delivery",
        title="No automatic rule",
        search_text="partial delivery hold",
        claim_text="A hold can explain why reserved goods are not shipped.",
        support="limited",
        limitations=("There is no ship-complete rule.",),
        fingerprint="1" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_no_automatic_rule",
        subject="partial delivery",
        statement="There is no automatic ship-complete rule.",
        support="limited",
        evidence_ids=(evidence.id,),
        limitations=evidence.limitations,
        workflow_role="gap",
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "accepted"


def test_public_explanatory_contract_can_ground_a_product_explanation() -> None:
    evidence = EvidenceUnit(
        id="evidence_connector_contract",
        source_id="source_connector_contract",
        subject="connector contract",
        title="Connector contract",
        search_text="connector stores source payload losslessly",
        claim_text="A connector stores the source payload losslessly.",
        support="explanatory",
        fingerprint="2" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_connector_contract",
        subject="connector contract",
        statement="A connector stores the source payload losslessly.",
        support="proven",
        evidence_ids=(evidence.id,),
        workflow_role="native",
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "accepted"


def test_vocabulary_evidence_can_ground_exact_tool_existence() -> None:
    evidence = EvidenceUnit(
        id="evidence_supplier_invoice_tool",
        source_id="source_supplier_invoice_tool",
        subject="supplier invoice tool",
        title="Supplier invoice tool",
        search_text="record_supplier_invoice command",
        claim_text="record_supplier_invoice records a supplier invoice.",
        support="vocabulary_only",
        references=("record_supplier_invoice",),
        fingerprint="3" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_supplier_invoice_tool",
        subject="supplier invoice tool",
        statement="record_supplier_invoice records a supplier invoice.",
        support="proven",
        evidence_ids=(evidence.id,),
        workflow_role="confirmed_execution",
        tool_names=("record_supplier_invoice",),
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "accepted"


def test_agent_proposal_cannot_be_presented_as_confirmed_execution() -> None:
    evidence = EvidenceUnit(
        id="evidence_credit_proposal",
        source_id="source_credit",
        subject="credit control",
        title="Credit review proposal",
        search_text="agent prepares a proposal requiring confirmation",
        claim_text="The agent can prepare a credit-review proposal.",
        support="proven",
        fingerprint="e" * 64,
    )
    claim = AdvisoryClaim(
        id="claim_credit_execution",
        subject="credit control",
        statement="Reality executes the credit release.",
        support="proven",
        evidence_ids=(evidence.id,),
        workflow_role="confirmed_execution",
    )

    result = validate_claim(claim, {evidence.id: evidence})

    assert result.validation == "rejected"
    assert result.reason_codes == ("proposal_is_not_execution",)


@pytest.mark.parametrize(
    "role",
    ["native", "agent_proposal", "confirmed_execution", "manual", "workaround", "gap"],
)
def test_advisory_claim_supports_every_reviewed_workflow_role(role: str) -> None:
    claim = AdvisoryClaim(
        id=f"claim_{role}",
        subject="workflow",
        statement="A reviewed workflow classification.",
        support="not_established",
        evidence_ids=(),
        workflow_role=role,
    )

    assert claim.workflow_role == role
