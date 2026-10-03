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
    """The customer an order is placed by, or refuse what is no customer order."""
    if document.type != "sales_order" or not document.party_id:
        raise InvalidOperation(code="delivery_rule_document_not_order")
    return document.party_id


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
    """
    State, or restate, the delivery rule of a customer or an order.

    BUSINESS PURPOSE:
    State, or restate, the delivery rule of a customer or an order.

    BUSINESS RULE services.delivery_rules.state_delivery_rule.step-13:
    Require the business permission for 'state_delivery_rule' before changing company records.

    BUSINESS RULE services.delivery_rules.state_delivery_rule.step-15:
    Run the shared validate delivery rule check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.delivery_rules.state_delivery_rule.refusal-29:
    IF a reviewed prior delivery rule was supplied and its current stored values differ:
        Refuse with delivery_rule_changed_since_review.

    BUSINESS RULE services.delivery_rules.state_delivery_rule.step-35:
    Pass the stated inputs to the shared store source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.delivery_rules.state_delivery_rule.step-68:
    Record the delivery_rule.stated audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.delivery_rules.state_delivery_rule.result:
    Return current, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.delivery_rules.state_delivery_rule.step-13
    _require_business_mutation(session, tenant_id, "state_delivery_rule")
    lock_delivery_state(session, tenant_id)
    # reality-rule: services.delivery_rules.state_delivery_rule.step-15
    kind, identity, rule, stated = validate_delivery_rule(
        session, tenant_id, rule, reason, party_id=party_id, document_id=document_id
    )
    current = _current(session, tenant_id, kind, identity)
    if action_id and current is not None:
        # The same confirmation again: it already stated this.
        in_force = session.scalar(
            select(SourceRecord.payload).where(
                SourceRecord.tenant_id == tenant_id,
                SourceRecord.id == current.source_record_id,
            )
        )
        if in_force and json.loads(in_force).get("statement_id") == action_id:
            return current
    # reality-rule: services.delivery_rules.state_delivery_rule.refusal-29
    if _expected is not UNCHECKED and rule_values(current) != _expected:
        raise InvalidOperation(code="delivery_rule_changed_since_review")
    previous = rule_values(current)
    # The statement id makes each confirmation its own version, so restating
    # an earlier rule is not taken for that earlier statement, while a replay
    # of the same confirmation is.
    # reality-rule: services.delivery_rules.state_delivery_rule.step-35
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
    # reality-rule: services.delivery_rules.state_delivery_rule.step-68
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
    # reality-rule: services.delivery_rules.state_delivery_rule.result
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
    """
    The effective rule of many orders in three reads, for readers that need many.

    BUSINESS PURPOSE:
    Resolve each requested order's current delivery policy from its own statement, then its customer's statement, then the default partial-delivery rule.

    BUSINESS RULE delivery_policy.effective.empty:
    IF no orders are requested, return no policies.

    BUSINESS RULE delivery_policy.effective.own:
    IF an order has its own delivery-rule statement, use that statement and its source evidence. It overrides the customer's statement.

    BUSINESS RULE delivery_policy.effective.customer:
    ELSE IF the order's customer has a delivery-rule statement in this company, use that customer statement and its source evidence.

    BUSINESS RULE delivery_policy.effective.default:
    ELSE return partial_allowed with default origin, no stated reason and no source-record identity.
    """
    ids = set(document_ids)
    # reality-rule: delivery_policy.effective.empty
    if not ids:
        return {}
    # The order's own party is its customer: the shortest true link.
    customers = dict(
        session.execute(
            select(Document.id, Document.party_id).where(
                Document.tenant_id == tenant_id, Document.id.in_(ids)
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
        # reality-rule: delivery_policy.effective.own
        if identity in by_document:
            result[identity] = _entry(by_document[identity], "order", identity)
            continue
        customer = customers.get(identity)
        # reality-rule: delivery_policy.effective.customer
        if customer in by_party:
            result[identity] = _entry(by_party[customer], "customer", customer)
            continue
        # reality-rule: delivery_policy.effective.default
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
    """
    The rule in force for a customer or an order, and every statement before it.

    BUSINESS PURPOSE:
    The rule in force for a customer or an order, and every statement before it.

    BUSINESS RULE services.delivery_rules.delivery_rules.result:
    Return the current result with subject, subject_id, own, effective, history.
    """
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
    # reality-rule: services.delivery_rules.delivery_rules.result
    return {
        "subject": kind,
        "subject_id": identity,
        "own": rule_values(current),
        "effective": effective,
        "history": history,
    }


def _open_lines(session: Session, tenant_id: str, order_id: str) -> dict[str, Any]:
    """The order's customer promises that still have something to ship."""
    from reality.services.core import commitment_terms

    promises = list(
        session.scalars(
            select(Commitment).where(
                Commitment.tenant_id == tenant_id,
                Commitment.document_id == order_id,
                Commitment.type == "customer_delivery",
                Commitment.status == "open",
            )
        )
    )
    terms = commitment_terms(session, tenant_id, [row.id for row in promises])
    return {row.id: terms[row.id].open for row in promises if terms[row.id].open > 0}


