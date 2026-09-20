"""Pure carrying-value reconciliation over explicit source-backed assessments."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

AssessmentKind = Literal["write_down", "recovery"]
MONEY = Decimal("0.0001")
UNIT = Decimal("0.000001")


class CarryingValueRefusal(ValueError):
    """Stable refusal for an unsupported or contradictory assessment."""


@dataclass(frozen=True)
class AssessmentPart:
    inventory_member_id: str
    quantity: Decimal
    acquisition_value: Decimal
    assessed_value: Decimal


@dataclass(frozen=True)
class AssessedPart:
    inventory_member_id: str
    quantity: Decimal
    acquisition_value: Decimal
    assessed_value: Decimal
    adjustment: Decimal
    unit_display: Decimal


@dataclass(frozen=True)
class CarryingValueResult:
    acquisition_value: Decimal
    carrying_value: Decimal
    adjustment: Decimal
    parts: tuple[AssessedPart, ...]


def _scale(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def _validate_input(part: AssessmentPart) -> None:
    if not part.inventory_member_id:
        raise CarryingValueRefusal("assessment_member_required")
    if not all(value.is_finite() for value in (part.quantity, part.acquisition_value, part.assessed_value)):
        raise CarryingValueRefusal("non_finite_assessment_value")
    if part.quantity <= 0:
        raise CarryingValueRefusal("non_positive_assessment_quantity")
    if part.acquisition_value < 0:
        raise CarryingValueRefusal("negative_acquisition_value")
    if part.assessed_value < 0:
        raise CarryingValueRefusal("negative_assessed_value")
    if any(_scale(value) > 4 for value in (part.quantity, part.acquisition_value, part.assessed_value)):
        raise CarryingValueRefusal("unsupported_assessment_precision")


def _scope(parts: Sequence[AssessmentPart]) -> tuple[tuple[str, Decimal, Decimal], ...]:
    return tuple(
        sorted(
            (
                part.inventory_member_id,
                part.quantity.quantize(MONEY),
                part.acquisition_value.quantize(MONEY),
            )
            for part in parts
        )
    )


def reconcile_assessment(
    kind: AssessmentKind,
    parts: Sequence[AssessmentPart],
    *,
    previous: Sequence[AssessmentPart] | None = None,
) -> CarryingValueResult:
    """Reconcile stated part totals without inventing value or changing acquisition cost."""
    if kind not in {"write_down", "recovery"}:
        raise CarryingValueRefusal("unsupported_assessment_kind")
    if not parts:
        raise CarryingValueRefusal("assessment_parts_required")
    for part in parts:
        _validate_input(part)
    identities = [part.inventory_member_id for part in parts]
    if len(set(identities)) != len(identities):
        raise CarryingValueRefusal("duplicate_assessment_member")

    previous_by_member: dict[str, AssessmentPart] = {}
    if kind == "recovery":
        if not previous:
            raise CarryingValueRefusal("recovery_predecessor_required")
        for prior in previous:
            _validate_input(prior)
        if _scope(parts) != _scope(previous):
            raise CarryingValueRefusal("recovery_scope_mismatch")
        previous_by_member = {part.inventory_member_id: part for part in previous}
    elif previous is not None:
        raise CarryingValueRefusal("write_down_predecessor_forbidden")

    reconciled = []
    for part in parts:
        acquisition = part.acquisition_value.quantize(MONEY)
        assessed = part.assessed_value.quantize(MONEY)
        if kind == "write_down" and assessed >= acquisition:
            raise CarryingValueRefusal("write_down_not_below_acquisition")
        if kind == "recovery":
            prior = previous_by_member[part.inventory_member_id]
            if assessed < prior.assessed_value.quantize(MONEY):
                raise CarryingValueRefusal("recovery_below_previous_value")
            if assessed > acquisition:
                raise CarryingValueRefusal("recovery_above_acquisition_ceiling")
        reconciled.append(
            AssessedPart(
                inventory_member_id=part.inventory_member_id,
                quantity=part.quantity.quantize(MONEY),
                acquisition_value=acquisition,
                assessed_value=assessed,
                adjustment=(assessed - acquisition).quantize(MONEY),
                unit_display=(assessed / part.quantity).quantize(
                    UNIT, rounding=ROUND_HALF_EVEN
                ),
            )
        )

    acquisition_total = sum(
        (part.acquisition_value for part in reconciled), Decimal(0)
    ).quantize(MONEY)
    carrying_total = sum(
        (part.assessed_value for part in reconciled), Decimal(0)
    ).quantize(MONEY)
    return CarryingValueResult(
        acquisition_value=acquisition_total,
        carrying_value=carrying_total,
        adjustment=(carrying_total - acquisition_total).quantize(MONEY),
        parts=tuple(reconciled),
    )
