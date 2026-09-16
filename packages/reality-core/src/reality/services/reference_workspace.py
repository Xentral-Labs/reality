"""Bounded master-data maintenance through canonical application proposals."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    Item,
    Location,
    Party,
    PartyRole,
    PaymentTerm,
    SourceRecord,
    Tenant,
)
from reality.db.query_order import query_order
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _decimal_audit_value,
    _snapshot_revision,
    decimal,
    get_tenant,
    master_data_update_snapshot,
)

FAMILIES = {"customer": Party, "supplier": Party, "item": Item, "location": Location}
REFERENCE_TOOLS = {
    f"{family}_{operation}"
    for family in ("party", "item", "location")
    for operation in ("create", "update")
}


def _base(tenant_id: str, family: str):
    if family not in FAMILIES:
        raise InvalidOperation("Unsupported master data family.")
    model = FAMILIES[family]
    query = select(model).where(model.tenant_id == tenant_id)
    if model is Party:
        query = query.where(
            select(PartyRole.id)
            .where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == Party.id,
                PartyRole.role == family,
            )
            .exists()
        )
    return model, query


def reference_register(
    session: Session,
    tenant_id: str,
    family: str,
    *,
    query: str = "",
    page: int = 1,
    size: int = 50,
    include_inactive: bool = False,
    sort: str = "",
    sort_direction: str = "asc",
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    model, statement = _base(tenant_id, family)
    if not include_inactive:
        statement = statement.where(model.is_active.is_(True))
    if query.strip():
        pattern = f"%{query.strip()}%"
        choices = [model.id.ilike(pattern), model.name.ilike(pattern)]
        if model is Item:
            choices.append(Item.sku.ilike(pattern))
        statement = statement.where(or_(*choices))
    total = int(
        session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    )
    size = max(1, min(size, 100))
    pages = max(1, (total + size - 1) // size)
    page = max(1, min(page, pages))
    records = session.scalars(
        statement.order_by(
            *query_order(
                sort,
                sort_direction,
                {"id": model.id, "name": model.name, "status": model.is_active},
                model.id,
                (
                    model.name,
                    model.id,
                ),
            )
        )
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    labels = _reference_labels(session, tenant_id, records)
    return {
        "items": [
            {
                "id": record.id,
                "family": family,
                "name": record.name,
                "sku": getattr(record, "sku", None),
                "unit": getattr(record, "unit", None),
                "is_active": record.is_active,
                **labels[record.id],
            }
            for record in records
        ],
        "page": {
            "number": page,
            "size": size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_previous": page > 1,
        },
        "scope": {
            "tenant_id": tenant_id,
            "family": family,
            "query": query,
            "include_inactive": include_inactive,
        },
    }


def _reference_labels(
    session: Session, tenant_id: str, records: list[Any]
) -> dict[str, dict[str, Any]]:
    """Resolve only the current page's business references, within the same tenant."""
    location_ids = {
        getattr(row, key, None)
        for row in records
        for key in ("default_location_id", "parent_location_id")
    } - {None}
    term_ids = {getattr(row, "payment_term_id", None) for row in records} - {None}
    locations = (
        {
            row.id: row.name
            for row in session.scalars(
                select(Location).where(
                    Location.tenant_id == tenant_id, Location.id.in_(location_ids)
                )
            )
        }
        if location_ids
        else {}
    )
    terms = (
        {
            row.id: row
            for row in session.scalars(
                select(PaymentTerm).where(
                    PaymentTerm.tenant_id == tenant_id, PaymentTerm.id.in_(term_ids)
                )
            )
        }
        if term_ids
        else {}
    )
    result = {}
    for row in records:
        if isinstance(row, Party):
            term = terms.get(row.payment_term_id)
            result[row.id] = {
                "accounting_code": row.accounting_code,
                "default_currency": row.default_currency,
                "payment_term_code": term.code if term else "",
                "payment_term_name": term.name if term else "",
            }
        elif isinstance(row, Item):
            result[row.id] = {
                "item_type": row.item_type,
                "default_location_name": locations.get(row.default_location_id),
            }
        else:
            result[row.id] = {
                "type": row.type,
                "allows_stock": row.allows_stock,
                "parent_location_name": locations.get(row.parent_location_id),
            }
    return result


def _source_identity(
    session: Session, tenant_id: str, source_record_id: str | None
) -> dict[str, str]:
    source = (
        session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant_id, SourceRecord.id == source_record_id
            )
        )
        if source_record_id
        else None
    )
    return {
        "source_system": source.source_system if source else "",
        "external_id": source.external_id if source else "",
    }


