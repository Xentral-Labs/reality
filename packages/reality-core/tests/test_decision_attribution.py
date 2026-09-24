"""Spec 263: one reader answers which decision caused a change and who settled it."""

from sqlalchemy import event

from reality.db.core import AppUser, ChangeProposal, now, uid
from reality.mcp.auth import create_mcp_access_token, revoke_mcp_access_token
from reality.services.core import create_tenant
from reality.services.decision_attribution import decision_attributions


def _person(session, email: str, display_name: str = "") -> AppUser:
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash="x",
        display_name=display_name,
        status="active",
    )
    session.add(user)
    session.flush()
    return user


def _decision(session, tenant_id: str, **values) -> ChangeProposal:
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=tenant_id,
        type=values.pop("type", "tool:item_create"),
        actor_type=values.pop("actor_type", "agent"),
        status=values.pop("status", "executed"),
        **values,
    )
    session.add(proposal)
    session.flush()
    return proposal


def test_a_signed_in_decider_is_named_as_a_person(session):
    tenant = create_tenant(session, "Person company")
    approver = _person(session, "anna@example.com", "Anna Owner")
    decision = _decision(
        session, tenant.id, decided_at=now(), decided_by_user_id=approver.id
    )

    result = decision_attributions(session, tenant.id, [decision.id])[decision.id]

    assert result["id"] == decision.id
    assert result["tool"] == "item_create"
    assert result["outcome"] == "executed"
    assert result["decided_at"] is not None
    assert result["decider"] == {"kind": "person", "name": "Anna Owner"}


def test_a_person_without_display_name_falls_back_to_the_address(session):
    tenant = create_tenant(session, "Address company")
    approver = _person(session, "nameless@example.com")
    decision = _decision(
        session, tenant.id, decided_at=now(), decided_by_user_id=approver.id
    )

    result = decision_attributions(session, tenant.id, [decision.id])[decision.id]

    assert result["decider"] == {"kind": "person", "name": "nameless@example.com"}


def test_an_mcp_decision_names_the_token_and_its_issuer(session):
    tenant = create_tenant(session, "Token company")
    owner = _person(session, "owner@example.com", "Olga Owner")
    token, _ = create_mcp_access_token(
        session, tenant.id, "Claude Desktop", issued_by_user_id=owner.id
    )
    decision = _decision(
        session, tenant.id, decided_at=now(), decided_via_token_id=token.id
    )

    result = decision_attributions(session, tenant.id, [decision.id])[decision.id]

    assert result["decider"] == {
        "kind": "mcp_token",
        "token_name": "Claude Desktop",
        "token_prefix": token.token_prefix,
        "revoked": False,
        "issuer": "Olga Owner",
    }


def test_a_legacy_token_reads_with_an_unknown_issuer(session):
    tenant = create_tenant(session, "Legacy token company")
    token, _ = create_mcp_access_token(session, tenant.id, "Old agent")
    decision = _decision(
        session, tenant.id, decided_at=now(), decided_via_token_id=token.id
    )

    decider = decision_attributions(session, tenant.id, [decision.id])[decision.id][
        "decider"
    ]

    assert decider["kind"] == "mcp_token"
    assert decider["issuer"] is None


def test_a_revoked_token_still_names_itself_and_says_so(session):
    tenant = create_tenant(session, "Revoked token company")
    owner = _person(session, "revoker@example.com", "Rita Owner")
    token, _ = create_mcp_access_token(
        session, tenant.id, "Retired agent", issued_by_user_id=owner.id
    )
    decision = _decision(
        session, tenant.id, decided_at=now(), decided_via_token_id=token.id
    )
    revoke_mcp_access_token(session, tenant.id, token.id)

    decider = decision_attributions(session, tenant.id, [decision.id])[decision.id][
        "decider"
    ]

    assert decider["token_name"] == "Retired agent"
    assert decider["revoked"] is True
    assert decider["issuer"] == "Rita Owner"


def test_unattributed_and_pending_decisions_read_as_unknown(session):
    tenant = create_tenant(session, "Unknown company")
    before_055 = _decision(session, tenant.id)
    unattended = _decision(session, tenant.id, status="rejected", decided_at=now())
    pending = _decision(session, tenant.id, status="proposed")

    result = decision_attributions(
        session, tenant.id, [before_055.id, unattended.id, pending.id]
    )

    assert result[before_055.id]["decider"] == {"kind": "unknown"}
    assert result[before_055.id]["decided_at"] is None
    assert result[unattended.id]["decider"] == {"kind": "unknown"}
    assert result[unattended.id]["outcome"] == "rejected"
    assert result[pending.id]["decider"] == {"kind": "unknown"}
    assert result[pending.id]["outcome"] == "proposed"


def test_another_companys_decision_token_and_people_are_never_resolved(session):
    tenant = create_tenant(session, "Reading company")
    other = create_tenant(session, "Other company")
    stranger = _person(session, "stranger@example.com", "Stranger One")
    their_token, _ = create_mcp_access_token(
        session, other.id, "Their agent", issued_by_user_id=stranger.id
    )
    theirs = _decision(
        session, other.id, decided_at=now(), decided_via_token_id=their_token.id
    )
    by_person = _decision(
        session, other.id, decided_at=now(), decided_by_user_id=stranger.id
    )
    local = _person(session, "local@example.com", "Local One")
    mine = _decision(session, tenant.id, decided_at=now(), decided_by_user_id=local.id)

    result = decision_attributions(
        session, tenant.id, [theirs.id, by_person.id, mine.id]
    )

    assert set(result) == {mine.id}
    assert result[mine.id]["decider"] == {"kind": "person", "name": "Local One"}
    assert "Stranger One" not in str(result)
    assert "Their agent" not in str(result)


def test_an_empty_request_reads_nothing(session):
    tenant = create_tenant(session, "Empty company")
    statements: list[str] = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        assert decision_attributions(session, tenant.id, []) == {}
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert statements == []


def test_attribution_costs_a_constant_number_of_statements(session):
    tenant = create_tenant(session, "Budget company")
    owner = _person(session, "budget@example.com", "Bea Owner")
    token, _ = create_mcp_access_token(
        session, tenant.id, "Agent", issued_by_user_id=owner.id
    )
    one = [
        _decision(session, tenant.id, decided_at=now(), decided_via_token_id=token.id)
    ]
    many = one + [
        _decision(
            session,
            tenant.id,
            decided_at=now(),
            **(
                {"decided_via_token_id": token.id}
                if index % 2
                else {"decided_by_user_id": owner.id}
            ),
        )
        for index in range(99)
    ]
    counts = []
    for decisions in (one, many):
        statements: list[str] = []

        def capture(
            _connection,
            _cursor,
            statement,
            _parameters,
            _context,
            _many,
            seen=statements,
        ):
            seen.append(statement)

        event.listen(session.bind, "before_cursor_execute", capture)
        try:
            result = decision_attributions(
                session, tenant.id, [decision.id for decision in decisions]
            )
        finally:
            event.remove(session.bind, "before_cursor_execute", capture)
        assert len(result) == len(decisions)
        counts.append(len(statements))

    assert counts[0] <= 3
    assert counts[1] <= 3
