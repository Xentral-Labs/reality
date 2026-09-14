"""Spec 182 FR-001, FR-003, FR-005, FR-009, FR-010, FR-012: storyline runs and chapters."""

import json

import pytest
from sqlalchemy import select

from reality.db.core import (
    AppUser,
    ChangeProposal,
    Party,
    PlaygroundRun,
    PlaygroundStep,
    StorylinePackageRecord,
    StorylineTraceEntry,
    Tenant,
    now,
    uid,
)
from reality.services import storyline
from reality.services.core import Conflict, InvalidOperation, NotFound
from reality.services.tenant_policy import PlaygroundOperationDenied
from reality.storyline import recorder
from reality.storyline.package import builtin_documents

KEY, VERSION = "order-to-close", 1


@pytest.fixture
def owner(session, monkeypatch):
    recorder.clear_cache()
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.commit()
    yield user
    recorder.clear_cache()


def started(session, owner, request_key="story-1"):
    view = storyline.start(
        session,
        owner.id,
        key=KEY,
        version=VERSION,
        request_key=request_key,
        confirmed=True,
    )
    assert view["status"] == "active", view
    return view


def play(session, owner, tenant_id, key, request_key=None):
    """Prepare and, for command chapters, confirm one chapter; return the step view."""
    engine = session.connection()
    prepared = storyline.prepare(
        engine,
        owner.id,
        tenant_id,
        key,
        request_key or f"req-{key}",
        db_session=session,
    )
    if prepared["refused"] or prepared["status"] == "done":
        return prepared
    return storyline.confirm(
        engine,
        owner.id,
        tenant_id,
        key,
        prepared["step_id"],
        prepared["preview_revision"],
        confirmed=True,
        db_session=session,
    )


def test_start_seeds_a_practice_company_and_resumes_the_same_run(session, owner):
    view = started(session, owner)
    run = session.get(PlaygroundRun, view["run_id"])

    assert (
        run.sandbox_kind,
        run.preset_key,
        run.storyline_key,
        run.storyline_version,
    ) == (
        "practice",
        "storyline",
        KEY,
        VERSION,
    )
    assert session.get(Tenant, run.tenant_id).purpose == "playground"
    stored = run.initialization_progress["storyline"]
    assert set(stored["refs"]) == {"parties", "items", "locations", "terms"}
    assert stored["refs"]["terms"]["net14"] == "NET14"
    assert stored["company_party_id"]
    assert {"opening", "overdue_invoice", "hold", "purchase_order"} <= set(
        stored["seed_outputs"]
    )
    parties = session.scalars(
        select(Party).where(Party.tenant_id == run.tenant_id)
    ).all()
    assert {party.name for party in parties} >= {
        "Nordlicht Handels GmbH",
        "Baltic Supply",
    }
    assert view["current_chapter"] == "order"

    again = storyline.start(
        session,
        owner.id,
        key=KEY,
        version=VERSION,
        request_key="story-2",
        confirmed=True,
    )
    assert again["run_id"] == view["run_id"]
    with pytest.raises(Conflict):
        storyline.start(
            session, owner.id, key=KEY, version=2, request_key="story-3", confirmed=True
        )


def test_start_needs_confirmation_and_a_known_package(
    session, owner, monkeypatch
):
    with pytest.raises(PlaygroundOperationDenied):
        storyline.start(session, owner.id, key=KEY, version=VERSION, request_key="x")
    with pytest.raises(NotFound):
        storyline.start(
            session,
            owner.id,
            key="no-such-story",
            version=1,
            request_key="x",
            confirmed=True,
        )


