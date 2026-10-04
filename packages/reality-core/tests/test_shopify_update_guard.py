import json
from copy import deepcopy
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from intake_review_support import accept_import_job as process_import_job
from sqlalchemy import select

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    Reservation,
    SourceStream,
)
from reality.services import core
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_tenant,
    enqueue_shopify_order,
    interpretation_coverage,
    open_quantity,
    process_pending_import_jobs,
    record_movement,
    reserve,
    retry_import_job,
)
from reality.tools.application import run_read_tool
from reality.web import api as api_module
from reality.web.app import app


def payload():
    return {
        "id": 4711,
        "name": "#4711",
        "currency": "EUR",
        "total_price": "100.00",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
        "line_items": [
            {"id": 1, "sku": "BIKE-LIGHT", "quantity": 10, "price": "10.00"}
        ],
    }


def enqueue(session, business, data):
    return enqueue_shopify_order(
        session,
        business.tenant.id,
        data,
        business.company.id,
        business.customer.id,
        business.location.id,
    )


def changed_payload():
    """A change spec 296 still holds: the shop states a new shipping address."""
    return {
        **payload(),
        "shipping_address": {"address1": "Nebenstr. 2", "city": "Ulm"},
        "updated_at": "2026-09-01T11:00:00Z",
    }


def snapshot(session, tenant_id):
    return {
        model.__tablename__: [
            tuple(getattr(record, column.key) for column in model.__table__.columns)
            for record in session.scalars(
                select(model).where(model.tenant_id == tenant_id).order_by(model.id)
            )
        ]
        for model in (
            Document,
            DocumentLine,
            Commitment,
            Reservation,
            Movement,
            LedgerEntry,
        )
    }


# Spec 296 narrowed the guard: lower quantities and a cancellation before anything
# shipped now apply themselves (tests/test_shop_order_changes.py). Every change
# below is still held, and a held change must leave every record untouched.
@pytest.mark.parametrize(
    ("change", "shipped", "code"),
    [
        ("quantity_up", 0, "quantity_increased"),
        ("quantity_up", 4, "quantity_increased"),
        ("quantity_up", 10, "closed_line_changed"),
        ("quantity_down", 10, "closed_line_changed"),
        ("cancelled_at", 4, "cancelled_after_shipment"),
        ("cancelled_at", 10, "cancelled_after_shipment"),
        ("address", 0, "address_changed"),
    ],
)
def test_changed_order_preserves_every_business_record(
    session, business, shipped, change, code
):
    first, job = enqueue(session, business, payload())
    _, _, _, commitments = process_import_job(session, business.tenant.id, job.id)
    commitment = commitments[0]
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    reserve(session, business.tenant.id, commitment.id)
    if shipped:
        record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            shipped,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
        )
    before = snapshot(session, business.tenant.id)
    changed = deepcopy(payload())
    changed["updated_at"] = "2026-09-01T11:00:00Z"
    if change == "quantity_up":
        changed["line_items"][0]["quantity"] = 12
    elif change == "quantity_down":
        changed["line_items"][0]["quantity"] = 7
    elif change == "cancelled_at":
        changed["cancelled_at"] = "2026-09-01T11:00:00Z"
    else:
        changed["shipping_address"] = {"address1": "Nebenstr. 2", "city": "Ulm"}
    source, update_job = enqueue(session, business, changed)
    assert process_import_job(session, business.tenant.id, update_job.id) is None
    session.expire_all()
    assert snapshot(session, business.tenant.id) == before
    assert open_quantity(session, business.tenant.id, commitment.id) == Decimal(
        10 - shipped
    )
    assert json.loads(source.payload) == changed
    assert json.loads(first.payload) == payload()
    assert source.supersedes_source_record_id == first.id
    assert (
        session.scalar(
            select(SourceStream).where(
                SourceStream.tenant_id == business.tenant.id,
                SourceStream.external_id == "4711",
            )
        ).current_source_record_id
        == source.id
    )
    coverage = interpretation_coverage(session, business.tenant.id, source.id)[0]
    assert coverage["current_classification"] == "needs_review"
    outcome = coverage["outcomes"][-1]
    assert outcome["reason_code"] == code
    assert code in outcome["summary"] and "unchanged" in outcome["summary"]
    assert outcome["produced_records"] == []
    assert update_job.next_attempt_at is None


