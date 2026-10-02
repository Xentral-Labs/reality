"""Account-owned default selection preserves identity, finance history and isolation."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    Base,
    BusinessEvent,
    FinanceRoleDestination,
    SubledgerAccount,
)
from reality.services import core
from reality.services.finance import accounts


def test_defaults_are_account_owned_and_legacy_relation_is_readonly(session, business):
    inspector = inspect(session.connection())
    assert "finance_role_destination" not in inspector.get_table_names()
    assert "finance_role_destination" in inspector.get_view_names()
    assert "default_destination_id" in SubledgerAccount.__table__.c
    tenant = business.tenant.id
    before = list(
        session.execute(
            select(SubledgerAccount).where(SubledgerAccount.tenant_id == tenant)
        )
    )
    for sql in (
        "INSERT INTO finance_role_destination VALUES ('a','b','cash','c')",
        "UPDATE finance_role_destination SET account_id='changed' WHERE tenant_id=:tenant",
        "DELETE FROM finance_role_destination WHERE tenant_id=:tenant",
    ):
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(text(sql), {"tenant": tenant})
    assert (
        list(
            session.execute(
                select(SubledgerAccount).where(SubledgerAccount.tenant_id == tenant)
            )
        )
        == before
    )
    Base.metadata.create_all(session.connection())


def test_switch_repeat_and_stale_revision_preserve_selection_and_account_revision(
    session, business
):
    tenant = business.tenant.id
    old = session.scalar(
        select(FinanceRoleDestination).where(
            FinanceRoleDestination.tenant_id == tenant,
            FinanceRoleDestination.role == "cash",
        )
    )
    destination_id, old_account_id = old.id, old.account_id
    new = accounts.create_account(
        session, tenant, code="cash-2", name="Second cash", role="cash", _commit=False
    )
    revision = accounts.list_accounts(session, tenant)["revision"]
    original = accounts._get(session, tenant, old_account_id)
    old_revision = original.revision
    accounts.set_default_account(
        session,
        tenant,
        role="cash",
        account_id=new["id"],
        expected_revision=revision,
        _commit=False,
    )
    assert original.default_destination_id is None
    chosen = accounts._get(session, tenant, new["id"])
    assert chosen.default_destination_id == destination_id
    assert chosen.revision == new["revision"] and original.revision == old_revision
    assert accounts.list_accounts(session, tenant)["defaults"]["cash"] == new["id"]
    with pytest.raises(core.Conflict):
        accounts.set_default_account(
            session,
            tenant,
            role="cash",
            account_id=old_account_id,
            expected_revision=revision,
            _commit=False,
        )
    accounts.set_default_account(
        session,
        tenant,
        role="cash",
        account_id=new["id"],
        expected_revision=revision + 1,
        _commit=False,
    )
    assert chosen.default_destination_id == destination_id
    assert chosen.revision == new["revision"]
    assert accounts.list_accounts(session, tenant)["revision"] == revision + 2


def test_marker_constraints_preserve_tenant_namespaces_and_role_uniqueness(
    session, business
):
    tenant = business.tenant.id
    chosen = accounts.resolve_account(session, tenant, "cash")
    extra = accounts.create_account(
        session, tenant, code="cash-2", name="Second", role="cash", _commit=False
    )
    with pytest.raises(DBAPIError), session.begin_nested():
        session.execute(
            text(
                "UPDATE subledger_account SET default_destination_id='different' WHERE tenant_id=:tenant AND id=:id"
            ),
            {"tenant": tenant, "id": extra["id"]},
        )
    sales = accounts.resolve_account(session, tenant, "sales_revenue")
    with pytest.raises(DBAPIError), session.begin_nested():
        session.execute(
            text(
                "UPDATE subledger_account SET default_destination_id=:marker WHERE tenant_id=:tenant AND id=:id"
            ),
            {"marker": chosen.default_destination_id, "tenant": tenant, "id": sales.id},
        )
    other = core.create_tenant(session, "Other defaults").id
    foreign = accounts.resolve_account(session, other, "cash")
    foreign.default_destination_id = chosen.default_destination_id
    session.flush()
    with pytest.raises(core.NotFound):
        accounts.set_default_account(
            session, tenant, role="cash", account_id=foreign.id, _commit=False
        )
    with pytest.raises(core.InvalidOperation):
        accounts.set_default_account(
            session, tenant, role="cash", account_id=sales.id, _commit=False
        )


def test_blocked_default_remains_selected_and_reads_do_not_mutate(session, business):
    tenant = business.tenant.id
    chosen = accounts.resolve_account(session, tenant, "cash")
    marker = chosen.default_destination_id
    accounts.update_account(session, tenant, chosen.id, state="blocked", _commit=False)
    before = accounts.list_accounts(session, tenant)
    count = session.scalar(
        select(func.count())
        .select_from(BusinessEvent)
        .where(BusinessEvent.tenant_id == tenant)
    )
    with pytest.raises(core.InvalidOperation):
        accounts.resolve_account(session, tenant, "cash")
    assert chosen.default_destination_id == marker
    assert accounts.list_accounts(session, tenant) == before
    assert (
        accounts.transaction_matrix(session, tenant)["revision"] == before["revision"]
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(BusinessEvent.tenant_id == tenant)
        )
        == count
    )
    accounts.initialize_accounts(session, tenant, _commit=False)
    assert accounts.list_accounts(session, tenant)["defaults"]["cash"] == chosen.id
    assert chosen.default_destination_id == marker


def test_competing_default_changes_use_existing_finance_revision(postgres_database):
    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = core.create_tenant(session, "Competing defaults").id
            marker = accounts.resolve_account(
                session, tenant, "cash"
            ).default_destination_id
            candidates = [
                accounts.create_account(
                    session, tenant, code=f"cash-{i}", name=f"Cash {i}", role="cash"
                )["id"]
                for i in range(2)
            ]
            revision = accounts.list_accounts(session, tenant)["revision"]
        barrier = Barrier(2)

        def choose(account_id):
            with factory() as session:
                barrier.wait(timeout=10)
                try:
                    accounts.set_default_account(
                        session,
                        tenant,
                        role="cash",
                        account_id=account_id,
                        expected_revision=revision,
                    )
                    return "selected"
                except core.Conflict:
                    session.rollback()
                    return "stale"

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(choose, candidates)) == ["selected", "stale"]
        with factory() as session:
            chosen = accounts.resolve_account(session, tenant, "cash")
            assert chosen.id in candidates and chosen.default_destination_id == marker
            assert accounts.list_accounts(session, tenant)["revision"] == revision + 1
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(FinanceRoleDestination)
                    .where(
                        FinanceRoleDestination.tenant_id == tenant,
                        FinanceRoleDestination.role == "cash",
                    )
                )
                == 1
            )
    finally:
        engine.dispose()


def test_partial_metadata_create_drop_keeps_logical_view_contract(postgres_database):
    from reality.db.core import Tenant

    engine = create_engine(postgres_database)
    tables = [
        Tenant.__table__,
        SubledgerAccount.__table__,
        FinanceRoleDestination.__table__,
    ]
    try:
        Base.metadata.create_all(engine, tables=tables)
        assert set(inspect(engine).get_table_names()) == {"tenant", "subledger_account"}
        assert inspect(engine).get_view_names() == ["finance_role_destination"]
        Base.metadata.drop_all(engine, tables=tables)
        assert inspect(engine).get_table_names() == []
        assert inspect(engine).get_view_names() == []
    finally:
        engine.dispose()
