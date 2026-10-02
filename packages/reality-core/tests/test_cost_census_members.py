"""Exact typed census storage preserves observations and protected admission."""

import queue
import threading
import time
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, insert, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from test_cost_census import seed
from test_cost_census_storage import retain

from reality.db.core import Base, now
from reality.services import core, costing
from reality.services.cost_census_storage import _content_hash, _member_hash

FAMILIES = {
    family: "cost_company_census_" + family
    for family in ("movement", "document", "line", "source")
}
STORE = "cost_company_census_member"


def rows(connection, tenant, census):
    return {
        family: [
            dict(r)
            for r in connection.execute(
                text(
                    f"SELECT * FROM {name} WHERE tenant_id=:t AND census_id=:c ORDER BY id"
                ),
                {"t": tenant, "c": census},
            ).mappings()
        ]
        for family, name in FAMILIES.items()
    }


def building(session, tenant, original):
    header = dict(
        session.execute(
            text("SELECT * FROM cost_company_census WHERE tenant_id=:t AND id=:c"),
            {"t": tenant, "c": original},
        )
        .mappings()
        .one()
    )
    header.update(
        id="cns_" + uuid4().hex,
        request_id=uuid4().hex,
        state="building",
        sealed_at=None,
    )
    session.execute(
        insert(Base.metadata.tables["cost_company_census"]).values(**header)
    )
    return header


def seed_capture(engine):
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        tenant = core.create_tenant(session, "Typed census").id
        session.commit()
    data = seed((engine, factory, tenant, None))
    original = retain(data)
    with factory() as session:
        members = rows(session.connection(), tenant, original["id"])
        line = members["line"][0]
        members["document"] = [
            r for r in members["document"] if r["id"] == line["document_member_id"]
        ]
        header = building(session, tenant, original["id"])
        selected = {}
        for family in FAMILIES:
            row = dict(members[family][0])
            row.update(id="collision", census_id=header["id"])
            if family == "line":
                row["document_member_id"] = "collision"
            if family == "source":
                row["interpretation_outcome_id"] = None
            row["content_hash"] = _member_hash(row)
            selected[family] = [row]
            session.execute(
                insert(Base.metadata.tables[FAMILIES[family]]).values(**row)
            )
            header[family + "_count"] = 1
        header["content_hash"] = _content_hash(header, selected)
        session.execute(
            text(
                "UPDATE cost_company_census SET state='sealed',sealed_at=:at,"
                "movement_count=1,document_count=1,line_count=1,source_count=1,"
                "content_hash=:h WHERE tenant_id=:t AND id=:c"
            ),
            {"at": now(), "h": header["content_hash"], "t": tenant, "c": header["id"]},
        )
        session.commit()
    return factory, tenant, header["id"], original, data


@pytest.fixture
def held(postgres_database, monkeypatch):
    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    command.upgrade(Config("alembic.ini"), "head")
    engine = create_engine(postgres_database)
    try:
        first = seed_capture(engine)
        second = seed_capture(engine)
        yield engine, first, second
    finally:
        engine.dispose()


def assert_indexes(connection):
    inspector = inspect(connection)
    for name in (STORE, "cost_company_contribution_input"):
        keys = [
            tuple(i["column_names"])
            for i in inspector.get_indexes(name)
            if not i.get("dialect_options", {}).get("postgresql_where")
        ]
        keys += [tuple(inspector.get_pk_constraint(name)["constrained_columns"])]
        keys += [
            tuple(c["column_names"]) for c in inspector.get_unique_constraints(name)
        ]
        for fk in inspector.get_foreign_keys(name):
            columns = tuple(fk["constrained_columns"])
            assert any(k[: len(columns)] == columns for k in keys), (name, columns)


def test_exact_schema_real_typed_links_and_indexes(held):
    engine, _, _ = held
    with engine.connect() as connection:
        inspector = inspect(connection)
        assert STORE in inspector.get_table_names()
        assert set(FAMILIES.values()) <= set(inspector.get_view_names())
        assert not set(FAMILIES.values()) & set(inspector.get_table_names())
        for name in FAMILIES.values():
            assert [c["name"] for c in inspector.get_columns(name)] == [
                c.name
                for c in Base.metadata.tables[name].c
                if c.name not in ("id", "tenant_id")
            ] + ["id", "tenant_id"]
        assert len(inspector.get_foreign_keys(STORE)) == 8
        consumer = next(
            f
            for f in inspector.get_foreign_keys("cost_company_contribution_input")
            if f["constrained_columns"] == ["tenant_id", "census_line_id"]
        )
        assert consumer["referred_table"] == STORE
        assert consumer["referred_columns"] == ["tenant_id", "line_member_identity"]
        assert_indexes(connection)


