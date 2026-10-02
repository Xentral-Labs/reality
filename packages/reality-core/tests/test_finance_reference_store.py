"""Shared storage retains separate Finance catalog contracts and typed identity."""

from sqlalchemy import inspect


def test_catalogs_share_one_physical_store(session):
    inspector = inspect(session.connection())
    assert "finance_reference_store" in inspector.get_table_names()
    assert not {"finance_reference", "accounting_target_reference"} & set(
        inspector.get_table_names()
    )
    assert {"finance_reference", "accounting_target_reference"} <= set(
        inspector.get_view_names()
    )


def _catalogs(session, tenant, identity="same"):
    from reality.db.finance_references import FinanceReference
    from reality.db.target_mappings import AccountingTarget, AccountingTargetReference

    session.add(
        AccountingTarget(
            tenant_id=tenant,
            id="target",
            namespace="target",
            name="Target",
            state="active",
            revision=1,
        )
    )
    session.flush()
    internal = FinanceReference(
        tenant_id=tenant,
        id=identity,
        kind="cost_center",
        code="internal",
        name="Internal",
        state="active",
        revision=1,
    )
    external = AccountingTargetReference(
        tenant_id=tenant,
        id=identity,
        target_id="target",
        kind="account",
        code="external",
        name="External",
        state="active",
        revision=1,
    )
    session.add_all([internal, external])
    session.flush()
    return internal, external


def test_view_orm_crud_preserves_colliding_family_and_tenant_ids(session, business):
    from sqlalchemy import select, text

    from reality.db.finance_references import FinanceReference
    from reality.db.target_mappings import AccountingTargetReference
    from reality.services import core

    tenant = business.tenant.id
    internal, external = _catalogs(session, tenant)
    other = core.create_tenant(session, "Other catalogs").id
    _catalogs(session, other)
    assert external.created_at is not None and external.updated_at is not None
    original_time = external.created_at
    internal.name, external.name = "Renamed internal", "Renamed external"
    session.flush()
    session.expire_all()
    assert (
        session.scalar(
            select(FinanceReference).where(
                FinanceReference.tenant_id == tenant, FinanceReference.id == "same"
            )
        ).name
        == "Renamed internal"
    )
    assert external.name == "Renamed external" and external.created_at == original_time
    assert (
        session.scalar(
            text("SELECT count(*) FROM finance_reference_store WHERE id='same'")
        )
        == 4
    )
    assert session.execute(
        text(
            "SELECT created_at,updated_at,target_id FROM finance_reference_store WHERE tenant_id=:t AND kind='cost_center'"
        ),
        {"t": tenant},
    ).one() == (None, None, None)
    session.delete(internal)
    session.flush()
    assert (
        session.scalar(
            select(AccountingTargetReference).where(
                AccountingTargetReference.tenant_id == tenant,
                AccountingTargetReference.id == "same",
            )
        )
        is external
    )
    session.delete(external)
    session.flush()
    assert (
        session.scalar(
            text("SELECT count(*) FROM finance_reference_store WHERE id='same'")
        )
        == 2
    )