def test_a_failing_seed_rolls_the_company_back_and_names_the_entry(session, owner):
    document = json.loads(json.dumps(builtin_documents()["order-to-close"]))
    document["key"] = "broken-seed"
    document["seed"]["history"][0]["input"]["quantity"] = "-8"
    session.add(
        StorylinePackageRecord(
            id=uid("stp"),
            owner_user_id=owner.id,
            key="broken-seed",
            version=1,
            title="Broken",
            checksum="x" * 64,
            document=document,
            validation={},
        )
    )
    session.commit()

    view = storyline.start(
        session,
        owner.id,
        key="broken-seed",
        version=1,
        request_key="broken-1",
        confirmed=True,
    )

    assert view["status"] == "initialization_failed"
    assert view["error"]["entry"] == 0
    assert view["error"]["command"] == "movement_create"
    run = session.get(PlaygroundRun, view["run_id"])
    assert run.initialization_error_code == "seed_failed"
    assert (
        session.scalars(select(Party).where(Party.tenant_id == run.tenant_id)).all()
        == []
    )


def test_state_is_refused_for_a_company_without_a_storyline(session, owner, business):
    with pytest.raises(NotFound):
        storyline.state(session, owner.id, business.tenant.id)


def test_chapters_play_through_the_ordinary_proposal_path(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]

    order = play(session, owner, tenant_id, "order")
    assert order["status"] == "done"
    assert order["proposal_status"] == "executed"
    assert order["marker"]["sequence"] >= 0
    assert order["receipt"]["records"]
    assert order["receipt"]["event_sequence"] > order["marker"]["sequence"]
    proposal = session.get(ChangeProposal, order["proposal_id"])
    assert proposal.type == "tool:order_create"
    assert proposal.actor_type == "human"
    step = session.get(PlaygroundStep, order["step_id"])
    assert step.lesson_step_key == "order"
    assert {
        identity.split("__")[1] for identity in step.before_observation["exceptions"]
    } == {"overdue_receivable", "overdue_incoming_supplier_commitment"}

    with pytest.raises(Conflict):
        storyline.prepare(
            session.connection(),
            owner.id,
            tenant_id,
            "order",
            "again",
            db_session=session,
        )

    state = storyline.state(session, owner.id, tenant_id)
    statuses = {entry["key"]: entry["status"] for entry in state["chapters"]}
    assert statuses["order"] == "done"
    assert statuses["reference"] == "current"
    assert state["current_chapter"] == "reference"

    delta = storyline.delta(session, owner.id, tenant_id, step_id=order["step_id"])
    assert [event["type"] for event in delta["events"]]
    assert {record["record_type"] for record in delta["records"]} >= {
        "commitment",
        "document",
    }
    assert [x["class_id"] for x in delta["exceptions"]["raised"]] == [
        "outgoing_commitment_at_risk"
    ]
    assert delta["graph"]["record"]["record_type"] == "commitment"
    assert any(node["primary"] for node in delta["graph"]["nodes"])

    reference = play(session, owner, tenant_id, "reference")
    assert reference["status"] == "done"
    fact_delta = storyline.delta(
        session, owner.id, tenant_id, step_id=reference["step_id"]
    )
    assert [fact["predicate"] for fact in fact_delta["facts"]] == [
        "order.customer_reference"
    ]

    receipt = play(session, owner, tenant_id, "receipt")
    assert receipt["status"] == "done"
    reserve = play(session, owner, tenant_id, "reserve")
    assert [
        x["class_id"]
        for x in storyline.delta(
            session, owner.id, tenant_id, step_id=reserve["step_id"]
        )["exceptions"]["cleared"]
    ] == ["outgoing_commitment_at_risk"]

    trace = storyline.trace(session, owner.id, tenant_id, step_id=order["step_id"])
    kinds = [(item["kind"], item["name"]) for item in trace["items"]]
    assert ("propose", "order_create") in kinds and ("confirm", "order_create") in kinds
    assert all(item["chapter"] == "order" for item in trace["items"])


