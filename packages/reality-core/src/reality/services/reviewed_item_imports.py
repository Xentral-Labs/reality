"""Reviewed item-file capture, exact selection and shared batch admission (spec 358)."""

from __future__ import annotations

import hashlib
import io
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSONB

from reality.db.core import ChangeProposal, ImportJob, Item, SourceRecord
from reality.services.artifacts import (
    get_artifact,
    mark_artifact_attached,
    materialize_artifact,
    stage_artifact,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import InvalidOperation
from reality.services.item_imports import MAX_ROWS, _validate_new_rows
from reality.services.reference_workspace import require_ordinary_workspace

_file_preparation: ContextVar[dict | None] = ContextVar(
    "reviewed_file_preparation", default=None
)


@contextmanager
def _file_rows_scope(session, source, artifact, configuration, rows):
    token = _file_preparation.set(
        {
            "session": session,
            "transaction": session.get_transaction(),
            "source_id": source.id,
            "artifact": artifact,
            "configuration": configuration,
            "rows": rows,
        }
    )
    try:
        yield
    finally:
        _file_preparation.reset(token)


# Reviewed file capture is separate from business acceptance. Original bytes are
# attached before any mapping/field-validation failure can reject interpretation.
def stage_reviewed_item_csv(
    session, tenant_id, content, filename, *, source_system="catalog_upload"
):
    """
    BUSINESS PURPOSE:
    Capture original item CSV bytes before interpretation or business consent.

    BUSINESS RULE item_intake.stage_reviewed_item_csv:
    Capture original item CSV bytes before interpretation or business consent.
    """
    from reality.services import core
    from reality.services.file_intake import RAW_BYTES, parse_item_csv

    # reality-rule: item_intake.stage_reviewed_item_csv
    require_ordinary_workspace(session, tenant_id)
    if not isinstance(content, bytes) or not content or len(content) > RAW_BYTES:
        raise InvalidOperation(code="intake_file_size_invalid")
    if not isinstance(source_system, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9_.-]{0,99}", source_system
    ):
        raise InvalidOperation(code="item_import_source_code_invalid")
    artifact, _ = stage_artifact(
        session,
        tenant_id,
        io.BytesIO(content),
        filename=filename,
        content_type="text/csv",
    )
    source, job = core.enqueue_source(
        session,
        tenant_id,
        source_system,
        "item_csv_raw",
        artifact.id,
        {
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "byte_size": artifact.byte_size,
            "content_type": artifact.content_type,
        },
        source_artifact_id=artifact.id,
        context={"profile": "file_capture.v1"},
        _commit=False,
    )
    mark_artifact_attached(artifact)
    session.commit()
    columns, rows = parse_item_csv(content)
    mapping = {
        field: column
        for field in ("sku", "name", "unit")
        for column in columns
        if column.strip().lower() == field
    }
    return {
        "id": artifact.id,
        "artifact_id": artifact.id,
        "source_record_id": source.id,
        "job_id": job.id,
        "filename": artifact.filename,
        "sha256": artifact.sha256,
        "byte_size": artifact.byte_size,
        "columns": columns,
        "row_count": len(rows),
        "mapping": mapping,
    }


def _reviewed_content(session, tenant_id, source):
    from reality.services.file_intake import RAW_BYTES

    artifact = get_artifact(session, tenant_id, source.source_artifact_id)
    if artifact.byte_size > RAW_BYTES:
        raise InvalidOperation(code="intake_file_size_invalid")
    with materialize_artifact(artifact) as path, path.open("rb") as stream:
        content = stream.read(RAW_BYTES + 1)
    if (
        len(content) != artifact.byte_size
        or hashlib.sha256(content).hexdigest() != artifact.sha256
    ):
        raise InvalidOperation(code="item_import_file_hash_mismatch")
    return artifact, content


