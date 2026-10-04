"""Current separately stored partner roles in finite retained reference reviews."""

from hashlib import sha256

from sqlalchemy import select

from reality.db.core import PartyRole
from reality.domain.intake import canonical_json


def party_role_reference(session, tenant_id, party_id):
    """Witness actual tenant-scoped role records without duplicating their values."""
    roles = session.scalars(
        select(PartyRole)
        .where(PartyRole.tenant_id == tenant_id, PartyRole.party_id == party_id)
        .order_by(PartyRole.id)
        .execution_options(populate_existing=True)
    )
    state = [
        {column.name: getattr(role, column.name) for column in PartyRole.__table__.columns}
        for role in roles
    ]
    return sha256(canonical_json(state).encode()).hexdigest()