def reference_detail(
    session: Session, tenant_id: str, family: str, record_id: str
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    model, statement = _base(tenant_id, family)
    record = session.scalar(statement.where(model.id == record_id))
    if record is None:
        raise NotFound("Master data record not found.")
    core_family = "party" if model is Party else family
    snapshot = master_data_update_snapshot(session, tenant_id, core_family, record.id)
    codes = _source_identity(session, tenant_id, record.source_record_id)
    if core_family == "party":
        codes["payment_term_code"] = (
            session.scalar(
                select(PaymentTerm.code).where(
                    PaymentTerm.tenant_id == tenant_id,
                    PaymentTerm.id == snapshot["payment_term_id"],
                )
            )
            if snapshot["payment_term_id"]
            else None
        ) or ""
    detail = {
        "id": record.id,
        "family": family,
        **snapshot,
        **codes,
        **_reference_labels(session, tenant_id, [record])[record.id],
        "is_active": record.is_active,
        "expected_revision": _snapshot_revision(snapshot),
    }

    from reality.services.operational_previews import master_data_preview

    detail["preview_sections"] = master_data_preview(detail)
    return detail


def require_ordinary_workspace(session: Session, tenant_id: str) -> None:
    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise NotFound("Company not found.")
    if tenant.purpose == "playground":
        raise InvalidOperation("Use the reviewed practice actions for this company.")


PARTY_ROLES = ("company", "customer", "supplier")
ITEM_TYPES = ("stocked", "service", "charge")
TRACKING_TYPES = ("none", "lot", "serial")
# Every operational field the shared create/update services accept, with the
# rule that normalises it. Lossless source_payload is deliberately absent.
FIELD_RULES: dict[str, dict[str, Any]] = {
    "party": {
        "name": "required",
        "type": ("choice", PARTY_ROLES),
        "roles": "roles",
        "accounting_code": "text",
        "payment_term_code": "text",
        "default_currency": "currency",
        "credit_limit": "money",
        "tax_identifier": "text",
        "source_system": "text",
        "external_id": "text",
    },
    "item": {
        "sku": "required",
        "name": "required",
        "unit": "required",
        "item_type": ("choice", ITEM_TYPES),
        "tracking_type": ("choice", TRACKING_TYPES),
        "default_location_id": "reference",
        "purchase_unit": "text",
        "conversion_factor": "factor",
        "lead_time_days": "count",
        "source_system": "text",
        "external_id": "text",
    },
    "location": {
        "name": "required",
        "type": "required",
        "parent_location_id": "reference",
        "allows_stock": "flag",
        "source_system": "text",
        "external_id": "text",
    },
}
CREATE_DEFAULTS = {"item": {"unit": "pcs"}, "location": {"type": "warehouse"}}


def _normalize(key: str, rule: Any, value: Any) -> Any:
    label = key.replace("_", " ")
    if rule == "flag":
        if not isinstance(value, bool):
            raise InvalidOperation(f"{label.capitalize()} must be true or false.")
        return value
    if rule == "roles":
        if (
            not isinstance(value, list)
            or not value
            or any(
                not isinstance(role, str) or role not in PARTY_ROLES for role in value
            )
        ):
            raise InvalidOperation(
                "Party roles must be company, customer, or supplier."
            )
        return sorted(set(value))
    if rule == "count":
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise InvalidOperation(f"{label.capitalize()} must be a whole number.")
        try:
            number = int(str(value).strip())
        except ValueError:
            raise InvalidOperation(f"{label.capitalize()} must be a whole number.")
        if number < 0:
            raise InvalidOperation(f"{label.capitalize()} cannot be negative.")
        return number
    if rule in {"money", "factor"}:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise InvalidOperation(f"{label.capitalize()} must be a number.")
        try:
            amount = decimal(str(value).strip())
        except (ArithmeticError, ValueError):
            raise InvalidOperation(f"{label.capitalize()} must be a number.")
        if rule == "money" and amount < 0:
            raise InvalidOperation(f"{label.capitalize()} cannot be negative.")
        if rule == "factor" and amount <= 0:
            raise InvalidOperation(f"{label.capitalize()} must be greater than zero.")
        return _decimal_audit_value(amount)
    if not isinstance(value, str):
        raise InvalidOperation(f"{label.capitalize()} must be text.")
    text = value.strip()
    if rule == "required":
        if not text or len(text) > 500:
            raise InvalidOperation(f"A {label} of at most 500 characters is required.")
        return text
    if rule == "currency":
        text = text.upper() or "EUR"
        if not re.fullmatch(r"[A-Z]{3}", text):
            raise InvalidOperation("Default currency must be a three-letter code.")
        return text
    if rule == "reference":
        return text or None
    if isinstance(rule, tuple):
        if text not in rule[1]:
            raise InvalidOperation(
                f"{label.capitalize()} must be one of: {', '.join(rule[1])}."
            )
        return text
    return text


def _editable_values(core_family: str, detail: dict[str, Any]) -> dict[str, Any]:
    """Current values of every editable field, so an omitted field is preserved."""
    return {key: detail[key] for key in FIELD_RULES[core_family]}


def prepare_reference(
    session: Session,
    tenant_id: str,
    family: str,
    operation: str,
    record: dict[str, Any],
    *,
    request_id: str,
    actor_id: str | None = None,
) -> ChangeProposal:
    from reality.tools.application import create_change_proposal

    _base(tenant_id, family)
    if operation not in {"create", "update"}:
        raise InvalidOperation("Unsupported master data operation.")
    if not request_id or len(request_id) > 200:
        raise InvalidOperation("A bounded request identity is required.")
    core_family = "party" if family in {"customer", "supplier"} else family
    rules = FIELD_RULES[core_family]
    control = {"id", "expected_revision"} if operation == "update" else set()
    unknown = set(record) - set(rules) - control
    if unknown:
        raise InvalidOperation(
            "Unsupported master data fields: " + ", ".join(sorted(unknown)) + "."
        )
    intent = {
        key: _normalize(key, rules[key], value)
        for key, value in record.items()
        if key in rules
    }
    for key in control:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InvalidOperation("An exact record and review revision are required.")
        intent[key] = value.strip()
    if operation == "create":
        for key, rule in rules.items():
            if rule == "required" and key not in intent:
                default = CREATE_DEFAULTS.get(core_family, {}).get(key)
                if default is None:
                    raise InvalidOperation(
                        f"A {key.replace('_', ' ')} of at most 500 characters is required."
                    )
                intent[key] = default
    if core_family == "party" and "roles" in intent and family not in intent["roles"]:
        raise InvalidOperation(f"The {family} role must remain on a {family} record.")
    tool = f"{core_family}_{operation}"
    identity = (
        "act_"
        + hashlib.sha256(
            json.dumps([tenant_id, actor_id, request_id]).encode()
        ).hexdigest()[:32]
    )
    lock_delivery_state(session, tenant_id)
    session.expire_all()
    require_ordinary_workspace(session, tenant_id)
    existing = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == identity
        )
    )
    if existing:
        prior = json.loads(existing.input).get("records", [{}])[0]
        same_role = core_family != "party" or family in prior.get("roles", [])
        if (
            existing.type != f"tool:{tool}"
            or not same_role
            or any(prior.get(key) != value for key, value in intent.items())
        ):
            raise InvalidOperation(
                "Request identity was already used for a different change."
            )
        return existing
    if operation == "update":
        detail = reference_detail(session, tenant_id, family, intent["id"])
        if detail["expected_revision"] != intent["expected_revision"]:
            raise InvalidOperation(
                "Master data changed since review; reload the record."
            )
        canonical = {**_editable_values(core_family, detail), **intent}
        if (
            core_family == "item"
            and detail["default_location_id"]
            and canonical["default_location_id"] is None
        ):
            raise InvalidOperation(
                "A default location cannot be removed; choose another location."
            )
        if (
            core_family == "location"
            and canonical["parent_location_id"] == intent["id"]
        ):
            raise InvalidOperation("A location cannot be its own parent.")
    else:
        canonical = dict(intent)
        if core_family == "party":
            canonical.setdefault("type", family)
            canonical.setdefault("roles", [family])
    proposal = create_change_proposal(
        session,
        tenant_id,
        tool,
        {"records": [canonical]},
        actor_type="human",
        _commit=False,
    )
    proposal.id = identity
    session.commit()
    return proposal


def reference_proposal(
    session: Session, tenant_id: str, proposal_id: str
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id
        )
    )
    if proposal is None or proposal.type.removeprefix("tool:") not in REFERENCE_TOOLS:
        raise NotFound("Master data proposal not found.")
    output = json.loads(proposal.output or "{}")
    return {
        "id": proposal.id,
        "tool": proposal.type.removeprefix("tool:"),
        "status": proposal.status,
        "input": json.loads(proposal.input),
        "output": output,
        "links": output.get("records", []) if proposal.status == "executed" else [],
    }