def prepare_reviewed_item_file(
    session,
    tenant_id,
    source_record_id,
    mapping,
    *,
    request_id,
    default_unit="pcs",
    _commit=True,
):
    """
    BUSINESS PURPOSE:
    Freeze whole-file selection and exact package meanings before one batch decision.

    BUSINESS RULE item_intake.prepare_reviewed_item_file:
    Freeze whole-file selection and exact package meanings before one batch decision.
    """
    from reality.domain.intake import PACKAGE_BYTES, FileSelection, content_digest
    from reality.services import core
    from reality.services.file_intake import mapped_item_rows, partition_rows
    from reality.services.intake import prepare_intake, review_intake
    from reality.services.intake_batches import prepare_batch

    # reality-rule: item_intake.prepare_reviewed_item_file
    lock_delivery_state(session, tenant_id)
    require_ordinary_workspace(session, tenant_id)
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, source_record_id
    )
    if source.source_type != "item_csv_raw" or not source.source_artifact_id:
        raise InvalidOperation(code="intake_profile_unsupported")
    # Response loss/restart returns the exact retained selection, even when its
    # accepted items now exist. Fresh interpretation uses a new explicit request.
    old = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:intake_batch_apply",
            cast(ChangeProposal.input, JSONB)["request_id"].astext == request_id,
        )
    )
    if old is not None:
        held = json.loads(old.input)
        selection = held["manifest"].get("file_selection")
        if (
            selection is None
            or selection["source_record_id"] != source.id
            or selection["mapping"] != mapping
            or selection["default_unit"] != default_unit
        ):
            raise InvalidOperation(code="intake_review_stale")
        return {
            "batch_id": old.id,
            "digest": held["digest"],
            "source_record_id": source.id,
            "artifact_id": selection["artifact_id"],
            "original_rows": selection["original_rows"],
            "excluded_rows": selection["excluded_rows"],
            "entries": held["manifest"]["entries"],
        }
    artifact, content = _reviewed_content(session, tenant_id, source)
    all_rows = mapped_item_rows(content, mapping, default_unit=default_unit)
    existing = set(
        session.scalars(
            select(Item.sku).where(
                Item.tenant_id == tenant_id,
                Item.sku.in_([row["sku"] for row in all_rows]),
            )
        )
    )
    included, excluded = [], []
    for number, row in enumerate(all_rows, 2):
        invalid = next(
            (
                field
                for field in ("sku", "name", "unit")
                if not row[field].strip() or len(row[field]) > 500
            ),
            None,
        )
        if invalid:
            excluded.append(
                {
                    "row": number,
                    "reason_code": "item_import_row_field_invalid",
                    "field": invalid,
                }
            )
        elif row["sku"] in existing:
            excluded.append(
                {
                    "row": number,
                    "reason_code": "item_import_row_sku_exists",
                    "sku": row["sku"],
                }
            )
        else:
            included.append({"row_number": number, **row})
    if not included:
        raise InvalidOperation(code="item_import_csv_no_rows")
    packages = partition_rows(included, byte_limit=PACKAGE_BYTES - 16384)
    # This is a retained interpretation setting, never a new source of raw bytes.
    configuration = {
        "mapping": dict(mapping),
        "default_unit": default_unit,
        "parser_version": 1,
    }
    key = content_digest(configuration)
    entries = []
    with _file_rows_scope(session, source, artifact, configuration, all_rows):
        for package in packages:
            numbers = [row["row_number"] for row in package.rows]
            _, job = core.enqueue_source(
                session,
                tenant_id,
                source.source_system,
                "item_csv_package",
                f"{source.id}:{key}:{package.index}",
                {
                    "source_record_id": source.id,
                    "artifact_id": artifact.id,
                    "sha256": artifact.sha256,
                    "row_numbers": numbers,
                },
                source_artifact_id=artifact.id,
                context={
                    "profile": "item_csv.v1",
                    **configuration,
                    "row_numbers": numbers,
                    "parent_source_id": source.id,
                },
                _commit=False,
            )
            proposal = prepare_intake(session, tenant_id, job.id, _commit=False)
            review = review_intake(session, tenant_id, proposal.id)
            entries.append({"proposal_id": proposal.id, "digest": review["digest"]})
    batch = prepare_batch(
        session,
        tenant_id,
        entries,
        request_id=request_id,
        _file_selection=FileSelection(
            source_record_id=source.id,
            artifact_id=artifact.id,
            original_rows=len(all_rows),
            mapping=mapping,
            default_unit=default_unit,
            excluded_rows=excluded,
        ),
        _commit=False,
    )
    if _commit:
        session.commit()
    return {
        "batch_id": batch.id,
        "digest": json.loads(batch.input)["digest"],
        "source_record_id": source.id,
        "artifact_id": artifact.id,
        "original_rows": len(all_rows),
        "excluded_rows": excluded,
        "entries": entries,
    }