def test_consecutive_updates_duplicates_and_retries_cannot_bypass_guard(
    session, business
):
    _, initial_job = enqueue(session, business, payload())
    original = process_import_job(session, business.tenant.id, initial_job.id)
    before = snapshot(session, business.tenant.id)
    for hour in (11, 12):
        changed = {
            **payload(),
            "updated_at": f"2026-09-01T{hour}:00:00Z",
            "shipping_address": {"city": str(hour)},
        }
        source, job = enqueue(session, business, changed)
        assert process_import_job(session, business.tenant.id, job.id) is None
        repeated_source, repeated_job = enqueue(session, business, changed)
        assert (repeated_source.id, repeated_job.id) == (source.id, job.id)
        assert process_import_job(session, business.tenant.id, job.id) is None
        assert job.attempts == 1
        assert (
            len(
                interpretation_coverage(session, business.tenant.id, source.id)[0][
                    "outcomes"
                ]
            )
            == 1
        )
        retry_import_job(session, business.tenant.id, job.id)
        assert process_import_job(session, business.tenant.id, job.id) is None
        outcomes = interpretation_coverage(session, business.tenant.id, source.id)[0][
            "outcomes"
        ]
        assert [(row["attempt"], row["classification"]) for row in outcomes] == [
            (1, "needs_review"),
            (2, "needs_review"),
        ]
    assert snapshot(session, business.tenant.id) == before
    assert (
        process_import_job(session, business.tenant.id, initial_job.id)[1].id
        == original[1].id
    )


def test_latest_pending_version_prepares_without_accepting_either_version(
    session, business
):
    _, first_job = enqueue(session, business, payload())
    source, job = enqueue(session, business, changed_payload())
    proposal = core.process_import_job(session, business.tenant.id, job.id)
    assert proposal.status == "proposed" and job.status == "awaiting_decision"
    assert (
        interpretation_coverage(session, business.tenant.id, source.id)[0][
            "current_classification"
        ]
        == "prepared"
    )
    assert snapshot(session, business.tenant.id)["commitment"] == []
    with pytest.raises(InvalidOperation, match="reviewed intake state"):
        core.process_import_job(session, business.tenant.id, first_job.id)


def test_synchronous_review_explains_the_actual_outcome(session, business):
    _, job = enqueue(session, business, payload())
    process_import_job(session, business.tenant.id, job.id)
    with pytest.raises(core.ShopifyUpdateNeedsReview, match="address_changed"):
        core.ingest_shopify_order(
            session,
            business.tenant.id,
            changed_payload(),
            business.company.id,
            business.customer.id,
            business.location.id,
        )


def test_review_does_not_stop_batch_and_is_tenant_scoped(session, business):
    _, initial_job = enqueue(session, business, payload())
    process_import_job(session, business.tenant.id, initial_job.id)
    source, job = enqueue(session, business, changed_payload())
    _, unrelated_job = enqueue(session, business, {**payload(), "id": 4712})
    assert process_pending_import_jobs(session, business.tenant.id) == (1, 0)
    assert unrelated_job.status == "awaiting_decision"
    other = create_tenant(session, "Other")
    with pytest.raises(NotFound):
        process_import_job(session, other.id, job.id)
    with pytest.raises(NotFound):
        run_read_tool(
            session,
            other.id,
            "interpretation_coverage",
            {"source_record_id": source.id},
        )
    assert (
        run_read_tool(
            session,
            business.tenant.id,
            "interpretation_coverage",
            {"source_record_id": source.id},
        )[0]["current_classification"]
        == "needs_review"
    )


def test_http_processing_exposes_review_reason_and_retry_preserves_state(
    session, business
):
    _, job = enqueue(session, business, payload())
    process_import_job(session, business.tenant.id, job.id)
    _, updated_job = enqueue(session, business, changed_payload())
    before = snapshot(session, business.tenant.id)

    def database_session():
        yield session

    app.dependency_overrides[api_module.database_session] = database_session
    try:
        with TestClient(app) as client:
            prefix = f"/api/tenants/{business.tenant.id}"
            for attempt in (1, 2):
                response = client.post(f"{prefix}/import-jobs/work")
                assert response.status_code == 200
                assert response.json() == {"prepared": 0, "completed": 0, "failed": 0}
                jobs = client.get(f"{prefix}/import-jobs")
                assert jobs.status_code == 200
                row = next(row for row in jobs.json() if row["id"] == updated_job.id)
                assert "address_changed" in row["error"]
                assert row["attempts"] == attempt
                if attempt == 1:
                    assert (
                        client.post(
                            f"{prefix}/import-jobs/{updated_job.id}/retry"
                        ).status_code
                        == 200
                    )
    finally:
        app.dependency_overrides.pop(api_module.database_session, None)
    assert snapshot(session, business.tenant.id) == before
