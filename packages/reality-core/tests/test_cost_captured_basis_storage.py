"""Pinned review selection survives later intake without changing financial authority."""

import pytest
import test_cost_census_resolution as resolution
import test_cost_census_storage as census_storage
from alembic import command
from alembic.config import Config
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError
from test_cost_captured_basis import example
from test_cost_census import read_session, seed

from reality.domain.cost_census import digest
from reality.services import core, costing


@pytest.fixture
def scheduled_database(postgres_database, monkeypatch):
    fixture = census_storage.scheduled_database.__wrapped__(
        postgres_database, monkeypatch
    )
    database = next(fixture)
    try:
        command.upgrade(Config("alembic.ini"), "0084_inventory_ownership_parts")
        yield database
    finally:
        fixture.close()


def retained(database, *, reviewed=True):
    if reviewed:
        factory, business, _, cutoff, _ = resolution.setup_review(
            database, contribution=True
        )
        tenant = business.tenant.id
        census = resolution.capture(factory, tenant, cutoff)
    else:
        data = seed(database)
        factory, tenant, *_ = data
        census = census_storage.retain(data)["id"]
    with read_session(factory) as session:
        basis = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="retain"
        )
        session.commit()
    return factory, tenant, census, basis


def test_v1_verification_and_v2_lifecycle_independence():
    from reality.domain.cost_captured_basis import (
        assemble_captured_basis,
        verify_captured_basis,
    )

    header, result = example()
    value = assemble_captured_basis(header, result, ["item"], ["line"])
    assert value["version"] == "captured-review-basis-v2"
    verify_captured_basis(value)
    held = value | {"retained": True, "basis_id": "durable"}
    verify_captured_basis(held)
    old = {key: part for key, part in value.items() if key != "digest"}
    old["version"] = "captured-review-basis-v1"
    old["digest"] = digest(old)
    verify_captured_basis(old)
    for changed in (
        old | {"retained": True},
        value | {"version": "future"},
        value | {"digest": "0" * 64},
    ):
        with pytest.raises(ValueError):
            verify_captured_basis(changed)


def test_retain_retry_and_pinned_replay(scheduled_database, monkeypatch):
    factory, tenant, census, basis = retained(scheduled_database)
    assert basis["retained"] and not basis["publication_eligible"]
    with read_session(factory) as session:
        replay = costing.replay_captured_cost_basis(session, tenant, basis["basis_id"])
        assert replay["inventory"][0]["result"]["acquisition_value"] == "420.0000"
        assert replay["contribution"][0]["result"]["db1"] == "570.0000"
        assert replay["contribution"][0]["result"]["db2"] is None
    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()

    def forbidden(*args, **kwargs):
        raise AssertionError("A retry/metadata read cannot resolve latest reviews")

    from reality.services import cost_census_resolution

    monkeypatch.setattr(cost_census_resolution, "_inventory_review", forbidden)
    monkeypatch.setattr(cost_census_resolution, "_contribution_review", forbidden)
    with read_session(factory) as session:
        assert (
            costing.retain_captured_cost_basis(
                session, tenant, census, request_id="retain"
            )
            == basis
        )
        assert costing.captured_cost_basis(session, tenant, basis["basis_id"]) == basis
        assert (
            costing.replay_captured_cost_basis(session, tenant, basis["basis_id"])[
                "captured_basis"
            ]
            == basis
        )
        with pytest.raises(core.InvalidOperation, match="request"):
            costing.retain_captured_cost_basis(
                session, tenant, census, request_id="retain", max_subjects=9
            )


def test_unknown_subjects_and_metadata_read_are_select_only(
    scheduled_database, monkeypatch
):
    factory, tenant, _, basis = retained(scheduled_database, reviewed=False)
    statements = []
    with read_session(factory) as session:

        def forbidden(*args, **kwargs):
            raise AssertionError("Metadata cannot calculate or flush")

        monkeypatch.setattr(session, "flush", forbidden)
        monkeypatch.setattr(costing, "inventory_cost", forbidden)
        monkeypatch.setattr(costing, "reviewed_contribution", forbidden)

        def record(conn, cursor, statement, *args):
            statements.append(statement)

        connection = session.connection()
        event.listen(connection, "before_cursor_execute", record)
        try:
            result = costing.captured_cost_basis(session, tenant, basis["basis_id"])
        finally:
            event.remove(connection, "before_cursor_execute", record)
    assert result == basis
    assert result["gaps"]["documents"] and result["gaps"]["sources"]
    assert all(value["unknown"] == 1 for value in result["coverage"].values())
    assert statements and all(sql.lstrip().startswith("SELECT") for sql in statements)


