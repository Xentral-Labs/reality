"""Seed pinned pre-0110 migration fixtures independently of current default storage.

Only fixture construction uses reflected legacy tables. Runtime business assertions
continue through the shared services; historical posting/authority proofs are retained.
"""

from sqlalchemy import MetaData, Table

from reality.domain.finance import BASE_ACCOUNT_ROLES
from reality.services import core


def bootstrap_legacy_accounts(session, tenant_id):
    metadata = MetaData()
    account = Table("subledger_account", metadata, autoload_with=session.connection())
    destination = Table(
        "finance_role_destination", metadata, autoload_with=session.connection()
    )
    state = Table("finance_state", metadata, autoload_with=session.connection())
    for role, label in BASE_ACCOUNT_ROLES.items():
        account_id = core.uid("acc")
        session.execute(
            account.insert().values(
                id=account_id,
                tenant_id=tenant_id,
                code=role,
                name=label,
                role=role,
                state="active",
                revision=1,
            )
        )
        session.execute(
            destination.insert().values(
                id=core.uid("dest"),
                tenant_id=tenant_id,
                role=role,
                account_id=account_id,
            )
        )
    session.execute(
        state.insert().values(id=core.uid("fin"), tenant_id=tenant_id, revision=0)
    )


def create_legacy_tenant(session, name):
    tenant = core.create_tenant(session, name, _with_finance_defaults=False)
    bootstrap_legacy_accounts(session, tenant.id)
    session.commit()
    return tenant
