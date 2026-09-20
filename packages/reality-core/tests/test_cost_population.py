"""Company population closure distinguishes missing work from unknown money."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from reality.domain.cost_population import (
    ContributionExpectation,
    ContributionObservation,
    EvaluatedPopulation,
    ExpectedPopulation,
    InventoryExpectation,
    InventoryObservation,
    PopulationBasis,
    PopulationRefusal,
    close_population,
)

HASH = "a" * 64
BASIS = PopulationBasis(
    tenant_id="tenant",
    effective_at=datetime(2026, 8, 31, tzinfo=UTC),
    knowledge_at=datetime(2026, 9, 1, tzinfo=UTC),
    event_sequence=50,
)


def inputs():
    expected = ExpectedPopulation(
        basis=BASIS,
        inventory=tuple(
            InventoryExpectation(item_id=key, input_fingerprint=HASH)
            for key in ("item-a", "item-b")
        ),
        contribution=tuple(
            ContributionExpectation(document_line_id=key, input_fingerprint=HASH)
            for key in ("line-a", "line-b")
        ),
    )
    evaluated = EvaluatedPopulation(
        basis=BASIS,
        inventory=(
            InventoryObservation(
                item_id="item-a",
                input_fingerprint=HASH,
                acquisition="known",
                carrying="unknown",
            ),
            InventoryObservation(
                item_id="item-b",
                input_fingerprint=HASH,
                acquisition="known",
                carrying="known",
            ),
        ),
        contribution=(
            ContributionObservation(
                document_line_id="line-a",
                input_fingerprint=HASH,
                db1="known",
                db2="known",
            ),
            ContributionObservation(
                document_line_id="line-b",
                input_fingerprint=HASH,
                db1="known",
                db2="unknown",
            ),
        ),
    )
    return expected, evaluated


def test_exact_population_can_close_with_independent_financial_gaps():
    expected, evaluated = inputs()
    result = close_population("tenant", expected, evaluated)
    assert result.inventory_rows == result.contribution_rows == 2
    assert result.acquisition.state == result.db1.state == "complete"
    assert result.carrying.state == result.db2.state == "partial"
    assert result.db2.expected == 2 and result.db2.covered == result.db2.unknown == 1
    assert result.has_financial_gaps
    with pytest.raises(FrozenInstanceError):
        result.inventory_rows = 0
    assert (
        close_population(
            "tenant",
            expected,
            evaluated.model_copy(
                update={
                    "inventory": evaluated.inventory[::-1],
                    "contribution": evaluated.contribution[::-1],
                }
            ),
        )
        == result
    )


@pytest.mark.parametrize(
    "family,key", [("inventory", "item_id"), ("contribution", "document_line_id")]
)
@pytest.mark.parametrize(
    "mutation,code",
    [
        ("missing", "cost_population_missing"),
        ("extra", "cost_population_unexpected"),
        ("replace", "cost_population_unexpected"),
        ("duplicate", "cost_population_duplicate"),
        ("stale", "cost_population_input_mismatch"),
    ],
)
def test_population_counts_never_replace_exact_membership(family, key, mutation, code):
    expected, evaluated = inputs()
    rows = getattr(evaluated, family)
    changed = {
        "missing": rows[:1],
        "extra": rows + (rows[0].model_copy(update={key: "unexpected"}),),
        "replace": (rows[0], rows[1].model_copy(update={key: "unexpected"})),
        "duplicate": (rows[0], rows[0]),
        "stale": (rows[0], rows[1].model_copy(update={"input_fingerprint": "b" * 64})),
    }[mutation]
    with pytest.raises(PopulationRefusal) as failure:
        close_population(
            "tenant", expected, evaluated.model_copy(update={family: changed})
        )
    assert failure.value.code == code


@pytest.mark.parametrize("family", ["inventory", "contribution"])
def test_duplicate_expectations_are_not_silently_collapsed(family):
    expected, evaluated = inputs()
    rows = getattr(expected, family)
    with pytest.raises(PopulationRefusal, match="cost_population_duplicate"):
        close_population(
            "tenant",
            expected.model_copy(update={family: (rows[0], rows[0])}),
            evaluated,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("tenant_id", "foreign"),
        ("effective_at", BASIS.effective_at + timedelta(days=1)),
        ("knowledge_at", BASIS.knowledge_at + timedelta(seconds=1)),
        ("event_sequence", 51),
    ],
)
def test_mixed_context_refuses_without_disclosing_ids(field, value):
    expected, evaluated = inputs()
    with pytest.raises(PopulationRefusal) as failure:
        close_population(
            "tenant",
            expected,
            evaluated.model_copy(
                update={"basis": BASIS.model_copy(update={field: value})}
            ),
        )
    assert failure.value.code == "cost_population_context_mismatch"
    assert "foreign" not in str(failure.value)
    with pytest.raises(PopulationRefusal, match="cost_population_context_mismatch"):
        close_population("foreign", expected, evaluated)


def test_empty_sealed_population_is_not_financial_zero():
    result = close_population(
        "tenant", ExpectedPopulation(basis=BASIS), EvaluatedPopulation(basis=BASIS)
    )
    assert result.inventory_rows == result.contribution_rows == 0
    assert not result.has_financial_gaps
    for coverage in (result.acquisition, result.carrying, result.db1, result.db2):
        assert coverage.state == "empty"
        assert coverage.expected == coverage.covered == coverage.unknown == 0


def test_explicit_unknown_observations_still_count_as_evaluated():
    expected, evaluated = inputs()
    evaluated = evaluated.model_copy(
        update={
            "inventory": tuple(
                row.model_copy(update={"acquisition": "unknown", "carrying": "unknown"})
                for row in evaluated.inventory
            ),
            "contribution": tuple(
                row.model_copy(update={"db1": "unknown", "db2": "unknown"})
                for row in evaluated.contribution
            ),
        }
    )
    result = close_population("tenant", expected, evaluated)
    assert result.inventory_rows == result.contribution_rows == 2
    assert result.acquisition.covered == result.db1.covered == result.db2.covered == 0
    assert result.db2.unknown == 2 and result.db2.state == "partial"


@pytest.mark.parametrize(
    "changes",
    [
        {"item_id": " "},
        {"input_fingerprint": "a" * 63},
        {"input_fingerprint": "z" * 64},
    ],
)
def test_invalid_expected_identity_or_fingerprint_is_rejected(changes):
    with pytest.raises(ValidationError):
        InventoryExpectation.model_validate(
            {"item_id": "item", "input_fingerprint": HASH, **changes}
        )


def test_financial_support_dependencies_are_strict():
    with pytest.raises(ValidationError):
        ContributionObservation(
            document_line_id="line", input_fingerprint=HASH, db1="unknown", db2="known"
        )
    with pytest.raises(ValidationError):
        InventoryObservation(
            item_id="item",
            input_fingerprint=HASH,
            acquisition="unknown",
            carrying="known",
        )
    with pytest.raises(ValidationError):
        PopulationBasis.model_validate({**BASIS.model_dump(), "event_sequence": True})
    with pytest.raises(ValidationError):
        PopulationBasis.model_validate(
            {**BASIS.model_dump(), "inventory_algorithm": "unreviewed-v2"}
        )


def test_large_population_closes_without_permutation_or_count_shortcuts():
    expected = ExpectedPopulation(
        basis=BASIS,
        inventory=tuple(
            InventoryExpectation(item_id=f"opaque-item-{n}", input_fingerprint=HASH)
            for n in range(10_000)
        ),
        contribution=tuple(
            ContributionExpectation(
                document_line_id=f"opaque-line-{n}", input_fingerprint=HASH
            )
            for n in range(100_000)
        ),
    )
    evaluated = EvaluatedPopulation(
        basis=BASIS,
        inventory=tuple(
            InventoryObservation(
                **row.model_dump(), acquisition="known", carrying="unknown"
            )
            for row in expected.inventory
        ),
        contribution=tuple(
            ContributionObservation(
                **row.model_dump(),
                db1="known",
                db2="unknown" if index % 10 == 0 else "known",
            )
            for index, row in enumerate(expected.contribution)
        ),
    )
    result = close_population("tenant", expected, evaluated)
    assert result.inventory_rows == 10_000 and result.contribution_rows == 100_000
    assert result.db1.covered == 100_000 and result.db2.covered == 90_000


def test_typed_families_do_not_collide_on_the_same_opaque_identity():
    expected = ExpectedPopulation(
        basis=BASIS,
        inventory=(InventoryExpectation(item_id="same", input_fingerprint=HASH),),
        contribution=(
            ContributionExpectation(document_line_id="same", input_fingerprint=HASH),
        ),
    )
    evaluated = EvaluatedPopulation(
        basis=BASIS,
        inventory=(
            InventoryObservation(
                item_id="same",
                input_fingerprint=HASH,
                acquisition="known",
                carrying="known",
            ),
        ),
        contribution=(
            ContributionObservation(
                document_line_id="same",
                input_fingerprint=HASH,
                db1="known",
                db2="known",
            ),
        ),
    )
    result = close_population("tenant", expected, evaluated)
    assert result.inventory_rows == result.contribution_rows == 1
    assert not result.has_financial_gaps
    assert all(
        part.state == "complete"
        for part in (result.acquisition, result.carrying, result.db1, result.db2)
    )


def test_population_basis_normalizes_utc_and_rejects_unproven_modes():
    from datetime import timezone

    assert (
        PopulationBasis.model_validate(
            {
                **BASIS.model_dump(),
                "effective_at": BASIS.effective_at.astimezone(
                    timezone(timedelta(hours=2))
                ),
            }
        )
        == BASIS
    )
    with pytest.raises(ValidationError):
        PopulationBasis.model_validate(
            {**BASIS.model_dump(), "knowledge_at": "2026-09-01T00:00:00"}
        )
    with pytest.raises(ValidationError):
        ContributionObservation(
            document_line_id="line",
            input_fingerprint=HASH,
            db1="estimated",
            db2="unknown",
        )
    with pytest.raises(ValidationError):
        PopulationBasis.model_validate(
            {**BASIS.model_dump(), "contribution_algorithm": "commercial-v2"}
        )
