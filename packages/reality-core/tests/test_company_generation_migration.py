"""Migration parity and rollback guards for financial company generations."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, UniqueConstraint, create_engine, inspect, text
from sqlalchemy.exc import DBAPIError
from test_cost_captured_basis_storage import scheduled_database  # noqa: F401

TABLES = {
    "cost_company_manifest",
    "cost_company_inventory_input",
    "cost_company_contribution_input",
    "cost_company_generation",
    "cost_company_inventory_result",
    "cost_company_contribution_result",
    "cost_company_publication",
}


def test_company_generation_migration_parity_and_empty_round_trip(
    postgres_database, monkeypatch
):
    from reality.db.core import Base

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0080_company_generations")
    engine = create_engine(postgres_database)
    try:
        inspector = inspect(engine)
        for name in TABLES:
            model = Base.metadata.tables[name]
            assert {column["name"] for column in inspector.get_columns(name)} == set(
                model.c.keys()
            )
            assert {
                tuple(row["constrained_columns"])
                for row in inspector.get_foreign_keys(name)
            } == {tuple(key.column_keys) for key in model.foreign_key_constraints}
            assert {
                tuple(row["column_names"])
                for row in inspector.get_unique_constraints(name)
            } == {
                tuple(constraint.columns.keys())
                for constraint in model.constraints
                if isinstance(constraint, UniqueConstraint)
            }
            assert {row["name"] for row in inspector.get_check_constraints(name)} == {
                constraint.name
                for constraint in model.constraints
                if isinstance(constraint, CheckConstraint)
            }
        command.downgrade(config, "0079_captured_report")
        assert not TABLES & set(inspect(engine).get_table_names())
        command.upgrade(config, "0080_company_generations")
    finally:
        engine.dispose()


def test_populated_company_manifest_refuses_downgrade(
    scheduled_database,  # noqa: F811
    monkeypatch,
):
    import test_cost_captured_basis_storage as storage

    engine, factory, _, _ = scheduled_database
    command.upgrade(Config("alembic.ini"), "0080_company_generations")
    _, tenant, census, _ = storage.retained(scheduled_database, reviewed=False)
    with factory() as session:
        session.execute(
            text(
                """
                INSERT INTO cost_company_manifest (
                    id, tenant_id, census_id, effective_at, knowledge_at,
                    target_event_sequence, inventory_algorithm_version,
                    contribution_algorithm_version, scope_key, population_digest,
                    inventory_count, contribution_count, header_gap_count,
                    source_gap_count, gap_digest, state, sealed_at, content_hash
                )
                SELECT 'manifest', tenant_id, id, effective_at, observed_at,
                    event_sequence, 'inventory-v1', 'commercial-v1', repeat('a',64),
                    repeat('b',64), 0, 0, 0, 0, repeat('c',64), 'building', NULL,
                    repeat('d',64)
                FROM cost_company_census WHERE tenant_id=:tenant AND id=:census
                """
            ),
            {"tenant": tenant, "census": census},
        )
        session.commit()
    monkeypatch.setenv(
        "REALITY_DATABASE_URL", engine.url.render_as_string(hide_password=False)
    )
    with pytest.raises(RuntimeError, match="company generation history"):
        command.downgrade(Config("alembic.ini"), "0079_captured_report")


def test_sealed_rows_are_immutable_and_unknown_shape_is_guarded(
    scheduled_database,  # noqa: F811
):
    import test_cost_captured_basis_storage as storage

    _, factory, _, _ = scheduled_database
    command.upgrade(Config("alembic.ini"), "0080_company_generations")
    _, tenant, census, _ = storage.retained(scheduled_database, reviewed=False)
    with factory() as session:
        item = session.scalar(
            text(
                """
                SELECT m.item_id FROM movement m
                JOIN cost_company_census_movement cm
                  ON cm.tenant_id=m.tenant_id AND cm.movement_id=m.id
                WHERE cm.tenant_id=:tenant AND cm.census_id=:census
                LIMIT 1
                """
            ),
            {"tenant": tenant, "census": census},
        )
        session.execute(
            text(
                """
                INSERT INTO cost_company_manifest (
                    id, tenant_id, census_id, effective_at, knowledge_at,
                    target_event_sequence, inventory_algorithm_version,
                    contribution_algorithm_version, scope_key, population_digest,
                    inventory_count, contribution_count, header_gap_count,
                    source_gap_count, gap_digest, state, sealed_at, content_hash
                )
                SELECT 'manifest', tenant_id, id, effective_at, observed_at,
                    event_sequence, 'inventory-v1', 'commercial-v1', repeat('a',64),
                    repeat('b',64), 1, 0, 1, 1, repeat('c',64), 'building', NULL,
                    repeat('d',64)
                FROM cost_company_census WHERE tenant_id=:tenant AND id=:census
                """
            ),
            {"tenant": tenant, "census": census},
        )
        session.execute(
            text(
                """
                INSERT INTO cost_company_inventory_input
                  (id,tenant_id,manifest_id,item_id,review_id,input_fingerprint,support_state)
                VALUES ('input',:tenant,'manifest',:item,NULL,repeat('e',64),'unknown')
                """
            ),
            {"tenant": tenant, "item": item},
        )
        session.execute(
            text(
                "UPDATE cost_company_manifest SET state='sealed', sealed_at=now() WHERE tenant_id=:tenant AND id='manifest'"
            ),
            {"tenant": tenant},
        )
        session.commit()
    with factory() as session, pytest.raises(DBAPIError, match="immutable"):
        session.execute(
            text(
                "UPDATE cost_company_manifest SET content_hash=repeat('f',64) WHERE tenant_id=:tenant AND id='manifest'"
            ),
            {"tenant": tenant},
        )
    with factory() as session:
        session.execute(
            text(
                """
                INSERT INTO cost_company_generation (
                  id,tenant_id,manifest_id,algorithm_bundle,scope_key,state,
                  expected_work_count,completed_work_count,inventory_count,
                  contribution_count,inventory_content_hash,contribution_content_hash,
                  started_at,completed_at)
                VALUES ('generation',:tenant,'manifest','company-v1',repeat('a',64),
                  'building',1,1,1,0,repeat('1',64),repeat('2',64),now(),NULL)
                """
            ),
            {"tenant": tenant},
        )
        session.commit()
    with factory() as session, pytest.raises(DBAPIError):
        session.execute(
            text(
                """
                INSERT INTO cost_company_inventory_result
                  (id,tenant_id,generation_id,inventory_input_id,
                   inventory_generation_id,state,result_fingerprint)
                VALUES ('bad',:tenant,'generation','input',NULL,'known',repeat('3',64))
                """
            ),
            {"tenant": tenant},
        )
    with factory() as session:
        session.execute(
            text(
                """
                INSERT INTO cost_company_inventory_result
                  (id,tenant_id,generation_id,inventory_input_id,
                   inventory_generation_id,state,result_fingerprint)
                VALUES ('result',:tenant,'generation','input',NULL,'unknown',repeat('3',64))
                """
            ),
            {"tenant": tenant},
        )
        session.execute(
            text(
                "UPDATE cost_company_generation SET state='sealed',completed_at=now() WHERE tenant_id=:tenant AND id='generation'"
            ),
            {"tenant": tenant},
        )
        session.commit()
    with factory() as session, pytest.raises(DBAPIError, match="immutable"):
        session.execute(
            text(
                "UPDATE cost_company_generation SET algorithm_bundle='changed' WHERE tenant_id=:tenant AND id='generation'"
            ),
            {"tenant": tenant},
        )
