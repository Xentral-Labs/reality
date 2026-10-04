"""A retained backorder decision owns its complete exact reservation batch."""
import json

import pytest
from intake_review_support import explicit_owner
from test_canonical_reservation_boundary import state

from reality.services import backorders, core
from reality.tools import application


def prepare(session, business):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    lines = []
    for index in range(2):
        commitment = core.create_commitment(session, tenant, "customer_delivery", business.company.id,
            business.customer.id, business.item.id, business.location.id, "3", f"2026-10-{10 + index}")
        lines.append({"commitment_id": commitment.id, "quantity": "2"})
    core.record_movement(session, tenant, "receipt", business.item.id, "7", to_location_id=business.location.id)
    values = {"item_id": business.item.id, "location_id": business.location.id, "lines": lines}
    proposal = application.create_change_proposal(session, tenant, "backorders_serve", values)
    return owner, proposal, values


@pytest.mark.parametrize("confirmed", [False, True])
def test_backorder_direct_or_unconfirmed_refuses(session, business, confirmed):
    owner, proposal, values = prepare(session, business)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        if confirmed: backorders.serve_backorders(session, business.tenant.id, **values)
        else: application.approve_and_execute_proposal(session, business.tenant.id, proposal.id,
            confirming_principal=owner, confirmed=False)
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("attack", ["changed", "repeated", "early_commit", "after_write_failure", "sibling_header", "changed_child", "second_child_failure"])
def test_backorder_callback_owns_exact_atomic_batch(session, business, monkeypatch, attack):
    owner, proposal, _ = prepare(session, business)
    before = state(session, business.tenant.id)
    original = backorders.serve_backorders
    child = core.reserve
    calls = 0
    def changed_child(db, tenant, *args, **arguments):
        nonlocal calls
        calls += 1
        if attack == "second_child_failure" and calls == 2: raise RuntimeError("Second actual reservation failed")
        if attack == "changed_child":
            if args: args = (*args[:1], "1", *args[2:])
            else: arguments["quantity"] = "1"
        return child(db, tenant, *args, **arguments)
    if attack in {"changed_child", "second_child_failure"}: monkeypatch.setattr(backorders, "reserve", changed_child)
    def callback(db, tenant, *args, **arguments):
        if attack == "changed":
            if args: args = (*args[:2], [{**row, "quantity": "1"} for row in args[2]], *args[3:])
            else: arguments["lines"] = [{**row, "quantity": "1"} for row in arguments["lines"]]
        if attack == "early_commit": db.commit()
        result = original(db, tenant, *args, **arguments)
        if attack == "repeated": original(db, tenant, *args, **arguments)
        if attack == "after_write_failure": raise RuntimeError("Actual batch failed after writing")
        if attack == "sibling_header": core.create_document(db, tenant, "sales_order", "UNRELATED", business.customer.id, "97", _commit=False)
        return result
    monkeypatch.setattr(backorders, "serve_backorders", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    session.rollback()
    assert state(session, business.tenant.id) == before


def test_backorder_actual_batch_receipt_and_replay(session, business):
    owner, proposal, _ = prepare(session, business)
    receipt = application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    assert len(json.loads(receipt.output)["reservations"]) == 2
    before = state(session, business.tenant.id)
    assert application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True).output == receipt.output
    assert state(session, business.tenant.id) == before
