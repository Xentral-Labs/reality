"""Captured reports preserve exact selection without claiming company completeness."""

from datetime import UTC, datetime

import pytest


def test_publication_context_and_cursor_rules():
    from reality.domain.captured_report import CapturedPublication, decide

    candidate = CapturedPublication(
        tenant_id="t",
        generation_id="g",
        basis_id="b",
        scope_key="s",
        effective_at=datetime(2026, 9, 1, tzinfo=UTC),
        event_sequence=10,
    )
    assert decide("t", candidate, None, None, 10)["freshness"] == "ready"
    assert decide("t", candidate, None, None, 11)["freshness"] == "pending"
    assert not decide("t", candidate, candidate, "old", 11)["change_pointer"]
    for tenant, prior, previous, cursor in [
        ("foreign", None, None, 10),
        ("t", None, None, 9),
        ("t", None, "absent", 10),
        ("t", candidate.model_copy(update={"scope_key": "other"}), "g", 10),
        (
            "t",
            candidate.model_copy(update={"generation_id": "old", "basis_id": "other"}),
            "old",
            10,
        ),
        (
            "t",
            candidate.model_copy(update={"generation_id": "new", "event_sequence": 11}),
            "new",
            11,
        ),
    ]:
        with pytest.raises(ValueError):
            decide(tenant, candidate, prior, previous, cursor)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CapturedPublication(
            **(candidate.model_dump() | {"knowledge_at": datetime.now(UTC)})
        )


@pytest.fixture
def report_database(postgres_database, monkeypatch):
    import test_cost_captured_basis_storage as storage
    from alembic import command
    from alembic.config import Config

    fixture = storage.scheduled_database.__wrapped__(postgres_database, monkeypatch)
    database = next(fixture)
    try:
        command.upgrade(Config("alembic.ini"), "0079_captured_report")
        yield database
    finally:
        fixture.close()


@pytest.mark.parametrize("reviewed", [True, False])
def test_build_retry_fixed_read_publication_and_disposal(
    report_database, reviewed, monkeypatch
):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.services import core, cost_captured_basis, costing

    factory, tenant, _, basis = storage.retained(report_database, reviewed=reviewed)
    with read_session(factory) as session:
        built = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )
        session.commit()
    with read_session(factory) as session:
        assert (
            costing.build_captured_cost_generation(session, tenant, basis["basis_id"])
            == built
        )

    def forbidden(*args, **kwargs):
        raise AssertionError("Report reads must not replay financial history")

    monkeypatch.setattr(cost_captured_basis, "_replay", forbidden)
    with factory() as session:
        monkeypatch.setattr(session, "flush", forbidden)
        report = costing.captured_cost_report(session, tenant, built["generation_id"])
        assert report["generation_id"] == built["generation_id"]
        assert report["financial_publication_eligible"] is False
        assert report["inventory"]["total"] == report["contribution"]["total"] == 1
        if reviewed:
            assert (
                report["groups"]["inventory"][0]["acquisition"]["known"] == "420.0000"
            )
            assert report["groups"]["contribution"][0]["db1"]["known"] == "570.0000"
            assert report["groups"]["contribution"][0]["db2"]["total"] is None
        else:
            assert report["groups"] == {"inventory": [], "contribution": []}
            assert report["inventory"]["rows"][0]["state"] == "unknown_at_capture"
    with factory() as session:
        published = costing.publish_captured_cost_generation(
            session, tenant, built["generation_id"], expected_previous_id=None
        )
        session.commit()
    assert published["change_pointer"]
    with factory() as session:
        assert not costing.publish_captured_cost_generation(
            session, tenant, built["generation_id"], expected_previous_id=None
        )["change_pointer"]
        with pytest.raises(core.InvalidOperation):
            costing.discard_captured_cost_generation(
                session, tenant, built["generation_id"]
            )
    with factory() as session:
        other = core.create_tenant(session, "Foreign").id
        session.commit()
    with factory() as session, pytest.raises(core.NotFound):
        costing.captured_cost_report(session, other, built["generation_id"])


def test_build_rollback_and_unpublished_cache_disposal(report_database):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.services import core, costing

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        rolled = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )
        session.rollback()
    with factory() as session, pytest.raises(core.NotFound):
        costing.captured_cost_report(session, tenant, rolled["generation_id"])
    with read_session(factory) as session:
        built = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )
        session.commit()
    with factory() as session:
        costing.discard_captured_cost_generation(
            session, tenant, built["generation_id"]
        )
        session.commit()
    with read_session(factory) as session:
        assert costing.captured_cost_basis(session, tenant, basis["basis_id"]) == basis


