"""Spec 234 T086: carrying value stays separate from acquisition cost authority."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from reality.domain.carrying_value import (
    AssessmentPart,
    CarryingValueRefusal,
    reconcile_assessment,
)
from reality.domain.costing import ValuationAssessment

D = Decimal


def part(
    member_id: str,
    quantity: str,
    acquisition_value: str,
    assessed_value: str,
) -> AssessmentPart:
    return AssessmentPart(
        inventory_member_id=member_id,
        quantity=D(quantity),
        acquisition_value=D(acquisition_value),
        assessed_value=D(assessed_value),
    )


def test_write_down_reconciles_source_stated_total_without_changing_acquisition():
    result = reconcile_assessment(
        "write_down",
        [part("member-a", "20", "210", "150")],
    )
    assert result.acquisition_value == D("210.0000")
    assert result.carrying_value == D("150.0000")
    assert result.adjustment == D("-60.0000")
    assert result.parts[0].unit_display == D("7.500000")


def test_partial_scope_conserves_only_the_assessed_quantity():
    result = reconcile_assessment(
        "write_down",
        [
            part("member-a", "10", "105", "80"),
            part("member-b", "5", "70", "50"),
        ],
    )
    assert result.acquisition_value == D("175.0000")
    assert result.carrying_value == D("130.0000")
    assert result.adjustment == D("-45.0000")


def test_recovery_requires_exact_predecessor_scope_and_respects_cost_ceiling():
    previous = [part("member-a", "20", "210", "150")]
    result = reconcile_assessment(
        "recovery",
        [part("member-a", "20", "210", "190")],
        previous=previous,
    )
    assert result.carrying_value == D("190.0000")
    assert result.adjustment == D("-20.0000")

    with pytest.raises(CarryingValueRefusal, match="recovery_above_acquisition_ceiling"):
        reconcile_assessment(
            "recovery",
            [part("member-a", "20", "210", "211")],
            previous=previous,
        )
    with pytest.raises(CarryingValueRefusal, match="recovery_scope_mismatch"):
        reconcile_assessment(
            "recovery",
            [part("member-a", "19", "199.5", "180")],
            previous=previous,
        )


@pytest.mark.parametrize(
    ("kind", "parts", "previous", "reason"),
    [
        (
            "write_down",
            [part("member-a", "1", "10", "10")],
            None,
            "write_down_not_below_acquisition",
        ),
        (
            "write_down",
            [part("member-a", "1", "10", "-1")],
            None,
            "negative_assessed_value",
        ),
        (
            "recovery",
            [part("member-a", "1", "10", "7")],
            [part("member-a", "1", "10", "8")],
            "recovery_below_previous_value",
        ),
        (
            "write_down",
            [part("member-a", "1", "10", "8"), part("member-a", "1", "10", "7")],
            None,
            "duplicate_assessment_member",
        ),
    ],
)
def test_invalid_assessment_directions_and_overlap_refuse(kind, parts, previous, reason):
    with pytest.raises(CarryingValueRefusal, match=reason):
        reconcile_assessment(kind, parts, previous=previous)


def assessment_request(**changes):
    value = {
        "operation": "valuation_assessment",
        "expected_event_sequence": 12,
        "reason": "Source-backed lower-value review",
        "inventory_review_id": "review-a",
        "kind": "write_down",
        "effective_at": "2026-09-20T00:00:00+00:00",
        "parts": [
            {
                "inventory_member_id": "member-a",
                "evidence_source_record_id": "source-a",
                "quantity": "20",
                "assessed_value": "150",
                "currency": "EUR",
            }
        ],
    }
    value.update(changes)
    return value


def test_assessment_request_requires_exact_source_scope_and_recovery_predecessor():
    request = ValuationAssessment.model_validate(assessment_request())
    assert request.parts[0].assessed_value == D("150")
    assert request.supersedes_id is None

    with pytest.raises(ValidationError, match="recovery requires"):
        ValuationAssessment.model_validate(assessment_request(kind="recovery"))
    with pytest.raises(ValidationError, match="write-down cannot supersede"):
        ValuationAssessment.model_validate(
            assessment_request(supersedes_id="assessment-a")
        )
    with pytest.raises(ValidationError, match="Duplicate assessment member"):
        ValuationAssessment.model_validate(
            assessment_request(parts=assessment_request()["parts"] * 2)
        )
