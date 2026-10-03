"""Customer shipments that did not reach the customer (spec 335).

A parcel that came back undeliverable, was refused at the door, or was lost
did not keep the delivery promise. Recording it reverses the shipment's
movements through the movement correction every reader already honours, so
fulfilment, open quantity, billing and costing agree without a line of special
handling: the promise is open again and a person reships or cancels it.

Undeliverable and refused goods come back to where they left from. Lost goods
are written off there in the same correction. A lost parcel may also open a
claim against the carrier or its insurer: a receivable of the business partner
named, settled by an ordinary incoming payment, like a fee claim.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from decimal import InvalidOperation as DecimalInvalid
from typing import Any

from sqlalchemy import cast, exists, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    Commitment,
    DeliveryFailure,
    Document,
    Movement,
    MovementCorrection,
    Party,
    Shipment,
    ShipmentPackage,
    uid,
)
from reality.services import core
from reality.services.core import emit_business_event

KINDS = {
    "undeliverable": "Undeliverable",
    "refused": "Refused",
    "lost": "Lost",
}
CLAIM_TYPE = "carrier_claim"
CLAIM_ROLE = "carrier_claim_income"
SOURCE_TYPE = "delivery_failure"
#: A stated time a little ahead of the clock is a clock difference, not a claim
#: about the future; the same allowance the shipment notice takes (spec 312).
CLOCK_ALLOWANCE = timedelta(minutes=5)
AMOUNT_SCALE = Decimal("0.01")


def _standing_movements(
    session: Session, tenant_id: str, shipment_id: str
) -> list[Movement]:
    """The shipment's movements that no correction has voided."""
    return list(
        session.scalars(
            select(Movement)
            .join(
                ShipmentPackage,
                (ShipmentPackage.tenant_id == Movement.tenant_id)
                & (ShipmentPackage.id == Movement.shipment_package_id),
            )
            .where(
                Movement.tenant_id == tenant_id,
                ShipmentPackage.shipment_id == shipment_id,
                Movement.type == "shipment",
                ~exists().where(
                    MovementCorrection.tenant_id == tenant_id,
                    MovementCorrection.original_movement_id == Movement.id,
                ),
            )
            .order_by(Movement.occurred_at, Movement.id)
        )
    )


def _occurred_at(value: Any, movements: list[Movement]) -> datetime:
    if value in (None, ""):
        return core.now()
    try:
        moment = core.utc_datetime(value)
    except (TypeError, ValueError) as error:
        raise core.InvalidOperation(code="delivery_failure_time_invalid") from error
    if moment is None:
        raise core.InvalidOperation(code="delivery_failure_time_invalid")
    if moment > core.now() + CLOCK_ALLOWANCE:
        raise core.InvalidOperation(code="delivery_failure_time_future")
    left = min(core.utc_datetime(movement.occurred_at) for movement in movements)
    if moment < left:
        raise core.InvalidOperation(code="delivery_failure_before_shipment")
    return moment


def _claim(
    session: Session,
    tenant_id: str,
    kind: str,
    party_id: Any,
    amount: Any,
) -> dict[str, Any] | None:
    if party_id in (None, "") and amount in (None, ""):
        return None
    if kind != "lost":
        raise core.InvalidOperation(code="delivery_failure_claim_lost_only")
    if party_id in (None, "") or amount in (None, ""):
        raise core.InvalidOperation(code="delivery_failure_claim_incomplete")
    try:
        stated = Decimal(str(amount))
    except (TypeError, ValueError, DecimalInvalid) as error:
        raise core.InvalidOperation(
            code="delivery_failure_claim_amount_invalid"
        ) from error
    if not stated.is_finite() or stated <= 0 or stated.as_tuple().exponent < -2:
        raise core.InvalidOperation(code="delivery_failure_claim_amount_invalid")
    party = core._tenant_record(session, Party, tenant_id, str(party_id))
    from reality.services.finance.accounts import resolve_account
    from reality.services.finance.company_currency import company_currency

    return {
        "party_id": party.id,
        "party": party.name,
        "amount": str(stated.quantize(AMOUNT_SCALE)),
        "currency": company_currency(session, tenant_id),
        "accounts": {
            "accounts_receivable": resolve_account(
                session, tenant_id, "accounts_receivable"
            ).id,
            CLAIM_ROLE: resolve_account(session, tenant_id, CLAIM_ROLE).id,
        },
    }