def test_foreign_and_clean_transaction_boundaries(scheduled_database):
    factory, tenant, census, basis = retained(scheduled_database)
    with factory() as session:
        other = core.create_tenant(session, "Other").id
        session.commit()
    with read_session(factory) as session:
        for operation in (
            costing.captured_cost_basis,
            costing.replay_captured_cost_basis,
        ):
            with pytest.raises(core.NotFound):
                operation(session, other, basis["basis_id"])
        with pytest.raises(core.NotFound):
            costing.retain_captured_cost_basis(
                session, other, census, request_id="foreign"
            )
        for limit in (True, 0, 11):
            with pytest.raises(core.InvalidOperation):
                costing.retain_captured_cost_basis(
                    session, tenant, census, request_id="bad", max_subjects=limit
                )
    with (
        factory() as session,
        pytest.raises(core.InvalidOperation, match="REPEATABLE READ"),
    ):
        costing.captured_cost_basis(session, tenant, basis["basis_id"])
    from reality.db.core import Tenant

    with read_session(factory) as session:
        session.add(Tenant(id="unflushed", name="Dirty"))
        with pytest.raises(core.InvalidOperation, match="clean"):
            costing.retain_captured_cost_basis(
                session, tenant, census, request_id="dirty"
            )


def test_rollback_and_caught_failure_leave_no_partial_basis(
    scheduled_database, monkeypatch
):
    from reality.services import cost_captured_basis as service

    factory, tenant, census, _ = retained(scheduled_database)
    with read_session(factory) as session:
        costing.retain_captured_cost_basis(
            session, tenant, census, request_id="rollback"
        )
        session.rollback()
    original = service._read

    def fail(*args, **kwargs):
        raise core.InvalidOperation("injected verification failure")

    monkeypatch.setattr(service, "_read", fail)
    with read_session(factory) as session:
        with pytest.raises(core.InvalidOperation, match="injected"):
            costing.retain_captured_cost_basis(
                session, tenant, census, request_id="failure"
            )
        session.commit()
    monkeypatch.setattr(service, "_read", original)
    with factory() as session:
        assert (
            session.scalar(
                text("SELECT count(*) FROM cost_captured_basis WHERE tenant_id=:t"),
                {"t": tenant},
            )
            == 1
        )


@pytest.mark.parametrize(
    "table",
    [
        "cost_captured_basis",
        "cost_captured_inventory_basis",
        "cost_captured_contribution_basis",
    ],
)
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_sealed_sql_immutability(scheduled_database, table, operation):
    factory, tenant, _, _ = retained(scheduled_database)
    statement = (
        f"DELETE FROM {table} WHERE tenant_id=:tenant"
        if operation == "delete"
        else f"UPDATE {table} SET id=id WHERE tenant_id=:tenant"
    )
    with factory() as session, pytest.raises(DBAPIError, match="immutable"):
        session.execute(text(statement), {"tenant": tenant})


def test_replay_refuses_altered_canonical_result(scheduled_database, monkeypatch):
    factory, tenant, _, basis = retained(scheduled_database)
    original = costing.inventory_cost

    def changed(*args, **kwargs):
        return original(*args, **kwargs) | {"acquisition_value": "999.0000"}

    monkeypatch.setattr(costing, "inventory_cost", changed)
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="digest"),
    ):
        costing.replay_captured_cost_basis(session, tenant, basis["basis_id"])


