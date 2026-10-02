"""Delivery rules: how a customer, or one of its orders, wants to be delivered (spec 306).

partial_allowed (the default), ship_complete (the whole order at once) or
no_backorders (what does not ship with the first shipment is cancelled, not
delivered later). A rule is a statement a person makes with a reason. An
order's rule wins over its customer's.

Every statement is a version of one source stream per subject (spec 320
pattern); the row names the one in force, and the history is the stream.
Whether an order is complete is never stored: readiness and the findings read
the promises, stock and reservations each time they are asked.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    DeliveryRule,
    Document,
    Party,
    PartyRole,
    SourceRecord,
    now,
    uid,
)
from reality.services.business_locks import lock_delivery_state
from reality.services.core import (
    InvalidOperation,
    _require_business_mutation,
    _tenant_record,
    emit_business_event,
    store_source_record,
)

RULES = ("partial_allowed", "ship_complete", "no_backorders")
DEFAULT_RULE = "partial_allowed"
SOURCE_SYSTEM = "internal_delivery_rule"
SOURCE_TYPE = "delivery_rule"
# A review that saw nothing, distinct from a call that checks nothing.
UNCHECKED: Any = object()


def _is_customer(session: Session, tenant_id: str, party: Party) -> bool:
    if party.type == "customer":
        return True
    return (
        session.scalar(
            select(PartyRole.id).where(
                PartyRole.tenant_id == tenant_id,
                PartyRole.party_id == party.id,
                PartyRole.role == "customer",
            )
        )
        is not None
    )


def _order_customer(session: Session, tenant_id: str, document: Document) -> str:
    """The customer an order delivers to, or refuse what is no customer order."""
    customer = session.scalar(
        select(Commitment.to_party_id)
        .where(
            Commitment.tenant_id == tenant_id,
            Commitment.document_id == document.id,
            Commitment.type == "customer_delivery",
        )
        .limit(1)
    )
    if customer is None:
        raise InvalidOperation(code="delivery_rule_document_not_order")
    return customer


def _subject(
    session: Session,
    tenant_id: str,
    party_id: str | None,
    document_id: str | None,
) -> tuple[str, str]:
    """('party' | 'document', id) of exactly one checked subject."""
    if bool(party_id) == bool(document_id):
        raise InvalidOperation(code="delivery_rule_subject_required")
    if party_id:
        party = _tenant_record(session, Party, tenant_id, party_id)
        if not _is_customer(session, tenant_id, party):
            raise InvalidOperation(code="delivery_rule_party_not_customer")
        return "party", party.id
    document = _tenant_record(session, Document, tenant_id, str(document_id))
    _order_customer(session, tenant_id, document)
    return "document", document.id


def _current(
    session: Session, tenant_id: str, kind: str, identity: str
) -> DeliveryRule | None:
    column = DeliveryRule.party_id if kind == "party" else DeliveryRule.document_id
    return session.scalar(
        select(DeliveryRule).where(
            DeliveryRule.tenant_id == tenant_id, column == identity
        )
    )


def validate_delivery_rule(
    session: Session,
    tenant_id: str,
    rule: str,
    reason: str,
    *,
    party_id: str | None = None,
    document_id: str | None = None,
) -> tuple[str, str, str, str]:
    """The checks a statement makes, also run by its review so both refuse alike."""
    kind, identity = _subject(session, tenant_id, party_id, document_id)
    if rule not in RULES:
        raise InvalidOperation(code="delivery_rule_unknown")
    stated = str(reason or "").strip()
    if not stated:
        raise InvalidOperation(code="delivery_rule_reason_required")
    return kind, identity, rule, stated


def rule_values(rule: DeliveryRule | None) -> dict[str, str] | None:
    """What a review shows and an execution compares, or None without a rule."""
    if rule is None:
        return None
    return {"rule": rule.rule, "reason": rule.reason}


def state_delivery_rule(
    session: Session,
    tenant_id: str,
    rule: str,
    reason: str,
    *,
    party_id: str | None = None,
    document_id: str | None = None,
    action_id: str | None = None,
    _expected: Any = UNCHECKED,
    _commit: bool = True,
) -> DeliveryRule:
    """State, or restate, the delivery rule of a customer or an order."""
    _require_business_mutation(session, tenant_id, "state_delivery_rule")
    lock_delivery_state(session, tenant_id)
    kind, identity, rule, stated = validate_delivery_rule(
        session, tenant_id, rule, reason, party_id=party_id, document_id=document_id
    )
    current = _current(session, tenant_id, kind, identity)
    if _expected is not UNCHECKED and rule_values(current) != _expected:
        raise InvalidOperation(code="delivery_rule_changed_since_review")
    previous = rule_values(current)
    # The statement id makes each confirmation its own version, so restating
    # an earlier rule is not taken for that earlier statement, while a replay
    # of the same confirmation is.
    source, _, _ = store_source_record(
        session,
        tenant_id,
        SOURCE_SYSTEM,
        SOURCE_TYPE,
        f"{kind}:{identity}",
        {
            f"{kind}_id": identity,
            "rule": rule,
            "reason": stated,
            "statement_id": action_id or uid("stm"),
        },
    )
    if current is None:
        current = DeliveryRule(
            id=uid("dlr"),
            tenant_id=tenant_id,
            party_id=identity if kind == "party" else None,
            document_id=identity if kind == "document" else None,
            rule=rule,
            reason=stated,
            source_record_id=source.id,
        )
        session.add(current)
    elif current.source_record_id != source.id:
        current.rule = rule
        current.reason = stated
        current.source_record_id = source.id
        current.updated_at = now()
    else:
        # The same confirmation again: it already stated this.
        return current
    session.flush()
    emit_business_event(
        session,
        tenant_id,
        "delivery_rule.stated",
        "delivery_rule",
        current.id,
        {
            f"{kind}_id": identity,
            "rule": rule,
            "reason": stated,
            **({"previous": previous} if previous else {}),
        },
        source_record_id=source.id,
        action_id=action_id,
        correlation_id=action_id,
    )
    if _commit:
        session.commit()
    return current


def _entry(rule: DeliveryRule, source: str, subject_id: str) -> dict[str, Any]:
    return {
        "rule": rule.rule,
        "source": source,
        "reason": rule.reason,
        "subject_id": subject_id,
        "source_record_id": rule.source_record_id,
    }


def effective_delivery_rule(
    session: Session, tenant_id: str, document_id: str
) -> dict[str, Any]:
    """The rule an order is shipped under: its own, else its customer's, else partial."""
    document = _tenant_record(session, Document, tenant_id, document_id)
    return effective_rules(session, tenant_id, [document.id])[document.id]


