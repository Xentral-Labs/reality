"""Reviewed delivery-specific holds retain scope and attributable effects."""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from unified_fixtures import delivery_fixture

from reality.db.core import BusinessEvent
from reality.services.core import (
    InvalidOperation,
    NotFound,
    active_commitment_hold,
    active_party_delivery_hold,
    active_reserved,
    create_tenant,
    hold_commitment,
    hold_party_delivery,
    release_commitment_hold,
    reserve,
    stock_at,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.services.delivery_reads import delivery_case
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def confirm(session, tid, proposal):
    return approve_and_execute_proposal(
        session,
        tid,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


def prepare(session, tid, cid, tool="commitment_hold", request="hold", **extra):
    args = {
        "commitment_id": cid,
        **(
            {"reason_code": "manual_review", "note": "Check address"}
            if tool == "commitment_hold"
            else {}
        ),
        **extra,
    }
    return prepare_delivery_action(session, tid, tool, args, request_id=request)


def test_hold_release_review_effects_and_party_scope(session, business):
    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    reserve(session, tid, cid, "4")
    proposal = prepare(session, tid, cid)
    assert active_commitment_hold(session, tid, cid) is None
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, tid, proposal.id)
    confirm(session, tid, proposal)
    confirm(session, tid, proposal)
    own = active_commitment_hold(session, tid, cid)
    assert own.note == "Check address"
    assert (
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tid, BusinessEvent.action_id == proposal.id
            )
        )
        == 1
    )
    with pytest.raises(InvalidOperation, match="hold"):
        reserve(session, tid, cid, "1")
    hold_party_delivery(
        session, tid, business.customer.id, "credit_check", "Customer-wide"
    )
    case = delivery_case(session, tid, cid)
    assert {row["scope"] for row in case["case"]["blockers"]} == {"commitment", "party"}
    assert {row["note"] for row in case["case"]["blockers"]} == {
        "Check address",
        "Customer-wide",
    }
    release = prepare(session, tid, cid, "commitment_hold_release", "release")
    assert active_commitment_hold(session, tid, cid)
    confirm(session, tid, release)
    assert active_commitment_hold(session, tid, cid) is None
    assert active_party_delivery_hold(session, tid, business.customer.id)
    assert stock_at(session, tid, business.item.id, business.location.id) == 20
    assert active_reserved(session, tid, business.item.id, business.location.id) == 4
    assert Decimal(delivery_case(session, tid, cid)["case"]["open"]) == 12
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "verified"
    )
    assert (
        delivery_proposal_detail(session, tid, release.id)["verification"] == "verified"
    )


def test_stale_same_reason_replacement_invalidates_release(session, business):
    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    hold_commitment(session, tid, cid, "manual_review")
    proposal = prepare(session, tid, cid, "commitment_hold_release", "stale")
    release_commitment_hold(session, tid, cid)
    replacement = hold_commitment(session, tid, cid, "manual_review")
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, tid, proposal)
    assert proposal.status == "proposed"
    assert active_commitment_hold(session, tid, cid).id == replacement.id


@pytest.mark.parametrize("tool", ["commitment_hold", "commitment_hold_release"])
def test_hold_event_recovery_never_reexecutes(session, business, tool):
    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    if tool.endswith("release"):
        hold_commitment(session, tid, cid, "manual_review")
    proposal = prepare(session, tid, cid, tool)
    proposal.status = "executing"
    session.commit()
    if tool.endswith("release"):
        release_commitment_hold(session, tid, cid, action_id=proposal.id)
    else:
        hold_commitment(
            session, tid, cid, "manual_review", "Check address", action_id=proposal.id
        )
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare(
            session,
            tid,
            cid,
            "commitment_hold_release"
            if tool == "commitment_hold"
            else "commitment_hold",
            request="conflict",
        )
    detail = reconcile_delivery(session, tid, proposal.id)
    assert detail["status"] == "executed"
    assert detail["verification"] == "verified"
    assert reconcile_delivery(session, tid, proposal.id)["receipt"] == detail["receipt"]
    assert (
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tid, BusinessEvent.action_id == proposal.id
            )
        )
        == 1
    )


