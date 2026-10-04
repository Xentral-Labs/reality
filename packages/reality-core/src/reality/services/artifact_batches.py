"""Whole-artifact selection and coherent bounded units, using shared settlement."""

import json
from collections import defaultdict
from contextvars import ContextVar

from reality.domain.intake import (
    PACKAGE_BYTES,
    ArtifactSelection,
    content_digest,
)
from reality.services import core

_rows_context = ContextVar("artifact_preparation_rows", default=None)


def _cached_rows(session, source, context):
    cache = _rows_context.get()
    if cache is None:
        return None
    if (
        cache["session"] is not session
        or cache["transaction"] is not session.get_transaction()
        or (context.get("parent_source_id") or source.id) != cache["source_id"]
        or source.source_artifact_id != cache["artifact"].id
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    rows = cache["rows"]
    numbers = context.get("row_numbers")
    if numbers is not None and (
        not numbers
        or len(set(numbers)) != len(numbers)
        or any(not isinstance(n, int) or not 2 <= n < len(rows) + 2 for n in numbers)
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    return cache["artifact"], [rows[n - 2] for n in numbers] if numbers else rows


def _prepare_artifact_or_batch(session, tenant_id, source, job):
    from reality.services.artifact_intake import _artifact_rows, _prepare_artifact
    from reality.services.file_intake import partition_rows
    from reality.services.file_interpreters import _mapped_row
    from reality.services.intake import prepare_intake, review_intake
    from reality.services.intake_batches import prepare_batch

    context = json.loads(job.input)
    if context.get("profile") == "artifact_unit.v1":
        return _prepare_artifact(session, tenant_id, source, job)
    artifact, rows = _artifact_rows(session, tenant_id, source, context)
    target = context.get("expected_target")
    mapping = context.get("column_mapping") or {}
    if not 1 <= len(rows) <= 5000:
        raise core.InvalidOperation(code="intake_file_rows_invalid")
    mapped = [_mapped_row(row, mapping) for row in rows]
    if target == "item":
        skus = [str(row.get("sku") or "").strip() for row in mapped]
        seen = set()
        for number, sku in enumerate(skus, 2):
            if sku in seen:
                raise core.InvalidOperation(
                    code="item_import_row_duplicate_sku",
                    values={"row": number, "sku": sku},
                )
            seen.add(sku)
    if target == "inventory_snapshot":
        keys = [(row.get("sku"), row.get("location")) for row in mapped]
        if len(set(keys)) != len(keys):
            raise core.InvalidOperation(code="intake_review_invalid")
    numbered = [{"row_number": number, **row} for number, row in enumerate(rows, 2)]
    if target == "sales_order":
        grouped = defaultdict(list)
        for row, original in zip(mapped, numbered, strict=True):
            identity = str(row.get("order_id") or row.get("order_number") or "").strip()
            if not identity:
                raise core.InvalidOperation(code="intake_review_invalid")
            grouped[identity].append(original)
        units = list(grouped.items())
    elif target == "bank_statement":
        units = [(str(index), [row]) for index, row in enumerate(numbered)]
    else:
        units = [
            (str(part.index), list(part.rows))
            for part in partition_rows(numbered, byte_limit=PACKAGE_BYTES - 16384)
        ]
    if len(units) > 500:
        raise core.InvalidOperation(code="intake_package_too_large")
    # A single complete unit keeps the existing synchronous review contract.
    # Larger selections use retained children and the already confirmed queue.
    if len(units) == 1:
        return _prepare_artifact(session, tenant_id, source, job)
    if any(len(unit) > 500 for _, unit in units):
        raise core.InvalidOperation(code="intake_package_too_large")
    configuration = {
        "expected_target": target,
        "column_mapping": mapping,
        "parser_version": 1,
    }
    key = content_digest(configuration)
    entries = []
    token = _rows_context.set(
        {
            "session": session,
            "transaction": session.get_transaction(),
            "source_id": source.id,
            "artifact": artifact,
            "rows": rows,
        }
    )
    try:
        for identity, unit in units:
            numbers = [row["row_number"] for row in unit]
            _, child_job = core.enqueue_source(
                session,
                tenant_id,
                source.source_system,
                "order" if target == "sales_order" else "artifact_package",
                identity
                if target == "sales_order"
                else f"{source.id}:{key}:{identity}",
                {
                    "source_record_id": source.id,
                    "artifact_id": artifact.id,
                    "sha256": artifact.sha256,
                    "row_numbers": numbers,
                },
                source_artifact_id=artifact.id,
                context={
                    "profile": "artifact_unit.v1",
                    **configuration,
                    "parent_source_id": source.id,
                    "row_numbers": numbers,
                },
                _commit=False,
            )
            child = prepare_intake(session, tenant_id, child_job.id, _commit=False)
            entries.append(
                {
                    "proposal_id": child.id,
                    "digest": review_intake(session, tenant_id, child.id)["digest"],
                }
            )
    finally:
        _rows_context.reset(token)
    return prepare_batch(
        session,
        tenant_id,
        entries,
        request_id=f"artifact:{source.id}:{key}",
        _artifact_selection=ArtifactSelection(
            source_record_id=source.id,
            artifact_id=artifact.id,
            original_rows=len(rows),
            target=target,
            column_mapping=mapping,
        ),
        _commit=False,
    )


def _validate_selection(session, tenant_id, manifest):
    from reality.db.core import SourceRecord
    from reality.services.intake import review_intake

    selection = manifest.artifact_selection
    if selection is None:
        return
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, selection.source_record_id
    )
    if source.source_artifact_id != selection.artifact_id:
        raise core.InvalidOperation(code="intake_review_invalid")
    numbers = []
    for entry in manifest.entries:
        review = review_intake(session, tenant_id, entry.proposal_id)
        mapping = review["plan"]["mapping"]
        if (
            review["digest"] != entry.digest
            or review["plan"]["profile"] != f"artifact:{selection.target}.v1"
            or mapping.get("parent_source_id") != source.id
            or mapping.get("expected_target") != selection.target
            or mapping.get("column_mapping") != selection.column_mapping
        ):
            raise core.InvalidOperation(code="intake_review_invalid")
        numbers.extend(mapping["row_numbers"])
    if sorted(numbers) != list(range(2, selection.original_rows + 2)):
        raise core.InvalidOperation(code="intake_review_invalid")


def _complete_artifact_job(session, tenant_id, manifest, progress):
    """Record truthful aggregate completion without turning partial review into success."""
    from sqlalchemy import select

    from reality.db.core import ImportJob, SourceRecord
    from reality.domain.intake import canonical_json
    from reality.services.intake import _outcome

    selection = manifest.artifact_selection
    if selection is None:
        return
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, selection.source_record_id
    )
    job = session.scalar(
        select(ImportJob)
        .where(
            ImportJob.tenant_id == tenant_id, ImportJob.source_record_id == source.id
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if job is None:
        raise core.InvalidOperation(code="intake_review_invalid")
    complete = all(
        result["disposition"] in {"applied", "replayed"}
        for result in progress["results"]
    )
    job.status = "completed" if complete else "awaiting_decision"
    job.completed_at = core.now() if complete else None
    job.next_attempt_at = None
    job.error = (
        ""
        if complete
        else canonical_json(
            {
                "reason_code": "intake_awaiting_decision",
                "batch_results": progress["results"],
            }
        )
    )
    _outcome(
        session,
        tenant_id,
        source,
        job,
        "interpreted" if complete else "prepared",
        reason_code="intake_applied" if complete else "intake_awaiting_decision",
        summary="Every reviewed artifact unit was accepted."
        if complete
        else "The artifact selection finished with refused or stopped units; renewed review is required.",
    )
