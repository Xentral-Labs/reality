"""Company publication binds exact financial input membership before pointer checks."""

import pytest
from pydantic import ValidationError

from reality.domain.cost_generation import (
    CompanyGenerationBasis,
    Completion,
    Generation,
    PublicationRefusal,
    population_fingerprint,
    publication_decision,
)
from reality.domain.cost_population import (
    EvaluatedPopulation,
    ExpectedPopulation,
    PopulationBasis,
)


def population():
    basis = PopulationBasis(
        tenant_id="tenant",
        effective_at="2026-09-01T00:00:00Z",
        knowledge_at="2026-09-19T00:00:00Z",
        event_sequence=20,
    )
    expected = ExpectedPopulation(
        basis=basis,
        inventory=(
            {"item_id": "item-a", "input_fingerprint": "a" * 64},
            {"item_id": "item-b", "input_fingerprint": "b" * 64},
        ),
        contribution=({"document_line_id": "line", "input_fingerprint": "c" * 64},),
    )
    evaluated = EvaluatedPopulation(
        basis=basis,
        inventory=tuple(
            {**row.model_dump(), "acquisition": "known", "carrying": "unknown"}
            for row in expected.inventory
        ),
        contribution=(
            {**expected.contribution[0].model_dump(), "db1": "known", "db2": "unknown"},
        ),
    )
    return expected, evaluated


def generation(expected=None, identity="g2", **changes):
    expected = expected or population()[0]
    data = {
        **expected.basis.model_dump(),
        "kind": "company",
        "scope_key": "company-all",
        "manifest_id": "manifest",
        "population_hash": population_fingerprint(expected),
        "algorithm_version": "company-v1",
    }
    data.update(changes)
    return Generation(id=identity, basis=CompanyGenerationBasis(**data))


def completion(**changes):
    data = {
        "inputs_sealed": True,
        "content_verified": True,
        "planned_work": 3,
        "completed_work": 3,
        "expected_inventory_rows": 2,
        "inventory_rows": 2,
        "expected_contribution_rows": 1,
        "contribution_rows": 1,
        "expected_trace_rows": 5,
        "trace_rows": 5,
    }
    data.update(changes)
    return Completion(**data)


def decide(**changes):
    expected, evaluated = population()
    data = {
        "tenant_id": "tenant",
        "candidate": generation(expected),
        "completion": completion(),
        "published": None,
        "expected_previous_id": None,
        "target_event_sequence": 20,
        "expected_population": expected,
        "evaluated_population": evaluated,
    }
    data.update(changes)
    return publication_decision(**data)


def test_distinct_subject_inputs_and_unknown_money_can_complete_work():
    result = decide()
    assert result.change_pointer and result.freshness == "ready"
    assert not hasattr(result, "financially_complete")
    assert not hasattr(generation().basis, "policy_revision_id")


def test_hash_is_canonical_but_binds_inputs_and_context():
    expected, _ = population()
    reordered = expected.model_copy(update={"inventory": expected.inventory[::-1]})
    assert population_fingerprint(expected) == population_fingerprint(reordered)
    changed = expected.model_copy(
        update={"basis": expected.basis.model_copy(update={"event_sequence": 21})}
    )
    assert population_fingerprint(expected) != population_fingerprint(changed)
    changed = expected.model_copy(update={"contribution": ()})
    assert population_fingerprint(expected) != population_fingerprint(changed)


@pytest.mark.parametrize("field", ["expected_population", "evaluated_population"])
def test_population_proof_is_mandatory(field):
    with pytest.raises(PublicationRefusal, match="cost_population_required"):
        decide(**{field: None})


def test_equal_count_input_substitution_cannot_reuse_manifest_hash():
    expected, evaluated = population()
    replacement = expected.inventory[0].model_copy(
        update={"input_fingerprint": "f" * 64}
    )
    expected = expected.model_copy(
        update={"inventory": (replacement, expected.inventory[1])}
    )
    evaluated = evaluated.model_copy(
        update={
            "inventory": (
                evaluated.inventory[0].model_copy(
                    update={"input_fingerprint": "f" * 64}
                ),
                evaluated.inventory[1],
            )
        }
    )
    with pytest.raises(PublicationRefusal, match="cost_population_manifest_mismatch"):
        decide(expected_population=expected, evaluated_population=evaluated)


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing", "cost_population_missing"),
        ("duplicate", "cost_population_duplicate"),
        ("stale", "cost_population_input_mismatch"),
        ("context", "cost_population_context_mismatch"),
    ],
)
def test_exact_closure_is_required(change, code):
    _, evaluated = population()
    if change == "missing":
        evaluated = evaluated.model_copy(update={"inventory": evaluated.inventory[:1]})
    elif change == "duplicate":
        evaluated = evaluated.model_copy(
            update={"inventory": (evaluated.inventory[0],) * 2}
        )
    elif change == "stale":
        evaluated = evaluated.model_copy(
            update={
                "inventory": (
                    evaluated.inventory[0].model_copy(
                        update={"input_fingerprint": "d" * 64}
                    ),
                    evaluated.inventory[1],
                )
            }
        )
    else:
        evaluated = evaluated.model_copy(
            update={"basis": evaluated.basis.model_copy(update={"event_sequence": 21})}
        )
    with pytest.raises(PublicationRefusal, match=code):
        decide(evaluated_population=evaluated)


