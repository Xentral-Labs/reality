"""Spec 356: authored setup grants no new lifecycle or merge authority."""

import pytest
from intake_review_support import reviewed_create_party
from test_current_fixed_setup_authority import fresh_company
from test_party_merge_decision_boundary import state

from reality.services import core, party_merges
from reality.services.intake import _invoke
from reality.tools import application


@pytest.mark.parametrize("tool", ["demo_seed", "normal_month"])
@pytest.mark.parametrize("operation", ["set_master_data_active", "merge_party"])
def test_fixed_profile_cannot_borrow_the_new_lifecycle_or_merge_family(
    session, monkeypatch, tool, operation
):
    tenant, owner, _ = fresh_company(session)
    duplicate = reviewed_create_party(session, tenant.id, "Actual unrelated duplicate", "customer")
    survivor = reviewed_create_party(session, tenant.id, "Actual unrelated survivor", "customer")
    proposal = application.create_change_proposal(session, tenant.id, tool, {})
    before = state(session, tenant.id)

    def callback(*args, **kwargs):
        if operation == "merge_party":
            _invoke(operation, party_merges.merge_party, session, tenant.id,
                    duplicate_party_id=duplicate.id, surviving_party_id=survivor.id,
                    reason="Unrelated reviewed-family effect", _commit=False)
        else:
            _invoke(operation, core.set_master_data_active, session, tenant.id,
                    model="party", record_id=duplicate.id, is_active=False, _commit=False)
        pytest.fail("The authored profile borrowed an unrelated canonical family.")

    if tool == "demo_seed":
        monkeypatch.setattr(application, "ensure_demo", callback)
    else:
        monkeypatch.setattr(application, "run_normal_month", callback)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(session, tenant.id, proposal.id,
            confirming_principal=owner, confirmed=True)
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, tenant.id) == before