def prepare_item_package(session, tenant_id, source, job):
    """
    BUSINESS PURPOSE:
    Resolve exact item fields and defaults without creating any item.

    BUSINESS RULE item_intake.prepare_item_package:
    Resolve exact item fields and defaults without creating any item.
    """
    from reality.domain.intake import Effect, PreparedIntake
    from reality.services import core
    from reality.services.file_intake import mapped_item_rows
    from reality.services.intake import _reference

    # reality-rule: item_intake.prepare_item_package
    source = core._tenant_record_read(session, SourceRecord, tenant_id, source.id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job.id)
    context = json.loads(job.input)
    descriptor = json.loads(source.payload)
    parent = core._tenant_record_read(
        session, SourceRecord, tenant_id, context["parent_source_id"]
    )
    if (
        parent.source_type != "item_csv_raw"
        or parent.source_artifact_id != source.source_artifact_id
        or descriptor.get("source_record_id") != parent.id
    ):
        raise InvalidOperation(code="intake_review_invalid")
    cached = _file_preparation.get()
    configuration = {
        key: context[key] for key in ("mapping", "default_unit", "parser_version")
    }
    if (
        cached is not None
        and cached["session"] is session
        and cached["transaction"] is session.get_transaction()
        and cached["source_id"] == parent.id
        and cached["configuration"] == configuration
    ):
        artifact, all_rows = cached["artifact"], cached["rows"]
    else:
        artifact, content = _reviewed_content(session, tenant_id, parent)
        all_rows = mapped_item_rows(
            content, context["mapping"], default_unit=context["default_unit"]
        )
    if (
        descriptor.get("sha256") != artifact.sha256
        or descriptor.get("row_numbers") != context["row_numbers"]
    ):
        raise InvalidOperation(code="intake_review_invalid")
    numbers = context["row_numbers"]
    if (
        not 1 <= len(numbers) <= MAX_ROWS
        or numbers != sorted(set(numbers))
        or any(
            type(number) is not int or not 2 <= number <= len(all_rows) + 1
            for number in numbers
        )
    ):
        raise InvalidOperation(code="intake_review_invalid")
    rows = [all_rows[number - 2] for number in numbers]
    _validate_new_rows(session, tenant_id, rows)
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="item_csv.v1",
        mapping=context,
        references=(_reference(session, tenant_id, "source_artifact", artifact.id),),
        effects=(
            Effect(
                operation="item_package",
                arguments={
                    "rows": rows,
                    "row_numbers": numbers,
                    "defaults": {
                        "item_type": "stocked",
                        "tracking_type": "none",
                        "default_location_id": None,
                        "purchase_unit": None,
                        "conversion_factor": "1",
                        "lead_time_days": 0,
                        "source_system": "",
                        "external_id": "",
                        "source_payload": None,
                    },
                },
            ),
        ),
        row_count=len(rows),
    )


def capture_reviewed_item_artifact(
    session, tenant_id, artifact_id, source_system, *, _commit=True
):
    """
    BUSINESS PURPOSE:
    Retain the selected artifact origin without authorizing item creation.

    BUSINESS RULE item_intake.capture_reviewed_item_artifact:
    Retain the selected artifact origin without authorizing item creation.
    """
    """Describe already retained original bytes before approving their meaning."""
    from reality.services import core
    from reality.services.file_intake import RAW_BYTES

    # reality-rule: item_intake.capture_reviewed_item_artifact
    require_ordinary_workspace(session, tenant_id)
    if not isinstance(source_system, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9_.-]{0,99}", source_system
    ):
        raise InvalidOperation(code="item_import_source_code_invalid")
    artifact = get_artifact(session, tenant_id, artifact_id)
    if not 0 < artifact.byte_size <= RAW_BYTES:
        raise InvalidOperation(code="intake_file_size_invalid")
    source, _ = core.enqueue_source(
        session,
        tenant_id,
        source_system,
        "item_csv_raw",
        artifact.id,
        {
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "byte_size": artifact.byte_size,
            "content_type": artifact.content_type,
        },
        source_artifact_id=artifact.id,
        context={"profile": "file_capture.v1"},
        _commit=False,
    )
    if artifact.status == "staged":
        mark_artifact_attached(artifact)
    if _commit:
        session.commit()
    return source