def preview_delivery_failure(
    session: Session,
    tenant_id: str,
    *,
    shipment_id: str,
    kind: str,
    reason: str,
    occurred_at: Any = None,
    claim_party_id: str | None = None,
    claim_amount: Any = None,
) -> dict[str, Any]:
    """What recording this failure would do, recording nothing."""
    shipment = core._tenant_record(session, Shipment, tenant_id, str(shipment_id))
    if shipment.direction != "outbound" or shipment.purpose != "customer_delivery":
        raise core.InvalidOperation(code="delivery_failure_not_customer_delivery")
    if kind not in KINDS:
        raise core.InvalidOperation(code="delivery_failure_kind_invalid")
    stated_reason = str(reason or "").strip()
    if not stated_reason:
        raise core.InvalidOperation(code="delivery_failure_reason_required")
    if session.scalar(
        select(DeliveryFailure.id).where(
            DeliveryFailure.tenant_id == tenant_id,
            DeliveryFailure.shipment_id == shipment.id,
        )
    ):
        raise core.InvalidOperation(code="delivery_failure_already_recorded")
    movements = _standing_movements(session, tenant_id, shipment.id)
    if not movements:
        raise core.InvalidOperation(code="delivery_failure_nothing_standing")
    moment = _occurred_at(occurred_at, movements)
    claim = _claim(session, tenant_id, kind, claim_party_id, claim_amount)
    reversed_by_promise: dict[str, Decimal] = {}
    for movement in movements:
        if movement.commitment_id:
            reversed_by_promise[movement.commitment_id] = reversed_by_promise.get(
                movement.commitment_id, Decimal()
            ) + core.decimal(movement.quantity)
    promises = []
    for commitment_id, quantity in sorted(reversed_by_promise.items()):
        commitment = core._tenant_record(session, Commitment, tenant_id, commitment_id)
        in_force = core.commitment_quantity(session, tenant_id, commitment_id)
        kept_after = (
            core.fulfilled_quantity(session, tenant_id, commitment_id) - quantity
        )
        promises.append(
            {
                "commitment_id": commitment_id,
                "status_before": commitment.status,
                "reversed": str(quantity),
                "open_after": str(max(Decimal(), in_force - kept_after)),
            }
        )
    return {
        "shipment_id": shipment.id,
        "counterparty_id": shipment.counterparty_id,
        "kind": kind,
        "reason": stated_reason,
        "occurred_at": moment.isoformat(),
        "goods": "written_off" if kind == "lost" else "back_in_stock",
        "movements": [
            {
                "movement_id": movement.id,
                "commitment_id": movement.commitment_id,
                "item_id": movement.item_id,
                "quantity": str(core.decimal(movement.quantity)),
                "from_location_id": movement.from_location_id,
            }
            for movement in movements
        ],
        "promises": promises,
        "claim": claim,
    }


def _claim_number(session: Session, tenant_id: str, shipment_id: str) -> str:
    """The parcel's tracking number names its claim; the shipment when it has none."""
    tracking = session.scalar(
        select(ShipmentPackage.tracking_number)
        .where(
            ShipmentPackage.tenant_id == tenant_id,
            ShipmentPackage.shipment_id == shipment_id,
            ShipmentPackage.tracking_number.is_not(None),
        )
        .order_by(ShipmentPackage.created_at, ShipmentPackage.id)
        .limit(1)
    )
    return f"{tracking or shipment_id}-CLAIM"


