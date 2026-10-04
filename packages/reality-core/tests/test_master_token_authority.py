"""Spec 356 FR-003: canonical masters recheck the current confirming token."""

import json

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import func, select

from reality.db.core import Party, now
from reality.mcp.auth import create_mcp_access_token
from reality.services import core
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


@pytest.mark.parametrize("change", ["revoke", "remove_confirmation_permission"])
def test_master_effect_refuses_token_authority_changed_after_dispatch(
    session, monkeypatch, change
):
    tenant = core.create_tenant(session, "Current token proof")
    owner = explicit_owner(session, tenant.id)
    token, _ = create_mcp_access_token(
        session, tenant.id, "Confirmed master client", issued_by_user_id=owner.user_id
    )
    proposal = create_change_proposal(
        session,
        tenant.id,
        "party_create",
        {
            "records": [
                {
                    "name": "Exact token partner",
                    "type": "customer",
                    "roles": ["customer"],
                }
            ]
        },
    )
    original = core.create_party

    def changed(*args, **kwargs):
        if change == "revoke":
            token.revoked_at = now()
        else:
            token.allowed_tools = json.dumps(["inventory_read"])
        session.flush()
        return original(*args, **kwargs)

    monkeypatch.setattr(core, "create_party", changed)
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(
            session, tenant.id, proposal.id, settling_token_id=token.id, confirmed=True
        )
    assert refused.value.code == "intake_approval_required"
    assert (
        session.scalar(
            select(func.count()).select_from(Party).where(Party.tenant_id == tenant.id)
        )
        == 0
    )