def effective_rules(
    session: Session, tenant_id: str, document_ids: list[str]
) -> dict[str, dict[str, Any]]:
    """The effective rule of many orders in three reads, for readers that need many."""
    ids = set(document_ids)
    if not ids:
        return {}
    customers = dict(
        session.execute(
            select(Commitment.document_id, Commitment.to_party_id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id.in_(ids),
                Commitment.type == "customer_delivery",
            )
        ).all()
    )
    rules = list(
        session.scalars(
            select(DeliveryRule).where(
                DeliveryRule.tenant_id == tenant_id,
                (DeliveryRule.document_id.in_(ids))
                | (DeliveryRule.party_id.in_(set(customers.values()) - {None})),
            )
        )
    )
    by_document = {row.document_id: row for row in rules if row.document_id}
    by_party = {row.party_id: row for row in rules if row.party_id}
    result = {}
    for identity in ids:
        if identity in by_document:
            result[identity] = _entry(by_document[identity], "order", identity)
            continue
        customer = customers.get(identity)
        if customer in by_party:
            result[identity] = _entry(by_party[customer], "customer", customer)
            continue
        result[identity] = {
            "rule": DEFAULT_RULE,
            "source": "default",
            "reason": "",
            "subject_id": None,
            "source_record_id": None,
        }
    return result


def delivery_rules(
    session: Session,
    tenant_id: str,
    *,
    party_id: str | None = None,
    document_id: str | None = None,
) -> dict[str, Any]:
    """The rule in force for a customer or an order, and every statement before it."""
    kind, identity = _subject(session, tenant_id, party_id, document_id)
    current = _current(session, tenant_id, kind, identity)
    history = [
        {
            "rule": payload.get("rule"),
            "reason": payload.get("reason"),
            "source_record_id": row.id,
            "version": row.version,
            "stated_at": row.received_at,
        }
        for row in session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.source_system == SOURCE_SYSTEM,
                SourceRecord.source_type == SOURCE_TYPE,
                SourceRecord.external_id == f"{kind}:{identity}",
            )
            .order_by(SourceRecord.version.desc())
        )
        for payload in [json.loads(row.payload)]
    ]
    effective = (
        effective_delivery_rule(session, tenant_id, identity)
        if kind == "document"
        else (
            _entry(current, "customer", identity)
            if current
            else {
                "rule": DEFAULT_RULE,
                "source": "default",
                "reason": "",
                "subject_id": None,
                "source_record_id": None,
            }
        )
    )
    return {
        "subject": kind,
        "subject_id": identity,
        "own": rule_values(current),
        "effective": effective,
        "history": history,
    }
