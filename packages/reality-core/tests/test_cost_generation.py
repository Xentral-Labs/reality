"""Publication decisions cannot promote unfinished or obsolete cost generations."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from reality.domain.cost_generation import (
    Completion,
    Generation,
    GenerationBasis,
    PublicationRefusal,
    publication_decision,
)


def generation(identity="g2", sequence=20, **basis_changes):
    basis = {
        "tenant_id": "tenant",
        "scope_key": "inventory-scope",
        "kind": "inventory",
        "manifest_id": "manifest",
        "policy_revision_id": "policy",
        "profile_revision_id": None,
        "effective_at": "2026-09-01T00:00:00Z",
        "knowledge_at": "2026-09-19T00:00:00Z",
        "event_sequence": sequence,
        "algorithm_version": "inventory-v1",
    }
    basis.update(basis_changes)
    return Generation(id=identity, basis=GenerationBasis(**basis))


def completion(**changes):
    values = {
        "inputs_sealed": True,
        "content_verified": True,
        "planned_work": 2,
        "completed_work": 2,
        "expected_inventory_rows": 2,
        "inventory_rows": 2,
        "expected_contribution_rows": 0,
        "contribution_rows": 0,
        "expected_trace_rows": 4,
        "trace_rows": 4,
    }
    values.update(changes)
    return Completion(**values)


def decide(candidate=None, progress=None, **changes):
    args = {
        "tenant_id": "tenant",
        "candidate": candidate or generation(),
        "completion": progress or completion(),
        "published": None,
        "expected_previous_id": None,
        "target_event_sequence": 20,
    }
    args.update(changes)
    return publication_decision(**args)


def test_complete_generation_can_publish_without_cost_coverage_claim():
    result = decide()
    assert result.generation_id == "g2"
    assert result.change_pointer is True
    assert result.freshness == "ready"
    assert result.processed_event_sequence == result.target_event_sequence == 20
    assert not hasattr(result, "financially_complete")


def test_late_freight_keeps_completed_basis_pending():
    result = decide(target_event_sequence=21)
    assert result.change_pointer is True
    assert result.freshness == "pending"
    assert result.processed_event_sequence == 20
    assert result.target_event_sequence == 21


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"inputs_sealed": False}, "cost_inputs_unsealed"),
        ({"content_verified": False}, "cost_content_unverified"),
        ({"completed_work": 1}, "cost_work_incomplete"),
        ({"inventory_rows": 1}, "cost_row_count_mismatch"),
        ({"contribution_rows": 1}, "cost_row_count_mismatch"),
        ({"trace_rows": 3}, "cost_row_count_mismatch"),
    ],
)
def test_incomplete_capture_work_and_rows_refuse(changes, code):
    with pytest.raises(PublicationRefusal) as error:
        decide(progress=completion(**changes))
    assert error.value.code == code


def test_pointer_race_refuses_instead_of_overwriting_new_publication():
    with pytest.raises(PublicationRefusal, match="cost_publication_changed"):
        decide(
            published=generation("g3", 21),
            expected_previous_id="g1",
            target_event_sequence=21,
        )


def test_older_build_cannot_replace_newer_even_with_matching_pointer():
    with pytest.raises(PublicationRefusal, match="cost_generation_obsolete"):
        decide(
            published=generation("g3", 21),
            expected_previous_id="g3",
            target_event_sequence=21,
        )


def test_successful_replacement_and_retry_after_lost_reply():
    result = decide(published=generation("g1", 19), expected_previous_id="g1")
    assert result.change_pointer
    retry = decide(
        published=generation(), expected_previous_id="g1", target_event_sequence=21
    )
    assert not retry.change_pointer
    assert retry.freshness == "pending"


@pytest.mark.parametrize("published", [None, generation("g1", 19)])
def test_missing_or_unexpected_pointer_refuses(published):
    with pytest.raises(PublicationRefusal, match="cost_publication_changed"):
        decide(published=published, expected_previous_id="different")


def test_same_identity_with_changed_basis_refuses():
    with pytest.raises(PublicationRefusal, match="cost_generation_identity_mismatch"):
        decide(published=generation(manifest_id="changed"))


@pytest.mark.parametrize(
    "changes",
    [
        {"scope_key": "other"},
        {"kind": "contribution", "profile_revision_id": "profile"},
    ],
)
def test_different_canonical_scope_refuses(changes):
    with pytest.raises(PublicationRefusal, match="cost_context_unsupported"):
        decide(published=generation("g1", 19, **changes), expected_previous_id="g1")


@pytest.mark.parametrize("field", ["candidate", "published"])
def test_foreign_tenant_is_generic_and_never_discloses_identity(field):
    with pytest.raises(PublicationRefusal) as error:
        decide(**{field: generation("secret", tenant_id="neighbor")})
    assert error.value.code == "cost_basis_unavailable"
    assert "secret" not in str(error.value) and "neighbor" not in str(error.value)


def test_backward_live_cursor_refuses():
    with pytest.raises(PublicationRefusal, match="cost_event_cursor_invalid"):
        decide(target_event_sequence=19)


def test_empty_scope_is_permitted_only_with_verified_sealed_zero_work():
    empty = completion(
        planned_work=0,
        completed_work=0,
        expected_inventory_rows=0,
        inventory_rows=0,
        expected_trace_rows=0,
        trace_rows=0,
    )
    assert decide(progress=empty).freshness == "ready"
    with pytest.raises(PublicationRefusal, match="cost_inputs_unsealed"):
        decide(progress=empty.model_copy(update={"inputs_sealed": False}))


@pytest.mark.parametrize(
    "changes",
    [
        {"planned_work": -1},
        {"completed_work": 3},
        {"inventory_rows": True},
        {"trace_rows": "4"},
        {"inputs_sealed": "yes"},
        {"unexpected": 1},
        {"planned_work": 0, "completed_work": 0},
    ],
)
def test_completion_facts_are_strict_and_consistent(changes):
    with pytest.raises(ValidationError):
        completion(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"tenant_id": " "},
        {"event_sequence": True},
        {"event_sequence": -1},
        {"effective_at": "2026-09-01"},
        {"kind": "contribution"},
        {"profile_revision_id": "profile"},
        {"kind": "anything"},
    ],
)
def test_basis_rejects_unsupported_or_invented_authority(changes):
    with pytest.raises(ValidationError):
        generation(**changes)


def test_basis_is_immutable_and_normalizes_utc():
    value = generation(effective_at="2026-09-01T02:00:00+02:00")
    assert value.basis.effective_at == datetime(2026, 9, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        value.basis.event_sequence = 30


@pytest.mark.parametrize("cursor", [-1, True, "20"])
def test_target_cursor_is_not_coerced(cursor):
    with pytest.raises(PublicationRefusal, match="cost_event_cursor_invalid"):
        decide(target_event_sequence=cursor)


@pytest.mark.parametrize(
    "changes",
    [
        {"policy_revision_id": "another-policy"},
        {"effective_at": "2026-08-01T00:00:00Z"},
    ],
)
def test_scope_key_cannot_mask_changed_valuation_basis(changes):
    with pytest.raises(PublicationRefusal, match="cost_context_unsupported"):
        decide(published=generation("g1", 19, **changes), expected_previous_id="g1")


def test_scope_key_cannot_mask_changed_contribution_profile():
    candidate = generation(kind="contribution", profile_revision_id="profile2")
    prior = generation("g1", 19, kind="contribution", profile_revision_id="profile1")
    with pytest.raises(PublicationRefusal, match="cost_context_unsupported"):
        decide(candidate=candidate, published=prior, expected_previous_id="g1")
