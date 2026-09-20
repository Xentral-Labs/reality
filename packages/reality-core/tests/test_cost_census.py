"""Source census includes unreviewed subjects without claiming financial completeness."""

from datetime import timedelta

import pytest
from sqlalchemy import delete, event, text

from reality.db.core import BusinessEvent, now
from reality.services import core, costing


def seed(scheduled_database):
    _, factory, tenant, _ = scheduled_database
    with factory() as session:
        party = core.create_party(session, tenant, "Customer", "customer")
        item = core.create_item(session, tenant, "CENSUS", "Unreviewed item")
        location = core.create_location(session, tenant, "Warehouse")
        cutoff = now()
        movement = core.record_movement(
            session,
            tenant,
            "receipt",
            item.id,
            "5",
            to_location_id=location.id,
            occurred_at=cutoff,
        )
        future = core.record_movement(
            session,
            tenant,
            "receipt",
            item.id,
            "2",
            to_location_id=location.id,
            occurred_at=cutoff + timedelta(days=1),
        )
        invoice, lines = core.create_manual_document_with_lines(
            session,
            tenant,
            "sales_invoice",
            "INV",
            party.id,
            [
                {
                    "sku": "SERVICE",
                    "description": "Service",
                    "quantity": "1",
                    "unit_price": "10",
                    "gross_amount": "10",
                    "line_type": "service",
                }
            ],
            "10",
            document_date="2099-01-01",
        )
        credit = core.create_document(
            session, tenant, "credit_note", "CR", party.id, "1"
        )
        source, _ = core.enqueue_source(
            session,
            tenant,
            "census_test",
            "unknown",
            "source",
            {"received": "uninterpreted"},
        )
        session.commit()
        return (
            factory,
            tenant,
            cutoff,
            item.id,
            location.id,
            movement.id,
            future.id,
            invoice.id,
            lines[0].id,
            credit.id,
            source.id,
        )


def read_session(factory):
    session = factory()
    session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
    return session


