"""A question asked now and answered later (spec 236).

The thing most likely to go wrong here is a refusal arriving minutes late as a
failed job instead of immediately as an answer to the asker. Only cost may be
deferred; a judgement about the question may not. Most of this file exists to hold
that line.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from reality.db.analytics import AnalysisRequest
from reality.db.core import AppUser, TenantMembership, now, uid
from reality.domain.traversal import Traversal
from reality.services import core
from reality.services.analytics import requests as analysis_requests
from reality.services.analytics.requests import SIZE_REFUSALS, ask, collect, listing
from reality.services.analytics.traversal import TraversalRefused


def member(session, tenant_id, role="member"):
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.flush()
    session.add(
        TenantMembership(
            id=uid("tmb"),
            tenant_id=tenant_id,
            user_id=user.id,
            role=role,
            status="active",
        )
    )
    session.flush()
    return user


def question(**overrides):
    payload = {
        "from": "order",
        "as": "o",
        "measures": ["order_count"],
        "group_by": [{"field": "o.currency"}],
    }
    payload.update(overrides)
    return Traversal.model_validate(payload)


@pytest.fixture
def asker(session, business):
    return member(session, business.tenant.id)


def test_a_question_within_the_budget_is_answered_in_the_request(
    session, business, asker
):
    """Nobody waits for something that was already fast."""
    core.create_document(
        session,
        business.tenant.id,
        "sales_order",
        "ORD-1",
        business.customer.id,
        "10",
        document_date="2026-08-01",
    )
    outcome = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-immediate",
    )
    assert outcome["state"] == "answered"
    assert outcome["answer"].rows
    assert session.query(AnalysisRequest).count() == 0


@pytest.mark.parametrize(
    "payload, code",
    [
        ({"from": "no_such_node", "measures": ["order_count"]}, "unknown_node"),
        ({"from": "order", "measures": ["no_such_measure"]}, "unknown_measure"),
        (
            {
                "from": "order",
                "measures": ["stated_order_amount"],
                "follow": [{"edge": "contains", "as": "l"}],
                "group_by": [{"field": "l.sku"}],
            },
            "fan_out",
        ),
    ],
)
def test_a_refusal_about_the_question_arrives_at_request_time(
    session, business, asker, payload, code
):
    """A judgement about the question is never deferred, only cost is."""
    body = {"as": "o", **payload}
    with pytest.raises(TraversalRefused) as refusal:
        ask(
            session,
            business.tenant.id,
            question=Traversal.model_validate(body),
            user_id=asker.id,
            request_id=f"req-{code}",
        )
    assert refusal.value.code == code
    assert refusal.value.code not in SIZE_REFUSALS
    assert session.query(AnalysisRequest).count() == 0


def test_only_the_size_refusals_defer(session, business, asker, monkeypatch):
    """The set that defers is exactly the set that is refused today."""
    for code in ("fan_out", "unit_mismatch", "not_additive", "unknown_property"):
        assert code not in SIZE_REFUSALS
    assert SIZE_REFUSALS == {"finance_limit", "inventory_limit", "position_limit"}


def _defer(monkeypatch, code="finance_limit"):
    def refuse(*_args, **_kwargs):
        raise TraversalRefused("This company is too large for one request.", code)

    monkeypatch.setattr(analysis_requests, "run_traversal", refuse)


def test_a_question_over_the_limit_is_accepted_for_the_worker(
    session, business, asker, monkeypatch
):
    _defer(monkeypatch)
    outcome = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-deferred",
    )
    assert outcome["state"] == "accepted"
    accepted = outcome["request"]
    assert accepted["state"] == "accepted"
    assert accepted["deferred_reason"] == "finance_limit"
    # The asker is told which limit sent this to the worker, not left to guess.
    assert "too large" in accepted["message"]

    row = session.get(AnalysisRequest, accepted["id"])
    assert row.run_id is not None
    assert row.question == question().model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    assert row.model_version
    assert row.expires_at > datetime.now(UTC)


def test_the_same_request_twice_finds_its_own_run(
    session, business, asker, monkeypatch
):
    _defer(monkeypatch)
    first = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-once",
    )["request"]
    second = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-once",
    )["request"]
    assert first["id"] == second["id"]
    assert session.query(AnalysisRequest).count() == 1


def test_the_worker_answers_and_the_asker_collects(
    session, business, asker, monkeypatch
):
    core.create_document(
        session,
        business.tenant.id,
        "sales_order",
        "ORD-2",
        business.customer.id,
        "10",
        document_date="2026-08-01",
    )
    _defer(monkeypatch)
    accepted = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-collect",
    )["request"]
    monkeypatch.undo()

    from reality.jobs.handlers.analysis import AnalysisConfig, run_requested_analysis
    from reality.jobs.registry import JobContext

    result = run_requested_analysis(
        session,
        JobContext(business.tenant.id, asker.id, "run-1", None, datetime.now(UTC)),
        AnalysisConfig(analysis_request_id=accepted["id"]),
    )
    assert result.counts["answered"] == 1
    assert result.references[0].record_type == "analysis_request"

    answer = collect(session, business.tenant.id, accepted["id"], user_id=asker.id)
    assert answer["state"] == "ready"
    assert answer["rows"]
    # The answer is returned with what was asked and when, so nothing downstream
    # can mistake it for what is true now.
    assert answer["question"]["from"] == "order"
    assert answer["answered_at"]
    assert answer["model_version"]


def test_a_question_that_still_cannot_be_answered_says_why_on_the_row(
    session, business, asker, monkeypatch
):
    _defer(monkeypatch)
    accepted = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-fails",
    )["request"]

    # The handler resolves the traversal from its own module, so the refusal it
    # must survive is patched where the handler looks for it.
    from reality.services.analytics import traversal as traversal_module

    def refuse(*_args, **_kwargs):
        raise TraversalRefused("Still too large.", "finance_limit")

    monkeypatch.setattr(traversal_module, "run_traversal", refuse)

    from reality.jobs.handlers.analysis import AnalysisConfig, run_requested_analysis
    from reality.jobs.registry import JobContext

    result = run_requested_analysis(
        session,
        JobContext(business.tenant.id, asker.id, "run-2", None, datetime.now(UTC)),
        AnalysisConfig(analysis_request_id=accepted["id"]),
    )
    # The run succeeded: it did what it was for. The question did not.
    assert result.counts["refused"] == 1
    answer = collect(session, business.tenant.id, accepted["id"], user_id=asker.id)
    assert answer["state"] == "failed"
    assert answer["failure_code"] == "finance_limit"


def test_access_is_checked_again_when_the_worker_runs(
    session, business, asker, monkeypatch
):
    """The minutes between asking and running are when access changes."""
    _defer(monkeypatch)
    accepted = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-removed",
    )["request"]
    monkeypatch.undo()

    from sqlalchemy import select as sa_select

    membership = session.scalar(
        sa_select(TenantMembership).where(TenantMembership.user_id == asker.id)
    )
    membership.status = "removed"
    session.flush()

    from reality.jobs.handlers.analysis import AnalysisConfig, run_requested_analysis
    from reality.jobs.registry import JobContext, JobError

    with pytest.raises(JobError) as error:
        run_requested_analysis(
            session,
            JobContext(business.tenant.id, asker.id, "run-3", None, datetime.now(UTC)),
            AnalysisConfig(analysis_request_id=accepted["id"]),
        )
    assert error.value.code == "not_authorized"


def test_a_stranger_cannot_request_or_collect(session, business, asker, monkeypatch):
    other_tenant = core.create_tenant(session, "Somebody Else GmbH")
    stranger = member(session, other_tenant.id)
    _defer(monkeypatch)
    accepted = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-private",
    )["request"]
    with pytest.raises(core.NotFound):
        collect(session, business.tenant.id, accepted["id"], user_id=stranger.id)
    with pytest.raises(core.NotFound):
        ask(
            session,
            business.tenant.id,
            question=question(),
            user_id=stranger.id,
            request_id="req-stranger",
        )


def test_an_uncollected_answer_does_not_linger(session, business, asker, monkeypatch):
    _defer(monkeypatch)
    accepted = ask(
        session,
        business.tenant.id,
        question=question(),
        user_id=asker.id,
        request_id="req-expiring",
    )["request"]
    row = session.get(AnalysisRequest, accepted["id"])
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.flush()

    assert analysis_requests.expire(session, business.tenant.id) == 1
    assert listing(session, business.tenant.id, user_id=asker.id)["items"] == []


# --- FR-008: requesting as a declared, confirmed command ------------------------


def propose_and_confirm(session, tenant_id, principal, arguments):
    from reality.services.analytics.reports import caller
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    with caller(principal):
        proposal = create_change_proposal(
            session, tenant_id, "graph.requests.create", arguments
        )
        executed = approve_and_execute_proposal(
            session,
            tenant_id,
            proposal.id,
            confirming_principal=principal,
        )
    return proposal, executed


def test_an_agent_proposes_a_request_and_a_person_confirms_it(
    session, business, asker, monkeypatch
):
    """Requesting writes something, so it is a proposal, not a read."""
    from reality.services.memberships import Principal

    _defer(monkeypatch)
    proposal, executed = propose_and_confirm(
        session,
        business.tenant.id,
        Principal(asker.id),
        {
            "question": question().model_dump(mode="json", by_alias=True),
            "request_id": "agent-1",
        },
    )
    assert proposal.status == "executed" or executed.status == "executed"
    outcome = json.loads(executed.output)
    assert outcome["state"] == "accepted"
    assert session.query(AnalysisRequest).count() == 1


def test_the_proposal_never_shows_the_question_to_the_company(
    session, business, asker, monkeypatch
):
    """A proposal record is company-visible; the question asked is the asker's."""
    from reality.services.analytics.reports import caller
    from reality.services.memberships import Principal
    from reality.tools.application import create_change_proposal

    _defer(monkeypatch)
    with caller(Principal(asker.id)):
        proposal = create_change_proposal(
            session,
            business.tenant.id,
            "graph.requests.create",
            {
                "question": question().model_dump(mode="json", by_alias=True),
                "request_id": "agent-sealed",
            },
        )
    stored = json.loads(proposal.input)
    assert set(stored) == {"requested_analysis"}
    assert "order" not in proposal.input


def test_a_question_the_model_cannot_express_is_refused_when_proposed(
    session, business, asker
):
    """Planning happens at proposal time, so the refusal reaches whoever asked."""
    from reality.services.analytics.reports import caller
    from reality.services.memberships import Principal
    from reality.tools.application import create_change_proposal

    with caller(Principal(asker.id)), pytest.raises(TraversalRefused) as refusal:
        create_change_proposal(
            session,
            business.tenant.id,
            "graph.requests.create",
            {
                "question": {
                    "from": "no_such_node",
                    "as": "o",
                    "measures": ["order_count"],
                },
                "request_id": "agent-bad",
            },
        )
    assert refusal.value.code == "unknown_node"


def test_requesting_cannot_be_executed_without_a_confirmation(session, business):
    from reality.services.core import InvalidOperation
    from reality.tools.application import TOOLS

    with pytest.raises(InvalidOperation, match="confirmation"):
        TOOLS["graph.requests.create"].handler(session, business.tenant.id, {})