def test_sealed_sql_rows_and_scope_guards(report_database):
    import test_cost_captured_basis_storage as storage
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_cost_census import read_session

    from reality.services import costing

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        built = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )
        session.commit()
    for statement in [
        "UPDATE cost_inventory_row SET acquisition_value=1 WHERE tenant_id=:tenant AND generation_id=:id",
        "DELETE FROM cost_contribution_row WHERE tenant_id=:tenant AND generation_id=:id",
        "UPDATE cost_generation SET output_hash=repeat('0',64) WHERE tenant_id=:tenant AND id=:id",
        "INSERT INTO cost_publication (id,tenant_id,scope_key,generation_id) VALUES ('bad',:tenant,'wrong',:id)",
    ]:
        with factory() as session, pytest.raises(DBAPIError):
            session.execute(
                text(statement), {"tenant": tenant, "id": built["generation_id"]}
            )


def test_foreign_operations_and_transaction_boundaries(report_database):
    import test_cost_captured_basis_storage as storage
    from test_cost_census import read_session

    from reality.services import core, costing

    factory, tenant, _, basis = storage.retained(report_database)
    with read_session(factory) as session:
        built = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )
        session.commit()
    with factory() as session:
        other = core.create_tenant(session, "Foreign").id
        session.commit()
    with read_session(factory) as session, pytest.raises(core.NotFound):
        costing.build_captured_cost_generation(session, other, basis["basis_id"])
    for call in (
        lambda s: costing.publish_captured_cost_generation(
            s, other, built["generation_id"], expected_previous_id=None
        ),
        lambda s: costing.discard_captured_cost_generation(
            s, other, built["generation_id"]
        ),
        lambda s: costing.captured_cost_report(s, other, built["generation_id"]),
    ):
        with factory() as session, pytest.raises(core.NotFound):
            call(session)
    with (
        factory() as session,
        pytest.raises(core.InvalidOperation, match="REPEATABLE READ"),
    ):
        costing.build_captured_cost_generation(session, tenant, basis["basis_id"])


def test_failed_build_savepoint_cannot_leave_output(report_database, monkeypatch):
    import test_cost_captured_basis_storage as storage
    from sqlalchemy import func, select
    from test_cost_census import read_session

    from reality.db.captured_report import CostGeneration, CostInventoryRow
    from reality.services import captured_report, costing

    factory, tenant, _, basis = storage.retained(report_database)
    original = captured_report._stored

    def fail(*args):
        original(*args)
        raise RuntimeError("injected verification failure")

    monkeypatch.setattr(captured_report, "_stored", fail)
    with read_session(factory) as session:
        with pytest.raises(RuntimeError, match="injected"):
            costing.build_captured_cost_generation(session, tenant, basis["basis_id"])
        session.commit()
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(CostGeneration)) == 0
        assert session.scalar(select(func.count()).select_from(CostInventoryRow)) == 0


def test_joint_pagination_cursor_binding_and_later_freshness(report_database):
    import test_cost_review_relevance as relevance
    from sqlalchemy import select
    from test_cost_census import read_session

    from reality.db.cost_census import CostCompanyCensus
    from reality.services import core, costing

    relevance.test_joint_inventory_and_contribution_reviews_coexist(report_database)
    _, factory, _, _ = report_database
    with factory() as session:
        census, tenant = session.execute(
            select(CostCompanyCensus.id, CostCompanyCensus.tenant_id)
        ).one()
    with read_session(factory) as session:
        basis = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="report"
        )
        session.commit()
    with read_session(factory) as session:
        generation = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session:
        first = costing.captured_cost_report(session, tenant, generation, page_size=1)
        second = costing.captured_cost_report(
            session,
            tenant,
            generation,
            page_size=1,
            inventory_cursor=first["inventory"]["next_cursor"],
            contribution_cursor=first["contribution"]["next_cursor"],
        )
        assert first["groups"] == second["groups"]
        assert len(first["groups"]["contribution"]) == 2
        for family in ("inventory", "contribution"):
            assert first[family]["total"] == second[family]["total"] == 2
            assert first[family]["rows"] != second[family]["rows"]
            assert second[family]["next_cursor"] is None
        for cursor in ("!bad!", first["contribution"]["next_cursor"]):
            with pytest.raises(core.InvalidOperation, match="cursor"):
                costing.captured_cost_report(
                    session, tenant, generation, inventory_cursor=cursor
                )
    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    with factory() as session:
        later = costing.captured_cost_report(session, tenant, generation, page_size=1)
        assert later["groups"] == first["groups"]
        assert later["freshness"] == "pending"
        assert later["context"] == first["context"]


