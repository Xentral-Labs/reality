"""Spec 263 US3/US4: every surface that shows a decision names its decider the same way."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from reality.db.core import AppUser, now, uid
from reality.mcp.auth import create_mcp_access_token
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    reject_proposal,
    run_read_tool,
)
from reality.web import api as api_module
from reality.web import app as web_module

app = web_module.app


def api_client(session) -> TestClient:
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def override_session():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = override_session
    return TestClient(app)


def _person(session, email: str, display_name: str) -> AppUser:
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash="x",
        display_name=display_name,
        status="active",
        email_verified_at=now(),
    )
    session.add(user)
    session.commit()
    return user


def _term(session, tenant_id: str, code: str):
    return create_change_proposal(
        session,
        tenant_id,
        "payment_term_create",
        {"code": code, "name": f"Term {code}", "due_days": 14},
    )


def _three_decisions(session, business):
    """One decided by a person, one through a token, one by nobody named."""
    person = _person(session, "anna@example.com", "Anna Owner")
    issuer = _person(session, "olga@example.com", "Olga Owner")
    token, _ = create_mcp_access_token(
        session, business.tenant.id, "Claude Desktop", issued_by_user_id=issuer.id
    )
    by_person = _term(session, business.tenant.id, "P")
    by_token = _term(session, business.tenant.id, "T")
    by_nobody = _term(session, business.tenant.id, "N")
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        by_person.id,
        confirming_principal=Principal(person.id),
    )
    approve_and_execute_proposal(
        session, business.tenant.id, by_token.id, settling_token_id=token.id
    )
    reject_proposal(session, business.tenant.id, by_nobody.id)
    return by_person, by_token, by_nobody, token


PERSON = {"kind": "person", "name": "Anna Owner"}


def _token_decider(token) -> dict:
    return {
        "kind": "mcp_token",
        "token_name": "Claude Desktop",
        "token_prefix": token.token_prefix,
        "revoked": False,
        "issuer": "Olga Owner",
    }


# --- US3: the history register and one decision (FR-004, FR-007, FR-008) --------


def test_history_names_every_kind_of_decider(session, business):
    by_person, by_token, by_nobody, token = _three_decisions(session, business)
    client = api_client(session)
    try:
        items = client.get(
            f"/api/tenants/{business.tenant.id}/change-proposals",
            params={"status": "history"},
        ).json()["items"]
    finally:
        app.dependency_overrides.clear()

    deciders = {item["id"]: item["decider"] for item in items}
    assert deciders[by_person.id] == PERSON
    assert deciders[by_token.id] == _token_decider(token)
    assert deciders[by_nobody.id] == {"kind": "unknown"}
    # The earlier name-only field stays for clients that already read it.
    assert {item["id"]: item["decided_by"] for item in items}[by_person.id] == (
        "Anna Owner"
    )


def test_one_decision_opens_with_its_decider_whatever_its_status(session, business):
    by_person, by_token, by_nobody, token = _three_decisions(session, business)
    pending = _term(session, business.tenant.id, "W")
    client = api_client(session)
    try:
        reviews = {
            proposal.id: client.get(
                f"/api/tenants/{business.tenant.id}/change-proposals/"
                f"{proposal.id}/review"
            ).json()
            for proposal in (by_person, by_token, by_nobody, pending)
        }
    finally:
        app.dependency_overrides.clear()

    assert reviews[by_person.id]["decider"] == PERSON
    assert reviews[by_token.id]["decider"] == _token_decider(token)
    assert reviews[by_token.id]["decided_at"] is not None
    assert reviews[by_nobody.id]["status"] == "rejected"
    assert reviews[by_nobody.id]["decider"] == {"kind": "unknown"}
    assert reviews[pending.id]["decider"] == {"kind": "unknown"}
    assert reviews[pending.id]["decided_at"] is None


def test_the_agent_status_read_states_the_decision(session, business):
    _, by_token, _, token = _three_decisions(session, business)

    status = run_read_tool(
        session,
        business.tenant.id,
        "proposal_execution_status",
        {"proposal_id": by_token.id},
    )

    assert status["decision"]["id"] == by_token.id
    assert status["decision"]["outcome"] == "executed"
    assert status["decision"]["decider"] == _token_decider(token)


# --- US4: activities name the decision behind each change (FR-010, FR-011) ------


def test_an_activity_names_the_decision_that_caused_it(session, business):
    from reality.services.core import timeline_activity

    by_person, by_token, _, token = _three_decisions(session, business)

    events = timeline_activity(session, business.tenant.id, hours=0)["events"]

    decided = {
        event["action_id"]: event["decision"] for event in events if event["action_id"]
    }
    assert decided[by_person.id]["decider"] == PERSON
    assert decided[by_token.id]["decider"] == _token_decider(token)
    assert decided[by_token.id]["tool"] == "payment_term_create"
    undecided = [event for event in events if not event["action_id"]]
    # The fixture's own records were entered without a decision and claim none.
    assert undecided and all(event["decision"] is None for event in undecided)
