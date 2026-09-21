"""Spec 182 FR-021 and SC-009: a run exported as a storyline draft.

The draft is what a person edits into a storyline of their own: confirmed commands
in order, seed identities as ``$ref``, created records as ``$chapter``, dates as
offsets, texts marked missing, and anything the format cannot express named in
place. A three-command free-play run needs only its texts to import and play.
"""

# ruff: noqa: F811 - fixtures are imported and then named as parameters
import json
from datetime import UTC, datetime, timedelta

import pytest
import yaml
from conftest import record_by_id
from sqlalchemy import select

from reality.db.core import BusinessEvent, PlaygroundRun
from reality.services import storyline
from reality.services.core import NotFound, now
from reality.storyline import recorder
from reality.storyline.export import day_offset
from reality.storyline.package import validate_package
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from tests.test_storyline_library_api import http  # noqa: F401
from tests.test_storyline_library_api import start as start_over_http
from tests.test_storyline_runs import KEY, owner, play, started  # noqa: F401


def confirm(session, tenant_id, tool, arguments):
    """A command a person confirms in the ordinary app of the practice company."""
    proposal = create_change_proposal(
        session, tenant_id, tool, arguments, actor_type="human"
    )
    token = json.loads(proposal.input).get("_delivery_review", {}).get("token")
    extra = {"review_token": token} if token else {}
    executed = approve_and_execute_proposal(
        session, tenant_id, proposal.id, confirmed=True, **extra
    )
    return json.loads(executed.output or "{}")


def seed_of(session, run_id):
    return record_by_id(session, PlaygroundRun, run_id).initialization_progress[
        "storyline"
    ]


def order_input(seed):
    refs = seed["refs"]
    today = now()
    return {
        "direction": "sales",
        "number": "AT-0090",
        "company_party_id": seed["company_party_id"],
        "counterparty_id": refs["parties"]["nordlicht"],
        "location_id": refs["locations"]["hamburg"],
        "gross_amount": "49.00",
        "document_date": today.date().isoformat(),
        "requested_delivery_at": (today + timedelta(days=5)).isoformat(),
        "payment_term_code": refs["terms"]["net14"],
        "lines": [
            {
                "item_id": refs["items"]["fjord"],
                "quantity": "2",
                "unit": "pcs",
                "unit_price": "24.50",
                "gross_amount": "49.00",
                "promised_at": (today + timedelta(days=5)).isoformat(),
            }
        ],
    }


def free_play_three_commands(session, tenant_id, seed):
    order = confirm(session, tenant_id, "order_create", order_input(seed))
    confirm(
        session, tenant_id, "reserve", {"commitment_id": order["commitment_ids"][0]}
    )
    confirm(
        session,
        tenant_id,
        "fact_observe",
        {
            "source_record_id": order["source_record_id"],
            "subject_type": "document",
            "subject_id": order["document_id"],
            "predicate": "order.customer_reference",
            "value": "PO-FREE-1",
            "observed_at": now().isoformat(),
            "idempotency_key": "free-play-reference",
        },
    )
    return order


def test_day_offsets_are_relative_to_the_run_start():
    start = datetime(2026, 9, 13, 9, tzinfo=UTC)
    assert day_offset("2026-09-13T17:00:00+00:00", start) == "0d"
    assert day_offset("2026-09-10", start) == "-3d"
    assert day_offset("2026-09-18T08:00:00Z", start) == "+5d"
    assert day_offset("PO-2026-118", start) is None


