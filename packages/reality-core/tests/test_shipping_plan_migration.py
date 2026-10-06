"""Planning input storage keeps the shortest same-company relationships."""

import json
from datetime import date

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from reality.db.core import Base, ShippingPlanStatement, SourceRecord, uid
from reality.services import core


def test_isolated_upgrade_empty_downgrade_and_retained_evidence_guard(
    postgres_database, monkeypatch
):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0146_shipping_plan_inputs")
    engine = create_engine(postgres_database)
    try:
        assert "shipping_capacity_window" in inspect(engine).get_table_names()
        command.downgrade(config, "0145_default_operational_cases")
        assert "shipping_plan_statement" not in inspect(engine).get_table_names()
        command.upgrade(config, "0146_shipping_plan_inputs")
        with Session(engine) as session:
            tenant = core.create_tenant(session, "Planning schema proof")
            location = core.create_location(session, tenant.id, "V", "Venlo")
            source, _, _ = core.store_source_record(
                session,
                tenant.id,
                "schema-proof",
                "plan",
                "opaque-stream",
                {"original_quantity": "2.0000"},
            )
            source_id = source.id
            session.add(
                ShippingPlanStatement(
                    tenant_id=tenant.id,
                    id=uid("sps"),
                    source_record_id=source_id,
                    statement_kind="withdrawal",
                    dispatch_location_id=location.id,
                    business_day=date(2026, 10, 6),
                    business_time_zone="UTC",
                    site_time_zone="UTC",
                )
            )
            session.commit()
        with pytest.raises(RuntimeError, match="planning evidence"):
            command.downgrade(config, "0145_default_operational_cases")
        with Session(engine) as session:
            assert json.loads(session.scalar(select(SourceRecord.payload))) == {
                "original_quantity": "2.0000"
            }
            assert (
                session.scalar(select(ShippingPlanStatement.source_record_id))
                == source_id
            )
    finally:
        engine.dispose()


def test_database_rejects_a_foreign_source(session, business):
    tenant = core.create_tenant(session, "Other company")
    source, _, _ = core.store_source_record(
        session,
        tenant.id,
        "schema-proof",
        "plan",
        "other-stream",
        {"untouched": "foreign"},
    )
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            ShippingPlanStatement(
                tenant_id=business.tenant.id,
                id=uid("sps"),
                source_record_id=source.id,
                statement_kind="withdrawal",
                dispatch_location_id=business.location.id,
                business_day=date(2026, 10, 6),
                business_time_zone="UTC",
                site_time_zone="UTC",
            )
        )
        session.flush()


def test_three_input_tables_keep_composite_business_links_and_no_derived_state():
    names = (
        "shipping_plan_statement",
        "shipping_dispatch_requirement",
        "shipping_capacity_window",
    )
    assert all(name in Base.metadata.tables for name in names)
    for name in names:
        table = Base.metadata.tables[name]
        assert list(table.primary_key.columns.keys()) == ["tenant_id", "id"]
        assert not {
            "status",
            "forecast",
            "completed",
            "document_id",
            "document_line_id",
        } & set(table.columns.keys())
        for constraint in table.foreign_key_constraints:
            if next(iter(constraint.elements)).target_fullname != "tenant.id":
                assert "tenant_id" in constraint.column_keys


def test_planning_does_not_expand_document_operational_state():
    columns = set(Base.metadata.tables["document"].columns.keys())
    assert (
        not {"shipping_status", "shipping_plan_id", "forecast", "handover_status"}
        & columns
    )
