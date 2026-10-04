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



def historical_post_sales_invoice(session, tenant_id, document_id):
    """Seed received ledger facts only in the four pinned migration fixtures.

    No current person, approval, credential or decision receipt is invented.
    Current runtime assertions run after the test upgrades the original facts.
    """
    from sqlalchemy import select, text

    version = session.scalar(text("SELECT version_num FROM alembic_version"))
    if version not in {"0050_opening_subledger", "0051_finance_references", "0052_component_assignments", "0053_source_classification"}:
        raise AssertionError("Historical posting construction is limited to the pinned migration schemas.")
    metadata = MetaData()
    document = Table("document", metadata, autoload_with=session.connection())
    ledger = Table("ledger_entry", metadata, autoload_with=session.connection())
    destination = Table("finance_role_destination", metadata, autoload_with=session.connection())
    received = session.execute(select(document).where(document.c.tenant_id == tenant_id, document.c.id == document_id)).mappings().one()
    if received["type"] != "sales_invoice":
        raise AssertionError("The pinned fixture records its stated sales invoice only.")
    group = core.uid("post")
    moment = core.now()
    for role, side in (("accounts_receivable", "debit"), ("sales_revenue", "credit")):
        account_id = session.scalar(select(destination.c.account_id).where(destination.c.tenant_id == tenant_id, destination.c.role == role))
        if account_id is None:
            raise AssertionError("The pinned fixture requires its original account destination.")
        values = {"id": core.uid("led"), "tenant_id": tenant_id, "document_id": document_id,
            "party_id": received["party_id"], "source_record_id": received["source_record_id"],
            "posting_group_id": group, "account": role, "account_id": account_id,
            "debit_credit": side, "amount": received["gross_amount"], "currency": received["currency"],
            "effective_at": moment, "created_at": moment}
        session.execute(ledger.insert().values(**{key: value for key, value in values.items() if key in ledger.c}))
    session.commit()