def test_hold_invalid_foreign_noop_and_chat_review(session, business):
    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    for invalid in [{"reason_code": "invented"}, {"reason_code": []}, {"note": None}]:
        with pytest.raises(InvalidOperation):
            prepare(session, tid, cid, **invalid)
    with pytest.raises(InvalidOperation):
        prepare(session, tid, cid, "commitment_hold_release")
    other = create_tenant(session, "Other")
    with pytest.raises(NotFound):
        prepare(session, other.id, cid)
    proposal = create_change_proposal(
        session,
        tid,
        "commitment_hold",
        {"commitment_id": cid, "reason_code": "manual_review"},
    )
    assert "_delivery_review" in json.loads(proposal.input)
    confirm(session, tid, proposal)
    with pytest.raises(InvalidOperation):
        prepare(session, tid, cid, request="already-held")
    proposal.output = json.dumps(
        {"records": [{"family": "commitment_hold", "id": "wrong"}]}
    )
    session.commit()
    assert (
        delivery_proposal_detail(session, tid, proposal.id)["verification"]
        == "unresolved"
    )


def test_hold_http_round_trip_and_practice_policy(session, business):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{tid}"
            for tool in ["commitment_hold", "commitment_hold_release"]:
                args = {"commitment_id": cid}
                if tool == "commitment_hold":
                    args.update(reason_code="other", note="Original <note>")
                response = client.post(
                    f"{base}/delivery-actions/prepare",
                    json={"tool": tool, "arguments": args, "request_id": tool},
                )
                assert response.status_code == 200, response.text
                proposed = response.json()
                response = client.post(
                    f"{base}/change-proposals/{proposed['id']}/approve",
                    json={
                        "confirmed": True,
                        "review_token": proposed["review"]["token"],
                    },
                )
                assert response.status_code == 200, response.text
                assert (
                    client.get(f"{base}/delivery-actions/{proposed['id']}").json()[
                        "verification"
                    ]
                    == "verified"
                )
    finally:
        app.dependency_overrides.clear()
    from reality.db.core import Tenant
    from reality.services.core import uid

    practice = Tenant(id=uid("ten"), name="Isolated practice", purpose="playground")
    session.add(practice)
    session.commit()
    with pytest.raises(InvalidOperation, match="practice"):
        prepare(session, practice.id, cid, request="practice")


def test_release_recovers_exact_plural_hold_set(session, business):
    from reality.db.core import CommitmentHold
    from reality.services.core import uid

    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    first = hold_commitment(session, tid, cid, "manual_review", "First")
    # Historical rows can contain multiple own holds; the current service prevents new duplicates.
    second = CommitmentHold(
        id=uid("hld"),
        tenant_id=tid,
        commitment_id=cid,
        reason_code="other",
        note="Historical",
        created_by="human",
    )
    session.add(second)
    session.commit()
    proposal = prepare(session, tid, cid, "commitment_hold_release")
    saved = json.loads(proposal.input)["_delivery_review"]
    assert saved["effect"] == {"holds_released": "2"}
    assert {row["id"] for row in saved["state"]["holds"]} == {first.id, second.id}
    proposal.status = "executing"
    session.commit()
    release_commitment_hold(session, tid, cid, action_id=proposal.id)
    result = reconcile_delivery(session, tid, proposal.id)
    assert result["verification"] == "verified"
    assert {row["id"] for row in result["receipt"]["records"]} == {first.id, second.id}


def test_hold_confirmation_rechecks_actor_membership(session, business):
    from types import SimpleNamespace

    tid = business.tenant.id
    cid = delivery_fixture(session, business).commitment.id
    proposal = prepare(session, tid, cid)
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            tid,
            proposal.id,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirmed=True,
            confirming_principal=SimpleNamespace(
                user_id="missing-user", is_platform_admin=False
            ),
        )
    assert active_commitment_hold(session, tid, cid) is None