def test_a_refused_preparation_is_an_outcome_and_the_story_continues(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    for key in ("order", "reference", "receipt", "reserve"):
        assert play(session, owner, tenant_id, key)["status"] == "done"

    dispatch = play(session, owner, tenant_id, "dispatch")

    assert dispatch["status"] == "refused"
    assert dispatch["proposal_id"] is None
    assert dispatch["refused"]["phase"] == "prepare"
    assert "delivery hold" in dispatch["refused"]["detail"]
    state = storyline.state(session, owner.id, tenant_id)
    statuses = {entry["key"]: entry["status"] for entry in state["chapters"]}
    assert statuses["dispatch"] == "done"
    assert state["current_chapter"] == "explain-hold"
    trace = storyline.trace(session, owner.id, tenant_id, step_id=dispatch["step_id"])
    assert [item["kind"] for item in trace["items"]] == ["error"]
    empty = storyline.delta(session, owner.id, tenant_id, step_id=dispatch["step_id"])
    assert empty["events"] == [] and empty["exceptions"] == {
        "raised": [],
        "cleared": [],
    }

    explain = play(session, owner, tenant_id, "explain-hold")
    assert explain["status"] == "done"
    assert [r["tool"] for r in explain["receipt"]["results"]] == [
        "exception_explain",
        "finance.party_balances.list",
    ]
    assert explain["receipt"]["results"][0]["input"]["exception_id"].startswith(
        "exc__overdue_receivable__doc_"
    )
    reads = storyline.trace(session, owner.id, tenant_id, step_id=explain["step_id"])
    assert [item["kind"] for item in reads["items"]] == ["read", "read"]


def test_branches_are_recorded_and_the_default_applies_without_a_choice(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    for key in ("order", "reference", "receipt", "reserve", "dispatch"):
        play(session, owner, tenant_id, key)
    with pytest.raises(NotFound):
        storyline.choose_branch(session, owner.id, tenant_id, "dispatch", "nope")
    with pytest.raises(Conflict):
        storyline.choose_branch(session, owner.id, tenant_id, "bill", "refund")

    chosen = storyline.choose_branch(session, owner.id, tenant_id, "dispatch", "call")

    assert chosen["current_chapter"] == "call-customer"
    assert session.get(PlaygroundRun, view["run_id"]).storyline_state["branches"] == {
        "dispatch": "call"
    }
    call = play(session, owner, tenant_id, "call-customer")
    assert call["status"] == "done"
    assert (
        storyline.state(session, owner.id, tenant_id)["current_chapter"]
        == "overpayment"
    )


def test_rejecting_a_chapter_allows_a_retry_with_a_new_request_key(session, owner):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    engine = session.connection()
    prepared = storyline.prepare(
        engine, owner.id, tenant_id, "order", "first", db_session=session
    )
    rejected = storyline.reject(
        engine,
        owner.id,
        tenant_id,
        "order",
        prepared["step_id"],
        confirmed=True,
        db_session=session,
    )
    assert rejected["status"] == "rejected"
    assert storyline.state(session, owner.id, tenant_id)["current_chapter"] == "order"
    with pytest.raises(Conflict):
        storyline.confirm(
            engine,
            owner.id,
            tenant_id,
            "order",
            prepared["step_id"],
            prepared["preview_revision"],
            confirmed=True,
            db_session=session,
        )

    again = play(session, owner, tenant_id, "order", request_key="second")
    assert again["status"] == "done"
    replay = storyline.confirm(
        engine,
        owner.id,
        tenant_id,
        "order",
        again["step_id"],
        "stale",
        confirmed=True,
        db_session=session,
    )
    assert replay["status"] == "done" and replay["proposal_id"] == again["proposal_id"]


def test_restart_archives_the_run_and_starts_a_fresh_company(session, owner):
    view = started(session, owner)
    play(session, owner, view["tenant_id"], "order")

    fresh = storyline.restart(
        session, owner.id, view["tenant_id"], request_key="restart-1", confirmed=True
    )

    assert fresh["status"] == "active"
    assert fresh["tenant_id"] != view["tenant_id"]
    old = session.get(PlaygroundRun, view["run_id"])
    assert old.status == "archived" and old.archived_at is not None
    assert (
        storyline.state(session, owner.id, fresh["tenant_id"])["current_chapter"]
        == "order"
    )
    assert session.scalars(
        select(StorylineTraceEntry).where(
            StorylineTraceEntry.tenant_id == view["tenant_id"]
        )
    ).all()


def test_library_lists_the_built_in_with_the_account_run(session, owner):
    before = storyline.library(session, owner.id)
    assert [item["key"] for item in before["items"]] == [
        "first-round",
        KEY,
        "purchase-to-pay",
    ]
    assert all(item["run"] is None for item in before["items"])
    view = started(session, owner)

    after = storyline.library(session, owner.id)
    played = next(item for item in after["items"] if item["key"] == KEY)

    assert played["run"]["tenant_id"] == view["tenant_id"]
    assert played["run"]["current_chapter"] == "order"
    assert played["title"]["de"] == "Auftrag bis Abschluss"
    # Only the storyline that was started carries a run.
    assert [item["key"] for item in after["items"] if item["run"]] == [KEY]


def test_tool_reference_explains_commands_views_and_exceptions():
    command = storyline.tool_reference("order_create")
    assert command["kind"] == "command" and command["access"] == "confirm"
    assert any(p["name"] == "lines" for p in command["parameters"])
    assert command["docs_path"].endswith("#command-order_create")

    view = storyline.tool_reference("view:open_items")
    assert view["label"]["de"] == "Offene Posten"

    exception = storyline.tool_reference("exception:overdue_receivable")
    assert exception["clears_through"]
    with pytest.raises(NotFound):
        storyline.tool_reference("no_such_tool")
    with pytest.raises(InvalidOperation):
        raise InvalidOperation("placeholder for symmetry")


def test_a_run_resumes_at_the_first_chapter_not_done_with_its_history_readable(
    session, owner
):
    view = started(session, owner)
    tenant_id = view["tenant_id"]
    first = play(session, owner, tenant_id, "order")
    play(session, owner, tenant_id, "reference")

    # Opening Storyline again resumes the same run and reports the next chapter.
    resumed = storyline.start(
        session, owner.id, key=KEY, version=VERSION, request_key="later", confirmed=True
    )
    assert resumed["run_id"] == view["run_id"]
    assert resumed["current_chapter"] == "receipt"
    state = storyline.state(session, owner.id, tenant_id)
    assert [c["status"] for c in state["chapters"][:3]] == ["done", "done", "current"]

    # Earlier chapters stay readable from their stored markers and trace.
    earlier = storyline.chapter_detail(session, owner.id, tenant_id, "order")
    assert earlier["status"] == "done" and earlier["can_run"] is False
    assert earlier["step"]["step_id"] == first["step_id"]
    assert storyline.delta(session, owner.id, tenant_id, step_id=first["step_id"])[
        "events"
    ]
    assert storyline.trace(session, owner.id, tenant_id, step_id=first["step_id"])[
        "items"
    ]
    with pytest.raises(Conflict):
        storyline.prepare(
            session.connection(),
            owner.id,
            tenant_id,
            "order",
            "replay",
            db_session=session,
        )


def test_free_play_is_recorded_with_its_own_marker_and_delta(session, owner):
    """FR-011: a command confirmed outside any chapter keeps trace and delta."""
    import json

    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    view = started(session, owner)
    tenant_id = view["tenant_id"]
    order = play(session, owner, tenant_id, "order")
    for key in ("reference", "receipt"):
        play(session, owner, tenant_id, key)

    # A person works in the ordinary app: reserve the order outside the story.
    proposal = create_change_proposal(
        session,
        tenant_id,
        "reserve",
        {"commitment_id": order["output"]["commitment_ids"][0]},
        actor_type="human",
    )
    token = json.loads(proposal.input).get("_delivery_review", {}).get("token")
    approve_and_execute_proposal(
        session, tenant_id, proposal.id, review_token=token, confirmed=True
    )

    free = storyline.trace(session, owner.id, tenant_id, free=True)
    kinds = [(item["kind"], item["name"]) for item in free["items"]]
    assert ("propose", "reserve") in kinds and ("confirm", "reserve") in kinds
    assert all(
        item["step_id"] is None and item["chapter"] is None for item in free["items"]
    )
    confirm = next(item for item in free["items"] if item["kind"] == "confirm")
    assert confirm["marker"] is not None

    delta = storyline.delta(session, owner.id, tenant_id, ordinal=confirm["ordinal"])
    assert [event["type"] for event in delta["events"]] and all(
        event["sequence"] > confirm["marker"]["sequence"] for event in delta["events"]
    )
    assert [x["class_id"] for x in delta["exceptions"]["cleared"]] == [
        "outgoing_commitment_at_risk"
    ]
    propose = next(item for item in free["items"] if item["kind"] == "propose")
    with pytest.raises(NotFound):
        storyline.delta(session, owner.id, tenant_id, ordinal=propose["ordinal"])

    # The story still knows where it is, and chapter traces exclude the free play.
    assert storyline.state(session, owner.id, tenant_id)["current_chapter"] == "reserve"
    chapters = storyline.trace(session, owner.id, tenant_id, limit=500)
    assert len(chapters["items"]) > len(free["items"])
    assert all(item["chapter"] for item in chapters["items"] if item["step_id"])


def test_a_chapter_whose_precondition_no_longer_holds_says_what_is_missing(
    session, owner
):
    """FR-011: preconditions name the missing finding and the restart is offered."""
    import json

    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
        run_read_tool,
    )

    view = started(session, owner)
    tenant_id = view["tenant_id"]
    for key in ("order", "reference", "receipt", "reserve", "dispatch"):
        play(session, owner, tenant_id, key)
    invoice = session.get(PlaygroundRun, view["run_id"]).initialization_progress[
        "storyline"
    ]["seed_outputs"]["overdue_invoice"]["document_id"]

    # Free play: the customer pays the old invoice exactly, so nothing is overdue any more.
    context = run_read_tool(
        session, tenant_id, "finance.settlement.context", {"document_id": invoice}
    )
    proposal = create_change_proposal(
        session,
        tenant_id,
        "finance.settlement.apply",
        {
            "expected_revision": context["revision"],
            "document_id": invoice,
            "mode": "payment",
            "amount": "1180.00",
            "allocation_amount": "1180.00",
            "reference": "paid outside the story",
            "effective_at": now().isoformat(),
        },
        actor_type="human",
    )
    approve_and_execute_proposal(session, tenant_id, proposal.id, confirmed=True)
    assert (
        json.loads(session.get(ChangeProposal, proposal.id).output)["mode"] == "payment"
    )

    detail = storyline.chapter_detail(session, owner.id, tenant_id, "explain-hold")
    failing = [check for check in detail["preconditions"] if not check["holds"]]
    assert [(c["kind"], c["name"]) for c in failing] == [
        ("finding_present", "overdue_receivable")
    ]
    assert detail["can_run"] is False
    with pytest.raises(Conflict, match="overdue_receivable"):
        storyline.prepare(
            session.connection(),
            owner.id,
            tenant_id,
            "explain-hold",
            "blocked",
            db_session=session,
        )

    fresh = storyline.restart(
        session,
        owner.id,
        tenant_id,
        request_key="fresh-after-free-play",
        confirmed=True,
    )
    assert fresh["status"] == "active" and fresh["tenant_id"] != tenant_id
    assert storyline.chapter_detail(session, owner.id, fresh["tenant_id"], "order")[
        "can_run"
    ]
