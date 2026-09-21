"""Retained discovery preserves observed evidence, never financial approval."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from test_cost_census import read_session, seed

from reality.services import core, costing


@pytest.fixture
def scheduled_database(postgres_database, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    # Service fixtures exercise the current model and therefore need the current
    # schema. Dedicated migration tests below remain pinned to exact revisions.
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    factory = sessionmaker(engine, expire_on_commit=False)
    try:
        with factory() as session:
            tenant = core.create_tenant(session, "Retained census").id
            session.commit()
        yield engine, factory, tenant, None
    finally:
        engine.dispose()


def retain(data, request="capture-1"):
    factory, tenant, cutoff, *_ = data
    with read_session(factory) as session:
        result = costing.retain_company_cost_census(
            session, tenant, cutoff, request_id=request
        )
        session.commit()
        return result


def test_retained_values_replay_and_original_read_only_discovery(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, cutoff, *_ = data
    capture = retain(data)
    assert capture["state"] == "sealed" and capture["publication_eligible"] is False
    assert "knowledge_at" not in capture
    assert retain(data) == capture
    with factory() as session:
        verified = costing.verify_company_cost_census(session, tenant, capture["id"])
        assert verified["verified"] and verified["counts"] == {
            "movement": 1,
            "document": 2,
            "line": 1,
            "source": 1,
        }
        page = costing.company_cost_census_members(
            session, tenant, capture["id"], family="line"
        )
        assert len(page["members"]) == 1
        assert page["members"][0]["observed_values"]["gross_amount"] == "10.0000"
        assert page["members"][0]["document_member_id"]
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="request"),
    ):
        costing.retain_company_cost_census(
            session, tenant, cutoff, request_id="capture-1", max_records=10
        )


def test_foreign_capture_and_member_reads_are_absent(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    capture = retain(data)
    with factory() as session:
        other = core.create_tenant(session, "Other").id
        session.commit()
    with factory() as session:
        for lookup in (costing.company_cost_census, costing.verify_company_cost_census):
            with pytest.raises(core.NotFound):
                lookup(session, other, capture["id"])
        with pytest.raises(core.NotFound):
            costing.company_cost_census_members(
                session, other, capture["id"], family="line"
            )
    assert retain(data)["tenant_id"] == tenant


def test_rollback_and_overflow_never_leave_durable_capture(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, cutoff, *_ = data
    with read_session(factory) as session:
        costing.retain_company_cost_census(
            session, tenant, cutoff, request_id="rollback"
        )
        session.rollback()
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="limit"),
    ):
        costing.retain_company_cost_census(
            session, tenant, cutoff, request_id="overflow", max_records=4
        )
    with factory() as session:
        assert (
            session.scalar(
                text(
                    "SELECT count(*) FROM cost_company_census WHERE tenant_id=:tenant"
                ),
                {"tenant": tenant},
            )
            == 0
        )


def test_sql_cannot_mutate_sealed_history(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    capture = retain(data)
    statements = [
        "UPDATE cost_company_census SET event_sequence=event_sequence+1 WHERE id=:id",
        "DELETE FROM cost_company_census WHERE id=:id",
        "UPDATE cost_company_census_line SET observed_values='{}'::jsonb WHERE census_id=:id",
        "DELETE FROM cost_company_census_source WHERE census_id=:id",
    ]
    for sql in statements:
        with factory() as session, pytest.raises(DBAPIError):
            session.execute(text(sql), {"id": capture["id"]})
    with factory() as session:
        assert costing.verify_company_cost_census(session, tenant, capture["id"])[
            "verified"
        ]


def test_pages_are_capture_bound_and_limits_are_strict(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    capture = retain(data)
    other = retain(data, "other")
    with factory() as session:
        first = costing.company_cost_census_members(
            session, tenant, capture["id"], family="document", limit=1
        )
        assert len(first["members"]) == 1 and first["next_cursor"]
        second = costing.company_cost_census_members(
            session,
            tenant,
            capture["id"],
            family="document",
            limit=1,
            cursor=first["next_cursor"],
        )
        assert len(second["members"]) == 1 and second["next_cursor"] is None
        assert first["members"][0]["id"] != second["members"][0]["id"]
        with pytest.raises(core.InvalidOperation, match="cursor"):
            costing.company_cost_census_members(
                session,
                tenant,
                other["id"],
                family="document",
                cursor=first["next_cursor"],
            )
        for limit in (0, 501, True):
            with pytest.raises(core.InvalidOperation, match="limit"):
                costing.company_cost_census_members(
                    session, tenant, capture["id"], family="document", limit=limit
                )


def test_later_manual_values_and_source_versions_do_not_rewrite_history(
    scheduled_database,
):
    data = seed(scheduled_database)
    factory, tenant, _, _, _, _, _, invoice, *_ = data
    old = retain(data)
    with factory() as session:
        snapshot = core.manual_document_line_snapshot(session, tenant, invoice)
        changed = {
            **snapshot["lines"][0],
            "description": "Revised service",
            "unit_price": "12",
            "gross_amount": "12",
        }
        core.correct_manual_document_lines(
            session,
            tenant,
            invoice,
            expected_revision=snapshot["revision"],
            lines=[changed],
        )
        replacement, _ = core.enqueue_source(
            session, tenant, "census_test", "unknown", "source", {"received": "changed"}
        )
        replacement_id = replacement.id
        session.commit()
    new = retain(data, "after-change")
    assert old["id"] != new["id"]
    with factory() as session:
        before = costing.company_cost_census_members(
            session, tenant, old["id"], family="line"
        )["members"][0]
        after = costing.company_cost_census_members(
            session, tenant, new["id"], family="line"
        )["members"][0]
        assert before["observed_values"]["gross_amount"] == "10.0000"
        assert after["observed_values"]["gross_amount"] == "12.0000"
        assert before["observed_values"]["description"] == "Service"
        assert after["observed_values"]["description"] == "Revised service"
        sources = costing.company_cost_census_members(
            session, tenant, new["id"], family="source"
        )["members"]
        assert sources[0]["source_record_id"] == replacement_id
        assert costing.verify_company_cost_census(session, tenant, old["id"])[
            "verified"
        ]
    assert retain(data) == old


def test_dirty_session_and_wrong_isolation_refuse(scheduled_database):
    from reality.db.core import Tenant

    data = seed(scheduled_database)
    factory, tenant, cutoff, *_ = data
    with read_session(factory) as session:
        obj = session.get(Tenant, tenant)
        obj.name = "Pending unrelated change"
        with pytest.raises(core.InvalidOperation, match="clean session"):
            costing.retain_company_cost_census(
                session, tenant, cutoff, request_id="dirty"
            )
        assert obj in session.dirty
    with (
        factory() as session,
        pytest.raises(core.InvalidOperation, match="REPEATABLE READ"),
    ):
        costing.retain_company_cost_census(
            session, tenant, cutoff, request_id="isolation"
        )


def test_partial_write_failure_rolls_back_savepoint_even_if_caller_commits(
    scheduled_database, monkeypatch
):
    from reality.services import cost_census_storage

    data = seed(scheduled_database)
    factory, tenant, cutoff, *_ = data

    def fail(*args):
        raise core.InvalidOperation("Injected verification failure")

    monkeypatch.setattr(cost_census_storage, "_verify", fail)
    with read_session(factory) as session:
        with pytest.raises(core.InvalidOperation, match="Injected"):
            costing.retain_company_cost_census(
                session, tenant, cutoff, request_id="failed"
            )
        session.commit()
    with factory() as session:
        assert (
            session.scalar(
                text(
                    "SELECT count(*) FROM cost_company_census WHERE tenant_id=:tenant"
                ),
                {"tenant": tenant},
            )
            == 0
        )


def test_concurrent_request_retries_once_in_fresh_transaction(scheduled_database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    data = seed(scheduled_database)
    factory, tenant, cutoff, *_ = data
    barrier = Barrier(2)

    def worker():
        try:
            with read_session(factory) as session:
                # Establish both snapshots before either inserts the request key.
                session.execute(text("SELECT count(*) FROM cost_company_census"))
                barrier.wait(timeout=10)
                result = costing.retain_company_cost_census(
                    session, tenant, cutoff, request_id="race"
                )
                session.commit()
                return result["id"]
        except DBAPIError as error:
            assert error.orig.sqlstate in ("23505", "40001")
            return retain(data, "race")["id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(lambda _: worker(), range(2)))
    assert first == second
    with factory() as session:
        assert (
            session.scalar(
                text(
                    "SELECT count(*) FROM cost_company_census WHERE tenant_id=:tenant"
                ),
                {"tenant": tenant},
            )
            == 1
        )


def test_reads_do_not_flush_or_recalculate_and_pages_stay_bounded(
    scheduled_database, monkeypatch
):
    from sqlalchemy import event

    data = seed(scheduled_database)
    factory, tenant, *_ = data
    capture = retain(data)

    def forbidden(*args, **kwargs):
        raise AssertionError("Retained inspection cannot flush or calculate")

    monkeypatch.setattr(costing, "inventory_cost", forbidden)
    statements = []
    with factory() as session:
        monkeypatch.setattr(session, "flush", forbidden)
        conn = session.connection()

        def track(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(conn, "before_cursor_execute", track)
        try:
            costing.company_cost_census_members(
                session, tenant, capture["id"], family="line", limit=1
            )
        finally:
            event.remove(conn, "before_cursor_execute", track)
    assert len(statements) == 2 and all(
        s.lstrip().startswith("SELECT") for s in statements
    )
    assert "LIMIT" in statements[-1]


def test_full_verification_detects_member_corruption(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, *_ = data
    capture = retain(data)
    with factory() as session:
        # Privileged corruption injection; normal SQL mutation is separately refused.
        session.execute(
            text(
                "ALTER TABLE cost_company_census_line DISABLE TRIGGER guard_company_census_member"
            )
        )
        session.execute(
            text(
                "UPDATE cost_company_census_line SET observed_values='{}'::jsonb WHERE tenant_id=:tenant AND census_id=:id"
            ),
            {"tenant": tenant, "id": capture["id"]},
        )
        session.execute(
            text(
                "ALTER TABLE cost_company_census_line ENABLE TRIGGER guard_company_census_member"
            )
        )
        session.commit()
    with factory() as session:
        with pytest.raises(core.InvalidOperation, match="integrity"):
            costing.verify_company_cost_census(session, tenant, capture["id"])
        with pytest.raises(core.InvalidOperation, match="integrity"):
            costing.company_cost_census_members(
                session, tenant, capture["id"], family="line"
            )


def test_retained_line_removal_has_domain_guidance_and_preserves_history(
    scheduled_database,
):
    data = seed(scheduled_database)
    factory, tenant, _, _, _, _, _, invoice, *_ = data
    capture = retain(data)
    with factory() as session:
        snapshot = core.manual_document_line_snapshot(session, tenant, invoice)
        # Replace the old identity with a new line; retained old identity cannot disappear.
        replacement = {**snapshot["lines"][0], "id": None, "source_line_id": "new-line"}
        with pytest.raises(
            core.InvalidOperation, match="Retained census evidence cannot be removed"
        ):
            core.correct_manual_document_lines(
                session,
                tenant,
                invoice,
                expected_revision=snapshot["revision"],
                lines=[replacement],
            )
        assert costing.verify_company_cost_census(session, tenant, capture["id"])[
            "verified"
        ]


def test_tenant_and_same_census_header_constraints_reject_invalid_links(
    scheduled_database,
):
    from sqlalchemy import insert

    from reality.db.core import now, uid
    from reality.db.cost_census import (
        CostCompanyCensus,
        CostCompanyCensusLine,
        CostCompanyCensusMovement,
    )

    data = seed(scheduled_database)
    factory, tenant, cutoff, _, _, movement, _, _, line, *_ = data
    capture = retain(data)
    with factory() as session:
        other = core.create_tenant(session, "Other tenant").id
        session.commit()
        header_member = costing.company_cost_census_members(
            session, tenant, capture["id"], family="document"
        )["members"][0]["id"]

    def building(session, owner, key):
        identity = uid("test")
        session.execute(
            insert(CostCompanyCensus.__table__).values(
                id=identity,
                tenant_id=owner,
                request_id=key,
                request_hash="0" * 64,
                effective_at=cutoff,
                observed_at=now(),
                snapshot_identity="test",
                event_sequence=0,
                input_schema_version=1,
                state="building",
                movement_count=0,
                document_count=0,
                line_count=0,
                source_count=0,
                content_hash="0" * 64,
            )
        )
        return identity

    with factory() as session:
        header = building(session, other, "foreign")
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(
                insert(CostCompanyCensusMovement.__table__).values(
                    id=uid("test"),
                    tenant_id=other,
                    census_id=header,
                    movement_id=movement,
                    observed_values={},
                    content_hash="0" * 64,
                )
            )
    with factory() as session:
        header = building(session, tenant, "wrong-capture")
        with pytest.raises(DBAPIError), session.begin_nested():
            session.execute(
                insert(CostCompanyCensusLine.__table__).values(
                    id=uid("test"),
                    tenant_id=tenant,
                    census_id=header,
                    document_line_id=line,
                    document_member_id=header_member,
                    observed_values={},
                    content_hash="0" * 64,
                )
            )


def test_retain_rejects_missing_tenant_before_writing(scheduled_database):
    data = seed(scheduled_database)
    factory, _, cutoff, *_ = data
    with read_session(factory) as session, pytest.raises(core.NotFound):
        costing.retain_company_cost_census(
            session, "missing", cutoff, request_id="absent"
        )


def test_capture_keeps_one_snapshot_while_intake_commits(scheduled_database):
    data = seed(scheduled_database)
    factory, tenant, cutoff, item, location, *_ = data
    with read_session(factory) as session:
        session.execute(text("SELECT count(*) FROM cost_company_census"))
        with factory() as writer:
            writer.execute(text("SET LOCAL lock_timeout='300ms'"))
            core.record_movement(
                writer,
                tenant,
                "receipt",
                item,
                "1",
                to_location_id=location,
                occurred_at=cutoff,
            )
            writer.commit()
        old = costing.retain_company_cost_census(
            session, tenant, cutoff, request_id="before-intake"
        )
        session.commit()
    new = retain(data, "after-intake")
    assert old["movement_count"] == 1 and new["movement_count"] == 2
    assert new["event_sequence"] > old["event_sequence"]


@pytest.mark.parametrize("bound", ["MEMBER_BYTES", "CAPTURE_BYTES"])
def test_byte_overflow_refuses_before_any_durable_write(
    scheduled_database, monkeypatch, bound
):
    from reality.domain import cost_census

    data = seed(scheduled_database)
    factory, tenant, cutoff, *_ = data
    monkeypatch.setattr(cost_census, bound, 10)
    with read_session(factory) as session:
        with pytest.raises(core.InvalidOperation, match="byte limit"):
            costing.retain_company_cost_census(
                session, tenant, cutoff, request_id="too-large"
            )
        session.commit()
    with factory() as session:
        assert (
            session.scalar(
                text(
                    "SELECT count(*) FROM cost_company_census WHERE tenant_id=:tenant"
                ),
                {"tenant": tenant},
            )
            == 0
        )


def test_sql_cannot_add_members_after_sealing(scheduled_database):
    from sqlalchemy import insert

    from reality.db.cost_census import CostCompanyCensusMovement

    data = seed(scheduled_database)
    factory, tenant, _, _, _, _, future, *_ = data
    capture = retain(data)
    with factory() as session, pytest.raises(DBAPIError, match="building same-tenant"):
        session.execute(
            insert(CostCompanyCensusMovement.__table__).values(
                id="unapproved-member",
                tenant_id=tenant,
                census_id=capture["id"],
                movement_id=future,
                observed_values={},
                content_hash="0" * 64,
            )
        )


def test_a_line_cannot_name_another_company_s_header_at_all(
    scheduled_database,
):
    """The capture used to have to notice this; now it cannot happen.

    A document line pointing at another company's document was writable, and the
    capture had to refuse the whole census rather than quietly drop the line.
    Since spec 181 FR-005 a reference between two company-scoped tables carries
    the company, so the malformed link is refused where it is written. The
    service's own guard remains for any other way a header goes missing; this is
    simply no longer one of them.
    """
    data = seed(scheduled_database)
    factory, tenant, _cutoff, _, _, _, _, _, line, *_ = data
    with factory() as session:
        other = core.create_tenant(session, "Other").id
        party = core.create_party(session, other, "Other customer", "customer")
        document = core.create_document(
            session, other, "sales_invoice", "PRIVATE", party.id, "0"
        )
        # The schema used to permit this malformed cross-tenant link, and the
        # service had to be careful not to omit the line. Since spec 181 FR-005
        # it cannot be written at all, which is where such a rule belongs.
        with pytest.raises(IntegrityError), session.begin_nested():
            session.execute(
                text(
                    "UPDATE document_line SET document_id=:parent "
                    "WHERE tenant_id=:tenant AND id=:line"
                ),
                {"parent": document.id, "tenant": tenant, "line": line},
            )
            session.flush()
        session.commit()
