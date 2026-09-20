"""Attention reads consume the stored exceptions projection; explanations stay live."""

from datetime import timedelta

import pytest
from sqlalchemy import event
from unified_fixtures import delivery_fixture

from reality.catalogs import load_operational_exception_catalog
from reality.services import exceptions as exception_service
from reality.services import projections
from reality.services.attention_reads import (
    FindingCleared,
    attention_detail,
    attention_register,
    attention_summary,
    stored_exceptions,
)
from reality.services.core import NotFound, create_tenant, reserve
from reality.services.exceptions import operational_exception_rows
from reality.services.projections import EXCEPTIONS, rebuild_projections


def _publish(session, tenant_id):
    """What the background worker does: publish one generation of stored rows."""
    rebuild_projections(session, tenant_id, [EXCEPTIONS], force=True)
    session.flush()


def _forbid_derivation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("stored attention reads must not derive or rebuild")

    monkeypatch.setattr(exception_service, "operational_exceptions", forbidden)
    monkeypatch.setattr(exception_service, "operational_exception_rows", forbidden)
    monkeypatch.setattr(projections, "rebuild_projections", forbidden)
    monkeypatch.setattr(projections, "derive_projection_rows", forbidden)


@pytest.fixture
def forbid_derivation(monkeypatch):
    """A stored read must neither derive exceptions nor rebuild any projection."""
    _forbid_derivation(monkeypatch)


def test_register_reads_the_stored_generation_in_canonical_order(
    session, business, monkeypatch
):
    delivery_fixture(session, business)
    canonical = operational_exception_rows(session, business.tenant.id)
    assert canonical
    _publish(session, business.tenant.id)
    # From here on every derivation and builder is forbidden.
    _forbid_derivation(monkeypatch)

    result = attention_register(session, business.tenant.id, size=1)
    assert result["page"]["total"] == len(canonical)
    assert result["items"][0]["id"] == canonical[0]["id"]
    everything = attention_register(session, business.tenant.id, size=100)
    assert [row["id"] for row in everything["items"]] == [
        row["id"] for row in canonical
    ]
    exact_page = attention_register(
        session, business.tenant.id, page=999, size=len(canonical)
    )
    assert exact_page["page"]["number"] == 1
    assert exact_page["page"]["pages"] == 1
    assert result["metadata"]["state"] == "ready"
    assert result["metadata"]["calculation_mode"] == "stored"
    assert result["metadata"]["completed_at"]
    assert result["observed_at"] == result["metadata"]["completed_at"]
    exact = attention_register(
        session,
        business.tenant.id,
        query=canonical[0]["id"],
        severity=canonical[0]["severity"],
    )
    assert exact["page"]["total"] == 1
    assert (
        attention_register(session, business.tenant.id, query="absent search")["page"][
            "total"
        ]
        == 0
    )
    class_id = canonical[0]["class_id"]
    filtered = attention_register(session, business.tenant.id, class_id=class_id)
    assert {row["class_id"] for row in filtered["items"]} == {class_id}
    assert filtered["page"]["total"] == sum(
        1 for row in canonical if row["class_id"] == class_id
    )
    with pytest.raises(ValueError):
        attention_register(session, business.tenant.id, severity="invented")
    with pytest.raises(ValueError):
        attention_register(session, business.tenant.id, class_id="invented_class")


def test_summary_counts_every_class_from_the_same_generation(session, business):
    delivery_fixture(session, business)
    canonical = operational_exception_rows(session, business.tenant.id)
    _publish(session, business.tenant.id)
    catalog_ids = [
        entry["id"] for entry in load_operational_exception_catalog().classes
    ]
    summary = attention_summary(session, business.tenant.id)
    assert [row["class_id"] for row in summary["classes"]] == catalog_ids
    assert summary["total"] == len(canonical)
    counts = {row["class_id"]: row["open"] for row in summary["classes"]}
    for class_id in catalog_ids:
        assert counts[class_id] == sum(
            1 for row in canonical if row["class_id"] == class_id
        )
    assert counts["outgoing_commitment_at_risk"] >= 1
    register = attention_register(session, business.tenant.id)
    assert summary["total"] == register["page"]["total"]
    assert summary["metadata"] == register["metadata"]


def test_register_and_summary_bound_work_in_postgresql(session, business):
    delivery_fixture(session, business)
    _publish(session, business.tenant.id)
    statements = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        first = attention_register(
            session,
            business.tenant.id,
            query="commitment",
            page=999,
            size=1,
        )
        register_statements = list(statements)
        statements.clear()
        attention_summary(session, business.tenant.id)
        summary_statements = list(statements)
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)

    assert len(first["items"]) <= 1
    register_sql = next(
        statement
        for statement in register_statements
        if "from projection_row" in statement and "json_agg" in statement
    )
    assert " limit " in register_sql
    assert " offset " in register_sql
    assert "concat_ws" in register_sql
    summary_sql = next(
        statement
        for statement in summary_statements
        if "from projection_row" in statement and "jsonb_object_agg" in statement
    )
    assert " group by " in summary_sql
    assert "json_agg" not in summary_sql