def test_unreviewed_reality_and_evidence_are_not_lost(scheduled_database, monkeypatch):
    (
        factory,
        tenant,
        cutoff,
        item,
        _,
        movement,
        future,
        invoice,
        line,
        credit,
        source,
    ) = seed(scheduled_database)
    with read_session(factory) as session:

        def forbidden(*args, **kwargs):
            raise AssertionError("Census may neither write nor calculate costs")

        monkeypatch.setattr(session, "flush", forbidden)
        monkeypatch.setattr(costing, "inventory_cost", forbidden)
        statements = []
        connection = session.connection()

        def track(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(connection, "before_cursor_execute", track)
        try:
            result = costing.capture_company_cost_census(session, tenant, cutoff)
        finally:
            event.remove(connection, "before_cursor_execute", track)
    assert len(statements) <= 8
    assert all(sql.lstrip().upper().startswith("SELECT") for sql in statements)
    assert result["publication_eligible"] is False
    assert result["context"]["snapshot"] and "knowledge_at" not in result["context"]
    assert result["inventory"][0]["item_id"] == item
    assert result["inventory"][0]["movement_ids"] == [movement]
    assert future not in result["inventory"][0]["movement_ids"]
    assert result["contribution"][0]["document_line_id"] == line
    assert result["contribution"][0]["document_id"] == invoice
    assert "economic_scope_unassessed" in result["contribution"][0]["gaps"]
    assert result["document_gaps"] == [
        {"document_id": credit, "reason": "document_lines_missing"}
    ]
    assert result["sources"][0]["source_record_id"] == source
    assert result["sources"][0]["classification"] == "unsupported"
    assert result["counts"] == {
        "inventory_items": 1,
        "contribution_candidates": 1,
        "document_gaps": 1,
        "active_sources": 1,
        "unresolved_sources": 1,
        "input_records": 5,
    }


def test_missing_or_ambiguous_events_are_gaps_not_exclusions(scheduled_database):
    factory, tenant, cutoff, _, _, movement, *_ = seed(scheduled_database)
    with factory.begin() as session:
        session.execute(
            delete(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant, BusinessEvent.subject_id == movement
            )
        )
    with read_session(factory) as session:
        result = costing.capture_company_cost_census(session, tenant, cutoff)
        assert result["inventory"][0]["gaps"] == ["movement_recorded_event_missing"]
    with factory.begin() as session:
        for _ in range(2):
            core.emit_business_event(
                session, tenant, "movement.recorded", "movement", movement, {}
            )
    with read_session(factory) as session:
        result = costing.capture_company_cost_census(session, tenant, cutoff)
        assert result["inventory"][0]["gaps"] == ["movement_recorded_event_ambiguous"]


def test_tenant_boundary_and_absence(scheduled_database):
    factory, _, cutoff, *_ = seed(scheduled_database)
    with factory.begin() as session:
        foreign = core.create_tenant(session, "Foreign").id
    with read_session(factory) as session:
        result = costing.capture_company_cost_census(session, foreign, cutoff)
        assert (
            not result["inventory"]
            and not result["contribution"]
            and not result["sources"]
        )
        with pytest.raises(core.NotFound):
            costing.capture_company_cost_census(session, "absent", cutoff)


@pytest.mark.parametrize("limit", [0, 100001, True, "5"])
def test_invalid_bounds_refuse(scheduled_database, limit):
    _, factory, tenant, _ = scheduled_database
    with read_session(factory) as session, pytest.raises(core.InvalidOperation):
        costing.capture_company_cost_census(session, tenant, now(), max_records=limit)


def test_combined_bound_refuses_instead_of_truncating(scheduled_database):
    factory, tenant, cutoff, *_ = seed(scheduled_database)
    with read_session(factory) as session:
        with pytest.raises(core.InvalidOperation, match="limit"):
            costing.capture_company_cost_census(session, tenant, cutoff, max_records=4)
        assert (
            costing.capture_company_cost_census(session, tenant, cutoff, max_records=5)[
                "counts"
            ]["input_records"]
            == 5
        )
    with (
        factory() as session,
        pytest.raises(core.InvalidOperation, match="REPEATABLE READ"),
    ):
        costing.capture_company_cost_census(session, tenant, cutoff)
    with (
        read_session(factory) as session,
        pytest.raises(core.InvalidOperation, match="cutoff"),
    ):
        costing.capture_company_cost_census(session, tenant, "2026-01-01")


def test_concurrent_intake_does_not_change_or_block_captured_snapshot(
    scheduled_database,
):
    factory, tenant, cutoff, item, location, *_ = seed(scheduled_database)
    with read_session(factory) as session:
        first = costing.capture_company_cost_census(session, tenant, cutoff)
        with factory.begin() as writer:
            writer.execute(text("SET LOCAL lock_timeout = '300ms'"))
            core.record_movement(
                writer,
                tenant,
                "receipt",
                item,
                "1",
                to_location_id=location,
                occurred_at=cutoff,
            )
        second = costing.capture_company_cost_census(session, tenant, cutoff)
        assert first["inventory"] == second["inventory"]
        assert first["context"]["event_sequence"] == second["context"]["event_sequence"]
    with read_session(factory) as session:
        fresh = costing.capture_company_cost_census(session, tenant, cutoff)
        assert len(fresh["inventory"][0]["movement_ids"]) == 2
        assert (
            fresh["inventory"][0]["record_fingerprint"]
            != first["inventory"][0]["record_fingerprint"]
        )


def test_source_supersession_and_credit_lines_stay_distinct(scheduled_database):
    factory, tenant, cutoff, _, _, _, _, _, _, _, old_source = seed(scheduled_database)
    with factory() as session:
        replacement, _ = core.enqueue_source(
            session,
            tenant,
            "census_test",
            "unknown",
            "source",
            {"received": "replacement"},
        )
        party = core.create_party(session, tenant, "Second customer", "customer")
        _, lines = core.create_manual_document_with_lines(
            session,
            tenant,
            "credit_note",
            "CR-LINE",
            party.id,
            [
                {
                    "sku": "CREDIT",
                    "description": "Credit",
                    "quantity": "1",
                    "unit_price": "1",
                    "gross_amount": "1",
                    "line_type": "service",
                }
            ],
            "1",
        )
        session.commit()
        replacement_id, line_id = replacement.id, lines[0].id
    with read_session(factory) as session:
        result = costing.capture_company_cost_census(session, tenant, cutoff)
    assert [row["source_record_id"] for row in result["sources"]] == [replacement_id]
    assert old_source != replacement_id
    assert line_id in {row["document_line_id"] for row in result["contribution"]}
    assert result["counts"]["contribution_candidates"] == 2
    assert result["sources"][0]["version"] == 2