def record_delivery_failure(
    session: Session,
    tenant_id: str,
    *,
    shipment_id: str,
    kind: str,
    reason: str,
    occurred_at: Any = None,
    claim_party_id: str | None = None,
    claim_amount: Any = None,
    action_id: str | None = None,
    _commit: bool = True,
) -> DeliveryFailure:
    """
    Record a failed delivery, reverse its shipment and open any claim.

    BUSINESS PURPOSE:
    Record a failed delivery, reverse its shipment and open any claim.

    BUSINESS RULE services.delivery_failures.record_delivery_failure.step-14:
    Require the business permission for 'record_delivery_failure' before changing company records.

    BUSINESS RULE services.delivery_failures.record_delivery_failure.result:
    Return failure, as prepared by the preceding checks and service calls.

    BUSINESS RULE services.delivery_failures.record_delivery_failure.effect-36:
    Run the shared preview delivery failure check and use its normalized inputs and current review evidence. Inspect that called function for its detailed eligibility rules.

    BUSINESS RULE services.delivery_failures.record_delivery_failure.effect-50:
    Pass the stated inputs to the shared create master source record service. Its own source describes validation and record changes.

    BUSINESS RULE services.delivery_failures.record_delivery_failure.effect-139:
    Record the shipment.delivery_failed audit or business-event evidence with the supplied record and confirmation identity.

    BUSINESS RULE services.delivery_failures.record_delivery_failure.effect-111:
    IF the reviewed delivery failure includes a claim:
        Pass the stated inputs to the shared create document service. Its own source describes validation and record changes.
    """
    # reality-rule: services.delivery_failures.record_delivery_failure.step-14
    core._require_business_mutation(session, tenant_id, "record_delivery_failure")
    from reality.services.business_locks import lock_delivery_state

    with session.begin_nested():
        lock_delivery_state(session, tenant_id)
        session.scalar(
            select(Shipment)
            .where(Shipment.tenant_id == tenant_id, Shipment.id == shipment_id)
            .with_for_update()
        )
        # reality-rule: services.delivery_failures.record_delivery_failure.effect-36
        reviewed = preview_delivery_failure(
            session,
            tenant_id,
            shipment_id=shipment_id,
            kind=kind,
            reason=reason,
            occurred_at=occurred_at,
            claim_party_id=claim_party_id,
            claim_amount=claim_amount,
        )
        if reviewed["claim"]:
            from reality.services.finance.accounts import lock_finance

            lock_finance(session, tenant_id)
        # reality-rule: services.delivery_failures.record_delivery_failure.effect-50
        source = core.create_master_source_record(
            session,
            tenant_id,
            SOURCE_TYPE,
            "manual",
            action_id or uid("delivery-failure"),
            {
                key: reviewed[key]
                for key in ("shipment_id", "kind", "reason", "occurred_at")
            }
            | {
                "claim": {
                    key: reviewed["claim"][key]
                    for key in ("party_id", "amount", "currency")
                }
                if reviewed["claim"]
                else None
            },
            action_id=action_id,
            _commit=False,
        )
        failure = DeliveryFailure(
            id=uid("dfl"),
            tenant_id=tenant_id,
            shipment_id=reviewed["shipment_id"],
            kind=reviewed["kind"],
            reason=reviewed["reason"],
            occurred_at=core.utc_datetime(reviewed["occurred_at"]),
            source_record_id=source.id,
        )
        session.add(failure)
        session.flush()
        stated = f"{KINDS[reviewed['kind']]}: {reviewed['reason']}"
        corrections = []
        for movement in reviewed["movements"]:
            corrections.append(
                core.correct_movement(
                    session,
                    tenant_id,
                    movement["movement_id"],
                    reason=stated,
                    replacement={
                        "type": "adjustment",
                        "item_id": movement["item_id"],
                        "quantity": movement["quantity"],
                        "from_location_id": movement["from_location_id"],
                        "occurred_at": reviewed["occurred_at"],
                        "reason": stated,
                        # The write-off is not part of the parcel it replaces.
                        "shipment_package_id": None,
                    }
                    if reviewed["kind"] == "lost"
                    else None,
                    actor_context={"delivery_failure_id": failure.id},
                    action_id=action_id,
                    _commit=False,
                ).correction_id
            )
        claim_document = None
        if reviewed["claim"]:
            claim = reviewed["claim"]
            # reality-rule: services.delivery_failures.record_delivery_failure.effect-111
            claim_document = core.create_document(
                session,
                tenant_id,
                CLAIM_TYPE,
                _claim_number(session, tenant_id, reviewed["shipment_id"]),
                claim["party_id"],
                claim["amount"],
                currency=claim["currency"],
                document_date=failure.occurred_at.date().isoformat(),
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
            core.post_ledger(
                session,
                tenant_id,
                claim_document.id,
                claim["party_id"],
                [
                    ("accounts_receivable", "debit", claim["amount"]),
                    (CLAIM_ROLE, "credit", claim["amount"]),
                ],
                account_ids=claim["accounts"],
                currency=claim["currency"],
                source_record_id=source.id,
                action_id=action_id,
                _commit=False,
            )
        # reality-rule: services.delivery_failures.record_delivery_failure.effect-139
        emit_business_event(
            session,
            tenant_id,
            "shipment.delivery_failed",
            "delivery_failure",
            failure.id,
            {
                "shipment_id": failure.shipment_id,
                "kind": failure.kind,
                "reason": failure.reason,
                "occurred_at": reviewed["occurred_at"],
                "correction_ids": corrections,
                "reopened_commitment_ids": [
                    promise["commitment_id"] for promise in reviewed["promises"]
                ],
                "claim_document_id": claim_document.id if claim_document else None,
            },
            source_record_id=source.id,
            action_id=action_id,
        )
    if _commit:
        session.commit()
    # reality-rule: services.delivery_failures.record_delivery_failure.result
    return failure


def _failure_detail(
    session: Session, tenant_id: str, failure: DeliveryFailure
) -> dict[str, Any]:
    claim = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.type == CLAIM_TYPE,
            Document.source_record_id == failure.source_record_id,
        )
    )
    corrections = list(
        session.scalars(
            select(MovementCorrection)
            .where(
                MovementCorrection.tenant_id == tenant_id,
                cast(MovementCorrection.actor_context, JSONB)[
                    "delivery_failure_id"
                ].astext
                == failure.id,
            )
            .order_by(MovementCorrection.corrected_at, MovementCorrection.id)
        )
    )
    return {
        "id": failure.id,
        "shipment_id": failure.shipment_id,
        "kind": failure.kind,
        "reason": failure.reason,
        "occurred_at": core.utc_datetime(failure.occurred_at),
        "recorded_at": core.utc_datetime(failure.created_at),
        "source_record_id": failure.source_record_id,
        "goods": "written_off" if failure.kind == "lost" else "back_in_stock",
        "corrections": [
            {
                "id": row.id,
                "original_movement_id": row.original_movement_id,
                "compensating_movement_id": row.compensating_movement_id,
                "replacement_movement_id": row.replacement_movement_id,
            }
            for row in corrections
        ],
        "claim": {
            "document_id": claim.id,
            "number": claim.number,
            "party_id": claim.party_id,
            "amount": str(core.decimal(claim.gross_amount)),
            "currency": claim.currency,
            "open": str(core.open_invoice_amount(session, tenant_id, claim.id)),
        }
        if claim
        else None,
    }