def order_ships_complete(
    session: Session,
    tenant_id: str,
    order_id: str,
    commitment_id: str,
    checked_quantity: Any,
    open_quantity: Any,
) -> bool:
    """
    Whether a line may ship as checked under its order's rule.

    Only ship complete restricts: the line ships its whole open quantity, and
    every other open line of the order is ready to ship its whole open
    quantity too. Cancelled and fulfilled lines have nothing left to wait for.

    BUSINESS PURPOSE:
    Check whether the proposed delivery of one order line respects the order's effective ship-complete policy.

    BUSINESS RULE delivery_policy.complete.partial_allowed:
    IF the effective rule is not ship_complete, permit this check without requiring the whole order.

    BUSINESS RULE delivery_policy.complete.full_line:
    IF the checked quantity is less than this line's open quantity under ship_complete, reject readiness.

    BUSINESS RULE delivery_policy.complete.other_lines:
    Require every other open customer-delivery line of this order to be ship-ready in full. Use shared fulfillment readiness without re-entering this delivery-policy check. Cancelled and fulfilled lines are excluded by the open-lines reader.
    """
    # reality-rule: delivery_policy.complete.partial_allowed
    if effective_rules(session, tenant_id, [order_id])[order_id]["rule"] != (
        "ship_complete"
    ):
        return True
    # reality-rule: delivery_policy.complete.full_line
    if checked_quantity < open_quantity:
        return False
    from reality.services.fulfillment_readiness import fulfillment_readiness

    # reality-rule: delivery_policy.complete.other_lines
    return all(
        fulfillment_readiness(
            session, tenant_id, identity, _delivery_rule=False
        ).ship_ready
        for identity in _open_lines(session, tenant_id, order_id)
        if identity != commitment_id
    )


def require_delivery_rule(
    session: Session, tenant_id: str, movements: list[tuple[str, Any]]
) -> None:
    """A shipment a person records keeps every order's ship-complete rule.

    The movements of one shipment are taken together: under ship complete each
    order in it must carry every open line with its whole open quantity.
    Importers record what a source states and do not come through here.
    """
    from decimal import Decimal

    shipped: dict[str, Decimal] = {}
    for commitment_id, quantity in movements:
        try:
            amount = Decimal(str(quantity))
        except ArithmeticError:
            # A quantity that is no number is refused by the movement's own check.
            continue
        if commitment_id and amount.is_finite():
            shipped[commitment_id] = shipped.get(commitment_id, Decimal(0)) + amount
    orders = {
        document_id
        for document_id in session.scalars(
            select(Commitment.document_id).where(
                Commitment.tenant_id == tenant_id,
                Commitment.id.in_(set(shipped)),
                Commitment.type == "customer_delivery",
                Commitment.document_id.is_not(None),
            )
        )
    }
    rules = effective_rules(session, tenant_id, list(orders))
    for order_id in sorted(orders):
        if rules[order_id]["rule"] != "ship_complete":
            continue
        left = [
            identity
            for identity, quantity in _open_lines(session, tenant_id, order_id).items()
            if shipped.get(identity, Decimal(0)) < quantity
        ]
        if left:
            number = session.scalar(
                select(Document.number).where(
                    Document.tenant_id == tenant_id, Document.id == order_id
                )
            )
            raise InvalidOperation(
                code="shipment_ship_complete_partial",
                values={"order": number or order_id, "lines": len(left)},
            )


def _affected_orders(
    session: Session, tenant_id: str, kind: str, identity: str
) -> list[str]:
    """Open orders the statement would govern: the order itself, or the customer's."""
    if kind == "document":
        return [identity]
    return sorted(
        set(
            session.scalars(
                select(Commitment.document_id).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.to_party_id == identity,
                    Commitment.type == "customer_delivery",
                    Commitment.status == "open",
                    Commitment.document_id.is_not(None),
                )
            )
        )
    )


def review_delivery_rule(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    The arguments a confirmation executes and what the person is shown.

    The review shows the subject's own rule now, or none, beside what it
    becomes, and the open orders it governs with the rule each would ship
    under. It carries the current rule into the arguments: executing them
    later refuses if the rule has changed in between.

    BUSINESS PURPOSE:
    The arguments a confirmation executes and what the person is shown.

    BUSINESS RULE services.delivery_rules.review_delivery_rule.step-10:
    Run the shared validate delivery rule check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.delivery_rules.review_delivery_rule.result:
    Return normalized, preview, as prepared by the preceding checks and service calls.
    """
    # reality-rule: services.delivery_rules.review_delivery_rule.step-10
    kind, identity, rule, stated = validate_delivery_rule(
        session,
        tenant_id,
        str(arguments.get("rule") or ""),
        str(arguments.get("reason") or ""),
        party_id=str(arguments.get("party_id") or "") or None,
        document_id=str(arguments.get("document_id") or "") or None,
    )
    current = rule_values(_current(session, tenant_id, kind, identity))
    orders = _affected_orders(session, tenant_id, kind, identity)
    effective = effective_rules(session, tenant_id, orders)
    numbers = dict(
        session.execute(
            select(Document.id, Document.number).where(
                Document.tenant_id == tenant_id, Document.id.in_(orders)
            )
        ).all()
    )
    if kind == "party":
        name = session.scalar(
            select(Party.name).where(Party.tenant_id == tenant_id, Party.id == identity)
        )
    else:
        name = numbers.get(identity, identity)
    normalized = {
        f"{kind}_id": identity,
        "rule": rule,
        "reason": stated,
        "reviewed": current,
    }
    preview = {
        "subject": kind,
        "subject_id": identity,
        "name": name,
        "current": current,
        "proposed": {"rule": rule, "reason": stated},
        "orders": [
            {
                "document_id": order_id,
                "number": numbers.get(order_id, order_id),
                "now": effective[order_id]["rule"],
                # A customer statement does not change an order with its own rule.
                "after": (
                    effective[order_id]["rule"]
                    if kind == "party" and effective[order_id]["source"] == "order"
                    else rule
                ),
            }
            for order_id in orders
        ],
    }
    # reality-rule: services.delivery_rules.review_delivery_rule.result
    return normalized, preview