def test_history_collision_namespaces_and_null_outcome(held):
    engine, first, second = held
    for factory, tenant, census, original, data in (first, second):
        with factory() as session:
            assert costing.verify_company_cost_census(session, tenant, census)[
                "verified"
            ]
            for family in FAMILIES:
                page = costing.company_cost_census_members(
                    session, tenant, census, family=family
                )
                assert len(page["members"]) == 1
                assert page["members"][0]["id"] == "collision"
                assert set(page["members"][0]) == set(
                    Base.metadata.tables[FAMILIES[family]].c.keys()
                )
            source = costing.company_cost_census_members(
                session, tenant, census, family="source"
            )
            assert source["members"][0]["interpretation_outcome_id"] is None
        assert retain(data) == original
    with engine.connect() as connection:
        assert (
            connection.scalar(
                text(f"SELECT count(*) FROM {STORE} WHERE id='collision'")
            )
            == 8
        )


def test_insert_returning_bulk_and_forbidden_mutations(held):
    engine, first, _ = held
    factory, tenant, census, _, _ = first
    with factory() as session:
        original = rows(session.connection(), tenant, census)
        header = building(session, tenant, census)
        for family, name in FAMILIES.items():
            row = dict(original[family][0])
            row["census_id"] = header["id"]
            row["id"] = "new-member"
            if family == "line":
                row["document_member_id"] = "new-member"
            table = Base.metadata.tables[name]
            assert (
                session.execute(insert(table).returning(table.c.id), [row]).scalar_one()
                == "new-member"
            )
        session.commit()
    for name in (*FAMILIES.values(), STORE):
        for operation in ("UPDATE", "DELETE"):
            statement = (
                f"UPDATE {name} SET content_hash=content_hash"
                if operation == "UPDATE"
                else f"DELETE FROM {name}"
            ) + " WHERE tenant_id=:t AND census_id=:c"
            with (
                engine.begin() as connection,
                pytest.raises(DBAPIError, match="immutable"),
            ):
                connection.execute(text(statement), {"t": tenant, "c": header["id"]})
    with engine.begin() as connection:
        assert (
            connection.execute(
                text(f"DELETE FROM {FAMILIES['source']} WHERE id='absent'")
            ).rowcount
            == 0
        )
    with factory() as session, pytest.raises(DBAPIError, match="building same-tenant"):
        row = dict(original["movement"][0])
        row["id"] = "after-seal"
        session.execute(
            insert(Base.metadata.tables[FAMILIES["movement"]]).values(**row)
        )


def test_physical_shape_and_document_family_references(held):
    engine, first, second = held
    factory, tenant, census, _, _ = first
    with factory() as session:
        header = building(session, tenant, census)
        originals = rows(session.connection(), tenant, census)
        session.commit()
    base = dict(originals["movement"][0])
    base.update(id="new-member", census_id=header["id"], member_family="movement")
    invalid = [
        dict(base, member_family="invalid"),
        dict(base, movement_id=None),
        dict(base, document_id=originals["document"][0]["document_id"]),
        dict(base, movement_id="absent"),
        dict(base, tenant_id=second[1]),
        dict(base, interpretation_outcome_id="absent"),
    ]
    for row in invalid:
        with engine.begin() as connection, pytest.raises(DBAPIError):
            connection.execute(insert(Base.metadata.tables[STORE]).values(**row))
    with factory() as session:
        wrong = dict(originals["movement"][0])
        wrong["census_id"] = header["id"]
        wrong["id"] = "new-member"
        session.execute(
            insert(Base.metadata.tables[FAMILIES["movement"]]).values(**wrong)
        )
        session.commit()
    line = dict(originals["line"][0])
    line["census_id"] = header["id"]
    line["id"] = "new-line"
    line["document_member_id"] = "new-member"
    # The equal ID names a movement in this capture and a document in another.
    with factory() as session, pytest.raises(IntegrityError):
        session.execute(insert(Base.metadata.tables[FAMILIES["line"]]).values(**line))
    with factory() as session, pytest.raises(IntegrityError):
        session.execute(
            insert(Base.metadata.tables[FAMILIES["movement"]]).values(**wrong)
        )