def test_concurrent_build_and_first_publication(report_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    import test_cost_captured_basis_storage as storage
    from sqlalchemy import select
    from sqlalchemy.exc import DBAPIError
    from test_cost_census import read_session

    from reality.db.cost_captured_basis import CostCapturedBasis
    from reality.services import costing

    factory, tenant, _, basis = storage.retained(report_database)
    barrier = Barrier(2)

    def build():
        try:
            with read_session(factory) as session:
                session.scalar(
                    select(CostCapturedBasis.id).where(
                        CostCapturedBasis.tenant_id == tenant
                    )
                )
                barrier.wait(timeout=10)
                result = costing.build_captured_cost_generation(
                    session, tenant, basis["basis_id"]
                )
                session.commit()
                return result
        except DBAPIError as error:
            assert error.orig.sqlstate in {"40001", "23505"}
            with read_session(factory) as session:
                result = costing.build_captured_cost_generation(
                    session, tenant, basis["basis_id"]
                )
                session.commit()
                return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: build(), range(2)))
    assert results[0] == results[1]
    barrier = Barrier(2)

    def publish():
        with factory() as session:
            barrier.wait(timeout=10)
            result = costing.publish_captured_cost_generation(
                session, tenant, results[0]["generation_id"], expected_previous_id=None
            )
            session.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: publish(), range(2)))
    assert sorted(row["change_pointer"] for row in results) == [False, True]


def test_migration_schema_parity_and_empty_round_trip(postgres_database, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    from reality.db.core import Base

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "0079_captured_report")
    engine = create_engine(postgres_database)
    names = {
        "cost_generation",
        "cost_inventory_row",
        "cost_contribution_row",
        "cost_publication",
    }
    try:
        inspector = inspect(engine)
        for name in names:
            model = Base.metadata.tables[name]
            assert {
                row["name"]: row["nullable"] for row in inspector.get_columns(name)
            } == {col.name: col.nullable for col in model.columns}
            assert {
                tuple(row["constrained_columns"])
                for row in inspector.get_foreign_keys(name)
            } == {tuple(f.column_keys) for f in model.foreign_key_constraints}
            assert {
                row["name"]
                for row in inspector.get_indexes(name)
                if not row.get("duplicates_constraint")
            } == {index.name for index in model.indexes}
        command.downgrade(config, "0078_captured_cost_basis")
        assert not names & set(inspect(engine).get_table_names())
        command.upgrade(config, "0079_captured_report")
    finally:
        engine.dispose()


def test_complete_db2_and_persisted_read_only_path(report_database, monkeypatch):
    import test_cost_captured_basis_storage as storage
    from sqlalchemy import event, select
    from test_cost_census import read_session

    from reality.db.cost_captured_basis import CostCapturedBasis
    from reality.services import costing

    storage.test_complete_db2_replay_uses_the_original_selling_evidence(report_database)
    _, factory, _, _ = report_database
    with factory() as session:
        identity, tenant = session.execute(
            select(CostCapturedBasis.id, CostCapturedBasis.tenant_id)
        ).one()
    with read_session(factory) as session:
        built = costing.build_captured_cost_generation(session, tenant, identity)
        session.commit()
    statements = []
    with factory() as session:

        def forbidden(*args, **kwargs):
            raise AssertionError("Report must not flush")

        monkeypatch.setattr(session, "flush", forbidden)
        connection = session.connection()

        def record(conn, cursor, statement, *args):
            statements.append(statement)

        event.listen(connection, "before_cursor_execute", record)
        try:
            report = costing.captured_cost_report(
                session, tenant, built["generation_id"]
            )
        finally:
            event.remove(connection, "before_cursor_execute", record)
    group = report["groups"]["contribution"][0]
    assert group["db1"]["known"] == "570.0000"
    assert group["db2"]["known"] == "456.0000"
    assert group["db2"]["total"] is group["db2_rate"] is None
    assert statements and all(sql.lstrip().startswith("SELECT") for sql in statements)
    assert not any(
        "FROM movement" in sql or "FROM source_record" in sql for sql in statements
    )


