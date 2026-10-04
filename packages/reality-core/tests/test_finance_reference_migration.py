"""Populated catalog consolidation preserves exact authorities and rollback schema."""

from types import SimpleNamespace

import pytest
from alembic import command
from alembic.config import Config
from intake_review_support import reviewed_post_sales_invoice
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_cost_projection_migration import _schema_snapshot

CATALOGS = ("finance_reference", "accounting_target_reference")
DEPENDENTS = (
    "component_assignment_part",
    "component_assignment_revision",
    "source_classification_mapping_revision",
    "finance_target_mapping_revision",
)


@pytest.fixture
def legacy_catalogs(postgres_database, monkeypatch):
    from reality.services import core
    from tests.finance.test_components import fixture, prepare
    from tests.finance.test_references import confirm
    from tests.finance.test_source_mappings import prepare as prepare_source
    from tests.finance.test_target_mappings import change, rule, setup

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0118_account_defaults")
    engine = create_engine(postgres_database)
    try:
        with Session(engine) as session:
            company = SimpleNamespace(
                tenant=core.create_tenant(session, "Catalog migration")
            )
            company.customer = reviewed_create_party(
                session, company.tenant.id, "Customer", "customer"
            )
            company.supplier = reviewed_create_party(
                session, company.tenant.id, "Supplier", "supplier"
            )
            tenant, target, account, case = setup(session, company)
            change(
                session,
                tenant,
                "finance.target_mapping.set",
                **rule(target, account, case),
            )
            with session.begin_nested():
                session.execute(
                    text(
                        "INSERT INTO finance_reference (id,tenant_id,kind,code,name,state,revision) VALUES ('collision',:t,'cost_center','center','Exact center','blocked',9)"
                    ),
                    {"t": tenant},
                )
                session.execute(
                    text(
                        "INSERT INTO accounting_target_reference (id,tenant_id,target_id,kind,code,name,state,revision,created_at,updated_at) VALUES ('collision',:t,:target,'tax_code','tax','Exact tax','blocked',7,'2026-09-01 12:34:56.123456+00','2026-09-02 12:34:56.654321+00')"
                    ),
                    {"t": tenant, "target": target["id"]},
                )
            doc, ids = fixture(session, company)
            reviewed_post_sales_invoice(session, tenant, doc.id)
            confirm(
                session,
                tenant,
                prepare(
                    session,
                    tenant,
                    doc,
                    case_reference_id=ids["DOMESTIC"],
                    group_reference_id=ids["GOODS"],
                    parts=[
                        {"cost_center_reference_id": ids["A"], "amount": "600"},
                        {"cost_center_reference_id": ids["B"], "amount": "400"},
                    ],
                ),
            )
            source = core.create_source_system(
                session, tenant, "declared-finance-test", "Source"
            )
            confirm(session, tenant, prepare_source(session, tenant, source, case))
            tax = change(
                session,
                tenant,
                "finance.target_reference.create",
                target_id=target["id"],
                kind="tax_code",
                code="ACTIVE-TAX",
                name="Tax",
            )
            change(
                session,
                tenant,
                "finance.target_mapping.set",
                target_id=target["id"],
                mapping_kind="case_routing",
                transaction_kind="sales_invoice",
                case_reference_id=ids["DOMESTIC"],
                group_mode="exact",
                group_reference_id=ids["GOODS"],
                external_account_id=account["id"],
                external_tax_code_id=tax["id"],
            )
            other = core.create_tenant(session, "Other catalog namespace").id
            session.execute(
                text(
                    "INSERT INTO finance_reference (id,tenant_id,kind,code,name,state,revision) VALUES ('collision',:t,'cost_center','center','Other exact center','active',1)"
                ),
                {"t": other},
            )
            session.commit()
        yield engine, config, tenant
    finally:
        engine.dispose()


def _all_records(connection, names):
    return {
        name: list(
            connection.scalars(
                text(f'SELECT to_jsonb(t)::text FROM "{name}" t ORDER BY 1')
            )
        )
        for name in names
    }


def test_populated_catalog_roundtrip_exact_values_authorities_and_schema(
    legacy_catalogs,
):
    engine, config, tenant = legacy_catalogs
    with engine.connect() as connection:
        physical = set(inspect(connection).get_table_names())
        names = sorted(physical - {"alembic_version"})
        before = _all_records(connection, names)
        schema = _schema_snapshot(connection, (*CATALOGS, *DEPENDENTS))
    command.upgrade(config, "0119_finance_references")
    with engine.connect() as connection:
        assert _all_records(connection, names) == before
        assert set(inspect(connection).get_table_names()) == physical - set(
            CATALOGS
        ) | {"finance_reference_store"}
        assert set(CATALOGS) <= set(inspect(connection).get_view_names())
        assert len(inspect(connection).get_foreign_keys("finance_reference_store")) == 2
    with engine.begin() as connection:
        checked = 0
        for table in DEPENDENTS:
            for fk in inspect(connection).get_foreign_keys(table):
                if fk["referred_table"] != "finance_reference_store":
                    continue
                column = next(
                    local
                    for local, remote in zip(
                        fk["constrained_columns"], fk["referred_columns"]
                    )
                    if remote == "id"
                )
                assert (
                    connection.scalar(
                        text(f"SELECT count(*) FROM {table} WHERE {column} IS NOT NULL")
                    )
                    > 0
                )
                with pytest.raises(DBAPIError), connection.begin_nested():
                    connection.execute(
                        text(
                            f"UPDATE {table} SET {column}='missing-reference' WHERE {column} IS NOT NULL"
                        )
                    )
                checked += 1
        assert checked == 8
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE finance_reference SET name='New exact label',revision=10 WHERE tenant_id=:t AND id='collision'"
            ),
            {"t": tenant},
        )
        connection.execute(
            text(
                "UPDATE accounting_target_reference SET name='New tax label',revision=8,updated_at='2026-10-02 01:02:03.456789+00' WHERE tenant_id=:t AND id='collision'"
            ),
            {"t": tenant},
        )
    with engine.connect() as connection:
        changed = _all_records(connection, names)
        assert {n: v for n, v in changed.items() if n not in CATALOGS} == {
            n: v for n, v in before.items() if n not in CATALOGS
        }
    command.downgrade(config, "0118_account_defaults")
    with engine.connect() as connection:
        assert _all_records(connection, names) == changed
        assert _schema_snapshot(connection, (*CATALOGS, *DEPENDENTS)) == schema
        assert set(inspect(connection).get_table_names()) == physical
    command.upgrade(config, "0119_finance_references")
    with engine.connect() as connection:
        assert _all_records(connection, names) == changed


from intake_review_support import reviewed_create_party
