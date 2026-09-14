"""Reviewed source-code translation; source and internal decisions stay separate."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import SourceRecord, SourceSystem, uid
from reality.db.source_mappings import SourceClassificationMapping as Mapping
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.finance.accounts import lock_finance
from reality.services.finance.references import (
    _get,
    _page,
    _result,
    _revision,
    list_references,
    resolve_reference,
)

SCOPE = ("source_system_id", "namespace", "field_kind", "source_code")


def _scope(tenant_id: str, values: dict) -> list:
    return [
        Mapping.tenant_id == tenant_id,
        *(getattr(Mapping, k) == values[k] for k in SCOPE),
    ]


def _row(row: Mapping) -> dict:
    return {
        **{
            k: getattr(row, k)
            for k in (
                "id",
                *SCOPE,
                "reference_id",
                "revision",
                "replaces_id",
                "state",
                "is_current",
                "reference_snapshot",
                "reason",
                "actor_id",
                "action_id",
            )
        },
        "created_at": row.created_at.isoformat(),
    }


def list_source_mappings(
    session: Session,
    tenant_id: str,
    *,
    query: str = "",
    source_query: str = "",
    reference_query: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    core.get_tenant(session, tenant_id)
    _page(limit, offset)
    clauses = [Mapping.tenant_id == tenant_id, Mapping.is_current.is_(True)]
    if query.strip():
        clauses.append(
            or_(
                Mapping.source_code.icontains(query.strip(), autoescape=True),
                Mapping.namespace.icontains(query.strip(), autoescape=True),
            )
        )
    source_clauses = [SourceSystem.tenant_id == tenant_id]
    if source_query.strip():
        source_clauses.append(
            or_(
                SourceSystem.code.icontains(source_query.strip(), autoescape=True),
                SourceSystem.name.icontains(source_query.strip(), autoescape=True),
            )
        )
    systems = list(
        session.scalars(
            select(SourceSystem)
            .where(*source_clauses)
            .order_by(SourceSystem.code)
            .limit(200)
        )
    )
    return {
        "revision": _revision(session, tenant_id),
        "limit": limit,
        "offset": offset,
        "total": session.scalar(
            select(func.count()).select_from(Mapping).where(*clauses)
        ),
        "items": [
            _row(r)
            for r in session.scalars(
                select(Mapping)
                .where(*clauses)
                .order_by(
                    Mapping.source_system_id,
                    Mapping.namespace,
                    Mapping.field_kind,
                    Mapping.source_code,
                )
                .limit(limit)
                .offset(offset)
            )
        ],
        "sources": [
            {"id": s.id, "code": s.code, "name": s.name, "active": s.is_active}
            for s in systems
        ],
        "sources_total": session.scalar(
            select(func.count()).select_from(SourceSystem).where(*source_clauses)
        ),
        "references": {
            kind: list_references(
                session,
                tenant_id,
                kind=kind,
                state="active",
                query=reference_query,
                limit=200,
            )
            for kind in ("case_code", "coding_group")
        },
    }


def source_mapping_history(
    session: Session,
    tenant_id: str,
    mapping_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _page(limit, offset)
    row = core._tenant_record(session, Mapping, tenant_id, mapping_id)
    clauses = _scope(tenant_id, _row(row))
    return {
        "total": session.scalar(
            select(func.count()).select_from(Mapping).where(*clauses)
        ),
        "limit": limit,
        "offset": offset,
        "items": [
            _row(r)
            for r in session.scalars(
                select(Mapping)
                .where(*clauses)
                .order_by(Mapping.revision.desc())
                .limit(limit)
                .offset(offset)
            )
        ],
    }


def preview_source_mapping(session: Session, tenant_id: str, arguments: dict) -> dict:
    core.get_tenant(session, tenant_id)
    lock_finance(session, tenant_id)
    if arguments["expected_revision"] != _revision(session, tenant_id):
        raise core.Conflict("Finance preview is stale; reload and confirm again.")
    source = session.scalar(
        select(SourceSystem)
        .where(
            SourceSystem.tenant_id == tenant_id,
            SourceSystem.id == arguments["source_system_id"],
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if source is None:
        raise core.NotFound("Source system not found.")
    for key in ("namespace", "source_code", "reason"):
        value = arguments[key]
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > (4000 if key == "reason" else 200)
        ):
            raise core.InvalidOperation(
                "Source namespace, code and reason must be nonempty within their length limits."
            )
    if arguments["field_kind"] not in ("case_code", "coding_group") or arguments[
        "state"
    ] not in ("active", "blocked"):
        raise core.InvalidOperation("Unsupported source mapping kind or state.")
    old = session.scalar(
        select(Mapping)
        .where(*_scope(tenant_id, arguments), Mapping.is_current.is_(True))
        .execution_options(populate_existing=True)
    )
    ref = _get(session, tenant_id, arguments["reference_id"])
    if ref.kind != arguments["field_kind"]:
        raise core.InvalidOperation("Source mapping reference has the wrong kind.")
    if arguments["state"] == "active":
        if not source.is_active:
            raise core.InvalidOperation("Source system is blocked.")
        resolve_reference(session, tenant_id, ref.id, ref.kind)
    elif old is None or old.reference_id != ref.id:
        raise core.InvalidOperation(
            "Only an existing mapping can be blocked without changing its destination."
        )
    if old and old.state == arguments["state"] and old.reference_id == ref.id:
        raise core.InvalidOperation("Source mapping change has no effect.")
    return {
        "before": _row(old) if old else None,
        "after": {
            **{k: arguments[k] for k in SCOPE},
            "reference_id": ref.id,
            "reference_snapshot": _result(ref),
            "revision": old.revision + 1 if old else 1,
            "replaces_id": old.id if old else None,
            "state": arguments["state"],
        },
        "reason": arguments["reason"],
        "source": {"id": source.id, "code": source.code, "name": source.name},
    }


def set_source_mapping(
    session: Session,
    tenant_id: str,
    *,
    arguments: dict,
    action_id: str,
    actor_id: str | None = None,
) -> dict:
    core._require_business_mutation(session, tenant_id, "finance_source_mapping_set")
    coordinator = lock_finance(session, tenant_id)
    review = preview_source_mapping(session, tenant_id, arguments)
    if review["before"]:
        old = core._tenant_record(session, Mapping, tenant_id, review["before"]["id"])
        old.is_current = False
        session.flush()
    row = Mapping(
        id=uid("smap"),
        tenant_id=tenant_id,
        **review["after"],
        reason=review["reason"],
        action_id=action_id,
        actor_id=actor_id,
    )
    session.add(row)
    coordinator.revision += 1
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "finance.source_mapping_changed",
        "source_classification_mapping_revision",
        row.id,
        {
            "before": review["before"],
            "after": _row(row),
            "reason": row.reason,
            "actor_id": actor_id,
        },
        action_id=action_id,
    )
    session.flush()
    return _row(row)


def resolve_source_codes(session: Session, tenant_id: str, item: dict) -> dict:
    """Read the declaration at this exact component scope, never inherit summary codes."""
    source = (
        core._tenant_record(session, SourceRecord, tenant_id, item["source_record_id"])
        if item["source_record_id"]
        else None
    )
    system = (
        session.scalar(
            select(SourceSystem).where(
                SourceSystem.tenant_id == tenant_id,
                SourceSystem.code == source.source_system,
            )
        )
        if source
        else None
    )
    codes = item["source_codes"]
    result = {}
    for key, kind, internal_key in (
        ("case", "case_code", "case_reference_id"),
        ("group", "coding_group", "group_reference_id"),
    ):
        declared = codes.get(key) if isinstance(codes, dict) else codes
        entry = {
            "declared": declared,
            "status": "missing",
            "mapping_id": None,
            "reference": None,
            "internal_reference_id": (item.get("current") or {}).get(internal_key),
        }
        result[key] = entry
        if declared is None:
            continue
        if not isinstance(declared, dict) or any(
            not isinstance(declared.get(k), str)
            or not declared[k].strip()
            or len(declared[k]) > 200
            for k in ("namespace", "code")
        ):
            entry["status"] = "malformed"
            continue
        if not system or not system.is_active:
            entry["status"] = "blocked_source" if system else "missing_source"
            continue
        scope = {
            "source_system_id": system.id,
            "namespace": declared["namespace"],
            "field_kind": kind,
            "source_code": declared["code"],
        }
        row = session.scalar(
            select(Mapping).where(
                *_scope(tenant_id, scope), Mapping.is_current.is_(True)
            )
        )
        if not row:
            entry["status"] = "unmapped"
            continue
        ref = _get(session, tenant_id, row.reference_id)
        entry.update(
            mapping_id=row.id,
            mapping_revision=row.revision,
            reference=_result(ref),
            reference_snapshot=row.reference_snapshot,
        )
        entry["status"] = (
            "blocked_mapping"
            if row.state == "blocked"
            else "blocked_reference"
            if ref.state != "active"
            else "conflict"
            if entry["internal_reference_id"]
            and entry["internal_reference_id"] != ref.id
            else "resolved"
        )
    return result
