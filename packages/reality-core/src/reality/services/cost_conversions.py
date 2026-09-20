"""Owner-confirmed source-backed unit and currency conversion revisions."""

from sqlalchemy import select

from reality.db.core import SourceRecord
from reality.db.costing import CostConversionBasisRevision
from reality.services import core


def _scope(request):
    return request.kind, request.from_code, request.to_code


def _check(session, tenant, request):
    from reality.services.costing import _hash, _row

    source = _row(session, SourceRecord, tenant, request.evidence_source_record_id)
    latest = session.scalar(
        select(CostConversionBasisRevision)
        .where(
            CostConversionBasisRevision.tenant_id == tenant,
            CostConversionBasisRevision.kind == request.kind,
            CostConversionBasisRevision.from_code == request.from_code,
            CostConversionBasisRevision.to_code == request.to_code,
        )
        .order_by(CostConversionBasisRevision.revision.desc())
        .limit(1)
    )
    if latest is None and request.supersedes_id is not None:
        raise core.InvalidOperation("First conversion revision cannot supersede history.")
    if latest is not None and request.supersedes_id != latest.id:
        raise core.Conflict("Conversion revision must supersede the exact latest basis.")
    values = {
        "kind": request.kind,
        "from_code": request.from_code,
        "to_code": request.to_code,
        "numerator": format(request.numerator, "f"),
        "denominator": format(request.denominator, "f"),
        "effective_at": request.effective_at.isoformat(),
        "evidence_source_record_id": source.id,
        "supersedes_id": request.supersedes_id,
    }
    return {
        **values,
        "revision": latest.revision + 1 if latest else 1,
        "content_hash": _hash(values),
    }


def _execute(session, tenant, request, prepared, event, action):
    from reality.services.costing import _new

    row = _new(
        session,
        CostConversionBasisRevision,
        tenant,
        evidence_source_record_id=prepared["evidence_source_record_id"],
        kind=request.kind,
        from_code=request.from_code,
        to_code=request.to_code,
        numerator=request.numerator,
        denominator=request.denominator,
        effective_at=request.effective_at,
        revision=prepared["revision"],
        supersedes_id=request.supersedes_id,
        introduced_event_id=event.id,
        action_id=action.id,
        reason=request.reason,
        input_schema_version=1,
        content_hash=prepared["content_hash"],
    )
    return {
        "conversion_basis_revision_id": row.id,
        **prepared,
        "action_id": action.id,
    }


def read_basis(session, tenant, identity, *, kind=None):
    from reality.services.costing import _row

    row = _row(session, CostConversionBasisRevision, tenant, identity)
    if kind is not None and row.kind != kind:
        raise core.InvalidOperation("Conversion kind does not match the requested use.")
    return row