def prepare_reviewed_item_import(session, tenant_id, config, *, request_id):
    """
    BUSINESS PURPOSE:
    Prepare the uploaded item file through shared reviewed admission.

    BUSINESS RULE item_intake.prepare_reviewed_item_import:
    Prepare the uploaded item file through shared reviewed admission.
    """
    # reality-rule: item_intake.prepare_reviewed_item_import
    if not isinstance(config, dict) or set(config) - {
        "artifact_id",
        "source_system",
        "mapping",
        "default_unit",
    }:
        raise InvalidOperation(code="item_import_fields_unsupported")
    source = capture_reviewed_item_artifact(
        session,
        tenant_id,
        config.get("artifact_id", ""),
        config.get("source_system", "manual_upload"),
    )
    result = prepare_reviewed_item_file(
        session,
        tenant_id,
        source.id,
        config.get("mapping", {}),
        default_unit=config.get("default_unit", "pcs"),
        request_id=request_id,
    )
    return reviewed_item_file_detail(session, tenant_id, result["batch_id"])


def reviewed_item_file_detail(session, tenant_id, batch_id, *, package_index=0):
    """
    BUSINESS PURPOSE:
    Explain one fixed item package and recorded queue progress without settlement.

    BUSINESS RULE item_intake.reviewed_item_file_detail:
    Explain one fixed item package and recorded queue progress without settlement.
    """
    """Explain one package page and all selected/excluded identities without writes."""
    from reality.services import core
    from reality.services.intake import review_intake
    from reality.services.intake_batches import _batch, _manifest, batch_status

    # reality-rule: item_intake.reviewed_item_file_detail
    batch = core._tenant_record_read(session, ChangeProposal, tenant_id, batch_id)
    if batch.type == "tool:item_create":
        from reality.services.delivery_actions import delivery_proposal_detail

        return delivery_proposal_detail(session, tenant_id, batch.id)
    batch = _batch(session, tenant_id, batch_id)
    held, manifest = _manifest(batch)
    selection = manifest.file_selection
    if selection is None:
        raise InvalidOperation(code="intake_profile_unsupported")
    if type(package_index) is not int or not 0 <= package_index < len(manifest.entries):
        raise InvalidOperation(code="intake_review_invalid")
    entry = manifest.entries[package_index]
    child = review_intake(session, tenant_id, entry.proposal_id)
    parent = core._tenant_record_read(
        session, SourceRecord, tenant_id, selection.source_record_id
    )
    artifact = get_artifact(session, tenant_id, selection.artifact_id)
    progress = batch_status(session, tenant_id, batch_id)
    # Count-only whole-manifest state; detailed receipts are read by package.
    stored = json.loads(batch.output)
    results = stored.get("results", [])
    counts = {
        name: sum(row["disposition"] == name for row in results)
        for name in ("applied", "replayed", "review_required", "stopped")
    }
    complete = batch.status == "executed" and counts["applied"] + counts[
        "replayed"
    ] == len(manifest.entries)
    proposal = core._tenant_record_read(
        session, ChangeProposal, tenant_id, entry.proposal_id
    )
    receipt = None
    if proposal.status == "executed":
        accepted = json.loads(proposal.output)
        receipt = {
            "artifact_id": artifact.id,
            "source_record_id": accepted["source_record_id"],
            "item_ids": [
                row["id"] for row in accepted["records"] if row["type"] == "item"
            ],
        }
    effect = child["plan"]["effects"][0]
    return {
        "id": batch.id,
        "tool": "intake_batch_apply",
        "status": batch.status,
        "verification": "verified"
        if complete
        else "partial"
        if batch.status == "executed"
        else "queued"
        if batch.status == "executing"
        else "pending",
        "review": {
            "token": held["digest"],
            "intent": {
                "import_file": {
                    "artifact_id": artifact.id,
                    "source_system": parent.source_system,
                    "mapping": selection.mapping,
                    "default_unit": selection.default_unit,
                }
            },
            "state": {
                "creation": {
                    "artifact": {"id": artifact.id, "filename": artifact.filename},
                    "source_system": parent.source_system,
                    "default_unit": selection.default_unit,
                    "rows": effect["arguments"]["rows"],
                    "row_numbers": effect["arguments"]["row_numbers"],
                    "defaults": effect["arguments"]["defaults"],
                    "original_rows": selection.original_rows,
                    "excluded_rows": [
                        row.model_dump(mode="json", exclude_none=True)
                        for row in selection.excluded_rows
                    ],
                    "package_index": package_index,
                    "package_count": len(manifest.entries),
                    "source_record_id": parent.id,
                }
            },
        },
        "receipt": receipt,
        "progress": {
            "total": len(manifest.entries),
            "settled": progress["settled"],
            "stopped": stored.get("stopped", False),
            "counts": counts,
        },
        "member": {
            "proposal_id": entry.proposal_id,
            "digest": entry.digest,
            "status": child["status"],
        },
    }
