"""Spec 356: the existing merge decision owns its duplicate lifecycle effect."""

import inspect

import pytest
from intake_review_support import explicit_owner, reviewed_create_party
from sqlalchemy import select
from test_master_lifecycle_decisions import snapshot

from reality.db.core import PartyMerge
from reality.domain.intake import canonical_json
from reality.services import core, party_merges
from reality.tools import application


def state(session, tenant):
    return snapshot(session, tenant) | {"merges": canonical_json([
        {column.name: getattr(row, column.name) for column in PartyMerge.__table__.columns}
        for row in session.scalars(select(PartyMerge).where(PartyMerge.tenant_id == tenant).order_by(PartyMerge.id))
    ])}


@pytest.mark.parametrize("attack", ["direct", "changed", "repeated", "early_commit", "post_write_failure", "sibling_header", "changed_lifecycle"])
def test_actual_merge_confirmation_refuses_unowned_or_partial_effects(session, business, monkeypatch, attack):
    duplicate = reviewed_create_party(session, business.tenant.id, "Actual duplicate", "customer")
    values = {"duplicate_party_id": duplicate.id, "surviving_party_id": business.customer.id, "reason": "Stated duplicate evidence"}
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, "party_merge", values)
    before = state(session, business.tenant.id)
    original = party_merges.merge_party

    def callback(*args, **kwargs):
        bound = inspect.signature(original).bind(*args, **kwargs)
        if attack == "changed":
            bound.arguments["reason"] = "Unreviewed replacement reason"
            return original(*bound.args, **bound.kwargs)
        if attack == "early_commit":
            session.commit()
        if attack == "sibling_header":
            core.create_document(session, business.tenant.id, "sales_order", "UNRELATED-MERGE", business.customer.id, "79")
        result = original(*args, **kwargs)
        if attack == "repeated":
            original(*args, **kwargs)
        if attack == "post_write_failure":
            raise RuntimeError("Actual post-write merge failure")
        return result

    if attack == "changed_lifecycle":
        actual_lifecycle = party_merges.set_master_data_active

        def lifecycle(*args, **kwargs):
            bound = inspect.signature(actual_lifecycle).bind(*args, **kwargs)
            bound.arguments["is_active"] = True
            return actual_lifecycle(*bound.args, **bound.kwargs)

        monkeypatch.setattr(party_merges, "set_master_data_active", lifecycle)
    else:
        monkeypatch.setattr(party_merges, "merge_party", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        if attack == "direct":
            original(session, business.tenant.id, **values)
        else:
            application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    session.rollback()
    assert state(session, business.tenant.id) == before
