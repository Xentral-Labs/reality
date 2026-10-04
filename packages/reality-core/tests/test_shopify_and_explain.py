import json
from copy import deepcopy
from pathlib import Path

import pytest
from intake_review_support import accept_import_job as process_shopify_import_job
from intake_review_support import accept_shopify_order as ingest_shopify_order
from sqlalchemy import func, select

from reality.db.core import Commitment, Document, ImportJob, SourceRecord
from reality.services.core import (
    InvalidOperation,
    commitment_quantity,
    enqueue_shopify_order,
    explain_commitment,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "shopify" / "order_10473.json"


def test_shopify_ingestion_is_lossless_idempotent_and_traceable(session, business):
    payload = json.loads(FIXTURE.read_text())

    source, document, lines, commitments = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    reordered_payload = dict(reversed(list(payload.items())))
    repeated = ingest_shopify_order(
        session,
        business.tenant.id,
        reordered_payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )

    assert json.loads(source.payload) == payload
    assert document.number == "#10473"
    assert lines[0].source_line_id == "817263"
    assert commitments[0].document_line_id == lines[0].id
    assert repeated[0].id == source.id
    assert source.version == 1
    assert len(source.payload_hash) == 64
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == 1
    assert session.scalar(select(func.count()).select_from(ImportJob)) == 1
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(Commitment)) == 1

    trace = explain_commitment(session, business.tenant.id, commitments[0].id)
    assert trace["source_record"].id == source.id
    assert trace["document"].id == document.id
    assert trace["document_line"].id == lines[0].id
    assert trace["raw_source"] == payload


def test_changed_source_creates_version_and_revises_without_replacing_interpretation(
    session, business
):
    payload = json.loads(FIXTURE.read_text())
    first = ingest_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    changed = deepcopy(payload)
    changed["line_items"][0]["quantity"] = 25
    changed["total_price"] = "1225.00"

    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        changed,
        business.company.id,
        business.customer.id,
        business.location.id,
    )

    # Spec 296: a lower quantity is applied as a revision of the same promise;
    # the first interpretation is kept, never replaced.
    applied = process_shopify_import_job(session, business.tenant.id, job.id)
    assert applied[1].id == first[1].id
    assert first[0].id != source.id
    assert source.version == 2
    assert source.supersedes_source_record_id == first[0].id
    assert first[1].status == "recorded"
    assert first[3][0].status == "open"
    assert first[3][0].quantity == 30
    assert commitment_quantity(session, business.tenant.id, first[3][0].id) == 25
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == 2


def test_source_survives_interpretation_failure(session, business):
    # An unknown SKU no longer fails the order (spec 296, tests/test_order_line_items.py);
    # a quantity that is not positive still does.
    payload = json.loads(FIXTURE.read_text())
    payload["line_items"][0]["quantity"] = 0

    with pytest.raises(InvalidOperation, match="greater than zero"):
        ingest_shopify_order(
            session,
            business.tenant.id,
            payload,
            business.company.id,
            business.customer.id,
            business.location.id,
        )

    assert session.scalar(select(func.count()).select_from(SourceRecord)) == 1
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    job = session.scalar(select(ImportJob))
    assert job.status == "failed"
    assert job.attempts == 1


def test_first_version_failure_retries_but_changed_version_requires_review(
    session, business, monkeypatch
):

    payload = json.loads(FIXTURE.read_text())
    reviewed_create_item(session, business.tenant.id, "LATER", "Later item")
    payload["line_items"][0]["sku"] = "LATER"
    from reality.services import shopify_intake

    interpret = shopify_intake.prepare_order
    failures = iter([True])

    def fails_once(*args, **kwargs):
        if next(failures, False):
            raise InvalidOperation("Unknown SKU: LATER")
        return interpret(*args, **kwargs)

    monkeypatch.setattr(shopify_intake, "prepare_order", fails_once)

    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    with pytest.raises(InvalidOperation, match="Unknown SKU"):
        process_shopify_import_job(session, business.tenant.id, job.id)

    assert source.version == 1
    assert job.status == "failed"

    changed_source, changed_job = enqueue_shopify_order(
        session,
        business.tenant.id,
        {**payload, "note": "Changed after failure"},
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    accepted = process_shopify_import_job(session, business.tenant.id, changed_job.id)
    assert changed_source.version == 2
    assert accepted[1].source_record_id == changed_source.id
    with pytest.raises(InvalidOperation, match="reviewed intake state"):
        process_shopify_import_job(session, business.tenant.id, job.id)
    assert job.status == "failed"
    assert changed_job.status == "completed"


def test_stale_and_conflicting_webhooks_are_stored_but_not_interpreted(
    session, business
):
    current_payload = json.loads(FIXTURE.read_text())
    current_payload["updated_at"] = "2026-09-02T10:00:00Z"
    current = ingest_shopify_order(
        session,
        business.tenant.id,
        current_payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )

    stale_payload = deepcopy(current_payload)
    stale_payload["updated_at"] = "2026-09-02T09:00:00Z"
    stale_payload["total_price"] = "1.00"
    stale_source, stale_job = enqueue_shopify_order(
        session,
        business.tenant.id,
        stale_payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    assert stale_source.supersedes_source_record_id is None
    assert stale_job.status == "completed"
    assert process_shopify_import_job(session, business.tenant.id, stale_job.id) is None

    conflict_payload = deepcopy(current_payload)
    conflict_payload["total_price"] = "2.00"
    conflict_source, conflict_job = enqueue_shopify_order(
        session,
        business.tenant.id,
        conflict_payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    assert conflict_source.supersedes_source_record_id is None
    assert conflict_job.status == "failed"
    with pytest.raises(InvalidOperation, match="reviewed intake state"):
        process_shopify_import_job(session, business.tenant.id, conflict_job.id)

    assert current[1].status == "recorded"
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == 3
    assert session.scalar(select(func.count()).select_from(Document)) == 1


from intake_review_support import reviewed_create_item