def test_storage_refuses_wrong_basis_member_and_foreign_basis(report_database):
    import test_cost_captured_basis_storage as storage
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_cost_census import read_session

    from reality.services import core, costing

    factory, tenant, census, basis = storage.retained(report_database)
    with read_session(factory) as session:
        second = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="second"
        )
        built = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )
        session.commit()
    with factory() as session:
        other = core.create_tenant(session, "Foreign").id
        session.commit()
    sql = "INSERT INTO cost_generation (id,tenant_id,captured_basis_id,kind,algorithm_version,scope_key,state,inventory_count,contribution_count,output_hash) VALUES ('wrong',:tenant,:basis,'captured_review_selection_v1','captured-report-v1',repeat('a',64),'building',1,1,repeat('0',64))"
    with factory() as session, pytest.raises(DBAPIError):
        session.execute(text(sql), {"tenant": other, "basis": basis["basis_id"]})
    with factory() as session, pytest.raises(DBAPIError):
        session.execute(text(sql), {"tenant": tenant, "basis": second["basis_id"]})
        session.execute(
            text(
                "INSERT INTO cost_inventory_row (id,tenant_id,generation_id,inventory_basis_member_id,state) SELECT 'wrong-row',tenant_id,'wrong',inventory_basis_member_id,'unknown_at_capture' FROM cost_inventory_row WHERE tenant_id=:tenant AND generation_id=:generation"
            ),
            {"tenant": tenant, "generation": built["generation_id"]},
        )


def test_numeric_admission_rejects_rounding_and_overflow():
    from decimal import Decimal

    from reality.services.captured_report import _amount
    from reality.services.core import InvalidOperation

    assert _amount("0") == Decimal(0)
    assert _amount("99999999999999.9999") == Decimal("99999999999999.9999")
    assert _amount(None) is None
    for value in ("0.00001", "100000000000000", "NaN", "Infinity"):
        with pytest.raises(InvalidOperation):
            _amount(value)


def test_publication_conflict_rollback_and_newer_capture(report_database):
    import test_cost_captured_basis_storage as storage
    import test_cost_census_resolution as resolution
    from sqlalchemy import select
    from test_cost_census import read_session

    from reality.db.captured_report import CostPublication
    from reality.services import core, costing

    factory, tenant, census, basis = storage.retained(report_database)
    with read_session(factory) as session:
        first = costing.build_captured_cost_generation(
            session, tenant, basis["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session, pytest.raises(core.InvalidOperation, match="changed"):
        costing.publish_captured_cost_generation(
            session, tenant, first, expected_previous_id="wrong"
        )
    with factory() as session:
        costing.publish_captured_cost_generation(
            session, tenant, first, expected_previous_id=None
        )
        session.rollback()
    with factory() as session:
        assert (
            session.scalar(
                select(CostPublication.id).where(CostPublication.tenant_id == tenant)
            )
            is None
        )
        costing.publish_captured_cost_generation(
            session, tenant, first, expected_previous_id=None
        )
        session.commit()
    with read_session(factory) as session:
        equal = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="equal-cursor"
        )
        second = costing.build_captured_cost_generation(
            session, tenant, equal["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session, pytest.raises(core.InvalidOperation, match="Ambiguous"):
        costing.publish_captured_cost_generation(
            session, tenant, second, expected_previous_id=first
        )
    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    next_census = resolution.capture(
        factory,
        tenant,
        datetime.fromisoformat(basis["context"]["effective_at"]),
        request="newer",
    )
    with read_session(factory) as session:
        newer = costing.retain_captured_cost_basis(
            session, tenant, next_census, request_id="newer"
        )
        third = costing.build_captured_cost_generation(
            session, tenant, newer["basis_id"]
        )["generation_id"]
        session.commit()
    with factory() as session, pytest.raises(core.InvalidOperation, match="changed"):
        costing.publish_captured_cost_generation(
            session, tenant, third, expected_previous_id=None
        )
    with factory() as session:
        costing.publish_captured_cost_generation(
            session, tenant, third, expected_previous_id=first
        )
        session.commit()
    with factory() as session, pytest.raises(core.InvalidOperation, match="Obsolete"):
        costing.publish_captured_cost_generation(
            session, tenant, first, expected_previous_id=third
        )
    with factory() as session:
        assert (
            session.scalar(
                select(CostPublication.generation_id).where(
                    CostPublication.tenant_id == tenant
                )
            )
            == third
        )
        assert (
            costing.captured_cost_report(session, tenant, first)["generation_id"]
            == first
        )