def test_candidate_context_must_equal_population_context():
    with pytest.raises(PublicationRefusal, match="cost_population_context_mismatch"):
        decide(candidate=generation(knowledge_at="2026-09-18T00:00:00Z"))


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"inputs_sealed": False}, "cost_inputs_unsealed"),
        ({"content_verified": False}, "cost_content_unverified"),
        ({"completed_work": 2}, "cost_work_incomplete"),
        ({"trace_rows": 4}, "cost_row_count_mismatch"),
        (
            {"inventory_rows": 1, "expected_inventory_rows": 1},
            "cost_population_row_count_mismatch",
        ),
        (
            {"contribution_rows": 0, "expected_contribution_rows": 0},
            "cost_population_row_count_mismatch",
        ),
    ],
)
def test_population_does_not_bypass_existing_integrity_gates(changes, code):
    with pytest.raises(PublicationRefusal, match=code):
        decide(completion=completion(**changes))


def test_retry_and_late_events_preserve_existing_semantics():
    result = decide(
        published=generation(), expected_previous_id="old", target_event_sequence=21
    )
    assert not result.change_pointer and result.freshness == "pending"
    with pytest.raises(PublicationRefusal, match="cost_generation_identity_mismatch"):
        decide(published=generation(manifest_id="different"))


def test_new_manifest_can_replace_prior_company_inputs():
    prior = generation(
        identity="old", event_sequence=19, manifest_id="prior", population_hash="f" * 64
    )
    assert decide(published=prior, expected_previous_id="old").change_pointer
    with pytest.raises(PublicationRefusal, match="cost_publication_changed"):
        decide(published=prior, expected_previous_id="wrong")
    prior = generation(identity="newer", event_sequence=21)
    with pytest.raises(PublicationRefusal, match="cost_generation_obsolete"):
        decide(published=prior, expected_previous_id="newer", target_event_sequence=21)


@pytest.mark.parametrize("field", ["candidate", "published"])
def test_foreign_generation_refuses_generically(field):
    with pytest.raises(PublicationRefusal, match="cost_basis_unavailable"):
        decide(**{field: generation(tenant_id="foreign")})


def test_empty_company_requires_explicit_empty_population():
    expected, _ = population()
    expected = expected.model_copy(update={"inventory": (), "contribution": ()})
    evaluated = EvaluatedPopulation(basis=expected.basis)
    result = decide(
        candidate=generation(expected),
        expected_population=expected,
        evaluated_population=evaluated,
        completion=completion(
            planned_work=0,
            completed_work=0,
            expected_inventory_rows=0,
            inventory_rows=0,
            expected_contribution_rows=0,
            contribution_rows=0,
            expected_trace_rows=0,
            trace_rows=0,
        ),
    )
    assert result.freshness == "ready"


@pytest.mark.parametrize(
    "changes",
    [
        {"policy_revision_id": "invented"},
        {"population_hash": "bad"},
        {"algorithm_version": "future"},
        {"event_sequence": True},
    ],
)
def test_company_basis_is_strict(changes):
    with pytest.raises(ValidationError):
        generation(**changes)


def test_selected_scope_cannot_be_promoted_to_company_by_population_arguments():
    from reality.domain.cost_generation import GenerationBasis

    selected = Generation(
        id="selected",
        basis=GenerationBasis(
            tenant_id="tenant",
            scope_key="company-all",
            kind="inventory",
            manifest_id="manifest",
            policy_revision_id="policy",
            profile_revision_id=None,
            effective_at="2026-09-01T00:00:00Z",
            knowledge_at="2026-09-19T00:00:00Z",
            event_sequence=20,
            algorithm_version="inventory-v1",
        ),
    )
    with pytest.raises(PublicationRefusal, match="cost_context_unsupported"):
        decide(candidate=selected)
    with pytest.raises(PublicationRefusal, match="cost_context_unsupported"):
        decide(published=selected, expected_previous_id="selected")


@pytest.mark.parametrize(
    "changes",
    [
        {"effective_at": "2026-08-31T00:00:00Z"},
        {"scope_key": "subset"},
    ],
)
def test_same_scope_label_cannot_mask_incompatible_company_cutoff(changes):
    with pytest.raises(PublicationRefusal, match="cost_context_unsupported"):
        decide(
            published=generation(identity="prior", **changes),
            expected_previous_id="prior",
        )


def test_duplicate_expected_members_cannot_pass_even_with_matching_digest():
    expected, evaluated = population()
    expected = expected.model_copy(update={"inventory": (expected.inventory[0],) * 2})
    with pytest.raises(PublicationRefusal, match="cost_population_duplicate"):
        decide(
            candidate=generation(expected),
            expected_population=expected,
            evaluated_population=evaluated,
        )


def test_foreign_population_is_rejected_before_returning_any_coverage():
    expected, evaluated = population()
    foreign = expected.basis.model_copy(update={"tenant_id": "foreign"})
    expected = expected.model_copy(update={"basis": foreign})
    evaluated = evaluated.model_copy(update={"basis": foreign})
    with pytest.raises(PublicationRefusal, match="cost_population_context_mismatch"):
        decide(expected_population=expected, evaluated_population=evaluated)