def test_concurrent_retry_uses_a_fresh_transaction(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    factory, tenant, census, _ = retained(scheduled_database, reviewed=False)
    barrier = Barrier(2)

    def worker():
        try:
            with read_session(factory) as session:
                session.execute(text("SELECT count(*) FROM cost_captured_basis"))
                barrier.wait(timeout=10)
                result = costing.retain_captured_cost_basis(
                    session, tenant, census, request_id="race"
                )
                session.commit()
                return result["basis_id"]
        except DBAPIError as error:
            assert error.orig.sqlstate in ("23505", "40001")
            with read_session(factory) as session:
                return costing.retain_captured_cost_basis(
                    session, tenant, census, request_id="race"
                )["basis_id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(lambda _: worker(), range(2)))
    assert first == second
    with factory() as session:
        assert (
            session.scalar(
                text(
                    "SELECT count(*) FROM cost_captured_basis WHERE tenant_id=:t AND request_id='race'"
                ),
                {"t": tenant},
            )
            == 1
        )


@pytest.mark.parametrize(
    "fault", ["member_payload", "missing_member", "header_coverage", "header_version"]
)
def test_corrupt_retained_content_refuses(scheduled_database, fault):
    factory, tenant, _, basis = retained(scheduled_database, reviewed=False)
    table = (
        "cost_captured_inventory_basis"
        if fault in ("member_payload", "missing_member")
        else "cost_captured_basis"
    )
    with factory() as session:
        session.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
        if fault == "member_payload":
            session.execute(
                text(
                    "UPDATE cost_captured_inventory_basis SET observations=observations || '{\"gaps\":[]}'::jsonb WHERE tenant_id=:t"
                ),
                {"t": tenant},
            )
        elif fault == "missing_member":
            session.execute(
                text("DELETE FROM cost_captured_inventory_basis WHERE tenant_id=:t"),
                {"t": tenant},
            )
        elif fault == "header_coverage":
            session.execute(
                text(
                    "UPDATE cost_captured_basis SET observations=jsonb_set(observations,'{coverage,db1,covered}','1') WHERE tenant_id=:t"
                ),
                {"t": tenant},
            )
        else:
            # Model version is SQL constrained; corruption must fail there already.
            with pytest.raises(DBAPIError):
                session.execute(
                    text(
                        "UPDATE cost_captured_basis SET basis_version='future' WHERE tenant_id=:t"
                    ),
                    {"t": tenant},
                )
            session.rollback()
            return
        session.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))
        session.commit()
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="digest"),
    ):
        costing.captured_cost_basis(session, tenant, basis["basis_id"])


def test_byte_overflow_does_not_persist(scheduled_database, monkeypatch):
    from reality.domain import cost_captured_basis as domain

    factory, tenant, census, _ = retained(scheduled_database, reviewed=False)
    monkeypatch.setattr(domain, "MEMBER_BYTES", 10)
    with read_session(factory) as session:
        with pytest.raises(core.InvalidOperation, match="byte limit"):
            costing.retain_captured_cost_basis(
                session, tenant, census, request_id="oversized"
            )
        session.commit()
    with factory() as session:
        assert (
            session.scalar(
                text("SELECT count(*) FROM cost_captured_basis WHERE tenant_id=:t"),
                {"t": tenant},
            )
            == 1
        )


def test_sealed_insertion_and_foreign_review_fk_refuse(scheduled_database):
    from sqlalchemy import insert, select

    from reality.db.cost_captured_basis import (
        CostCapturedBasis,
        CostCapturedInventoryBasis,
    )

    factory, tenant, _, basis = retained(scheduled_database)
    _, other, _, _ = retained(scheduled_database)
    header, member = CostCapturedBasis.__table__, CostCapturedInventoryBasis.__table__
    with factory() as session:
        row = dict(
            session.execute(select(member).where(member.c.tenant_id == tenant))
            .mappings()
            .one()
        )
        foreign_review = session.scalar(
            select(member.c.review_id).where(member.c.tenant_id == other)
        )
        parent = dict(
            session.execute(select(header).where(header.c.id == basis["basis_id"]))
            .mappings()
            .one()
        )
    with factory() as session, pytest.raises(DBAPIError, match="building"):
        session.execute(insert(member).values(**(row | {"id": core.uid("member")})))
    parent.update(
        id=core.uid("basis"), request_id="building", state="building", sealed_at=None
    )
    with factory() as session:
        session.execute(insert(header).values(**parent))
        with pytest.raises(DBAPIError, match="foreign key"):
            session.execute(
                insert(member).values(
                    **(
                        row
                        | {
                            "id": core.uid("member"),
                            "basis_id": parent["id"],
                            "review_id": foreign_review,
                        }
                    )
                )
            )
        session.rollback()
    with factory() as session, pytest.raises(DBAPIError, match="foreign key"):
        session.execute(insert(header).values(**(parent | {"tenant_id": other})))


