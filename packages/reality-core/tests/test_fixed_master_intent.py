"""Spec 356 FR-003: fixed definitions cannot grant different master-data intent."""

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import func, select

from reality.db.core import Party, SourceRecord
from reality.services import core
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


@pytest.mark.parametrize("attack", ["replace_intent", "repeat_effect"])
def test_compact_definition_cannot_accept_changed_master_callbacks(
    session, monkeypatch, attack
):
    tenant = core.create_tenant(session, "Fixed intent proof")
    principal = explicit_owner(session, tenant.id)
    proposal = create_change_proposal(session, tenant.id, "demo_seed", {})
    original = core.create_party

    def changed(db, company, name, party_type, **arguments):
        if attack == "replace_intent":
            name = "Different unconfirmed definition partner"
        if attack == "repeat_effect":
            original(db, company, name, party_type, **arguments)
        return original(db, company, name, party_type, **arguments)

    monkeypatch.setattr(core, "create_party", changed)
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session,
            tenant.id,
            proposal.id,
            confirming_principal=principal,
            confirmed=True,
        )
    assert (
        refused.value.code
        == {
            "replace_intent": "intake_review_invalid",
            "repeat_effect": "intake_approval_required",
        }[attack]
    )
    for model in [Party, SourceRecord]:
        assert (
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.tenant_id == tenant.id)
            )
            == 0
        )