def test_uninitialized_company_is_awaiting_calculation_not_empty(
    session, forbid_derivation
):
    tenant = create_tenant(session, "Fresh attention")
    register = attention_register(session, tenant.id)
    assert register["items"] == [] and register["page"]["total"] == 0
    assert register["metadata"]["state"] == "uninitialized"
    assert register["metadata"]["completed_at"] is None
    summary = attention_summary(session, tenant.id)
    assert summary["total"] == 0
    assert all(row["open"] == 0 for row in summary["classes"])
    assert summary["metadata"]["state"] == "uninitialized"
    with pytest.raises(NotFound):
        attention_register(session, "ten_missing")


def test_stale_generation_keeps_rows_and_reports_pending(
    session, business, monkeypatch
):
    fixture = delivery_fixture(session, business)
    _publish(session, business.tenant.id)
    rows, metadata = stored_exceptions(session, business.tenant.id)
    assert metadata["state"] == "ready"
    listed = {row["record_id"] for row in rows}
    assert fixture.commitment.id in listed
    # The finding clears in Reality; the stored generation still lists it until the
    # worker publishes the next one, and a minute later the reader is told so.
    reserve(session, business.tenant.id, fixture.commitment.id, "12")
    later = projections.now() + timedelta(seconds=120)
    monkeypatch.setattr(projections, "now", lambda: later)
    rows, metadata = stored_exceptions(session, business.tenant.id)
    assert fixture.commitment.id in {row["record_id"] for row in rows}
    assert metadata["state"] == "pending"
    monkeypatch.undo()
    _publish(session, business.tenant.id)
    rows, metadata = stored_exceptions(session, business.tenant.id)
    assert fixture.commitment.id not in {row["record_id"] for row in rows}
    assert metadata["state"] == "ready"


def test_detail_explains_live_and_classifies_a_cleared_finding(session, business):
    fixture = delivery_fixture(session, business)
    _publish(session, business.tenant.id)
    result = attention_register(session, business.tenant.id)
    finding = next(
        row for row in result["items"] if row["record_id"] == fixture.commitment.id
    )
    detail = attention_detail(session, business.tenant.id, finding["id"])
    assert detail["target"]["delivery_id"] == fixture.commitment.id
    assert detail["guidance"]
    assert business.customer.name in detail["context"]
    assert business.item.name in detail["context"]
    other = create_tenant(session, "Foreign attention")
    with pytest.raises(NotFound):
        attention_detail(session, other.id, finding["id"])
    reserve(session, business.tenant.id, fixture.commitment.id, "12")
    with pytest.raises(FindingCleared) as cleared:
        attention_detail(session, business.tenant.id, finding["id"])
    assert isinstance(cleared.value, NotFound)
    assert cleared.value.code == "finding_cleared"
    assert cleared.value.completed_at == result["metadata"]["completed_at"]
    _publish(session, business.tenant.id)
    with pytest.raises(NotFound) as plain:
        attention_detail(session, business.tenant.id, finding["id"])
    assert not isinstance(plain.value, FindingCleared)
    with pytest.raises(NotFound) as unknown:
        attention_detail(session, business.tenant.id, "exc__invented__x")
    assert not isinstance(unknown.value, FindingCleared)


def test_two_findings_of_one_class_are_ordered_by_date_and_not_by_record_id(
    session, business
):
    """The part of the order a rank used to carry (spec 181 FR-002).

    Within a class the derivation puts the oldest promise first. The stored rows used
    to carry their *place* in that order, and the reader fell back on the record id
    whenever a generation had none — a different order. The row now carries `sort_at`,
    so the two agree.

    The two promises here are built so that the dates and the ids disagree: the
    later-created promise is made the older one. Without that, an order by id would
    pass this test by accident.
    """
    from reality.services.core import create_commitment, record_movement, utc_datetime

    tenant = business.tenant.id
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "20",
        to_location_id=business.location.id,
    )
    promises = [
        create_commitment(
            session,
            tenant,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            "2",
            "2026-08-01T00:00:00+00:00",
        )
        for _ in range(2)
    ]
    first_by_id, second_by_id = sorted(promises, key=lambda row: row.id)
    # The promise with the larger id is the older one, so date and id disagree.
    first_by_id.due_at = utc_datetime("2026-08-20T00:00:00+00:00")
    second_by_id.due_at = utc_datetime("2026-08-01T00:00:00+00:00")
    session.flush()

    canonical = operational_exception_rows(session, tenant)
    overdue = [
        row["record_id"]
        for row in canonical
        if row["class_id"] == "overdue_outgoing_customer_commitment"
    ]
    assert overdue[:2] == [second_by_id.id, first_by_id.id], (
        "the derivation puts the older promise first"
    )
    assert overdue[:2] != sorted(overdue[:2]), (
        "the fixture no longer makes date and id disagree"
    )

    _publish(session, tenant)
    stored, _ = stored_exceptions(session, tenant)
    assert [
        row["record_id"]
        for row in stored
        if row["class_id"] == "overdue_outgoing_customer_commitment"
    ][:2] == overdue[:2]
