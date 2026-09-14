import pytest

from reality.db.core import InterpretationOutcome, InterpretationRecordReference
from reality.mcp.catalog import MCP_TOOL_NAMES, model_tool_schemas
from reality.services import core
from reality.services.core import (
    create_tenant,
    enqueue_shopify_order,
    enqueue_source,
    interpretation_coverage,
    process_import_job,
    retry_import_job,
)
from reality.tools.application import run_read_tool


def shopify_payload():
    return {
        "id": 4501,
        "name": "#4501",
        "created_at": "2026-09-03T10:00:00Z",
        "updated_at": "2026-09-03T10:00:00Z",
        "currency": "EUR",
        "total_price": "24.00",
        "line_items": [
            {
                "id": 91,
                "sku": "BIKE-LIGHT",
                "name": "Bike Light",
                "quantity": 2,
                "price": "12.00",
            }
        ],
    }


def enqueue_order(session, business):
    return enqueue_shopify_order(
        session,
        business.tenant.id,
        shopify_payload(),
        business.company.id,
        business.customer.id,
        business.location.id,
    )


def test_shopify_attempt_records_all_produced_reality_atomically(session, business):
    _source, job = enqueue_order(session, business)
    _, document, lines, commitments = process_import_job(
        session, business.tenant.id, job.id
    )

    outcomes = (
        session.query(InterpretationOutcome)
        .filter_by(tenant_id=business.tenant.id)
        .all()
    )
    assert [
        (row.attempt, row.classification, row.interpreter_name) for row in outcomes
    ] == [(1, "interpreted", "shopify.order")]
    references = (
        session.query(InterpretationRecordReference)
        .filter_by(outcome_id=outcomes[0].id)
        .all()
    )
    assert {(row.record_type, row.record_id) for row in references} == {
        ("document", document.id),
        *(("document_line", row.id) for row in lines),
        *(("commitment", row.id) for row in commitments),
    }

    process_import_job(session, business.tenant.id, job.id)
    assert session.query(InterpretationOutcome).count() == 1


def test_unsupported_and_historical_sources_have_explicit_coverage(session, business):
    source, _ = enqueue_source(
        session,
        business.tenant.id,
        "custom",
        "mystery",
        "42",
        {"secret": "not returned"},
    )
    row = interpretation_coverage(session, business.tenant.id, source.id)[0]
    assert row["current_classification"] == "unsupported"
    assert row["outcomes"][0]["reason_code"] == "interpreter_unavailable"
    assert "payload" not in row

    historical, historical_job = enqueue_order(session, business)
    session.query(InterpretationOutcome).filter_by(
        source_record_id=historical.id
    ).delete()
    session.commit()
    historical_job.status = "completed"
    session.commit()
    assert (
        interpretation_coverage(session, business.tenant.id, historical.id)[0][
            "current_classification"
        ]
        == "not_recorded"
    )


def test_intake_version_dispositions_and_review_are_explicit(
    session, business, monkeypatch
):
    first, _ = enqueue_source(
        session,
        business.tenant.id,
        "custom",
        "versioned",
        "V-1",
        {"value": 1},
        source_version_at="2026-09-03T10:00:00Z",
    )
    stale, _ = enqueue_source(
        session,
        business.tenant.id,
        "custom",
        "versioned",
        "V-1",
        {"value": 0},
        source_version_at="2026-09-02T10:00:00Z",
    )
    conflict, _ = enqueue_source(
        session,
        business.tenant.id,
        "custom",
        "versioned",
        "V-1",
        {"value": 2},
        source_version_at="2026-09-03T10:00:00Z",
    )
    assert (
        interpretation_coverage(session, business.tenant.id, stale.id)[0][
            "current_classification"
        ]
        == "stale"
    )
    assert (
        interpretation_coverage(session, business.tenant.id, conflict.id)[0][
            "current_classification"
        ]
        == "conflict"
    )
    assert first.id not in {stale.id, conflict.id}

    source, job = enqueue_order(session, business)

    def review(*args, **kwargs):
        raise core.InterpretationNeedsReview("raw private detail")

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("shopify", "order"), review)
    assert process_import_job(session, business.tenant.id, job.id) is None
    outcome = interpretation_coverage(session, business.tenant.id, source.id)[0][
        "outcomes"
    ][0]
    assert outcome["classification"] == "needs_review"
    assert "raw private detail" not in outcome["summary"]


def test_failed_attempt_is_preserved_before_successful_retry(
    session, business, monkeypatch
):
    source, job = enqueue_order(session, business)
    interpreter = core.SOURCE_INTERPRETERS[("shopify", "order")]

    def fail(*args, **kwargs):
        raise RuntimeError("payload contained private customer data")

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("shopify", "order"), fail)
    with pytest.raises(RuntimeError):
        process_import_job(session, business.tenant.id, job.id)
    failed = interpretation_coverage(session, business.tenant.id, source.id)[0]
    assert failed["outcomes"][0]["classification"] == "failed"
    assert "private customer data" not in failed["outcomes"][0]["summary"]

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("shopify", "order"), interpreter)
    retry_import_job(session, business.tenant.id, job.id)
    process_import_job(session, business.tenant.id, job.id)
    attempts = interpretation_coverage(session, business.tenant.id, source.id)[0][
        "outcomes"
    ]
    assert [(row["attempt"], row["classification"]) for row in attempts] == [
        (1, "failed"),
        (2, "interpreted"),
    ]


def test_coverage_tool_is_read_only_tenant_scoped_and_in_mcp(session, business):
    source, _ = enqueue_source(
        session, business.tenant.id, "custom", "mystery", "43", {}
    )
    result = run_read_tool(
        session,
        business.tenant.id,
        "interpretation_coverage",
        {"source_record_id": source.id},
    )
    assert result[0]["source_record_id"] == source.id

    other = create_tenant(session, "Other")
    with pytest.raises(core.NotFound):
        run_read_tool(
            session,
            other.id,
            "interpretation_coverage",
            {"source_record_id": source.id},
        )

    schemas = {
        item["function"]["name"]: item["function"]
        for item in model_tool_schemas(access=("read",))
    }
    assert "interpretation_coverage" in MCP_TOOL_NAMES
    assert schemas["interpretation_coverage"]["parameters"]["required"] == []