def delivery_failure_summary(
    session: Session,
    tenant_id: str,
    *,
    delivery_failure_id: str | None = None,
    shipment_id: str | None = None,
) -> dict[str, Any]:
    """One failed delivery with what it reversed and the claim it opened."""
    if bool(delivery_failure_id) == bool(shipment_id):
        raise core.InvalidOperation(code="delivery_failure_lookup_invalid")
    failure = session.scalar(
        select(DeliveryFailure).where(
            DeliveryFailure.tenant_id == tenant_id,
            DeliveryFailure.id == delivery_failure_id
            if delivery_failure_id
            else DeliveryFailure.shipment_id == shipment_id,
        )
    )
    if failure is None:
        raise core.NotFound(code="delivery_failure_not_found")
    return _failure_detail(session, tenant_id, failure)


def failures_by_shipment(
    session: Session, tenant_id: str, shipment_ids: list[str]
) -> dict[str, dict[str, Any]]:
    """What the shipment read shows of each failure, in one query for a page."""
    if not shipment_ids:
        return {}
    return {
        row.shipment_id: {
            "id": row.id,
            "kind": row.kind,
            "reason": row.reason,
            "occurred_at": core.utc_datetime(row.occurred_at),
        }
        for row in session.scalars(
            select(DeliveryFailure).where(
                DeliveryFailure.tenant_id == tenant_id,
                DeliveryFailure.shipment_id.in_(shipment_ids),
            )
        )
    }


__all__ = [
    "KINDS",
    "delivery_failure_summary",
    "failures_by_shipment",
    "preview_delivery_failure",
    "record_delivery_failure",
]
