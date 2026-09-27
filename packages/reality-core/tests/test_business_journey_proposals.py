from pathlib import Path

import pytest
import yaml
from reality.services.business_journeys import (
    JourneyProposalError,
    create_proposal,
    list_proposals,
    moderate_proposal,
    prepare_proposal,
    set_vote,
)

QUESTION_FIXTURES = yaml.safe_load(
    (Path(__file__).parent / "fixtures/business_journey_questions.yaml").read_text()
)


def _input() -> dict[str, str]:
    return {
        "title": "Supplier sends less than advised",
        "business_question": "What happens when the advice says 100 and 96 arrive?",
        "expected_outcome": "Keep advice, receipt and the four missing units visible.",
        "process_area": "receiving",
    }


def test_proposal_requires_confirmation_and_shows_existing_journeys(
    session, scheduled_owner
) -> None:
    preview = create_proposal(session, scheduled_owner.id, **_input())

    assert preview["requires_confirmation"] is True
    assert preview["journey_matches"]
    assert list_proposals(session) == []

    created = create_proposal(
        session, scheduled_owner.id, **_input(), confirmed=True
    )
    assert created["status"] == "proposed"
    assert created["vote_count"] == 0


@pytest.mark.parametrize(
    "case", QUESTION_FIXTURES["duplicate_proposals"], ids=lambda case: case["name"]
)
def test_curated_paraphrases_find_open_proposal_before_submission(
    session, scheduled_owner, case
) -> None:
    existing = create_proposal(
        session, scheduled_owner.id, **case["existing"], confirmed=True
    )

    preview = prepare_proposal(session, **case["candidate"])

    matches = preview["proposal_matches"]
    assert matches
    assert matches[0]["id"] == existing["id"]
    assert matches[0]["similarity_score"] >= 30


@pytest.mark.parametrize(
    "case", QUESTION_FIXTURES["unrelated_proposals"], ids=lambda case: case["name"]
)
def test_unrelated_proposals_are_not_reported_as_duplicates(
    session, scheduled_owner, case
) -> None:
    create_proposal(session, scheduled_owner.id, **case["existing"], confirmed=True)

    preview = prepare_proposal(session, **case["candidate"])

    assert preview["proposal_matches"] == []


def test_one_reversible_vote_per_account(session, scheduled_owner) -> None:
    proposal = create_proposal(
        session, scheduled_owner.id, **_input(), confirmed=True
    )

    first = set_vote(session, scheduled_owner.id, str(proposal["id"]), active=True)
    retry = set_vote(session, scheduled_owner.id, str(proposal["id"]), active=True)
    withdrawn = set_vote(session, scheduled_owner.id, str(proposal["id"]), active=False)

    assert first["vote_count"] == 1
    assert retry["vote_count"] == 1
    assert retry["voted"] is True
    assert withdrawn["vote_count"] == 0
    assert withdrawn["voted"] is False


def test_proposal_rejects_contact_details(session, scheduled_owner) -> None:
    values = _input()
    values["business_question"] = "Contact me at owner@example.com about receiving"
    try:
        create_proposal(session, scheduled_owner.id, **values, confirmed=True)
    except JourneyProposalError as error:
        assert "contact" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected personal contact details to be refused")


def test_only_platform_admin_can_moderate_with_valid_lifecycle(
    session, scheduled_owner
) -> None:
    proposal = create_proposal(
        session, scheduled_owner.id, **_input(), confirmed=True
    )

    try:
        moderate_proposal(
            session,
            scheduled_owner.id,
            str(proposal["id"]),
            status="under_review",
            public_rationale="Reviewing evidence and demand.",
        )
    except JourneyProposalError as error:
        assert "administrator" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected non-admin moderation to be refused")

    scheduled_owner.is_platform_admin = True
    session.flush()
    reviewed = moderate_proposal(
        session,
        scheduled_owner.id,
        str(proposal["id"]),
        status="under_review",
        public_rationale="Reviewing evidence and demand.",
    )
    available = moderate_proposal(
        session,
        scheduled_owner.id,
        str(proposal["id"]),
        status="available",
        public_rationale="Available through the under-delivery journey.",
        available_journey_id="H02",
    )

    assert reviewed["status"] == "under_review"
    assert available["status"] == "available"
    assert available["available_journey_id"] == "H02"
    assert available["reviewed_at"]


def test_moderation_rejects_invalid_transition_and_missing_journey(
    session, scheduled_owner
) -> None:
    scheduled_owner.is_platform_admin = True
    proposal = create_proposal(
        session, scheduled_owner.id, **_input(), confirmed=True
    )

    for status, journey in (("available", None), ("in_progress", "H02")):
        try:
            moderate_proposal(
                session,
                scheduled_owner.id,
                str(proposal["id"]),
                status=status,
                public_rationale="Reviewed by product governance.",
                available_journey_id=journey,
            )
        except JourneyProposalError:
            pass
        else:  # pragma: no cover
            raise AssertionError("Expected invalid moderation to be refused")