def test_complete_db2_replay_uses_the_original_selling_evidence(scheduled_database):
    from sqlalchemy import select

    from reality.db.cost_census import CostCompanyCensus

    resolution.test_confirmed_db2_uses_existing_selling_cost_proof(scheduled_database)
    _, factory, _, _ = scheduled_database
    with factory() as session:
        census, tenant = session.execute(
            select(CostCompanyCensus.id, CostCompanyCensus.tenant_id)
        ).one()
    with read_session(factory) as session:
        held = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="full-db2"
        )
        session.commit()
    with read_session(factory) as session:
        replay = costing.replay_captured_cost_basis(session, tenant, held["basis_id"])
    assert replay["contribution"][0]["result"]["db2"] == "456.0000"
    assert replay["captured_basis"]["coverage"]["db2"]["covered"] == 1


def test_historical_only_basis_is_not_upgraded_by_retention(scheduled_database):
    factory, tenant, census, _ = retained(scheduled_database)
    with read_session(factory) as session:
        cutoff = costing.company_cost_census(session, tenant, census)["effective_at"]
    from datetime import datetime

    with factory() as session:
        core.emit_business_event(session, tenant, "test.later", "tenant", tenant, {})
        session.commit()
    later = resolution.capture(factory, tenant, datetime.fromisoformat(cutoff), "later")
    with read_session(factory) as session:
        held = costing.retain_captured_cost_basis(
            session, tenant, later, request_id="historical-only"
        )
        session.commit()
    with read_session(factory) as session:
        replay = costing.replay_captured_cost_basis(session, tenant, held["basis_id"])
    assert replay["inventory"][0]["result"] is None
    assert replay["inventory"][0]["basis_result"]["acquisition_value"] == "420.0000"
    assert held["coverage"]["acquisition"]["covered"] == 0


@pytest.mark.parametrize("limit", ["MEMBER_BYTES", "BASIS_BYTES"])
def test_both_domain_byte_limits_refuse(limit, monkeypatch):
    from reality.domain import cost_captured_basis as domain

    header, resolved = example()
    basis = domain.assemble_captured_basis(header, resolved, ["item"], ["line"])
    monkeypatch.setattr(domain, limit, 10)
    with pytest.raises(ValueError, match="byte limit"):
        domain.verify_captured_basis(basis)


def test_empty_basis_retains_empty_coverage_without_zero_money(scheduled_database):
    _, factory, tenant, _ = scheduled_database
    census = resolution.capture(factory, tenant, core.now())
    with read_session(factory) as session:
        held = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="empty"
        )
        session.commit()
    with read_session(factory) as session:
        replay = costing.replay_captured_cost_basis(session, tenant, held["basis_id"])
    assert all(row["state"] == "empty" for row in held["coverage"].values())
    assert replay["inventory"] == replay["contribution"] == []


def test_same_tenant_wrong_review_subject_refuses(scheduled_database):
    import test_cost_review_relevance as relevance
    from sqlalchemy import select, update

    from reality.db.cost_captured_basis import CostCapturedInventoryBasis
    from reality.db.cost_census import CostCompanyCensus

    relevance.test_joint_inventory_and_contribution_reviews_coexist(scheduled_database)
    _, factory, _, _ = scheduled_database
    with factory() as session:
        census, tenant = session.execute(
            select(CostCompanyCensus.id, CostCompanyCensus.tenant_id)
        ).one()
    with read_session(factory) as session:
        held = costing.retain_captured_cost_basis(
            session, tenant, census, request_id="joint"
        )
        session.commit()
    table = CostCapturedInventoryBasis.__table__
    with factory() as session:
        rows = (
            session.execute(select(table).where(table.c.tenant_id == tenant))
            .mappings()
            .all()
        )
        first = dict(rows[0])
        first["review_id"] = rows[1]["review_id"]
        first["content_hash"] = digest(
            {key: value for key, value in first.items() if key != "content_hash"}
        )
        session.execute(
            text("ALTER TABLE cost_captured_inventory_basis DISABLE TRIGGER USER")
        )
        session.execute(
            update(table)
            .where(table.c.tenant_id == tenant, table.c.id == first["id"])
            .values(review_id=first["review_id"], content_hash=first["content_hash"])
        )
        session.execute(
            text("ALTER TABLE cost_captured_inventory_basis ENABLE TRIGGER USER")
        )
        session.commit()
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="digest"),
    ):
        costing.captured_cost_basis(session, tenant, held["basis_id"])