def test_view_and_store_constraints_preserve_catalog_boundaries(session, business):
    import pytest
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    tenant = business.tenant.id
    _catalogs(session, tenant)
    # This transformation would be valid in physical storage; only the view's
    # family check prevents it from silently moving into the internal catalog.
    session.execute(
        text(
            "INSERT INTO accounting_target_reference (id,tenant_id,target_id,kind,code,name,state,revision,created_at,updated_at) VALUES ('external-only',:t,'target','account','external-only','External only','active',1,now(),now())"
        ),
        {"t": tenant},
    )
    with pytest.raises(DBAPIError, match="check option"), session.begin_nested():
        session.execute(
            text(
                "UPDATE accounting_target_reference SET kind='cost_center',target_id=NULL,created_at=NULL,updated_at=NULL WHERE tenant_id=:t AND id='external-only'"
            ),
            {"t": tenant},
        )
    for sql in (
        "UPDATE finance_reference SET kind='account' WHERE tenant_id=:t",
        "UPDATE accounting_target_reference SET kind='cost_center' WHERE tenant_id=:t",
        "INSERT INTO finance_reference VALUES ('same',:t,'case_code','different','Duplicate family ID','active',1)",
        "INSERT INTO finance_reference VALUES ('long',:t,'case_code',repeat('x',101),'Too long','active',1)",
        "INSERT INTO finance_reference VALUES ('invalid',:t,'unknown','x','Invalid','active',1)",
        "UPDATE accounting_target_reference SET target_id='missing' WHERE tenant_id=:t",
        "UPDATE accounting_target_reference SET created_at=NULL WHERE tenant_id=:t",
        "UPDATE finance_reference SET revision=0 WHERE tenant_id=:t",
    ):
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(text(sql), {"t": tenant})
    assert (
        session.execute(
            text(
                "INSERT INTO finance_reference VALUES ('boundary',:t,'case_code',repeat('x',100),'Boundary','active',1) RETURNING id"
            ),
            {"t": tenant},
        ).scalar_one()
        == "boundary"
    )
    assert (
        session.execute(
            text(
                "UPDATE finance_reference SET name='Updated' WHERE tenant_id=:t AND id='boundary' RETURNING name"
            ),
            {"t": tenant},
        ).scalar_one()
        == "Updated"
    )
    assert (
        session.execute(
            text(
                "DELETE FROM finance_reference WHERE tenant_id=:t AND id='boundary' RETURNING id"
            ),
            {"t": tenant},
        ).scalar_one()
        == "boundary"
    )


def test_all_incoming_catalog_links_target_physical_typed_keys(session):
    inspector = inspect(session.connection())
    links = [
        fk
        for table in inspector.get_table_names()
        for fk in inspector.get_foreign_keys(table)
        if fk["referred_table"] == "finance_reference_store"
    ]
    assert len(links) == 8
    assert (
        sum(fk["referred_columns"] == ["tenant_id", "id", "kind"] for fk in links) == 6
    )
    assert (
        sum(
            fk["referred_columns"] == ["tenant_id", "target_id", "id", "kind"]
            for fk in links
        )
        == 2
    )


def test_partial_metadata_catalog_lifecycle(postgres_database):
    from sqlalchemy import create_engine

    from reality.db.core import Base, Tenant
    from reality.db.finance_reference_store import storage
    from reality.db.finance_references import FinanceReference
    from reality.db.target_mappings import AccountingTarget, AccountingTargetReference

    engine = create_engine(postgres_database)
    tables = [
        Tenant.__table__,
        AccountingTarget.__table__,
        storage,
        FinanceReference.__table__,
        AccountingTargetReference.__table__,
    ]
    try:
        Base.metadata.create_all(engine, tables=tables)
        Base.metadata.create_all(engine, tables=tables)
        assert set(inspect(engine).get_table_names()) == {
            "tenant",
            "accounting_target",
            "finance_reference_store",
        }
        assert set(inspect(engine).get_view_names()) == {
            "finance_reference",
            "accounting_target_reference",
        }
        Base.metadata.drop_all(engine, tables=tables)
        assert inspect(engine).get_table_names() == []
        assert inspect(engine).get_view_names() == []
    finally:
        engine.dispose()


def test_company_count_and_purge_process_shared_catalog_once(session, business):
    from sqlalchemy import text

    from reality.services.account_deletion import _tenant_record_count
    from reality.services.core import _purge_tenant_records

    tenant = business.tenant.id
    before = _tenant_record_count(session, tenant)
    _catalogs(session, tenant)
    # One destination and two reference rows; the logical views add no extra count.
    assert _tenant_record_count(session, tenant) == before + 3
    _purge_tenant_records(session, tenant)
    assert (
        session.scalar(
            text("SELECT count(*) FROM finance_reference_store WHERE tenant_id=:t"),
            {"t": tenant},
        )
        == 0
    )
