"""Reviewed external destinations, independent of local accounting effects."""

import json
from datetime import datetime

from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    Document,
    LedgerEntry,
    SubledgerAccount,
    now,
    uid,
)
from reality.db.target_mappings import AccountingTarget as Target
from reality.db.target_mappings import AccountingTargetReference as Reference
from reality.db.target_mappings import TargetMapping as Mapping
from reality.domain.target_mappings import COMMANDS, SCOPE
from reality.services import core
from reality.services.core import emit_business_event
from reality.services.finance.accounts import lock_finance
from reality.services.finance.references import _get, _page, _result, _revision


def serialize(row) -> dict:
    return {
        c.name: (
            getattr(row, c.name).isoformat()
            if isinstance(getattr(row, c.name), datetime)
            else getattr(row, c.name)
        )
        for c in row.__table__.columns
        if c.name
        not in ("tenant_id", "case_kind", "group_kind", "account_kind", "tax_kind")
    }


def _get_row(session, tenant_id, model, identity):
    row = session.scalar(
        select(model)
        .where(model.tenant_id == tenant_id, model.id == identity)
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise core.NotFound("Finance target record not found.")
    return row


def _list(session, tenant_id, model, clauses, query, limit, offset):
    core.get_tenant(session, tenant_id)
    _page(limit, offset)
    clauses = [model.tenant_id == tenant_id, *clauses]
    label = (
        model.namespace
        if model is Target
        else model.code
        if model is Reference
        else model.mapping_kind
    )
    if query.strip():
        clauses.append(
            or_(
                label.icontains(query.strip(), autoescape=True),
                (model.name if model is not Mapping else model.reason).icontains(
                    query.strip(), autoescape=True
                ),
            )
        )
    return {
        "revision": _revision(session, tenant_id),
        "total": session.scalar(
            select(func.count()).select_from(model).where(*clauses)
        ),
        "limit": limit,
        "offset": offset,
        "items": [
            serialize(row)
            for row in session.scalars(
                select(model)
                .where(*clauses)
                .order_by(label, model.id)
                .limit(limit)
                .offset(offset)
            )
        ],
    }


def list_targets(
    session: Session,
    tenant_id: str,
    *,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    return _list(session, tenant_id, Target, [], query, limit, offset)


def list_target_references(
    session: Session,
    tenant_id: str,
    *,
    target_id: str,
    kind: str | None = None,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _get_row(session, tenant_id, Target, target_id)
    if kind is not None and kind not in ("account", "tax_code"):
        raise core.InvalidOperation("Invalid external reference kind.")
    return _list(
        session,
        tenant_id,
        Reference,
        [Reference.target_id == target_id, *([Reference.kind == kind] if kind else [])],
        query,
        limit,
        offset,
    )


def list_mappings(
    session: Session,
    tenant_id: str,
    *,
    target_id: str,
    query: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _get_row(session, tenant_id, Target, target_id)
    return _list(
        session,
        tenant_id,
        Mapping,
        [Mapping.target_id == target_id, Mapping.is_current.is_(True)],
        query,
        limit,
        offset,
    )


def _scope(tenant_id, values):
    return [
        Mapping.tenant_id == tenant_id,
        *(getattr(Mapping, k) == values[k] for k in SCOPE),
    ]


def mapping_history(
    session: Session,
    tenant_id: str,
    *,
    mapping_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _page(limit, offset)
    row = _get_row(session, tenant_id, Mapping, mapping_id)
    clauses = _scope(tenant_id, serialize(row))
    return {
        "total": session.scalar(
            select(func.count()).select_from(Mapping).where(*clauses)
        ),
        "limit": limit,
        "offset": offset,
        "items": [
            serialize(r)
            for r in session.scalars(
                select(Mapping)
                .where(*clauses)
                .order_by(Mapping.revision.desc())
                .limit(limit)
                .offset(offset)
            )
        ],
    }


def validate(command: str, arguments: dict) -> dict:
    try:
        return COMMANDS[command].model_validate(arguments).model_dump()
    except (ValidationError, KeyError) as error:
        raise core.InvalidOperation(str(error)) from error


def _active(row):
    if row.state != "active":
        raise core.InvalidOperation("Selected target or reference is blocked.")


def preview_change(
    session: Session, tenant_id: str, command: str, arguments: dict
) -> dict:
    values = validate(command, arguments)
    core.get_tenant(session, tenant_id)
    lock_finance(session, tenant_id)
    if values["expected_revision"] != _revision(session, tenant_id):
        raise core.Conflict("Finance preview is stale; reload and review again.")
    before = None
    if command == "finance.target_mapping.set":
        target = _get_row(session, tenant_id, Target, values["target_id"])
        old = session.scalar(
            select(Mapping)
            .where(*_scope(tenant_id, values), Mapping.is_current.is_(True))
            .execution_options(populate_existing=True)
        )
        before = serialize(old) if old else None
        snapshot = {"target": serialize(target)}
        for key, kind in (
            ("external_account", "account"),
            ("external_tax_code", "tax_code"),
        ):
            identity = values[key + "_id"]
            row = (
                _get_row(session, tenant_id, Reference, identity) if identity else None
            )
            if row and (row.target_id != target.id or row.kind != kind):
                raise core.InvalidOperation(
                    "External reference has the wrong target or kind."
                )
            snapshot[key] = serialize(row) if row else None
            if row and values["state"] == "active":
                _active(row)
        for key, kind in (("case", "case_code"), ("group", "coding_group")):
            row = (
                _get(session, tenant_id, values[key + "_reference_id"])
                if values[key + "_reference_id"]
                else None
            )
            if row and row.kind != kind:
                raise core.InvalidOperation("Internal reference has the wrong kind.")
            snapshot[key] = _result(row) if row else None
            if row and values["state"] == "active":
                _active(row)
        account = (
            _get_row(session, tenant_id, SubledgerAccount, values["local_account_id"])
            if values["local_account_id"]
            else None
        )
        snapshot["local_account"] = serialize(account) if account else None
        if values["state"] == "active":
            _active(target)
            if account:
                _active(account)
            if values["mapping_kind"] == "case_routing":
                overlap = session.scalar(
                    select(Mapping.id).where(
                        Mapping.tenant_id == tenant_id,
                        Mapping.target_id == target.id,
                        Mapping.is_current.is_(True),
                        Mapping.state == "active",
                        Mapping.transaction_kind == values["transaction_kind"],
                        Mapping.case_reference_id == values["case_reference_id"],
                        Mapping.group_mode != values["group_mode"],
                    )
                )
                if overlap:
                    raise core.Conflict(
                        "Target mapping modes overlap; block the existing mode first."
                    )
        elif old is None or any(
            getattr(old, key) != values[key]
            for key in ("external_account_id", "external_tax_code_id")
        ):
            raise core.InvalidOperation(
                "Only an existing mapping can be blocked without changing destinations."
            )
        after = {
            k: values[k]
            for k in (*SCOPE, "external_account_id", "external_tax_code_id", "state")
        }
        if (
            old
            and all(getattr(old, k) == v for k, v in after.items())
            and old.configuration_snapshot == snapshot
        ):
            raise core.InvalidOperation("Mapping change has no effect.")
        after.update(
            revision=old.revision + 1 if old else 1,
            replaces_id=old.id if old else None,
            configuration_snapshot=snapshot,
        )
    else:
        is_target = command.startswith("finance.target.")
        model = Target if is_target else Reference
        if command.endswith(".update"):
            row = _get_row(
                session,
                tenant_id,
                model,
                values["target_id" if is_target else "reference_id"],
            )
            before = serialize(row)
            if row.name == values["name"] and row.state == values["state"]:
                raise core.InvalidOperation("Configuration change has no effect.")
            after = {
                **before,
                "name": values["name"],
                "state": values["state"],
                "revision": row.revision + 1,
            }
        else:
            clauses = [model.tenant_id == tenant_id]
            if is_target:
                clauses.append(Target.namespace == values["namespace"])
                after = {k: values[k] for k in ("namespace", "name")}
            else:
                _active(_get_row(session, tenant_id, Target, values["target_id"]))
                clauses.extend(
                    [
                        Reference.target_id == values["target_id"],
                        Reference.kind == values["kind"],
                        Reference.code == values["code"],
                    ]
                )
                after = {k: values[k] for k in ("target_id", "kind", "code", "name")}
            if session.scalar(select(model.id).where(*clauses)):
                raise core.Conflict(
                    "Target namespace or reference code already exists."
                )
            after.update(state="active", revision=1)
    return {"before": before, "after": after, "reason": values["reason"]}


def maintain_target_configuration(
    session: Session,
    tenant_id: str,
    *,
    command: str,
    arguments: dict,
    action_id: str,
    actor_id: str | None = None,
) -> dict:
    core._require_business_mutation(session, tenant_id, "finance_target_maintain")
    coordinator = lock_finance(session, tenant_id)
    review = preview_change(session, tenant_id, command, arguments)
    model = (
        Mapping
        if command == "finance.target_mapping.set"
        else Target
        if command.startswith("finance.target.")
        else Reference
    )
    if model is Mapping:
        if review["before"]:
            _get_row(
                session, tenant_id, Mapping, review["before"]["id"]
            ).is_current = False
            session.flush()
        row = Mapping(
            id=uid("tmap"),
            tenant_id=tenant_id,
            **review["after"],
            reason=review["reason"],
            actor_id=actor_id,
            action_id=action_id,
        )
        session.add(row)
    elif review["before"]:
        row = _get_row(session, tenant_id, model, review["before"]["id"])
        for key in ("name", "state", "revision"):
            setattr(row, key, review["after"][key])
        row.updated_at = now()
    else:
        row = model(
            id=uid("target" if model is Target else "tref"),
            tenant_id=tenant_id,
            **review["after"],
        )
        session.add(row)
    coordinator.revision += 1
    session.flush()
    result = serialize(row)
    emit_business_event(
        session,
        tenant_id,
        "finance.target_configuration_changed",
        "accounting_target",
        row.id if model is Target else row.target_id,
        {
            "before": review["before"],
            "after": result,
            "reason": review["reason"],
            "actor_id": actor_id,
        },
        action_id=action_id,
    )
    session.flush()
    return result


def _classification(session, tenant_id, item, key):
    resolution = item["source_resolution"][key]
    if resolution["status"] not in ("missing", "resolved"):
        return None, key + "_" + resolution["status"]
    identity = resolution["internal_reference_id"] or (
        resolution["reference"] or {}
    ).get("id")
    if identity:
        row = _get(session, tenant_id, identity)
        if row.state != "active":
            return identity, key + "_blocked"
    return identity, None


def _destination(session, tenant_id, target, matches):
    if target.state != "active":
        return {"status": "blocked_target"}
    if len(matches) != 1:
        return {"status": "missing_mapping" if not matches else "ambiguous_mapping"}
    row = matches[0]
    account = _get_row(session, tenant_id, Reference, row.external_account_id)
    tax = (
        _get_row(session, tenant_id, Reference, row.external_tax_code_id)
        if row.external_tax_code_id
        else None
    )
    return {
        "status": "resolved"
        if account.state == "active" and (not tax or tax.state == "active")
        else "blocked_destination",
        "mapping": serialize(row),
        "external_account": serialize(account),
        "external_tax_code": serialize(tax) if tax else None,
    }


def preview_document(
    session: Session,
    tenant_id: str,
    *,
    target_id: str,
    document_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Use one repeatable snapshot without locking or writing operational state."""
    from reality.services.finance.components import component_context

    # A separate read transaction also excludes uncommitted caller writes from this public read.
    with Session(
        session.get_bind().engine.execution_options(isolation_level="REPEATABLE READ"),
        autoflush=False,
    ) as reader:
        return _preview_document(
            reader, tenant_id, target_id, document_id, limit, offset, component_context
        )


def _preview_document(
    session, tenant_id, target_id, document_id, limit, offset, context_builder
):
    target = _get_row(session, tenant_id, Target, target_id)
    doc = _get_row(session, tenant_id, Document, document_id)
    context = context_builder(session, tenant_id, doc.id, limit=limit, offset=offset)
    mappings = list(
        session.scalars(
            select(Mapping).where(
                Mapping.tenant_id == tenant_id,
                Mapping.target_id == target.id,
                Mapping.is_current.is_(True),
                Mapping.state == "active",
            )
        )
    )
    items = []
    for item in context["items"]:
        case, case_error = _classification(session, tenant_id, item, "case")
        group, group_error = _classification(session, tenant_id, item, "group")
        candidates = [
            r
            for r in mappings
            if r.mapping_kind == "case_routing"
            and r.transaction_kind == doc.type
            and r.case_reference_id == case
        ]
        status = case_error or group_error or ("missing_case" if not case else None)
        if item.get("current"):
            action = _get_row(
                session, tenant_id, ChangeProposal, item["current"]["action_id"]
            )
            try:
                reviewed = json.loads(action.input)
            except (TypeError, ValueError):
                reviewed = {}
            if (
                not isinstance(reviewed, dict)
                or reviewed.get("expected_evidence_hash") != item["evidence_hash"]
            ):
                status = "stale_assignment"
        if len({row.group_mode for row in candidates}) > 1:
            status = "ambiguous_mapping"
        if (
            not status
            and candidates
            and candidates[0].group_mode == "exact"
            and not group
        ):
            status = "missing_group"
        matches = [
            r
            for r in candidates
            if r.group_mode == "none" or r.group_reference_id == group
        ]
        destination = (
            {"status": status}
            if status
            else _destination(session, tenant_id, target, matches)
        )
        if target.state != "active":
            destination = {"status": "blocked_target"}
        items.append(
            {
                "received": item,
                "case_reference_id": case,
                "group_reference_id": group,
                **destination,
            }
        )
    legs = []
    entries = list(
        session.scalars(
            select(LedgerEntry)
            .where(
                LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id == doc.id
            )
            .order_by(LedgerEntry.id)
            .limit(limit)
            .offset(offset)
        )
    )
    for entry in entries:
        account = _get_row(session, tenant_id, SubledgerAccount, entry.account_id)
        matches = [
            r
            for r in mappings
            if r.mapping_kind == "local_account" and r.local_account_id == account.id
        ]
        legs.append(
            {
                "entry_id": entry.id,
                "account": serialize(account),
                **(
                    {"status": "blocked_local_account"}
                    if account.state != "active"
                    else _destination(session, tenant_id, target, matches)
                ),
            }
        )
    return {
        "target": serialize(target),
        "document_id": doc.id,
        "transaction_kind": doc.type,
        "revision": context["revision"],
        "items": items,
        "total": context["total"],
        "limit": limit,
        "offset": offset,
        "operational_legs": legs,
        "operational_legs_total": session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(
                LedgerEntry.tenant_id == tenant_id, LedgerEntry.document_id == doc.id
            )
        ),
        "scope": "mapping_resolution_only",
    }
