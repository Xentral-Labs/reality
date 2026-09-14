"""Bounded new-item CSV interpretation and evidence in the shared proposal lifecycle."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import BusinessEvent, ChangeProposal, Item, SourceRecord
from reality.services.artifacts import (
    get_artifact,
    mark_artifact_attached,
    materialize_artifact,
    stage_artifact,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    create_item,
    emit_business_event,
    get_tenant,
    store_source_record,
)
from reality.services.reference_workspace import require_ordinary_workspace

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 500


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _parse(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if not content or len(content) > MAX_BYTES:
        raise InvalidOperation("CSV must contain data and be at most 2 MiB.")
    try:
        text = content.decode("utf-8-sig")
        if "\x00" in text:
            raise InvalidOperation("CSV contains an invalid null character.")
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(io.StringIO(text, newline=""), dialect=dialect, strict=True)
        columns = next(reader)
        if (
            not 1 <= len(columns) <= 50
            or any(not c.strip() for c in columns)
            or len({c.strip().lower() for c in columns}) != len(columns)
        ):
            raise InvalidOperation("CSV requires 1–50 distinct, nonempty column names.")
        if any(len(c) > 500 for c in columns):
            raise InvalidOperation("CSV column names must be at most 500 characters.")
        rows = []
        for number, values in enumerate(reader, 2):
            if len(values) != len(columns):
                raise InvalidOperation(
                    f"Row {number}: the number of fields differs from the header."
                )
            rows.append(dict(zip(columns, values, strict=True)))
            if len(rows) > MAX_ROWS:
                raise InvalidOperation("CSV may contain at most 500 item rows.")
        if not rows:
            raise InvalidOperation("CSV has no item rows.")
        return columns, rows
    except (UnicodeError, csv.Error, StopIteration) as error:
        raise InvalidOperation("Upload a valid UTF-8 CSV file.") from error


def stage_item_csv(
    session: Session, tenant_id: str, content: bytes, filename: str
) -> dict[str, Any]:
    require_ordinary_workspace(session, tenant_id)
    columns, rows = _parse(content)
    artifact, _ = stage_artifact(
        session,
        tenant_id,
        io.BytesIO(content),
        filename=filename,
        content_type="text/csv",
    )
    mapping = {
        field: column
        for field in ("sku", "name", "unit")
        for column in columns
        if column.strip().lower() == field
    }
    return {
        "id": artifact.id,
        "filename": artifact.filename,
        "sha256": artifact.sha256,
        "columns": columns,
        "row_count": len(rows),
        "mapping": mapping,
    }


def _read(session: Session, tenant_id: str, artifact_id: str):
    artifact = get_artifact(session, tenant_id, artifact_id)
    if artifact.byte_size > MAX_BYTES:
        raise InvalidOperation("CSV must be at most 2 MiB.")
    with materialize_artifact(artifact) as path, path.open("rb") as stream:
        content = stream.read(MAX_BYTES + 1)
    if (
        len(content) != artifact.byte_size
        or hashlib.sha256(content).hexdigest() != artifact.sha256
    ):
        raise InvalidOperation("The original file no longer matches its recorded hash.")
    columns, rows = _parse(content)
    return artifact, columns, rows


def _validate_new_rows(
    session: Session, tenant_id: str, rows: list[dict[str, Any]]
) -> None:
    seen: set[str] = set()
    existing = set(
        session.scalars(
            select(Item.sku).where(
                Item.tenant_id == tenant_id, Item.sku.in_([row["sku"] for row in rows])
            )
        )
    )
    for number, row in enumerate(rows, 2):
        for field in ("sku", "name", "unit"):
            if (
                not isinstance(row.get(field), str)
                or not row[field].strip()
                or len(row[field]) > 500
            ):
                raise InvalidOperation(
                    f"Row {number}: {field} is required and must be at most 500 characters."
                )
        if row["sku"] in seen:
            raise InvalidOperation(
                f"Row {number}: duplicate SKU {row['sku']} in this file."
            )
        if row["sku"] in existing:
            raise InvalidOperation(
                f"Row {number}: SKU {row['sku']} already exists in this company."
            )
        seen.add(row["sku"])


def preview_item_import(
    session: Session, tenant_id: str, config: dict[str, Any]
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    if set(config) - {"artifact_id", "source_system", "mapping", "default_unit"}:
        raise InvalidOperation("Unsupported item import fields.")
    source = config.get("source_system", "")
    unit = config.get("default_unit", "pcs")
    mapping = config.get("mapping", {})
    if not isinstance(source, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9_.-]{0,99}", source
    ):
        raise InvalidOperation(
            "Source code must use 1–100 lowercase letters, numbers, dots, dashes or underscores."
        )
    if not isinstance(unit, str) or not unit.strip() or len(unit) > 500:
        raise InvalidOperation("A default unit of at most 500 characters is required.")
    if not isinstance(mapping, dict) or set(mapping) - {"sku", "name", "unit"}:
        raise InvalidOperation("Map only SKU, name and unit.")
    artifact, columns, raw = _read(
        session, tenant_id, str(config.get("artifact_id", ""))
    )
    if (
        any(
            not isinstance(value, str) or value not in columns
            for value in mapping.values()
        )
        or not mapping.get("sku")
        or not mapping.get("name")
    ):
        raise InvalidOperation(
            "Choose existing columns for SKU and name and optionally unit."
        )
    if len(set(mapping.values())) != len(mapping):
        raise InvalidOperation("Each mapped field must use a different column.")
    rows = [
        {
            "sku": row[mapping["sku"]].strip(),
            "name": row[mapping["name"]].strip(),
            "unit": (row[mapping["unit"]].strip() if mapping.get("unit") else "")
            or unit.strip(),
        }
        for row in raw
    ]
    _validate_new_rows(session, tenant_id, rows)
    return {
        "artifact": {
            "id": artifact.id,
            "filename": artifact.filename,
            "sha256": artifact.sha256,
            "byte_size": artifact.byte_size,
        },
        "source_system": source,
        "mapping": mapping,
        "default_unit": unit.strip(),
        "rows": rows,
    }


def review_item_import(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    if set(arguments) != {"import_file"} or not isinstance(
        arguments.get("import_file"), dict
    ):
        raise InvalidOperation("An exact file-import configuration is required.")
    creation = preview_item_import(session, tenant_id, arguments["import_file"])
    intent = {"import_file": dict(arguments["import_file"])}
    state = {"creation": creation}
    token = hashlib.sha256(_json([tenant_id, intent, state]).encode()).hexdigest()
    return {
        "version": 1,
        "tool": "item_create",
        "intent": intent,
        "state": state,
        "effect": {"items": len(creation["rows"])},
        "token": token,
    }


def assert_import_overlap(
    session: Session, tenant_id: str, arguments: dict[str, Any], exclude: str | None
) -> None:
    creation = preview_item_import(session, tenant_id, arguments["import_file"])
    skus = {row["sku"] for row in creation["rows"]}
    for other in session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == "tool:item_create",
            ChangeProposal.status == "executing",
        )
    ):
        if other.id == exclude:
            continue
        saved = json.loads(other.input)
        prior = (
            saved.get("_delivery_review", {})
            .get("state", {})
            .get("creation", {})
            .get("rows", saved.get("records", []))
        )
        if any(row.get("sku") in skus for row in prior):
            raise InvalidOperation(
                "An overlapping item creation is unresolved. Check its outcome first."
            )


def record_item_import(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    lock_delivery_state(session, tenant_id)
    session.expire_all()
    creation = preview_item_import(session, tenant_id, arguments["import_file"])
    action_id = arguments.get("_action_id")
    if not action_id:
        raise InvalidOperation("Item import requires a confirmed proposal.")
    artifact = get_artifact(session, tenant_id, creation["artifact"]["id"])
    try:
        source, created, _ = store_source_record(
            session,
            tenant_id,
            creation["source_system"],
            "item_csv",
            artifact.sha256,
            creation,
            source_artifact_id=artifact.id,
        )
        if not created:
            raise InvalidOperation(
                "This file interpretation was already recorded. Inspect its original result."
            )
        emit_business_event(
            session,
            tenant_id,
            "source_record.received",
            "source_record",
            source.id,
            {
                "source_system": source.source_system,
                "source_type": source.source_type,
                "external_id": source.external_id,
            },
            source_record_id=source.id,
            action_id=action_id,
        )
        ids = [
            create_item(
                session,
                tenant_id,
                row["sku"],
                row["name"],
                row["unit"],
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            ).id
            for row in creation["rows"]
        ]
        mark_artifact_attached(artifact)
        session.flush()
        return {
            "artifact_id": artifact.id,
            "source_record_id": source.id,
            "item_ids": ids,
        }
    except Exception:
        session.rollback()
        raise


def item_import_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    review = json.loads(proposal.input)["_delivery_review"]
    result = {
        "id": proposal.id,
        "tool": "item_create",
        "status": proposal.status,
        "review": review,
        "receipt": json.loads(proposal.output)
        if proposal.status == "executed"
        else None,
        "verification": "pending" if proposal.status == "proposed" else "unresolved",
        "links": [],
        "observation": None,
        "observation_error": None,
    }
    if proposal.status not in {"executing", "executed"}:
        return result
    events = list(
        session.scalars(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
            )
        )
    )
    received = [
        event for event in events if event.event_type == "source_record.received"
    ]
    created = [event for event in events if event.event_type == "item.created"]
    expected = review["state"]["creation"]
    if len(received) != 1 or len(created) != len(expected["rows"]):
        return result
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.id == received[0].subject_id,
        )
    )
    if (
        not source
        or json.loads(source.payload) != expected
        or source.source_artifact_id != expected["artifact"]["id"]
        or received[0].source_record_id != source.id
    ):
        return result
    by_sku = {json.loads(event.payload).get("sku"): event for event in created}
    ids = []
    for row in expected["rows"]:
        event = by_sku.get(row["sku"])
        if (
            not event
            or event.source_record_id != source.id
            or event.subject_type != "item"
            or json.loads(event.payload).get("unit") != row["unit"]
        ):
            return result
        if not session.scalar(
            select(Item.id).where(
                Item.tenant_id == tenant_id, Item.id == event.subject_id
            )
        ):
            return result
        ids.append(event.subject_id)
    receipt = {
        "artifact_id": source.source_artifact_id,
        "source_record_id": source.id,
        "item_ids": ids,
    }
    if proposal.status == "executed" and result["receipt"] != receipt:
        return result
    result.update(
        verification="verified"
        if proposal.status == "executed"
        else "recorded_unsettled",
        recorded_receipt=receipt,
        links=[
            {"kind": "source_record", "id": source.id},
            *({"kind": "item", "id": identity} for identity in ids),
        ],
    )
    return result
