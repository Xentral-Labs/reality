import json

import pytest
from sqlalchemy import event
from test_mcp_read_contract import order, read

from reality.db.core import ChangeProposal, now, uid
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_tenant,
    emit_business_event,
    record_movement,
)
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
    run_read_tool,
)


def executed_reservation(session, business, number="DECISION-ORDER"):
    _, document, _, commitments = order(session, business, number)
    commitment = next(c for c in commitments if c.type == "customer_delivery")
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "reserve",
        {"commitment_id": commitment.id, "quantity": "1"},
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    return document, commitment, proposal


def discover(session, business, document=None, **kwargs):
    return read(
        session,
        business,
        "business_records_discover",
        family="executed_decision",
        **({"document_id": document.id} if document else {}),
        **kwargs,
    )


def test_discover_executed_order_decision_then_verify_without_replay(session, business):
    document, commitment, proposal = executed_reservation(session, business)
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        action_id=proposal.id,
    )
    other_document, _, other = executed_reservation(
        session, business, "OTHER-SAME-ITEM"
    )
    other_document.number = document.number
    session.flush()
    assert other_document.id != document.id
    pending = create_change_proposal(
        session,
        business.tenant.id,
        "reserve",
        {"commitment_id": commitment.id, "quantity": "1"},
    )
    emit_business_event(
        session,
        business.tenant.id,
        "test.nonexecuted",
        "commitment",
        commitment.id,
        {},
        action_id=pending.id,
    )
    page = discover(session, business, document)
    assert [row["proposal_id"] for row in page["records"]] == [proposal.id]
    row = page["records"][0]
    assert row["id"] == proposal.id
    assert row["status"] == "executed"
    assert row["tool"] == "reserve"
    assert row["association_scope"] == "retained_execution_events"
    assert row["review_read"] == "proposal_review"
    assert row["verification_read"] == "proposal_execution_status"
    assert set(row) == {
        "id",
        "proposal_id",
        "tool",
        "status",
        "created_at",
        "decided_at",
        "review_read",
        "verification_read",
        "association_scope",
    }
    assert page["metadata"]["decision_coverage"]["historical_completeness"] == "unknown"
    assert page["metadata"]["persistence"]["business_writes"] is False
    assert other.id not in json.dumps(page)
    status = read(
        session, business, row["verification_read"], proposal_id=row["proposal_id"]
    )
    assert status["status"] == "executed"
    assert status["receipt"]["commitment_id"] == commitment.id
    assert (
        read(session, business, row["review_read"], proposal_id=row["proposal_id"])[
            "id"
        ]
        == proposal.id
    )
    assert (
        discover(session, business, document, response_format="legacy")
        == page["records"]
    )
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "business_discover",
            {"family": "executed_decision", "document_id": document.id},
        )
        == page["records"]
    )


def test_decision_pages_scope_exact_references_privacy_and_no_writes(session, business):
    document, commitment, first = executed_reservation(session, business)
    second = create_change_proposal(
        session,
        business.tenant.id,
        "reserve",
        {"commitment_id": commitment.id, "quantity": "1"},
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        second.id,
        review_token=json.loads(second.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    document.number = "DIRTY-LOCAL-LABEL"
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lstrip().upper())

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        page = discover(session, business, document, limit=1)
        final = discover(
            session, business, document, limit=1, cursor=page["next_cursor"]
        )
        legacy = discover(session, business, document, response_format="legacy")
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert {r["id"] for r in page["records"] + final["records"]} == {
        first.id,
        second.id,
    }
    assert len(legacy) == 2
    assert final["summary"]["selection_record_count"] is None
    assert not any(s.startswith(("INSERT", "UPDATE", "DELETE")) for s in statements)
    _, another, _, _ = order(session, business, "OTHER")
    with pytest.raises(InvalidOperation):
        discover(session, business, another, cursor=page["next_cursor"])
    assert (
        discover(session, business, document, record_id=first.id, query="no-match")[
            "records"
        ][0]["id"]
        == first.id
    )
    assert discover(session, business, document, query="no-match")["records"] == []
    assert (
        discover(session, business, query="reserve")["records"][0]["association_scope"]
        == "retained_executed_decisions"
    )
    foreign = create_tenant(session, "Other company")
    with pytest.raises(NotFound):
        run_read_tool(
            session,
            foreign.id,
            "business_discover",
            {"family": "executed_decision", "document_id": document.id},
        )
    with pytest.raises(NotFound):
        run_read_tool(
            session,
            foreign.id,
            "business_discover",
            {"family": "executed_decision", "record_id": first.id},
        )
    with pytest.raises(InvalidOperation):
        read(
            session,
            business,
            "business_records_discover",
            family="item",
            document_id=document.id,
        )


def test_shortest_membership_and_no_effect_do_not_invent_associations(
    session, business
):
    document, commitment, proposal = executed_reservation(session, business)
    _, other_document, _, _ = order(session, business, "OTHER")
    # Fixture: an inconsistent longer fallback cannot override the explicit line.
    commitment.document_id = other_document.id
    no_effect = ChangeProposal(
        id=uid("act"),
        tenant_id=business.tenant.id,
        type="tool:reserve",
        status="executed",
        input=json.dumps({"commitment_id": commitment.id, "token": "secret"}),
        output="{}",
        created_at=now(),
    )
    session.add(no_effect)
    session.flush()
    assert discover(session, business, other_document)["records"] == []
    assert [r["id"] for r in discover(session, business, document)["records"]] == [
        proposal.id
    ]
    assert "secret" not in json.dumps(discover(session, business))
    commitment.document_line_id = None
    session.flush()
    assert discover(session, business, document)["records"] == []
    assert [
        r["id"] for r in discover(session, business, other_document)["records"]
    ] == [proposal.id]


@pytest.mark.parametrize("status", ["proposed", "rejected", "failed", "executing"])
def test_nonexecuted_states_are_excluded_even_with_exact_events(
    session, business, status
):
    document, _, proposal = executed_reservation(session, business)
    proposal.status = status  # Fixture: retained lifecycle is authoritative.
    session.flush()
    assert discover(session, business, document)["records"] == []
    with pytest.raises(NotFound):
        discover(session, business, document, record_id=proposal.id)


@pytest.mark.parametrize("kind", ["document", "document_line", "commitment"])
def test_explicit_direct_member_event_and_tenant_collision(session, business, kind):
    document, commitment, proposal = executed_reservation(session, business)
    member = {
        "document": document.id,
        "document_line": commitment.document_line_id,
        "commitment": commitment.id,
    }[kind]
    emit_business_event(
        session,
        business.tenant.id,
        "test.explicit_effect",
        kind,
        member,
        {},
        action_id=proposal.id,
    )
    foreign = create_tenant(session, "Foreign company")
    collision = ChangeProposal(
        id=proposal.id,
        tenant_id=foreign.id,
        type="tool:secret_tool",
        status="executed",
        input="{}",
        output="{}",
        created_at=now(),
    )
    session.add(collision)
    session.flush()
    emit_business_event(
        session, foreign.id, "test.foreign", kind, member, {}, action_id=collision.id
    )
    page = discover(session, business, document)
    assert len(page["records"]) == 1
    assert page["records"][0]["tool"] == "reserve"
    assert "secret_tool" not in json.dumps(page)
