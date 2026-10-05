"""Pure versioned creation boundaries never infer intent from evidence."""

import pytest

from reality.domain.operational_cases import (
    event_disposition,
    fulfillment_state,
    return_state,
)


@pytest.mark.parametrize(
    "event",
    [
        "item.created",
        "location.created",
        "party.created",
        "operational_case.taken_over",
        "unknown.future",
        "refund.succeeded",
    ],
)
def test_observation_is_not_a_new_goal(event):
    assert event_disposition(event) == "no_case"


def test_creation_update_settle_and_freshness_are_distinct():
    assert event_disposition("commitment.created") == "create_or_match"
    assert event_disposition("return.announced") == "create_or_match"
    assert event_disposition("commitment.revised") == "update"
    assert event_disposition("commitment.fulfilled") == "settle"
    assert event_disposition("source_record.received") == "freshness"


def test_partial_fulfillment_and_correction_follow_current_facts():
    assert (
        fulfillment_state(
            [
                {"status": "open", "open_quantity": "1"},
                {"status": "fulfilled", "open_quantity": "0"},
            ]
        )
        == "outstanding"
    )
    assert (
        fulfillment_state([{"status": "fulfilled", "open_quantity": "0"}])
        == "completed"
    )
    assert (
        fulfillment_state([{"status": "cancelled", "open_quantity": "30"}])
        == "completed"
    )
    assert return_state("withdrawn") == "abandoned"
    assert return_state("fulfilled") == "completed"