@pytest.mark.parametrize("seal_first", [True, False])
def test_insert_and_seal_serialize_on_same_parent(held, seal_first):
    engine, first, _ = held
    factory, tenant, census, _, _ = first
    with factory() as session:
        header = building(session, tenant, census)
        row = dict(rows(session.connection(), tenant, census)["movement"][0])
        row["census_id"] = header["id"]
        row["id"] = "racing-member"
        session.commit()
    seal = text(
        "UPDATE cost_company_census SET state='sealed',sealed_at=:at WHERE tenant_id=:t AND id=:c"
    )
    args = {"at": now(), "t": tenant, "c": header["id"]}
    insert_stmt = insert(Base.metadata.tables[FAMILIES["movement"]]).values(**row)
    messages = queue.Queue()

    def competitor():
        try:
            with engine.begin() as connection:
                connection.execute(text("SET LOCAL lock_timeout='15s'"))
                messages.put(
                    ("pid", connection.scalar(text("SELECT pg_backend_pid()")))
                )
                connection.execute(
                    insert_stmt if seal_first else seal, {} if seal_first else args
                )
            messages.put(("result", "ok"))
        except DBAPIError as error:
            messages.put(("result", str(error)))

    with engine.connect() as owner:
        tx = owner.begin()
        owner.execute(seal if seal_first else insert_stmt, args if seal_first else {})
        thread = threading.Thread(target=competitor)
        thread.start()
        pid = messages.get(timeout=10)[1]
        deadline = time.monotonic() + 10
        blocked = False
        while time.monotonic() < deadline:
            with engine.connect() as observer:
                blocked = bool(
                    observer.scalar(
                        text("SELECT cardinality(pg_blocking_pids(:p))"), {"p": pid}
                    )
                )
            if blocked:
                break
            threading.Event().wait(0.02)
        try:
            assert blocked, (
                "Must observe a real database lock wait, not infer it from elapsed time"
            )
        finally:
            tx.commit()
            thread.join(timeout=20)
        assert not thread.is_alive()
    result = messages.get(timeout=2)[1]
    assert ("building same-tenant" in result) if seal_first else result == "ok"


def test_partial_repeated_metadata_lifecycle(postgres_database):
    from reality.db.cost_census_members import storage
    from reality.db.schema_views import include_schema_object

    assert include_schema_object(storage, STORE, "table", False, None)
    for name in FAMILIES.values():
        assert not include_schema_object(
            Base.metadata.tables[name], name, "table", False, None
        )

    selected = set()

    def visit(table):
        if table in selected:
            return
        selected.add(table)
        for fk in table.foreign_key_constraints:
            visit(fk.referred_table)

    visit(storage)
    selected.update(Base.metadata.tables[n] for n in FAMILIES.values())
    engine = create_engine(postgres_database)
    try:
        for _ in range(2):
            Base.metadata.create_all(engine, tables=list(selected))
            Base.metadata.create_all(engine, tables=list(selected))
            Base.metadata.drop_all(engine, tables=list(selected))
            with engine.connect() as connection:
                assert not connection.scalar(
                    text(
                        "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname='guard_company_census_member_store' OR proname LIKE 'insert_cost_company_census_%')"
                    )
                )
    finally:
        engine.dispose()


def test_count_visits_members_once_and_empty_company_purge_is_unchanged(held):
    from reality.services.account_deletion import _tenant_record_count

    engine, first, _ = held
    with Session(engine) as session:
        inspector = inspect(session.connection())
        actual = 0
        for name in inspector.get_table_names():
            if name == "tenant" or "tenant_id" not in {
                c["name"] for c in inspector.get_columns(name)
            }:
                continue
            actual += session.scalar(
                text(f'SELECT count(*) FROM "{name}" WHERE tenant_id=:t'),
                {"t": first[1]},
            )
        assert _tenant_record_count(session, first[1]) == actual
        empty = core.create_tenant(session, "No protected census").id
        session.commit()
    with Session(engine) as session:
        core._purge_tenant_records(session, empty)
        session.commit()
        assert _tenant_record_count(session, empty) == 0
        assert costing.verify_company_cost_census(session, first[1], first[2])[
            "verified"
        ]
