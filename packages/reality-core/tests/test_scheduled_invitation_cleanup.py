from datetime import timedelta

import pytest
from sqlalchemy import select

from reality.db.core import CompanyInvitation, now, uid
from reality.services.core import create_tenant
from reality.services.notifications import cleanup_terminal_invitations


def invitation(session, tenant_id, actor_id, *, old=True, status="revoked"):
    row = CompanyInvitation(
        id=uid("inv"),
        tenant_id=tenant_id,
        invited_by_user_id=actor_id,
        normalized_email=f"{uid('mail')}@example.test",
        status=status,
        expires_at=now(),
        terminal_at=now() - timedelta(days=91 if old else 89),
    )
    session.add(row)
    return row


def test_cleanup_batch_scope_and_retention(session, business, scheduled_owner):
    second = create_tenant(session, "Second company")
    other = invitation(session, second.id, scheduled_owner.id)
    recent = invitation(session, business.tenant.id, scheduled_owner.id, old=False)
    pending = invitation(
        session, business.tenant.id, scheduled_owner.id, status="pending"
    )
    for _ in range(101):
        invitation(session, business.tenant.id, scheduled_owner.id)
    session.flush()
    assert cleanup_terminal_invitations(session, tenant_id=business.tenant.id) == 100
    assert cleanup_terminal_invitations(session, tenant_id=business.tenant.id) == 1
    assert cleanup_terminal_invitations(session, tenant_id=business.tenant.id) == 0
    assert (
        session.scalar(
            select(CompanyInvitation.id).where(CompanyInvitation.tenant_id == second.id)
        )
        == other.id
    )
    assert session.get(CompanyInvitation, recent.id) is not None
    assert session.get(CompanyInvitation, pending.id) is not None
    with pytest.raises(ValueError):
        cleanup_terminal_invitations(session, tenant_id=business.tenant.id, limit=101)