def test_three_free_play_commands_export_as_a_draft_that_needs_only_texts(
    session, owner
):
    """SC-009: refs, chapter references, offsets and missing texts; then it plays."""
    view = started(session, owner)
    tenant_id, run_id = view["tenant_id"], view["run_id"]
    seed = seed_of(session, run_id)
    free_play_three_commands(session, tenant_id, seed)

    body, content_type, filename = storyline.export_draft(session, owner.id, run_id)
    assert (content_type, filename) == (
        "application/yaml",
        "order-to-close-draft.storyline.yaml",
    )
    draft = yaml.safe_load(body)
    assert draft["draft"] is True and draft["key"] == "order-to-close-draft"
    assert (
        draft["seed"]
        == storyline.package_document(session, owner.id, KEY, 1)[0]["seed"]
    )
    assert [c["key"] for c in draft["chapters"]] == ["step-1", "step-2", "step-3"]
    assert [c.get("next") for c in draft["chapters"]] == ["step-2", "step-3", None]
    first, second, third = draft["chapters"]
    assert first["command"] == "order_create"
    assert first["input"]["counterparty_id"] == "$ref.parties.nordlicht"
    assert first["input"]["company_party_id"] == "$company.party"
    assert first["input"]["location_id"] == "$ref.locations.hamburg"
    assert first["input"]["payment_term_code"] == "$ref.terms.net14"
    assert first["input"]["lines"][0]["item_id"] == "$ref.items.fjord"
    assert first["input"]["document_date"] == "0d"
    assert first["input"]["requested_delivery_at"] == "+5d"
    assert first["input"]["lines"][0]["promised_at"] == "+5d"
    assert second["input"] == {
        "commitment_id": "$chapter.step-1.output.commitment_ids[0]"
    }
    assert third["input"]["subject_id"] == "$chapter.step-1.output.document_id"
    assert (
        third["input"]["source_record_id"] == "$chapter.step-1.output.source_record_id"
    )
    assert third["input"]["observed_at"] == "0d"
    for chapter in draft["chapters"]:
        assert chapter["title"] == {"missing": True}
        assert chapter["situation"] == {"missing": True}
        assert chapter["explain"] == {"missing": True}
    assert draft["summary"] == {"missing": True}
    assert "_delivery_review" not in json.dumps(draft)

    # The draft validates except for the texts still to be written and the draft
    # mark itself, which says "edit me before import".
    result = validate_package(draft)
    assert {issue.code for issue in result.errors} == {"missing_text", "draft"}
    assert {issue.path for issue in result.errors if issue.code == "missing_text"} == {
        "summary",
        *(
            f"chapters[{i}].{field}"
            for i in range(3)
            for field in ("title", "situation", "explain")
        ),
    }

    # Texts filled in and the mark removed, the draft imports and plays to the same events.
    draft["draft"] = False
    draft["summary"] = {"en": "Three commands from free play."}
    for position, chapter in enumerate(draft["chapters"], start=1):
        chapter["title"] = {"en": f"Step {position}"}
        chapter["situation"] = {"en": f"Do step {position}."}
        chapter["explain"] = {"en": f"Step {position} happened."}
    imported = storyline.import_package(
        session,
        owner.id,
        yaml.safe_dump(draft, sort_keys=False).encode(),
        filename="draft.storyline.yaml",
    )
    assert imported["chapters"] == 3
    copy = storyline.start(
        session,
        owner.id,
        key=draft["key"],
        version=1,
        request_key="play-draft",
        confirmed=True,
    )
    assert copy["status"] == "active", copy
    for key in ("step-1", "step-2", "step-3"):
        assert play(session, owner, copy["tenant_id"], key)["status"] == "done", key

    def event_types(tenant):
        return sorted(
            session.scalars(
                select(BusinessEvent.event_type).where(
                    BusinessEvent.tenant_id == tenant
                )
            )
        )

    assert event_types(copy["tenant_id"]) == event_types(tenant_id)


def test_story_chapters_keep_their_texts_and_unsupported_commands_stay_in_place(
    session, owner
):
    view = started(session, owner)
    tenant_id, run_id = view["tenant_id"], view["run_id"]
    order = play(session, owner, tenant_id, "order")
    confirm(
        session,
        tenant_id,
        "reserve",
        {"commitment_id": order["output"]["commitment_ids"][0]},
    )
    scope = recorder.TraceScope(tenant_id=tenant_id, run_id=run_id, actor="person")
    recorder.record(
        session,
        scope,
        kind="confirm",
        name="membership_grant",
        input={"email": "someone@example.test"},
        result={},
    )
    recorder.record(
        session,
        scope,
        kind="confirm",
        name="fact_observe",
        input={
            "subject_type": "document",
            "subject_id": "doc_ffffffffff",
            "predicate": "order.customer_reference",
            "value": "x",
        },
        result={},
    )

    draft = yaml.safe_load(storyline.export_draft(session, owner.id, run_id)[0])
    keys = [c["key"] for c in draft["chapters"]]
    assert keys == ["order", "step-2", "step-3", "step-4"]
    first, reserve, membership, stray = draft["chapters"]
    assert first["title"]["en"] == "Create the order" and first["view"] == "view:orders"
    assert first["input"]["counterparty_id"] == "$ref.parties.nordlicht"
    assert reserve["input"] == {
        "commitment_id": "$chapter.order.output.commitment_ids[0]"
    }
    assert reserve["title"] == {"missing": True}
    assert membership["kind"] == "unsupported"
    assert "membership_grant" in membership["reason"]
    assert stray["kind"] == "unsupported" and stray["command"] == "fact_observe"
    assert "subject_id names doc_ffffffffff" in stray["reason"]
    codes = {(issue.path, issue.code) for issue in validate_package(draft).errors}
    assert ("chapters[2]", "unsupported") in codes
    assert ("chapters[3]", "unsupported") in codes

    with pytest.raises(NotFound):
        storyline.export_draft(session, owner.id, "run_missing")


def test_the_draft_route_downloads_the_run_of_the_account(http):
    client, _actor = http
    run = start_over_http(client)
    response = client.get(f"/api/storyline/runs/{run['run_id']}/draft")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/yaml")
    assert response.headers["content-disposition"].endswith(
        'filename="order-to-close-draft.storyline.yaml"'
    )
    assert yaml.safe_load(response.content)["draft"] is True
    as_json = client.get(f"/api/storyline/runs/{run['run_id']}/draft?format=json")
    assert as_json.status_code == 200
    assert as_json.json()["chapters"] == []
    assert client.get("/api/storyline/runs/run_nope/draft").status_code == 404
    assert (
        client.get(f"/api/storyline/runs/{run['run_id']}/draft?format=xml").status_code
        == 422
    )
