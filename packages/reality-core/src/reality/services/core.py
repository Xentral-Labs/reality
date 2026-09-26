from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections.abc import Callable, Collection, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Select,
    and_,
    case,
    cast,
    delete,
    func,
    literal,
    null,
    or_,
    select,
    text,
    union_all,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.sql.elements import ColumnElement

from reality.db.core import (
    AISettings,
    AppUser,
    Base,
    BusinessEvent,
    ChangeProposal,
    ChatMessage,
    ChatSession,
    Commitment,
    CommitmentHold,
    CommitmentRevision,
    Document,
    DocumentLine,
    Fact,
    HandlingUnit,
    ImportJob,
    InterpretationOutcome,
    InterpretationRecordReference,
    Item,
    LedgerEntry,
    LedgerReversal,
    Location,
    Lot,
    Movement,
    MovementCorrection,
    Party,
    PartyEmailAddress,
    PartyGroup,
    PartyGroupMember,
    PartyGroupPriceList,
    PartyHold,
    PartyPriceList,
    PartyRole,
    PaymentTerm,
    PriceList,
    PriceListEntry,
    ProjectionCheckpoint,
    Reservation,
    ReturnAnnouncement,
    SerialUnit,
    SettlementAllocation,
    Shipment,
    ShipmentPackage,
    SourceArtifact,
    SourceCapability,
    SourceRecord,
    SourceStream,
    SourceSystem,
    Tenant,
    TenantEventProgress,
    UTCDateTime,
    now,
    uid,
)
from reality.domain.calendar import InvalidDay, as_day
from reality.domain.stock_scope import movement_at
from reality.integrations.catalog import connector_catalog, connector_shell
from reality.services.interaction_recorder import note_event as note_interaction_event
from reality.storyline.recorder import wrap_chat

ZERO = Decimal(0)
MANUAL_OPERATIONAL_DOCUMENT_TYPES = (
    "sales_order",
    "purchase_order",
    "sales_invoice",
    "supplier_invoice",
    "credit_note",
    "supplier_credit_note",
)
HOLD_REASONS = {
    "credit_check",
    "customer_request",
    "address_clarification",
    "compliance",
    "manual_review",
    "other",
}

INTERPRETATION_CLASSIFICATIONS = {
    "interpreted",
    "needs_review",
    "unsupported",
    "stale",
    "conflict",
    "failed",
}
INTERPRETATION_RECORD_TYPES = {
    "document",
    "document_line",
    "commitment",
    "ledger_entry",
    "settlement_allocation",
}


def validate_manual_operational_document_type(document_type: object) -> str:
    """Validate the closed public operational vocabulary without constraining intake."""
    normalized = str(document_type).strip()
    if normalized not in MANUAL_OPERATIONAL_DOCUMENT_TYPES:
        raise InvalidOperation(
            "Unsupported operational document type. Expected one of: "
            + ", ".join(MANUAL_OPERATIONAL_DOCUMENT_TYPES)
            + "."
        )
    return normalized


AGENT_DISCOVERY_MODELS: dict[str, tuple[type[Base], tuple[str, ...]]] = {
    "party": (Party, ("id", "name", "type", "is_active", "default_currency")),
    "item": (
        Item,
        ("id", "sku", "name", "unit", "item_type", "tracking_type", "is_active"),
    ),
    "location": (
        Location,
        ("id", "name", "type", "parent_location_id", "allows_stock", "is_active"),
    ),
    "document": (
        Document,
        (
            "id",
            "type",
            "number",
            "party_id",
            "currency",
            "gross_amount",
            "document_date",
        ),
    ),
    "commitment": (
        Commitment,
        (
            "id",
            "type",
            "from_party_id",
            "to_party_id",
            "item_id",
            "location_id",
            "quantity",
            "amount",
            "currency",
            "due_at",
            "status",
            "document_id",
            "document_line_id",
        ),
    ),
    "movement": (
        Movement,
        (
            "id",
            "type",
            "item_id",
            "from_location_id",
            "to_location_id",
            "quantity",
            "commitment_id",
            "handling_unit_id",
            "lot_id",
            "serial_unit_id",
            "occurred_at",
        ),
    ),
    "reservation": (
        Reservation,
        (
            "id",
            "commitment_id",
            "quantity",
            "status",
            "handling_unit_id",
            "lot_id",
            "serial_unit_id",
        ),
    ),
    "handling_unit": (HandlingUnit, ("id", "nve", "source_record_id")),
    "lot": (Lot, ("id", "item_id", "lot_number", "source_record_id")),
    "serial_unit": (
        SerialUnit,
        ("id", "item_id", "serial_number", "lot_id", "source_record_id"),
    ),
    "payment_term": (
        PaymentTerm,
        ("id", "code", "name", "due_days", "requires_prepayment", "is_active"),
    ),
    "price_list": (
        PriceList,
        ("id", "code", "name", "direction", "currency", "is_default", "is_active"),
    ),
    "price_list_entry": (
        PriceListEntry,
        ("id", "price_list_id", "item_id", "min_quantity", "unit_price", "unit"),
    ),
    "party_group": (PartyGroup, ("id", "code", "name", "is_active")),
    "ledger_entry": (
        LedgerEntry,
        (
            "id",
            "document_id",
            "party_id",
            "account",
            "debit_credit",
            "amount",
            "currency",
            "posting_group_id",
            "effective_at",
        ),
    ),
    "source_system": (SourceSystem, ("id", "code", "name", "description", "is_active")),
    "source_capability": (
        SourceCapability,
        ("id", "source_system_id", "source_type", "target_type", "is_active"),
    ),
    "source_record": (
        SourceRecord,
        (
            "id",
            "source_system",
            "source_type",
            "external_id",
            "version",
            "supersedes_source_record_id",
            "payload_hash",
            "received_at",
        ),
    ),
}
FILE_INTERPRETER_TARGETS = {
    "item",
    "party",
    "location",
    "sales_order",
    "inventory_snapshot",
    "bank_statement",
}


class RealityError(Exception):
    """Base class for business-readable application errors."""


class NotFound(RealityError):
    pass


class InvalidOperation(RealityError):
    pass


class InterpretationNeedsReview(RealityError):
    """An interpreter safely declined because business meaning is ambiguous."""


class ShopifyUpdateNeedsReview(InterpretationNeedsReview):
    """A changed source cannot safely amend existing operational Reality yet."""

    summary = (
        "Shopify order updates require review. The new source is retained; "
        "existing operational records remain unchanged. Automatic amendment "
        "is not supported."
    )


class Conflict(InvalidOperation):
    """The requested mutation is valid in shape but based on stale state."""


def business_discovery_statement(
    session: OrmSession,
    tenant_id: str,
    family: str,
    *,
    query: str = "",
    record_id: str | None = None,
) -> tuple[Select, type[Base], tuple[str, ...]]:
    """Build the same scoped selection for legacy discovery and cursor pages."""
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    definition = AGENT_DISCOVERY_MODELS.get(family.strip().lower())
    if definition is None:
        raise InvalidOperation("Unsupported discovery family.")
    model, fields = definition
    statement = select(model).where(model.tenant_id == tenant_id)
    if record_id:
        statement = statement.where(model.id == record_id)
    elif query.strip():
        raw_query = query.strip()
        needle = f"%{raw_query}%"
        searchable = [
            getattr(model, name)
            for name in (
                "name",
                "code",
                "sku",
                "number",
                "external_id",
                "nve",
                "lot_number",
                "serial_number",
            )
            if hasattr(model, name)
        ]
        if searchable:
            predicates = [column.ilike(needle) for column in searchable]
            if model is Party and "@" in raw_query:
                normalized = _normalize_party_email(raw_query)
                predicates.append(
                    select(PartyEmailAddress.id)
                    .where(
                        PartyEmailAddress.tenant_id == tenant_id,
                        PartyEmailAddress.party_id == Party.id,
                        PartyEmailAddress.normalized_email == normalized,
                    )
                    .exists()
                )
            statement = statement.where(or_(*predicates))
    return statement.order_by(model.id), model, fields


def business_discovery_record(
    row: Any, fields: tuple[str, ...], session: OrmSession
) -> dict[str, Any]:
    result = {}
    for field in fields:
        value = getattr(row, field)
        result[field] = (
            value.isoformat()
            if isinstance(value, (date, datetime))
            else str(value)
            if isinstance(value, Decimal)
            else value
        )
    if isinstance(row, (Commitment, Movement, Reservation)):
        item_id = (
            row.item_id
            if not isinstance(row, Reservation)
            else session.scalar(
                select(Commitment.item_id).where(
                    Commitment.tenant_id == row.tenant_id,
                    Commitment.id == row.commitment_id,
                )
            )
        )
        unit = (
            session.scalar(
                select(Item.unit).where(
                    Item.tenant_id == row.tenant_id, Item.id == item_id
                )
            )
            if item_id
            else None
        )
        result.update(
            unit=unit or None,
            unit_status="known" if unit else "unknown",
            quantity_basis="item_unit",
        )
    if isinstance(row, LedgerEntry):
        result["side"] = result["debit_credit"]
    if isinstance(row, Party):
        result["emails"] = [
            {"email": address.email, "label": address.label}
            for address in session.scalars(
                select(PartyEmailAddress)
                .where(
                    PartyEmailAddress.tenant_id == row.tenant_id,
                    PartyEmailAddress.party_id == row.id,
                )
                .order_by(PartyEmailAddress.normalized_email, PartyEmailAddress.id)
            )
        ]
    return result


def discover_business_records(
    session: OrmSession,
    tenant_id: str,
    family: str,
    *,
    query: str = "",
    limit: int = 25,
    record_id: str | None = None,
) -> list[dict[str, Any]]:
    """Legacy bounded lookup; complete traversal uses the shared page contract."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise InvalidOperation("Discovery limit must be between 1 and 100.")
    statement, _, fields = business_discovery_statement(
        session, tenant_id, family, query=query, record_id=record_id
    )
    rows = list(session.scalars(statement.limit(limit)))
    if record_id and not rows:
        raise NotFound("Business record not found.")
    return [business_discovery_record(row, fields, session) for row in rows]


def decimal(value: Decimal | float | str) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("Quantity and amount values must be finite.")
    return result


def _normalize_party_email(value: str) -> str:
    normalized = value.strip().casefold()
    if (
        len(normalized) > 320
        or "@" not in normalized
        or normalized.startswith("@")
        or normalized.endswith("@")
        or "." not in normalized.rsplit("@", 1)[1]
    ):
        raise InvalidOperation("Enter a valid email address.")
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError as error:
        raise InvalidOperation("Email addresses must use an ASCII domain.") from error
    return normalized


def _party_email_values(values: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if values is None:
        return []
    if len(values) > 20:
        raise InvalidOperation("A Party can have at most 20 email addresses.")
    normalized_values: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        email = str(value.get("email") or "").strip()
        normalized = _normalize_party_email(email)
        label = str(value.get("label") or "").strip()
        if len(label) > 80:
            raise InvalidOperation(
                "Party email labels can contain at most 80 characters."
            )
        if normalized in seen:
            raise InvalidOperation("A Party cannot contain duplicate email addresses.")
        seen.add(normalized)
        normalized_values.append(
            {"email": email, "normalized_email": normalized, "label": label}
        )
    return sorted(normalized_values, key=lambda item: item["normalized_email"])


def _replace_party_emails(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    values: list[dict[str, Any]],
) -> None:
    normalized = _party_email_values(values)
    for existing in session.scalars(
        select(PartyEmailAddress).where(
            PartyEmailAddress.tenant_id == tenant_id,
            PartyEmailAddress.party_id == party_id,
        )
    ):
        session.delete(existing)
    session.flush()
    session.add_all(
        PartyEmailAddress(
            id=uid("pem"),
            tenant_id=tenant_id,
            party_id=party_id,
            email=value["email"],
            normalized_email=value["normalized_email"],
            label=value["label"],
        )
        for value in normalized
    )


def positive(value: Decimal | float | str, field: str = "quantity") -> Decimal:
    result = decimal(value)
    if result <= ZERO:
        raise InvalidOperation(f"{field.capitalize()} must be greater than zero.")
    return result


def utc_datetime(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise InvalidOperation(
                "Date/time must be a valid ISO 8601 value."
            ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


#: The proposal whose confirmed execution is writing events right now, as
#: (tenant id, proposal id). Set only by `approve_and_execute_proposal`.
_executing: ContextVar[tuple[str, str] | None] = ContextVar(
    "executing_proposal", default=None
)


@contextmanager
def executing_proposal(tenant_id: str, proposal_id: str) -> Iterator[None]:
    """Let every event written in this block reference the proposal executing it.

    Spec 263 FR-005. The proposal id used to reach a handler only when the tool
    was on a list, and four families of master data never made it onto that list,
    so a price or a payment term could not say which decision created it. The one
    function that writes events now fills the reference itself, for every tool.
    """
    token = _executing.set((tenant_id, proposal_id))
    try:
        yield
    finally:
        _executing.reset(token)


def emit_business_event(
    session: OrmSession,
    tenant_id: str,
    event_type: str,
    subject_type: str,
    subject_id: str,
    payload: dict[str, Any],
    *,
    source_record_id: str | None = None,
    action_id: str | None = None,
    causation_id: str | None = None,
    correlation_id: str | None = None,
    occurred_at: datetime | None = None,
) -> BusinessEvent:
    # Lock the tenant row so tenant-local sequence allocation remains deterministic
    # without making the sequence event identity.
    _require_business_mutation(session, tenant_id, "emit_business_event")
    if action_id is None:
        # An explicit reference always wins: costing and commercial matching thread
        # the action they were handed, and overriding it would misattribute them.
        executing = _executing.get()
        if executing is not None and executing[0] == tenant_id:
            action_id = executing[1]
    from reality.services.tenant_policy import require_decision_action

    require_decision_action(session, tenant_id, action_id, event_type=event_type)
    session.scalar(select(Tenant).where(Tenant.id == tenant_id).with_for_update())
    progress = _event_progress(session, tenant_id)
    last_sequence = (
        progress.last_event_sequence
        if progress is not None
        else session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == tenant_id
            )
        )
        or 0
    )
    event = BusinessEvent(
        id=uid("evt"),
        tenant_id=tenant_id,
        sequence=last_sequence + 1,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        occurred_at=occurred_at or now(),
        recorded_at=now(),
        payload=json.dumps(payload, default=str, sort_keys=True, separators=(",", ":")),
        source_record_id=source_record_id,
        action_id=action_id,
        causation_id=causation_id,
        correlation_id=correlation_id,
    )
    session.add(event)
    note_interaction_event(tenant_id, event.id)
    if progress is not None:
        # The company's progress and the event that moved it are written in one
        # transaction, so a reader that sees one sees the other (spec 181 FR-004).
        progress.last_event_sequence = event.sequence
    return event


#: Whether this process has found the event-progress table. It is asked once, because
#: the answer cannot change under a running process: a migration adds the table before
#: the code that needs it is asked to do anything with it.
_progress_table: dict[str, bool] = {}


def _event_progress(session: OrmSession, tenant_id: str) -> TenantEventProgress | None:
    """The company's event progress row, or None where the schema has no such table.

    The number is an accelerator for deciding what to refresh (spec 181 FR-004), not a
    business record — the events themselves are the truth, and the sequence can always
    be read from them. So its absence must not stop business from happening, which is
    not only about old schemas in tests: during a rolling upgrade the new code runs
    against the old schema until the migration lands, and a company that cannot record
    a sale for that window would be a far worse failure than a scheduler sweep that has
    to fall back to visiting every company.
    """
    bind = session.get_bind()
    # A bound session hands back a Connection; only the engine behind it names the
    # database this answer belongs to.
    url = str(getattr(bind, "engine", bind).url)
    if url not in _progress_table:
        _progress_table[url] = sa_inspect(bind).has_table(
            TenantEventProgress.__tablename__
        )
    if not _progress_table[url]:
        return None
    progress = session.get(TenantEventProgress, tenant_id)
    if progress is None:
        progress = TenantEventProgress(tenant_id=tenant_id, last_event_sequence=0)
        session.add(progress)
    return progress


def business_events(
    session: OrmSession, tenant_id: str, *, after_sequence: int = 0
) -> list[BusinessEvent]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.sequence > after_sequence,
            )
            .order_by(BusinessEvent.sequence)
        )
    )


def _attention_event_condition():
    return or_(
        BusinessEvent.event_type.like("%failed%"),
        BusinessEvent.event_type.like("%unmapped%"),
        BusinessEvent.event_type.like("%conflict%"),
        BusinessEvent.event_type.like("%error%"),
        BusinessEvent.event_type.like("%rejected%"),
        func.lower(BusinessEvent.payload).like('%"disposition": "failed"%'),
    )


def activity_signal(
    session: OrmSession, tenant_id: str, *, after_sequence: int = 0
) -> dict[str, int]:
    """Return a lightweight tenant-scoped cursor over durable business events."""
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    cursor = max(0, after_sequence)
    latest_sequence = int(
        session.scalar(
            select(func.max(BusinessEvent.sequence)).where(
                BusinessEvent.tenant_id == tenant_id
            )
        )
        or 0
    )
    new_criteria = (
        BusinessEvent.tenant_id == tenant_id,
        BusinessEvent.sequence > cursor,
    )
    new_events = int(
        session.scalar(
            select(func.count()).select_from(BusinessEvent).where(*new_criteria)
        )
        or 0
    )
    attention_events = int(
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(*new_criteria, _attention_event_condition())
        )
        or 0
    )
    return {
        "latest_sequence": latest_sequence,
        "new_events": new_events,
        "attention_events": attention_events,
    }


def _canonical_fact_value(contract: dict[str, Any], value: Any) -> str:
    value_type = contract["value_type"]
    try:
        if value_type in {"string", "enum"}:
            canonical: Any = str(value).strip()
            if not canonical:
                raise ValueError
            if value_type == "enum" and canonical not in contract["allowed_values"]:
                raise ValueError
        elif value_type == "date":
            canonical = date.fromisoformat(str(value)).isoformat()
        elif value_type == "datetime":
            parsed = utc_datetime(str(value))
            if parsed is None:
                raise ValueError
            canonical = parsed.isoformat()
        elif value_type == "integer":
            canonical = int(value)
            if isinstance(value, (float, Decimal)) and Decimal(str(value)) != canonical:
                raise ValueError
        elif value_type == "decimal":
            canonical = format(decimal(value).normalize(), "f")
        elif value_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError
            canonical = value
        else:  # The catalog validator rejects this before runtime use.
            raise ValueError
    except (TypeError, ValueError, ArithmeticError) as error:
        raise InvalidOperation(
            f"Fact value does not satisfy {contract['predicate']} ({value_type})."
        ) from error
    if isinstance(canonical, str):
        return canonical
    return json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _fact_contract(predicate: str) -> dict[str, Any]:
    from reality.catalogs import load_application_catalog

    entry = next(
        (
            item
            for item in load_application_catalog()["fact_predicates"]
            if item["predicate"] == predicate
        ),
        None,
    )
    if entry is None:
        raise InvalidOperation("Fact predicate is not supported.")
    return entry


def observe_fact(
    session: OrmSession,
    tenant_id: str,
    *,
    source_record_id: str,
    subject_type: str,
    subject_id: str,
    predicate: str,
    value: Any,
    observed_at: datetime | str,
    idempotency_key: str,
    action_id: str | None = None,
) -> Fact:
    """Append one validated, source-supported observation exactly once."""
    _require_business_mutation(session, tenant_id, "observe_fact")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    if not source_record_id.strip():
        raise InvalidOperation("Fact source record is required.")
    source = _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    normalized_subject_type = subject_type.strip()
    normalized_subject_id = subject_id.strip()
    normalized_predicate = predicate.strip()
    normalized_key = idempotency_key.strip()
    if (
        not normalized_subject_type
        or not normalized_subject_id
        or not normalized_predicate
    ):
        raise InvalidOperation("Fact subject, subject ID and predicate are required.")
    if not normalized_key:
        raise InvalidOperation("Fact idempotency key is required.")
    contract = _fact_contract(normalized_predicate)
    if normalized_subject_type not in contract["subject_types"]:
        raise InvalidOperation("Fact predicate does not support this subject type.")
    subject_models = {
        "party": Party,
        "item": Item,
        "location": Location,
        "document": Document,
        "document_line": DocumentLine,
        "commitment": Commitment,
        "reservation": Reservation,
        "movement": Movement,
        "ledger_entry": LedgerEntry,
        "lot": Lot,
    }
    subject_model = subject_models.get(normalized_subject_type)
    if subject_model is None:
        raise InvalidOperation("Fact subject type is not supported.")
    _tenant_record(session, subject_model, tenant_id, normalized_subject_id)
    canonical_value = _canonical_fact_value(contract, value)
    canonical_observed_at = utc_datetime(observed_at)
    if canonical_observed_at is None:
        raise InvalidOperation("Fact observation time is required.")
    request_fingerprint = hashlib.sha256(
        f"{tenant_id}\x1f{normalized_key}".encode()
    ).hexdigest()
    fact, _created = _persist_fact_observation(
        session,
        tenant_id,
        source=source,
        subject_type=normalized_subject_type,
        subject_id=normalized_subject_id,
        predicate=normalized_predicate,
        value=canonical_value,
        observed_at=canonical_observed_at,
        request_fingerprint=request_fingerprint,
        action_id=action_id,
        interpretation_rule_id=None,
        commit=True,
    )
    return fact


def _persist_fact_observation(
    session: OrmSession,
    tenant_id: str,
    *,
    source: SourceRecord,
    subject_type: str,
    subject_id: str,
    predicate: str,
    value: str,
    observed_at: datetime,
    request_fingerprint: str,
    action_id: str | None,
    interpretation_rule_id: str | None,
    commit: bool,
) -> tuple[Fact, bool]:
    """Persist one already validated Fact without owning the caller's transaction."""
    if session.get_bind().dialect.name == "postgresql":
        lock_key = int.from_bytes(
            hashlib.sha256(request_fingerprint.encode()).digest()[:8],
            "big",
            signed=True,
        )
        session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
        )
    existing = session.scalar(
        select(Fact).where(
            Fact.tenant_id == tenant_id,
            Fact.request_fingerprint == request_fingerprint,
        )
    )
    intended = {
        "source_record_id": source.id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "predicate": predicate,
        "value": value,
        "observed_at": observed_at,
        "interpretation_rule_id": interpretation_rule_id,
    }
    if existing is not None:
        stored = {key: getattr(existing, key) for key in intended}
        if stored != intended:
            raise InvalidOperation("Idempotency key was already used for another Fact.")
        return existing, False
    fact = Fact(
        id=uid("fct"),
        tenant_id=tenant_id,
        subject_type=subject_type,
        subject_id=subject_id,
        predicate=predicate,
        value=value,
        observed_at=observed_at,
        source_record_id=source.id,
        request_fingerprint=request_fingerprint,
        interpretation_rule_id=interpretation_rule_id,
        recorded_at=now(),
    )
    session.add(fact)
    emit_business_event(
        session,
        tenant_id,
        "fact.observed",
        "fact",
        fact.id,
        {
            "subject_type": fact.subject_type,
            "subject_id": fact.subject_id,
            "predicate": fact.predicate,
            "value": fact.value,
        },
        source_record_id=fact.source_record_id,
        occurred_at=fact.observed_at,
        action_id=action_id,
    )
    if commit:
        session.commit()
    return fact, True


def _tenant_record(session: OrmSession, model, tenant_id: str, record_id: str):
    if model is Tenant:
        record = session.scalar(
            select(Tenant).where(Tenant.id == tenant_id, Tenant.id == record_id)
        )
        if record is None:
            raise NotFound("Tenant not found.")
        return record
    record = session.scalar(
        select(model).where(model.tenant_id == tenant_id, model.id == record_id)
    )
    if record is None:
        raise NotFound(f"{model.__name__} not found.")
    return record


def _require_business_mutation(
    session: OrmSession, tenant_id: str, operation: str
) -> None:
    # Import at the boundary because the policy shares the domain error types.
    # Only fixed, transaction-bound reference setup is currently admitted.
    from reality.services.tenant_policy import require_core_operation

    require_core_operation(session, tenant_id, operation)
    from reality.services.business_locks import DELIVERY_WRITERS, lock_delivery_state

    finance_operations = {
        "post_ledger",
        "post_sales_invoice",
        "post_supplier_invoice",
        "post_customer_payment",
        "record_customer_payment",
        "post_supplier_payment",
        "record_supplier_payment",
        "post_sales_credit_note",
        "post_supplier_credit_note",
        "record_customer_refund",
        "post_customer_refund",
        "record_supplier_refund",
        "post_supplier_refund",
        "allocate_settlement",
        "allocate_credit_note",
        "allocate_supplier_credit_note",
        "reverse_ledger_posting_group",
    }
    # Every finance writer acquires the shared business lock before finance state.
    if operation in DELIVERY_WRITERS or operation in finance_operations:
        lock_delivery_state(session, tenant_id)
    if operation in finance_operations:
        from reality.services.finance.accounts import lock_finance

        state = lock_finance(session, tenant_id)
        state.revision += 1


def tenants(session: OrmSession, *, include_archived: bool = False) -> list[Tenant]:
    query = select(Tenant)
    if not include_archived:
        query = query.where(Tenant.archived_at.is_(None))
    return list(session.scalars(query.order_by(Tenant.name)))


def get_tenant(session: OrmSession, tenant_id: str) -> Tenant:
    return _tenant_record(session, Tenant, tenant_id, tenant_id)


def find_tenant(session: OrmSession, name_or_id: str) -> Tenant:
    by_id = session.scalar(select(Tenant).where(Tenant.id == name_or_id))
    if by_id:
        return by_id
    matches = list(session.scalars(select(Tenant).where(Tenant.name == name_or_id)))
    if not matches:
        raise NotFound("Tenant not found.")
    if len(matches) > 1:
        raise InvalidOperation("Tenant name is ambiguous; use its opaque ID.")
    return matches[0]


def create_tenant(
    session: OrmSession,
    name: str,
    *,
    _commit: bool = True,
    _with_finance_defaults: bool = True,
) -> Tenant:
    if not name.strip():
        raise InvalidOperation("Tenant name is required.")
    tenant = Tenant(id=uid("ten"), name=name.strip())
    session.add(tenant)
    session.flush()
    if _with_finance_defaults:
        from reality.services.finance.accounts import _bootstrap_accounts

        _bootstrap_accounts(session, tenant.id)
    if _commit:
        session.commit()
    else:
        session.flush()
    return tenant


def archive_tenant(session: OrmSession, tenant_id: str) -> Tenant:
    _require_business_mutation(session, tenant_id, "archive_tenant")
    tenant = get_tenant(session, tenant_id)
    if tenant.archived_at is not None:
        raise InvalidOperation("Tenant is already archived.")
    active_count = (
        session.scalar(
            select(func.count(Tenant.id)).where(Tenant.archived_at.is_(None))
        )
        or 0
    )
    if active_count <= 1:
        raise InvalidOperation(
            "Create or restore another tenant before archiving this one."
        )
    tenant.archived_at = now()
    session.commit()
    return tenant


def restore_tenant(session: OrmSession, tenant_id: str) -> Tenant:
    _require_business_mutation(session, tenant_id, "restore_tenant")
    tenant = get_tenant(session, tenant_id)
    if tenant.archived_at is None:
        raise InvalidOperation("Tenant is not archived.")
    tenant.archived_at = None
    session.commit()
    return tenant


def permanently_delete_tenant(
    session: OrmSession,
    tenant_id: str,
    *,
    confirmation_name: str,
    confirmation_word: str,
) -> None:
    _require_business_mutation(session, tenant_id, "permanently_delete_tenant")
    tenant = get_tenant(session, tenant_id)
    if tenant.archived_at is None:
        raise InvalidOperation("Archive the tenant before permanently deleting it.")
    if confirmation_name != tenant.name or confirmation_word != "DELETE":
        raise InvalidOperation(
            "Tenant name and DELETE confirmation must match exactly."
        )
    _purge_tenant_records(session, tenant.id)
    session.delete(tenant)
    session.commit()


def _purge_tenant_records(session: OrmSession, tenant_id: str) -> None:
    """Delete every tenant-scoped row of one tenant, leaving the tenant itself.

    Private on purpose: the authority to reach it lives with the caller. The
    company danger zone (spec 186) guards it with owner membership and two
    confirmations; platform administration (spec 192) guards it with the
    platform-admin role and two confirmations of its own.
    """
    for table in reversed(Base.metadata.sorted_tables):
        if table.name == Tenant.__tablename__ or "tenant_id" not in table.c:
            continue
        session.execute(delete(table).where(table.c.tenant_id == tenant_id))


def _usage_sources() -> tuple[tuple[str | None, Any, Any], ...]:
    """What the usage summary counts, and where it reads a last-activity time.

    One entry per table — `(bucket, model, timestamp column)`, with `None` where a
    table only counts or only dates — because the whole summary is asked in one
    statement. The per-table form cost 37 round trips: about 11 ms on a company of
    200 orders and about 13 ms on one of 2,400, so the round trips were the cost and
    the scans were not (spec 181).
    """
    return (
        ("source_count", SourceRecord, SourceRecord.received_at),
        ("evidence_count", Document, None),
        ("reality_count", Commitment, Commitment.created_at),
        ("reality_count", Reservation, Reservation.reserved_at),
        ("reality_count", Movement, Movement.occurred_at),
        ("reality_count", LedgerEntry, LedgerEntry.effective_at),
        ("configured_count", SourceSystem, None),
        ("configured_count", Party, None),
        ("configured_count", Item, None),
        ("configured_count", Location, None),
        (None, ImportJob, ImportJob.created_at),
        (None, CommitmentHold, CommitmentHold.created_at),
        (None, PartyHold, PartyHold.created_at),
        (None, SettlementAllocation, SettlementAllocation.allocated_at),
        (None, Fact, Fact.observed_at),
        (None, ChangeProposal, ChangeProposal.created_at),
        (None, BusinessEvent, BusinessEvent.occurred_at),
        (None, ChatSession, ChatSession.updated_at),
        (None, ChatMessage, ChatMessage.created_at),
    )


def tenant_usage_summaries(
    session: OrmSession, *, tenant_id: str | None = None
) -> dict[str, dict[str, Any]]:
    """Return one cheap, grouped usage projection for every tenant.

    Every table is asked in the same statement. The figures are identical to the
    per-table form this replaces: a count of rows per tenant, and the latest of the
    timestamps the tables carry.
    """
    tenant_rows = (
        [get_tenant(session, tenant_id)]
        if tenant_id
        else tenants(session, include_archived=True)
    )
    summaries: dict[str, dict[str, Any]] = {
        tenant.id: {
            "state": "empty",
            "source_count": 0,
            "evidence_count": 0,
            "reality_count": 0,
            "configured_count": 0,
            "last_activity_at": None,
        }
        for tenant in tenant_rows
    }

    parts = []
    for index, (bucket, model, timestamp_column) in enumerate(_usage_sources()):
        parts.append(
            select(
                literal(index).label("source"),
                model.tenant_id.label("tenant_id"),
                func.count(model.id).label("total"),
                (
                    func.max(timestamp_column)
                    if timestamp_column is not None
                    else cast(null(), UTCDateTime)
                ).label("last_at"),
            )
            .where(model.tenant_id == tenant_id if tenant_id else True)
            .group_by(model.tenant_id)
        )
    buckets = [bucket for bucket, _, _ in _usage_sources()]
    for index, grouped_tenant_id, total, last_at in session.execute(union_all(*parts)):
        summary = summaries.get(grouped_tenant_id)
        if summary is None:
            # A tenant outside this call's scope, or archived away between reads.
            continue
        bucket = buckets[index]
        if bucket is not None:
            summary[bucket] += total
        current = summary["last_activity_at"]
        if last_at is not None and (current is None or last_at > current):
            summary["last_activity_at"] = last_at

    for summary in summaries.values():
        operational_count = (
            summary["source_count"]
            + summary["evidence_count"]
            + summary["reality_count"]
        )
        if operational_count:
            summary["state"] = "in_use"
        elif summary["configured_count"]:
            summary["state"] = "configured"
    return summaries


def payment_terms(
    session: OrmSession, tenant_id: str, *, include_inactive: bool = True
) -> list[PaymentTerm]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    query = select(PaymentTerm).where(PaymentTerm.tenant_id == tenant_id)
    if not include_inactive:
        query = query.where(PaymentTerm.is_active.is_(True))
    return list(session.scalars(query.order_by(PaymentTerm.code)))


def payment_term_by_code(
    session: OrmSession, tenant_id: str, code: str, *, active_only: bool = True
) -> PaymentTerm | None:
    code = code.strip().upper()
    if not code:
        return None
    query = select(PaymentTerm).where(
        PaymentTerm.tenant_id == tenant_id, PaymentTerm.code == code
    )
    if active_only:
        query = query.where(PaymentTerm.is_active.is_(True))
    term = session.scalar(query)
    if term is None:
        raise NotFound(f"Active payment term '{code}' not found.")
    return term


def _early_payment_discount(
    discount_percent: Decimal | float | str | None, discount_days: int | None
) -> tuple[Decimal | None, int | None]:
    """The two figures that make an early-payment discount, or neither.

    Half a discount condition is not a condition. A rate without a window says
    nothing about when it applies and a window without a rate says nothing about
    what it is worth, so either alone is refused rather than half-stored for a
    derivation to guess at.

    Null in both is the statement that this term grants no discount. A rate of
    zero would say "nothing off", which is a different thing, and a rate of a
    hundred or more is not a payment condition at all.
    """
    if discount_percent is None and discount_days is None:
        return None, None
    if discount_percent is None or discount_days is None:
        raise InvalidOperation(
            "A payment term discount needs both a rate and a number of days."
        )
    rate = decimal(discount_percent)
    if rate <= ZERO or rate >= Decimal(100):
        raise InvalidOperation(
            "Payment term discount percent must be above zero and below 100."
        )
    if discount_days < 0:
        raise InvalidOperation("Payment term discount days cannot be negative.")
    return rate, discount_days


def create_payment_term(
    session: OrmSession,
    tenant_id: str,
    code: str,
    name: str,
    due_days: int,
    *,
    source_system: str = "",
    external_id: str = "",
    source_payload: dict[str, Any] | None = None,
    discount_percent: Decimal | float | str | None = None,
    discount_days: int | None = None,
    requires_prepayment: bool = False,
    _commit: bool = True,
) -> PaymentTerm:
    _require_business_mutation(session, tenant_id, "create_payment_term")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    code, name = code.strip().upper(), name.strip()
    if not code or not name:
        raise InvalidOperation("Payment term code and name are required.")
    if due_days < 0:
        raise InvalidOperation("Payment term due days cannot be negative.")
    rate, window = _early_payment_discount(discount_percent, discount_days)
    if session.scalar(
        select(PaymentTerm.id).where(
            PaymentTerm.tenant_id == tenant_id, PaymentTerm.code == code
        )
    ):
        raise InvalidOperation(f"Payment term code '{code}' already exists.")
    source = create_master_source_record(
        session,
        tenant_id,
        "payment_term",
        source_system,
        external_id,
        (
            source_payload
            if source_payload is not None
            else {
                "code": code,
                "name": name,
                "due_days": due_days,
                "requires_prepayment": requires_prepayment,
            }
        ),
        _commit=False,
    )
    term = PaymentTerm(
        id=uid("ptm"),
        tenant_id=tenant_id,
        code=code,
        name=name,
        due_days=due_days,
        discount_percent=rate,
        discount_days=window,
        requires_prepayment=requires_prepayment,
        source_record_id=source.id if source else None,
    )
    session.add(term)
    emit_business_event(
        session,
        tenant_id,
        "payment_term.created",
        "payment_term",
        term.id,
        {
            "code": term.code,
            "due_days": term.due_days,
            "requires_prepayment": term.requires_prepayment,
        },
        source_record_id=term.source_record_id,
    )
    if _commit:
        session.commit()
    return term


def update_payment_term(
    session: OrmSession,
    tenant_id: str,
    payment_term_id: str,
    code: str,
    name: str,
    due_days: int,
    *,
    discount_percent: Decimal | float | str | None = None,
    discount_days: int | None = None,
    requires_prepayment: bool = False,
) -> PaymentTerm:
    _require_business_mutation(session, tenant_id, "update_payment_term")
    term = _tenant_record(session, PaymentTerm, tenant_id, payment_term_id)
    code, name = code.strip().upper(), name.strip()
    if not code or not name:
        raise InvalidOperation("Payment term code and name are required.")
    if due_days < 0:
        raise InvalidOperation("Payment term due days cannot be negative.")
    duplicate = session.scalar(
        select(PaymentTerm.id).where(
            PaymentTerm.tenant_id == tenant_id,
            PaymentTerm.code == code,
            PaymentTerm.id != payment_term_id,
        )
    )
    if duplicate:
        raise InvalidOperation(f"Payment term code '{code}' already exists.")
    rate, window = _early_payment_discount(discount_percent, discount_days)
    term.code, term.name, term.due_days = code, name, due_days
    term.discount_percent, term.discount_days = rate, window
    term.requires_prepayment = requires_prepayment
    emit_business_event(
        session,
        tenant_id,
        "payment_term.updated",
        "payment_term",
        term.id,
        {
            "code": code,
            "name": name,
            "due_days": due_days,
            "requires_prepayment": requires_prepayment,
        },
        source_record_id=term.source_record_id,
    )
    session.commit()
    return term


@dataclass(frozen=True)
class PriceResult:
    unit_price: Decimal
    currency: str
    unit: str
    price_list_id: str
    price_list_entry_id: str
    source: str
    assignment_id: str | None
    party_group_id: str | None
    evaluated_at: datetime


def price_lists(session: OrmSession, tenant_id: str) -> list[PriceList]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(PriceList)
            .where(PriceList.tenant_id == tenant_id)
            .order_by(PriceList.direction, PriceList.code)
        )
    )


def price_list_entries(session: OrmSession, tenant_id: str) -> list[PriceListEntry]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(PriceListEntry)
            .where(PriceListEntry.tenant_id == tenant_id)
            .order_by(
                PriceListEntry.price_list_id,
                PriceListEntry.item_id,
                PriceListEntry.min_quantity,
            )
        )
    )


def party_groups(session: OrmSession, tenant_id: str) -> list[PartyGroup]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(PartyGroup)
            .where(PartyGroup.tenant_id == tenant_id)
            .order_by(PartyGroup.code)
        )
    )


def create_price_list(
    session: OrmSession,
    tenant_id: str,
    code: str,
    name: str,
    direction: str,
    currency: str,
    *,
    valid_from: datetime | str | None = None,
    valid_until: datetime | str | None = None,
    is_default: bool = False,
    source_system: str = "",
    external_id: str = "",
    source_payload: dict[str, Any] | None = None,
) -> PriceList:
    _require_business_mutation(session, tenant_id, "create_price_list")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    code, name = code.strip().upper(), name.strip()
    direction, currency = direction.strip().lower(), currency.strip().upper()
    if not code or not name:
        raise InvalidOperation("Price-list code and name are required.")
    if direction not in {"sales", "purchase"}:
        raise InvalidOperation("Price-list direction must be sales or purchase.")
    if len(currency) != 3:
        raise InvalidOperation("Price-list currency must be a three-letter ISO code.")
    starts, ends = utc_datetime(valid_from), utc_datetime(valid_until)
    if starts and ends and ends <= starts:
        raise InvalidOperation("Price-list valid-until must be after valid-from.")
    if session.scalar(
        select(PriceList.id).where(
            PriceList.tenant_id == tenant_id, PriceList.code == code
        )
    ):
        raise InvalidOperation(f"Price-list code '{code}' already exists.")
    if is_default and session.scalar(
        select(PriceList.id).where(
            PriceList.tenant_id == tenant_id,
            PriceList.direction == direction,
            PriceList.currency == currency,
            PriceList.is_default.is_(True),
            PriceList.is_active.is_(True),
        )
    ):
        raise InvalidOperation(
            f"An active default {direction} price list for {currency} already exists."
        )
    source = create_master_source_record(
        session,
        tenant_id,
        "price_list",
        source_system,
        external_id,
        source_payload
        or {"code": code, "name": name, "direction": direction, "currency": currency},
    )
    result = PriceList(
        id=uid("prl"),
        tenant_id=tenant_id,
        code=code,
        name=name,
        direction=direction,
        currency=currency,
        valid_from=starts,
        valid_until=ends,
        is_default=is_default,
        source_record_id=source.id if source else None,
    )
    session.add(result)
    emit_business_event(
        session,
        tenant_id,
        "price_list.created",
        "price_list",
        result.id,
        {"code": result.code, "direction": direction, "currency": currency},
        source_record_id=result.source_record_id,
    )
    session.commit()
    return result


def update_price_list(
    session: OrmSession,
    tenant_id: str,
    price_list_id: str,
    code: str,
    name: str,
    direction: str,
    currency: str,
    *,
    is_default: bool = False,
) -> PriceList:
    _require_business_mutation(session, tenant_id, "update_price_list")
    result = _tenant_record(session, PriceList, tenant_id, price_list_id)
    code, name = code.strip().upper(), name.strip()
    direction, currency = direction.strip().lower(), currency.strip().upper()
    if not code or not name:
        raise InvalidOperation("Price-list code and name are required.")
    if direction not in {"sales", "purchase"}:
        raise InvalidOperation("Price-list direction must be sales or purchase.")
    if len(currency) != 3:
        raise InvalidOperation("Price-list currency must be a three-letter ISO code.")
    duplicate = session.scalar(
        select(PriceList.id).where(
            PriceList.tenant_id == tenant_id,
            PriceList.code == code,
            PriceList.id != price_list_id,
        )
    )
    if duplicate:
        raise InvalidOperation(f"Price-list code '{code}' already exists.")
    if is_default:
        other_default = session.scalar(
            select(PriceList.id).where(
                PriceList.tenant_id == tenant_id,
                PriceList.direction == direction,
                PriceList.currency == currency,
                PriceList.is_default.is_(True),
                PriceList.is_active.is_(True),
                PriceList.id != price_list_id,
            )
        )
        if other_default:
            raise InvalidOperation(
                f"An active default {direction} price list for {currency} already exists."
            )
    result.code, result.name = code, name
    result.direction, result.currency, result.is_default = (
        direction,
        currency,
        is_default,
    )
    emit_business_event(
        session,
        tenant_id,
        "price_list.updated",
        "price_list",
        result.id,
        {
            "code": code,
            "name": name,
            "direction": direction,
            "currency": currency,
            "is_default": is_default,
        },
        source_record_id=result.source_record_id,
    )
    session.commit()
    return result


def create_price_list_entry(
    session: OrmSession,
    tenant_id: str,
    price_list_id: str,
    item_id: str,
    min_quantity: Decimal | float | str,
    unit_price: Decimal | float | str,
    unit: str,
    *,
    valid_from: datetime | str | None = None,
    valid_until: datetime | str | None = None,
) -> PriceListEntry:
    _require_business_mutation(session, tenant_id, "create_price_list_entry")
    _tenant_record(session, PriceList, tenant_id, price_list_id)
    _tenant_record(session, Item, tenant_id, item_id)
    minimum = positive(min_quantity, "minimum quantity")
    price = decimal(unit_price)
    if price < ZERO:
        raise InvalidOperation("Unit price cannot be negative.")
    unit = unit.strip()
    if not unit:
        raise InvalidOperation("Price unit is required.")
    starts, ends = utc_datetime(valid_from), utc_datetime(valid_until)
    if starts and ends and ends <= starts:
        raise InvalidOperation("Entry valid-until must be after valid-from.")
    if session.scalar(
        select(PriceListEntry.id).where(
            PriceListEntry.tenant_id == tenant_id,
            PriceListEntry.price_list_id == price_list_id,
            PriceListEntry.item_id == item_id,
            PriceListEntry.min_quantity == minimum,
        )
    ):
        raise InvalidOperation("This price tier already exists.")
    entry = PriceListEntry(
        id=uid("pre"),
        tenant_id=tenant_id,
        price_list_id=price_list_id,
        item_id=item_id,
        min_quantity=minimum,
        unit_price=price,
        unit=unit,
        valid_from=starts,
        valid_until=ends,
    )
    session.add(entry)
    emit_business_event(
        session,
        tenant_id,
        "price_list_entry.created",
        "price_list_entry",
        entry.id,
        {
            "price_list_id": price_list_id,
            "item_id": item_id,
            "min_quantity": minimum,
            "unit_price": price,
            "unit": unit,
        },
    )
    session.commit()
    return entry


def assign_party_price_list(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    price_list_id: str,
    priority: int = 100,
) -> PartyPriceList:
    _require_business_mutation(session, tenant_id, "assign_party_price_list")
    _tenant_record(session, Party, tenant_id, party_id)
    _tenant_record(session, PriceList, tenant_id, price_list_id)
    assignment = PartyPriceList(
        id=uid("ppl"),
        tenant_id=tenant_id,
        party_id=party_id,
        price_list_id=price_list_id,
        priority=priority,
    )
    session.add(assignment)
    emit_business_event(
        session,
        tenant_id,
        "party_price_list.assigned",
        "party_price_list",
        assignment.id,
        {"party_id": party_id, "price_list_id": price_list_id, "priority": priority},
    )
    session.commit()
    return assignment


def create_party_group(
    session: OrmSession, tenant_id: str, code: str, name: str
) -> PartyGroup:
    _require_business_mutation(session, tenant_id, "create_party_group")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    code, name = code.strip().upper(), name.strip()
    if not code or not name:
        raise InvalidOperation("Party-group code and name are required.")
    if session.scalar(
        select(PartyGroup.id).where(
            PartyGroup.tenant_id == tenant_id, PartyGroup.code == code
        )
    ):
        raise InvalidOperation(f"Party-group code '{code}' already exists.")
    group = PartyGroup(id=uid("pgr"), tenant_id=tenant_id, code=code, name=name)
    session.add(group)
    emit_business_event(
        session,
        tenant_id,
        "party_group.created",
        "party_group",
        group.id,
        {"code": group.code, "name": group.name},
    )
    session.commit()
    return group


def update_party_group(
    session: OrmSession, tenant_id: str, party_group_id: str, code: str, name: str
) -> PartyGroup:
    _require_business_mutation(session, tenant_id, "update_party_group")
    group = _tenant_record(session, PartyGroup, tenant_id, party_group_id)
    code, name = code.strip().upper(), name.strip()
    if not code or not name:
        raise InvalidOperation("Party-group code and name are required.")
    duplicate = session.scalar(
        select(PartyGroup.id).where(
            PartyGroup.tenant_id == tenant_id,
            PartyGroup.code == code,
            PartyGroup.id != party_group_id,
        )
    )
    if duplicate:
        raise InvalidOperation(f"Party-group code '{code}' already exists.")
    group.code, group.name = code, name
    emit_business_event(
        session,
        tenant_id,
        "party_group.updated",
        "party_group",
        group.id,
        {"code": code, "name": name},
        source_record_id=group.source_record_id,
    )
    session.commit()
    return group


def add_party_group_member(
    session: OrmSession, tenant_id: str, party_group_id: str, party_id: str
) -> PartyGroupMember:
    _require_business_mutation(session, tenant_id, "add_party_group_member")
    group = _tenant_record(session, PartyGroup, tenant_id, party_group_id)
    if not group.is_active:
        raise InvalidOperation("Cannot add members to an inactive party group.")
    _tenant_record(session, Party, tenant_id, party_id)
    member = PartyGroupMember(
        id=uid("pgm"),
        tenant_id=tenant_id,
        party_group_id=party_group_id,
        party_id=party_id,
    )
    session.add(member)
    emit_business_event(
        session,
        tenant_id,
        "party_group_member.added",
        "party_group_member",
        member.id,
        {"party_group_id": party_group_id, "party_id": party_id},
    )
    session.commit()
    return member


def assign_group_price_list(
    session: OrmSession,
    tenant_id: str,
    party_group_id: str,
    price_list_id: str,
    priority: int = 100,
) -> PartyGroupPriceList:
    _require_business_mutation(session, tenant_id, "assign_group_price_list")
    _tenant_record(session, PartyGroup, tenant_id, party_group_id)
    _tenant_record(session, PriceList, tenant_id, price_list_id)
    assignment = PartyGroupPriceList(
        id=uid("gpl"),
        tenant_id=tenant_id,
        party_group_id=party_group_id,
        price_list_id=price_list_id,
        priority=priority,
    )
    session.add(assignment)
    emit_business_event(
        session,
        tenant_id,
        "party_group_price_list.assigned",
        "party_group_price_list",
        assignment.id,
        {
            "party_group_id": party_group_id,
            "price_list_id": price_list_id,
            "priority": priority,
        },
    )
    session.commit()
    return assignment


def resolve_price(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    item_id: str,
    quantity: Decimal | float | str,
    direction: str,
    currency: str,
    unit: str,
    *,
    at: datetime | str | None = None,
) -> PriceResult | None:
    _tenant_record(session, Party, tenant_id, party_id)
    _tenant_record(session, Item, tenant_id, item_id)
    requested_quantity = positive(quantity)
    moment = utc_datetime(at) or now()
    direction, currency = direction.lower(), currency.upper()

    def valid(record: Any) -> bool:
        return (record.valid_from is None or record.valid_from <= moment) and (
            record.valid_until is None or record.valid_until > moment
        )

    direct = list(
        session.scalars(
            select(PartyPriceList)
            .where(
                PartyPriceList.tenant_id == tenant_id,
                PartyPriceList.party_id == party_id,
            )
            .order_by(PartyPriceList.priority)
        )
    )
    group_links = list(
        session.execute(
            select(PartyGroupPriceList, PartyGroupMember)
            .join(
                PartyGroupMember,
                PartyGroupMember.party_group_id == PartyGroupPriceList.party_group_id,
            )
            .join(PartyGroup, PartyGroup.id == PartyGroupPriceList.party_group_id)
            .where(
                PartyGroupPriceList.tenant_id == tenant_id,
                PartyGroupMember.tenant_id == tenant_id,
                PartyGroupMember.party_id == party_id,
                PartyGroup.is_active.is_(True),
            )
            .order_by(PartyGroupPriceList.priority)
        )
    )
    candidates = [
        (link.price_list_id, "party", link.id, None) for link in direct if valid(link)
    ] + [
        (link.price_list_id, "group", link.id, link.party_group_id)
        for link, membership in group_links
        if valid(link) and valid(membership)
    ]
    defaults = list(
        session.scalars(
            select(PriceList).where(
                PriceList.tenant_id == tenant_id,
                PriceList.direction == direction,
                PriceList.currency == currency,
                PriceList.is_default.is_(True),
                PriceList.is_active.is_(True),
            )
        )
    )
    candidates.extend((price_list.id, "default", None, None) for price_list in defaults)
    for price_list_id, source, assignment_id, party_group_id in candidates:
        price_list = _tenant_record(session, PriceList, tenant_id, price_list_id)
        if (
            not price_list.is_active
            or price_list.direction != direction
            or price_list.currency != currency
            or not valid(price_list)
        ):
            continue
        entries = list(
            session.scalars(
                select(PriceListEntry)
                .where(
                    PriceListEntry.tenant_id == tenant_id,
                    PriceListEntry.price_list_id == price_list.id,
                    PriceListEntry.item_id == item_id,
                    PriceListEntry.unit == unit,
                    PriceListEntry.min_quantity <= requested_quantity,
                )
                .order_by(PriceListEntry.min_quantity.desc())
            )
        )
        entry = next((candidate for candidate in entries if valid(candidate)), None)
        if entry:
            return PriceResult(
                entry.unit_price,
                price_list.currency,
                entry.unit,
                price_list.id,
                entry.id,
                source,
                assignment_id,
                party_group_id,
                moment,
            )
    return None


def create_master_source_record(
    session: OrmSession,
    tenant_id: str,
    source_type: str,
    source_system: str,
    external_id: str,
    payload: dict[str, Any],
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> SourceRecord | None:
    _require_business_mutation(session, tenant_id, "create_master_source_record")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    source_system, external_id = source_system.strip(), external_id.strip()
    if bool(source_system) != bool(external_id):
        raise InvalidOperation(
            "Source system and external ID must be provided together."
        )
    if not source_system:
        return None
    source, created, _ = store_source_record(
        session,
        tenant_id,
        source_system,
        source_type,
        external_id,
        payload,
    )
    if created and action_id:
        emit_business_event(
            session,
            tenant_id,
            "source_record.stored",
            "source_record",
            source.id,
            {"source_type": source_type, "origin": source_system},
            source_record_id=source.id,
            action_id=action_id,
            correlation_id=action_id,
        )
    if _commit:
        # The submitted source truth is durable before its interpretation.
        session.commit()
    return source


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _lock_source_identity(
    session: OrmSession,
    tenant_id: str,
    source_system: str,
    source_type: str,
    external_id: str,
) -> None:
    if session.get_bind().dialect.name != "postgresql":
        return
    identity = f"{tenant_id}\x1f{source_system}\x1f{source_type}\x1f{external_id}"
    lock_key = int.from_bytes(
        hashlib.sha256(identity.encode()).digest()[:8], "big", signed=True
    )
    session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key}
    )


def store_source_record(
    session: OrmSession,
    tenant_id: str,
    source_system: str,
    source_type: str,
    external_id: str,
    payload: dict[str, Any],
    *,
    source_version_at: datetime | None = None,
    source_artifact_id: str | None = None,
) -> tuple[SourceRecord, bool, str]:
    """Return an immutable source version and whether it was newly inserted."""
    _require_business_mutation(session, tenant_id, "store_source_record")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    _lock_source_identity(session, tenant_id, source_system, source_type, external_id)
    payload_hash = canonical_payload_hash(payload)
    identity = (
        SourceRecord.tenant_id == tenant_id,
        SourceRecord.source_system == source_system,
        SourceRecord.source_type == source_type,
        SourceRecord.external_id == external_id,
    )
    stream = session.scalar(
        select(SourceStream)
        .where(
            SourceStream.tenant_id == tenant_id,
            SourceStream.source_system == source_system,
            SourceStream.source_type == source_type,
            SourceStream.external_id == external_id,
        )
        .with_for_update()
    )
    if stream is None:
        stream = SourceStream(
            id=uid("sst"),
            tenant_id=tenant_id,
            source_system=source_system,
            source_type=source_type,
            external_id=external_id,
        )
        session.add(stream)
        session.flush()
    existing = session.scalar(
        select(SourceRecord).where(*identity, SourceRecord.payload_hash == payload_hash)
    )
    if existing:
        return existing, False, "duplicate"

    latest = session.scalar(
        select(SourceRecord)
        .where(*identity)
        .order_by(SourceRecord.version.desc())
        .limit(1)
    )
    current = (
        _tenant_record(
            session, SourceRecord, tenant_id, stream.current_source_record_id
        )
        if stream.current_source_record_id
        else None
    )
    disposition = "current"
    supersedes_id = current.id if current else None
    if current and source_version_at and current.source_version_at:
        if source_version_at < current.source_version_at:
            disposition, supersedes_id = "stale", None
        elif source_version_at == current.source_version_at:
            disposition, supersedes_id = "conflict", None

    source = SourceRecord(
        id=uid("src"),
        tenant_id=tenant_id,
        source_system=source_system,
        source_type=source_type,
        external_id=external_id,
        payload=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        payload_hash=payload_hash,
        source_artifact_id=source_artifact_id,
        version=(latest.version + 1) if latest else 1,
        source_version_at=source_version_at,
        supersedes_source_record_id=supersedes_id,
    )
    session.add(source)
    session.flush()
    if disposition == "current":
        stream.current_source_record_id = source.id
    return source, True, disposition


def update_master_source_reference(
    session: OrmSession,
    tenant_id: str,
    current_source_id: str | None,
    source_type: str,
    source_system: str | None,
    external_id: str | None,
    payload: dict[str, Any],
    *,
    payload_was_provided: bool = False,
) -> SourceRecord | None:
    _require_business_mutation(session, tenant_id, "update_master_source_reference")
    current = (
        _tenant_record(session, SourceRecord, tenant_id, current_source_id)
        if current_source_id
        else None
    )
    if source_system is None and external_id is None:
        return current
    source_system = (source_system or "").strip()
    external_id = (external_id or "").strip()
    if (
        current
        and current.source_system == source_system
        and current.external_id == external_id
        and (
            not payload_was_provided
            or current.payload_hash == canonical_payload_hash(payload)
        )
    ):
        return current
    return create_master_source_record(
        session, tenant_id, source_type, source_system, external_id, payload
    )


def create_party(
    session: OrmSession,
    tenant_id: str,
    name: str,
    party_type: str,
    *,
    action_id: str | None = None,
    source_system: str = "",
    external_id: str = "",
    source_payload: dict[str, Any] | None = None,
    roles: list[str] | None = None,
    accounting_code: str = "",
    payment_term_code: str = "",
    default_currency: str = "EUR",
    credit_limit: Decimal | float | str = ZERO,
    tax_identifier: str = "",
    emails: list[dict[str, Any]] | None = None,
    source_record_id: str | None = None,
    _commit: bool = True,
) -> Party:
    _require_business_mutation(session, tenant_id, "create_party")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    name = name.strip()
    if not name:
        raise InvalidOperation("Party name is required.")
    selected_roles = list(dict.fromkeys(roles or [party_type]))
    if not selected_roles or any(
        role not in {"company", "customer", "supplier"} for role in selected_roles
    ):
        raise InvalidOperation("Party roles must be company, customer, or supplier.")
    source = (
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
        if source_record_id
        else create_master_source_record(
            session,
            tenant_id,
            "party",
            source_system,
            external_id,
            source_payload
            or {"name": name, "type": party_type, "emails": emails or []},
            _commit=_commit,
            action_id=action_id,
        )
    )
    party = Party(
        id=uid("pty"),
        tenant_id=tenant_id,
        name=name,
        type=party_type,
        source_record_id=source.id if source else None,
        accounting_code=accounting_code.strip(),
        payment_term_id=(
            payment_term_by_code(session, tenant_id, payment_term_code).id
            if payment_term_code.strip()
            else None
        ),
        default_currency=default_currency.strip().upper() or "EUR",
        credit_limit=decimal(credit_limit),
        tax_identifier=tax_identifier.strip(),
    )
    if party.credit_limit < ZERO:
        raise InvalidOperation("Credit limit cannot be negative.")
    session.add(party)
    session.flush()
    session.add_all(
        PartyRole(id=uid("pro"), tenant_id=tenant_id, party_id=party.id, role=role)
        for role in selected_roles
    )
    if emails:
        _replace_party_emails(session, tenant_id, party.id, emails)
    emit_business_event(
        session,
        tenant_id,
        "party.created",
        "party",
        party.id,
        {"name": party.name, "roles": selected_roles},
        source_record_id=party.source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return party


def create_item(
    session: OrmSession,
    tenant_id: str,
    sku: str,
    name: str,
    unit: str = "pcs",
    *,
    action_id: str | None = None,
    source_system: str = "",
    external_id: str = "",
    source_payload: dict[str, Any] | None = None,
    item_type: str = "stocked",
    tracking_type: str = "none",
    default_location_id: str | None = None,
    purchase_unit: str | None = None,
    conversion_factor: Decimal | float | str = 1,
    lead_time_days: int = 0,
    source_record_id: str | None = None,
    _commit: bool = True,
) -> Item:
    _require_business_mutation(session, tenant_id, "create_item")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    sku, name, unit = sku.strip(), name.strip(), unit.strip()
    if not sku or not name or not unit:
        raise InvalidOperation("Item SKU, name, and unit are required.")
    if item_type not in {"stocked", "service", "charge"}:
        raise InvalidOperation("Item type must be stocked, service, or charge.")
    if tracking_type not in {"none", "lot", "serial"}:
        raise InvalidOperation("Tracking type must be none, lot, or serial.")
    if default_location_id:
        _tenant_record(session, Location, tenant_id, default_location_id)
    factor = positive(conversion_factor, "conversion factor")
    if lead_time_days < 0:
        raise InvalidOperation("Lead time days cannot be negative.")
    source = (
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
        if source_record_id
        else create_master_source_record(
            session,
            tenant_id,
            "item",
            source_system,
            external_id,
            source_payload or {"sku": sku, "name": name, "unit": unit},
            _commit=False,
            action_id=action_id,
        )
    )
    item = Item(
        id=uid("itm"),
        tenant_id=tenant_id,
        sku=sku,
        name=name,
        unit=unit,
        source_record_id=source.id if source else None,
        item_type=item_type,
        tracking_type=tracking_type,
        default_location_id=default_location_id,
        purchase_unit=(purchase_unit or unit).strip(),
        conversion_factor=factor,
        lead_time_days=lead_time_days,
    )
    session.add(item)
    emit_business_event(
        session,
        tenant_id,
        "item.created",
        "item",
        item.id,
        {"sku": item.sku, "unit": item.unit},
        source_record_id=item.source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return item


def create_location(
    session: OrmSession,
    tenant_id: str,
    name: str,
    location_type: str = "warehouse",
    *,
    action_id: str | None = None,
    parent_location_id: str | None = None,
    allows_stock: bool = True,
    source_system: str = "",
    external_id: str = "",
    source_payload: dict[str, Any] | None = None,
    source_record_id: str | None = None,
    _commit: bool = True,
) -> Location:
    _require_business_mutation(session, tenant_id, "create_location")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    name, location_type = name.strip(), location_type.strip()
    if not name or not location_type:
        raise InvalidOperation("Location name and type are required.")
    if parent_location_id:
        _tenant_record(session, Location, tenant_id, parent_location_id)
    source = (
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
        if source_record_id
        else create_master_source_record(
            session,
            tenant_id,
            "location",
            source_system,
            external_id,
            source_payload or {"name": name, "type": location_type},
            _commit=_commit,
            action_id=action_id,
        )
    )
    location = Location(
        id=uid("loc"),
        tenant_id=tenant_id,
        name=name,
        type=location_type,
        parent_location_id=parent_location_id,
        allows_stock=allows_stock,
        source_record_id=source.id if source else None,
    )
    session.add(location)
    emit_business_event(
        session,
        tenant_id,
        "location.created",
        "location",
        location.id,
        {"name": location.name, "type": location.type},
        source_record_id=location.source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return location


def create_parties(
    session: OrmSession,
    tenant_id: str,
    records: list[dict[str, Any]],
    *,
    action_id: str | None = None,
) -> list[Party]:
    _require_business_mutation(session, tenant_id, "create_parties")
    from reality.services.tenant_policy import require_master_call

    require_master_call(session, tenant_id, "party_create", records, action_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    if not records:
        raise InvalidOperation("At least one Party is required.")
    created: list[Party] = []
    try:
        for record in records:
            roles = list(record["roles"])
            created.append(
                create_party(
                    session,
                    tenant_id,
                    record["name"],
                    record.get("type") or (roles[0] if roles else ""),
                    source_system=record.get("source_system") or "",
                    external_id=record.get("external_id") or "",
                    source_payload=record.get("source_payload"),
                    roles=roles,
                    accounting_code=record.get("accounting_code", ""),
                    payment_term_code=record.get("payment_term_code", ""),
                    default_currency=record.get("default_currency", "EUR"),
                    credit_limit=record.get("credit_limit", "0"),
                    tax_identifier=record.get("tax_identifier", ""),
                    emails=record.get("emails", []),
                    _commit=False,
                    action_id=action_id,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return created


def create_items(
    session: OrmSession,
    tenant_id: str,
    records: list[dict[str, Any]],
    *,
    action_id: str | None = None,
) -> list[Item]:
    _require_business_mutation(session, tenant_id, "create_items")
    from reality.services.tenant_policy import require_master_call

    require_master_call(session, tenant_id, "item_create", records, action_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    if not records:
        raise InvalidOperation("At least one Item is required.")
    created: list[Item] = []
    try:
        for record in records:
            created.append(
                create_item(
                    session,
                    tenant_id,
                    record["sku"],
                    record["name"],
                    record.get("unit", "pcs"),
                    source_system=record.get("source_system") or "",
                    external_id=record.get("external_id") or "",
                    source_payload=record.get("source_payload"),
                    item_type=record.get("item_type", "stocked"),
                    tracking_type=record.get("tracking_type", "none"),
                    default_location_id=record.get("default_location_id"),
                    purchase_unit=record.get("purchase_unit"),
                    conversion_factor=record.get("conversion_factor", "1"),
                    lead_time_days=record.get("lead_time_days", 0),
                    _commit=False,
                    action_id=action_id,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return created


def create_locations(
    session: OrmSession,
    tenant_id: str,
    records: list[dict[str, Any]],
    *,
    action_id: str | None = None,
) -> list[Location]:
    _require_business_mutation(session, tenant_id, "create_locations")
    from reality.services.tenant_policy import require_master_call

    require_master_call(session, tenant_id, "location_create", records, action_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    if not records:
        raise InvalidOperation("At least one Location is required.")
    created: list[Location] = []
    local_references: dict[str, str] = {}
    try:
        for record in records:
            reference = str(record.get("ref") or "").strip()
            parent_reference = str(record.get("parent_ref") or "").strip()
            parent_location_id = record.get("parent_location_id")
            if reference and reference in local_references:
                raise InvalidOperation(
                    f"Duplicate Location batch reference: {reference}"
                )
            if parent_reference and parent_location_id:
                raise InvalidOperation(
                    "Use either parent_ref for this batch or parent_location_id for an existing Location."
                )
            if parent_reference:
                parent_location_id = local_references.get(parent_reference)
                if parent_location_id is None:
                    raise InvalidOperation(
                        f"Location parent_ref must reference an earlier record in the same batch: {parent_reference}"
                    )
            location = create_location(
                session,
                tenant_id,
                record["name"],
                record.get("type", "warehouse"),
                parent_location_id=parent_location_id,
                allows_stock=record.get("allows_stock", True),
                source_system=record.get("source_system") or "",
                external_id=record.get("external_id") or "",
                source_payload=record.get("source_payload"),
                _commit=False,
                action_id=action_id,
            )
            created.append(location)
            if reference:
                local_references[reference] = location.id
        session.commit()
    except Exception:
        session.rollback()
        raise
    return created


def _decimal_audit_value(value: Decimal | float | str) -> str:
    normalized = decimal(value).normalize()
    return "0" if normalized == ZERO else format(normalized, "f")


def _field_changes(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    return {
        field: {"before": before[field], "after": after[field]}
        for field in before
        if before[field] != after[field]
    }


def _party_update_snapshot(
    session: OrmSession, tenant_id: str, party: Party
) -> dict[str, Any]:
    roles = sorted(
        session.scalars(
            select(PartyRole.role).where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == party.id,
            )
        ).all()
    )
    return {
        "name": party.name,
        "type": party.type,
        "roles": roles,
        "accounting_code": party.accounting_code,
        "payment_term_id": party.payment_term_id,
        "default_currency": party.default_currency,
        "credit_limit": _decimal_audit_value(party.credit_limit),
        "tax_identifier": party.tax_identifier,
        "source_record_id": party.source_record_id,
        "emails": [
            {"email": row.email, "label": row.label}
            for row in session.scalars(
                select(PartyEmailAddress)
                .where(
                    PartyEmailAddress.tenant_id == tenant_id,
                    PartyEmailAddress.party_id == party.id,
                )
                .order_by(PartyEmailAddress.normalized_email, PartyEmailAddress.id)
            )
        ],
    }


def _item_update_snapshot(item: Item) -> dict[str, Any]:
    return {
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "item_type": item.item_type,
        "tracking_type": item.tracking_type,
        "default_location_id": item.default_location_id,
        "purchase_unit": item.purchase_unit,
        "conversion_factor": _decimal_audit_value(item.conversion_factor),
        "lead_time_days": item.lead_time_days,
        "source_record_id": item.source_record_id,
    }


def _location_update_snapshot(location: Location) -> dict[str, Any]:
    return {
        "name": location.name,
        "type": location.type,
        "parent_location_id": location.parent_location_id,
        "allows_stock": location.allows_stock,
        "source_record_id": location.source_record_id,
    }


def _snapshot_revision(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def master_data_update_snapshot(
    session: OrmSession, tenant_id: str, family: str, record_id: str
) -> dict[str, Any]:
    if family == "party":
        party = _tenant_record(session, Party, tenant_id, record_id)
        return _party_update_snapshot(session, tenant_id, party)
    if family == "item":
        return _item_update_snapshot(
            _tenant_record(session, Item, tenant_id, record_id)
        )
    if family == "location":
        return _location_update_snapshot(
            _tenant_record(session, Location, tenant_id, record_id)
        )
    raise InvalidOperation("Unsupported master data family.")


def preview_master_data_updates(
    session: OrmSession, tenant_id: str, family: str, records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not records:
        raise InvalidOperation("At least one update record is required.")
    seen: set[str] = set()
    preview: list[dict[str, Any]] = []
    for record in records:
        record_id = str(record.get("id") or "")
        if not record_id:
            raise InvalidOperation("Update records require an opaque ID.")
        if record_id in seen:
            raise InvalidOperation(f"Duplicate update target: {record_id}")
        seen.add(record_id)
        before = master_data_update_snapshot(session, tenant_id, family, record_id)
        after = dict(before)
        if family == "party":
            after.update(
                {
                    "name": str(record["name"]).strip(),
                    "type": str(record["type"]),
                    "roles": sorted(set(record["roles"])),
                }
            )
            if "accounting_code" in record:
                after["accounting_code"] = str(record["accounting_code"]).strip()
            if "payment_term_code" in record:
                code = str(record["payment_term_code"]).strip()
                after["payment_term_id"] = (
                    payment_term_by_code(session, tenant_id, code).id if code else None
                )
            if "default_currency" in record:
                after["default_currency"] = (
                    str(record["default_currency"]).strip().upper() or "EUR"
                )
            if "credit_limit" in record:
                after["credit_limit"] = _decimal_audit_value(record["credit_limit"])
            if "tax_identifier" in record:
                after["tax_identifier"] = str(record["tax_identifier"]).strip()
            if "emails" in record:
                after["emails"] = [
                    {"email": item["email"], "label": item["label"]}
                    for item in _party_email_values(record["emails"])
                ]
        elif family == "item":
            after.update(
                {
                    "sku": str(record["sku"]).strip(),
                    "name": str(record["name"]).strip(),
                    "unit": str(record["unit"]).strip(),
                }
            )
            for field in ("item_type", "tracking_type"):
                if field in record:
                    after[field] = record[field]
            if record.get("default_location_id"):
                after["default_location_id"] = record["default_location_id"]
            if record.get("purchase_unit") is not None:
                after["purchase_unit"] = (
                    str(record["purchase_unit"] or "").strip() or after["unit"]
                )
            if "conversion_factor" in record:
                after["conversion_factor"] = _decimal_audit_value(
                    record["conversion_factor"]
                )
            if "lead_time_days" in record:
                after["lead_time_days"] = record["lead_time_days"]
        else:
            after.update(
                {
                    "name": str(record["name"]).strip(),
                    "type": str(record["type"]).strip(),
                }
            )
            for field in ("parent_location_id", "allows_stock"):
                if field in record:
                    after[field] = record[field]
        preview.append(
            {
                "id": record_id,
                "expected_revision": _snapshot_revision(before),
                "changes": _field_changes(before, after),
            }
        )
    return preview


def update_party(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    name: str,
    party_type: str,
    *,
    source_system: str | None = None,
    external_id: str | None = None,
    source_payload: dict[str, Any] | None = None,
    roles: list[str] | None = None,
    accounting_code: str | None = None,
    payment_term_code: str | None = None,
    default_currency: str | None = None,
    credit_limit: Decimal | float | str | None = None,
    tax_identifier: str | None = None,
    emails: list[dict[str, Any]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Party:
    _require_business_mutation(session, tenant_id, "update_party")
    party = _tenant_record(session, Party, tenant_id, party_id)
    before = _party_update_snapshot(session, tenant_id, party)
    name = name.strip()
    if not name:
        raise InvalidOperation("Party name is required.")
    selected_roles = list(dict.fromkeys(roles or [party_type]))
    if not selected_roles or any(
        role not in {"company", "customer", "supplier"} for role in selected_roles
    ):
        raise InvalidOperation("Party roles must be company, customer, or supplier.")
    source = update_master_source_reference(
        session,
        tenant_id,
        party.source_record_id,
        "party",
        source_system,
        external_id,
        source_payload
        or {
            "name": name,
            "type": party_type,
            "emails": emails if emails is not None else before["emails"],
        },
        payload_was_provided=source_payload is not None,
    )
    party.name, party.type = name, party_type
    party.source_record_id = source.id if source else None
    existing_roles = {
        role.role: role
        for role in session.scalars(
            select(PartyRole).where(
                PartyRole.tenant_id == tenant_id, PartyRole.party_id == party.id
            )
        )
    }
    for role_name, role in existing_roles.items():
        if role_name not in selected_roles:
            session.delete(role)
    for role_name in selected_roles:
        if role_name not in existing_roles:
            session.add(
                PartyRole(
                    id=uid("pro"),
                    tenant_id=tenant_id,
                    party_id=party.id,
                    role=role_name,
                )
            )
    if accounting_code is not None:
        party.accounting_code = accounting_code.strip()
    if payment_term_code is not None:
        party.payment_term_id = (
            payment_term_by_code(session, tenant_id, payment_term_code).id
            if payment_term_code.strip()
            else None
        )
    if default_currency is not None:
        party.default_currency = default_currency.strip().upper() or "EUR"
    if credit_limit is not None:
        party.credit_limit = decimal(credit_limit)
        if party.credit_limit < ZERO:
            raise InvalidOperation("Credit limit cannot be negative.")
    if tax_identifier is not None:
        party.tax_identifier = tax_identifier.strip()
    if emails is not None:
        _replace_party_emails(session, tenant_id, party.id, emails)
    session.flush()
    changes = _field_changes(before, _party_update_snapshot(session, tenant_id, party))
    if changes:
        emit_business_event(
            session,
            tenant_id,
            "party.updated",
            "party",
            party.id,
            {"name": party.name, "roles": selected_roles, "changes": changes},
            source_record_id=party.source_record_id,
            action_id=action_id,
        )
    if _commit:
        session.commit()
    return party


def update_item(
    session: OrmSession,
    tenant_id: str,
    item_id: str,
    sku: str,
    name: str,
    unit: str,
    *,
    source_system: str | None = None,
    external_id: str | None = None,
    source_payload: dict[str, Any] | None = None,
    item_type: str | None = None,
    tracking_type: str | None = None,
    default_location_id: str | None = None,
    purchase_unit: str | None = None,
    conversion_factor: Decimal | float | str | None = None,
    lead_time_days: int | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Item:
    _require_business_mutation(session, tenant_id, "update_item")
    item = _tenant_record(session, Item, tenant_id, item_id)
    before = _item_update_snapshot(item)
    sku, name, unit = sku.strip(), name.strip(), unit.strip()
    if not sku or not name or not unit:
        raise InvalidOperation("Item SKU, name, and unit are required.")
    source = update_master_source_reference(
        session,
        tenant_id,
        item.source_record_id,
        "item",
        source_system,
        external_id,
        source_payload or {"sku": sku, "name": name, "unit": unit},
        payload_was_provided=source_payload is not None,
    )
    item.sku, item.name, item.unit = sku, name, unit
    item.source_record_id = source.id if source else None
    if item_type is not None:
        if item_type not in {"stocked", "service", "charge"}:
            raise InvalidOperation("Item type must be stocked, service, or charge.")
        item.item_type = item_type
    if tracking_type is not None:
        if tracking_type not in {"none", "lot", "serial"}:
            raise InvalidOperation("Tracking type must be none, lot, or serial.")
        item.tracking_type = tracking_type
    if default_location_id:
        _tenant_record(session, Location, tenant_id, default_location_id)
        item.default_location_id = default_location_id
    if purchase_unit is not None:
        item.purchase_unit = purchase_unit.strip() or unit
    if conversion_factor is not None:
        item.conversion_factor = positive(conversion_factor, "conversion factor")
    if lead_time_days is not None:
        if lead_time_days < 0:
            raise InvalidOperation("Lead time days cannot be negative.")
        item.lead_time_days = lead_time_days
    changes = _field_changes(before, _item_update_snapshot(item))
    if changes:
        emit_business_event(
            session,
            tenant_id,
            "item.updated",
            "item",
            item.id,
            {"sku": item.sku, "unit": item.unit, "changes": changes},
            source_record_id=item.source_record_id,
            action_id=action_id,
        )
    if _commit:
        session.commit()
    return item


def update_location(
    session: OrmSession,
    tenant_id: str,
    location_id: str,
    name: str,
    location_type: str,
    *,
    parent_location_id: str | None = None,
    allows_stock: bool | None = None,
    source_system: str | None = None,
    external_id: str | None = None,
    source_payload: dict[str, Any] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Location:
    _require_business_mutation(session, tenant_id, "update_location")
    location = _tenant_record(session, Location, tenant_id, location_id)
    before = _location_update_snapshot(location)
    name, location_type = name.strip(), location_type.strip()
    if not name or not location_type:
        raise InvalidOperation("Location name and type are required.")
    if parent_location_id == location.id:
        raise InvalidOperation("A location cannot be its own parent.")
    ancestor_id = parent_location_id
    while ancestor_id:
        ancestor = _tenant_record(session, Location, tenant_id, ancestor_id)
        if ancestor.id == location.id:
            raise InvalidOperation("Location hierarchy cannot contain a cycle.")
        ancestor_id = ancestor.parent_location_id
    source = update_master_source_reference(
        session,
        tenant_id,
        location.source_record_id,
        "location",
        source_system,
        external_id,
        source_payload or {"name": name, "type": location_type},
        payload_was_provided=source_payload is not None,
    )
    location.name, location.type = name, location_type
    location.parent_location_id = parent_location_id
    location.source_record_id = source.id if source else None
    if allows_stock is not None:
        location.allows_stock = allows_stock
    changes = _field_changes(before, _location_update_snapshot(location))
    if changes:
        emit_business_event(
            session,
            tenant_id,
            "location.updated",
            "location",
            location.id,
            {"name": location.name, "type": location.type, "changes": changes},
            source_record_id=location.source_record_id,
            action_id=action_id,
        )
    if _commit:
        session.commit()
    return location


def _assert_update_revision(
    session: OrmSession, tenant_id: str, family: str, record: dict[str, Any]
) -> None:
    expected = record.get("expected_revision")
    if expected is None:
        return
    current = master_data_update_snapshot(session, tenant_id, family, record["id"])
    if expected != _snapshot_revision(current):
        raise InvalidOperation(
            f"{family.capitalize()} changed since proposal review; create a new proposal."
        )


def update_parties(
    session: OrmSession,
    tenant_id: str,
    records: list[dict[str, Any]],
    *,
    action_id: str | None = None,
) -> list[Party]:
    _require_business_mutation(session, tenant_id, "update_parties")
    from reality.services.tenant_policy import require_master_call

    require_master_call(session, tenant_id, "party_update", records, action_id)
    if not records:
        raise InvalidOperation("At least one Party is required.")
    preview_master_data_updates(session, tenant_id, "party", records)
    updated: list[Party] = []
    try:
        for record in records:
            _assert_update_revision(session, tenant_id, "party", record)
            updated.append(
                update_party(
                    session,
                    tenant_id,
                    record["id"],
                    record["name"],
                    record["type"],
                    source_system=record.get("source_system"),
                    external_id=record.get("external_id"),
                    source_payload=record.get("source_payload"),
                    roles=record["roles"],
                    accounting_code=record.get("accounting_code"),
                    payment_term_code=record.get("payment_term_code"),
                    default_currency=record.get("default_currency"),
                    credit_limit=record.get("credit_limit"),
                    tax_identifier=record.get("tax_identifier"),
                    emails=record.get("emails"),
                    action_id=action_id,
                    _commit=False,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return updated


def update_items(
    session: OrmSession,
    tenant_id: str,
    records: list[dict[str, Any]],
    *,
    action_id: str | None = None,
) -> list[Item]:
    _require_business_mutation(session, tenant_id, "update_items")
    from reality.services.tenant_policy import require_master_call

    require_master_call(session, tenant_id, "item_update", records, action_id)
    if not records:
        raise InvalidOperation("At least one Item is required.")
    preview_master_data_updates(session, tenant_id, "item", records)
    updated: list[Item] = []
    try:
        for record in records:
            _assert_update_revision(session, tenant_id, "item", record)
            updated.append(
                update_item(
                    session,
                    tenant_id,
                    record["id"],
                    record["sku"],
                    record["name"],
                    record["unit"],
                    source_system=record.get("source_system"),
                    external_id=record.get("external_id"),
                    source_payload=record.get("source_payload"),
                    item_type=record.get("item_type"),
                    tracking_type=record.get("tracking_type"),
                    default_location_id=record.get("default_location_id"),
                    purchase_unit=record.get("purchase_unit"),
                    conversion_factor=record.get("conversion_factor"),
                    lead_time_days=record.get("lead_time_days"),
                    action_id=action_id,
                    _commit=False,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return updated


def update_locations(
    session: OrmSession,
    tenant_id: str,
    records: list[dict[str, Any]],
    *,
    action_id: str | None = None,
) -> list[Location]:
    _require_business_mutation(session, tenant_id, "update_locations")
    from reality.services.tenant_policy import require_master_call

    require_master_call(session, tenant_id, "location_update", records, action_id)
    if not records:
        raise InvalidOperation("At least one Location is required.")
    preview_master_data_updates(session, tenant_id, "location", records)
    updated: list[Location] = []
    try:
        for record in records:
            _assert_update_revision(session, tenant_id, "location", record)
            current = master_data_update_snapshot(
                session, tenant_id, "location", record["id"]
            )
            updated.append(
                update_location(
                    session,
                    tenant_id,
                    record["id"],
                    record["name"],
                    record["type"],
                    parent_location_id=record.get(
                        "parent_location_id", current["parent_location_id"]
                    ),
                    allows_stock=record.get("allows_stock", current["allows_stock"]),
                    source_system=record.get("source_system"),
                    external_id=record.get("external_id"),
                    source_payload=record.get("source_payload"),
                    action_id=action_id,
                    _commit=False,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return updated


def set_master_data_active(
    session: OrmSession,
    tenant_id: str,
    model: type[Party | Item | Location | PaymentTerm],
    record_id: str,
    is_active: bool,
    *,
    action_id: str | None = None,
) -> Party | Item | Location | PaymentTerm:
    _require_business_mutation(session, tenant_id, "set_master_data_active")
    if model not in {Party, Item, Location, PaymentTerm}:
        raise InvalidOperation("Unsupported master data type.")
    record = _tenant_record(session, model, tenant_id, record_id)
    before = record.is_active
    record.is_active = is_active
    if before != is_active:
        emit_business_event(
            session,
            tenant_id,
            "master_data.lifecycle_changed",
            model.__tablename__,
            record_id,
            {
                "is_active": is_active,
                "changes": {"is_active": {"before": before, "after": is_active}},
            },
            action_id=action_id,
        )
    session.commit()
    return record


def create_commitment(
    session: OrmSession,
    tenant_id: str,
    commitment_type: str,
    from_party_id: str,
    to_party_id: str,
    item_id: str,
    location_id: str,
    quantity: Decimal | float | str,
    due_at: datetime | str | None,
    *,
    action_id: str | None = None,
    amount: Decimal | float | str = ZERO,
    currency: str = "EUR",
    document_id: str | None = None,
    document_line_id: str | None = None,
    priority: str = "normal",
    _commit: bool = True,
) -> Commitment:
    _require_business_mutation(session, tenant_id, "create_commitment")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    if commitment_type not in {"customer_delivery", "supplier_delivery"}:
        raise InvalidOperation("Unsupported commitment type.")
    if priority not in {"low", "normal", "high", "urgent"}:
        raise InvalidOperation("Priority must be low, normal, high, or urgent.")
    for model, record_id in [
        (Party, from_party_id),
        (Party, to_party_id),
        (Item, item_id),
        (Location, location_id),
    ]:
        _tenant_record(session, model, tenant_id, record_id)
    if document_id:
        _tenant_record(session, Document, tenant_id, document_id)
    if document_line_id:
        line = _tenant_record(session, DocumentLine, tenant_id, document_line_id)
        if document_id and line.document_id != document_id:
            raise InvalidOperation("Document line does not belong to the document.")
    commitment = Commitment(
        id=uid("com"),
        tenant_id=tenant_id,
        type=commitment_type,
        from_party_id=from_party_id,
        to_party_id=to_party_id,
        item_id=item_id,
        location_id=location_id,
        quantity=positive(quantity),
        amount=decimal(amount),
        currency=currency,
        due_at=utc_datetime(due_at),
        status="open",
        document_id=document_id,
        document_line_id=document_line_id,
        priority=priority,
    )
    session.add(commitment)
    emit_business_event(
        session,
        tenant_id,
        "commitment.created",
        "commitment",
        commitment.id,
        {
            "type": commitment.type,
            "item_id": item_id,
            "quantity": commitment.quantity,
            "document_id": document_id,
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return commitment


def commitments(
    session: OrmSession, tenant_id: str, commitment_ids: Iterable[str] | None = None
) -> list[Commitment]:
    """Every promise of the company, or the named ones, in the same order."""
    ids = None if commitment_ids is None else set(commitment_ids)
    if ids is not None and not ids:
        return []
    statement = select(Commitment).where(Commitment.tenant_id == tenant_id)
    if ids is not None:
        statement = statement.where(Commitment.id.in_(ids))
    return list(session.scalars(statement.order_by(Commitment.due_at)))


def movement_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str, movement_type: str
) -> Decimal:
    """How much of one movement type stands against a promise.

    Movements a correction has voided do not count. Every caller reads the
    figure here — the service layer and the operational exception queue alike —
    so the two can never disagree about how much moved.
    """
    return _movement_quantities(session, tenant_id, commitment_id).get(
        (commitment_id, movement_type), ZERO
    )


def _movement_quantities(
    session: OrmSession, tenant_id: str, commitment_id: str | None = None
) -> dict[tuple[str | None, str], Decimal]:
    """Batch the same correction-aware quantities used by the scalar reader."""
    recorded = (
        select(Movement.commitment_id, Movement.type, func.sum(Movement.quantity))
        .where(Movement.tenant_id == tenant_id)
        .group_by(Movement.commitment_id, Movement.type)
    )
    reversed_values = (
        select(Movement.commitment_id, Movement.type, func.sum(Movement.quantity))
        .select_from(MovementCorrection)
        .join(Movement, Movement.id == MovementCorrection.original_movement_id)
        .where(
            MovementCorrection.tenant_id == tenant_id,
            Movement.tenant_id == tenant_id,
        )
        .group_by(Movement.commitment_id, Movement.type)
    )
    if commitment_id is not None:
        recorded = recorded.where(Movement.commitment_id == commitment_id)
        reversed_values = reversed_values.where(Movement.commitment_id == commitment_id)
    quantities = {
        (identity, kind): decimal(value)
        for identity, kind, value in session.execute(recorded)
    }
    for identity, kind, value in session.execute(reversed_values):
        key = (identity, kind)
        quantities[key] = quantities.get(key, ZERO) - decimal(value)
    return quantities


def fulfilled_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    """How much of a promise has been kept.

    Returns are deliberately not subtracted here. Fulfilment answers whether the
    company kept its word, and it did when the goods went out; taking returns off
    would reopen a kept promise as overdue and make a fully returned order look
    undelivered. The question "how much did the customer keep" is a different one,
    asked by the billing and crediting classes.
    """
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    movement_type = "shipment" if commitment.type == "customer_delivery" else "receipt"
    recorded = session.scalar(
        select(func.coalesce(func.sum(Movement.quantity), 0)).where(
            Movement.tenant_id == tenant_id,
            Movement.commitment_id == commitment_id,
            Movement.type == movement_type,
        )
    )
    reversed_value = session.scalar(
        select(func.coalesce(func.sum(Movement.quantity), 0))
        .select_from(MovementCorrection)
        .join(Movement, Movement.id == MovementCorrection.original_movement_id)
        .where(
            MovementCorrection.tenant_id == tenant_id,
            Movement.tenant_id == tenant_id,
            Movement.commitment_id == commitment_id,
            Movement.type == movement_type,
        )
    )
    return decimal(recorded or ZERO) - decimal(reversed_value or ZERO)


def movement_quantity_resolving(
    session: OrmSession, tenant_id: str, return_movement_id: str
) -> Decimal:
    """How much of one return has been settled.

    Movements a correction has voided do not count, on this side as on every
    other, so a resolution recorded in error stops settling anything.
    """
    recorded = session.scalar(
        select(func.coalesce(func.sum(Movement.quantity), 0)).where(
            Movement.tenant_id == tenant_id,
            Movement.resolves_movement_id == return_movement_id,
        )
    )
    reversed_value = session.scalar(
        select(func.coalesce(func.sum(Movement.quantity), 0))
        .select_from(MovementCorrection)
        .join(Movement, Movement.id == MovementCorrection.original_movement_id)
        .where(
            MovementCorrection.tenant_id == tenant_id,
            Movement.tenant_id == tenant_id,
            Movement.resolves_movement_id == return_movement_id,
        )
    )
    return decimal(recorded or ZERO) - decimal(reversed_value or ZERO)


def returned_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    """How much has come back against a customer delivery."""
    return movement_quantity(session, tenant_id, commitment_id, "return")


def returnable_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    """How much can still come back against a customer delivery.

    What went out, less what has already returned, both read the correction-aware
    way so a voided shipment protects nothing and a return recorded in error
    stops blocking one.

    The open quantity says nothing about this: on a fully shipped promise it is
    zero, and every return would be refused. What actually went out is the only
    honest bound, and it is asked here by the returning-movement path and by an
    announcement of a return that has not left the customer yet.
    """
    shipped = movement_quantity(session, tenant_id, commitment_id, "shipment")
    return shipped - returned_quantity(session, tenant_id, commitment_id)


def supplier_returned_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    """How much has gone back against a supplier delivery."""
    return movement_quantity(session, tenant_id, commitment_id, "supplier_return")


def commitment_revisions(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> list[CommitmentRevision]:
    """Every date a counterparty has stated for one promise, oldest first.

    Ordered by when it was stated and then by identity, so two statements in the
    same instant resolve the same way on every read.
    """
    return list(
        session.scalars(
            select(CommitmentRevision)
            .where(
                CommitmentRevision.tenant_id == tenant_id,
                CommitmentRevision.commitment_id == commitment_id,
            )
            .order_by(CommitmentRevision.stated_at, CommitmentRevision.id)
        )
    )


def _effective_commitment_value(
    commitment: Commitment, revisions: list[CommitmentRevision], field: str
) -> Any:
    """Read the latest stated non-null value from chronologically ordered revisions."""
    for revision in reversed(revisions):
        value = getattr(revision, field)
        if value is not None:
            return value
    return getattr(commitment, field)


def commitment_due_at(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> datetime | None:
    """The date a promise is actually due on: the last one anybody stated.

    One rule for every caller, because the date in force is now a derived figure
    several classes depend on and two copies of it would eventually disagree —
    which is what happened to unit comparability and to the learned thresholds
    before it.

    The latest revision that stated a date, which is not necessarily the latest
    revision: a statement about the quantity alone leaves an earlier date
    standing, because nobody restated it.

    The promise's own date is the fallback, never the answer where a
    counterparty has said something later.
    """
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    return _effective_commitment_value(
        commitment, commitment_revisions(session, tenant_id, commitment_id), "due_at"
    )


@dataclass(frozen=True)
class CommitmentTerms:
    """What one promise is for right now: the same figures the scalar readers give."""

    quantity: Decimal
    due_at: datetime | None
    fulfilled: Decimal
    open: Decimal
    reserved: Decimal

    @property
    def risk(self) -> str:
        return "AT RISK" if self.reserved < self.open else "OK"


def commitment_terms(
    session: OrmSession,
    tenant_id: str,
    commitment_ids: Iterable[str] | None = None,
) -> dict[str, CommitmentTerms]:
    """`commitment_quantity`, `commitment_due_at`, `fulfilled_quantity`, `open_quantity`
    and the active reservation for many promises in four reads.

    The projection builders asked those four questions once per commitment; on a
    1,000-order company that was 11,000 to 18,000 reads per builder (spec 181).
    Same revisions rule, same correction-aware movements, same reservation sum.
    """
    ids = None if commitment_ids is None else set(commitment_ids)
    if ids is not None and not ids:
        return {}
    rows = select(Commitment).where(Commitment.tenant_id == tenant_id)
    revisions_query = (
        select(CommitmentRevision)
        .where(CommitmentRevision.tenant_id == tenant_id)
        .order_by(CommitmentRevision.stated_at, CommitmentRevision.id)
    )
    reserved_query = (
        select(Reservation.commitment_id, func.sum(Reservation.quantity))
        .where(Reservation.tenant_id == tenant_id, Reservation.status == "active")
        .group_by(Reservation.commitment_id)
    )
    if ids is not None:
        rows = rows.where(Commitment.id.in_(ids))
        revisions_query = revisions_query.where(
            CommitmentRevision.commitment_id.in_(ids)
        )
        reserved_query = reserved_query.where(Reservation.commitment_id.in_(ids))
    revisions: dict[str, list[CommitmentRevision]] = {}
    for revision in session.scalars(revisions_query):
        revisions.setdefault(revision.commitment_id, []).append(revision)
    movements = _movement_quantities(session, tenant_id)
    reserved = {
        identity: decimal(value) for identity, value in session.execute(reserved_query)
    }
    terms: dict[str, CommitmentTerms] = {}
    for commitment in session.scalars(rows):
        stated = revisions.get(commitment.id, [])
        quantity = decimal(_effective_commitment_value(commitment, stated, "quantity"))
        movement_type = (
            "shipment" if commitment.type == "customer_delivery" else "receipt"
        )
        fulfilled = movements.get((commitment.id, movement_type), ZERO)
        terms[commitment.id] = CommitmentTerms(
            quantity=quantity,
            due_at=_effective_commitment_value(commitment, stated, "due_at"),
            fulfilled=fulfilled,
            open=max(ZERO, quantity - fulfilled),
            reserved=reserved.get(commitment.id, ZERO),
        )
    return terms


def commitment_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    """How much a promise is actually for: the last quantity anybody stated.

    The latest revision that stated a quantity, which is not necessarily the
    latest revision — a later statement about the date alone leaves an earlier
    quantity standing, because nobody restated it.

    One rule for every caller, beside the one that answers the date. This is the
    fourth derived figure this work has had to keep single-sourced, and by now
    the pattern is to write it once rather than find copies later.
    """
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    return decimal(
        _effective_commitment_value(
            commitment,
            commitment_revisions(session, tenant_id, commitment_id),
            "quantity",
        )
    )


def revise_commitment(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    due_at: datetime | str | None = None,
    *,
    quantity: Decimal | float | str | None = None,
    note: str = "",
    stated_at: datetime | str | None = None,
    source_record_id: str | None = None,
    retained_allocations: list[dict[str, Any]] | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> CommitmentRevision:
    """Record that the other side now says a promise is due on another day.

    This is not a correction. A correction says the record was wrong; this says
    the record was right and the world moved, which is the ordinary event in
    every trading relationship and was unrecordable until now.

    A held promise may still be revised. A hold stops execution, and what the
    other side said is not execution; refusing would lose a statement because of
    an unrelated block.

    A date already past is accepted: a supplier admitting it will be three days
    late is a real statement and the most useful kind.
    """
    _require_business_mutation(session, tenant_id, "revise_commitment")
    commitment = session.scalar(
        select(Commitment)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == commitment_id,
        )
        .with_for_update()
    )
    if commitment is None:
        raise NotFound("Commitment was not found.")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    if commitment.status != "open":
        raise InvalidOperation("Only an open commitment can be revised.")
    stated_due = utc_datetime(due_at) if due_at is not None else None
    if due_at is not None and stated_due is None:
        raise InvalidOperation("A revision must state a readable date.")
    stated_quantity = (
        positive(quantity, "revised quantity") if quantity is not None else None
    )
    if stated_due is None and stated_quantity is None:
        raise InvalidOperation("A revision must restate a date, a quantity, or both.")
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    active_allocations: list[Reservation] = []
    retained_quantity = ZERO
    retained_specs: list[tuple[Reservation, Decimal]] = []
    reconcile_allocations = False
    if stated_quantity is not None and commitment.type == "customer_delivery":
        active_allocations = list(
            session.scalars(
                select(Reservation)
                .where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.commitment_id == commitment.id,
                    Reservation.status == "active",
                )
                .order_by(Reservation.reserved_at, Reservation.id)
            )
        )
        fulfilled = fulfilled_quantity(session, tenant_id, commitment.id)
        revised_open = max(ZERO, stated_quantity - fulfilled)
        allocated = sum((decimal(row.quantity) for row in active_allocations), ZERO)
        if allocated > revised_open:
            reconcile_allocations = True
            identities = {
                (
                    row.location_id,
                    row.handling_unit_id,
                    row.lot_id,
                    row.serial_unit_id,
                )
                for row in active_allocations
            }
            if revised_open > ZERO and len(identities) > 1:
                if retained_allocations is None:
                    raise InvalidOperation(
                        "The revised quantity requires an explicit retained reservation "
                        "choice because active allocations use different locations or "
                        "tracking identities."
                    )
                by_id = {row.id: row for row in active_allocations}
                selected_ids: set[str] = set()
                for selected in retained_allocations:
                    if set(selected) != {"reservation_id", "quantity"}:
                        raise InvalidOperation(
                            "Each retained allocation must name only reservation_id and quantity."
                        )
                    reservation_id = str(selected["reservation_id"])
                    if reservation_id in selected_ids or reservation_id not in by_id:
                        raise InvalidOperation(
                            "Retained allocations must name distinct active reservations "
                            "for this commitment."
                        )
                    selected_ids.add(reservation_id)
                    selected_quantity = positive(
                        selected["quantity"], "retained allocation quantity"
                    )
                    original = by_id[reservation_id]
                    if selected_quantity > decimal(original.quantity):
                        raise InvalidOperation(
                            "A retained allocation cannot exceed its active reservation."
                        )
                    retained_specs.append((original, selected_quantity))
                retained_quantity = sum(
                    (selected_quantity for _, selected_quantity in retained_specs), ZERO
                )
                if retained_quantity > revised_open:
                    raise InvalidOperation(
                        "Retained allocation total cannot exceed revised open quantity."
                    )
            else:
                if retained_allocations:
                    raise InvalidOperation(
                        "Explicit retained allocations are only accepted when active "
                        "reservation identities require a choice."
                    )
                retained_quantity = revised_open
    revision = CommitmentRevision(
        id=uid("rev"),
        tenant_id=tenant_id,
        commitment_id=commitment.id,
        due_at=stated_due,
        quantity=stated_quantity,
        stated_at=utc_datetime(stated_at) or now(),
        note=note.strip(),
        source_record_id=source_record_id,
    )
    session.add(revision)
    if reconcile_allocations:
        template = active_allocations[0]
        for reservation in active_allocations:
            reservation.status = "released"
            emit_business_event(
                session,
                tenant_id,
                "reservation.released",
                "reservation",
                reservation.id,
                {
                    "commitment_id": commitment.id,
                    "cause": "commitment_quantity_revision",
                },
                source_record_id=source_record_id,
                action_id=action_id,
                correlation_id=action_id,
            )
        if retained_quantity > ZERO:
            allocations_to_create = retained_specs or [(template, retained_quantity)]
            for retained_from, retained_part in allocations_to_create:
                retained = Reservation(
                    id=uid("res"),
                    tenant_id=tenant_id,
                    commitment_id=commitment.id,
                    item_id=retained_from.item_id,
                    location_id=retained_from.location_id,
                    quantity=retained_part,
                    status="active",
                    handling_unit_id=retained_from.handling_unit_id,
                    lot_id=retained_from.lot_id,
                    serial_unit_id=retained_from.serial_unit_id,
                )
                session.add(retained)
                emit_business_event(
                    session,
                    tenant_id,
                    "reservation.created",
                    "reservation",
                    retained.id,
                    {
                        "commitment_id": commitment.id,
                        "item_id": retained.item_id,
                        "location_id": retained.location_id,
                        "quantity": retained.quantity,
                        "handling_unit_id": retained.handling_unit_id,
                        "lot_id": retained.lot_id,
                        "serial_unit_id": retained.serial_unit_id,
                        "previous_reservation_ids": [
                            row.id for row in active_allocations
                        ],
                        "cause": "commitment_quantity_revision",
                    },
                    source_record_id=source_record_id,
                    action_id=action_id,
                    correlation_id=action_id,
                )
    emit_business_event(
        session,
        tenant_id,
        "commitment.revised",
        "commitment",
        commitment.id,
        {
            "commitment_revision_id": revision.id,
            "due_at": stated_due.isoformat() if stated_due else None,
            "quantity": str(stated_quantity) if stated_quantity is not None else None,
            "originally_due_at": (
                commitment.due_at.isoformat() if commitment.due_at else None
            ),
        },
        source_record_id=source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    session.flush()
    # A promise revised down to what has already arrived is finished, and it is
    # settled here rather than at the next movement, because there may not be a
    # next movement. This is the one stored thing a revision writes, and it is
    # the same field the movement path sets for the same reason.
    if (
        stated_quantity is not None
        and open_quantity(session, tenant_id, commitment.id) == ZERO
    ):
        commitment.status = "fulfilled"
        # The only way a held promise reaches a closed state. A hold stops
        # execution and refuses every movement naming the promise, and Spec 093
        # deliberately lets a held promise still be revised — so a counterparty
        # saying "only send what you already sent" would otherwise leave a hold
        # standing on a finished promise, refusing every return against it for
        # a reason that has nothing to do with returns.
        release_commitment_hold(session, tenant_id, commitment.id, _commit=False)
    if _commit:
        session.commit()
    return revision


def open_quantity(session: OrmSession, tenant_id: str, commitment_id: str) -> Decimal:
    """What a promise still has to deliver, against the quantity in force."""
    return max(
        ZERO,
        commitment_quantity(session, tenant_id, commitment_id)
        - fulfilled_quantity(session, tenant_id, commitment_id),
    )


def stock_at(
    session: OrmSession, tenant_id: str, item_id: str, location_id: str | None = None
) -> Decimal:
    _tenant_record(session, Item, tenant_id, item_id)
    if location_id:
        _tenant_record(session, Location, tenant_id, location_id)
    incoming = select(func.coalesce(func.sum(Movement.quantity), 0)).where(
        Movement.tenant_id == tenant_id,
        Movement.item_id == item_id,
        Movement.to_location_id.is_not(None),
    )
    outgoing = select(func.coalesce(func.sum(Movement.quantity), 0)).where(
        Movement.tenant_id == tenant_id,
        Movement.item_id == item_id,
        Movement.from_location_id.is_not(None),
    )
    if location_id:
        incoming = incoming.where(Movement.to_location_id == location_id)
        outgoing = outgoing.where(Movement.from_location_id == location_id)
    return decimal(session.scalar(incoming) or ZERO) - decimal(
        session.scalar(outgoing) or ZERO
    )


def active_reserved(
    session: OrmSession, tenant_id: str, item_id: str, location_id: str | None = None
) -> Decimal:
    query = select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
        Reservation.tenant_id == tenant_id,
        Reservation.item_id == item_id,
        Reservation.status == "active",
    )
    if location_id:
        query = query.where(Reservation.location_id == location_id)
    return decimal(session.scalar(query) or ZERO)


def _validate_inventory_identity(
    session: OrmSession,
    tenant_id: str,
    item: Item,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    require_tracked_identity: bool = False,
) -> tuple[HandlingUnit | None, Lot | None, SerialUnit | None]:
    handling_unit = (
        _tenant_record(session, HandlingUnit, tenant_id, handling_unit_id)
        if handling_unit_id
        else None
    )
    lot = _tenant_record(session, Lot, tenant_id, lot_id) if lot_id else None
    serial = (
        _tenant_record(session, SerialUnit, tenant_id, serial_unit_id)
        if serial_unit_id
        else None
    )
    if lot and lot.item_id != item.id:
        raise InvalidOperation("Lot does not belong to the movement item.")
    if serial and serial.item_id != item.id:
        raise InvalidOperation("Serial unit does not belong to the movement item.")
    if serial and lot and serial.lot_id != lot.id:
        raise InvalidOperation("Serial unit does not belong to the selected lot.")
    if item.tracking_type == "none" and (lot or serial):
        raise InvalidOperation("Untracked items cannot use lot or serial identity.")
    if item.tracking_type == "lot":
        if serial:
            raise InvalidOperation("Lot-tracked items cannot use serial identity.")
        if require_tracked_identity and not lot:
            raise InvalidOperation("Lot-tracked items require a lot.")
    if item.tracking_type == "serial" and require_tracked_identity and not serial:
        raise InvalidOperation("Serial-tracked items require a serial unit.")
    return handling_unit, lot, serial


def stock_by_identity(
    session: OrmSession,
    tenant_id: str,
    item_id: str,
    location_id: str,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
) -> Decimal:
    incoming = select(func.coalesce(func.sum(Movement.quantity), 0)).where(
        Movement.tenant_id == tenant_id,
        Movement.item_id == item_id,
        Movement.to_location_id == location_id,
    )
    outgoing = select(func.coalesce(func.sum(Movement.quantity), 0)).where(
        Movement.tenant_id == tenant_id,
        Movement.item_id == item_id,
        Movement.from_location_id == location_id,
    )
    for field, value in (
        (Movement.handling_unit_id, handling_unit_id),
        (Movement.lot_id, lot_id),
        (Movement.serial_unit_id, serial_unit_id),
    ):
        if value:
            incoming = incoming.where(field == value)
            outgoing = outgoing.where(field == value)
    return decimal(session.scalar(incoming) or ZERO) - decimal(
        session.scalar(outgoing) or ZERO
    )


def reserved_by_identity(
    session: OrmSession,
    tenant_id: str,
    item_id: str,
    location_id: str,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
) -> Decimal:
    query = select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
        Reservation.tenant_id == tenant_id,
        Reservation.item_id == item_id,
        Reservation.location_id == location_id,
        Reservation.status == "active",
    )
    for field, value in (
        (Reservation.handling_unit_id, handling_unit_id),
        (Reservation.lot_id, lot_id),
        (Reservation.serial_unit_id, serial_unit_id),
    ):
        if value:
            query = query.where(field == value)
    return decimal(session.scalar(query) or ZERO)


@dataclass(frozen=True)
class ReservationResult:
    reservation: Reservation | None
    requested: Decimal
    reserved: Decimal
    shortage: Decimal
    event: BusinessEvent | None = None


def _preview_reservation(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    quantity: Decimal | float | str | None = None,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
) -> dict[str, Any]:
    """Validate and calculate allocation once for review and execution."""
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    require_not_held(session, tenant_id, commitment_id)
    if commitment.type != "customer_delivery" or commitment.status != "open":
        raise InvalidOperation(
            "Only open customer delivery commitments can be reserved."
        )
    item = _tenant_record(session, Item, tenant_id, commitment.item_id)
    _, _, serial = _validate_inventory_identity(
        session,
        tenant_id,
        item,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        require_tracked_identity=True,
    )
    if serial and serial.lot_id:
        lot_id = serial.lot_id
    remaining = open_quantity(session, tenant_id, commitment_id)
    already = decimal(
        session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment_id,
                Reservation.status == "active",
            )
        )
        or ZERO
    )
    requested = (
        Decimal(1)
        if serial_unit_id and quantity is None
        else remaining - already
        if quantity is None
        else positive(quantity)
    )
    if serial_unit_id and requested != Decimal(1):
        raise InvalidOperation("A serial reservation must have quantity 1.")
    requested = min(requested, max(ZERO, remaining - already))
    aggregate_available = max(
        ZERO,
        stock_at(session, tenant_id, commitment.item_id, commitment.location_id)
        - active_reserved(
            session, tenant_id, commitment.item_id, commitment.location_id
        ),
    )
    if handling_unit_id or lot_id or serial_unit_id:
        identity_available = max(
            ZERO,
            stock_by_identity(
                session,
                tenant_id,
                commitment.item_id,
                commitment.location_id,
                handling_unit_id=handling_unit_id,
                lot_id=lot_id,
                serial_unit_id=serial_unit_id,
            )
            - reserved_by_identity(
                session,
                tenant_id,
                commitment.item_id,
                commitment.location_id,
                handling_unit_id=handling_unit_id,
                lot_id=lot_id,
                serial_unit_id=serial_unit_id,
            ),
        )
        available = min(aggregate_available, identity_available)
    else:
        available = aggregate_available
    allocated = min(requested, available)
    return {
        "commitment": commitment,
        "requested": requested,
        "allocated": allocated,
        "lot_id": lot_id,
    }


def reserve(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    quantity: Decimal | float | str | None = None,
    *,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> ReservationResult:
    _require_business_mutation(session, tenant_id, "reserve")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    preview = _preview_reservation(
        session,
        tenant_id,
        commitment_id,
        quantity,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
    )
    commitment = preview["commitment"]
    requested, allocated, lot_id = (
        preview["requested"],
        preview["allocated"],
        preview["lot_id"],
    )
    reservation = None
    event = None
    if allocated > ZERO:
        reservation = Reservation(
            id=uid("res"),
            tenant_id=tenant_id,
            commitment_id=commitment.id,
            item_id=commitment.item_id,
            location_id=commitment.location_id,
            quantity=allocated,
            status="active",
            handling_unit_id=handling_unit_id,
            lot_id=lot_id,
            serial_unit_id=serial_unit_id,
        )
        session.add(reservation)
        event = emit_business_event(
            session,
            tenant_id,
            "reservation.created",
            "reservation",
            reservation.id,
            {
                "commitment_id": commitment.id,
                "item_id": commitment.item_id,
                "location_id": commitment.location_id,
                "quantity": allocated,
                "handling_unit_id": handling_unit_id,
                "lot_id": lot_id,
                "serial_unit_id": serial_unit_id,
            },
            action_id=action_id,
            correlation_id=action_id,
        )
        if _commit:
            session.commit()
        else:
            session.flush()
    return ReservationResult(
        reservation, requested, allocated, requested - allocated, event
    )


def release_reservation(
    session: OrmSession,
    tenant_id: str,
    reservation_id: str,
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> Reservation:
    from reality.services.tenant_policy import require_decision_release

    _require_business_mutation(session, tenant_id, "release_reservation")
    require_decision_release(session, tenant_id, reservation_id, action_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    reservation = _tenant_record(session, Reservation, tenant_id, reservation_id)
    if reservation.status == "active":
        reservation.status = "released"
        emit_business_event(
            session,
            tenant_id,
            "reservation.released",
            "reservation",
            reservation.id,
            {"commitment_id": reservation.commitment_id},
            action_id=action_id,
            correlation_id=action_id,
        )
        if _commit:
            session.commit()
        else:
            session.flush()
    return reservation


def _consume_reservations(
    session: OrmSession,
    commitment: Commitment,
    shipped: Decimal,
    *,
    from_location_id: str,
    action_id: str | None = None,
    causation_id: str | None = None,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
) -> None:
    remaining = shipped
    reservations = session.scalars(
        select(Reservation)
        .where(
            Reservation.tenant_id == commitment.tenant_id,
            Reservation.commitment_id == commitment.id,
            Reservation.status == "active",
            Reservation.location_id == from_location_id,
            Reservation.handling_unit_id == handling_unit_id,
            Reservation.lot_id == lot_id,
            Reservation.serial_unit_id == serial_unit_id,
        )
        .order_by(Reservation.reserved_at)
    ).all()
    for reservation in reservations:
        if remaining <= ZERO:
            break
        allocated = decimal(reservation.quantity)
        reservation.status = "consumed"
        emit_business_event(
            session,
            commitment.tenant_id,
            "reservation.consumed",
            "reservation",
            reservation.id,
            {
                "commitment_id": commitment.id,
                "quantity": allocated,
                "consumed_quantity": min(remaining, allocated),
                "cause": "shipment",
            },
            action_id=action_id,
            correlation_id=action_id,
            causation_id=causation_id,
        )
        if allocated > remaining:
            remainder = Reservation(
                id=uid("res"),
                tenant_id=reservation.tenant_id,
                commitment_id=reservation.commitment_id,
                item_id=reservation.item_id,
                location_id=reservation.location_id,
                quantity=allocated - remaining,
                status="active",
                handling_unit_id=reservation.handling_unit_id,
                lot_id=reservation.lot_id,
                serial_unit_id=reservation.serial_unit_id,
            )
            session.add(remainder)
            emit_business_event(
                session,
                commitment.tenant_id,
                "reservation.created",
                "reservation",
                remainder.id,
                {
                    "commitment_id": commitment.id,
                    "quantity": remainder.quantity,
                    "item_id": remainder.item_id,
                    "location_id": remainder.location_id,
                    "handling_unit_id": remainder.handling_unit_id,
                    "lot_id": remainder.lot_id,
                    "serial_unit_id": remainder.serial_unit_id,
                    "previous_reservation_id": reservation.id,
                    "cause": "shipment_remainder",
                },
                action_id=action_id,
                correlation_id=action_id,
                causation_id=causation_id,
            )
        remaining -= min(remaining, allocated)
    _release_reservations_beyond_open(
        session,
        commitment,
        from_location_id,
        action_id=action_id,
        causation_id=causation_id,
    )


def _release_reservations_beyond_open(
    session: OrmSession,
    commitment: Commitment,
    from_location_id: str,
    *,
    action_id: str | None,
    causation_id: str | None,
) -> None:
    """Release what a shipment from elsewhere left reserved beyond the open quantity.

    Stock held at another location was not taken, so its Reservation is not
    consumed; the promise simply no longer needs all of it.
    """
    elsewhere = session.scalars(
        select(Reservation)
        .where(
            Reservation.tenant_id == commitment.tenant_id,
            Reservation.commitment_id == commitment.id,
            Reservation.status == "active",
            Reservation.location_id != from_location_id,
        )
        .order_by(Reservation.reserved_at.desc())
    ).all()
    if not elsewhere:
        return
    held = decimal(
        session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == commitment.tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
        or ZERO
    )
    excess = held - open_quantity(session, commitment.tenant_id, commitment.id)
    for reservation in elsewhere:
        if excess <= ZERO:
            break
        allocated = decimal(reservation.quantity)
        released = min(excess, allocated)
        reservation.status = "released"
        emit_business_event(
            session,
            commitment.tenant_id,
            "reservation.released",
            "reservation",
            reservation.id,
            {
                "commitment_id": commitment.id,
                "released_quantity": released,
                "cause": "shipped_from_another_location",
            },
            action_id=action_id,
            correlation_id=action_id,
            causation_id=causation_id,
        )
        if allocated > released:
            remainder = Reservation(
                id=uid("res"),
                tenant_id=reservation.tenant_id,
                commitment_id=reservation.commitment_id,
                item_id=reservation.item_id,
                location_id=reservation.location_id,
                quantity=allocated - released,
                status="active",
                handling_unit_id=reservation.handling_unit_id,
                lot_id=reservation.lot_id,
                serial_unit_id=reservation.serial_unit_id,
            )
            session.add(remainder)
            emit_business_event(
                session,
                commitment.tenant_id,
                "reservation.created",
                "reservation",
                remainder.id,
                {
                    "commitment_id": commitment.id,
                    "quantity": remainder.quantity,
                    "item_id": remainder.item_id,
                    "location_id": remainder.location_id,
                    "handling_unit_id": remainder.handling_unit_id,
                    "lot_id": remainder.lot_id,
                    "serial_unit_id": remainder.serial_unit_id,
                    "previous_reservation_id": reservation.id,
                    "cause": "shipped_from_another_location",
                },
                action_id=action_id,
                correlation_id=action_id,
                causation_id=causation_id,
            )
        excess -= released


def create_handling_unit(
    session: OrmSession,
    tenant_id: str,
    nve: str | None = None,
    *,
    source_record_id: str | None = None,
) -> HandlingUnit:
    _require_business_mutation(session, tenant_id, "create_handling_unit")
    get_tenant(session, tenant_id)
    normalized_nve = nve.strip() if nve and nve.strip() else None
    if normalized_nve and session.scalar(
        select(HandlingUnit).where(
            HandlingUnit.tenant_id == tenant_id,
            HandlingUnit.nve == normalized_nve,
        )
    ):
        raise InvalidOperation("NVE already exists for this tenant.")
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    handling_unit = HandlingUnit(
        id=uid("hu"),
        tenant_id=tenant_id,
        nve=normalized_nve,
        source_record_id=source_record_id,
    )
    session.add(handling_unit)
    emit_business_event(
        session,
        tenant_id,
        "handling_unit.created",
        "handling_unit",
        handling_unit.id,
        {"nve": handling_unit.nve},
        source_record_id=source_record_id,
    )
    session.commit()
    return handling_unit


def handling_units(session: OrmSession, tenant_id: str) -> list[HandlingUnit]:
    get_tenant(session, tenant_id)
    return list(
        session.scalars(
            select(HandlingUnit)
            .where(HandlingUnit.tenant_id == tenant_id)
            .order_by(HandlingUnit.created_at.desc())
        )
    )


def _stated_date(value: date | str) -> date:
    """A calendar day exactly as stated, or a refusal.

    Nothing is computed here and nothing is defaulted: a best-before is read off
    the goods, and a date nobody could read is not a date.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        raise InvalidOperation(
            "A stated date must be a readable calendar day."
        ) from None


def create_lot(
    session: OrmSession,
    tenant_id: str,
    item_id: str,
    lot_number: str,
    *,
    expires_at: date | str | None = None,
    source_record_id: str | None = None,
    _commit: bool = True,
) -> Lot:
    _require_business_mutation(session, tenant_id, "create_lot")
    item = _tenant_record(session, Item, tenant_id, item_id)
    if item.tracking_type not in {"lot", "serial"}:
        raise InvalidOperation("Lots require an item with lot or serial tracking.")
    number = lot_number.strip()
    if not number:
        raise InvalidOperation("Lot number is required.")
    if session.scalar(
        select(Lot).where(
            Lot.tenant_id == tenant_id,
            Lot.item_id == item_id,
            Lot.lot_number == number,
        )
    ):
        raise InvalidOperation("Lot number already exists for this item.")
    stated_expiry = _stated_date(expires_at) if expires_at is not None else None
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    lot = Lot(
        id=uid("lot"),
        tenant_id=tenant_id,
        item_id=item_id,
        lot_number=number,
        expires_at=stated_expiry,
        source_record_id=source_record_id,
    )
    session.add(lot)
    emit_business_event(
        session,
        tenant_id,
        "lot.created",
        "lot",
        lot.id,
        {
            "item_id": item_id,
            "lot_number": number,
            "expires_at": stated_expiry.isoformat() if stated_expiry else None,
        },
        source_record_id=source_record_id,
    )
    if _commit:
        session.commit()
    else:
        session.flush()
    return lot


def state_lot_expiry(
    session: OrmSession,
    tenant_id: str,
    lot_id: str,
    expires_at: date | str,
    *,
    _commit: bool = True,
) -> Lot:
    """Record the best-before date somebody read off the goods.

    Statable after the lot exists because goods arrive before anybody reads the
    label, and the alternative would be recreating the lot.

    Re-stating a *different* date is refused. A best-before read off the goods is
    a received value, and two different dates for one lot means one of them is
    wrong in a way this product cannot adjudicate. Re-stating the same date is
    accepted and changes nothing, so a retry is safe. A proper correction needs
    the append-only shape a promise revision has, which is separable work.

    Nothing is computed. A shelf life multiplied out from a production date would
    be a date nobody stated.
    """
    _require_business_mutation(session, tenant_id, "state_lot_expiry")
    lot = _tenant_record(session, Lot, tenant_id, lot_id)
    stated = _stated_date(expires_at)
    if lot.expires_at is not None and lot.expires_at != stated:
        raise InvalidOperation(
            "A lot's best-before date is already stated as "
            f"{lot.expires_at.isoformat()}; it is a received value and is not adjusted. "
            "Correct it instead, saying what is stated now and why it was wrong."
        )
    if lot.expires_at == stated:
        return lot
    lot.expires_at = stated
    emit_business_event(
        session,
        tenant_id,
        "lot.expiry_stated",
        "lot",
        lot.id,
        {
            "item_id": lot.item_id,
            "lot_number": lot.lot_number,
            "expires_at": stated.isoformat(),
        },
    )
    if _commit:
        session.commit()
    return lot


def correct_lot_expiry(
    session: OrmSession,
    tenant_id: str,
    lot_id: str,
    expires_at: date | str | None,
    *,
    expected_expires_at: date | str | None,
    reason: str,
    actor_context: dict[str, Any] | None = None,
    _commit: bool = True,
) -> Lot:
    """Say the stated best-before was read wrong, and what it says instead.

    A correction rather than a restatement, and the difference decides the shape.
    A counterparty moving a delivery date is the world moving, which is why that
    keeps every statement. A best-before is printed on a box: it does not move,
    so a second date means the first reading was wrong, and keeping both as
    equally valid statements would record a contradiction as though it were
    history. So the value is corrected in place and the audit goes in the event,
    exactly as a manual document's line correction carries its own.

    It costs two things. A **reason**, because this is somebody saying the record
    was wrong and the reason is the only part of that a later reader can use. And
    the date they believe is stored — including naming that none is — because an
    operation that overwrites what a person got wrong must not be reachable by
    somebody who has not looked at it. That is the confirmed count of a stale
    closure, the confirmed total of a payment run and the expected revision of a
    document correction, for the same reason each time.

    Correcting to nothing is allowed: a date read off the wrong label, on an item
    with no shelf life, can only honestly be fixed by saying the lot has no date.
    The cost is that the record then looks like one nobody ever dated, and the
    event history is where that distinction survives.

    Nothing is judged. Reality cannot know which label was misread; it records
    that somebody says the first reading was wrong.
    """
    _require_business_mutation(session, tenant_id, "correct_lot_expiry")
    lot = _tenant_record(session, Lot, tenant_id, lot_id)
    stated_reason = (reason or "").strip()
    if not stated_reason:
        raise InvalidOperation("A best-before correction requires a reason.")
    corrected = _stated_date(expires_at) if expires_at is not None else None
    confirmed = (
        _stated_date(expected_expires_at) if expected_expires_at is not None else None
    )
    if lot.expires_at != confirmed:
        raise InvalidOperation(
            "The best-before correction no longer matches what is stated: "
            f"{lot.expires_at.isoformat() if lot.expires_at else 'none'} is stored, "
            f"{confirmed.isoformat() if confirmed else 'none'} was confirmed."
        )
    if corrected == confirmed:
        raise InvalidOperation(
            "A correction must change the best-before date; this one changes nothing."
        )
    lot.expires_at = corrected
    emit_business_event(
        session,
        tenant_id,
        "lot.expiry_corrected",
        "lot",
        lot.id,
        {
            "item_id": lot.item_id,
            "lot_number": lot.lot_number,
            "before": confirmed.isoformat() if confirmed else None,
            "after": corrected.isoformat() if corrected else None,
            "reason": stated_reason,
            # So a reader can see where the batch came from, which is a
            # different question from where the date came from.
            "lot_source_record_id": lot.source_record_id,
            "actor_context": actor_context or {},
        },
    )
    if _commit:
        session.commit()
    return lot


def expired_lots(
    session: OrmSession, tenant_id: str, *, as_of: datetime | None = None
) -> list[Lot]:
    """Lots whose stated best-before has passed, oldest first.

    A lot with no stated date is absent in both directions: there is no way to
    tell an item with no shelf life from one whose label nobody read, so nothing
    is asserted about it.
    """
    get_tenant(session, tenant_id)
    today = (as_of or now()).date()
    return list(
        session.scalars(
            select(Lot)
            .where(
                Lot.tenant_id == tenant_id,
                Lot.expires_at.is_not(None),
                Lot.expires_at < today,
            )
            .order_by(Lot.expires_at, Lot.id)
        )
    )


def create_serial_unit(
    session: OrmSession,
    tenant_id: str,
    item_id: str,
    serial_number: str,
    *,
    lot_id: str | None = None,
    source_record_id: str | None = None,
    _commit: bool = True,
) -> SerialUnit:
    _require_business_mutation(session, tenant_id, "create_serial_unit")
    item = _tenant_record(session, Item, tenant_id, item_id)
    if item.tracking_type != "serial":
        raise InvalidOperation("Serial units require an item with serial tracking.")
    number = serial_number.strip()
    if not number:
        raise InvalidOperation("Serial number is required.")
    lot = _tenant_record(session, Lot, tenant_id, lot_id) if lot_id else None
    if lot and lot.item_id != item_id:
        raise InvalidOperation("Lot does not belong to the serial item.")
    if session.scalar(
        select(SerialUnit).where(
            SerialUnit.tenant_id == tenant_id,
            SerialUnit.item_id == item_id,
            SerialUnit.serial_number == number,
        )
    ):
        raise InvalidOperation("Serial number already exists for this item.")
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    serial = SerialUnit(
        id=uid("ser"),
        tenant_id=tenant_id,
        item_id=item_id,
        serial_number=number,
        lot_id=lot_id,
        source_record_id=source_record_id,
    )
    session.add(serial)
    emit_business_event(
        session,
        tenant_id,
        "serial_unit.created",
        "serial_unit",
        serial.id,
        {"item_id": item_id, "serial_number": number, "lot_id": lot_id},
        source_record_id=source_record_id,
    )
    if _commit:
        session.commit()
    else:
        session.flush()
    return serial


def lots(session: OrmSession, tenant_id: str, item_id: str | None = None) -> list[Lot]:
    get_tenant(session, tenant_id)
    query = select(Lot).where(Lot.tenant_id == tenant_id)
    if item_id:
        _tenant_record(session, Item, tenant_id, item_id)
        query = query.where(Lot.item_id == item_id)
    return list(session.scalars(query.order_by(Lot.created_at.desc())))


def serial_units(
    session: OrmSession, tenant_id: str, item_id: str | None = None
) -> list[SerialUnit]:
    get_tenant(session, tenant_id)
    query = select(SerialUnit).where(SerialUnit.tenant_id == tenant_id)
    if item_id:
        _tenant_record(session, Item, tenant_id, item_id)
        query = query.where(SerialUnit.item_id == item_id)
    return list(session.scalars(query.order_by(SerialUnit.created_at.desc())))


def return_announcements(
    session: OrmSession,
    tenant_id: str,
    *,
    commitment_id: str | None = None,
    status: str | None = None,
) -> list[ReturnAnnouncement]:
    """Every return a customer has announced, in the order they said so.

    Ordered by when it was announced and then by identity, so two identical
    reads of an unchanged tenant return the same list in the same order.
    """
    get_tenant(session, tenant_id)
    query = select(ReturnAnnouncement).where(ReturnAnnouncement.tenant_id == tenant_id)
    if commitment_id:
        _tenant_record(session, Commitment, tenant_id, commitment_id)
        query = query.where(ReturnAnnouncement.commitment_id == commitment_id)
    if status:
        query = query.where(ReturnAnnouncement.status == status)
    return list(
        session.scalars(
            query.order_by(ReturnAnnouncement.announced_at, ReturnAnnouncement.id)
        )
    )


def arrived_against_announcement(
    session: OrmSession, tenant_id: str, announcement_id: str
) -> Decimal:
    """How much has come back against one announcement.

    Correction-aware on this side as on every other, so a return recorded in
    error stops counting as having arrived.
    """
    recorded = session.scalar(
        select(func.coalesce(func.sum(Movement.quantity), 0)).where(
            Movement.tenant_id == tenant_id,
            Movement.return_announcement_id == announcement_id,
        )
    )
    reversed_value = session.scalar(
        select(func.coalesce(func.sum(Movement.quantity), 0))
        .select_from(MovementCorrection)
        .join(Movement, Movement.id == MovementCorrection.original_movement_id)
        .where(
            MovementCorrection.tenant_id == tenant_id,
            Movement.tenant_id == tenant_id,
            Movement.return_announcement_id == announcement_id,
        )
    )
    return decimal(recorded or ZERO) - decimal(reversed_value or ZERO)


def announcement_outstanding(
    session: OrmSession, tenant_id: str, announcement: ReturnAnnouncement
) -> Decimal:
    """What an announcement is still waiting for, never below nothing.

    A customer who said two and sent three has nothing outstanding rather than
    minus one: the extra item physically exists and is an ordinary return.
    """
    arrived = arrived_against_announcement(session, tenant_id, announcement.id)
    return max(decimal(announcement.quantity) - arrived, ZERO)


def announceable_quantity(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    """How much may still be announced against a customer delivery.

    What can still come back, less what open announcements are already claiming.
    Without that second term a customer could announce the same five items twice
    and the receiving desk would expect ten.
    """
    claimed = sum(
        (
            announcement_outstanding(session, tenant_id, announcement)
            for announcement in return_announcements(
                session, tenant_id, commitment_id=commitment_id, status="open"
            )
        ),
        ZERO,
    )
    return returnable_quantity(session, tenant_id, commitment_id) - claimed


def announce_customer_return(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    quantity: Decimal | float | str,
    *,
    reference: str = "",
    reason: str = "",
    expected_by: datetime | str | None = None,
    announced_at: datetime | str | None = None,
    note: str = "",
    source_record_id: str | None = None,
    _commit: bool = True,
) -> ReturnAnnouncement:
    """Record that a customer says goods are coming back.

    Until now a return was only recordable once it was standing on the dock, so
    everything before that — how much, why, the number the parcel will carry,
    the day the customer said it would go — was kept in somebody's inbox.

    A fulfilled delivery is exactly when returns happen, so only a cancelled
    promise is refused. Nothing here is generated: the reference least of all,
    because a number this product invented would be a number somebody has to
    tell the customer, and there is no way to do that from here.
    """
    _require_business_mutation(session, tenant_id, "announce_customer_return")
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    if commitment.type != "customer_delivery":
        raise InvalidOperation(
            "A customer return is announced against a customer delivery."
        )
    if commitment.status == "cancelled":
        raise InvalidOperation(
            "A cancelled promise cannot have a return announced against it."
        )
    qty = positive(quantity, "announced quantity")
    stated_expectation = utc_datetime(expected_by) if expected_by is not None else None
    if expected_by is not None and stated_expectation is None:
        raise InvalidOperation("An announcement must state a readable expected day.")
    available = announceable_quantity(session, tenant_id, commitment.id)
    if qty > available:
        raise InvalidOperation(
            "More is announced than can still come back against the delivery."
        )
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    announcement = ReturnAnnouncement(
        id=uid("ann"),
        tenant_id=tenant_id,
        commitment_id=commitment.id,
        quantity=qty,
        reference=reference,
        reason=reason,
        announced_at=utc_datetime(announced_at) or now(),
        expected_by=stated_expectation,
        status="open",
        note=note,
        source_record_id=source_record_id,
    )
    session.add(announcement)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "return.announced",
        "return_announcement",
        announcement.id,
        {
            "commitment_id": commitment.id,
            "quantity": qty,
            "reference": reference,
            "reason": reason,
            "expected_by": stated_expectation,
        },
        source_record_id=source_record_id,
        occurred_at=announcement.announced_at,
    )
    if _commit:
        session.commit()
    return announcement


def withdraw_return_announcement(
    session: OrmSession,
    tenant_id: str,
    announcement_id: str,
    *,
    note: str = "",
    _commit: bool = True,
) -> ReturnAnnouncement:
    """Record that the customer is not sending the goods back after all.

    What they announced is kept. A withdrawal is another statement about the
    same conversation, not a reason to forget the first one, and what may be
    announced against the delivery returns to what the delivery allows.
    """
    _require_business_mutation(session, tenant_id, "withdraw_return_announcement")
    announcement = _tenant_record(
        session, ReturnAnnouncement, tenant_id, announcement_id
    )
    if announcement.status != "open":
        raise InvalidOperation("Only an open announcement can be withdrawn.")
    announcement.status = "withdrawn"
    announcement.closed_at = now()
    if note:
        announcement.note = note
    emit_business_event(
        session,
        tenant_id,
        "return.announcement_withdrawn",
        "return_announcement",
        announcement.id,
        {
            "commitment_id": announcement.commitment_id,
            "quantity": decimal(announcement.quantity),
            "note": note,
        },
    )
    if _commit:
        session.commit()
    return announcement


def validate_commitment_movement_quantity(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    quantity: Decimal | float | str,
) -> None:
    """Shared non-mutating fulfillment bound for review and execution."""
    _tenant_record(session, Commitment, tenant_id, commitment_id)
    if positive(quantity) > open_quantity(session, tenant_id, commitment_id):
        raise InvalidOperation("Movement exceeds the commitment's open quantity.")


def _excluded_stock_effect(
    movement: Movement | None,
    item_id: str,
    location_id: str | None,
    **identity: str | None,
) -> Decimal:
    """Physical contribution removed by the proposed inverse, without writing rows."""
    if movement is None or movement.item_id != item_id:
        return ZERO
    if any(
        value and getattr(movement, key) != value for key, value in identity.items()
    ):
        return ZERO
    incoming = bool(
        movement.to_location_id
        and (not location_id or movement.to_location_id == location_id)
    )
    outgoing = bool(
        movement.from_location_id
        and (not location_id or movement.from_location_id == location_id)
    )
    return decimal(movement.quantity) * (int(incoming) - int(outgoing))


def _projected_movement_quantity(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    movement_type: str,
    excluded: Movement | None,
) -> Decimal:
    quantity = movement_quantity(session, tenant_id, commitment_id, movement_type)
    if (
        excluded
        and excluded.commitment_id == commitment_id
        and excluded.type == movement_type
    ):
        quantity -= decimal(excluded.quantity)
    return quantity


def _append_movement(
    session: OrmSession,
    tenant_id: str,
    movement_type: str,
    item_id: str,
    quantity: Decimal | float | str,
    *,
    from_location_id: str | None = None,
    to_location_id: str | None = None,
    commitment_id: str | None = None,
    source_record_id: str | None = None,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    occurred_at: datetime | None = None,
    reason: str | None = None,
    resolves_movement_id: str | None = None,
    return_announcement_id: str | None = None,
    shipment_package_id: str | None = None,
    emit_recorded_event: bool = True,
    consume_reservations: bool = True,
    commit: bool = False,
    action_id: str | None = None,
    validate_only: bool = False,
    _correcting: Movement | None = None,
) -> Movement | dict[str, Any]:
    if _correcting is not None and not validate_only:
        raise InvalidOperation("Projected state is only valid for a read-only preview.")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    qty = positive(quantity)
    item = _tenant_record(session, Item, tenant_id, item_id)
    if item.item_type != "stocked":
        raise InvalidOperation("Only stocked items can have physical movements.")
    for location_id in (from_location_id, to_location_id):
        if location_id:
            location = _tenant_record(session, Location, tenant_id, location_id)
            if not location.allows_stock:
                raise InvalidOperation("Location does not allow physical stock.")
    commitment = (
        _tenant_record(session, Commitment, tenant_id, commitment_id)
        if commitment_id
        else None
    )
    if commitment:
        require_not_held(session, tenant_id, commitment.id)
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    if shipment_package_id:
        shipment_package = _tenant_record(
            session, ShipmentPackage, tenant_id, shipment_package_id
        )
        shipment = _tenant_record(
            session, Shipment, tenant_id, shipment_package.shipment_id
        )
        from reality.domain.shipments import (
            ShipmentCompatibilityError,
            validate_movement_compatibility,
        )

        try:
            validate_movement_compatibility(
                shipment.purpose, shipment.direction, movement_type
            )
        except ShipmentCompatibilityError as error:
            raise InvalidOperation(str(error)) from error
    _, _, serial = _validate_inventory_identity(
        session,
        tenant_id,
        item,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        require_tracked_identity=True,
    )
    if serial and serial.lot_id:
        lot_id = serial.lot_id
    if serial_unit_id and qty != Decimal(1):
        raise InvalidOperation("A serial movement must have quantity 1.")
    requirements = {
        "opening_stock": (False, True),
        "receipt": (False, True),
        "shipment": (True, False),
        "transfer": (True, True),
        "return": (False, True),
        # Goods going back to a supplier are the opposite physical fact from a
        # customer return, so they are their own kind with their own direction.
        # One type inferring its direction from the commitment would stop a
        # movement being a plain statement about what happened.
        "supplier_return": (True, False),
    }
    if movement_type == "adjustment":
        if bool(from_location_id) == bool(to_location_id):
            raise InvalidOperation(
                "Adjustment requires exactly one location direction."
            )
        if not reason or not reason.strip():
            raise InvalidOperation("Adjustment reason is required.")
        needs_from, needs_to = bool(from_location_id), bool(to_location_id)
    elif movement_type in requirements:
        needs_from, needs_to = requirements[movement_type]
    else:
        raise InvalidOperation("Unsupported movement type.")
    if (needs_from and not from_location_id) or (needs_to and not to_location_id):
        raise InvalidOperation(f"Locations are incomplete for {movement_type}.")
    if (
        movement_type in {"shipment", "transfer", "supplier_return"}
        or (movement_type == "adjustment" and from_location_id)
    ) and (
        stock_at(session, tenant_id, item_id, from_location_id)
        - _excluded_stock_effect(_correcting, item_id, from_location_id)
    ) < qty:
        raise InvalidOperation("Movement exceeds physical stock.")
    if (
        from_location_id
        and (handling_unit_id or lot_id or serial_unit_id)
        and stock_by_identity(
            session,
            tenant_id,
            item_id,
            from_location_id,
            handling_unit_id=handling_unit_id,
            lot_id=lot_id,
            serial_unit_id=serial_unit_id,
        )
        - _excluded_stock_effect(
            _correcting,
            item_id,
            from_location_id,
            handling_unit_id=handling_unit_id,
            lot_id=lot_id,
            serial_unit_id=serial_unit_id,
        )
        < qty
    ):
        raise InvalidOperation("Movement exceeds stock for the selected identity.")
    if serial_unit_id and movement_type in {"opening_stock", "receipt", "return"}:
        serial_in = session.scalar(
            select(func.coalesce(func.sum(Movement.quantity), 0)).where(
                Movement.tenant_id == tenant_id,
                Movement.serial_unit_id == serial_unit_id,
                Movement.to_location_id.is_not(None),
            )
        )
        serial_out = session.scalar(
            select(func.coalesce(func.sum(Movement.quantity), 0)).where(
                Movement.tenant_id == tenant_id,
                Movement.serial_unit_id == serial_unit_id,
                Movement.from_location_id.is_not(None),
            )
        )
        if (
            decimal(serial_in or ZERO)
            - decimal(serial_out or ZERO)
            - _excluded_stock_effect(
                _correcting, item_id, None, serial_unit_id=serial_unit_id
            )
            > ZERO
        ):
            raise InvalidOperation("Serial unit is already in physical stock.")
    announcement = None
    if return_announcement_id:
        # Resolved before the commitment is judged, so a caller naming an
        # announcement on the wrong kind of movement is told that rather than
        # something about open quantity.
        announcement = _tenant_record(
            session, ReturnAnnouncement, tenant_id, return_announcement_id
        )
        if movement_type != "return":
            raise InvalidOperation(
                "Only returning goods fulfil an announced customer return."
            )
        if announcement.status != "open":
            raise InvalidOperation("Only an open announcement can be fulfilled.")
        # The check that makes the reference mean something. Without it any
        # return could claim to fulfil any customer's announcement.
        if announcement.commitment_id != commitment_id:
            raise InvalidOperation(
                "A movement fulfils an announcement of its own delivery only."
            )
    if commitment:
        # A return names the delivery it reverses, and each side is reversed by
        # its own kind: a customer delivery by goods coming back, a supplier
        # delivery by goods going out again.
        allowed = (
            {"shipment", "return"}
            if commitment.type == "customer_delivery"
            else {"receipt", "supplier_return"}
        )
        if movement_type not in allowed or commitment.item_id != item_id:
            raise InvalidOperation("Movement does not match the commitment.")
        if (
            movement_type == "shipment"
            and commitment.type == "customer_delivery"
            and active_party_delivery_hold(session, tenant_id, commitment.to_party_id)
        ):
            raise InvalidOperation(
                "Customer has an active delivery hold; release it before shipment."
            )
        if movement_type == "return":
            # One rule answers what can still come back, and this path is its
            # caller rather than its owner: an announcement of a return has to
            # bound itself by exactly the same figure.
            if qty > (
                _projected_movement_quantity(
                    session, tenant_id, commitment.id, "shipment", _correcting
                )
                - _projected_movement_quantity(
                    session, tenant_id, commitment.id, "return", _correcting
                )
            ):
                raise InvalidOperation(
                    "Return exceeds what was shipped against the commitment."
                )
        elif movement_type == "supplier_return":
            # The same reasoning in the other direction, and it matters more
            # here: a supplier delivery is usually received in full, so its open
            # quantity is zero exactly when a company is most likely to want to
            # send something back.
            received = _projected_movement_quantity(
                session, tenant_id, commitment.id, "receipt", _correcting
            )
            already_gone = _projected_movement_quantity(
                session, tenant_id, commitment.id, "supplier_return", _correcting
            )
            if qty > received - already_gone:
                raise InvalidOperation(
                    "Supplier return exceeds what was received against the commitment."
                )
        else:
            if _correcting is None:
                validate_commitment_movement_quantity(
                    session, tenant_id, commitment.id, qty
                )
            else:
                fulfilled_type = (
                    "shipment" if commitment.type == "customer_delivery" else "receipt"
                )
                projected_open = max(
                    ZERO,
                    commitment_quantity(session, tenant_id, commitment.id)
                    - _projected_movement_quantity(
                        session, tenant_id, commitment.id, fulfilled_type, _correcting
                    ),
                )
                if qty > projected_open:
                    raise InvalidOperation(
                        "Movement exceeds the commitment's open quantity."
                    )
    resolved_return = None
    if resolves_movement_id:
        resolved_return = _tenant_record(
            session, Movement, tenant_id, resolves_movement_id
        )
        if resolved_return.type != "return":
            raise InvalidOperation("A resolution must name a return.")
        if resolved_return.item_id != item_id:
            raise InvalidOperation(
                "A resolution must concern the same item as the return."
            )
        # The one physical check available: goods can only be settled out of
        # the place they came back to. Without it any outward movement could
        # claim to settle any return.
        if not from_location_id or from_location_id != resolved_return.to_location_id:
            raise InvalidOperation(
                "A resolution must take the goods out of the location they came back to."
            )
        already = movement_quantity_resolving(session, tenant_id, resolved_return.id)
        if qty > decimal(resolved_return.quantity) - already:
            raise InvalidOperation("Resolutions exceed what came back.")
    if validate_only:
        return {
            "quantity": qty,
            "lot_id": lot_id,
            "commitment_id": commitment_id,
            "item_id": item_id,
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
        }
    movement = Movement(
        id=uid("mov"),
        tenant_id=tenant_id,
        type=movement_type,
        item_id=item_id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        quantity=qty,
        commitment_id=commitment_id,
        source_record_id=source_record_id,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        occurred_at=occurred_at or now(),
        resolves_movement_id=resolves_movement_id,
        return_announcement_id=return_announcement_id,
        shipment_package_id=shipment_package_id,
    )
    session.add(movement)
    recorded_event = None
    if emit_recorded_event:
        recorded_event = emit_business_event(
            session,
            tenant_id,
            "movement.recorded",
            "movement",
            movement.id,
            {
                "type": movement.type,
                "item_id": item_id,
                "quantity": qty,
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "commitment_id": commitment_id,
                "handling_unit_id": handling_unit_id,
                "lot_id": lot_id,
                "serial_unit_id": serial_unit_id,
                "shipment_package_id": shipment_package_id,
            },
            source_record_id=source_record_id,
            occurred_at=movement.occurred_at,
            action_id=action_id,
            correlation_id=action_id,
        )
    session.flush()
    if movement_type == "adjustment":
        session.add(
            ChangeProposal(
                id=uid("act"),
                tenant_id=tenant_id,
                type="inventory_adjusted",
                input=json.dumps({"reason": reason}),
                output=json.dumps({"movement_id": movement.id}),
            )
        )
    if commitment:
        if movement_type == "shipment" and consume_reservations:
            _consume_reservations(
                session,
                commitment,
                qty,
                from_location_id=from_location_id,
                action_id=action_id,
                causation_id=recorded_event.id if recorded_event else None,
                handling_unit_id=handling_unit_id,
                lot_id=lot_id,
                serial_unit_id=serial_unit_id,
            )
        if open_quantity(session, tenant_id, commitment.id) == ZERO:
            previous_status = commitment.status
            commitment.status = "fulfilled"
            if previous_status != "fulfilled" and emit_recorded_event:
                emit_business_event(
                    session,
                    tenant_id,
                    "commitment.fulfilled",
                    "commitment",
                    commitment.id,
                    {"previous_status": previous_status, "movement_id": movement.id},
                    action_id=action_id,
                    correlation_id=action_id,
                    causation_id=recorded_event.id if recorded_event else None,
                )
    if (
        announcement is not None
        and announcement_outstanding(session, tenant_id, announcement) <= ZERO
    ):
        # Settled at this moment rather than at the next read, because there may
        # be no next event: the parcel arrived and that is the end of it. Same
        # field and same reasoning as a promise falling to what already arrived.
        announcement.status = "fulfilled"
        announcement.closed_at = now()
    if commit:
        session.commit()
    return movement


def record_movement(
    session: OrmSession,
    tenant_id: str,
    movement_type: str,
    item_id: str,
    quantity: Decimal | float | str,
    *,
    from_location_id: str | None = None,
    to_location_id: str | None = None,
    commitment_id: str | None = None,
    source_record_id: str | None = None,
    handling_unit_id: str | None = None,
    lot_id: str | None = None,
    serial_unit_id: str | None = None,
    occurred_at: datetime | None = None,
    reason: str | None = None,
    resolves_movement_id: str | None = None,
    return_announcement_id: str | None = None,
    shipment_package_id: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Movement:
    _require_business_mutation(session, tenant_id, "record_movement")
    from reality.services.tenant_policy import (
        require_decision_action,
        require_decision_movement,
    )

    require_decision_action(session, tenant_id, action_id)
    require_decision_movement(
        session,
        tenant_id,
        {
            "movement_type": movement_type,
            "item_id": item_id,
            "quantity": quantity,
            "to_location_id": to_location_id,
            "from_location_id": from_location_id,
            "commitment_id": commitment_id,
            "occurred_at": occurred_at,
        },
        extra_identity=any(
            value is not None
            for value in (
                from_location_id
                if movement_type not in {"receipt", "return"}
                else None,
                commitment_id if movement_type not in {"receipt", "return"} else None,
                source_record_id,
                handling_unit_id,
                lot_id,
                serial_unit_id,
                reason,
                resolves_movement_id,
                return_announcement_id,
                shipment_package_id,
            )
        ),
    )
    return _append_movement(
        session,
        tenant_id,
        movement_type,
        item_id,
        quantity,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        commitment_id=commitment_id,
        source_record_id=source_record_id,
        handling_unit_id=handling_unit_id,
        lot_id=lot_id,
        serial_unit_id=serial_unit_id,
        occurred_at=occurred_at,
        reason=reason,
        resolves_movement_id=resolves_movement_id,
        return_announcement_id=return_announcement_id,
        shipment_package_id=shipment_package_id,
        commit=_commit,
        action_id=action_id,
    )


@dataclass(frozen=True)
class MovementCorrectionResult:
    correction_id: str
    original_movement_id: str
    compensating_movement_id: str
    replacement_movement_id: str | None
    request_fingerprint: str
    replayed: bool


def _movement_values(movement: Movement) -> dict[str, Any]:
    return {
        "id": movement.id,
        "type": movement.type,
        "item_id": movement.item_id,
        "quantity": format(decimal(movement.quantity).normalize(), "f"),
        "from_location_id": movement.from_location_id,
        "to_location_id": movement.to_location_id,
        "commitment_id": movement.commitment_id,
        "source_record_id": movement.source_record_id,
        "handling_unit_id": movement.handling_unit_id,
        "lot_id": movement.lot_id,
        "serial_unit_id": movement.serial_unit_id,
        "occurred_at": movement.occurred_at.isoformat(),
        "resolves_movement_id": movement.resolves_movement_id,
        "return_announcement_id": movement.return_announcement_id,
        "shipment_package_id": movement.shipment_package_id,
    }


def _movement_correction_relation_for_member(
    session: OrmSession, tenant_id: str, movement_id: str
) -> tuple[MovementCorrection | None, str]:
    relation = session.scalar(
        select(MovementCorrection).where(
            MovementCorrection.tenant_id == tenant_id,
            MovementCorrection.original_movement_id == movement_id,
        )
    )
    if relation:
        return relation, "corrected"
    relation = session.scalar(
        select(MovementCorrection).where(
            MovementCorrection.tenant_id == tenant_id,
            MovementCorrection.compensating_movement_id == movement_id,
        )
    )
    if relation:
        return relation, "compensation"
    relation = session.scalar(
        select(MovementCorrection).where(
            MovementCorrection.tenant_id == tenant_id,
            MovementCorrection.replacement_movement_id == movement_id,
        )
    )
    return (relation, "replacement") if relation else (None, "normal")


def movement_correction_snapshot(
    session: OrmSession, tenant_id: str, movement_id: str
) -> dict[str, Any]:
    movement = session.scalar(
        select(Movement).where(
            Movement.tenant_id == tenant_id, Movement.id == movement_id
        )
    )
    if movement is None:
        raise NotFound("Movement not found.")
    relation, role = _movement_correction_relation_for_member(
        session, tenant_id, movement_id
    )
    original = movement
    compensation = replacement = None
    if relation:
        original = _tenant_record(
            session, Movement, tenant_id, relation.original_movement_id
        )
        compensation = _tenant_record(
            session, Movement, tenant_id, relation.compensating_movement_id
        )
        replacement = (
            _tenant_record(
                session, Movement, tenant_id, relation.replacement_movement_id
            )
            if relation.replacement_movement_id
            else None
        )
    revision = canonical_payload_hash(
        {
            "movement": _movement_values(original),
            "correction_id": relation.id if relation else None,
            "request_fingerprint": relation.request_fingerprint if relation else None,
        }
    )
    return {
        "movement_id": movement_id,
        "revision": revision,
        "role": role,
        "status": "corrected" if relation else "recorded",
        "correctable": relation is None or role == "replacement",
        "guidance": (
            "Compensating Movements cannot be corrected."
            if role == "compensation"
            else "This Movement already has a correction chain."
            if role == "corrected"
            else "Preview and confirm a full inverse with an optional replacement."
        ),
        "original": _movement_values(original),
        "compensation": _movement_values(compensation) if compensation else None,
        "replacement": _movement_values(replacement) if replacement else None,
        "correction": (
            {
                "id": relation.id,
                "reason": relation.reason,
                "corrected_at": relation.corrected_at.isoformat(),
                "actor_context": json.loads(relation.actor_context or "{}"),
                "request_fingerprint": relation.request_fingerprint,
            }
            if relation
            else None
        ),
    }


def preview_movement_correction(
    session: OrmSession,
    tenant_id: str,
    movement_id: str,
    *,
    reason: str,
    replacement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(reason, str):
        raise InvalidOperation("Movement correction reason is required.")
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise InvalidOperation("Movement correction reason is required.")
    snapshot = movement_correction_snapshot(session, tenant_id, movement_id)
    if not snapshot["correctable"]:
        raise InvalidOperation(snapshot["guidance"])
    original = _tenant_record(session, Movement, tenant_id, movement_id)
    if original.to_location_id and stock_at(
        session, tenant_id, original.item_id, original.to_location_id
    ) < decimal(original.quantity):
        raise InvalidOperation(
            "Later Movements depend on this stock; correct dependent Movements first."
        )
    if (
        original.to_location_id
        and (original.handling_unit_id or original.lot_id or original.serial_unit_id)
        and stock_by_identity(
            session,
            tenant_id,
            original.item_id,
            original.to_location_id,
            handling_unit_id=original.handling_unit_id,
            lot_id=original.lot_id,
            serial_unit_id=original.serial_unit_id,
        )
        < decimal(original.quantity)
    ):
        raise InvalidOperation(
            "Later tracked-identity Movements depend on this stock; correct them first."
        )
    normalized_replacement = None
    if replacement is not None:
        allowed = {
            "type",
            "item_id",
            "quantity",
            "from_location_id",
            "to_location_id",
            "commitment_id",
            "source_record_id",
            "handling_unit_id",
            "lot_id",
            "serial_unit_id",
            "occurred_at",
            "reason",
        }
        if (
            not isinstance(replacement, dict)
            or set(replacement) - allowed
            or not {"type", "item_id", "quantity"} <= set(replacement)
        ):
            raise InvalidOperation("Check the supported replacement fields.")
        normalized_replacement = {
            key: (str(value) if isinstance(value, Decimal) else value)
            for key, value in sorted(replacement.items())
        }
        if normalized_replacement.get("occurred_at") is not None:
            normalized_replacement["occurred_at"] = utc_datetime(
                normalized_replacement["occurred_at"]
            ).isoformat()
    if normalized_replacement is not None:
        values = dict(normalized_replacement)
        kind, item, quantity = (
            values.pop("type"),
            values.pop("item_id"),
            values.pop("quantity"),
        )
        _append_movement(
            session,
            tenant_id,
            kind,
            item,
            quantity,
            **values,
            validate_only=True,
            _correcting=original,
        )
    fingerprint = _movement_correction_fingerprint(
        tenant_id, movement_id, normalized_reason, normalized_replacement
    )
    compensation = {
        **_movement_values(original),
        "id": None,
        "type": "correction",
        "from_location_id": original.to_location_id,
        "to_location_id": original.from_location_id,
        "commitment_id": None,
        "source_record_id": None,
    }
    return {
        "movement_id": movement_id,
        "revision": snapshot["revision"],
        "request_fingerprint": fingerprint,
        "reason": normalized_reason,
        "original": _movement_values(original),
        "compensation": compensation,
        "replacement": normalized_replacement,
        "net_quantity": (
            str(decimal(normalized_replacement["quantity"]))
            if normalized_replacement
            else "0"
        ),
    }


def _movement_correction_fingerprint(
    tenant_id: str,
    movement_id: str,
    reason: str,
    replacement: dict[str, Any] | None,
) -> str:
    payload = {
        "tenant_id": tenant_id,
        "movement_id": movement_id,
        "reason": reason,
        "replacement": replacement,
    }
    return canonical_payload_hash(payload)


def correct_movement(
    session: OrmSession,
    tenant_id: str,
    movement_id: str,
    *,
    reason: str,
    replacement: dict[str, Any] | None = None,
    actor_context: dict[str, Any] | None = None,
    expected_revision: str | None = None,
    preview_fingerprint: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> MovementCorrectionResult:
    _require_business_mutation(session, tenant_id, "correct_movement")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise InvalidOperation("Movement correction reason is required.")
    normalized_replacement = None
    if replacement is not None:
        normalized_replacement = {
            key: (str(value) if isinstance(value, Decimal) else value)
            for key, value in sorted(replacement.items())
        }
        if normalized_replacement.get("occurred_at") is not None:
            normalized_replacement["occurred_at"] = utc_datetime(
                normalized_replacement["occurred_at"]
            ).isoformat()
    fingerprint = _movement_correction_fingerprint(
        tenant_id, movement_id, normalized_reason, normalized_replacement
    )
    try:
        original = session.scalar(
            select(Movement)
            .where(Movement.tenant_id == tenant_id, Movement.id == movement_id)
            .with_for_update()
        )
        if original is None:
            raise NotFound("Movement not found.")
        if preview_fingerprint and preview_fingerprint != fingerprint:
            raise Conflict("Movement correction preview no longer matches the request.")
        compensation_relation = session.scalar(
            select(MovementCorrection).where(
                MovementCorrection.tenant_id == tenant_id,
                MovementCorrection.compensating_movement_id == movement_id,
            )
        )
        if compensation_relation:
            raise InvalidOperation("A compensating Movement cannot be corrected.")
        existing = session.scalar(
            select(MovementCorrection).where(
                MovementCorrection.tenant_id == tenant_id,
                MovementCorrection.original_movement_id == movement_id,
            )
        )
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise Conflict(
                    "Movement was already corrected; reload its correction chain."
                )
            return MovementCorrectionResult(
                existing.id,
                existing.original_movement_id,
                existing.compensating_movement_id,
                existing.replacement_movement_id,
                existing.request_fingerprint,
                True,
            )
        current_snapshot = movement_correction_snapshot(session, tenant_id, movement_id)
        if expected_revision and expected_revision != current_snapshot["revision"]:
            raise Conflict(
                "Movement correction preview is stale; reload and preview again."
            )

        compensation_from = original.to_location_id
        compensation_to = original.from_location_id
        if compensation_from and stock_at(
            session, tenant_id, original.item_id, compensation_from
        ) < decimal(original.quantity):
            raise InvalidOperation(
                "Later Movements depend on this stock; correct dependent Movements first."
            )
        if (
            compensation_from
            and (
                original.handling_unit_id or original.lot_id or original.serial_unit_id
            )
            and stock_by_identity(
                session,
                tenant_id,
                original.item_id,
                compensation_from,
                handling_unit_id=original.handling_unit_id,
                lot_id=original.lot_id,
                serial_unit_id=original.serial_unit_id,
            )
            < decimal(original.quantity)
        ):
            raise InvalidOperation(
                "Later tracked-identity Movements depend on this stock; correct them first."
            )
        compensation = Movement(
            id=uid("mov"),
            tenant_id=tenant_id,
            type="correction",
            item_id=original.item_id,
            from_location_id=compensation_from,
            to_location_id=compensation_to,
            quantity=original.quantity,
            commitment_id=None,
            source_record_id=None,
            handling_unit_id=original.handling_unit_id,
            lot_id=original.lot_id,
            serial_unit_id=original.serial_unit_id,
            occurred_at=now(),
        )
        session.add(compensation)
        session.flush()

        corrected_at = now()
        correction = MovementCorrection(
            id=uid("mco"),
            tenant_id=tenant_id,
            original_movement_id=original.id,
            compensating_movement_id=compensation.id,
            replacement_movement_id=None,
            reason=normalized_reason,
            corrected_at=corrected_at,
            actor_context=json.dumps(
                actor_context or {}, sort_keys=True, separators=(",", ":")
            ),
            request_fingerprint=fingerprint,
        )
        session.add(correction)
        session.flush()

        replacement_movement = None
        if normalized_replacement is not None:
            replacement_data = dict(normalized_replacement)
            replacement_movement = _append_movement(
                session,
                tenant_id,
                replacement_data.pop("type"),
                replacement_data.pop("item_id"),
                replacement_data.pop("quantity"),
                from_location_id=replacement_data.pop("from_location_id", None),
                to_location_id=replacement_data.pop("to_location_id", None),
                commitment_id=replacement_data.pop("commitment_id", None),
                source_record_id=replacement_data.pop("source_record_id", None),
                handling_unit_id=replacement_data.pop("handling_unit_id", None),
                lot_id=replacement_data.pop("lot_id", None),
                serial_unit_id=replacement_data.pop("serial_unit_id", None),
                occurred_at=utc_datetime(replacement_data.pop("occurred_at", None)),
                reason=replacement_data.pop("reason", None),
                shipment_package_id=replacement_data.pop(
                    "shipment_package_id", original.shipment_package_id
                ),
                emit_recorded_event=False,
                consume_reservations=False,
                commit=False,
            )
            if replacement_data:
                raise InvalidOperation("Unsupported replacement fields.")
            correction.replacement_movement_id = replacement_movement.id
        session.flush()
        affected_commitments = {
            value
            for value in (
                original.commitment_id,
                replacement_movement.commitment_id if replacement_movement else None,
            )
            if value
        }
        for commitment_id in affected_commitments:
            commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
            if commitment.status != "cancelled":
                commitment.status = (
                    "fulfilled"
                    if open_quantity(session, tenant_id, commitment.id) == ZERO
                    else "open"
                )
        correction_event = emit_business_event(
            session,
            tenant_id,
            "movement.corrected",
            "movement",
            original.id,
            {
                "correction_id": correction.id,
                "item_id": original.item_id,
                "compensating_movement_id": compensation.id,
                "replacement_movement_id": correction.replacement_movement_id,
                "reason": normalized_reason,
                "actor_context": actor_context or {},
            },
            occurred_at=corrected_at,
            action_id=action_id,
            correlation_id=action_id,
        )
        from reality.services.costing import _capture_correction

        session.flush()
        _capture_correction(session, tenant_id, correction, correction_event)
        if _commit:
            session.commit()
        return MovementCorrectionResult(
            correction.id,
            original.id,
            compensation.id,
            correction.replacement_movement_id,
            fingerprint,
            False,
        )
    except Exception:
        if _commit:
            session.rollback()
        raise


def cancel_commitment(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    *,
    reason: str,
    source_record_id: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Commitment:
    _require_business_mutation(session, tenant_id, "cancel_commitment")
    stated_reason = reason.strip()
    if not stated_reason:
        raise InvalidOperation("A cancellation requires a reason.")
    commitment = session.scalar(
        select(Commitment)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == commitment_id,
        )
        .with_for_update()
    )
    if commitment is None:
        raise NotFound("Commitment was not found.")
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    if commitment.status != "open":
        raise InvalidOperation("Only an open commitment can be cancelled.")
    commitment.status = "cancelled"
    commitment.cancelled_at = now()
    released_reservation_ids = []
    for reservation in session.scalars(
        select(Reservation).where(
            Reservation.tenant_id == tenant_id,
            Reservation.commitment_id == commitment_id,
            Reservation.status == "active",
        )
    ):
        reservation.status = "released"
        released_reservation_ids.append(reservation.id)
    # A hold says somebody is dealing with this promise. Nobody is: the promise
    # is off. Leaving it active would go on refusing every movement against the
    # promise — including goods coming back against a partial shipment — for a
    # reason that no longer has a subject. Reservations are let go here for
    # exactly the same reason, and a hold is the same shape of thing.
    #
    # Nothing anybody said is erased: a release sets one timestamp, and the
    # reason, the note, who raised it and when all stay. That is what makes
    # doing this automatically safe.
    released_holds = release_commitment_hold(
        session, tenant_id, commitment.id, _commit=False
    )
    emit_business_event(
        session,
        tenant_id,
        "commitment.cancelled",
        "commitment",
        commitment.id,
        {
            "released_reservations": True,
            "released_reservation_ids": released_reservation_ids,
            "released_hold_ids": [hold.id for hold in released_holds],
            "reason": stated_reason,
        },
        source_record_id=source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return commitment


def active_commitment_hold(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> CommitmentHold | None:
    _tenant_record(session, Commitment, tenant_id, commitment_id)
    return session.scalar(
        select(CommitmentHold)
        .where(
            CommitmentHold.tenant_id == tenant_id,
            CommitmentHold.commitment_id == commitment_id,
            CommitmentHold.released_at.is_(None),
        )
        .order_by(CommitmentHold.created_at.desc())
    )


def require_not_held(session: OrmSession, tenant_id: str, commitment_id: str) -> None:
    hold = active_commitment_hold(session, tenant_id, commitment_id)
    if hold:
        raise InvalidOperation(
            f"Commitment is on hold ({hold.reason_code}); release it before execution."
        )


def _validate_commitment_hold(
    session: OrmSession, tenant_id: str, commitment_id: str, reason_code: str
) -> Commitment:
    """Shared read-only prerequisites for a delivery hold."""
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    if commitment.status != "open":
        raise InvalidOperation("Only open commitments can be put on hold.")
    if not isinstance(reason_code, str) or reason_code not in HOLD_REASONS:
        raise InvalidOperation("Unsupported hold reason.")
    return commitment


def hold_commitment(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    reason_code: str,
    note: str = "",
    *,
    created_by: str = "human",
    action_id: str | None = None,
    _commit: bool = True,
) -> CommitmentHold:
    _require_business_mutation(session, tenant_id, "hold_commitment")
    _validate_commitment_hold(session, tenant_id, commitment_id, reason_code)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    existing = active_commitment_hold(session, tenant_id, commitment_id)
    if existing:
        return existing
    hold = CommitmentHold(
        id=uid("hld"),
        tenant_id=tenant_id,
        commitment_id=commitment_id,
        reason_code=reason_code,
        note=note.strip(),
        created_by=created_by.strip() or "human",
    )
    session.add(hold)
    emit_business_event(
        session,
        tenant_id,
        "commitment.held",
        "commitment",
        commitment_id,
        {"hold_id": hold.id, "reason_code": reason_code},
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    else:
        session.flush()
    return hold


# A closure shows a person enough promises to recognise what they are about to
# close. It is recognition, not completeness: the count is what they confirm.
STALE_CLOSURE_SAMPLE = 25


def _stale_promises(
    session: OrmSession,
    tenant_id: str,
    *,
    direction: str,
    due_before: datetime | str,
) -> list[Commitment]:
    """Promises an import left behind, by a rule a person can state and check.

    One selection, used by the preview and by the closure, so the number
    somebody confirms is the number that closes. Nothing here decides that a
    promise is dead — it answers what matches criteria somebody typed.
    """
    if direction not in {"sales", "purchase"}:
        raise InvalidOperation("Direction must be sales or purchase.")
    cutoff = utc_datetime(due_before)
    if cutoff is None:
        raise InvalidOperation("A closure needs a date to be due before.")
    commitment_type = (
        "customer_delivery" if direction == "sales" else "supplier_delivery"
    )
    movement_type = "shipment" if direction == "sales" else "receipt"
    matches = []
    rows = session.scalars(
        select(Commitment)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.type == commitment_type,
            Commitment.status == "open",
            Commitment.due_at.is_not(None),
            Commitment.due_at < cutoff,
        )
        .order_by(Commitment.due_at, Commitment.id)
    )
    for row in rows:
        # Anything that has moved is work in progress rather than residue, read
        # the correction-aware way so a voided shipment protects nothing.
        if movement_quantity(session, tenant_id, row.id, movement_type) > ZERO:
            continue
        # A hold is somebody saying they are dealing with this promise.
        if active_commitment_hold(session, tenant_id, row.id):
            continue
        party_id = row.to_party_id if direction == "sales" else row.from_party_id
        if party_id and active_party_delivery_hold(session, tenant_id, party_id):
            continue
        matches.append(row)
    return matches


def _reserved_against(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> Decimal:
    return decimal(
        session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment_id,
                Reservation.status == "active",
            )
        )
        or ZERO
    )


def preview_stale_promise_closure(
    session: OrmSession,
    tenant_id: str,
    *,
    direction: str,
    due_before: datetime | str,
) -> dict[str, Any]:
    """What a closure would do, without doing any of it."""
    get_tenant(session, tenant_id)
    matches = _stale_promises(
        session, tenant_id, direction=direction, due_before=due_before
    )
    released = sum(
        (_reserved_against(session, tenant_id, row.id) for row in matches), ZERO
    )
    return {
        "count": len(matches),
        "released_quantity": released,
        "sample": [row.id for row in matches[:STALE_CLOSURE_SAMPLE]],
    }


def close_stale_promises(
    session: OrmSession,
    tenant_id: str,
    *,
    direction: str,
    due_before: datetime | str,
    expected_count: int,
    reason: str,
    actor_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Close the promises somebody previewed, counted and gave a reason for.

    The confirmed count is the safety: what a person looked at may not be what
    is there. This is the only operation in the product that closes many records
    at once, and it is deliberately hard to run by accident.
    """
    _require_business_mutation(session, tenant_id, "close_stale_promises")
    get_tenant(session, tenant_id)
    stated_reason = (reason or "").strip()
    if not stated_reason:
        raise InvalidOperation("A closure requires a reason.")
    matches = _stale_promises(
        session, tenant_id, direction=direction, due_before=due_before
    )
    if len(matches) != expected_count:
        raise InvalidOperation(
            "The closure no longer matches the confirmed count: "
            f"{len(matches)} match, {expected_count} were confirmed."
        )
    try:
        for row in matches:
            cancel_commitment(
                session,
                tenant_id,
                row.id,
                reason=stated_reason,
                _commit=False,
            )
        emit_business_event(
            session,
            tenant_id,
            "promises.closed",
            "tenant",
            tenant_id,
            {
                "direction": direction,
                "due_before": utc_datetime(due_before).isoformat(),
                "reason": stated_reason,
                "closed": len(matches),
                "commitment_ids": [row.id for row in matches],
                "actor_context": actor_context or {},
            },
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"closed": len(matches), "reason": stated_reason}


def release_commitment_hold(
    session: OrmSession,
    tenant_id: str,
    commitment_id: str,
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[CommitmentHold]:
    """Lift every hold on one promise.

    `_commit=False` lets the release join the transaction that closed the
    promise, which is how a bulk closure releases forty sets of holds or none.
    There is one release path on purpose: two copies of "set the timestamp and
    emit the event" is how the two copies stop agreeing.
    """
    _require_business_mutation(session, tenant_id, "release_commitment_hold")
    _tenant_record(session, Commitment, tenant_id, commitment_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    holds = list(
        session.scalars(
            select(CommitmentHold).where(
                CommitmentHold.tenant_id == tenant_id,
                CommitmentHold.commitment_id == commitment_id,
                CommitmentHold.released_at.is_(None),
            )
        )
    )
    released_at = now()
    for hold in holds:
        hold.released_at = released_at
    if holds:
        emit_business_event(
            session,
            tenant_id,
            "commitment.hold_released",
            "commitment",
            commitment_id,
            {"hold_ids": [hold.id for hold in holds]},
            action_id=action_id,
            correlation_id=action_id,
        )
    if _commit:
        session.commit()
    return holds


def hold_document_commitments(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    reason_code: str,
    note: str = "",
    *,
    created_by: str = "human",
) -> list[CommitmentHold]:
    _require_business_mutation(session, tenant_id, "hold_document_commitments")
    _tenant_record(session, Document, tenant_id, document_id)
    linked = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id == document_id,
                Commitment.status == "open",
            )
        )
    )
    if not linked:
        raise InvalidOperation("Document has no open commitments to hold.")
    return [
        hold_commitment(
            session,
            tenant_id,
            commitment.id,
            reason_code,
            note,
            created_by=created_by,
        )
        for commitment in linked
    ]


def release_document_holds(
    session: OrmSession, tenant_id: str, document_id: str
) -> list[CommitmentHold]:
    _require_business_mutation(session, tenant_id, "release_document_holds")
    _tenant_record(session, Document, tenant_id, document_id)
    linked_ids = list(
        session.scalars(
            select(Commitment.id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id == document_id,
            )
        )
    )
    released = []
    for commitment_id in linked_ids:
        released.extend(release_commitment_hold(session, tenant_id, commitment_id))
    return released


def active_party_delivery_hold(
    session: OrmSession, tenant_id: str, party_id: str
) -> PartyHold | None:
    _tenant_record(session, Party, tenant_id, party_id)
    return session.scalar(
        select(PartyHold)
        .where(
            PartyHold.tenant_id == tenant_id,
            PartyHold.party_id == party_id,
            PartyHold.hold_type == "delivery",
            PartyHold.released_at.is_(None),
        )
        .order_by(PartyHold.created_at.desc())
    )


def party_hold_snapshot(hold: PartyHold) -> dict[str, Any]:
    """Immutable identity and declaration fields, independent of later release."""
    return {
        "id": hold.id,
        "party_id": hold.party_id,
        "hold_type": hold.hold_type,
        "reason_code": hold.reason_code,
        "note": hold.note,
        "created_by": hold.created_by,
        "created_at": str(hold.created_at),
    }


def hold_party_delivery(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    reason_code: str,
    note: str = "",
    *,
    created_by: str = "human",
    action_id: str | None = None,
) -> PartyHold:
    _require_business_mutation(session, tenant_id, "hold_party_delivery")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Party, tenant_id, party_id)
    if reason_code not in HOLD_REASONS:
        raise InvalidOperation("Unsupported hold reason.")
    existing = active_party_delivery_hold(session, tenant_id, party_id)
    if existing:
        return existing
    hold = PartyHold(
        id=uid("phd"),
        tenant_id=tenant_id,
        party_id=party_id,
        hold_type="delivery",
        reason_code=reason_code,
        note=note.strip(),
        created_by=created_by.strip() or "human",
    )
    session.add(hold)
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "party.delivery_hold_placed",
        "party",
        party_id,
        {
            "hold_id": hold.id,
            "reason_code": reason_code,
            "hold": party_hold_snapshot(hold),
        },
        action_id=action_id,
        correlation_id=action_id,
        occurred_at=hold.created_at,
    )
    session.commit()
    return hold


def release_party_delivery_hold(
    session: OrmSession, tenant_id: str, party_id: str, *, action_id: str | None = None
) -> list[PartyHold]:
    _require_business_mutation(session, tenant_id, "release_party_delivery_hold")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Party, tenant_id, party_id)
    holds = list(
        session.scalars(
            select(PartyHold)
            .where(
                PartyHold.tenant_id == tenant_id,
                PartyHold.party_id == party_id,
                PartyHold.hold_type == "delivery",
                PartyHold.released_at.is_(None),
            )
            .order_by(PartyHold.id)
        )
    )
    released_at = now()
    for hold in holds:
        hold.released_at = released_at
    if holds:
        emit_business_event(
            session,
            tenant_id,
            "party.delivery_hold_released",
            "party",
            party_id,
            {
                "hold_ids": [hold.id for hold in holds],
                "holds": [party_hold_snapshot(hold) for hold in holds],
                "released_at": str(released_at),
            },
            action_id=action_id,
            correlation_id=action_id,
            occurred_at=released_at,
        )
    session.commit()
    return holds


def inventory_rows(
    session: OrmSession, tenant_id: str, *, item_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    """Derive the same inventory observations with a fixed number of tenant reads.

    `item_ids` narrows every read to the articles the caller can still reach. It
    changes which rows come back, never how one is derived: each article's stock
    is worked out from its own movements, reservations and open supplier promises,
    so a smaller set yields the same rows for the articles it names.
    """
    from reality.services.inventory_positions import movement_legs

    def only(statement, column):
        return statement if item_ids is None else statement.where(column.in_(item_ids))

    items = list(
        session.scalars(
            only(select(Item).where(Item.tenant_id == tenant_id), Item.id).order_by(
                Item.name
            )
        )
    )
    movements_by_item: dict[str, list[Movement]] = {}
    for movement in session.scalars(
        only(
            select(Movement).where(Movement.tenant_id == tenant_id), Movement.item_id
        ).order_by(Movement.occurred_at.desc())
    ):
        movements_by_item.setdefault(movement.item_id, []).append(movement)
    reserved_by_item = dict(
        session.execute(
            only(
                select(Reservation.item_id, func.sum(Reservation.quantity)).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.status == "active",
                ),
                Reservation.item_id,
            ).group_by(Reservation.item_id)
        ).all()
    )
    suppliers = list(
        session.scalars(
            only(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.type == "supplier_delivery",
                    Commitment.status == "open",
                ),
                Commitment.item_id,
            )
        )
    )
    terms = commitment_terms(session, tenant_id, [row.id for row in suppliers])
    incoming_by_item: dict[str, Decimal] = {}
    for commitment in suppliers:
        incoming_by_item[commitment.item_id] = (
            incoming_by_item.get(commitment.item_id, ZERO) + terms[commitment.id].open
        )
    rows = []
    for item in items:
        movements = movements_by_item.get(item.id, [])
        receipts = [movement for movement in movements if movement.to_location_id]
        issues = [movement for movement in movements if movement.from_location_id]
        physical = sum(
            (amount for movement in movements for _, amount in movement_legs(movement)),
            ZERO,
        )
        reserved = decimal(reserved_by_item.get(item.id, ZERO))
        incoming = incoming_by_item.get(item.id, ZERO)
        rows.append(
            {
                "item": item,
                "physical": physical,
                "reserved": reserved,
                "available": physical - reserved,
                "incoming": incoming,
                "projected": physical - reserved + incoming,
                "receipts": receipts,
                "issues": issues,
            }
        )
    return rows


def risk(commitment: Commitment, session: OrmSession) -> str:
    if commitment.type != "customer_delivery" or commitment.status != "open":
        return "OK"
    reserved = decimal(
        session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == commitment.tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
        or ZERO
    )
    return (
        "AT RISK"
        if reserved < open_quantity(session, commitment.tenant_id, commitment.id)
        else "OK"
    )


def name(session: OrmSession, model, record_id: str | None, tenant_id: str) -> str:
    if not record_id:
        return "—"
    record = _tenant_record(session, model, tenant_id, record_id)
    return (
        getattr(record, "name", getattr(record, "sku", record_id))
        if record
        else record_id
    )


def operational_exceptions(
    session: OrmSession, tenant_id: str
) -> list[tuple[str, str, str, str]]:
    """Compatibility tuple view backed by the canonical exception service."""
    from reality.services.exceptions import operational_exception_rows

    return [
        (row["severity"], row["title"], row["id"], row["impact"])
        for row in operational_exception_rows(session, tenant_id)
    ]


# Compatibility for callers deployed before the terminology was clarified.
issues = operational_exceptions


def commitment_rows(
    session: OrmSession, tenant_id: str, commitment_ids: Iterable[str] | None = None
):
    """Every promise with its risk, counterparty, item and reservation, in six reads.

    `commitment_ids` narrows every read to the promises the caller names. It changes
    which rows come back, never how one is derived: each promise's risk, counterparty
    and reservation are worked out from its own records.
    """
    rows = []
    listed = commitments(session, tenant_id, commitment_ids)
    terms = commitment_terms(session, tenant_id, [row.id for row in listed])
    party_ids = {
        row.to_party_id if row.type == "customer_delivery" else row.from_party_id
        for row in listed
    } - {None}
    parties = (
        {
            row.id: row
            for row in session.scalars(
                select(Party).where(
                    Party.tenant_id == tenant_id, Party.id.in_(party_ids)
                )
            )
        }
        if party_ids
        else {}
    )
    item_ids = {row.item_id for row in listed} - {None}
    item_rows = (
        {
            row.id: row
            for row in session.scalars(
                select(Item).where(Item.tenant_id == tenant_id, Item.id.in_(item_ids))
            )
        }
        if item_ids
        else {}
    )

    def label(record, record_id):
        if not record_id:
            return "—"
        return (
            getattr(record, "name", getattr(record, "sku", record_id))
            if record
            else record_id
        )

    for commitment in listed:
        term = terms[commitment.id]
        counterparty_id = (
            commitment.to_party_id
            if commitment.type == "customer_delivery"
            else commitment.from_party_id
        )
        rows.append(
            (
                commitment,
                term.risk
                if commitment.type == "customer_delivery"
                and commitment.status == "open"
                else "OK",
                label(parties.get(counterparty_id), counterparty_id),
                label(item_rows.get(commitment.item_id), commitment.item_id),
                term.reserved,
            )
        )
    return rows


def commitment_control_accounts(
    session: OrmSession, tenant_id: str
) -> list[dict[str, Any]]:
    result = []
    for item in items(session, tenant_id):
        open_commitments = list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.item_id == item.id,
                    Commitment.status == "open",
                )
            )
        )
        incoming = [
            commitment
            for commitment in open_commitments
            if commitment.type == "supplier_delivery"
        ]
        outgoing = [
            commitment
            for commitment in open_commitments
            if commitment.type == "customer_delivery"
        ]
        if not incoming and not outgoing:
            continue
        incoming_quantity = sum(
            (open_quantity(session, tenant_id, entry.id) for entry in incoming), ZERO
        )
        outgoing_quantity = sum(
            (open_quantity(session, tenant_id, entry.id) for entry in outgoing), ZERO
        )
        result.append(
            {
                "item": item,
                "incoming": incoming,
                "outgoing": outgoing,
                "incoming_quantity": incoming_quantity,
                "outgoing_quantity": outgoing_quantity,
                "net": incoming_quantity - outgoing_quantity,
            }
        )
    return result


def document_rows(
    session: OrmSession, tenant_id: str, document_ids: Collection[str] | None = None
):
    """Every document with its source, lines and linked promises, in four reads.

    `document_ids` bounds all four to a named set, for a caller that already knows
    which documents it has to account for. `None` means the whole company.
    """
    scope = [Document.id.in_(document_ids)] if document_ids is not None else []
    documents = list(
        session.scalars(
            select(Document)
            .where(Document.tenant_id == tenant_id, *scope)
            .order_by(Document.document_date, Document.id)
        )
    )
    held = {row.id for row in documents}
    source_ids = {row.source_record_id for row in documents} - {None}
    sources = (
        {
            row.id: row
            for row in session.scalars(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant_id, SourceRecord.id.in_(source_ids)
                )
            )
        }
        if source_ids
        else {}
    )
    lines: dict[str, list[DocumentLine]] = {}
    for line in session.scalars(
        select(DocumentLine)
        .where(
            DocumentLine.tenant_id == tenant_id,
            *([DocumentLine.document_id.in_(held)] if document_ids is not None else []),
        )
        .order_by(DocumentLine.id)
    ):
        lines.setdefault(line.document_id, []).append(line)
    linked: dict[str, list[Commitment]] = {}
    for commitment in session.scalars(
        select(Commitment)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_id.is_not(None),
            *([Commitment.document_id.in_(held)] if document_ids is not None else []),
        )
        .order_by(Commitment.id)
    ):
        linked.setdefault(commitment.document_id, []).append(commitment)
    return [
        (
            document,
            sources.get(document.source_record_id)
            if document.source_record_id
            else None,
            lines.get(document.id, []),
            linked.get(document.id, []),
        )
        for document in documents
    ]


def chat_sessions(
    session: OrmSession,
    tenant_id: str,
    limit: int | None = None,
    offset: int = 0,
    *,
    archived: bool = False,
) -> list[ChatSession]:
    statement = (
        select(ChatSession)
        .where(
            ChatSession.tenant_id == tenant_id,
            ChatSession.archived_at.is_not(None)
            if archived
            else ChatSession.archived_at.is_(None),
        )
        .order_by(ChatSession.updated_at.desc())
    )
    if limit is not None:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)
    return list(session.scalars(statement))


def chat_session_count(session: OrmSession, tenant_id: str) -> int:
    get_tenant(session, tenant_id)
    return int(
        session.scalar(
            select(func.count(ChatSession.id)).where(ChatSession.tenant_id == tenant_id)
        )
        or 0
    )


def chat_message_counts(
    session: OrmSession, tenant_id: str, session_ids: Iterable[str]
) -> dict[str, int]:
    """Return tenant-scoped durable message counts without storing derived state."""
    ids = tuple(session_ids)
    if not ids:
        return {}
    rows = session.execute(
        select(ChatMessage.session_id, func.count(ChatMessage.id))
        .where(
            ChatMessage.tenant_id == tenant_id,
            ChatMessage.session_id.in_(ids),
        )
        .group_by(ChatMessage.session_id)
    )
    return {session_id: int(count) for session_id, count in rows}


def remove_chat_session(session: OrmSession, tenant_id: str, session_id: str) -> None:
    """Delete an empty session or retain a conversation by archiving it."""
    _require_business_mutation(session, tenant_id, "archive_chat_session")
    chat_session = session.scalar(
        select(ChatSession)
        .where(ChatSession.tenant_id == tenant_id, ChatSession.id == session_id)
        .with_for_update()
    )
    if chat_session is None:
        raise NotFound("ChatSession not found.")
    if chat_message_counts(session, tenant_id, (session_id,)).get(session_id, 0):
        chat_session.archived_at = chat_session.archived_at or now()
    else:
        session.delete(chat_session)
    session.commit()


def archive_chat_session(session: OrmSession, tenant_id: str, session_id: str) -> None:
    """Hide one tenant-scoped conversation without removing its audit context."""
    _require_business_mutation(session, tenant_id, "archive_chat_session")
    chat_session = _tenant_record(session, ChatSession, tenant_id, session_id)
    chat_session.archived_at = chat_session.archived_at or now()
    session.commit()


def restore_chat_session(session: OrmSession, tenant_id: str, session_id: str) -> None:
    """Return one retained tenant-scoped conversation to the active list."""
    _require_business_mutation(session, tenant_id, "restore_chat_session")
    chat_session = _tenant_record(session, ChatSession, tenant_id, session_id)
    chat_session.archived_at = None
    session.commit()


# Transitional name for callers while DELETE retains its HTTP compatibility.
delete_chat_session = remove_chat_session


def _change_proposal_conditions(
    tenant_id: str, pending: bool, query: str, tool: str = ""
):
    statuses = ("proposed",) if pending else ("executed", "rejected")
    conditions = [
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.status.in_(statuses),
    ]
    if tool:
        conditions.append(ChangeProposal.type == f"tool:{tool}")
    term = query.strip().lower()
    if term:
        conditions.append(
            or_(
                func.lower(ChangeProposal.type).like(f"%{term}%"),
                func.lower(ChangeProposal.input).like(f"%{term}%"),
            )
        )
    return conditions


def decision_maker_names(
    session: OrmSession, tenant_id: str, user_ids: Iterable[str | None]
) -> dict[str, str]:
    """Name the people who settled this tenant's decisions.

    Only a user who actually decided one of this tenant's change proposals is
    resolved, so the register cannot be turned into a directory of everyone.
    """
    wanted = {user_id for user_id in user_ids if user_id}
    if not wanted:
        return {}
    rows = session.execute(
        select(AppUser.id, AppUser.display_name, AppUser.email)
        .join(ChangeProposal, ChangeProposal.decided_by_user_id == AppUser.id)
        .where(ChangeProposal.tenant_id == tenant_id, AppUser.id.in_(wanted))
        .distinct()
    ).all()
    return {row.id: (row.display_name.strip() or row.email) for row in rows}


def change_proposals(
    session: OrmSession,
    tenant_id: str,
    *,
    pending: bool,
    query: str = "",
    tool: str = "",
    offset: int = 0,
    limit: int | None = None,
) -> list[ChangeProposal]:
    """List the tenant decision queue without coupling it to Chat presentation.

    Decision history only grows, so the caller slices it in the database. The
    identifier breaks ties so a page boundary can neither repeat nor skip a row
    when two decisions share a timestamp.
    """
    statement = (
        select(ChangeProposal)
        .where(*_change_proposal_conditions(tenant_id, pending, query, tool))
        .order_by(
            ChangeProposal.created_at.asc()
            if pending
            else ChangeProposal.created_at.desc(),
            ChangeProposal.id.asc() if pending else ChangeProposal.id.desc(),
        )
        .offset(offset)
    )
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.scalars(statement))


def change_proposal_count(
    session: OrmSession,
    tenant_id: str,
    *,
    pending: bool,
    query: str = "",
    tool: str = "",
) -> int:
    """Count the same tenant decision queue the paged reader returns."""
    return int(
        session.scalar(
            select(func.count())
            .select_from(ChangeProposal)
            .where(*_change_proposal_conditions(tenant_id, pending, query, tool))
        )
        or 0
    )


def get_chat_session(
    session: OrmSession, tenant_id: str, session_id: str
) -> ChatSession:
    """Validate the conversation scope without loading its messages."""
    return _tenant_record(session, ChatSession, tenant_id, session_id)


def chat_messages(
    session: OrmSession, tenant_id: str, session_id: str
) -> list[ChatMessage]:
    get_chat_session(session, tenant_id, session_id)
    return list(
        session.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.tenant_id == tenant_id,
                ChatMessage.session_id == session_id,
            )
            .order_by(ChatMessage.created_at)
        )
    )


def chat_suggestions(session: OrmSession, tenant_id: str) -> list[dict[str, object]]:
    get_tenant(session, tenant_id)
    has_parties = bool(
        session.scalar(select(func.count(Party.id)).where(Party.tenant_id == tenant_id))
    )
    suggestions: list[dict[str, object]] = []
    if not has_parties:
        suggestions.append(
            {
                "category": "Guided demo",
                "label": "Build the demo company",
                "description": "Create source, evidence, stock and promises after confirmation.",
                "message": "start demo",
            }
        )
    suggestions.append(
        {
            "category": "Full scenario",
            "label": "Run September 2026 business month",
            "description": (
                "Run O2C, P2P, shortage, receipts, shipments, return, invoice, "
                "payment and credit."
                if not has_parties
                else "This full scenario needs an empty tenant. Create or select an "
                "empty tenant first."
            ),
            "message": "run normal month",
            "disabled": has_parties,
        }
    )
    suggestions.extend(
        [
            {
                "category": "Learn the model",
                "label": "Explain Source → Evidence → Reality",
                "description": "Understand how raw input becomes documents and operational truth.",
                "message": "Explain Source Evidence Reality",
            },
            {
                "category": "Learn the model",
                "label": "Why are documents not the center?",
                "description": "See why fulfillment is derived from commitments and movements.",
                "message": "Why are documents not operational status?",
            },
        ]
    )
    if not has_parties:
        return suggestions
    suggestions.extend(
        [
            {
                "category": "Understand",
                "label": "Explain inventory",
                "description": "Show physical, reserved, available and incoming quantities.",
                "message": "Show inventory",
            },
            {
                "category": "Operate",
                "label": "Show fulfillment risks",
                "description": "Find customer promises that are not sufficiently reserved.",
                "message": "Show delivery risk",
            },
            {
                "category": "Evidence",
                "label": "Show interpreted documents",
                "description": "List evidence records and whether they have source payloads.",
                "message": "List interpreted documents",
            },
            {
                "category": "Operations",
                "label": "Summarize commitments",
                "description": "Show incoming and outgoing promises with their current state.",
                "message": "Summarize commitments",
            },
            {
                "category": "Finance",
                "label": "Show open financial positions",
                "description": "Derive receivables and payables from ledger entries.",
                "message": "Show open receivables and payables",
            },
        ]
    )
    reservable = next(
        (
            commitment
            for commitment in commitments(session, tenant_id)
            if commitment.type == "customer_delivery"
            and commitment.status == "open"
            and risk(commitment, session) == "AT RISK"
        ),
        None,
    )
    if reservable:
        suggestions.append(
            {
                "category": "Try an action",
                "label": "Reserve available stock",
                "description": f"Prepare a confirmed reservation for {reservable.id}.",
                "message": f"reserve {reservable.id}",
            }
        )
    return suggestions


def create_chat_session(session: OrmSession, tenant_id: str) -> ChatSession:
    _require_business_mutation(session, tenant_id, "create_chat_session")
    get_tenant(session, tenant_id)
    chat_session = ChatSession(
        id=uid("cht"), tenant_id=tenant_id, title="New conversation"
    )
    session.add(chat_session)
    session.commit()
    return chat_session


def add_chat_assistant_message(
    session: OrmSession, tenant_id: str, session_id: str, content: str
) -> ChatMessage:
    _require_business_mutation(session, tenant_id, "add_chat_assistant_message")
    chat_session = _tenant_record(session, ChatSession, tenant_id, session_id)
    message = ChatMessage(
        id=uid("msg"),
        tenant_id=tenant_id,
        session_id=session_id,
        role="assistant",
        content=content,
    )
    chat_session.updated_at = now()
    session.add(message)
    session.commit()
    return message


@wrap_chat
def send_chat_message(
    session: OrmSession,
    tenant_id: str,
    session_id: str,
    message: str,
    *,
    actor_user_id: str | None = None,
    context_commitment_id: str | None = None,
    language: str = "en",
    locale: str = "en-GB",
    timezone: str = "UTC",
    on_event: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[ChatMessage, ChatMessage]:
    _require_business_mutation(session, tenant_id, "send_chat_message")
    turn_outcome = "fallback"
    turn_started = time.perf_counter()
    if not message.strip():
        raise InvalidOperation("Enter a question.")
    chat_session = _tenant_record(session, ChatSession, tenant_id, session_id)
    context_prefix = "\x1ereality.context.v1:"
    if message.startswith(context_prefix):
        raise InvalidOperation("Context annotations are created by the server.")
    original_message = message
    stored_message = message
    if context_commitment_id:
        commitment = _tenant_record(
            session, Commitment, tenant_id, context_commitment_id
        )
        if commitment.type != "customer_delivery":
            raise InvalidOperation(
                "Select a customer delivery for contextual assistance."
            )
        stored_message = context_prefix + json.dumps(
            {
                "commitment_id": commitment.id,
                "message": message,
                "label": f"{name(session, Party, commitment.to_party_id, tenant_id)} · {name(session, Item, commitment.item_id, tenant_id)}",
            }
        )
        from reality.services.delivery_reads import delivery_case

        snapshot = delivery_case(session, tenant_id, commitment.id)
        message = f"Selected delivery observations: {json.dumps(snapshot, default=str)}\nQuestion: {original_message}"
    user_message = ChatMessage(
        id=uid("msg"),
        tenant_id=tenant_id,
        session_id=session_id,
        role="user",
        content=stored_message,
    )
    from reality.agent.settings import configured_api_key, has_configured_api_key

    ai_configuration = session.get(AISettings, tenant_id)
    own_provider = (
        ai_configuration
        if ai_configuration
        and ai_configuration.provider in {"anthropic", "openai_compatible"}
        and has_configured_api_key(ai_configuration)
        else None
    )
    managed_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    managed_workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()
    if own_provider or managed_key:
        import asyncio

        from reality.agent.mcp_chat import reply_via_anthropic_tools, reply_via_tools

        recent_messages = list(
            session.scalars(
                select(ChatMessage)
                .where(
                    ChatMessage.tenant_id == tenant_id,
                    ChatMessage.session_id == session_id,
                )
                .order_by(
                    ChatMessage.created_at.desc(),
                    case((ChatMessage.role == "assistant", 1), else_=0).desc(),
                    ChatMessage.id.desc(),
                )
                .limit(12)
            )
        )
        history = [
            {"role": row.role, "content": row.content}
            for row in reversed(recent_messages)
        ]
        from reality.services.tenant_policy import PlaygroundOperationDenied

        if not own_provider:
            from reality.services.free_playground import reserve_managed_question

            reserve_managed_question(session, tenant_id, actor_user_id)
        try:
            if own_provider and own_provider.provider == "openai_compatible":
                provider_reply = reply_via_tools(
                    session=session,
                    tenant_id=tenant_id,
                    api_key=configured_api_key(own_provider),
                    model=own_provider.model,
                    base_url=own_provider.base_url,
                    history=history,
                    message=message,
                    language=language,
                    locale=locale,
                    timezone=timezone,
                    **({"on_event": on_event} if on_event else {}),
                )
            else:
                provider_reply = reply_via_anthropic_tools(
                    session=session,
                    tenant_id=tenant_id,
                    api_key=configured_api_key(own_provider)
                    if own_provider
                    else managed_key,
                    workspace_id="" if own_provider else managed_workspace_id,
                    history=history,
                    message=message,
                    language=language,
                    locale=locale,
                    timezone=timezone,
                    **({"on_event": on_event} if on_event else {}),
                )
            reply = asyncio.run(provider_reply)
            # An empty reply falls through to the deterministic keyword chain
            # below, so it is a fallback turn however it was produced.
            turn_outcome = "model" if reply else "fallback"
        # A policy refusal is not an outage: say which company kind is closed
        # and why (feature 169). Provider, transport, protocol and tool failures
        # degrade to a safe user-visible response; no exception escapes here.
        except PlaygroundOperationDenied as error:
            reply = f"The Copilot is not available for this company: {error}"
            turn_outcome = "denied"
        except InvalidOperation as error:
            # A refusal is a sentence somebody wrote for a reader: the question
            # was understood and cannot be answered that way. Replacing it with
            # "try again later" turns a correct answer into an apparent outage,
            # and the reader retries something that will never work.
            reply = str(error)
            turn_outcome = "refused"
        except Exception as error:
            # Whatever this was, the class name alone is not enough to fix it.
            logging.getLogger(__name__).exception("copilot turn failed")
            reply = (
                "The managed Copilot could not answer right now. "
                f"Please try again later ({type(error).__name__})."
            )
            turn_outcome = "provider_error"
    else:
        reply = ""
    if context_commitment_id and not own_provider and not managed_key:
        reply = "No AI provider is connected. You can still inspect the delivery and use its actions."
        turn_outcome = "no_provider"
    normalized = original_message.lower()
    parts = original_message.split()
    if reply:
        pass
    elif normalized in {"run normal month", "monatslauf starten", "normal month"}:
        from reality.tools.application import propose_tool

        proposal = propose_tool(session, tenant_id, "normal_month", {})
        reply = (
            f"Prepared September 2026 scenario proposal {proposal.id}. "
            "Confirm it to run the same normal-month service used by the CLI."
        )
    elif normalized in {"start demo", "demo starten"}:
        from reality.tools.application import propose_tool

        proposal = propose_tool(session, tenant_id, "demo_seed", {})
        reply = (
            f"Prepared demo proposal {proposal.id}. "
            "Confirm it to create the demo company using shared services."
        )
    elif len(parts) in {2, 3} and parts[0].lower() in {"reserve", "reserviere"}:
        from reality.tools.application import propose_tool

        arguments = {"commitment_id": parts[1]}
        if len(parts) == 3:
            arguments["quantity"] = parts[2]
        proposal = propose_tool(session, tenant_id, "reserve", arguments)
        reply = (
            f"Prepared reservation proposal {proposal.id}. "
            "Review and confirm it before any stock is allocated."
        )
    elif any(word in normalized for word in ["liefer", "ship", "risk"]):
        current_exceptions = operational_exceptions(session, tenant_id)
        reply = (
            "Current operational risks:\n"
            + "\n".join(
                f"• {exception[2]} — {exception[3]}" for exception in current_exceptions
            )
            if current_exceptions
            else "No current fulfillment risks."
        )
    elif any(word in normalized for word in ["bestand", "stock", "inventory"]):
        reply = "Inventory:\n" + "\n".join(
            f"• {row['item'].name}: physical {row['physical']:g}, reserved {row['reserved']:g}, available {row['available']:g}, incoming {row['incoming']:g}"
            for row in inventory_rows(session, tenant_id)
        )
    elif "source" in normalized and "evidence" in normalized:
        reply = (
            "Source → Evidence → Reality:\n"
            "• SourceRecord preserves the external payload losslessly.\n"
            "• Document and DocumentLine are normalized evidence.\n"
            "• Commitments, reservations, movements and ledger entries represent business reality.\n"
            "The links use opaque IDs, so every conclusion can be traced back to its source."
        )
    elif "documents not" in normalized or "dokumente" in normalized:
        reply = (
            "Documents are evidence, not operational state. A sales order does not store "
            "delivery or reservation status. Fulfillment comes from Movements linked to a "
            "Commitment; availability comes from Movements minus active Reservations."
        )
    elif "document" in normalized or "evidence" in normalized:
        rows = document_rows(session, tenant_id)
        reply = (
            "Evidence documents:\n"
            + "\n".join(
                f"• {document.type} {document.number}: {len(lines)} line(s), "
                f"{len(linked)} commitment(s), source {source.external_id if source else '—'}"
                for document, source, lines, linked in rows
            )
            if rows
            else "No evidence documents exist yet."
        )
    elif "commitment" in normalized or "promise" in normalized:
        current = commitments(session, tenant_id)
        reply = (
            "Commitments:\n"
            + "\n".join(
                f"• {record.type}: {record.quantity:g} × "
                f"{name(session, Item, record.item_id, tenant_id)} · {record.status} · due {record.due_at}"
                for record in current
            )
            if current
            else "No commitments exist yet."
        )
    elif any(word in normalized for word in ["receivable", "payable", "finance"]):
        receivable = account_balance(session, tenant_id, "accounts_receivable")
        payable = -account_balance(session, tenant_id, "accounts_payable")
        reply = (
            "Open financial positions derived from LedgerEntries:\n"
            f"• Customer receivables: EUR {receivable:g}\n"
            f"• Supplier payables: EUR {payable:g}"
        )
    elif not own_provider and not managed_key:
        reply = (
            "AI is not configured for this company. Add an Anthropic API key in "
            "AI configuration, then ask again."
        )
        turn_outcome = "no_provider"
    else:
        reply = "V0 local agent: ask about inventory or fulfillment risk."
    # Set where the reply is produced, not sniffed from its text: the string
    # is user-facing copy and a copy edit would silently flip the metric.
    _record_copilot_turn(
        own_provider, managed_key, turn_outcome, time.perf_counter() - turn_started
    )
    assistant_message = ChatMessage(
        id=uid("msg"),
        tenant_id=tenant_id,
        session_id=session_id,
        role="assistant",
        content=reply,
    )
    session.add_all([user_message, assistant_message])
    chat_session.updated_at = now()
    if chat_session.title == "New conversation":
        chat_session.title = message[:42]
    session.commit()
    return user_message, assistant_message


def create_document(
    session: OrmSession,
    tenant_id: str,
    document_type: str,
    number: str,
    party_id: str,
    amount: Decimal | float | str,
    *,
    currency: str = "EUR",
    document_date: str = "",
    source_record_id: str | None = None,
    ordered_at: datetime | str | None = None,
    requested_delivery_at: datetime | str | None = None,
    customer_reference: str = "",
    sales_channel: str = "",
    payment_term_code: str = "",
    ship_to_party_id: str | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> Document:
    _require_business_mutation(session, tenant_id, "create_document")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Party, tenant_id, party_id)
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    if ship_to_party_id:
        _tenant_record(session, Party, tenant_id, ship_to_party_id)
    document = Document(
        id=uid("doc"),
        tenant_id=tenant_id,
        source_record_id=source_record_id,
        type=document_type,
        number=number,
        party_id=party_id,
        currency=currency,
        gross_amount=decimal(amount),
        status="recorded",
        document_date=_document_day(document_date),
        ordered_at=utc_datetime(ordered_at),
        requested_delivery_at=utc_datetime(requested_delivery_at),
        customer_reference=customer_reference.strip(),
        sales_channel=sales_channel.strip(),
        payment_term_id=(
            payment_term_by_code(session, tenant_id, payment_term_code).id
            if payment_term_code.strip()
            else None
        ),
        ship_to_party_id=ship_to_party_id,
    )
    session.add(document)
    emit_business_event(
        session,
        tenant_id,
        "document.recorded",
        "document",
        document.id,
        {
            "type": document.type,
            "number": document.number,
            "party_id": party_id,
            "amount": document.gross_amount,
            "currency": document.currency,
        },
        source_record_id=source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return document


def _preview_manual_document_input(
    session: OrmSession,
    tenant_id: str,
    document_type: str,
    number: str,
    party_id: str,
    lines: list[dict[str, Any]],
    gross_amount: Decimal | float | str,
    *,
    currency: str = "EUR",
    document_date: str = "",
    ordered_at: datetime | str | None = None,
    requested_delivery_at: datetime | str | None = None,
    customer_reference: str = "",
    sales_channel: str = "",
    payment_term_code: str = "",
    ship_to_party_id: str | None = None,
    source_record_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Pure normalization shared by document recording and order review."""
    document_type, number, currency = (
        document_type.strip(),
        number.strip(),
        currency.strip().upper(),
    )
    if not document_type or not number or not party_id or not currency:
        raise InvalidOperation("Type, number, party, and currency are required.")
    _tenant_record(session, Party, tenant_id, party_id)
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    if ship_to_party_id:
        _tenant_record(session, Party, tenant_id, ship_to_party_id)
    if not lines:
        raise InvalidOperation("A manual document requires at least one line.")

    if gross_amount is None or str(gross_amount).strip() == "":
        # A total that disagrees with the lines is the finding, so it is stated
        # rather than derived. See Constitution principle VIII.
        raise InvalidOperation(
            "A manual document requires a stated total; it is never calculated."
        )

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(lines, start=1):
        normalized.append(
            _normalize_manual_line_input(session, tenant_id, document_type, raw, index)
        )

    selected_rows = [row for row in normalized if row["price_list_entry_id"]]
    if selected_rows:
        effective_at = _document_pricing_effective_at(
            ordered_at=ordered_at, document_date=document_date
        )
        for row in selected_rows:
            _validate_selected_price_entry(
                session,
                tenant_id,
                document_type=document_type,
                party_id=party_id,
                currency=currency,
                line=row,
                at=effective_at,
            )

    values = {
        "type": document_type,
        "number": number,
        "party_id": party_id,
        "currency": currency,
        "gross_amount": decimal(gross_amount),
        "status": "recorded",
        "document_date": _document_day(document_date),
        "ordered_at": utc_datetime(ordered_at),
        "requested_delivery_at": utc_datetime(requested_delivery_at),
        "customer_reference": customer_reference.strip(),
        "sales_channel": sales_channel.strip(),
        "payment_term_id": (
            payment_term_by_code(session, tenant_id, payment_term_code).id
            if payment_term_code.strip()
            else None
        ),
        "ship_to_party_id": ship_to_party_id,
    }
    return values, normalized


def create_manual_document_with_lines(
    session: OrmSession,
    tenant_id: str,
    document_type: str,
    number: str,
    party_id: str,
    lines: list[dict[str, Any]],
    gross_amount: Decimal | float | str,
    *,
    action_id: str | None = None,
    currency: str = "EUR",
    document_date: str = "",
    ordered_at: datetime | str | None = None,
    requested_delivery_at: datetime | str | None = None,
    customer_reference: str = "",
    sales_channel: str = "",
    payment_term_code: str = "",
    ship_to_party_id: str | None = None,
    source_record_id: str | None = None,
    _commit: bool = True,
) -> tuple[Document, list[DocumentLine]]:
    """Atomically record manual document evidence and its normalized lines.

    This deliberately creates evidence only. Operational commitments are created
    through their explicit application command, rather than being guessed from a
    manually entered document type.
    """
    _require_business_mutation(session, tenant_id, "create_manual_document_with_lines")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    values, normalized = _preview_manual_document_input(
        session,
        tenant_id,
        document_type,
        number,
        party_id,
        lines,
        gross_amount,
        currency=currency,
        document_date=document_date,
        ordered_at=ordered_at,
        requested_delivery_at=requested_delivery_at,
        customer_reference=customer_reference,
        sales_channel=sales_channel,
        payment_term_code=payment_term_code,
        ship_to_party_id=ship_to_party_id,
        source_record_id=source_record_id,
    )
    document = Document(
        id=uid("doc"), tenant_id=tenant_id, source_record_id=source_record_id, **values
    )
    session.add(document)
    session.flush()
    created_lines = [
        DocumentLine(
            id=uid("lin"),
            tenant_id=tenant_id,
            document_id=document.id,
            source_line_id=row["source_line_id"],
            item_id=row["item_id"],
            sku=row["sku"],
            description=row["description"],
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            gross_amount=row["gross_amount"],
            promised_at=row["promised_at"],
            payload=json.dumps(
                {"reality_finance_v1": row["reality_finance_v1"]},
                sort_keys=True,
            )
            if row["reality_finance_v1"] is not None
            else "{}",
            unit=row["unit"],
            requested_at=utc_datetime(row["promised_at"]),
            line_type=row["line_type"],
            price_list_entry_id=row["price_list_entry_id"],
            billed_document_line_id=row["billed_document_line_id"],
        )
        for row in normalized
    ]
    session.add_all(created_lines)
    emit_business_event(
        session,
        tenant_id,
        "document.recorded",
        "document",
        document.id,
        {
            "type": document.type,
            "number": document.number,
            "party_id": party_id,
            "amount": document.gross_amount,
            "currency": document.currency,
            "line_count": len(created_lines),
            "document_line_ids": [line.id for line in created_lines],
            "origin": "manual",
        },
        source_record_id=source_record_id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return document, created_lines


def _preview_manual_order(
    session: OrmSession,
    tenant_id: str,
    arguments: dict[str, Any],
    *,
    check_existing: bool = True,
) -> dict[str, Any]:
    """Validate one agreement without allocating IDs or writing business records."""
    required = {
        "direction",
        "number",
        "company_party_id",
        "counterparty_id",
        "location_id",
        "lines",
        "gross_amount",
    }
    optional = {
        "currency",
        "document_date",
        "ordered_at",
        "requested_delivery_at",
        "customer_reference",
        "sales_channel",
        "payment_term_code",
        "ship_to_party_id",
    }
    if set(arguments) - required - optional or required - set(arguments):
        raise InvalidOperation("The order has missing or unsupported fields.")
    if not isinstance(arguments["direction"], str):
        raise InvalidOperation("Order direction must be sales or purchase.")
    direction = arguments["direction"].strip().lower()
    if direction not in {"sales", "purchase"}:
        raise InvalidOperation("Order direction must be sales or purchase.")
    lines = arguments["lines"]
    if (
        not isinstance(lines, list)
        or not lines
        or any(not isinstance(line, dict) for line in lines)
    ):
        raise InvalidOperation("An order requires at least one item line.")
    if arguments.get("document_date"):
        try:
            date.fromisoformat(arguments["document_date"])
        except (TypeError, ValueError) as error:
            raise InvalidOperation("Document date must use YYYY-MM-DD.") from error
    for model, key in (
        (Party, "company_party_id"),
        (Party, "counterparty_id"),
        (Location, "location_id"),
    ):
        _tenant_record(session, model, tenant_id, arguments[key])
    try:
        values, normalized = _preview_manual_document_input(
            session,
            tenant_id,
            "sales_order" if direction == "sales" else "purchase_order",
            arguments["number"],
            arguments["counterparty_id"],
            lines,
            arguments["gross_amount"],
            **{key: arguments[key] for key in optional if key in arguments},
        )
        for line in normalized:
            _tenant_record(session, Item, tenant_id, line["item_id"])
    except (TypeError, ValueError, ArithmeticError, AttributeError) as error:
        raise InvalidOperation("The order contains an invalid value.") from error
    if check_existing:
        payload = {
            "currency": "EUR",
            "document_date": "",
            "ordered_at": None,
            "requested_delivery_at": None,
            "customer_reference": "",
            "sales_channel": "",
            "payment_term_code": "",
            "ship_to_party_id": None,
            **arguments,
        }
        payload = json.loads(json.dumps(payload, default=str))
        existing = session.scalar(
            select(Document.id)
            .join(SourceRecord, Document.source_record_id == SourceRecord.id)
            .where(
                Document.tenant_id == tenant_id,
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == "manual",
                SourceRecord.source_type == values["type"],
                SourceRecord.external_id == values["number"],
                Document.type == values["type"],
                SourceRecord.payload_hash == canonical_payload_hash(payload),
            )
        )
        if existing:
            raise InvalidOperation(
                "This exact order is already recorded. Open the existing order instead."
            )
    return {"document": values, "lines": normalized, "direction": direction}


def create_manual_order(
    session: OrmSession,
    tenant_id: str,
    direction: str,
    number: str,
    company_party_id: str,
    counterparty_id: str,
    location_id: str,
    lines: list[dict[str, Any]],
    gross_amount: Decimal | float | str,
    *,
    action_id: str | None = None,
    currency: str = "EUR",
    document_date: str = "",
    ordered_at: datetime | str | None = None,
    requested_delivery_at: datetime | str | None = None,
    customer_reference: str = "",
    sales_channel: str = "",
    payment_term_code: str = "",
    ship_to_party_id: str | None = None,
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Commitment]]:
    """Atomically turn one manual order payload into Evidence and Reality."""
    _require_business_mutation(session, tenant_id, "create_manual_order")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    _tenant_record(session, Party, tenant_id, company_party_id)
    _tenant_record(session, Party, tenant_id, counterparty_id)
    _tenant_record(session, Location, tenant_id, location_id)
    payload = {
        "direction": direction,
        "number": number,
        "company_party_id": company_party_id,
        "counterparty_id": counterparty_id,
        "location_id": location_id,
        "currency": currency,
        "gross_amount": str(gross_amount)
        if isinstance(gross_amount, Decimal)
        else gross_amount,
        "document_date": document_date,
        "ordered_at": str(ordered_at) if ordered_at is not None else None,
        "requested_delivery_at": (
            str(requested_delivery_at) if requested_delivery_at is not None else None
        ),
        "customer_reference": customer_reference,
        "sales_channel": sales_channel,
        "payment_term_code": payment_term_code,
        "ship_to_party_id": ship_to_party_id,
        "lines": lines,
    }
    preview = _preview_manual_order(session, tenant_id, payload)
    direction = preview["direction"]
    document_type = preview["document"]["type"]
    try:
        source = create_master_source_record(
            session,
            tenant_id,
            document_type,
            "manual",
            number,
            payload,
            _commit=False,
            action_id=action_id,
        )
        if source is None:  # pragma: no cover - manual source identity is complete
            raise InvalidOperation("Manual order source could not be recorded.")
        document, document_lines = create_manual_document_with_lines(
            session,
            tenant_id,
            document_type,
            number,
            counterparty_id,
            lines,
            gross_amount,
            currency=currency,
            document_date=document_date,
            ordered_at=ordered_at,
            requested_delivery_at=requested_delivery_at,
            customer_reference=customer_reference,
            sales_channel=sales_channel,
            payment_term_code=payment_term_code,
            ship_to_party_id=ship_to_party_id,
            source_record_id=source.id,
            _commit=False,
            action_id=action_id,
        )
        commitments = []
        for line in document_lines:
            commitments.append(
                create_commitment(
                    session,
                    tenant_id,
                    "customer_delivery"
                    if direction == "sales"
                    else "supplier_delivery",
                    company_party_id if direction == "sales" else counterparty_id,
                    counterparty_id if direction == "sales" else company_party_id,
                    line.item_id,
                    location_id,
                    line.quantity,
                    line.requested_at or requested_delivery_at,
                    amount=line.gross_amount,
                    currency=currency,
                    document_id=document.id,
                    document_line_id=line.id,
                    _commit=False,
                    action_id=action_id,
                )
            )
        emit_business_event(
            session,
            tenant_id,
            "order.recorded",
            "document",
            document.id,
            {
                "creation": preview,
                "commitments": [
                    {
                        key: getattr(commitment, key)
                        for key in (
                            "id",
                            "type",
                            "from_party_id",
                            "to_party_id",
                            "item_id",
                            "location_id",
                            "quantity",
                            "amount",
                            "currency",
                            "due_at",
                            "document_id",
                            "document_line_id",
                        )
                    }
                    for commitment in commitments
                ],
                "receipt": {
                    "source_record_id": source.id,
                    "document_id": document.id,
                    "document_line_ids": [line.id for line in document_lines],
                    "commitment_ids": [commitment.id for commitment in commitments],
                },
            },
            source_record_id=source.id,
            action_id=action_id,
            correlation_id=action_id,
        )
        session.commit()
        return source, document, document_lines, commitments
    except Exception:
        session.rollback()
        raise


_LINE_DECIMAL_QUANTUM = Decimal("0.0001")
_LINE_ECONOMIC_FIELDS = {
    "item_id",
    "quantity",
    "unit",
    "unit_price",
    "gross_amount",
    "promised_at",
    "line_type",
    "price_list_entry_id",
    "billed_document_line_id",
}


def _pricing_direction(document_type: str) -> str | None:
    # A credit note gives money back to a customer, so it belongs on the selling
    # side and may credit a sales order line. Supplier credit notes are a
    # separate flow and are not expressed by this type.
    if document_type.startswith("sales_") or document_type == "credit_note":
        return "sales"
    if document_type.startswith(("purchase_", "supplier_")):
        return "purchase"
    return None


def _document_day(value: date | datetime | str | None) -> date | None:
    """A stated document date, refused as a business error rather than a crash.

    The column takes a day, so text that is not one cannot be stored. Callers reach
    this through the tools and the API, where an unreadable date is the asker's
    mistake and belongs in a 422, not in a traceback.
    """
    try:
        return as_day(value)
    except InvalidDay as error:
        raise InvalidOperation("Document date must use YYYY-MM-DD.") from error


def _document_pricing_effective_at(
    *, ordered_at: datetime | str | None, document_date: date | str | None
) -> datetime:
    ordered = utc_datetime(ordered_at)
    if ordered:
        return ordered
    day = _document_day(document_date)
    if day:
        return datetime.combine(day, datetime.min.time(), UTC)
    return now()


def _validate_selected_price_entry(
    session: OrmSession,
    tenant_id: str,
    *,
    document_type: str,
    party_id: str,
    currency: str,
    line: dict[str, Any],
    at: datetime,
) -> None:
    entry_id = line["price_list_entry_id"]
    if not entry_id:
        return
    _tenant_record(session, PriceListEntry, tenant_id, entry_id)
    direction = _pricing_direction(document_type)
    if direction is None or not line["item_id"]:
        raise InvalidOperation(
            "A selected price entry requires a supported commercial document and item."
        )
    selected = resolve_price(
        session,
        tenant_id,
        party_id,
        line["item_id"],
        line["quantity"],
        direction,
        currency,
        line["unit"],
        at=at,
    )
    if (
        selected is None
        or selected.price_list_entry_id != entry_id
        or selected.unit_price != line["unit_price"]
        or selected.currency != currency
        or selected.unit != line["unit"]
    ):
        raise InvalidOperation(
            "Selected price entry does not reproduce the agreed line context."
        )


def _line_decimal_text(value: Decimal | float | str) -> str:
    return format(decimal(value).quantize(_LINE_DECIMAL_QUANTUM), "f")


def _validate_billed_document_line(
    session: OrmSession,
    tenant_id: str,
    document_type: str,
    billed_document_line_id: str,
) -> str:
    """Refuse a reference that would produce a confidently wrong exception."""
    billed = _tenant_record(session, DocumentLine, tenant_id, billed_document_line_id)
    agreed_document = _tenant_record(session, Document, tenant_id, billed.document_id)
    if document_type == "credit_note" and agreed_document.type == "sales_invoice":
        return billed.id
    if agreed_document.type not in {"sales_order", "purchase_order"}:
        raise InvalidOperation("A billed reference must point at an order line.")
    if _pricing_direction(agreed_document.type) != _pricing_direction(document_type):
        raise InvalidOperation(
            "A billed reference must stay on one side of the business."
        )
    return billed.id


def _normalize_manual_line_input(
    session: OrmSession,
    tenant_id: str,
    document_type: str,
    raw: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    item_id = str(raw.get("item_id") or "").strip() or None
    item = _tenant_record(session, Item, tenant_id, item_id) if item_id else None
    quantity = positive(raw.get("quantity", 0))
    unit_price = decimal(raw.get("unit_price", 0))
    raw_total = raw.get("gross_amount")
    if raw_total is None or str(raw_total).strip() == "":
        # Never quantity times unit price: a rebate or the source's own rounding
        # makes that product wrong, and recomputing it would hide the difference.
        raise InvalidOperation(
            f"Line {index} requires a stated amount; it is never calculated."
        )
    gross_amount = decimal(raw_total)
    unit = str(raw.get("unit") or (item.unit if item else "pcs")).strip()
    line_type = str(raw.get("line_type") or "item").strip()
    if not unit or not line_type:
        raise InvalidOperation("Line unit and type are required.")
    promised_at = str(raw.get("promised_at") or "").strip()
    utc_datetime(promised_at)
    billed_document_line_id = (
        str(raw.get("billed_document_line_id") or "").strip() or None
    )
    if billed_document_line_id:
        billed_document_line_id = _validate_billed_document_line(
            session, tenant_id, document_type, billed_document_line_id
        )
    finance_detail = raw.get("reality_finance_v1")
    if finance_detail is not None and not isinstance(finance_detail, dict):
        raise InvalidOperation("Received finance line detail must be an object.")
    return {
        "id": str(raw.get("id") or "").strip() or None,
        "source_line_id": str(raw.get("source_line_id") or index).strip(),
        "item_id": item.id if item else None,
        "sku": str(raw.get("sku") or (item.sku if item else "")).strip(),
        "description": str(
            raw.get("description") or (item.name if item else "")
        ).strip(),
        "quantity": quantity,
        "unit_price": unit_price,
        "gross_amount": gross_amount,
        "promised_at": promised_at,
        "unit": unit,
        "line_type": line_type,
        "price_list_entry_id": (
            str(raw.get("price_list_entry_id") or "").strip() or None
        ),
        "billed_document_line_id": billed_document_line_id,
        "reality_finance_v1": finance_detail,
    }


def _stored_manual_line(line: DocumentLine) -> dict[str, Any]:
    payload = json.loads(line.payload or "{}")
    return {
        "id": line.id,
        "source_line_id": line.source_line_id or "",
        "item_id": line.item_id,
        "sku": line.sku,
        "description": line.description,
        "quantity": line.quantity,
        "unit_price": line.unit_price,
        "gross_amount": line.gross_amount,
        "promised_at": line.promised_at,
        "unit": line.unit,
        "line_type": line.line_type,
        "price_list_entry_id": line.price_list_entry_id,
        "billed_document_line_id": line.billed_document_line_id,
        "reality_finance_v1": payload.get("reality_finance_v1"),
    }


def historical_pricing_explanation(
    session: OrmSession,
    tenant_id: str,
    document_line_id: str,
    *,
    at: datetime | str | None = None,
) -> dict[str, Any]:
    """Explain immutable agreed pricing beside a fresh pricing resolution."""
    line = _tenant_record(session, DocumentLine, tenant_id, document_line_id)
    document = _tenant_record(session, Document, tenant_id, line.document_id)
    retained_entry = (
        _tenant_record(session, PriceListEntry, tenant_id, line.price_list_entry_id)
        if line.price_list_entry_id
        else None
    )
    retained_list = (
        _tenant_record(session, PriceList, tenant_id, retained_entry.price_list_id)
        if retained_entry
        else None
    )
    compared_at = utc_datetime(at) or now()
    direction = _pricing_direction(document.type)
    unavailable_reason: str | None = None
    current: PriceResult | None = None
    if not direction:
        unavailable_reason = "Unsupported commercial document direction."
    elif not line.item_id:
        unavailable_reason = "The agreed line has no item identity."
    elif not document.party_id:
        unavailable_reason = "The document has no party identity."
    else:
        current = resolve_price(
            session,
            tenant_id,
            document.party_id,
            line.item_id,
            line.quantity,
            direction,
            document.currency,
            line.unit,
            at=compared_at,
        )
        if current is None:
            unavailable_reason = "No price resolves for the current context."

    changed = bool(
        current
        and (
            current.unit_price != line.unit_price
            or current.currency != document.currency
            or current.unit != line.unit
            or current.price_list_entry_id != line.price_list_entry_id
        )
    )
    return {
        "line_id": line.id,
        "document_id": document.id,
        "agreed": {
            "quantity": line.quantity,
            "unit": line.unit,
            "unit_price": line.unit_price,
            "gross_amount": line.gross_amount,
            "currency": document.currency,
            "price_list_entry_id": line.price_list_entry_id,
            "price_list_id": retained_list.id if retained_list else None,
            "price_list_code": retained_list.code if retained_list else None,
        },
        "current_resolution": {
            "available": current is not None,
            "compared_at": compared_at,
            "unit_price": current.unit_price if current else None,
            "currency": current.currency if current else None,
            "unit": current.unit if current else None,
            "source": current.source if current else None,
            "price_list_id": current.price_list_id if current else None,
            "price_list_entry_id": current.price_list_entry_id if current else None,
            "unavailable_reason": unavailable_reason,
        },
        "changed_since_agreement": changed,
    }


def _line_wire_value(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "quantity": _line_decimal_text(row["quantity"]),
        "unit_price": _line_decimal_text(row["unit_price"]),
        "gross_amount": _line_decimal_text(row["gross_amount"]),
    }


def _line_revision(lines: list[dict[str, Any]]) -> str:
    canonical = [
        _line_wire_value(row) for row in sorted(lines, key=lambda row: row["id"] or "")
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _document_line_reality_exists(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    line_ids: set[str],
) -> bool:
    commitment_clauses = [Commitment.document_id == document_id]
    if line_ids:
        commitment_clauses.append(Commitment.document_line_id.in_(line_ids))
    return bool(
        session.scalar(
            select(Commitment.id)
            .where(
                Commitment.tenant_id == tenant_id,
                or_(*commitment_clauses),
            )
            .limit(1)
        )
        or session.scalar(
            select(LedgerEntry.id)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document_id,
            )
            .limit(1)
        )
    )


def manual_document_line_snapshot(
    session: OrmSession, tenant_id: str, document_id: str
) -> dict[str, Any]:
    document = _tenant_record(session, Document, tenant_id, document_id)
    if document.source_record_id:
        return {
            "document_id": document.id,
            "revision": "",
            "correctable": False,
            "has_linked_reality": False,
            "economic_changes_blocked": True,
            "correction_guidance": (
                "External evidence cannot be overwritten. Record a new source version instead."
            ),
            "lines": [],
        }
    stored = list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == document.id,
            )
            .order_by(DocumentLine.id)
        )
    )
    rows = [_stored_manual_line(line) for line in stored]
    has_reality = _document_line_reality_exists(
        session, tenant_id, document.id, {line.id for line in stored}
    )
    return {
        "document_id": document.id,
        "revision": _line_revision(rows),
        "correctable": True,
        "has_linked_reality": has_reality,
        "economic_changes_blocked": has_reality,
        "correction_guidance": (
            "Use the owning Reality correction workflow for economic line changes."
            if has_reality
            else ""
        ),
        "lines": [
            _line_wire_value(row)
            for row in sorted(rows, key=lambda row: row["id"] or "")
        ],
    }


def correct_manual_document_lines(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    *,
    expected_revision: str,
    lines: list[dict[str, Any]],
    actor_context: dict[str, str] | None = None,
) -> dict[str, Any]:
    _require_business_mutation(session, tenant_id, "correct_manual_document_lines")
    document = session.scalar(
        select(Document)
        .where(Document.tenant_id == tenant_id, Document.id == document_id)
        .with_for_update()
    )
    if not document:
        raise NotFound("Document was not found.")
    if document.source_record_id:
        raise InvalidOperation(
            "External evidence cannot be overwritten. Record a new source version instead."
        )
    if not lines:
        raise InvalidOperation("A manual document requires at least one line.")
    stored = list(
        session.scalars(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == document.id,
            )
            .order_by(DocumentLine.id)
            .with_for_update()
        )
    )
    stored_by_id = {line.id: line for line in stored}
    normalized = [
        _normalize_manual_line_input(session, tenant_id, document.type, raw, index)
        for index, raw in enumerate(lines, start=1)
    ]
    entries_to_validate = [
        row
        for row in normalized
        if row["price_list_entry_id"]
        and (
            row["id"] is None
            or row["id"] not in stored_by_id
            or stored_by_id[row["id"]].price_list_entry_id != row["price_list_entry_id"]
        )
    ]
    if entries_to_validate:
        correction_effective_at = _document_pricing_effective_at(
            ordered_at=document.ordered_at, document_date=document.document_date
        )
        for row in entries_to_validate:
            _validate_selected_price_entry(
                session,
                tenant_id,
                document_type=document.type,
                party_id=document.party_id,
                currency=document.currency,
                line=row,
                at=correction_effective_at,
            )
    requested_ids = [row["id"] for row in normalized if row["id"]]
    if len(requested_ids) != len(set(requested_ids)):
        raise InvalidOperation("A document line ID may appear only once.")
    unknown_ids = set(requested_ids) - set(stored_by_id)
    if unknown_ids:
        raise InvalidOperation("A document line does not belong to this document.")
    source_ids = [row["source_line_id"] for row in normalized]
    if len(source_ids) != len(set(source_ids)):
        raise InvalidOperation("Source line references must be unique per document.")

    current_rows = [_stored_manual_line(line) for line in stored]
    current_revision = _line_revision(current_rows)
    existing_requested = [row for row in normalized if row["id"]]
    identical = not any(row["id"] is None for row in normalized) and {
        _line_revision(current_rows)
    } == {_line_revision(existing_requested)}
    if identical:
        snapshot = manual_document_line_snapshot(session, tenant_id, document.id)
        return {**snapshot, "changed": False, "added": 0, "updated": 0, "removed": 0}
    if expected_revision != current_revision:
        raise Conflict("The document lines are stale. Reload before saving.")

    removed_ids = set(stored_by_id) - set(requested_ids)
    if removed_ids:
        from reality.db.cost_census import CostCompanyCensusLine

        retained = session.scalar(
            select(CostCompanyCensusLine.id)
            .where(
                CostCompanyCensusLine.tenant_id == tenant_id,
                CostCompanyCensusLine.document_line_id.in_(removed_ids),
            )
            .limit(1)
        )
        if retained is not None:
            raise InvalidOperation(
                "Retained census evidence cannot be removed. Correct the existing "
                "line or add replacement evidence."
            )
    changed_rows: list[tuple[DocumentLine, dict[str, Any], dict[str, Any]]] = []
    for row in existing_requested:
        before = _stored_manual_line(stored_by_id[row["id"]])
        if _line_revision([before]) != _line_revision([row]):
            changed_rows.append((stored_by_id[row["id"]], before, row))
    economic_change = bool(removed_ids or any(row["id"] is None for row in normalized))
    for _, before, after in changed_rows:
        economic_change = economic_change or any(
            _line_wire_value(before)[field] != _line_wire_value(after)[field]
            for field in _LINE_ECONOMIC_FIELDS
        )
    if economic_change and _document_line_reality_exists(
        session, tenant_id, document.id, set(stored_by_id)
    ):
        raise InvalidOperation(
            "Economic line evidence cannot change after Reality was derived. "
            "Use the owning Reality correction workflow."
        )

    from reality.services.costing import _protect_document

    _protect_document(session, tenant_id, document.id)

    try:
        audit = {"added": [], "removed": [], "changed": []}
        for line_id in sorted(removed_ids):
            line = stored_by_id[line_id]
            audit["removed"].append(
                {"id": line.id, "before": _line_wire_value(_stored_manual_line(line))}
            )
            session.delete(line)
        for line, before, after in changed_rows:
            for field in (
                "source_line_id",
                "item_id",
                "sku",
                "description",
                "quantity",
                "unit_price",
                "gross_amount",
                "promised_at",
                "unit",
                "line_type",
                "price_list_entry_id",
                "billed_document_line_id",
            ):
                setattr(line, field, after[field])
            line.requested_at = utc_datetime(after["promised_at"])
            audit["changed"].append(
                {
                    "id": line.id,
                    "before": _line_wire_value(before),
                    "after": _line_wire_value(after),
                }
            )
        added_count = 0
        for row in normalized:
            if row["id"] is not None:
                continue
            line = DocumentLine(
                id=uid("lin"),
                tenant_id=tenant_id,
                document_id=document.id,
                source_line_id=row["source_line_id"],
                item_id=row["item_id"],
                sku=row["sku"],
                description=row["description"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                gross_amount=row["gross_amount"],
                promised_at=row["promised_at"],
                payload=json.dumps(
                    {"reality_finance_v1": row["reality_finance_v1"]},
                    sort_keys=True,
                )
                if row["reality_finance_v1"] is not None
                else "{}",
                unit=row["unit"],
                requested_at=utc_datetime(row["promised_at"]),
                line_type=row["line_type"],
                price_list_entry_id=row["price_list_entry_id"],
                billed_document_line_id=row["billed_document_line_id"],
            )
            session.add(line)
            session.flush()
            audit["added"].append(
                {"id": line.id, "after": _line_wire_value(_stored_manual_line(line))}
            )
            added_count += 1
        payload: dict[str, Any] = {"changed_fields": ["lines"], "line_changes": audit}
        if actor_context:
            payload["actor_context"] = actor_context
        emit_business_event(
            session, tenant_id, "document.corrected", "document", document.id, payload
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    snapshot = manual_document_line_snapshot(session, tenant_id, document.id)
    return {
        **snapshot,
        "changed": True,
        "added": added_count,
        "updated": len(changed_rows),
        "removed": len(removed_ids),
    }


def correct_manual_document(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    *,
    document_type: str,
    number: str,
    party_id: str,
    amount: Decimal | float | str,
    currency: str = "EUR",
    document_date: str = "",
    ordered_at: datetime | str | None = None,
    requested_delivery_at: datetime | str | None = None,
    customer_reference: str = "",
    sales_channel: str = "",
    payment_term_code: str = "",
    ship_to_party_id: str | None = None,
) -> Document:
    """Correct manually recorded evidence without bypassing derived Reality."""
    _require_business_mutation(session, tenant_id, "correct_manual_document")
    document = _tenant_record(session, Document, tenant_id, document_id)
    if document.source_record_id:
        raise InvalidOperation(
            "External evidence cannot be overwritten. Record a new source version instead."
        )
    document_type, number, currency = (
        document_type.strip(),
        number.strip(),
        currency.strip().upper(),
    )
    if not document_type or not number or not party_id or not currency:
        raise InvalidOperation("Type, number, party, and currency are required.")
    _tenant_record(session, Party, tenant_id, party_id)
    if ship_to_party_id:
        _tenant_record(session, Party, tenant_id, ship_to_party_id)
    payment_term = (
        payment_term_by_code(session, tenant_id, payment_term_code)
        if payment_term_code.strip()
        else None
    )
    protected_changes = {
        "type": (document.type, document_type),
        "party_id": (document.party_id, party_id),
        "currency": (document.currency, currency),
        "gross_amount": (document.gross_amount, decimal(amount)),
    }
    has_downstream_reality = bool(
        session.scalar(
            select(Commitment.id)
            .where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id == document.id,
            )
            .limit(1)
        )
        or session.scalar(
            select(LedgerEntry.id)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document.id,
            )
            .limit(1)
        )
    )
    changed_protected = [
        name for name, (before, after) in protected_changes.items() if before != after
    ]
    if has_downstream_reality and changed_protected:
        raise InvalidOperation(
            "Cannot change type, party, currency, or gross amount after Reality "
            "records were derived from this document."
        )
    changes = {
        "type": document_type,
        "number": number,
        "party_id": party_id,
        "currency": currency,
        "gross_amount": decimal(amount),
        "document_date": _document_day(document_date),
        "ordered_at": utc_datetime(ordered_at),
        "requested_delivery_at": utc_datetime(requested_delivery_at),
        "customer_reference": customer_reference.strip(),
        "sales_channel": sales_channel.strip(),
        "payment_term_id": payment_term.id if payment_term else None,
        "ship_to_party_id": ship_to_party_id or None,
    }
    changed_fields = [
        field for field, value in changes.items() if getattr(document, field) != value
    ]
    if changed_fields:
        from reality.services.costing import _protect_document

        _protect_document(session, tenant_id, document.id)

    for field, value in changes.items():
        setattr(document, field, value)
    if changed_fields:
        emit_business_event(
            session,
            tenant_id,
            "document.corrected",
            "document",
            document.id,
            {"changed_fields": changed_fields},
        )
    session.commit()
    return document


def record_corrected_document_source(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    payload: dict[str, Any],
    *,
    source_version_at: datetime | str | None = None,
) -> tuple[SourceRecord, ImportJob]:
    """Append a source version for external evidence; never mutate the old payload."""
    _require_business_mutation(session, tenant_id, "record_corrected_document_source")
    document = _tenant_record(session, Document, tenant_id, document_id)
    if not document.source_record_id:
        raise InvalidOperation(
            "Manual evidence has no source stream. Use document correction instead."
        )
    source = _tenant_record(session, SourceRecord, tenant_id, document.source_record_id)
    original_job = session.scalar(
        select(ImportJob).where(
            ImportJob.tenant_id == tenant_id,
            ImportJob.source_record_id == source.id,
        )
    )
    context: dict[str, Any] = {}
    if original_job and original_job.input:
        try:
            context = json.loads(original_job.input)
        except json.JSONDecodeError:
            context = {}
        context.pop("disposition", None)
    return enqueue_source(
        session,
        tenant_id,
        source.source_system,
        source.source_type,
        source.external_id,
        payload,
        source_version_at=source_version_at,
        context=context,
    )


def post_ledger(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    party_id: str,
    postings: list[tuple[str, str, Decimal | int | float | str]],
    *,
    currency: str = "EUR",
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    account_ids: dict[str, str] | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    _require_business_mutation(session, tenant_id, "post_ledger")
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    document = _tenant_record(session, Document, tenant_id, document_id)
    from reality.services.finance.opening import check_opening_coverage

    check_opening_coverage(session, tenant_id, document, effective_at)
    _tenant_record(session, Party, tenant_id, party_id)
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
    debit = sum(
        (positive(amount, "amount") for _, side, amount in postings if side == "debit"),
        ZERO,
    )
    credit = sum(
        (
            positive(amount, "amount")
            for _, side, amount in postings
            if side == "credit"
        ),
        ZERO,
    )
    if debit != credit or any(
        side not in {"debit", "credit"} for _, side, _ in postings
    ):
        raise InvalidOperation("Ledger posting group must balance debits and credits.")
    from reality.services.finance.accounts import resolve_account

    resolved = {
        role: resolve_account(session, tenant_id, role, (account_ids or {}).get(role))
        for role, _, _ in postings
    }
    if not postings:
        raise InvalidOperation("Ledger posting group cannot be empty.")
    group_id = uid("pst")
    posting_time = effective_at or now()
    entries = [
        LedgerEntry(
            id=uid("led"),
            tenant_id=tenant_id,
            posting_group_id=group_id,
            account_id=resolved[account].id,
            account_record=resolved[account],
            party_id=party_id,
            amount=positive(amount, "amount"),
            currency=currency,
            debit_credit=side,
            effective_at=posting_time,
            document_id=document_id,
            source_record_id=source_record_id,
        )
        for account, side, amount in postings
    ]
    session.add_all(entries)
    emit_business_event(
        session,
        tenant_id,
        "ledger.posted",
        "posting_group",
        group_id,
        {
            "document_id": document_id,
            "party_id": party_id,
            "currency": currency,
            "entries": [
                {
                    "id": entry.id,
                    "account": entry.account,
                    "account_id": entry.account_id,
                    "side": entry.debit_credit,
                    "amount": entry.amount,
                }
                for entry in entries
            ],
        },
        source_record_id=source_record_id,
        occurred_at=posting_time,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return entries


@dataclass(frozen=True)
class LedgerReversalResult:
    reversal_id: str
    original_posting_group_id: str
    reversing_posting_group_id: str
    request_fingerprint: str
    replayed: bool


def _ledger_entry_values(entry: LedgerEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "posting_group_id": entry.posting_group_id,
        "account": entry.account,
        "account_id": entry.account_id,
        "party_id": entry.party_id,
        "amount": str(decimal(entry.amount)),
        "currency": entry.currency,
        "debit_credit": entry.debit_credit,
        "effective_at": entry.effective_at.isoformat(),
        "document_id": entry.document_id,
        "source_record_id": entry.source_record_id,
    }


def _ledger_group_entries(
    session: OrmSession,
    tenant_id: str,
    posting_group_id: str,
    *,
    lock: bool = False,
) -> list[LedgerEntry]:
    query = select(LedgerEntry).where(
        LedgerEntry.tenant_id == tenant_id,
        LedgerEntry.posting_group_id == posting_group_id,
    )
    if lock:
        query = query.with_for_update()
    entries = list(session.scalars(query.order_by(LedgerEntry.id)))
    if not entries:
        raise NotFound("Ledger posting group not found.")
    debit = sum(
        (decimal(entry.amount) for entry in entries if entry.debit_credit == "debit"),
        ZERO,
    )
    credit = sum(
        (decimal(entry.amount) for entry in entries if entry.debit_credit == "credit"),
        ZERO,
    )
    if debit != credit or any(
        entry.debit_credit not in {"debit", "credit"} for entry in entries
    ):
        raise InvalidOperation("Ledger posting group is not balanced.")
    if len({entry.currency for entry in entries}) != 1:
        raise InvalidOperation("Ledger posting group must use one currency.")
    if len({entry.party_id for entry in entries}) != 1:
        raise InvalidOperation("Ledger posting group must use one party.")
    return entries


def _ledger_reversal_for_group(
    session: OrmSession, tenant_id: str, posting_group_id: str
) -> tuple[LedgerReversal | None, str]:
    relation = session.scalar(
        select(LedgerReversal).where(
            LedgerReversal.tenant_id == tenant_id,
            LedgerReversal.original_posting_group_id == posting_group_id,
        )
    )
    if relation:
        return relation, "reversed_original"
    relation = session.scalar(
        select(LedgerReversal).where(
            LedgerReversal.tenant_id == tenant_id,
            LedgerReversal.reversing_posting_group_id == posting_group_id,
        )
    )
    return (relation, "reversing") if relation else (None, "normal")


def _allocation_values(allocation: SettlementAllocation) -> dict[str, Any]:
    return {
        "id": allocation.id,
        "payment_ledger_entry_id": allocation.payment_ledger_entry_id,
        "invoice_ledger_entry_id": allocation.invoice_ledger_entry_id,
        "amount": str(decimal(allocation.amount)),
        "currency": allocation.currency,
    }


def _allocations_for_entries(
    session: OrmSession, tenant_id: str, entry_ids: set[str]
) -> list[SettlementAllocation]:
    if not entry_ids:
        return []
    return list(
        session.scalars(
            select(SettlementAllocation).where(
                SettlementAllocation.tenant_id == tenant_id,
                or_(
                    SettlementAllocation.payment_ledger_entry_id.in_(entry_ids),
                    SettlementAllocation.invoice_ledger_entry_id.in_(entry_ids),
                ),
            )
        )
    )


def ledger_reversal_snapshot(
    session: OrmSession, tenant_id: str, posting_group_id: str
) -> dict[str, Any]:
    entries = _ledger_group_entries(session, tenant_id, posting_group_id)
    relation, role = _ledger_reversal_for_group(session, tenant_id, posting_group_id)
    original_group_id = (
        relation.original_posting_group_id if relation else posting_group_id
    )
    original_entries = (
        _ledger_group_entries(session, tenant_id, original_group_id)
        if original_group_id != posting_group_id
        else entries
    )
    reversing_entries = (
        _ledger_group_entries(session, tenant_id, relation.reversing_posting_group_id)
        if relation
        else []
    )
    allocations = _allocations_for_entries(
        session, tenant_id, {entry.id for entry in original_entries}
    )
    revision = canonical_payload_hash(
        {
            "entries": [_ledger_entry_values(entry) for entry in original_entries],
            "allocations": [_allocation_values(row) for row in allocations],
            "reversal_id": relation.id if relation else None,
        }
    )
    return {
        "posting_group_id": posting_group_id,
        "revision": revision,
        "role": role,
        "status": "reversed" if relation else "posted",
        "reversible": relation is None,
        "guidance": (
            "Reversing posting groups cannot be reversed."
            if role == "reversing"
            else "This posting group has already been reversed."
            if role == "reversed_original"
            else "Preview and confirm a complete posting-group reversal."
        ),
        "original_entries": [_ledger_entry_values(row) for row in original_entries],
        "reversing_entries": [_ledger_entry_values(row) for row in reversing_entries],
        "affected_allocations": [_allocation_values(row) for row in allocations],
        "reversal": (
            {
                "id": relation.id,
                "original_posting_group_id": relation.original_posting_group_id,
                "reversing_posting_group_id": relation.reversing_posting_group_id,
                "reason": relation.reason,
                "reversed_at": relation.reversed_at.isoformat(),
                "actor_context": json.loads(relation.actor_context or "{}"),
                "request_fingerprint": relation.request_fingerprint,
            }
            if relation
            else None
        ),
    }


def _ledger_reversal_fingerprint(
    tenant_id: str, posting_group_id: str, reason: str
) -> str:
    return canonical_payload_hash(
        {
            "tenant_id": tenant_id,
            "posting_group_id": posting_group_id,
            "reason": reason,
        }
    )


def preview_ledger_reversal(
    session: OrmSession, tenant_id: str, posting_group_id: str, *, reason: str
) -> dict[str, Any]:
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise InvalidOperation("Ledger reversal reason is required.")
    snapshot = ledger_reversal_snapshot(session, tenant_id, posting_group_id)
    if not snapshot["reversible"]:
        raise InvalidOperation(snapshot["guidance"])
    inverse = [
        {
            **entry,
            "id": None,
            "posting_group_id": None,
            "debit_credit": "credit" if entry["debit_credit"] == "debit" else "debit",
            "document_id": None,
            "source_record_id": None,
        }
        for entry in snapshot["original_entries"]
    ]
    return {
        **snapshot,
        "reason": normalized_reason,
        "request_fingerprint": _ledger_reversal_fingerprint(
            tenant_id, posting_group_id, normalized_reason
        ),
        "inverse_entries": inverse,
        "inactive_allocation_ids": [
            row["id"] for row in snapshot["affected_allocations"]
        ],
    }


def reverse_ledger_posting_group(
    session: OrmSession,
    tenant_id: str,
    posting_group_id: str,
    *,
    reason: str,
    actor_context: dict[str, Any] | None = None,
    action_id: str | None = None,
    expected_revision: str | None = None,
    preview_fingerprint: str | None = None,
    _commit: bool = True,
) -> LedgerReversalResult:
    _require_business_mutation(session, tenant_id, "reverse_ledger_posting_group")
    from reality.services.business_locks import lock_delivery_state

    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    lock_delivery_state(session, tenant_id)
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise InvalidOperation("Ledger reversal reason is required.")
    fingerprint = _ledger_reversal_fingerprint(
        tenant_id, posting_group_id, normalized_reason
    )
    try:
        entries = _ledger_group_entries(session, tenant_id, posting_group_id, lock=True)
        if preview_fingerprint and preview_fingerprint != fingerprint:
            raise Conflict("Ledger reversal preview no longer matches the request.")
        existing, role = _ledger_reversal_for_group(
            session, tenant_id, posting_group_id
        )
        if existing:
            if (
                role == "reversed_original"
                and existing.request_fingerprint == fingerprint
            ):
                return LedgerReversalResult(
                    existing.id,
                    existing.original_posting_group_id,
                    existing.reversing_posting_group_id,
                    existing.request_fingerprint,
                    True,
                )
            if role == "reversing":
                raise InvalidOperation("A reversing posting group cannot be reversed.")
            raise Conflict(
                "Ledger posting group was already reversed; reload its chain."
            )
        snapshot = ledger_reversal_snapshot(session, tenant_id, posting_group_id)
        if expected_revision and expected_revision != snapshot["revision"]:
            raise Conflict(
                "Ledger reversal preview is stale; reload and preview again."
            )
        reversing_group_id = uid("pst")
        reversed_at = now()
        inverse_entries = [
            LedgerEntry(
                id=uid("led"),
                tenant_id=tenant_id,
                posting_group_id=reversing_group_id,
                account_id=entry.account_id,
                account_record=entry.account_record,
                party_id=entry.party_id,
                amount=entry.amount,
                currency=entry.currency,
                debit_credit=("credit" if entry.debit_credit == "debit" else "debit"),
                effective_at=reversed_at,
                document_id=None,
                source_record_id=None,
            )
            for entry in entries
        ]
        session.add_all(inverse_entries)
        session.flush()
        relation = LedgerReversal(
            id=uid("lrv"),
            tenant_id=tenant_id,
            original_posting_group_id=posting_group_id,
            reversing_posting_group_id=reversing_group_id,
            reason=normalized_reason,
            reversed_at=reversed_at,
            actor_context=json.dumps(
                actor_context or {}, sort_keys=True, separators=(",", ":")
            ),
            request_fingerprint=fingerprint,
        )
        session.add(relation)
        session.flush()
        affected_allocations = _allocations_for_entries(
            session, tenant_id, {entry.id for entry in entries}
        )
        emit_business_event(
            session,
            tenant_id,
            "ledger.reversed",
            "posting_group",
            posting_group_id,
            {
                "reversal_id": relation.id,
                "reversing_posting_group_id": reversing_group_id,
                "reason": normalized_reason,
                "actor_context": actor_context or {},
                "affected_allocation_ids": [row.id for row in affected_allocations],
                "original_entries": [_ledger_entry_values(row) for row in entries],
                "reversing_entries": [
                    _ledger_entry_values(row) for row in inverse_entries
                ],
            },
            occurred_at=reversed_at,
            action_id=action_id,
            correlation_id=action_id,
        )
        if _commit:
            session.commit()
        else:
            session.flush()
        return LedgerReversalResult(
            relation.id,
            posting_group_id,
            reversing_group_id,
            fingerprint,
            False,
        )
    except Exception:
        session.rollback()
        raise


def record_sales_invoice(
    session: OrmSession,
    tenant_id: str,
    order_line_id: str | None = None,
    quantity: Decimal | str | None = None,
    gross_amount: Decimal | str | None = None,
    number: str = "",
    *,
    lines: list[dict[str, Any]] | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    delivery_guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record stated invoice evidence and its receivable, never generate a total."""
    _require_business_mutation(session, tenant_id, "record_sales_invoice")
    if lines is not None and delivery_guard is not None:
        raise InvalidOperation("A delivery guard requires a single sales order line.")
    if lines is not None:
        arguments = {
            "lines": lines,
            "gross_amount": gross_amount,
            "number": number,
            "effective_at": effective_at,
        }
        if order_line_id is not None or quantity is not None:
            raise InvalidOperation("Use either invoice lines or a single order line.")
        return _record_multi_order_invoice(
            session, tenant_id, "sales", arguments, action_id
        )
    return _record_order_invoice(
        session,
        tenant_id,
        order_line_id,
        quantity,
        gross_amount,
        number,
        direction="sales",
        delivery_guard=delivery_guard,
        effective_at=effective_at,
        action_id=action_id,
    )


def record_supplier_invoice(
    session: OrmSession,
    tenant_id: str,
    order_line_id: str | None = None,
    quantity: Decimal | str | None = None,
    gross_amount: Decimal | str | None = None,
    number: str = "",
    *,
    lines: list[dict[str, Any]] | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
) -> dict[str, Any]:
    """Record received supplier invoice evidence and its payable atomically."""
    _require_business_mutation(session, tenant_id, "record_supplier_invoice")
    if lines is not None:
        arguments = {
            "lines": lines,
            "gross_amount": gross_amount,
            "number": number,
            "effective_at": effective_at,
        }
        if order_line_id is not None or quantity is not None:
            raise InvalidOperation("Use either invoice lines or a single order line.")
        return _record_multi_order_invoice(
            session, tenant_id, "purchase", arguments, action_id
        )
    return _record_order_invoice(
        session,
        tenant_id,
        order_line_id,
        quantity,
        gross_amount,
        number,
        direction="purchase",
        effective_at=effective_at,
        action_id=action_id,
    )


def uncredited_return_quantity(
    session: OrmSession, tenant_id: str, order_line_id: str
) -> Decimal:
    """Read returned goods still eligible for linked credit evidence."""
    _tenant_record(session, DocumentLine, tenant_id, order_line_id)
    commitments = session.scalars(
        select(Commitment.id).where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_line_id == order_line_id,
            Commitment.type == "customer_delivery",
        )
    )
    returned = sum(
        (returned_quantity(session, tenant_id, id_) for id_ in commitments), ZERO
    )
    invoice_lines = (
        select(DocumentLine.id)
        .join(
            Document,
            (Document.id == DocumentLine.document_id)
            & (Document.tenant_id == tenant_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.billed_document_line_id == order_line_id,
            Document.type == "sales_invoice",
        )
    )
    credited = session.scalar(
        select(func.coalesce(func.sum(DocumentLine.quantity), 0))
        .join(
            Document,
            (Document.id == DocumentLine.document_id)
            & (Document.tenant_id == DocumentLine.tenant_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            or_(
                DocumentLine.billed_document_line_id == order_line_id,
                DocumentLine.billed_document_line_id.in_(invoice_lines),
            ),
            Document.type == "credit_note",
        )
    )
    return returned - credited


def _order_line_billing(
    session: OrmSession,
    tenant_id: str,
    order_line_id: str,
    *,
    projected_reversal_group: str | None = None,
) -> dict[str, Any]:
    """Observe quantity availability without changing received invoice evidence."""
    line = _tenant_record(session, DocumentLine, tenant_id, order_line_id)
    order = _tenant_record(session, Document, tenant_id, line.document_id)
    invoice_type = {
        "sales_order": "sales_invoice",
        "purchase_order": "supplier_invoice",
    }.get(order.type)
    if invoice_type is None:
        raise InvalidOperation("Billing availability requires an order line.")
    evidence = []
    billed = ZERO
    for invoice_line, invoice in session.execute(
        select(DocumentLine, Document)
        .join(
            Document,
            (Document.id == DocumentLine.document_id)
            & (Document.tenant_id == tenant_id),
        )
        .where(
            DocumentLine.tenant_id == tenant_id,
            DocumentLine.billed_document_line_id == line.id,
            Document.type == invoice_type,
        )
        .order_by(Document.id, DocumentLine.id)
    ):
        groups = sorted(
            set(
                session.scalars(
                    select(LedgerEntry.posting_group_id).where(
                        LedgerEntry.tenant_id == tenant_id,
                        LedgerEntry.document_id == invoice.id,
                    )
                )
            )
        )
        reversals = list(
            session.scalars(
                select(LedgerReversal)
                .where(
                    LedgerReversal.tenant_id == tenant_id,
                    LedgerReversal.original_posting_group_id.in_(groups),
                )
                .order_by(LedgerReversal.id)
            )
        )
        reversed_groups = {row.original_posting_group_id for row in reversals}
        if projected_reversal_group:
            reversed_groups.add(projected_reversal_group)
        released = bool(groups) and set(groups) <= reversed_groups
        if not released:
            billed += invoice_line.quantity
        evidence.append(
            {
                "invoice_id": invoice.id,
                "invoice_line_id": invoice_line.id,
                "number": invoice.number,
                "source_record_id": invoice.source_record_id,
                "quantity": invoice_line.quantity,
                "posting_group_ids": groups,
                "reversal_ids": [row.id for row in reversals],
                "released": released,
            }
        )
    remaining = max(line.quantity - billed, ZERO)
    item = (
        _tenant_record(session, Item, tenant_id, line.item_id) if line.item_id else None
    )
    return {
        "order_line_id": line.id,
        "order_id": order.id,
        "label": item.name if item else line.description or line.sku or line.id,
        "unit": line.unit,
        "ordered": line.quantity,
        "invoiced": billed,
        "remaining": remaining,
        "can_invoice": remaining > ZERO,
        "evidence": evidence,
    }


def _validate_invoice_delivery_guard(
    session: OrmSession,
    tenant_id: str,
    line: DocumentLine,
    quantity: Decimal,
    guard: Any,
) -> None:
    from reality.services.exceptions import kept_and_billed_quantity

    # The guard names no line of its own: the invoice's order line already is
    # the condition's subject, so a guard cannot point anywhere else.
    if (
        not isinstance(guard, dict)
        or set(guard) != {"unbilled_quantity", "unit"}
        or guard["unit"] != line.unit
        or not isinstance(guard["unbilled_quantity"], str)
    ):
        raise InvalidOperation("The invoice delivery guard is invalid.")
    commitments = list(
        session.scalars(
            select(Commitment.id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_line_id == line.id,
                Commitment.type == "customer_delivery",
            )
        )
    )
    if len(commitments) != 1:
        raise InvalidOperation("The invoice delivery evidence is missing or ambiguous.")
    kept, billed = kept_and_billed_quantity(session, tenant_id, commitments[0], line)
    if kept <= ZERO:
        raise InvalidOperation("The delivery changed. Prepare a fresh invoice review.")
    if billed is None:
        raise InvalidOperation("The invoice delivery unit cannot be verified.")
    unbilled = kept - billed
    if (
        unbilled <= ZERO
        or quantity > unbilled
        or unbilled != positive(guard["unbilled_quantity"], "delivery quantity")
    ):
        raise InvalidOperation("The delivery changed. Prepare a fresh invoice review.")


MAX_INVOICE_POSITIONS = 200


def _preview_order_invoice(
    session: OrmSession, tenant_id: str, direction: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """Validate stated invoice evidence without creating financial records."""
    if "lines" in arguments:
        required = {"lines", "gross_amount", "number"}
        if not required <= arguments.keys() or arguments.keys() - required - {
            "effective_at"
        }:
            raise InvalidOperation("Invoice fields are incomplete or unsupported.")
        selections = arguments["lines"]
        if not isinstance(selections, list) or not selections:
            raise InvalidOperation("Select at least one invoice position.")
        if len(selections) > MAX_INVOICE_POSITIONS:
            raise InvalidOperation(
                f"An invoice carries at most {MAX_INVOICE_POSITIONS} positions."
            )
        previews = []
        seen = set()
        for selection in selections:
            if (
                not isinstance(selection, dict)
                or not {
                    "order_line_id",
                    "quantity",
                    "gross_amount",
                }
                <= set(selection)
                or set(selection)
                - {
                    "order_line_id",
                    "quantity",
                    "gross_amount",
                    "reality_finance_v1",
                }
            ):
                raise InvalidOperation(
                    "Invoice position fields are incomplete or unsupported."
                )
            if (
                not isinstance(selection["order_line_id"], str)
                or selection["order_line_id"] in seen
            ):
                raise InvalidOperation("Invoice positions must be distinct.")
            seen.add(selection["order_line_id"])
            previews.append(
                _preview_order_invoice(
                    session,
                    tenant_id,
                    direction,
                    {
                        **selection,
                        "number": arguments["number"],
                        "effective_at": arguments.get("effective_at"),
                    },
                )
            )
        # A consolidated invoice may bill several orders (spec 280), but only of one
        # party in one currency: the invoice states one debtor and one amount.
        if len({row["party_id"] for row in previews}) != 1:
            raise InvalidOperation("Invoice positions must belong to one party.")
        if len({row["currency"] for row in previews}) != 1:
            raise InvalidOperation("Invoice positions must share one currency.")
        orders: dict[str, Document] = {}
        for row in previews:
            order_id = _tenant_record(
                session, DocumentLine, tenant_id, row["order_line_id"]
            ).document_id
            if order_id not in orders:
                orders[order_id] = _tenant_record(
                    session, Document, tenant_id, order_id
                )
        first = previews[0]
        amount = positive(arguments["gross_amount"], "gross_amount")
        for value in [
            amount,
            *(v for row in previews for v in (row["quantity"], row["gross_amount"])),
        ]:
            if value >= Decimal(100000000000000) or value != value.quantize(
                Decimal("0.0001")
            ):
                raise InvalidOperation(
                    "Invoice values must fit four decimal places without rounding."
                )
        document, lines = _preview_manual_document_input(
            session,
            tenant_id,
            "sales_invoice" if direction == "sales" else "supplier_invoice",
            arguments["number"],
            first["party_id"],
            [
                {**row["lines"][0], "source_line_id": str(index)}
                for index, row in enumerate(previews, 1)
            ],
            amount,
            currency=first["currency"],
            document_date=first["document"]["document_date"],
        )
        return {
            "direction": direction,
            "order_line_id": first["order_line_id"],
            "gross_amount": amount,
            "number": document["number"],
            "currency": first["currency"],
            "party_id": first["party_id"],
            "effective_at": first["effective_at"],
            "document": document,
            "lines": lines,
            "selections": [
                {k: row[k] for k in ("order_line_id", "quantity", "gross_amount")}
                for row in previews
            ],
            "orders": [
                {"id": order.id, "number": order.number} for order in orders.values()
            ],
        }
    required = {"order_line_id", "quantity", "gross_amount", "number"}
    if not required <= arguments.keys() or arguments.keys() - required - {
        "effective_at",
        "reality_finance_v1",
        "delivery_guard",
    }:
        raise InvalidOperation("Invoice fields are incomplete or unsupported.")
    line = _tenant_record(session, DocumentLine, tenant_id, arguments["order_line_id"])
    order = _tenant_record(session, Document, tenant_id, line.document_id)
    if direction not in {"sales", "purchase"} or order.type != f"{direction}_order":
        raise InvalidOperation(f"Invoice requires a {direction} order line.")
    quantity = positive(arguments["quantity"], "quantity")
    amount = positive(arguments["gross_amount"], "gross_amount")
    for value in (quantity, amount):
        if value >= Decimal(100000000000000) or value != value.quantize(
            Decimal("0.0001")
        ):
            raise InvalidOperation(
                "Invoice values must fit four decimal places without rounding."
            )
    if quantity > _order_line_billing(session, tenant_id, line.id)["remaining"]:
        raise InvalidOperation(
            "Invoice quantity exceeds the remaining billable quantity."
        )
    guard = arguments.get("delivery_guard")
    if "delivery_guard" in arguments:
        if direction != "sales":
            raise InvalidOperation("A delivery guard requires a sales invoice.")
        _validate_invoice_delivery_guard(session, tenant_id, line, quantity, guard)
    effective = utc_datetime(arguments.get("effective_at"))
    document, lines = _preview_manual_document_input(
        session,
        tenant_id,
        "sales_invoice" if direction == "sales" else "supplier_invoice",
        arguments["number"],
        order.party_id,
        [
            {
                "item_id": line.item_id,
                "quantity": quantity,
                "unit": line.unit,
                "unit_price": line.unit_price,
                "gross_amount": amount,
                "billed_document_line_id": line.id,
                "reality_finance_v1": arguments.get("reality_finance_v1"),
            }
        ],
        amount,
        currency=order.currency,
        document_date=effective.date().isoformat() if effective else "",
    )
    return {
        "direction": direction,
        **({"delivery_guard": guard} if guard is not None else {}),
        "order_line_id": line.id,
        "quantity": quantity,
        "gross_amount": amount,
        "number": document["number"],
        "currency": document["currency"],
        "party_id": order.party_id,
        "item_id": line.item_id,
        "unit": line.unit,
        "unit_price": line.unit_price,
        "effective_at": effective,
        "document": document,
        "lines": lines,
    }


def _record_multi_order_invoice(
    session: OrmSession,
    tenant_id: str,
    direction: str,
    arguments: dict[str, Any],
    action_id: str | None,
) -> dict[str, Any]:
    from reality.services.tenant_policy import require_decision_finance

    invoice_type = "sales_invoice" if direction == "sales" else "supplier_invoice"
    require_decision_finance(
        session, tenant_id, f"{invoice_type}_record", arguments, action_id
    )
    with session.begin_nested():
        creation = _preview_order_invoice(session, tenant_id, direction, arguments)
        ids = [row["order_line_id"] for row in creation["selections"]]
        list(
            session.scalars(
                select(DocumentLine)
                .where(DocumentLine.tenant_id == tenant_id, DocumentLine.id.in_(ids))
                .order_by(DocumentLine.id)
                .with_for_update()
            )
        )
        session.expire_all()
        creation = _preview_order_invoice(session, tenant_id, direction, arguments)
        effective = creation["effective_at"] or now()
        payload = {
            **arguments,
            "currency": creation["currency"],
            "effective_at": effective.isoformat(),
        }
        source = create_master_source_record(
            session,
            tenant_id,
            invoice_type,
            "manual",
            action_id or uid("invoice"),
            payload,
            action_id=action_id,
            _commit=False,
        )
        document, lines = create_manual_document_with_lines(
            session,
            tenant_id,
            invoice_type,
            creation["number"],
            creation["party_id"],
            creation["lines"],
            creation["gross_amount"],
            currency=creation["currency"],
            document_date=effective.date().isoformat(),
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        post = post_sales_invoice if direction == "sales" else post_supplier_invoice
        entries = post(
            session,
            tenant_id,
            document.id,
            effective_at=effective,
            action_id=action_id,
            _commit=False,
        )
        result = {
            "records": [
                {"family": "source_record", "id": source.id},
                {"family": "document", "id": document.id},
                *[{"family": "document_line", "id": row.id} for row in lines],
                *[{"family": "ledger_entry", "id": row.id} for row in entries],
            ]
        }
        emit_business_event(
            session,
            tenant_id,
            "invoice.recorded",
            "document",
            document.id,
            {
                "creation": creation,
                "receipt": result,
                "effective_at": effective,
                "entries": [
                    {
                        key: getattr(row, key)
                        for key in (
                            "id",
                            "posting_group_id",
                            "account",
                            "party_id",
                            "amount",
                            "currency",
                            "debit_credit",
                            "effective_at",
                            "document_id",
                            "source_record_id",
                        )
                    }
                    for row in entries
                ],
            },
            source_record_id=source.id,
            action_id=action_id,
            correlation_id=action_id,
        )
    session.commit()
    return result


def _record_order_invoice(
    session: OrmSession,
    tenant_id: str,
    order_line_id: str,
    quantity: Decimal | str,
    gross_amount: Decimal | str,
    number: str,
    *,
    direction: str,
    effective_at: datetime | None,
    action_id: str | None,
    credit: bool = False,
    delivery_guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from reality.services.tenant_policy import require_decision_finance

    invoice_type = (
        "credit_note"
        if credit
        else "sales_invoice"
        if direction == "sales"
        else "supplier_invoice"
    )
    require_decision_finance(
        session,
        tenant_id,
        "sales_credit_record" if credit else f"{invoice_type}_record",
        {
            **(
                {"delivery_guard": delivery_guard} if delivery_guard is not None else {}
            ),
            "order_line_id": order_line_id,
            "quantity": quantity,
            "gross_amount": gross_amount,
            "number": number,
            "effective_at": effective_at,
        },
        action_id,
    )
    session.expire_all()
    with session.begin_nested():
        line = session.scalar(
            select(DocumentLine)
            .where(
                DocumentLine.tenant_id == tenant_id, DocumentLine.id == order_line_id
            )
            .with_for_update()
        )
        if line is None:
            raise NotFound("Order line not found.")
        creation = None
        if not credit:
            creation = _preview_order_invoice(
                session,
                tenant_id,
                direction,
                {
                    **(
                        {"delivery_guard": delivery_guard}
                        if delivery_guard is not None
                        else {}
                    ),
                    "order_line_id": order_line_id,
                    "quantity": quantity,
                    "gross_amount": gross_amount,
                    "number": number,
                    "effective_at": effective_at,
                },
            )
        order = _tenant_record(session, Document, tenant_id, line.document_id)
        if order.type != f"{direction}_order":
            raise InvalidOperation(f"Invoice requires a {direction} order line.")
        quantity, gross_amount = (
            positive(quantity, "quantity"),
            positive(gross_amount, "gross_amount"),
        )
        if quantity > line.quantity:
            raise InvalidOperation("Invoice quantity exceeds the order line.")
        if credit and quantity > uncredited_return_quantity(
            session, tenant_id, line.id
        ):
            raise InvalidOperation(
                "Credit quantity exceeds returned, not yet credited goods."
            )
        effective_at = effective_at or now()
        payload = {
            **(
                {"delivery_guard": delivery_guard} if delivery_guard is not None else {}
            ),
            "order_line_id": line.id,
            "quantity": str(quantity),
            "gross_amount": str(gross_amount),
            "number": number,
            "currency": order.currency,
            "effective_at": effective_at.isoformat(),
        }
        source = create_master_source_record(
            session,
            tenant_id,
            invoice_type,
            "manual",
            action_id or uid("invoice"),
            payload,
            action_id=action_id,
            _commit=False,
        )
        document, lines = create_manual_document_with_lines(
            session,
            tenant_id,
            invoice_type,
            number,
            order.party_id,
            [
                {
                    "item_id": line.item_id,
                    "quantity": str(quantity),
                    "unit": line.unit,
                    "unit_price": str(line.unit_price),
                    "gross_amount": str(gross_amount),
                    "billed_document_line_id": line.id,
                }
            ],
            gross_amount,
            currency=order.currency,
            document_date=effective_at.date().isoformat(),
            source_record_id=source.id,
            action_id=action_id,
            _commit=False,
        )
        post = (
            post_sales_credit_note
            if credit
            else post_sales_invoice
            if direction == "sales"
            else post_supplier_invoice
        )
        entries = post(
            session,
            tenant_id,
            document.id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
        result = {
            "records": [
                {"family": "source_record", "id": source.id},
                {"family": "document", "id": document.id},
                *[{"family": "document_line", "id": row.id} for row in lines],
                *[{"family": "ledger_entry", "id": row.id} for row in entries],
            ]
        }
        if creation is not None:
            emit_business_event(
                session,
                tenant_id,
                "invoice.recorded",
                "document",
                document.id,
                {
                    "creation": creation,
                    "receipt": result,
                    "effective_at": effective_at,
                    "entries": [
                        {
                            key: getattr(row, key)
                            for key in (
                                "id",
                                "posting_group_id",
                                "account",
                                "party_id",
                                "amount",
                                "currency",
                                "debit_credit",
                                "effective_at",
                                "document_id",
                                "source_record_id",
                            )
                        }
                        for row in entries
                    ],
                },
                source_record_id=source.id,
                action_id=action_id,
                correlation_id=action_id,
            )
    session.commit()
    return result


def record_sales_credit(
    session: OrmSession,
    tenant_id: str,
    order_line_id: str | None = None,
    quantity: Decimal | str | None = None,
    gross_amount: Decimal | str | None = None,
    number: str | None = None,
    *,
    invoice_id: str | None = None,
    lines: list[dict[str, Any]] | None = None,
    reason: str | None = None,
    allocation_amount: Decimal | str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
) -> dict[str, Any]:
    """Record an invoice-linked financial credit or a legacy return credit."""
    _require_business_mutation(session, tenant_id, "record_sales_credit")
    if invoice_id is not None or lines is not None:
        from reality.services.credit_actions import _record_invoice_credit

        if order_line_id is not None or quantity is not None:
            raise InvalidOperation(
                "Use either invoice positions or legacy return-credit fields."
            )
        return _record_invoice_credit(
            session,
            tenant_id,
            {
                "invoice_id": invoice_id,
                "lines": lines,
                "reason": reason,
                "allocation_amount": allocation_amount,
                "gross_amount": gross_amount,
                "number": number,
                "effective_at": effective_at,
            },
            action_id,
        )
    if reason is not None or allocation_amount is not None:
        raise InvalidOperation(
            "Invoice credit fields require an invoice and positions."
        )
    return _record_order_invoice(
        session,
        tenant_id,
        order_line_id,
        quantity,
        gross_amount,
        number,
        direction="sales",
        effective_at=effective_at,
        action_id=action_id,
        credit=True,
    )


def post_sales_invoice(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    *,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    _require_business_mutation(session, tenant_id, "post_sales_invoice")
    document = _tenant_record(session, Document, tenant_id, document_id)
    if document.type != "sales_invoice":
        raise InvalidOperation("Document is not a sales invoice.")
    if account_balance(session, tenant_id, "sales_revenue", document.id) != ZERO:
        raise InvalidOperation("Sales invoice is already posted.")
    return post_ledger(
        session,
        tenant_id,
        document.id,
        document.party_id,
        [
            ("accounts_receivable", "debit", document.gross_amount),
            ("sales_revenue", "credit", document.gross_amount),
        ],
        currency=document.currency,
        source_record_id=document.source_record_id,
        effective_at=effective_at,
        action_id=action_id,
        _commit=_commit,
    )


def _preview_invoice_payment(
    session: OrmSession, tenant_id: str, direction: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """Validate a stated selected-invoice payment without creating evidence."""
    required = {"invoice_id", "amount"}
    if not required <= arguments.keys() or arguments.keys() - required - {
        "payment_number",
        "source_record_id",
        "effective_at",
    }:
        raise InvalidOperation("Payment fields are incomplete or unsupported.")
    invoice = _tenant_record(session, Document, tenant_id, arguments["invoice_id"])
    expected = {
        "customer": "sales_invoice",
        "supplier": "supplier_invoice",
        "customer_refund": "credit_note",
    }.get(direction)
    if expected is None or invoice.type != expected:
        raise InvalidOperation(f"Payment requires a {expected}.")
    control = _settlement_control_entry(session, tenant_id, invoice.id)
    if _ledger_reversal_for_group(session, tenant_id, control.posting_group_id)[0]:
        raise InvalidOperation(
            "Credit note posting is reversed."
            if direction == "customer_refund"
            else "Invoice posting is reversed."
        )
    amount = positive(arguments["amount"], "amount")
    opened = open_invoice_amount(session, tenant_id, invoice.id)
    if amount > opened:
        raise InvalidOperation(
            "Refund exceeds the open credit amount."
            if direction == "customer_refund"
            else "Payment exceeds the open invoice amount."
        )
    if amount != amount.quantize(Decimal("0.0001")):
        raise InvalidOperation(
            "Payment amount supports at most four decimal places without rounding."
        )
    reference = arguments.get("payment_number")
    if reference is not None and not isinstance(reference, str):
        raise InvalidOperation(
            "Refund reference must be text."
            if direction == "customer_refund"
            else "Payment reference must be text."
        )
    source_id = arguments.get("source_record_id") or None
    if source_id:
        _tenant_record(session, SourceRecord, tenant_id, source_id)
    effective = utc_datetime(arguments.get("effective_at"))
    return {
        "creation": {
            "direction": direction,
            "invoice_id": invoice.id,
            "invoice_entry_id": control.id,
            "party_id": invoice.party_id,
            "currency": invoice.currency,
            "amount": amount,
            "payment_number": reference,
            "source_record_id": source_id,
            "effective_at": effective,
        },
        "open_before": opened,
        "open_after": opened - amount,
    }


def post_customer_payment(
    session: OrmSession,
    tenant_id: str,
    invoice_id: str,
    amount,
    *,
    payment_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Record and allocate one customer payment as a single financial transaction."""
    _require_business_mutation(session, tenant_id, "post_customer_payment")
    from reality.services.tenant_policy import require_decision_finance

    require_decision_finance(
        session,
        tenant_id,
        "customer_payment_post",
        {
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_number": payment_number,
            "effective_at": effective_at,
            **(
                {"source_record_id": source_record_id}
                if source_record_id is not None
                else {}
            ),
        },
        action_id,
    )
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant_id)
    with session.begin_nested():
        preview = _preview_invoice_payment(
            session,
            tenant_id,
            "customer",
            {
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_number": payment_number,
                "source_record_id": source_record_id,
                "effective_at": effective_at,
            },
        )
        source_record_id = preview["creation"]["source_record_id"]
        invoice = _tenant_record(session, Document, tenant_id, invoice_id)
        amount = positive(amount, "amount")
        if amount > open_invoice_amount(session, tenant_id, invoice.id):
            raise InvalidOperation("Payment exceeds the open customer receivable.")
        entries = record_customer_payment(
            session,
            tenant_id,
            invoice.party_id,
            amount,
            _control_account_id=_settlement_control_entry(
                session, tenant_id, invoice.id
            ).account_id,
            currency=invoice.currency,
            payment_number=payment_number,
            source_record_id=source_record_id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
        allocate_settlement(
            session,
            tenant_id,
            _control_entry(entries, "accounts_receivable").id,
            _settlement_control_entry(session, tenant_id, invoice.id).id,
            amount,
            action_id=action_id,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def record_customer_payment(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    amount,
    *,
    currency: str = "EUR",
    payment_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _control_account_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    _require_business_mutation(session, tenant_id, "record_customer_payment")
    amount = positive(amount, "amount")
    with session.begin_nested():
        payment = create_document(
            session,
            tenant_id,
            "customer_payment",
            payment_number or uid("pay"),
            party_id,
            amount,
            currency=currency,
            document_date=(effective_at or now()).date().isoformat(),
            source_record_id=source_record_id,
            action_id=action_id,
            _commit=False,
        )
        entries = post_ledger(
            session,
            tenant_id,
            payment.id,
            party_id,
            [("cash", "debit", amount), ("accounts_receivable", "credit", amount)],
            account_ids={"accounts_receivable": _control_account_id}
            if _control_account_id
            else None,
            currency=currency,
            source_record_id=source_record_id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def post_sales_credit_note(
    session: OrmSession,
    tenant_id: str,
    credit_note_id: str,
    *,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Book a credit note as the exact reverse of a sales invoice.

    It needs no invoice. The obligation exists whether or not anything is open,
    and a receivable going negative is the statement that the company owes this
    customer — which is the ordinary consumer return, paid at checkout and sent
    back a week later.
    """
    _require_business_mutation(session, tenant_id, "post_sales_credit_note")
    document = _tenant_record(session, Document, tenant_id, credit_note_id)
    if document.type != "credit_note":
        raise InvalidOperation("Document is not a credit note.")
    if account_balance(session, tenant_id, "sales_revenue", document.id) != ZERO:
        raise InvalidOperation("Credit note is already posted.")
    amount = positive(document.gross_amount, "credit note total")
    return post_ledger(
        session,
        tenant_id,
        document.id,
        document.party_id,
        [
            ("sales_revenue", "debit", amount),
            ("accounts_receivable", "credit", amount),
        ],
        currency=document.currency,
        source_record_id=document.source_record_id,
        effective_at=effective_at,
        action_id=action_id,
        _commit=_commit,
    )


def record_customer_refund(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    amount,
    *,
    currency: str = "EUR",
    refund_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _control_account_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Money going back to a customer, the mirror of a customer payment."""
    _require_business_mutation(session, tenant_id, "record_customer_refund")
    amount = positive(amount, "amount")
    effective_at = utc_datetime(effective_at)
    with session.begin_nested():
        refund = create_document(
            session,
            tenant_id,
            "customer_refund",
            refund_number or uid("ref"),
            party_id,
            amount,
            currency=currency,
            document_date=(effective_at or now()).date().isoformat(),
            source_record_id=source_record_id,
            action_id=action_id,
            _commit=False,
        )
        entries = post_ledger(
            session,
            tenant_id,
            refund.id,
            party_id,
            [("accounts_receivable", "debit", amount), ("cash", "credit", amount)],
            account_ids={"accounts_receivable": _control_account_id}
            if _control_account_id
            else None,
            currency=currency,
            source_record_id=source_record_id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def _preview_customer_refund(
    session: OrmSession, tenant_id: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """Validate the existing refund intent through the shared settlement preview."""
    required = {"credit_note_id", "amount"}
    if not required <= arguments.keys() or arguments.keys() - required - {
        "refund_number",
        "source_record_id",
        "effective_at",
    }:
        raise InvalidOperation("Refund fields are incomplete or unsupported.")
    from reality.services.credit_actions import _exact

    amount = _exact(arguments["amount"], "Refund amount")
    mapped = {
        "invoice_id": arguments["credit_note_id"],
        "amount": amount,
        "payment_number": arguments.get("refund_number"),
        "source_record_id": arguments.get("source_record_id"),
        "effective_at": arguments.get("effective_at"),
    }
    return _preview_invoice_payment(session, tenant_id, "customer_refund", mapped)


def post_customer_refund(
    session: OrmSession,
    tenant_id: str,
    credit_note_id: str,
    amount,
    *,
    refund_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Give a credited customer their money, and settle the credit note."""
    _require_business_mutation(session, tenant_id, "post_customer_refund")
    from reality.services.tenant_policy import require_decision_finance

    require_decision_finance(
        session,
        tenant_id,
        "customer_refund_post",
        {
            "credit_note_id": credit_note_id,
            "amount": amount,
            "refund_number": refund_number,
            "effective_at": effective_at,
            **(
                {"source_record_id": source_record_id}
                if source_record_id is not None
                else {}
            ),
        },
        action_id,
    )
    session.expire_all()
    with session.begin_nested():
        preview = _preview_customer_refund(
            session,
            tenant_id,
            {
                "credit_note_id": credit_note_id,
                "amount": amount,
                "refund_number": refund_number,
                "source_record_id": source_record_id,
                "effective_at": effective_at,
            },
        )
        source_record_id = preview["creation"]["source_record_id"]
        amount = preview["creation"]["amount"]
        note = _tenant_record(session, Document, tenant_id, credit_note_id)
        if note.type != "credit_note":
            raise InvalidOperation("Document is not a credit note.")
        amount = positive(amount, "amount")
        if amount > open_invoice_amount(session, tenant_id, note.id):
            raise InvalidOperation("Refund exceeds what the credit note still owes.")
        entries = record_customer_refund(
            session,
            tenant_id,
            note.party_id,
            amount,
            _control_account_id=_settlement_control_entry(
                session, tenant_id, note.id
            ).account_id,
            currency=note.currency,
            refund_number=refund_number,
            source_record_id=source_record_id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
        allocate_settlement(
            session,
            tenant_id,
            _control_entry(entries, "accounts_receivable").id,
            _settlement_control_entry(session, tenant_id, note.id).id,
            amount,
            action_id=action_id,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def allocate_credit_note(
    session: OrmSession,
    tenant_id: str,
    credit_note_id: str,
    invoice_id: str,
    amount,
    *,
    _commit: bool = True,
) -> SettlementAllocation:
    """Net a posted credit note against an invoice the customer still owes.

    The other way to settle a credit is to refund it. Both go through the one
    settlement relation, so an invoice falls exactly as a payment makes it fall
    and nothing downstream needs telling that a credit was involved.
    """
    _require_business_mutation(session, tenant_id, "allocate_credit_note")
    note = _tenant_record(session, Document, tenant_id, credit_note_id)
    if note.type != "credit_note":
        raise InvalidOperation("Document is not a credit note.")
    invoice = _tenant_record(session, Document, tenant_id, invoice_id)
    if note.party_id != invoice.party_id:
        raise InvalidOperation("A credit note settles only its own customer.")
    return allocate_settlement(
        session,
        tenant_id,
        _settlement_control_entry(session, tenant_id, note.id).id,
        _settlement_control_entry(session, tenant_id, invoice.id).id,
        amount,
        _commit=_commit,
    )


def post_supplier_invoice(
    session: OrmSession,
    tenant_id: str,
    document_id: str,
    *,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    _require_business_mutation(session, tenant_id, "post_supplier_invoice")
    document = _tenant_record(session, Document, tenant_id, document_id)
    if document.type != "supplier_invoice":
        raise InvalidOperation("Document is not a supplier invoice.")
    if account_balance(session, tenant_id, "accounts_payable", document.id) != ZERO:
        raise InvalidOperation("Supplier invoice is already posted.")
    return post_ledger(
        session,
        tenant_id,
        document.id,
        document.party_id,
        [
            ("inventory", "debit", document.gross_amount),
            ("accounts_payable", "credit", document.gross_amount),
        ],
        currency=document.currency,
        source_record_id=document.source_record_id,
        effective_at=effective_at,
        action_id=action_id,
        _commit=_commit,
    )


def post_supplier_payment(
    session: OrmSession,
    tenant_id: str,
    invoice_id: str,
    amount,
    *,
    payment_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    _require_business_mutation(session, tenant_id, "post_supplier_payment")
    from reality.services.tenant_policy import require_decision_finance

    require_decision_finance(
        session,
        tenant_id,
        "supplier_payment_post",
        {
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_number": payment_number,
            "effective_at": effective_at,
            **(
                {"source_record_id": source_record_id}
                if source_record_id is not None
                else {}
            ),
        },
        action_id,
    )
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant_id)
    with session.begin_nested():
        preview = _preview_invoice_payment(
            session,
            tenant_id,
            "supplier",
            {
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_number": payment_number,
                "source_record_id": source_record_id,
                "effective_at": effective_at,
            },
        )
        source_record_id = preview["creation"]["source_record_id"]
        invoice = _tenant_record(session, Document, tenant_id, invoice_id)
        if invoice.type != "supplier_invoice":
            raise InvalidOperation("Document is not a supplier invoice.")
        amount = positive(amount, "amount")
        open_payable = open_invoice_amount(session, tenant_id, invoice.id)
        if amount > open_payable:
            raise InvalidOperation("Payment exceeds the open supplier payable.")
        entries = record_supplier_payment(
            session,
            tenant_id,
            invoice.party_id,
            amount,
            _control_account_id=_settlement_control_entry(
                session, tenant_id, invoice.id
            ).account_id,
            currency=invoice.currency,
            payment_number=payment_number,
            source_record_id=source_record_id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
        allocate_settlement(
            session,
            tenant_id,
            _control_entry(entries, "accounts_payable").id,
            _settlement_control_entry(session, tenant_id, invoice.id).id,
            amount,
            action_id=action_id,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def record_supplier_payment(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    amount,
    *,
    currency: str = "EUR",
    payment_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _control_account_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    _require_business_mutation(session, tenant_id, "record_supplier_payment")
    amount = positive(amount, "amount")
    with session.begin_nested():
        payment = create_document(
            session,
            tenant_id,
            "supplier_payment",
            payment_number or uid("pay"),
            party_id,
            amount,
            currency=currency,
            document_date=(effective_at or now()).date().isoformat(),
            source_record_id=source_record_id,
            action_id=action_id,
            _commit=False,
        )
        entries = post_ledger(
            session,
            tenant_id,
            payment.id,
            party_id,
            [("accounts_payable", "debit", amount), ("cash", "credit", amount)],
            account_ids={"accounts_payable": _control_account_id}
            if _control_account_id
            else None,
            currency=currency,
            source_record_id=source_record_id,
            effective_at=effective_at,
            action_id=action_id,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def _control_entry(entries: list[LedgerEntry], account: str) -> LedgerEntry:
    return next(entry for entry in entries if entry.account == account)


# What one document owes or claims, and on which side of which control account
# it sits. A settlement links two of these on opposite sides: a payment settles
# an invoice, and a refund settles a credit note the same way from the other
# direction. A wrong side here would still balance and still be wrong.
# Which control entry settles a document, and which side of it that entry sits
# on. `open_invoice_amount` needs no knowledge of any particular type: it takes
# the balance on this account for this document and flips its sign by the side
# recorded here, so a supplier credit sitting on the debit side of accounts
# payable reads as a claim on the supplier without a line of special handling.
from reality.domain.finance import OPENING_DIRECTIONS

SETTLEMENT_CONTROL = {
    **{f"opening_{kind}": control for kind, control in OPENING_DIRECTIONS.items()},
    "customer_settlement_adjustment": ("accounts_receivable", "credit"),
    "supplier_settlement_adjustment": ("accounts_payable", "debit"),
    "sales_invoice": ("accounts_receivable", "debit"),
    "supplier_invoice": ("accounts_payable", "credit"),
    "credit_note": ("accounts_receivable", "credit"),
    "customer_refund": ("accounts_receivable", "debit"),
    "supplier_credit_note": ("accounts_payable", "debit"),
    "supplier_refund": ("accounts_payable", "credit"),
    "customer_deposit": ("accounts_receivable", "credit"),
    "supplier_deposit": ("accounts_payable", "debit"),
    "dunning_fee_charge": ("accounts_receivable", "debit"),
}


def _settlement_control_entry(
    session: OrmSession, tenant_id: str, invoice_id: str
) -> LedgerEntry:
    invoice = _tenant_record(session, Document, tenant_id, invoice_id)
    control = SETTLEMENT_CONTROL.get(invoice.type)
    if control is None:
        raise InvalidOperation("Settlement target is not a settleable document.")
    account, side = control
    entry = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.document_id == invoice.id,
            LedgerEntry.account == account,
            LedgerEntry.debit_credit == side,
        )
    )
    if entry is None:
        raise InvalidOperation("Invoice has no posted control-account entry.")
    return entry


def _settlement_control_entries(
    session: OrmSession,
    tenant_id: str,
    documents: list[Document],
    *,
    effective_before: datetime | None = None,
) -> dict[str, LedgerEntry]:
    """The control-account entry per settleable document, read once for many.

    A document whose type has no control account, or that nobody has posted, is
    absent here: the two cases `_settlement_control_entry` refuses one at a time.
    """
    wanted = {
        document.id: SETTLEMENT_CONTROL[document.type]
        for document in documents
        if document.type in SETTLEMENT_CONTROL
    }
    if not wanted:
        return {}
    entries: dict[str, LedgerEntry] = {}
    for entry in session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.effective_at < effective_before if effective_before else True,
            LedgerEntry.document_id.in_(list(wanted)),
            LedgerEntry.account.in_({account for account, _ in wanted.values()}),
        )
    ):
        if (entry.account, entry.debit_credit) == wanted[entry.document_id]:
            entries.setdefault(entry.document_id, entry)
    return entries


def _ledger_reversal_roles(
    session: OrmSession,
    tenant_id: str,
    posting_group_ids: set[str],
    *,
    effective_before: datetime | None = None,
) -> dict[str, tuple[LedgerReversal, str]]:
    """What `_ledger_reversal_for_group` answers, for many posting groups at once.

    A group that was reversed reports the reversal even when it also reverses
    another group, the same precedence the single-group read applies.
    """
    if not posting_group_ids:
        return {}
    relations = list(
        session.scalars(
            select(LedgerReversal).where(
                LedgerReversal.tenant_id == tenant_id,
                LedgerReversal.reversed_at < effective_before
                if effective_before
                else True,
                or_(
                    LedgerReversal.original_posting_group_id.in_(posting_group_ids),
                    LedgerReversal.reversing_posting_group_id.in_(posting_group_ids),
                ),
            )
        )
    )
    roles: dict[str, tuple[LedgerReversal, str]] = {}
    for relation in relations:
        if relation.reversing_posting_group_id in posting_group_ids:
            roles.setdefault(
                relation.reversing_posting_group_id, (relation, "reversing")
            )
    for relation in relations:
        if relation.original_posting_group_id in posting_group_ids:
            roles[relation.original_posting_group_id] = (relation, "reversed_original")
    return roles


def _document_account_balances(
    session: OrmSession,
    tenant_id: str,
    accounts: set[str],
    document_ids: list[str],
    *,
    effective_before: datetime | None = None,
) -> dict[tuple[str, str], Decimal]:
    """`account_balance` per (account, document) for many documents in one read."""
    if not accounts or not document_ids:
        return {}
    balances: dict[tuple[str, str], Decimal] = {}
    for account, document_id, side, amount in session.execute(
        select(
            LedgerEntry.account,
            LedgerEntry.document_id,
            LedgerEntry.debit_credit,
            func.sum(LedgerEntry.amount),
        )
        .where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.effective_at < effective_before if effective_before else True,
            LedgerEntry.account.in_(accounts),
            LedgerEntry.document_id.in_(document_ids),
        )
        .group_by(
            LedgerEntry.account, LedgerEntry.document_id, LedgerEntry.debit_credit
        )
    ):
        signed = decimal(amount) if side == "debit" else -decimal(amount)
        balances[(account, document_id)] = (
            balances.get((account, document_id), ZERO) + signed
        )
    return balances


def _allocated_per_entry(allocations: list[SettlementAllocation]) -> dict[str, Decimal]:
    """How much of each ledger entry the active allocations already consume."""
    allocated: dict[str, Decimal] = {}
    for row in allocations:
        for entry_id in {row.invoice_ledger_entry_id, row.payment_ledger_entry_id}:
            allocated[entry_id] = allocated.get(entry_id, ZERO) + decimal(row.amount)
    return allocated


@dataclass(frozen=True)
class SettlementPosition:
    """Where one settleable document stands: its control entry, reversal role, open amount."""

    control: LedgerEntry
    relation: LedgerReversal | None
    role: str
    open: Decimal


def settlement_positions(
    session: OrmSession,
    tenant_id: str,
    documents: list[Document],
    *,
    effective_before: datetime | None = None,
) -> dict[str, SettlementPosition]:
    """`open_invoice_amount` and its inputs for many documents in five reads.

    Documents without a control account or never posted are absent. The reads are
    bounded by the documents passed, never by the company: allocations are read for
    these control entries only.
    """
    controls = _settlement_control_entries(
        session, tenant_id, documents, effective_before=effective_before
    )
    roles = _ledger_reversal_roles(
        session,
        tenant_id,
        {entry.posting_group_id for entry in controls.values()},
        effective_before=effective_before,
    )
    balances = _document_account_balances(
        session,
        tenant_id,
        {entry.account for entry in controls.values()},
        list(controls),
        effective_before=effective_before,
    )
    allocated = _allocated_per_entry(
        active_settlement_allocations(
            session,
            tenant_id,
            entry_ids={entry.id for entry in controls.values()},
            effective_before=effective_before,
        )
    )
    positions = {}
    for document_id, control in controls.items():
        relation, role = roles.get(control.posting_group_id, (None, "normal"))
        positions[document_id] = SettlementPosition(
            control,
            relation,
            role,
            _open_amount(
                control,
                role,
                balances.get((control.account, document_id), ZERO),
                allocated.get(control.id, ZERO),
            ),
        )
    return positions


def open_invoice_amounts(
    session: OrmSession, tenant_id: str, documents: list[Document]
) -> dict[str, Decimal]:
    """`open_invoice_amount` for many documents; absent when a document is not settleable."""
    return {
        document_id: position.open
        for document_id, position in settlement_positions(
            session, tenant_id, documents
        ).items()
    }


def _open_amount(
    control: LedgerEntry, role: str, balance: Decimal, allocated: Decimal
) -> Decimal:
    """The one arithmetic behind an open amount, shared by the single and the bulk read."""
    if role == "reversed_original":
        return ZERO
    gross_open = balance if control.debit_credit == "debit" else -balance
    return gross_open - decimal(allocated)


def allocate_settlement(
    session: OrmSession,
    tenant_id: str,
    payment_ledger_entry_id: str,
    invoice_ledger_entry_id: str,
    amount,
    *,
    action_id: str | None = None,
    _commit: bool = True,
) -> SettlementAllocation:
    _require_business_mutation(session, tenant_id, "allocate_settlement")
    from reality.services.business_locks import lock_delivery_state

    lock_delivery_state(session, tenant_id)
    if action_id:
        _tenant_record(session, ChangeProposal, tenant_id, action_id)
    payment = _tenant_record(session, LedgerEntry, tenant_id, payment_ledger_entry_id)
    invoice = _tenant_record(session, LedgerEntry, tenant_id, invoice_ledger_entry_id)
    amount = positive(amount, "amount")
    if (
        payment.account_id != invoice.account_id
        or payment.debit_credit == invoice.debit_credit
    ):
        raise InvalidOperation(
            "Settlement entries must be opposite sides of one control account."
        )
    if payment.party_id != invoice.party_id or payment.party_id is None:
        raise InvalidOperation("Settlement entries must belong to the same party.")
    if payment.account not in {"accounts_receivable", "accounts_payable"}:
        raise InvalidOperation("Settlement requires control accounts.")
    from reality.services.finance.accounts import resolve_account

    resolve_account(session, tenant_id, payment.account, payment.account_id)
    if payment.currency != invoice.currency:
        raise InvalidOperation("Settlement entries must use the same currency.")
    if (
        _ledger_reversal_for_group(session, tenant_id, payment.posting_group_id)[0]
        or _ledger_reversal_for_group(session, tenant_id, invoice.posting_group_id)[0]
    ):
        raise InvalidOperation(
            "Settlement entries must belong to active posting groups."
        )
    allocated_payment = sum(
        (
            decimal(row.amount)
            for row in active_settlement_allocations(session, tenant_id)
            if payment.id in (row.payment_ledger_entry_id, row.invoice_ledger_entry_id)
        ),
        ZERO,
    )
    if amount > decimal(payment.amount) - decimal(allocated_payment):
        raise InvalidOperation("Allocation exceeds the unallocated payment amount.")
    invoice_document = _tenant_record(session, Document, tenant_id, invoice.document_id)
    if amount > open_invoice_amount(session, tenant_id, invoice_document.id):
        raise InvalidOperation("Allocation exceeds the invoice open amount.")
    allocation = SettlementAllocation(
        id=uid("set"),
        tenant_id=tenant_id,
        payment_ledger_entry_id=payment.id,
        invoice_ledger_entry_id=invoice.id,
        amount=amount,
        currency=payment.currency,
    )
    session.add(allocation)
    emit_business_event(
        session,
        tenant_id,
        "settlement.allocated",
        "settlement_allocation",
        allocation.id,
        {
            "payment_ledger_entry_id": payment.id,
            "invoice_ledger_entry_id": invoice.id,
            "amount": amount,
            "currency": payment.currency,
        },
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return allocation


def post_supplier_credit_note(
    session: OrmSession,
    tenant_id: str,
    credit_note_id: str,
    *,
    effective_at: datetime | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Book a credit a supplier sent as the exact reverse of its invoice.

    It needs no invoice. The claim exists whether or not anything is open, and a
    payable going the other way is the statement that the supplier owes this
    company — which is what a credit arriving after the invoice was paid is.

    The reverse of the original posting is the one answer that needs no
    judgement. Whether a rebate rather than a returned item ought to land
    somewhere other than inventory is an accounting argument, and adjudicating
    it would mean Reality authoring a treatment nobody stated.
    """
    _require_business_mutation(session, tenant_id, "post_supplier_credit_note")
    document = _tenant_record(session, Document, tenant_id, credit_note_id)
    if document.type != "supplier_credit_note":
        raise InvalidOperation("Document is not a supplier credit note.")
    if account_balance(session, tenant_id, "accounts_payable", document.id) != ZERO:
        raise InvalidOperation("Supplier credit note is already posted.")
    amount = positive(document.gross_amount, "supplier credit note total")
    return post_ledger(
        session,
        tenant_id,
        document.id,
        document.party_id,
        [
            ("accounts_payable", "debit", amount),
            ("inventory", "credit", amount),
        ],
        currency=document.currency,
        source_record_id=document.source_record_id,
        effective_at=effective_at,
        _commit=_commit,
    )


def record_supplier_refund(
    session: OrmSession,
    tenant_id: str,
    party_id: str,
    amount,
    *,
    currency: str = "EUR",
    refund_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    _control_account_id: str | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Money coming back from a supplier, the mirror of a supplier payment."""
    _require_business_mutation(session, tenant_id, "record_supplier_refund")
    amount = positive(amount, "amount")
    with session.begin_nested():
        refund = create_document(
            session,
            tenant_id,
            "supplier_refund",
            refund_number or uid("ref"),
            party_id,
            amount,
            currency=currency,
            document_date=(effective_at or now()).date().isoformat(),
            source_record_id=source_record_id,
            action_id=action_id,
            _commit=False,
        )
        entries = post_ledger(
            session,
            tenant_id,
            refund.id,
            party_id,
            [
                ("cash", "debit", amount),
                ("accounts_payable", "credit", amount),
            ],
            account_ids={"accounts_payable": _control_account_id}
            if _control_account_id
            else None,
            currency=currency,
            source_record_id=source_record_id,
            action_id=action_id,
            effective_at=effective_at,
            _commit=False,
        )

    if _commit:
        session.commit()
    return entries


def post_supplier_refund(
    session: OrmSession,
    tenant_id: str,
    credit_note_id: str,
    amount,
    *,
    refund_number: str | None = None,
    source_record_id: str | None = None,
    effective_at: datetime | None = None,
    _commit: bool = True,
) -> list[LedgerEntry]:
    """Take the money back from a supplier, and settle the credit note."""
    _require_business_mutation(session, tenant_id, "post_supplier_refund")
    with session.begin_nested():
        note = _tenant_record(session, Document, tenant_id, credit_note_id)
        if note.type != "supplier_credit_note":
            raise InvalidOperation("Document is not a supplier credit note.")
        amount = positive(amount, "amount")
        if amount > open_invoice_amount(session, tenant_id, note.id):
            raise InvalidOperation("Refund exceeds what the credit note still claims.")
        entries = record_supplier_refund(
            session,
            tenant_id,
            note.party_id,
            amount,
            _control_account_id=_settlement_control_entry(
                session, tenant_id, note.id
            ).account_id,
            currency=note.currency,
            refund_number=refund_number,
            source_record_id=source_record_id,
            effective_at=effective_at,
            _commit=False,
        )
        allocate_settlement(
            session,
            tenant_id,
            _control_entry(entries, "accounts_payable").id,
            _settlement_control_entry(session, tenant_id, note.id).id,
            amount,
            _commit=False,
        )
    if _commit:
        session.commit()
    return entries


def allocate_supplier_credit_note(
    session: OrmSession,
    tenant_id: str,
    credit_note_id: str,
    invoice_id: str,
    amount,
    *,
    _commit: bool = True,
) -> SettlementAllocation:
    """Net a posted supplier credit against an invoice the company still owes.

    The other way to settle one is to have the supplier refund it. Both go
    through the one settlement relation, so a payable falls exactly as a payment
    makes it fall and nothing downstream needs telling that a credit was
    involved.
    """
    _require_business_mutation(session, tenant_id, "allocate_supplier_credit_note")
    note = _tenant_record(session, Document, tenant_id, credit_note_id)
    if note.type != "supplier_credit_note":
        raise InvalidOperation("Document is not a supplier credit note.")
    invoice = _tenant_record(session, Document, tenant_id, invoice_id)
    if invoice.type != "supplier_invoice":
        raise InvalidOperation("A supplier credit settles only a supplier invoice.")
    if note.party_id != invoice.party_id:
        raise InvalidOperation("A supplier credit settles only its own supplier.")
    return allocate_settlement(
        session,
        tenant_id,
        _settlement_control_entry(session, tenant_id, note.id).id,
        _settlement_control_entry(session, tenant_id, invoice.id).id,
        amount,
        _commit=_commit,
    )


def open_invoice_amount(
    session: OrmSession,
    tenant_id: str,
    invoice_id: str,
    *,
    allocations: list[SettlementAllocation] | None = None,
) -> Decimal:
    """What a settleable document still owes or claims.

    "Invoice" in the name is narrower than what this answers: a credit note and
    a customer refund are settled the same way and are measured here too. The
    name is kept because renaming a function the aging register, the isolation
    catalog and four exception classes depend on would ripple far for no gain.
    """
    invoice = _tenant_record(session, Document, tenant_id, invoice_id)
    control = _settlement_control_entry(session, tenant_id, invoice.id)
    _, role = _ledger_reversal_for_group(session, tenant_id, control.posting_group_id)
    document_balance = account_balance(session, tenant_id, control.account, invoice.id)
    # Every allocation touching this control entry reduces what is left on it,
    # whichever side it sits on. An invoice is only ever settled; a credit note
    # can settle an invoice and be settled by a refund, so counting one side
    # would leave it owing money it has already given back.
    # A caller that measures many documents passes the tenant's active
    # allocations once; reading them per document made the open items register
    # quadratic in the number of invoices (feature 170 measured 578 invoices at
    # 23 seconds, 18 of them here). `financial_open_items` goes further and reads
    # the control entries, reversals and balances for all its documents at once.
    if allocations is None:
        allocations = active_settlement_allocations(
            session, tenant_id, entry_ids={control.id}
        )
    return _open_amount(
        control,
        role,
        document_balance,
        _allocated_per_entry(allocations).get(control.id, ZERO),
    )


def account_balance(
    session: OrmSession, tenant_id: str, account: str, document_id: str | None = None
) -> Decimal:
    query = select(LedgerEntry).where(
        LedgerEntry.tenant_id == tenant_id, LedgerEntry.account == account
    )
    if document_id:
        query = query.where(LedgerEntry.document_id == document_id)
    balance = ZERO
    for entry in session.scalars(query):
        signed = (
            decimal(entry.amount)
            if entry.debit_credit == "debit"
            else -decimal(entry.amount)
        )
        balance += signed
    return balance


def financial_open_items(
    session: OrmSession,
    tenant_id: str,
    *,
    document_ids: set[str] | None = None,
    effective_before: datetime | None = None,
    party_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    return _financial_open_items(
        session,
        tenant_id,
        document_ids=document_ids,
        effective_before=effective_before,
        party_ids=party_ids,
    )


def _financial_open_items(
    session: OrmSession,
    tenant_id: str,
    *,
    document_ids: set[str] | None = None,
    effective_before: datetime | None = None,
    party_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Open items, optionally for named documents or named parties.

    Both narrowings select rows; neither changes how one is derived. An item's
    open amount comes from its own postings and its own allocations, so asking
    about fewer documents returns fewer rows of the same arithmetic.
    """
    get_tenant(session, tenant_id)
    rows = []
    documents = list(
        session.scalars(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.type.in_(
                    (
                        "sales_invoice",
                        "supplier_invoice",
                        "opening_customer_debt",
                        "opening_supplier_debt",
                    )
                ),
            )
            .where(Document.id.in_(document_ids) if document_ids is not None else True)
            .where(Document.party_id.in_(party_ids) if party_ids is not None else True)
            .order_by(Document.document_date, Document.number)
        )
    )
    parties = {
        row.id: row
        for row in session.scalars(
            select(Party).where(
                Party.tenant_id == tenant_id,
                Party.id.in_({document.party_id for document in documents}),
            )
        )
    }
    from reality.db.opening import OpeningItem, OpeningScope

    opening_details = {
        item.document_id: item
        for item in session.scalars(
            select(OpeningItem).where(
                OpeningItem.tenant_id == tenant_id,
                OpeningItem.document_id.in_([d.id for d in documents]),
            )
        )
    }
    opening_kinds = (
        dict(
            session.execute(
                select(OpeningItem.document_id, OpeningScope.coverage_kind)
                .join(
                    OpeningScope,
                    (OpeningScope.tenant_id == tenant_id)
                    & (OpeningScope.id == OpeningItem.scope_id),
                )
                .where(
                    OpeningItem.tenant_id == tenant_id,
                    OpeningItem.document_id.in_(opening_details),
                )
            ).all()
        )
        if opening_details
        else {}
    )
    # Six reads for the whole register instead of nine per document: a demo
    # company with 2,230 invoices took 27 seconds here, and four exception
    # classes each asked again.
    positions = settlement_positions(
        session, tenant_id, documents, effective_before=effective_before
    )
    for document in documents:
        party = parties.get(document.party_id or "")
        position = positions.get(document.id)
        if position is None:
            # No control account for the type, or never posted: not an open item.
            continue
        control, relation, role = position.control, position.relation, position.role
        open_amount = position.open
        gross = decimal(control.amount if effective_before else document.gross_amount)
        rows.append(
            {
                "document": document,
                "origin": "opening" if document.id in opening_details else "invoice",
                "coverage_kind": opening_kinds.get(document.id),
                "original_due_date": opening_details[document.id].original_due_date
                if document.id in opening_details
                else None,
                "party": party.name if party else "—",
                "party_payment_term_id": party.payment_term_id if party else None,
                "control": control,
                "open": open_amount,
                "settled": gross - open_amount,
                "status": (
                    "reversed"
                    if relation and role == "reversed_original"
                    else "paid"
                    if open_amount == ZERO
                    else "partial"
                    if open_amount < gross
                    else "open"
                ),
            }
        )
    return rows


def duplicate_supplier_invoices(
    session: OrmSession,
    tenant_id: str,
    *,
    _open_items: list[dict[str, Any]] | None = None,
) -> list[tuple[Document, Document]]:
    """Every supplier invoice recorded under a number its supplier already used.

    Returns each duplicate paired with the document it duplicates, so a caller can
    both know that a document is one and say which earlier document it repeats.

    Documents are read directly rather than through the open-item derivation: an
    invoice nobody has posted yet does not appear there, and a duplicate caught
    before anybody pays it is the one worth catching.

    This lives here rather than in the exception class that has reported it since
    Spec 078 because a payment run needs exactly the same set, and two answers to
    "is this a duplicate" is how a queue and an operation start disagreeing about
    money.
    """
    # A withdrawn invoice cannot be paid twice, and a supplier reissuing a
    # corrected invoice under its original number is ordinary rather than a
    # finding, so a reversed document is neither reported nor matched against.
    # A caller that already holds the open items register passes it; the
    # exception evaluation reads that register once for every money class.
    if _open_items is None:
        _open_items = financial_open_items(session, tenant_id)
    withdrawn = {
        row["document"].id for row in _open_items if row["status"] == "reversed"
    }
    documents = session.scalars(
        select(Document)
        .where(Document.tenant_id == tenant_id, Document.type == "supplier_invoice")
        .order_by(Document.document_date, Document.id)
    ).all()
    groups: dict[tuple[str, str], list[Document]] = {}
    for document in documents:
        number = document.number.strip().casefold()
        # An empty string is not a number two documents can share; grouping on it
        # would report every unnumbered document as a duplicate of every other.
        if not number or document.id in withdrawn:
            continue
        groups.setdefault((document.party_id or "", number), []).append(document)
    pairs: list[tuple[Document, Document]] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        # Ordered by date and then by identity, so the original never changes
        # between reads even when two arrive on the same day.
        original, *duplicates = members
        pairs.extend((duplicate, original) for duplicate in duplicates)
    return pairs


def open_item_control_accounts(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    currencies = sorted({row["document"].currency for row in rows})
    return [
        {
            "currency": currency,
            "receivables": [
                row
                for row in rows
                if row["document"].currency == currency
                and row["document"].type == "sales_invoice"
                and row["open"] != ZERO
            ],
            "payables": [
                row
                for row in rows
                if row["document"].currency == currency
                and row["document"].type == "supplier_invoice"
                and row["open"] != ZERO
            ],
        }
        for currency in currencies
    ]


def payment_rows(
    session: OrmSession, tenant_id: str, cash_entry_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    """Every payment with what it settled, or the named ones alone.

    `cash_entry_ids` selects rows and nothing else: a payment's allocated and
    unallocated amounts come from its own control entry and its own allocations.
    """
    return _payment_rows(session, tenant_id, cash_entry_ids=cash_entry_ids)


def _payment_rows(
    session: OrmSession, tenant_id: str, *, cash_entry_ids: set[str] | None = None
) -> list[dict[str, Any]]:
    """Every payment with what it settled, in six reads for the whole company.

    The per-payment form read the control entry, the reversal, every allocation of
    the company, the document and the party once per payment; on a 1,400-order
    company that was 11,000 reads and four minutes (spec 181).
    """
    from reality.db.search import payment_eligibility

    get_tenant(session, tenant_id)
    cash_entries = [
        cash
        for cash in session.scalars(
            select(LedgerEntry)
            .where(payment_eligibility(tenant_id))
            .where(
                LedgerEntry.id.in_(cash_entry_ids)
                if cash_entry_ids is not None
                else True
            )
            .order_by(LedgerEntry.effective_at.desc())
        )
        # Reversing cash entries carry correction evidence through LedgerReversal,
        # not a payment Document, and therefore are not independent payment rows.
        if cash.document_id is not None
    ]
    if not cash_entries:
        return []
    groups = {cash.posting_group_id for cash in cash_entries}
    controls: dict[str, LedgerEntry] = {}
    for entry in session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.tenant_id == tenant_id,
            LedgerEntry.posting_group_id.in_(groups),
            LedgerEntry.account.in_(("accounts_receivable", "accounts_payable")),
        )
    ):
        controls.setdefault(entry.posting_group_id, entry)
    roles = _ledger_reversal_roles(session, tenant_id, groups)
    # Only the payment side counts: what this control entry has given to invoices.
    allocated_by_payment: dict[str, Decimal] = {}
    for row in active_settlement_allocations(
        session, tenant_id, entry_ids={entry.id for entry in controls.values()}
    ):
        allocated_by_payment[row.payment_ledger_entry_id] = allocated_by_payment.get(
            row.payment_ledger_entry_id, ZERO
        ) + decimal(row.amount)
    documents = {
        row.id: row
        for row in session.scalars(
            select(Document).where(
                Document.tenant_id == tenant_id,
                Document.id.in_({cash.document_id for cash in cash_entries}),
            )
        )
    }
    party_ids = {cash.party_id for cash in cash_entries if cash.party_id}
    parties = (
        {
            row.id: row
            for row in session.scalars(
                select(Party).where(
                    Party.tenant_id == tenant_id, Party.id.in_(party_ids)
                )
            )
        }
        if party_ids
        else {}
    )
    rows = []
    for cash in cash_entries:
        control = controls.get(cash.posting_group_id)
        document = documents.get(cash.document_id)
        if control is None or document is None:
            continue
        relation, role = roles.get(cash.posting_group_id, (None, "normal"))
        allocated = allocated_by_payment.get(control.id, ZERO)
        party = parties.get(cash.party_id) if cash.party_id else None
        rows.append(
            {
                "cash_entry": cash,
                "control_entry": control,
                "document": document,
                "party": (
                    "—"
                    if not cash.party_id
                    else getattr(party, "name", cash.party_id)
                    if party
                    else cash.party_id
                ),
                "direction": "incoming" if cash.debit_credit == "debit" else "outgoing",
                "allocated": allocated,
                "unallocated": (
                    ZERO
                    if relation and role == "reversed_original"
                    else decimal(cash.amount) - allocated
                ),
                "reversal_role": role,
            }
        )
    return rows


def active_settlement_allocations(
    session: OrmSession,
    tenant_id: str,
    *,
    entry_ids: set[str] | None = None,
    effective_before: datetime | None = None,
) -> list[SettlementAllocation]:
    """Return immutable allocations whose linked posting groups remain active.

    `entry_ids` narrows the read to allocations touching those ledger entries. A
    caller measuring one invoice or one payment passes them; reading every
    allocation of the company for one document made payment matching grow with the
    company's history (spec 181, ingest cost).

    With `effective_before`, an allocation counts once both of its endpoint entries
    are effective. `allocated_at` is when it was recorded, which is knowledge time,
    so it is no cutoff (spec 232 FR-003).
    """
    if entry_ids is not None and not entry_ids:
        return []
    query = select(SettlementAllocation).where(
        SettlementAllocation.tenant_id == tenant_id,
    )
    if entry_ids is not None:
        query = query.where(
            or_(
                SettlementAllocation.payment_ledger_entry_id.in_(entry_ids),
                SettlementAllocation.invoice_ledger_entry_id.in_(entry_ids),
            )
        )
    allocations = list(session.scalars(query))
    if not allocations:
        return []
    entry_ids = {
        entry_id
        for row in allocations
        for entry_id in (
            row.payment_ledger_entry_id,
            row.invoice_ledger_entry_id,
        )
    }
    entries = {
        row.id: row
        for row in session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.effective_at < effective_before
                if effective_before
                else True,
                LedgerEntry.id.in_(entry_ids),
            )
        )
    }
    reversed_groups = set(
        session.scalars(
            select(LedgerReversal.original_posting_group_id).where(
                LedgerReversal.tenant_id == tenant_id,
                LedgerReversal.reversed_at < effective_before
                if effective_before
                else True,
                LedgerReversal.original_posting_group_id.in_(
                    {entry.posting_group_id for entry in entries.values()}
                ),
            )
        )
    )
    return [
        row
        for row in allocations
        if entries.get(row.payment_ledger_entry_id) is not None
        and entries.get(row.invoice_ledger_entry_id) is not None
        and entries[row.payment_ledger_entry_id].posting_group_id not in reversed_groups
        and entries[row.invoice_ledger_entry_id].posting_group_id not in reversed_groups
    ]


def journal_rows(session: OrmSession, tenant_id: str) -> list[LedgerEntry]:
    get_tenant(session, tenant_id)
    return list(
        session.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant_id)
            .order_by(LedgerEntry.effective_at.desc(), LedgerEntry.posting_group_id)
        )
    )


def ledger_t_accounts(entries: list[LedgerEntry]) -> list[dict[str, Any]]:
    keys = sorted({(entry.account, entry.currency) for entry in entries})
    accounts = []
    for account, currency in keys:
        debit = [
            entry
            for entry in entries
            if entry.account == account
            and entry.currency == currency
            and entry.debit_credit == "debit"
        ]
        credit = [
            entry
            for entry in entries
            if entry.account == account
            and entry.currency == currency
            and entry.debit_credit == "credit"
        ]
        debit_total = sum((decimal(entry.amount) for entry in debit), ZERO)
        credit_total = sum((decimal(entry.amount) for entry in credit), ZERO)
        accounts.append(
            {
                "account": account,
                "currency": currency,
                "debit": debit,
                "credit": credit,
                "debit_total": debit_total,
                "credit_total": credit_total,
                "balance": debit_total - credit_total,
            }
        )
    return accounts


def account_statement(
    session: OrmSession, tenant_id: str, account: str, currency: str
) -> dict[str, Any]:
    get_tenant(session, tenant_id)
    account, currency = account.strip(), currency.strip().upper()
    if not account or not currency:
        raise InvalidOperation("Account and currency are required.")
    entries = list(
        session.scalars(
            select(LedgerEntry)
            .where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.account == account,
                LedgerEntry.currency == currency,
            )
            .order_by(
                LedgerEntry.effective_at,
                LedgerEntry.posting_group_id,
                LedgerEntry.id,
            )
        )
    )
    running_balance = ZERO
    rows = []
    for entry in entries:
        running_balance += (
            decimal(entry.amount)
            if entry.debit_credit == "debit"
            else -decimal(entry.amount)
        )
        rows.append({"entry": entry, "balance": running_balance})
    account_view = ledger_t_accounts(entries)
    return {
        "account": account,
        "currency": currency,
        "entries": rows,
        "t_account": account_view[0] if account_view else None,
        "balance": running_balance,
    }


def ledger_posting_groups(entries: list[LedgerEntry]) -> list[dict[str, Any]]:
    group_ids = list(dict.fromkeys(entry.posting_group_id for entry in entries))
    groups = []
    for group_id in group_ids:
        debit = [
            entry
            for entry in entries
            if entry.posting_group_id == group_id and entry.debit_credit == "debit"
        ]
        credit = [
            entry
            for entry in entries
            if entry.posting_group_id == group_id and entry.debit_credit == "credit"
        ]
        debit_total = sum((decimal(entry.amount) for entry in debit), ZERO)
        credit_total = sum((decimal(entry.amount) for entry in credit), ZERO)
        groups.append(
            {
                "id": group_id,
                "effective_at": (debit or credit)[0].effective_at,
                "currency": (debit or credit)[0].currency,
                "debit": debit,
                "credit": credit,
                "debit_total": debit_total,
                "credit_total": credit_total,
                "balanced": debit_total == credit_total,
            }
        )
    return groups


def parties(session: OrmSession, tenant_id: str) -> list[Party]:
    get_tenant(session, tenant_id)
    return list(
        session.scalars(
            select(Party).where(Party.tenant_id == tenant_id).order_by(Party.name)
        )
    )


def items(session: OrmSession, tenant_id: str) -> list[Item]:
    get_tenant(session, tenant_id)
    return list(
        session.scalars(
            select(Item).where(Item.tenant_id == tenant_id).order_by(Item.name)
        )
    )


def locations(session: OrmSession, tenant_id: str) -> list[Location]:
    get_tenant(session, tenant_id)
    return list(
        session.scalars(
            select(Location)
            .where(Location.tenant_id == tenant_id)
            .order_by(Location.name)
        )
    )


def document_detail(
    session: OrmSession, tenant_id: str, document_id: str
) -> dict[str, Any]:
    document = _tenant_record(session, Document, tenant_id, document_id)
    source = (
        _tenant_record(session, SourceRecord, tenant_id, document.source_record_id)
        if document.source_record_id
        else None
    )
    linked_commitments = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id == document.id,
            )
        )
    )
    commitment_ids = [commitment.id for commitment in linked_commitments]
    ledger_entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant_id,
                LedgerEntry.document_id == document.id,
            )
        )
    )
    lines = list(
        session.scalars(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.document_id == document.id,
            )
        )
    )
    item_ids = {line.item_id for line in lines if line.item_id}
    return {
        "document": document,
        "party": (
            _tenant_record(session, Party, tenant_id, document.party_id)
            if document.party_id
            else None
        ),
        "source": source,
        "payment_term": (
            _tenant_record(session, PaymentTerm, tenant_id, document.payment_term_id)
            if document.payment_term_id
            else None
        ),
        "ship_to_party": (
            _tenant_record(session, Party, tenant_id, document.ship_to_party_id)
            if document.ship_to_party_id
            else None
        ),
        "lines": lines,
        "items_by_id": {
            item.id: item
            for item in session.scalars(
                select(Item).where(Item.tenant_id == tenant_id, Item.id.in_(item_ids))
            )
        }
        if item_ids
        else {},
        "has_downstream_reality": bool(linked_commitments or ledger_entries),
        "commitments": linked_commitments,
        "active_holds": list(
            session.scalars(
                select(CommitmentHold).where(
                    CommitmentHold.tenant_id == tenant_id,
                    CommitmentHold.commitment_id.in_(commitment_ids),
                    CommitmentHold.released_at.is_(None),
                )
            )
        )
        if commitment_ids
        else [],
        "ledger_entries": ledger_entries,
        "ledger_posting_groups": ledger_posting_groups(ledger_entries),
    }


def party_detail(session: OrmSession, tenant_id: str, party_id: str) -> dict[str, Any]:
    party = _tenant_record(session, Party, tenant_id, party_id)
    payment_term = (
        _tenant_record(session, PaymentTerm, tenant_id, party.payment_term_id)
        if party.payment_term_id
        else None
    )
    party.payment_term_code = payment_term.code if payment_term else ""
    return {
        "party": party,
        "roles": list(
            session.scalars(
                select(PartyRole).where(
                    PartyRole.tenant_id == tenant_id,
                    PartyRole.party_id == party.id,
                )
            )
        ),
        "active_delivery_hold": active_party_delivery_hold(
            session, tenant_id, party.id
        ),
        "payment_term": payment_term,
        "source": (
            _tenant_record(session, SourceRecord, tenant_id, party.source_record_id)
            if party.source_record_id
            else None
        ),
        "documents": list(
            session.scalars(
                select(Document).where(
                    Document.tenant_id == tenant_id, Document.party_id == party.id
                )
            )
        ),
        "commitments": list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    (Commitment.from_party_id == party.id)
                    | (Commitment.to_party_id == party.id),
                )
            )
        ),
        "ledger_entries": list(
            session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == tenant_id,
                    LedgerEntry.party_id == party.id,
                )
            )
        ),
    }


def item_detail(session: OrmSession, tenant_id: str, item_id: str) -> dict[str, Any]:
    item = _tenant_record(session, Item, tenant_id, item_id)
    item_movements = list(
        session.scalars(
            select(Movement)
            .where(Movement.tenant_id == tenant_id, Movement.item_id == item.id)
            .order_by(Movement.occurred_at.desc())
        )
    )
    handling_unit_ids = {
        movement.handling_unit_id
        for movement in item_movements
        if movement.handling_unit_id
    }
    lot_ids = {movement.lot_id for movement in item_movements if movement.lot_id}
    serial_unit_ids = {
        movement.serial_unit_id
        for movement in item_movements
        if movement.serial_unit_id
    }
    return {
        "item": item,
        "source": (
            _tenant_record(session, SourceRecord, tenant_id, item.source_record_id)
            if item.source_record_id
            else None
        ),
        "physical": stock_at(session, tenant_id, item.id),
        "commitments": list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id, Commitment.item_id == item.id
                )
            )
        ),
        "movements": item_movements,
        "handling_units": {
            unit.id: unit
            for unit in session.scalars(
                select(HandlingUnit).where(
                    HandlingUnit.tenant_id == tenant_id,
                    HandlingUnit.id.in_(handling_unit_ids),
                )
            )
        }
        if handling_unit_ids
        else {},
        "lots": {
            lot.id: lot
            for lot in session.scalars(
                select(Lot).where(
                    Lot.tenant_id == tenant_id,
                    Lot.id.in_(lot_ids),
                )
            )
        }
        if lot_ids
        else {},
        "serial_units": {
            serial.id: serial
            for serial in session.scalars(
                select(SerialUnit).where(
                    SerialUnit.tenant_id == tenant_id,
                    SerialUnit.id.in_(serial_unit_ids),
                )
            )
        }
        if serial_unit_ids
        else {},
        "reservations": list(
            session.scalars(
                select(Reservation).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.item_id == item.id,
                )
            )
        ),
    }


LOCATION_DETAIL_ROWS = 20


def location_detail(
    session: OrmSession, tenant_id: str, location_id: str
) -> dict[str, Any]:
    """What lies at one place, derived per company rather than per item (spec 262)."""
    location = _tenant_record(session, Location, tenant_id, location_id)
    arriving = func.sum(
        case((Movement.to_location_id == location.id, Movement.quantity), else_=ZERO)
    )
    leaving = func.sum(
        case((Movement.from_location_id == location.id, Movement.quantity), else_=ZERO)
    )
    held = arriving - leaving
    positions = (
        select(Item, held.label("physical"))
        .join(
            Movement,
            and_(Movement.tenant_id == Item.tenant_id, Movement.item_id == Item.id),
        )
        .where(Item.tenant_id == tenant_id, movement_at(location.id))
        .group_by(Item.tenant_id, Item.id)
        .having(held != ZERO)
    )
    at_location = (
        select(Movement)
        .where(Movement.tenant_id == tenant_id, movement_at(location.id))
        .order_by(Movement.occurred_at.desc(), Movement.id.desc())
    )
    return {
        "location": location,
        "source": (
            _tenant_record(session, SourceRecord, tenant_id, location.source_record_id)
            if location.source_record_id
            else None
        ),
        "stock": [
            {"item": item, "physical": decimal(physical)}
            for item, physical in session.execute(
                positions.order_by(Item.name, Item.id).limit(LOCATION_DETAIL_ROWS)
            )
        ],
        "stock_count": session.scalar(
            select(func.count()).select_from(positions.subquery())
        )
        or 0,
        "movements": list(session.scalars(at_location.limit(LOCATION_DETAIL_ROWS))),
        "movement_count": session.scalar(
            select(func.count()).where(
                Movement.tenant_id == tenant_id, movement_at(location.id)
            )
        )
        or 0,
        "commitment_count": session.scalar(
            select(func.count()).where(
                Commitment.tenant_id == tenant_id,
                Commitment.location_id == location.id,
            )
        )
        or 0,
    }


def _append_interpretation_outcome(
    session: OrmSession,
    tenant_id: str,
    source: SourceRecord,
    job: ImportJob,
    attempt: int,
    classification: str,
    *,
    interpreter_name: str = "",
    reason_code: str = "",
    summary: str = "",
    references: list[tuple[str, str]] | None = None,
) -> InterpretationOutcome:
    if classification not in INTERPRETATION_CLASSIFICATIONS:
        raise InvalidOperation("Unknown interpretation classification.")
    existing = session.scalar(
        select(InterpretationOutcome).where(
            InterpretationOutcome.tenant_id == tenant_id,
            InterpretationOutcome.import_job_id == job.id,
            InterpretationOutcome.attempt == attempt,
        )
    )
    if existing:
        return existing
    normalized = list(dict.fromkeys(references or []))
    if classification != "interpreted" and normalized:
        raise InvalidOperation(
            "Only interpreted outcomes may reference produced records."
        )
    if any(
        record_type not in INTERPRETATION_RECORD_TYPES for record_type, _ in normalized
    ):
        raise InvalidOperation("Unknown interpretation record type.")
    outcome = InterpretationOutcome(
        id=uid("ino"),
        tenant_id=tenant_id,
        source_record_id=source.id,
        import_job_id=job.id,
        attempt=attempt,
        classification=classification,
        interpreter_name=interpreter_name,
        interpreter_version="1",
        reason_code=reason_code,
        summary=summary[:240],
        completed_at=now(),
    )
    session.add(outcome)
    session.flush()
    for record_type, record_id in normalized:
        session.add(
            InterpretationRecordReference(
                id=uid("inr"),
                tenant_id=tenant_id,
                outcome_id=outcome.id,
                record_type=record_type,
                record_id=record_id,
            )
        )
    return outcome


_INTERPRETATION_FAMILIES = (
    (Document, "document"),
    (DocumentLine, "document_line"),
    (Commitment, "commitment"),
    (LedgerEntry, "ledger_entry"),
    (SettlementAllocation, "settlement_allocation"),
)


def _interpretation_references(result: Any) -> list[tuple[str, str]]:
    """Controlled produced-record references from any interpreter result shape."""
    if not isinstance(result, tuple):
        return []

    def flatten(items):
        for item in items:
            if isinstance(item, list | tuple):
                yield from flatten(item)
            else:
                yield item

    references = []
    for record in flatten(result):
        for model, family in _INTERPRETATION_FAMILIES:
            if isinstance(record, model):
                references.append((family, record.id))
                break
    return references


def enqueue_source(
    session: OrmSession,
    tenant_id: str,
    source_system: str,
    source_type: str,
    external_id: str,
    payload: dict[str, Any],
    *,
    source_version_at: datetime | str | None = None,
    context: dict[str, Any] | None = None,
    source_artifact_id: str | None = None,
    _commit: bool = True,
) -> tuple[SourceRecord, ImportJob]:
    _require_business_mutation(session, tenant_id, "enqueue_source")
    source_system, source_type, external_id = (
        source_system.strip().lower(),
        source_type.strip(),
        external_id.strip(),
    )
    if not source_system or not source_type or not external_id:
        raise InvalidOperation(
            "Source system, source type, and external ID are required."
        )
    if not isinstance(payload, dict):
        raise InvalidOperation("Source payload must be a JSON object.")
    if source_artifact_id:
        _tenant_record(session, SourceArtifact, tenant_id, source_artifact_id)
    source, created, disposition = store_source_record(
        session,
        tenant_id,
        source_system,
        source_type,
        external_id,
        payload,
        source_version_at=utc_datetime(source_version_at),
        source_artifact_id=source_artifact_id,
    )
    job = session.scalar(
        select(ImportJob).where(
            ImportJob.tenant_id == tenant_id,
            ImportJob.source_record_id == source.id,
        )
    )
    if job is None:
        # Artifact-backed uploads require an explicit file parser before a JSON
        # object interpreter may run. Never feed the artifact envelope into a
        # source-specific object interpreter merely because its labels match.
        interpreter_available = (
            source_artifact_id is None
            and (source_system, source_type) in SOURCE_INTERPRETERS
        ) or (
            source_artifact_id is not None
            and (context or {}).get("expected_target") in FILE_INTERPRETER_TARGETS
        )
        job = ImportJob(
            id=uid("imp"),
            tenant_id=tenant_id,
            source_record_id=source.id,
            status="pending" if interpreter_available else "unmapped",
            input=json.dumps(
                {**(context or {}), "disposition": disposition},
                separators=(",", ":"),
            ),
        )
        if disposition == "stale":
            job.status = "completed"
            job.error = "Stale source version stored without interpretation."
            job.completed_at = now()
        elif disposition == "conflict":
            job.status = "failed"
            job.error = "Conflicting payloads have the same upstream version timestamp."
        session.add(job)
        session.flush()
        intake_classification = {
            "unmapped": (
                "unsupported",
                "interpreter_unavailable",
                "No interpreter is registered for this source type.",
            ),
            "completed": (
                "stale",
                "stale_source_version",
                "The source version is older than the current version.",
            ),
            "failed": (
                "conflict",
                "source_version_conflict",
                "The source version conflicts with an existing payload.",
            ),
        }.get(job.status)
        if intake_classification:
            classification, reason_code, summary = intake_classification
            _append_interpretation_outcome(
                session,
                tenant_id,
                source,
                job,
                0,
                classification,
                reason_code=reason_code,
                summary=summary,
            )
        if created:
            emit_business_event(
                session,
                tenant_id,
                "source_record.received",
                "source_record",
                source.id,
                {
                    "source_system": source_system,
                    "source_type": source_type,
                    "external_id": external_id,
                    "version": source.version,
                    "disposition": disposition,
                },
                source_record_id=source.id,
            )
            if job.status == "unmapped":
                emit_business_event(
                    session,
                    tenant_id,
                    "source_record.unmapped",
                    "source_record",
                    source.id,
                    {"source_system": source_system, "source_type": source_type},
                    source_record_id=source.id,
                )
    if _commit:
        session.commit()
    else:
        session.flush()
    return source, job


def create_source_system(
    session: OrmSession,
    tenant_id: str,
    code: str,
    name: str,
    description: str = "",
    *,
    _commit: bool = True,
) -> SourceSystem:
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "source_system_create")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    code, name = code.strip().lower(), name.strip()
    if not code or not name:
        raise InvalidOperation("Source system code and name are required.")
    existing = session.scalar(
        select(SourceSystem).where(
            SourceSystem.tenant_id == tenant_id, SourceSystem.code == code
        )
    )
    if existing:
        raise InvalidOperation(f"Source system code already exists: {code}")
    system = SourceSystem(
        id=uid("sys"),
        tenant_id=tenant_id,
        code=code,
        name=name,
        description=description.strip(),
    )
    session.add(system)
    if _commit:
        session.commit()
    else:
        session.flush()
    return system


def install_connector_shell(
    session: OrmSession,
    tenant_id: str,
    connector_code: str,
    source_types: list[str] | None = None,
    system_code: str | None = None,
    system_name: str | None = None,
) -> SourceSystem:
    if connector_code == "demo_data":
        raise InvalidOperation(
            "Use the confirmed Demo Data connection preview in a compatible Sandbox."
        )
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "connector_install")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    try:
        shell = connector_shell(connector_code.strip().lower())
    except KeyError as error:
        raise NotFound("Connector shell not found.") from error
    selected_types = source_types or list(shell["capabilities"])
    unknown = set(selected_types) - set(shell["capabilities"])
    if not selected_types or unknown:
        detail = f": {', '.join(sorted(unknown))}" if unknown else ""
        raise InvalidOperation(f"Select valid source types{detail}.")
    instance_code = (system_code or shell["code"]).strip().lower()
    instance_name = (system_name or shell["name"]).strip()
    if not instance_code or not instance_name:
        raise InvalidOperation("Source system code and name are required.")
    existing = session.scalar(
        select(SourceSystem).where(
            SourceSystem.tenant_id == tenant_id,
            SourceSystem.code == instance_code,
        )
    )
    if existing:
        raise InvalidOperation(f"Source system already exists: {instance_code}")
    system = SourceSystem(
        id=uid("sys"),
        tenant_id=tenant_id,
        code=instance_code,
        name=instance_name,
        description=f"{shell['name']} {shell['category']} source definition · no connection",
        connector_code=shell["code"],
    )
    session.add(system)
    session.flush()
    for source_type in dict.fromkeys(selected_types):
        target_type = shell["capabilities"][source_type]
        session.add(
            SourceCapability(
                id=uid("cap"),
                tenant_id=tenant_id,
                source_system_id=system.id,
                source_type=source_type,
                target_type=target_type,
            )
        )
    session.commit()
    return system


def connector_shells(session: OrmSession, tenant_id: str) -> list[dict[str, Any]]:
    systems = source_systems(session, tenant_id)
    return [
        {
            **shell,
            # Grouped by the recorded connector only. The description prefix this
            # once tested is ambiguous between connectors whose display names share
            # a prefix, which listed one instance under two shells (spec 211).
            "instances": [
                system for system in systems if system.connector_code == shell["code"]
            ],
        }
        for shell in connector_catalog()["connectors"]
    ]


def source_systems(session: OrmSession, tenant_id: str) -> list[SourceSystem]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(SourceSystem)
            .where(SourceSystem.tenant_id == tenant_id)
            .order_by(SourceSystem.name, SourceSystem.code)
        )
    )


def source_capabilities(session: OrmSession, tenant_id: str) -> list[SourceCapability]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(SourceCapability)
            .where(SourceCapability.tenant_id == tenant_id)
            .order_by(SourceCapability.source_type, SourceCapability.target_type)
        )
    )


def set_source_system_active(
    session: OrmSession, tenant_id: str, source_system_id: str, is_active: bool
) -> SourceSystem:
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "source_system_update")
    system = _tenant_record(session, SourceSystem, tenant_id, source_system_id)
    system.is_active = is_active
    system.updated_at = now()
    session.commit()
    return system


def set_source_system_base_url(
    session: OrmSession, tenant_id: str, source_system_id: str, base_url: str
) -> SourceSystem:
    """Configure where this instance's records can be opened, or clear it.

    Configuration only: the address is never called and holds no credential, so
    the integration registry stays descriptive.
    """
    from reality.services.provenance import validate_base_url
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "source_system_update")
    system = _tenant_record(session, SourceSystem, tenant_id, source_system_id)
    try:
        system.base_url = validate_base_url(base_url) or None
    except ValueError as error:
        raise InvalidOperation(str(error)) from error
    system.updated_at = now()
    session.commit()
    return system


def create_source_capability(
    session: OrmSession,
    tenant_id: str,
    source_system_id: str,
    source_type: str,
    target_type: str,
    *,
    _commit: bool = True,
) -> SourceCapability:
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "source_capability_create")
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    system = _tenant_record(session, SourceSystem, tenant_id, source_system_id)
    source_type, target_type = source_type.strip(), target_type.strip()
    if not source_type or not target_type:
        raise InvalidOperation("Source type and target type are required.")
    existing = session.scalar(
        select(SourceCapability).where(
            SourceCapability.tenant_id == tenant_id,
            SourceCapability.source_system_id == system.id,
            SourceCapability.source_type == source_type,
        )
    )
    if existing:
        raise InvalidOperation(
            f"Source capability already exists: {system.code}/{source_type}"
        )
    capability = SourceCapability(
        id=uid("cap"),
        tenant_id=tenant_id,
        source_system_id=system.id,
        source_type=source_type,
        target_type=target_type,
    )
    session.add(capability)
    if _commit:
        session.commit()
    else:
        session.flush()
    return capability


def set_source_capability_active(
    session: OrmSession, tenant_id: str, capability_id: str, is_active: bool
) -> SourceCapability:
    from reality.services.tenant_policy import require_business_operation

    require_business_operation(session, tenant_id, "source_capability_update")
    capability = _tenant_record(session, SourceCapability, tenant_id, capability_id)
    capability.is_active = is_active
    capability.updated_at = now()
    session.commit()
    return capability


def integration_registry(session: OrmSession, tenant_id: str) -> dict[str, Any]:
    systems = source_systems(session, tenant_id)
    capabilities = source_capabilities(session, tenant_id)
    records = source_records(session, tenant_id)
    jobs = import_jobs(session, tenant_id)
    records_by_system: dict[str, int] = {}
    for record in records:
        records_by_system[record.source_system] = (
            records_by_system.get(record.source_system, 0) + 1
        )
    jobs_by_source = {job.source_record_id: job for job in jobs}
    system_by_id = {system.id: system for system in systems}
    return {
        "systems": systems,
        "capabilities": [
            {
                "capability": capability,
                "system": system_by_id[capability.source_system_id],
                "interpreter_available": (
                    system_by_id[capability.source_system_id].code,
                    capability.source_type,
                )
                in SOURCE_INTERPRETERS,
            }
            for capability in capabilities
        ],
        "record_counts": records_by_system,
        "recent_records": records[:10],
        "jobs_by_source": jobs_by_source,
    }


def enqueue_shopify_order(
    session: OrmSession,
    tenant_id: str,
    payload: dict[str, Any],
    company_party_id: str,
    customer_party_id: str,
    location_id: str,
) -> tuple[SourceRecord, ImportJob]:
    _require_business_mutation(session, tenant_id, "enqueue_shopify_order")
    _tenant_record(session, Party, tenant_id, company_party_id)
    _tenant_record(session, Party, tenant_id, customer_party_id)
    _tenant_record(session, Location, tenant_id, location_id)
    external_id = str(payload["id"])
    return enqueue_source(
        session,
        tenant_id,
        "shopify",
        "order",
        external_id,
        payload,
        source_version_at=payload.get("updated_at"),
        context={
            "company_party_id": company_party_id,
            "customer_party_id": customer_party_id,
            "location_id": location_id,
        },
    )


def _shopify_interpretation(
    session: OrmSession, tenant_id: str, source: SourceRecord, context: dict[str, str]
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Commitment]]:
    existing_document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.source_record_id == source.id,
            Document.type == "sales_order",
        )
    )
    if existing_document:
        lines = list(
            session.scalars(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.document_id == existing_document.id,
                )
            )
        )
        commitments_created = list(
            session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.document_id == existing_document.id,
                )
            )
        )
        return source, existing_document, lines, commitments_created

    if source.version > 1:
        raise ShopifyUpdateNeedsReview()

    company_party_id = context["company_party_id"]
    customer_party_id = context["customer_party_id"]
    location_id = context["location_id"]
    _tenant_record(session, Party, tenant_id, company_party_id)
    _tenant_record(session, Party, tenant_id, customer_party_id)
    _tenant_record(session, Location, tenant_id, location_id)
    payload = json.loads(source.payload)
    items_by_sku = {}
    for raw_line in payload.get("line_items", []):
        sku = str(raw_line.get("sku", ""))
        item = session.scalar(
            select(Item).where(Item.tenant_id == tenant_id, Item.sku == sku)
        )
        if item is None:
            raise InvalidOperation(f"Unknown SKU: {sku}")
        items_by_sku[sku] = item

    promised_at = next(
        (
            attribute.get("value", "")
            for attribute in payload.get("note_attributes", [])
            if attribute.get("name") == "requested_delivery"
        ),
        "",
    )
    document = Document(
        id=uid("doc"),
        tenant_id=tenant_id,
        source_record_id=source.id,
        type="sales_order",
        number=str(
            payload.get("name") or f"#{payload.get('order_number', source.external_id)}"
        ),
        party_id=customer_party_id,
        currency=payload.get("currency", "EUR"),
        gross_amount=decimal(payload.get("total_price", 0)),
        status="recorded",
        document_date=_document_day(payload.get("created_at")),
        ordered_at=utc_datetime(payload.get("created_at")),
        requested_delivery_at=utc_datetime(promised_at),
        sales_channel="shopify",
    )
    session.add(document)
    session.flush()
    lines: list[DocumentLine] = []
    commitments_created: list[Commitment] = []
    for raw_line in payload.get("line_items", []):
        item = items_by_sku[str(raw_line.get("sku", ""))]
        quantity = positive(raw_line["quantity"])
        price = decimal(raw_line.get("price", 0))
        raw_line_id = raw_line.get("id")
        line = DocumentLine(
            id=uid("lin"),
            tenant_id=tenant_id,
            document_id=document.id,
            source_line_id=str(raw_line_id) if raw_line_id is not None else None,
            item_id=item.id,
            sku=item.sku,
            description=str(raw_line.get("name") or raw_line.get("title") or item.name),
            quantity=quantity,
            unit_price=price,
            gross_amount=quantity * price,
            promised_at=promised_at,
            unit=item.unit,
            requested_at=utc_datetime(promised_at),
            line_type="item",
            payload=json.dumps(raw_line, ensure_ascii=False, separators=(",", ":")),
        )
        session.add(line)
        session.flush()
        commitment = Commitment(
            id=uid("com"),
            tenant_id=tenant_id,
            type="customer_delivery",
            from_party_id=company_party_id,
            to_party_id=customer_party_id,
            item_id=item.id,
            location_id=location_id,
            quantity=quantity,
            amount=quantity * price,
            currency=document.currency,
            due_at=utc_datetime(promised_at),
            status="open",
            document_id=document.id,
            document_line_id=line.id,
        )
        session.add(commitment)
        lines.append(line)
        commitments_created.append(commitment)

    session.add(
        ChangeProposal(
            id=uid("act"),
            tenant_id=tenant_id,
            type="shopify_order_interpreted",
            input=json.dumps({"source_record_id": source.id}),
            output=json.dumps(
                {
                    "document_id": document.id,
                    "commitment_ids": [item.id for item in commitments_created],
                }
            ),
        )
    )
    emit_business_event(
        session,
        tenant_id,
        "document.recorded",
        "document",
        document.id,
        {
            "type": document.type,
            "number": document.number,
            "party_id": customer_party_id,
            "amount": document.gross_amount,
            "currency": document.currency,
        },
        source_record_id=source.id,
    )
    for commitment in commitments_created:
        emit_business_event(
            session,
            tenant_id,
            "commitment.created",
            "commitment",
            commitment.id,
            {
                "type": commitment.type,
                "item_id": commitment.item_id,
                "quantity": commitment.quantity,
                "document_id": document.id,
            },
            source_record_id=source.id,
            correlation_id=source.id,
        )
    return source, document, lines, commitments_created


def _demo_interpretation(session, tenant_id, source, context):
    from reality.integrations.demo_data import interpret

    return interpret(session, tenant_id, source, context)


def _demo_invoice_interpretation(session, tenant_id, source, context):
    from reality.integrations.demo_data import interpret_invoice

    return interpret_invoice(session, tenant_id, source, context)


def _demo_payment_interpretation(session, tenant_id, source, context):
    from reality.integrations.demo_data import interpret_payment

    return interpret_payment(session, tenant_id, source, context)


SOURCE_INTERPRETERS = {
    ("shopify", "order"): _shopify_interpretation,
    ("demo_data", "order"): _demo_interpretation,
    ("demo_data", "invoice"): _demo_invoice_interpretation,
    ("demo_data", "payment"): _demo_payment_interpretation,
}
# Synthetic pairs the scheduler may interpret inside its own transaction.
SYNTHETIC_SOURCES = frozenset(
    pair for pair in SOURCE_INTERPRETERS if pair[0] == "demo_data"
)


def _import_review_outcome(
    session: OrmSession, tenant_id: str, job: ImportJob
) -> InterpretationOutcome | None:
    return session.scalar(
        select(InterpretationOutcome)
        .where(
            InterpretationOutcome.tenant_id == tenant_id,
            InterpretationOutcome.import_job_id == job.id,
            InterpretationOutcome.attempt == job.attempts,
            InterpretationOutcome.classification == "needs_review",
        )
        .limit(1)
    )


def process_import_job_bound(
    session: OrmSession, tenant_id: str, job_id: str
) -> Any | None:
    """Interpret synthetic intake within the caller transaction and a business savepoint.

    Expected validation failures retain their intake and safe outcome. Database,
    timeout and programming failures propagate so the worker can retry atomically.
    """
    from pydantic import ValidationError

    _require_business_mutation(session, tenant_id, "process_import_job")
    job = session.scalar(
        select(ImportJob)
        .where(ImportJob.tenant_id == tenant_id, ImportJob.id == job_id)
        .with_for_update()
    )
    if job is None:
        raise NotFound("ImportJob not found.")
    source = _tenant_record(session, SourceRecord, tenant_id, job.source_record_id)
    pair = (source.source_system, source.source_type)
    if pair not in SYNTHETIC_SOURCES:
        raise InvalidOperation(
            "Bound interpretation requires the registered Demo Data source."
        )
    kind = source.source_type
    interpreter = SOURCE_INTERPRETERS[pair]
    if job.status == "completed":
        return interpreter(session, tenant_id, source, json.loads(job.input))
    job.attempts += 1
    job.status, job.error = "processing", ""
    session.flush()
    try:
        with session.begin_nested():
            result = interpreter(session, tenant_id, source, json.loads(job.input))
            session.flush()
    except (InvalidOperation, ValidationError):
        job.status, job.error = "failed", f"Demo {kind} could not be interpreted."
        job.next_attempt_at = None
        _append_interpretation_outcome(
            session,
            tenant_id,
            source,
            job,
            job.attempts,
            "failed",
            interpreter_name=f"demo_data.{kind}",
            reason_code="interpreter_error",
            summary=f"The synthetic {kind} failed validation; its business changes were rolled back.",
        )
        session.flush()
        return None
    job.status, job.completed_at, job.next_attempt_at = "completed", now(), None
    _append_interpretation_outcome(
        session,
        tenant_id,
        source,
        job,
        job.attempts,
        "interpreted",
        interpreter_name=f"demo_data.{kind}",
        reason_code="interpretation_completed",
        summary=f"The synthetic {kind} was interpreted successfully.",
        references=_interpretation_references(result),
    )
    emit_business_event(
        session,
        tenant_id,
        "source_record.interpreted",
        "source_record",
        source.id,
        {"source_system": "demo_data", "source_type": kind, "import_job_id": job.id},
        source_record_id=source.id,
    )
    session.flush()
    return result


def process_import_job(session: OrmSession, tenant_id: str, job_id: str) -> Any | None:
    _require_business_mutation(session, tenant_id, "process_import_job")
    job = session.scalar(
        select(ImportJob)
        .where(ImportJob.tenant_id == tenant_id, ImportJob.id == job_id)
        .with_for_update()
    )
    if job is None:
        raise NotFound("ImportJob not found.")
    source = _tenant_record(session, SourceRecord, tenant_id, job.source_record_id)
    if (source.source_system, source.source_type) == ("demo_data", "order"):
        result = process_import_job_bound(session, tenant_id, job_id)
        failed = job.status == "failed"
        session.commit()
        if failed:
            raise InvalidOperation("Demo order could not be interpreted.")
        return result
    context = json.loads(job.input)
    if (
        source.source_artifact_id
        and context.get("expected_target") in FILE_INTERPRETER_TARGETS
    ):
        from reality.services.file_interpreters import interpret_artifact

        interpreter = interpret_artifact
    elif source.source_artifact_id:
        interpreter = None
    else:
        interpreter = SOURCE_INTERPRETERS.get(
            (source.source_system, source.source_type)
        )
    if interpreter is None:
        job.status = "unmapped"
        job.error = "No interpreter registered for this source system and type."
        _append_interpretation_outcome(
            session,
            tenant_id,
            source,
            job,
            0,
            "unsupported",
            reason_code="interpreter_unavailable",
            summary="No interpreter is registered for this source type.",
        )
        session.commit()
        return None
    if job.status == "completed":
        if source.source_artifact_id and context.get("expected_target") == "item":
            identities = list(
                session.scalars(
                    select(BusinessEvent.subject_id)
                    .where(
                        BusinessEvent.tenant_id == tenant_id,
                        BusinessEvent.source_record_id == source.id,
                        BusinessEvent.event_type == "item.created",
                    )
                    .order_by(BusinessEvent.subject_id)
                )
            )
            return {
                "target": "item",
                "rows": len(identities),
                "created_ids": identities,
            }
        if context.get("disposition") == "stale":
            return None
        if _import_review_outcome(session, tenant_id, job):
            return None
        return interpreter(session, tenant_id, source, context)
    if context.get("disposition") == "conflict":
        raise InvalidOperation(job.error)

    attempt = job.attempts + 1
    job.status = "processing"
    job.attempts = attempt
    job.error = ""
    try:
        result = interpreter(session, tenant_id, source, context)
        job.status = "completed"
        job.completed_at = now()
        job.next_attempt_at = None
        interpreter_name = (
            f"{source.source_system}.{source.source_type}"
            if not source.source_artifact_id
            else f"file.{context.get('expected_target', 'unknown')}"
        )
        _append_interpretation_outcome(
            session,
            tenant_id,
            source,
            job,
            attempt,
            "interpreted",
            interpreter_name=interpreter_name,
            reason_code="interpretation_completed",
            summary="The source was interpreted successfully.",
            references=_interpretation_references(result),
        )
        emit_business_event(
            session,
            tenant_id,
            "source_record.interpreted",
            "source_record",
            source.id,
            {
                "source_system": source.source_system,
                "source_type": source.source_type,
                "import_job_id": job.id,
            },
            source_record_id=source.id,
        )
        session.commit()
        from reality.services.reality_gaps import evaluate_active_rules

        evaluate_active_rules(session, tenant_id, source.id)
        return result
    except InterpretationNeedsReview as error:
        session.rollback()
        shopify_update = isinstance(error, ShopifyUpdateNeedsReview)
        summary = (
            ShopifyUpdateNeedsReview.summary
            if shopify_update
            else "The source requires human review before Reality can be created."
        )
        review_job = _tenant_record(session, ImportJob, tenant_id, job_id)
        review_job.status = "completed"
        review_job.attempts = attempt
        review_job.error = (
            summary if shopify_update else "Business meaning requires review."
        )
        review_job.completed_at = now()
        review_job.next_attempt_at = None
        review_source = _tenant_record(
            session, SourceRecord, tenant_id, review_job.source_record_id
        )
        _append_interpretation_outcome(
            session,
            tenant_id,
            review_source,
            review_job,
            attempt,
            "needs_review",
            interpreter_name=f"{review_source.source_system}.{review_source.source_type}",
            reason_code=(
                "shopify_update_requires_review"
                if shopify_update
                else "ambiguous_business_meaning"
            ),
            summary=summary,
        )
        session.commit()
        return None
    except Exception as error:
        session.rollback()
        failed_job = _tenant_record(session, ImportJob, tenant_id, job_id)
        failed_job.status = "failed"
        failed_job.attempts = attempt
        failed_job.error = str(error)
        failed_job.next_attempt_at = now() + timedelta(seconds=min(2**attempt, 300))
        failed_source = _tenant_record(
            session, SourceRecord, tenant_id, failed_job.source_record_id
        )
        _append_interpretation_outcome(
            session,
            tenant_id,
            failed_source,
            failed_job,
            attempt,
            "failed",
            interpreter_name=f"{failed_source.source_system}.{failed_source.source_type}",
            reason_code="interpreter_error",
            summary="The interpreter failed; its business changes were rolled back.",
        )
        session.commit()
        raise


def process_shopify_import_job(
    session: OrmSession, tenant_id: str, job_id: str
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Commitment]] | None:
    _require_business_mutation(session, tenant_id, "process_shopify_import_job")
    job = _tenant_record(session, ImportJob, tenant_id, job_id)
    source = _tenant_record(session, SourceRecord, tenant_id, job.source_record_id)
    if (source.source_system, source.source_type) != ("shopify", "order"):
        raise InvalidOperation("Import job is not a Shopify order.")
    return process_import_job(session, tenant_id, job_id)


def process_pending_import_jobs(
    session: OrmSession, tenant_id: str, *, limit: int = 100
) -> tuple[int, int]:
    _require_business_mutation(session, tenant_id, "process_pending_import_jobs")
    job_ids = list(
        session.scalars(
            select(ImportJob.id)
            .where(
                ImportJob.tenant_id == tenant_id,
                (ImportJob.status == "pending")
                | (
                    (ImportJob.status == "failed")
                    & (ImportJob.next_attempt_at.is_not(None))
                    & (ImportJob.next_attempt_at <= now())
                ),
            )
            .order_by(ImportJob.created_at)
            .limit(limit)
        )
    )
    completed = failed = 0
    for job_id in job_ids:
        try:
            if process_import_job(session, tenant_id, job_id):
                completed += 1
        except RealityError:
            failed += 1
    return completed, failed


def source_records(session: OrmSession, tenant_id: str) -> list[SourceRecord]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(SourceRecord)
            .where(SourceRecord.tenant_id == tenant_id)
            .order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
        )
    )


def import_jobs(session: OrmSession, tenant_id: str) -> list[ImportJob]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    return list(
        session.scalars(
            select(ImportJob)
            .where(ImportJob.tenant_id == tenant_id)
            .order_by(ImportJob.created_at.desc())
        )
    )


def interpretation_coverage(
    session: OrmSession, tenant_id: str, source_record_id: str | None = None
) -> list[dict[str, Any]]:
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    statement = select(SourceRecord).where(SourceRecord.tenant_id == tenant_id)
    if source_record_id:
        _tenant_record(session, SourceRecord, tenant_id, source_record_id)
        statement = statement.where(SourceRecord.id == source_record_id)
    sources = list(
        session.scalars(
            statement.order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
        )
    )
    rows: list[dict[str, Any]] = []
    for source in sources:
        job = session.scalar(
            select(ImportJob).where(
                ImportJob.tenant_id == tenant_id,
                ImportJob.source_record_id == source.id,
            )
        )
        outcomes = (
            list(
                session.scalars(
                    select(InterpretationOutcome)
                    .where(
                        InterpretationOutcome.tenant_id == tenant_id,
                        InterpretationOutcome.source_record_id == source.id,
                    )
                    .order_by(
                        InterpretationOutcome.attempt,
                        InterpretationOutcome.completed_at,
                    )
                )
            )
            if job
            else []
        )
        serialized = []
        for outcome in outcomes:
            references = list(
                session.scalars(
                    select(InterpretationRecordReference)
                    .where(
                        InterpretationRecordReference.tenant_id == tenant_id,
                        InterpretationRecordReference.outcome_id == outcome.id,
                    )
                    .order_by(
                        InterpretationRecordReference.record_type,
                        InterpretationRecordReference.record_id,
                    )
                )
            )
            serialized.append(
                {
                    "outcome_id": outcome.id,
                    "attempt": outcome.attempt,
                    "classification": outcome.classification,
                    "interpreter_name": outcome.interpreter_name,
                    "interpreter_version": outcome.interpreter_version,
                    "reason_code": outcome.reason_code,
                    "summary": outcome.summary,
                    "completed_at": outcome.completed_at.isoformat(),
                    "produced_records": [
                        {
                            "record_type": reference.record_type,
                            "record_id": reference.record_id,
                        }
                        for reference in references
                    ],
                }
            )
        current = (
            serialized[-1]["classification"]
            if serialized
            else (
                job.status
                if job and job.status in {"pending", "processing"}
                else "not_recorded"
            )
        )
        rows.append(
            {
                "source_record_id": source.id,
                "source_system": source.source_system,
                "source_type": source.source_type,
                "external_id": source.external_id,
                "received_at": source.received_at.isoformat(),
                "import_job_id": job.id if job else None,
                "job_status": job.status if job else None,
                "job_attempts": job.attempts if job else 0,
                "current_classification": current,
                "outcomes": serialized,
            }
        )
    return rows


def retry_import_job(session: OrmSession, tenant_id: str, job_id: str) -> ImportJob:
    _require_business_mutation(session, tenant_id, "retry_import_job")
    job = _tenant_record(session, ImportJob, tenant_id, job_id)
    source = _tenant_record(session, SourceRecord, tenant_id, job.source_record_id)
    context = json.loads(job.input)
    supported_file = (
        bool(source.source_artifact_id)
        and context.get("expected_target") in FILE_INTERPRETER_TARGETS
    )
    if (
        job.status == "completed"
        and source.source_artifact_id
        and context.get("expected_target") == "item"
    ):
        return job
    if (
        not supported_file
        and (source.source_system, source.source_type) not in SOURCE_INTERPRETERS
    ):
        job.status = "unmapped"
        job.error = "No interpreter registered for this source system and type."
    else:
        job.status = "pending"
        job.error = ""
        job.next_attempt_at = None
    session.commit()
    return job


def ingest_shopify_order(
    session: OrmSession,
    tenant_id: str,
    payload: dict[str, Any],
    company_party_id: str,
    customer_party_id: str,
    location_id: str,
) -> tuple[SourceRecord, Document, list[DocumentLine], list[Commitment]]:
    _require_business_mutation(session, tenant_id, "ingest_shopify_order")
    _source, job = enqueue_shopify_order(
        session,
        tenant_id,
        payload,
        company_party_id,
        customer_party_id,
        location_id,
    )
    result = process_shopify_import_job(session, tenant_id, job.id)
    if result is None:
        review = _import_review_outcome(session, tenant_id, job)
        if review:
            raise InvalidOperation(review.summary)
        raise InvalidOperation(
            "Stale source version was stored without interpretation."
        )
    return result


def explain_commitment(
    session: OrmSession, tenant_id: str, commitment_id: str
) -> dict[str, Any]:
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    reservations = list(
        session.scalars(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
            )
        )
    )
    movements = list(
        session.scalars(
            select(Movement).where(
                Movement.tenant_id == tenant_id, Movement.commitment_id == commitment.id
            )
        )
    )
    line = (
        _tenant_record(session, DocumentLine, tenant_id, commitment.document_line_id)
        if commitment.document_line_id
        else None
    )
    document = (
        _tenant_record(session, Document, tenant_id, commitment.document_id)
        if commitment.document_id
        else None
    )
    source = (
        _tenant_record(session, SourceRecord, tenant_id, document.source_record_id)
        if document and document.source_record_id
        else None
    )
    return {
        "commitment": commitment,
        "reservations": reservations,
        "movements": movements,
        "fulfilled": fulfilled_quantity(session, tenant_id, commitment.id),
        "open": open_quantity(session, tenant_id, commitment.id),
        "risk": risk(commitment, session),
        "document_line": line,
        "document": document,
        "source_record": source,
        "raw_source": json.loads(source.payload) if source else None,
    }


def timeline(
    session: OrmSession,
    tenant_id: str,
    records: dict[str, Iterable[str]] | None = None,
) -> list[tuple[Any, str, str, str]]:
    """The company's records in time order — all of them, or the named ones.

    `records` maps a record kind (`source_record`, `commitment`, `reservation`,
    `movement`, `ledger_entry`) to the ids to read. It changes which rows come back,
    never how one is derived: a row prints its own record's fields and, where the
    record names an article, that article's name (spec 181 FR-002).
    """

    def read(model, kind):
        statement = select(model).where(model.tenant_id == tenant_id)
        if records is None:
            return list(session.scalars(statement))
        ids = set(records.get(kind) or ())
        if not ids:
            return []
        return list(session.scalars(statement.where(model.id.in_(ids))))

    sources = read(SourceRecord, "source_record")
    promises = read(Commitment, "commitment")
    reservations = read(Reservation, "reservation")
    movements = read(Movement, "movement")
    entries = read(LedgerEntry, "ledger_entry")

    # One item read for the whole timeline instead of one per commitment,
    # reservation and movement (spec 181).
    item_ids = {
        record.item_id
        for record in (*promises, *reservations, *movements)
        if record.item_id
    }
    item_query = select(Item).where(Item.tenant_id == tenant_id)
    if records is not None:
        item_query = item_query.where(Item.id.in_(item_ids)) if item_ids else None
    item_names = (
        {}
        if item_query is None
        else {
            row.id: getattr(row, "name", None) or row.sku or row.id
            for row in session.scalars(item_query)
        }
    )

    def item_name(item_id: str | None) -> str:
        if not item_id:
            return "—"
        return item_names.get(item_id, item_id)

    rows = []
    for record in sources:
        rows.append(
            (
                record.received_at,
                "SOURCE",
                f"{record.source_system} {record.source_type} {record.external_id}",
                record.id,
            )
        )
    for record in promises:
        rows.append(
            (
                record.created_at,
                "COMMITMENT",
                f"{record.type}: {record.quantity:g} × {item_name(record.item_id)}",
                record.id,
            )
        )
    for record in reservations:
        rows.append(
            (
                record.reserved_at,
                "RESERVATION",
                f"{record.quantity:g} × {item_name(record.item_id)}",
                record.id,
            )
        )
    for record in movements:
        rows.append(
            (
                record.occurred_at,
                "MOVEMENT",
                f"{record.type}: {record.quantity:g} × {item_name(record.item_id)}",
                record.id,
            )
        )
    for record in entries:
        rows.append(
            (
                record.effective_at,
                "LEDGER",
                f"{record.account}: {record.debit_credit} {record.amount:g} {record.currency}",
                record.id,
            )
        )
    return sorted(rows, key=lambda row: utc_datetime(row[0]), reverse=True)


def _warehouse_identity_maps(session: OrmSession, tenant_id: str) -> dict[str, dict]:
    """Load only identities inside the requested tenant boundary."""
    return {
        "items": {
            row.id: row
            for row in session.scalars(select(Item).where(Item.tenant_id == tenant_id))
        },
        "locations": {
            row.id: row
            for row in session.scalars(
                select(Location).where(Location.tenant_id == tenant_id)
            )
        },
        "handling_units": {
            row.id: row
            for row in session.scalars(
                select(HandlingUnit).where(HandlingUnit.tenant_id == tenant_id)
            )
        },
        "lots": {
            row.id: row
            for row in session.scalars(select(Lot).where(Lot.tenant_id == tenant_id))
        },
        "serial_units": {
            row.id: row
            for row in session.scalars(
                select(SerialUnit).where(SerialUnit.tenant_id == tenant_id)
            )
        },
    }


def reservation_register(session: OrmSession, tenant_id: str) -> list[dict[str, Any]]:
    """Return reservation bindings for warehouse control."""
    identities = _warehouse_identity_maps(session, tenant_id)
    records = session.scalars(
        select(Reservation)
        .where(Reservation.tenant_id == tenant_id)
        .order_by(Reservation.reserved_at.desc())
    )
    return [
        {
            "reservation": record,
            "item": identities["items"].get(record.item_id),
            "location": identities["locations"].get(record.location_id),
            "handling_unit": identities["handling_units"].get(record.handling_unit_id),
            "lot": identities["lots"].get(record.lot_id),
            "serial_unit": identities["serial_units"].get(record.serial_unit_id),
        }
        for record in records
    ]


def movement_register(session: OrmSession, tenant_id: str) -> list[dict[str, Any]]:
    """Return the append-only physical movement journal."""
    identities = _warehouse_identity_maps(session, tenant_id)
    records = session.scalars(
        select(Movement)
        .where(Movement.tenant_id == tenant_id)
        .order_by(Movement.occurred_at.desc())
    )
    return [
        {
            "movement": record,
            "item": identities["items"].get(record.item_id),
            "from_location": identities["locations"].get(record.from_location_id),
            "to_location": identities["locations"].get(record.to_location_id),
            "handling_unit": identities["handling_units"].get(record.handling_unit_id),
            "lot": identities["lots"].get(record.lot_id),
            "serial_unit": identities["serial_units"].get(record.serial_unit_id),
        }
        for record in records
    ]


def warehouse_identity_registers(
    session: OrmSession, tenant_id: str
) -> dict[str, list[dict[str, Any]]]:
    """Return searchable NVE, lot, and serial identities with current position."""
    identities = _warehouse_identity_maps(session, tenant_id)
    movements = movement_register(session, tenant_id)

    def current_location(identity_key: str, identity_id: str) -> Location | None:
        balances: dict[str, Decimal] = {}
        for row in movements:
            identity = row[identity_key]
            if identity and identity.id == identity_id:
                quantity = row["movement"].quantity
                if row["from_location"] is not None:
                    location_id = row["from_location"].id
                    balances[location_id] = balances.get(location_id, ZERO) - quantity
                if row["to_location"] is not None:
                    location_id = row["to_location"].id
                    balances[location_id] = balances.get(location_id, ZERO) + quantity
        positive_locations = [
            identities["locations"].get(location_id)
            for location_id, quantity in balances.items()
            if quantity > ZERO
        ]
        # A single register location is only truthful when the net movement legs
        # resolve to exactly one positive tenant location.
        return positive_locations[0] if len(positive_locations) == 1 else None

    return {
        "handling_units": [
            {"record": row, "location": current_location("handling_unit", row.id)}
            for row in identities["handling_units"].values()
        ],
        "lots": [
            {
                "record": row,
                "item": identities["items"].get(row.item_id),
                "location": current_location("lot", row.id),
            }
            for row in identities["lots"].values()
        ],
        "serial_units": [
            {
                "record": row,
                "item": identities["items"].get(row.item_id),
                "lot": identities["lots"].get(row.lot_id),
                "location": current_location("serial_unit", row.id),
            }
            for row in identities["serial_units"].values()
        ],
    }


def settlement_register(
    session: OrmSession, tenant_id: str, *, limit: int = 100
) -> list[dict[str, Any]]:
    """Return payment-to-invoice settlement links for reconciliation."""
    allocations = list(
        session.scalars(
            select(SettlementAllocation)
            .where(SettlementAllocation.tenant_id == tenant_id)
            .order_by(SettlementAllocation.allocated_at.desc())
            .limit(max(1, min(limit, 100)))
        )
    )
    entry_ids = {
        entry_id
        for row in allocations
        for entry_id in (row.payment_ledger_entry_id, row.invoice_ledger_entry_id)
    }
    entries = (
        {
            row.id: row
            for row in session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == tenant_id, LedgerEntry.id.in_(entry_ids)
                )
            )
        }
        if entry_ids
        else {}
    )
    document_ids = {row.document_id for row in entries.values() if row.document_id}
    documents = (
        {
            row.id: row
            for row in session.scalars(
                select(Document).where(
                    Document.tenant_id == tenant_id, Document.id.in_(document_ids)
                )
            )
        }
        if document_ids
        else {}
    )
    return [
        {
            "allocation": row,
            "payment": entries.get(row.payment_ledger_entry_id),
            "invoice": entries.get(row.invoice_ledger_entry_id),
            "document": documents.get(
                entries.get(row.invoice_ledger_entry_id).document_id
                if entries.get(row.invoice_ledger_entry_id)
                else ""
            ),
        }
        for row in allocations
    ]


def effective_payment_term(
    document: Document,
    party_payment_term_id: str | None,
    terms: dict[str, PaymentTerm],
) -> PaymentTerm | None:
    """Which term governs an invoice: its own, else its party's, else none.

    Commercial terms are usually agreed with the customer rather than restated
    on every invoice, so the party's term stands in when the invoice carries
    none. Only when neither exists is the invoice due on issue.
    """
    return terms.get(document.payment_term_id or party_payment_term_id or "")


def invoice_due_date(document: Document, term: PaymentTerm | None) -> date | None:
    """When an invoice is due: its own date advanced by the payment term.

    An invoice carrying no date asserts nothing; without any applicable term the
    invoice is due on its own date.
    """
    document_day = document.document_date
    if document_day is None:
        return None
    return document_day + timedelta(days=term.due_days) if term else document_day


def invoice_discount_date(document: Document, term: PaymentTerm | None) -> date | None:
    """When an early-payment discount stops being available, if there is one.

    The same shape of question as the due date and answered in the same place,
    so that the register, the queue and anything else asking cannot drift apart
    about when a window closes. A term granting no discount places no window,
    and neither does an invoice whose own date cannot be read.
    """
    if term is None or term.discount_percent is None or term.discount_days is None:
        return None
    document_day = document.document_date
    if document_day is None:
        return None
    return document_day + timedelta(days=term.discount_days)


def invoice_days_overdue(due_date: date | None, as_of: datetime) -> int | None:
    """Whole days between the due date and the evaluation instant, never below zero."""
    if due_date is None:
        return None
    return max((as_of.date() - due_date).days, 0)


def _payment_terms_by_id(session: OrmSession, tenant_id: str) -> dict[str, PaymentTerm]:
    return {
        row.id: row
        for row in session.scalars(
            select(PaymentTerm).where(PaymentTerm.tenant_id == tenant_id)
        )
    }


def with_invoice_aging(
    rows: list[dict[str, Any]], terms: dict[str, PaymentTerm], as_of: datetime
) -> list[dict[str, Any]]:
    """Enrich open-item rows with the one due-date rule."""
    enriched = []
    for row in rows:
        # Resolved once and passed on, so the window and the due date are always
        # about the same term and no consumer resolves a second one.
        term = effective_payment_term(
            row["document"], row.get("party_payment_term_id"), terms
        )
        if row.get("origin") == "opening":
            term = None
            due_date = row.get("original_due_date")
        else:
            due_date = invoice_due_date(row["document"], term)
        enriched.append(
            {
                **row,
                "due_date": due_date,
                "days_overdue": invoice_days_overdue(due_date, as_of),
                "payment_term": term,
                "discount_date": None
                if row.get("origin") == "opening"
                else invoice_discount_date(row["document"], term),
            }
        )
    return enriched


def aging_register(
    session: OrmSession,
    tenant_id: str,
    *,
    as_of: datetime | None = None,
    document_ids: set[str] | None = None,
    party_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Derive due dates and aging, optionally for a bounded set of documents."""
    return with_invoice_aging(
        _financial_open_items(
            session, tenant_id, document_ids=document_ids, party_ids=party_ids
        ),
        _payment_terms_by_id(session, tenant_id),
        as_of or now(),
    )


# Why a supplier invoice a payment run may not pay was left out. Reported rather
# than silently dropped, because an operator who cannot see what was withheld
# cannot tell a short run from a wrong one.
PAYMENT_RUN_WITHHELD_REASONS = {
    "reversed": "The posting behind this invoice has been reversed.",
    "duplicate": "This invoice carries a number its supplier already used.",
    "settled": "This invoice has nothing open.",
}


def _payment_run_needed_on(row: dict[str, Any], today: date) -> date | None:
    """The day the money is needed: an open discount deadline, else the due date.

    A window that has already closed is not a deadline any more, so the invoice
    falls back to when it is actually due.
    """
    deadline = row["discount_date"]
    if deadline is not None and deadline >= today:
        return deadline
    return row["due_date"]


def payable_supplier_invoices(
    session: OrmSession, tenant_id: str, *, as_of: datetime | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Every supplier invoice a payment run may pay, and every one it may not.

    One rule, asked by the preview and by the run. Two answers to "may this be
    paid" is how a proposal and the operation that executes it start disagreeing
    about money.

    Payable means a supplier invoice, not reversed, with something open, and not
    already reported as a duplicate. The duplicate is the one exclusion here that
    refuses rather than warns: paying it is money that does not come back, and
    the class has a clearing path — reverse the wrong posting, or confirm the
    numbers differ — so refusing traps nobody.

    A sales invoice is absent from both lists rather than withheld. It was never
    a candidate, and reporting it as one would bury the invoices that were.
    """
    moment = as_of or now()
    duplicates = {
        duplicate.id for duplicate, _ in duplicate_supplier_invoices(session, tenant_id)
    }
    payable: list[dict[str, Any]] = []
    withheld: list[dict[str, Any]] = []
    for row in aging_register(session, tenant_id, as_of=moment):
        if row["document"].type != "supplier_invoice":
            continue
        reason = (
            "reversed"
            if row["status"] == "reversed"
            else "duplicate"
            if row["document"].id in duplicates
            else "settled"
            if decimal(row["open"]) <= ZERO
            else None
        )
        if reason is None:
            payable.append(row)
        else:
            withheld.append({**row, "withheld_because": reason})
    return payable, withheld


def _payment_run_entry(row: dict[str, Any], today: date) -> dict[str, Any]:
    """One line of a proposal.

    The rate and the day the window closes are named; what the discount is worth
    is not. A rate applied to a gross amount is a division producing money nobody
    agreed to, with a remainder somebody has to round, and the rounded figure
    would become what a supplier is told they were paid.
    """
    document = row["document"]
    term = row["payment_term"]
    deadline = row["discount_date"]
    discount_open = deadline is not None and deadline >= today
    return {
        "invoice_id": document.id,
        "number": document.number,
        "party_id": document.party_id,
        "supplier": row["party"],
        "currency": document.currency,
        "open_amount": decimal(row["open"]),
        "due_date": row["due_date"],
        "days_overdue": row["days_overdue"],
        "needed_on": _payment_run_needed_on(row, today),
        "discount_percent": (
            decimal(term.discount_percent)
            if discount_open and term is not None and term.discount_percent is not None
            else None
        ),
        "discount_date": deadline if discount_open else None,
    }


def preview_payment_run(
    session: OrmSession,
    tenant_id: str,
    *,
    pay_by: datetime | str,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """What is worth paying now, without paying any of it.

    Two kinds of invoice belong in the answer: one that is due by the stated day,
    and one whose early-payment window has not closed yet. The second is why the
    early-payment-discount class named a payment run in its own guidance — an
    invoice nobody has to pay for another month can still be the one worth paying
    this afternoon.

    Every figure comes from the aging register, so this proposal, that register
    and the operational exception queue cannot disagree about what an invoice
    owes.
    """
    get_tenant(session, tenant_id)
    moment = as_of or now()
    today = moment.date()
    cutoff_moment = utc_datetime(pay_by)
    if cutoff_moment is None:
        raise InvalidOperation("A payment run preview needs a day to pay by.")
    cutoff = cutoff_moment.date()
    payable, withheld = payable_supplier_invoices(session, tenant_id, as_of=moment)
    proposed = []
    for row in payable:
        due_date = row["due_date"]
        deadline = row["discount_date"]
        if (due_date is not None and due_date <= cutoff) or (
            deadline is not None and deadline >= today
        ):
            proposed.append(_payment_run_entry(row, today))
    # Soonest money first, and a line with no date at all last rather than first:
    # an invoice nobody can date is not urgent, it is unanswered. Identity breaks
    # every tie, so two identical reads return an identical answer.
    proposed.sort(
        key=lambda entry: (
            entry["needed_on"] is None,
            entry["needed_on"] or today,
            entry["invoice_id"],
        )
    )
    suppliers: dict[tuple[str, str], dict[str, Any]] = {}
    totals: dict[str, dict[str, Any]] = {}
    for entry in proposed:
        supplier = suppliers.setdefault(
            (entry["party_id"] or "", entry["currency"]),
            {
                "party_id": entry["party_id"],
                "supplier": entry["supplier"],
                "currency": entry["currency"],
                "count": 0,
                "open_amount": ZERO,
            },
        )
        supplier["count"] += 1
        supplier["open_amount"] += entry["open_amount"]
        # Totalled per currency, never across them. A run pays in one currency,
        # and a sum of two currencies is not a total.
        total = totals.setdefault(
            entry["currency"],
            {"currency": entry["currency"], "count": 0, "open_amount": ZERO},
        )
        total["count"] += 1
        total["open_amount"] += entry["open_amount"]
    return {
        "as_of": moment,
        "pay_by": cutoff,
        "count": len(proposed),
        "proposed": proposed,
        "suppliers": sorted(
            suppliers.values(),
            key=lambda row: (row["currency"], row["supplier"], row["party_id"] or ""),
        ),
        "totals": sorted(totals.values(), key=lambda row: row["currency"]),
        "withheld": sorted(
            (
                {
                    "invoice_id": row["document"].id,
                    "number": row["document"].number,
                    "supplier": row["party"],
                    "currency": row["document"].currency,
                    "open_amount": decimal(row["open"]),
                    "reason": row["withheld_because"],
                    "explanation": PAYMENT_RUN_WITHHELD_REASONS[
                        row["withheld_because"]
                    ],
                }
                for row in withheld
            ),
            key=lambda row: (row["reason"], row["invoice_id"]),
        ),
    }


def execute_payment_run(
    session: OrmSession,
    tenant_id: str,
    *,
    payments: list[dict[str, Any]],
    currency: str,
    expected_total,
    reason: str,
    effective_at: datetime | None = None,
    action_id: str | None = None,
    actor_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pay what somebody confirmed, all of it or none of it.

    Every amount here was stated by the caller. Nothing multiplies a gross amount
    by a discount rate, because that produces money nobody agreed to; the preview
    names the rate and a person decides what to pay against it.

    The confirmation figure is a total rather than a count. Spec 085 confirmed a
    count because a count was what the person had looked at; here a person
    approves an amount of money and the list is usually assembled by a client
    from the proposal, where every line can be right and the sum still wrong.

    Everything is refused before anything is written, and the whole run commits
    once. The alternative is a Friday where nineteen payments went out and
    twenty-one did not and somebody has to work out which.
    """
    _require_business_mutation(session, tenant_id, "execute_payment_run")
    get_tenant(session, tenant_id)
    stated_reason = (reason or "").strip()
    if not stated_reason:
        raise InvalidOperation("A payment run requires a reason.")
    if not payments:
        raise InvalidOperation("A payment run needs at least one payment.")
    run_currency = (currency or "").strip()
    if not run_currency:
        raise InvalidOperation("A payment run needs the currency it is paid in.")
    confirmed_total = decimal(expected_total)
    stated: list[tuple[str, Decimal, str | None]] = []
    seen: set[str] = set()
    for item in payments:
        invoice_id = item["invoice_id"]
        if invoice_id in seen:
            raise InvalidOperation("A payment run names each invoice once.")
        seen.add(invoice_id)
        stated.append(
            (invoice_id, positive(item["amount"], "amount"), item.get("payment_number"))
        )
    total = sum((amount for _, amount, _ in stated), ZERO)
    if total != confirmed_total:
        raise InvalidOperation(
            "The payment run no longer matches the confirmed total: "
            f"{total} stated, {confirmed_total} confirmed."
        )
    payable, withheld = payable_supplier_invoices(session, tenant_id)
    rows = {row["document"].id: row for row in payable}
    refusals = {row["document"].id: row["withheld_because"] for row in withheld}
    for invoice_id, amount, _ in stated:
        row = rows.get(invoice_id)
        if row is None:
            withheld_because = refusals.get(invoice_id)
            raise InvalidOperation(
                PAYMENT_RUN_WITHHELD_REASONS[withheld_because]
                if withheld_because
                else "A payment run pays open supplier invoices of this tenant only."
            )
        if row["document"].currency.strip().upper() != run_currency.upper():
            raise InvalidOperation(
                "A payment run pays in one currency: "
                f"{row['document'].currency} does not match {run_currency}."
            )
        if amount > decimal(row["open"]):
            raise InvalidOperation("Payment exceeds the open supplier payable.")
    paid: list[dict[str, Any]] = []
    try:
        for invoice_id, amount, payment_number in stated:
            entries = post_supplier_payment(
                session,
                tenant_id,
                invoice_id,
                amount,
                payment_number=payment_number,
                effective_at=effective_at,
                action_id=action_id,
                _commit=False,
            )
            paid.append(
                {
                    "invoice_id": invoice_id,
                    "amount": amount,
                    "payment_document_id": _control_entry(
                        entries, "accounts_payable"
                    ).document_id,
                }
            )
        emit_business_event(
            session,
            tenant_id,
            "payments.run",
            "tenant",
            tenant_id,
            {
                "reason": stated_reason,
                "currency": run_currency,
                "total": total,
                "count": len(paid),
                "payments": paid,
                "actor_context": actor_context or {},
            },
            action_id=action_id,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {
        "paid": len(paid),
        "total": total,
        "currency": run_currency,
        "reason": stated_reason,
        "payments": paid,
    }


def system_control_registers(
    session: OrmSession, tenant_id: str
) -> dict[str, list[Any]]:
    """Return tenant-scoped control-plane registers without exposing secrets."""
    get_tenant(session, tenant_id)
    return {
        "import_jobs": list(
            session.scalars(
                select(ImportJob)
                .where(ImportJob.tenant_id == tenant_id)
                .order_by(ImportJob.created_at.desc())
            )
        ),
        "projections": list(
            session.scalars(
                select(ProjectionCheckpoint)
                .where(ProjectionCheckpoint.tenant_id == tenant_id)
                .order_by(ProjectionCheckpoint.projection_name)
            )
        ),
        "actions": list(
            session.scalars(
                select(ChangeProposal)
                .where(ChangeProposal.tenant_id == tenant_id)
                .order_by(ChangeProposal.created_at.desc())
            )
        ),
        "source_records": list(
            session.scalars(
                select(SourceRecord)
                .where(SourceRecord.tenant_id == tenant_id)
                .order_by(SourceRecord.received_at.desc())
            )
        ),
    }


def hold_register(
    session: OrmSession, tenant_id: str, *, limit: int = 100
) -> list[dict[str, Any]]:
    """Return active and released execution controls in one audit register."""
    safe_limit = max(1, min(limit, 100))
    commitment_holds = list(
        session.scalars(
            select(CommitmentHold)
            .where(CommitmentHold.tenant_id == tenant_id)
            .order_by(CommitmentHold.created_at.desc())
            .limit(safe_limit)
        )
    )
    party_holds = list(
        session.scalars(
            select(PartyHold)
            .where(PartyHold.tenant_id == tenant_id)
            .order_by(PartyHold.created_at.desc())
            .limit(safe_limit)
        )
    )
    commitment_ids = {row.commitment_id for row in commitment_holds}
    party_ids = {row.party_id for row in party_holds}
    commitments_by_id = (
        {
            row.id: row
            for row in session.scalars(
                select(Commitment).where(
                    Commitment.tenant_id == tenant_id, Commitment.id.in_(commitment_ids)
                )
            )
        }
        if commitment_ids
        else {}
    )
    parties_by_id = (
        {
            row.id: row
            for row in session.scalars(
                select(Party).where(
                    Party.tenant_id == tenant_id, Party.id.in_(party_ids)
                )
            )
        }
        if party_ids
        else {}
    )
    rows = [
        {
            "kind": "Commitment",
            "hold": hold,
            "subject": commitments_by_id.get(hold.commitment_id),
            "label": hold.commitment_id,
        }
        for hold in commitment_holds
    ]
    rows.extend(
        {
            "kind": "Delivery",
            "hold": hold,
            "subject": parties_by_id.get(hold.party_id),
            "label": parties_by_id.get(hold.party_id).name
            if parties_by_id.get(hold.party_id)
            else hold.party_id,
        }
        for hold in party_holds
    )
    return sorted(rows, key=lambda row: row["hold"].created_at, reverse=True)[
        :safe_limit
    ]


def timeline_activity(
    session: OrmSession,
    tenant_id: str,
    *,
    query: str = "",
    area: str = "",
    status: str = "",
    hours: int = 24,
    limit: int = 100,
    before_sequence: int | None = None,
    record_type: str = "",
    after_sequence: int | None = None,
    _subject_filter: ColumnElement[bool] | None = None,
) -> dict[str, Any]:
    """Tenant-scoped activity projection for the operational timeline UI.

    Paging runs backwards from ``before_sequence`` by default. ``after_sequence``
    switches to a forward read in ascending order: everything recorded after a
    marker, which is how a Storyline chapter reads its delta (spec 182). The two
    cursors exclude each other; the time filter is not applied to a forward read
    because a marker already bounds it.
    """
    _tenant_record(session, Tenant, tenant_id, tenant_id)
    if before_sequence is not None and after_sequence is not None:
        raise InvalidOperation("Use either before_sequence or after_sequence.")
    forward = after_sequence is not None
    since = now() - timedelta(hours=max(1, min(hours, 24 * 30)))
    criteria = [BusinessEvent.tenant_id == tenant_id]
    if _subject_filter is not None:
        criteria.append(_subject_filter)
    if hours != 0 and not forward:
        criteria.append(BusinessEvent.occurred_at >= since)
    if before_sequence is not None:
        criteria.append(BusinessEvent.sequence < before_sequence)
    if forward:
        criteria.append(BusinessEvent.sequence > after_sequence)
    if record_type == "ledger_entry":
        criteria.append(
            BusinessEvent.subject_type.in_(("ledger_entry", "posting_group"))
        )
    elif record_type:
        criteria.append(BusinessEvent.subject_type == record_type)
    if query:
        pattern = f"%{query.strip().lower()}%"
        criteria.append(
            or_(
                func.lower(BusinessEvent.event_type).like(pattern),
                func.lower(BusinessEvent.subject_type).like(pattern),
                func.lower(BusinessEvent.subject_id).like(pattern),
                func.lower(BusinessEvent.payload).like(pattern),
                func.lower(func.coalesce(BusinessEvent.source_record_id, "")).like(
                    pattern
                ),
                *(
                    select(reference.id)
                    .where(
                        reference.tenant_id == tenant_id,
                        func.lower(reference.name).like(pattern),
                        or_(
                            BusinessEvent.subject_id == reference.id,
                            func.strpos(BusinessEvent.payload, '"' + reference.id + '"')
                            > 0,
                        ),
                    )
                    .exists()
                    for reference in (Party, Item, Location)
                ),
            )
        )
    area_prefixes = {
        "sources": ("source_record.%", "document.%"),
        "finance": ("ledger_entry.%", "ledger.%", "payment.%", "settlement.%"),
        "operations": ("commitment.%", "reservation.%", "movement.%"),
        "warehouse": ("reservation.%", "movement.%"),
    }
    if area in {"sales", "purchasing"}:
        document_types = (
            ("sales_order", "sales_invoice", "credit_note")
            if area == "sales"
            else ("purchase_order", "supplier_invoice", "supplier_credit")
        )
        criteria.append(
            select(Document.id)
            .where(
                Document.tenant_id == tenant_id,
                Document.type.in_(document_types),
                or_(
                    and_(
                        BusinessEvent.subject_type == "document",
                        BusinessEvent.subject_id == Document.id,
                    ),
                    BusinessEvent.source_record_id == Document.source_record_id,
                ),
            )
            .exists()
        )
    elif area in area_prefixes:
        criteria.append(
            or_(
                *(BusinessEvent.event_type.like(value) for value in area_prefixes[area])
            )
        )
    elif area == "master_data":
        known = tuple(value for values in area_prefixes.values() for value in values)
        criteria.append(
            and_(*(BusinessEvent.event_type.not_like(value) for value in known))
        )
    attention = _attention_event_condition()
    if status == "attention":
        criteria.append(attention)
    elif status == "completed":
        criteria.append(~attention)
    statement = (
        select(BusinessEvent)
        .where(*criteria)
        .order_by(
            BusinessEvent.sequence.asc() if forward else BusinessEvent.sequence.desc()
        )
        .limit(limit + 1)
    )
    records = list(session.scalars(statement))

    def event_area(event_type: str) -> str:
        prefix = event_type.split(".", 1)[0]
        if prefix in {"source_record", "document"}:
            return "sources"
        if prefix in {"ledger_entry", "payment", "settlement"}:
            return "finance"
        if prefix in {"commitment", "reservation", "movement"}:
            return "operations"
        return "master_data"

    def event_status(event_type: str, payload: dict[str, Any]) -> str:
        text_value = f"{event_type} {payload.get('disposition', '')}".lower()
        return (
            "attention"
            if any(
                x in text_value
                for x in ("failed", "unmapped", "conflict", "error", "rejected")
            )
            else "completed"
        )

    events = []
    for event in records:
        payload = json.loads(event.payload or "{}")
        event_view = {
            "id": event.id,
            "sequence": event.sequence,
            "type": event.event_type,
            "subject_type": event.subject_type,
            "subject_id": event.subject_id,
            "occurred_at": event.occurred_at,
            "recorded_at": event.recorded_at,
            "payload": payload,
            "source_record_id": event.source_record_id,
            "action_id": event.action_id,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "area": event_area(event.event_type),
            "status": event_status(event.event_type, payload),
        }
        events.append(event_view)
    from reality.services.decision_attribution import decision_attributions

    # Which decision caused each change, and who settled it (spec 263 FR-010).
    decisions = decision_attributions(
        session, tenant_id, {event["action_id"] for event in events}
    )
    for event in events:
        event["decision"] = decisions.get(event["action_id"] or "")

    party_ids = {
        str(event["payload"]["party_id"])
        for event in events
        if event["payload"].get("party_id")
    }
    item_ids = {
        str(event["payload"]["item_id"])
        for event in events
        if event["payload"].get("item_id")
    }
    source_record_ids = {
        str(event["source_record_id"]) for event in events if event["source_record_id"]
    }
    party_names = (
        {
            row_id: name
            for row_id, name in session.execute(
                select(Party.id, Party.name).where(
                    Party.tenant_id == tenant_id, Party.id.in_(party_ids)
                )
            )
        }
        if party_ids
        else {}
    )
    item_names = (
        {
            row_id: name
            for row_id, name in session.execute(
                select(Item.id, Item.name).where(
                    Item.tenant_id == tenant_id, Item.id.in_(item_ids)
                )
            )
        }
        if item_ids
        else {}
    )
    source_context = (
        {
            row_id: {
                "source_system": source_system,
                "source_type": source_type,
                "external_id": external_id,
            }
            for row_id, source_system, source_type, external_id in session.execute(
                select(
                    SourceRecord.id,
                    SourceRecord.source_system,
                    SourceRecord.source_type,
                    SourceRecord.external_id,
                ).where(
                    SourceRecord.tenant_id == tenant_id,
                    SourceRecord.id.in_(source_record_ids),
                )
            )
        }
        if source_record_ids
        else {}
    )

    def display_name(value: Any) -> str:
        return str(value or "").replace("_", " ").strip().capitalize()

    event_titles = {
        "party.created": "Business partner created",
        "item.created": "Item created",
        "location.created": "Location created",
        "source_record.received": "Source received",
        "source_record.stored": "Source recorded by confirmed action",
        "source_record.interpreted": "Source processing completed",
        "source_record.unmapped": "Source needs mapping",
        "document.recorded": "Business document recorded",
        "commitment.created": "Delivery commitment created",
        "commitment.changed": "Delivery commitment changed",
        "commitment.fulfilled": "Delivery commitment fulfilled",
        "reservation.created": "Inventory reserved",
        "reservation.released": "Inventory reservation released",
        "reservation.consumed": "Inventory reservation consumed",
        "movement.recorded": "Inventory movement recorded",
        "ledger_entry.recorded": "Ledger entry recorded",
    }
    for event in events:
        payload = event["payload"]
        event_type = event["type"]
        title = event_titles.get(event_type)
        if event_type == "document.recorded" and payload.get("type"):
            title = f"{display_name(payload['type'])} recorded"
        if not title:
            prefix, _, action = event_type.partition(".")
            title = f"{display_name(prefix)} {display_name(action)}".strip()
        details: list[str] = []
        if payload.get("name"):
            details.append(str(payload["name"]))
        if payload.get("sku"):
            details.append(str(payload["sku"]))
        if payload.get("number"):
            details.append(str(payload["number"]))
        if payload.get("external_id"):
            details.append(str(payload["external_id"]))
        if payload.get("source_system"):
            details.append(display_name(payload["source_system"]))
        party_name = party_names.get(str(payload.get("party_id", "")))
        if party_name:
            details.append(party_name)
        item_name = item_names.get(str(payload.get("item_id", "")))
        if item_name:
            details.append(item_name)
        if payload.get("quantity") is not None:
            details.append(f"Quantity {payload['quantity']}")
        if payload.get("amount") is not None:
            amount = f"{payload['amount']} {payload.get('currency', '')}".strip()
            details.append(amount)
        event["business_title"] = title
        event["business_detail"] = " · ".join(dict.fromkeys(details))
        event["business_context"] = {
            "party": party_name,
            "item": item_name,
            "name": payload.get("name"),
            "sku": payload.get("sku"),
            "reference": payload.get("number"),
            "quantity": payload.get("quantity"),
            "amount": payload.get("amount"),
            "currency": payload.get("currency"),
            "unit": payload.get("unit"),
        }

    groups: dict[str, dict[str, Any]] = {}
    for event in events[:limit]:
        key = event["correlation_id"] or event["source_record_id"] or event["id"]
        group = groups.setdefault(key, {"id": key, "events": [], "status": "completed"})
        group["events"].append(event)
        if event["status"] == "attention":
            group["status"] = "attention"
    activities = []
    for group in groups.values():
        newest = group["events"][0]
        oldest = group["events"][-1]
        payload = newest["payload"]
        document_event = next(
            (
                event
                for event in group["events"]
                if event["type"] == "document.recorded"
            ),
            None,
        )
        source_event = next(
            (
                event
                for event in group["events"]
                if event["type"] == "source_record.received"
            ),
            None,
        )
        title = (
            payload.get("number")
            or payload.get("external_id")
            or newest["subject_type"].replace("_", " ").title()
        )
        if document_event:
            document_payload = document_event["payload"]
            document_kind = display_name(document_payload.get("type") or "Document")
            reference = document_payload.get("number")
            business_title = (
                f"{document_kind}{f' {reference}' if reference else ''} processed"
            )
        elif source_event:
            source_payload = source_event["payload"]
            source_kind = display_name(source_payload.get("source_type") or "Source")
            reference = source_payload.get("external_id")
            business_title = (
                f"{source_kind}{f' {reference}' if reference else ''} processed"
            )
        else:
            business_title = newest["business_title"]
        context: list[str] = []
        source = source_context.get(str(newest.get("source_record_id") or ""))
        if source:
            context.append(display_name(source["source_system"]))
        for event in group["events"]:
            event_payload = event["payload"]
            if event_payload.get("source_system"):
                context.append(display_name(event_payload["source_system"]))
            party_name = party_names.get(str(event_payload.get("party_id", "")))
            if party_name:
                context.append(party_name)
        event_count = len(group["events"])
        context.append(f"{event_count} step{'s' if event_count != 1 else ''}")
        group.update(
            title=str(title),
            subtitle=f"{len(group['events'])} event{'s' if len(group['events']) != 1 else ''} · {newest['area'].replace('_', ' ').title()}",
            business_title=business_title,
            business_detail=" · ".join(dict.fromkeys(context)),
            occurred_at=newest["occurred_at"],
            duration_ms=max(
                0,
                int(
                    (newest["recorded_at"] - oldest["occurred_at"]).total_seconds()
                    * 1000
                ),
            ),
        )
        activities.append(group)

    current_time = now()
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_criteria = (
        BusinessEvent.tenant_id == tenant_id,
        BusinessEvent.occurred_at >= today_start,
    )
    event_count = int(
        session.scalar(
            select(func.count()).select_from(BusinessEvent).where(*today_criteria)
        )
        or 0
    )
    exceptions = int(
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(*today_criteria, attention)
        )
        or 0
    )
    orders = int(
        session.scalar(
            select(func.count())
            .select_from(BusinessEvent)
            .where(
                *today_criteria,
                BusinessEvent.event_type == "document.recorded",
                or_(
                    BusinessEvent.payload.like('%"type": "sales_order"%'),
                    BusinessEvent.payload.like('%"type": "customer_order"%'),
                ),
            )
        )
        or 0
    )
    today_records = [r for r in records if r.occurred_at.date() == current_time.date()]
    latencies = [
        max(0, (r.recorded_at - r.occurred_at).total_seconds() * 1000)
        for r in today_records
    ]
    chart = []
    # Hour bucketing remains UTC and normalizes for the in-memory comparison.
    current = current_time.replace(tzinfo=None, minute=0, second=0, microsecond=0)
    chart_start = current - timedelta(hours=23)
    hour_expression = func.extract("hour", BusinessEvent.occurred_at)
    bucket_rows = session.execute(
        select(
            hour_expression.label("hour"),
            func.count().label("count"),
            func.sum(case((attention, 1), else_=0)).label("attention"),
        )
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.occurred_at >= chart_start,
            BusinessEvent.occurred_at < current + timedelta(hours=1),
        )
        .group_by(hour_expression)
    )
    buckets = {
        int(hour): (int(count), int(attention_count or 0))
        for hour, count, attention_count in bucket_rows
    }
    for offset in range(23, -1, -1):
        start = current - timedelta(hours=offset)
        bucket_count, attention_count = buckets.get(start.hour, (0, 0))
        chart.append(
            {
                "label": start.strftime("%H:%M"),
                "count": bucket_count,
                "attention": attention_count,
            }
        )
    latest_source = session.scalar(
        select(func.max(BusinessEvent.occurred_at)).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.event_type == "source_record.received",
        )
    )
    return {
        "activities": activities,
        "business_counts": {
            key: int(
                session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.tenant_id == tenant_id, model.type.in_(types))
                )
                or 0
            )
            for key, model, types in (
                ("sales_orders", Document, ("sales_order",)),
                ("purchase_orders", Document, ("purchase_order",)),
                ("deliveries", Movement, ("shipment", "receipt")),
                ("invoices", Document, ("sales_invoice", "supplier_invoice")),
            )
        },
        "record_counts": {
            key: int(
                session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.tenant_id == tenant_id)
                )
                or 0
            )
            for key, model in (
                ("document", Document),
                ("commitment", Commitment),
                ("movement", Movement),
                ("ledger_entry", LedgerEntry),
            )
        },
        "events": events[:limit],
        "chart": chart,
        "summary": {
            "events": event_count,
            "orders": orders,
            "exceptions": exceptions,
            "latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
            "latest_source": latest_source,
        },
        "has_more": len(events) > limit,
    }


def ensure_demo(session: OrmSession, tenant: Tenant) -> None:
    _require_business_mutation(session, tenant.id, "ensure_demo")
    if session.scalar(select(func.count(Party.id)).where(Party.tenant_id == tenant.id)):
        return
    company = create_party(session, tenant.id, "Acme Bikes GmbH", "company")
    customer = create_party(session, tenant.id, "Müller GmbH", "customer")
    supplier = create_party(session, tenant.id, "Bike Parts GmbH", "supplier")
    location = create_location(session, tenant.id, "Augsburg Warehouse")
    item = create_item(session, tenant.id, "BIKE-LIGHT", "Bike Light")
    record_movement(
        session, tenant.id, "opening_stock", item.id, 20, to_location_id=location.id
    )
    today = datetime.now(UTC).date()
    raw = {
        "id": 5837291038,
        "order_number": 10473,
        "name": "#10473",
        "created_at": f"{today.isoformat()}T09:15:00Z",
        "currency": "EUR",
        "total_price": "1470.00",
        "customer": {"name": "Müller GmbH"},
        "line_items": [
            {
                "id": 8172,
                "sku": "BIKE-LIGHT",
                "name": "Bike Light",
                "quantity": 30,
                "price": "49.00",
            }
        ],
        "note_attributes": [
            {
                "name": "requested_delivery",
                "value": str(today + timedelta(days=1)),
            }
        ],
        "tags": "web-demo",
    }
    _, _, _, outgoing = ingest_shopify_order(
        session, tenant.id, raw, company.id, customer.id, location.id
    )
    reserve(session, tenant.id, outgoing[0].id)
    create_commitment(
        session,
        tenant.id,
        "supplier_delivery",
        supplier.id,
        company.id,
        item.id,
        location.id,
        20,
        str(today + timedelta(days=2)),
        amount=600,
    )
    chat_session = ChatSession(
        id=uid("cht"), tenant_id=tenant.id, title="Why can’t Müller ship?"
    )
    session.add(chat_session)
    session.flush()
    session.add_all(
        [
            ChatMessage(
                id=uid("msg"),
                tenant_id=tenant.id,
                session_id=chat_session.id,
                role="user",
                content="Why can’t Müller ship tomorrow?",
            ),
            ChatMessage(
                id=uid("msg"),
                tenant_id=tenant.id,
                session_id=chat_session.id,
                role="assistant",
                content="Müller needs 30 Bike Lights tomorrow. 20 are reserved, so 10 are currently missing.",
            ),
        ]
    )
    session.commit()


def _record_copilot_turn(
    own_provider, managed_key, outcome: str, seconds: float | None = None
) -> None:
    """Separate a real model answer from the deterministic fallback.

    Both return HTTP 200, so no amount of request-level instrumentation can
    tell them apart. `outcome=fallback` with a configured provider is the
    signal that the Copilot is degraded -- the state the deployment sat in
    while the managed key was missing and the UI looked perfectly healthy.
    """
    try:
        from reality.telemetry.metrics import copilot_turn

        if own_provider:
            provider = "tenant"
        elif managed_key:
            provider = "managed"
        else:
            provider = "none"
        copilot_turn(provider, outcome, seconds)
    except Exception:
        # A metric must never break a chat turn.
        logging.getLogger(__name__).debug("copilot metric failed", exc_info=True)
