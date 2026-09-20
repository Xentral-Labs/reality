"""Received shares and tax decisions cannot manufacture acquisition amounts."""

from decimal import Decimal

import pytest

from reality.domain.costing import CostPart, contribution, validate_shares


@pytest.mark.parametrize("credit", ["50", "-50"])
def test_source_sign_does_not_reverse_a_purchase_reduction(credit):
    part = CostPart(
        movement_id="receipt",
        category="purchase_reduction",
        source_share=credit,
        cost_effect=-1,
    )
    assert contribution(part) == Decimal(-50)
    validate_shares([part], Decimal(credit), Decimal(0))


def test_bucket_conservation_cannot_hide_overassignment_with_opposite_signs():
    parts = [
        CostPart(
            movement_id="one", category="goods", source_share="110", cost_effect=1
        ),
        CostPart(
            movement_id="two", category="goods", source_share="-10", cost_effect=1
        ),
    ]
    with pytest.raises(ValueError):
        validate_shares(parts, Decimal(100), Decimal(0))


def test_tax_bucket_and_precision_are_independent():
    part = CostPart(
        movement_id="receipt",
        category="nonrecoverable_tax",
        amount_bucket="nonrecoverable_tax",
        source_share="19",
        cost_effect=1,
    )
    with pytest.raises(ValueError):
        validate_shares([part], Decimal(100), Decimal(10))
    with pytest.raises(ValueError):
        CostPart(
            movement_id="receipt",
            category="goods",
            source_share="1.00001",
            cost_effect=1,
        )
    with pytest.raises(ValueError):
        CostPart(
            movement_id="receipt", category="goods", source_share="NaN", cost_effect=1
        )


def test_duplicate_or_semantically_reversed_parts_refuse():
    part = CostPart(
        movement_id="receipt", category="goods", source_share="50", cost_effect=1
    )
    with pytest.raises(ValueError):
        validate_shares([part, part], Decimal(100), Decimal(0))
    with pytest.raises(ValueError):
        CostPart(
            movement_id="receipt",
            category="purchase_reduction",
            source_share="50",
            cost_effect=1,
        )


def test_credit_tax_cannot_have_the_opposite_economic_direction():
    reduction = CostPart(
        movement_id="receipt",
        category="purchase_reduction",
        source_share="50",
        cost_effect=-1,
    )
    wrong_tax = CostPart(
        movement_id="receipt",
        category="nonrecoverable_tax",
        source_share="9.5",
        cost_effect=1,
        amount_bucket="nonrecoverable_tax",
    )
    with pytest.raises(ValueError, match="direction"):
        validate_shares([reduction, wrong_tax], Decimal(50), Decimal("9.5"))
    tax = wrong_tax.model_copy(update={"cost_effect": -1})
    validate_shares([reduction, tax], Decimal(50), Decimal("9.5"))
    assert contribution(reduction) + contribution(tax) == Decimal("-59.5")
