"""State-bound review for the existing reservation and shipment tools."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, cast, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from reality.db.core import ChangeProposal, Commitment, Location, Reservation, Tenant
from reality.services.business_locks import lock_delivery_state
from reality.services.commitment_actions import (
    COMMITMENT_ACTION_TOOLS,
    assert_no_unresolved_commitment_action,
    commitment_action_detail,
    review_commitment_action,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    _append_movement,
    _preview_reservation,
)
from reality.services.credit_actions import (
    _assert_credit_overlap,
    _credit_detail,
    _review_credit,
)
from reality.services.credit_hold_actions import (
    CREDIT_HOLD_TOOLS,
    assert_no_unresolved_credit_release,
    credit_release_detail,
    review_credit_release,
)
from reality.services.customer_exchange_actions import (
    CUSTOMER_EXCHANGE_TOOLS,
    assert_no_unresolved_customer_exchange,
    customer_exchange_proposal_detail,
    review_customer_exchange,
)
from reality.services.customer_hold_actions import (
    CUSTOMER_HOLD_TOOLS,
    assert_customer_hold_overlap,
    customer_hold_detail,
    review_customer_hold,
)
from reality.services.delivery_failure_actions import (
    DELIVERY_FAILURE_TOOLS,
    assert_no_unresolved_delivery_failure,
    delivery_failure_proposal_detail,
    review_delivery_failure,
)
from reality.services.delivery_reads import delivery_case
from reality.services.down_payment_actions import (
    BILLING_DOCUMENT_TOOLS,
    assert_no_unresolved_billing_document,
    billing_document_detail,
    review_billing_document,
)
from reality.services.drop_ship_actions import (
    DROP_SHIP_TOOLS,
    assert_no_unresolved_drop_shipment,
    drop_shipment_proposal_detail,
    review_drop_shipment,
)
from reality.services.financial_reversal_actions import (
    _assert_financial_overlap,
    _reversal_detail,
    _review_reversal,
)
from reality.services.hold_actions import (
    HOLD_TOOLS,
    hold_receipt,
    review_hold,
    verify_hold,
)
from reality.services.invoice_actions import (
    INVOICE_TOOLS,
    _assert_no_unresolved_invoice,
    _invoice_detail,
    _review_invoice,
)
from reality.services.opening_stock_actions import (
    assert_opening_overlap,
    is_opening,
    opening_detail,
    review_opening,
)
from reality.services.order_line_items import (
    ORDER_LINE_ITEM_TOOLS,
    assert_no_unresolved_item_assignment,
    item_assignment_detail,
    review_item_assignment,
)
from reality.services.payment_actions import (
    PAYMENT_TOOLS,
    _assert_no_unresolved_payment,
    _payment_detail,
    _review_payment,
)
from reality.services.prepayment_release_actions import (
    PREPAYMENT_RELEASE_TOOLS,
    assert_no_unresolved_prepayment_release,
    prepayment_release_detail,
    review_prepayment_release,
)
from reality.services.return_disposition_actions import (
    RETURN_DISPOSITION_TOOLS,
    assert_no_unresolved_return_disposition,
    return_disposition_detail,
    review_return_disposition,
)
from reality.services.supply_assignment_actions import (
    SUPPLY_ASSIGNMENT_TOOLS,
    assert_no_unresolved_supply_assignment,
    review_supply_assignment,
    supply_assignment_detail,
)

REVIEW_KEY = "_delivery_review"
PUBLIC_MOVEMENT_TYPES = (
    "opening_stock",
    "receipt",
    "shipment",
    "transfer",
    "return",
    "supplier_return",
    "adjustment",
)


def validate_public_movement_type(movement_type: object) -> str:
    normalized = str(movement_type).strip()
    if normalized not in PUBLIC_MOVEMENT_TYPES:
        raise InvalidOperation(
            code="movement_type_unsupported",
            values={"types": ", ".join(PUBLIC_MOVEMENT_TYPES)},
        )
    return normalized


def eligible(tool: str, arguments: dict[str, Any]) -> bool:
    from reality.services.shipment_actions import is_shipment_action

    return (
        is_shipment_action(tool)
        or is_opening(tool, arguments)
        or (tool == "item_create" and "import_file" in arguments)
        or (tool == "sales_credit_record" and "invoice_id" in arguments)
        or tool
        in {
            "reserve",
            "reservation_release",
            "movement_correct",
            "order_create",
            "ledger_reverse",
            *INVOICE_TOOLS,
            *PAYMENT_TOOLS,
            *HOLD_TOOLS,
            *CUSTOMER_HOLD_TOOLS,
            *SUPPLY_ASSIGNMENT_TOOLS,
            *RETURN_DISPOSITION_TOOLS,
            *CUSTOMER_EXCHANGE_TOOLS,
            *DELIVERY_FAILURE_TOOLS,
            *DROP_SHIP_TOOLS,
            *ORDER_LINE_ITEM_TOOLS,
            *CREDIT_HOLD_TOOLS,
            *PREPAYMENT_RELEASE_TOOLS,
            *BILLING_DOCUMENT_TOOLS,
            *COMMITMENT_ACTION_TOOLS,
        }
        or (
            tool == "movement_create"
            and arguments.get("movement_type")
            in {"shipment", "receipt", "return", "transfer"}
        )
    )


def action_commitment(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> str:
    if tool == "reservation_release":
        reservation = session.scalar(
            select(Reservation)
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.id == arguments.get("reservation_id"),
            )
            .execution_options(populate_existing=True)
        )
        if reservation is None:
            raise NotFound(code="reservation_not_found")
        return reservation.commitment_id
    return str(arguments.get("commitment_id", ""))


def release_snapshot(
    session: Session, tenant_id: str, reservation_id: str
) -> dict[str, Any]:
    reservation = session.scalar(
        select(Reservation)
        .where(
            Reservation.tenant_id == tenant_id,
            Reservation.id == reservation_id,
        )
        .execution_options(populate_existing=True)
    )
    if reservation is None:
        raise NotFound(code="reservation_not_found")
    return {
        "id": reservation.id,
        "commitment_id": reservation.commitment_id,
        "item_id": reservation.item_id,
        "location_id": reservation.location_id,
        "quantity": _quantity(reservation.quantity),
        "status": reservation.status,
        **{
            key: getattr(reservation, key)
            for key in ("handling_unit_id", "lot_id", "serial_unit_id")
        },
    }


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _quantity(value: Any) -> str:
    # PostgreSQL Numeric scale must not make an unchanged review stale in a new session.
    return format(Decimal(value).normalize(), "f")


def review_delivery(
    session: Session, tenant_id: str, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    from reality.services.shipment_actions import (
        is_shipment_action,
        review_shipment_action,
    )

    if is_shipment_action(tool):
        return review_shipment_action(session, tenant_id, tool, arguments)
    if tool in CUSTOMER_HOLD_TOOLS:
        return review_customer_hold(session, tenant_id, tool, arguments)
    if is_opening(tool, arguments):
        return review_opening(session, tenant_id, arguments)
    if tool == "item_create" and "import_file" in arguments:
        from reality.services.item_imports import review_item_import

        return review_item_import(session, tenant_id, arguments)
    if tool == "sales_credit_record" and "invoice_id" in arguments:
        return _review_credit(session, tenant_id, arguments)
    if tool == "ledger_reverse":
        return _review_reversal(session, tenant_id, arguments)
    if tool in PAYMENT_TOOLS:
        return _review_payment(session, tenant_id, tool, arguments)
    if tool in INVOICE_TOOLS:
        return _review_invoice(session, tenant_id, tool, arguments)
    if tool in SUPPLY_ASSIGNMENT_TOOLS:
        return review_supply_assignment(session, tenant_id, arguments)
    if tool in RETURN_DISPOSITION_TOOLS:
        return review_return_disposition(session, tenant_id, arguments)
    if tool in CUSTOMER_EXCHANGE_TOOLS:
        return review_customer_exchange(session, tenant_id, arguments)
    if tool in DELIVERY_FAILURE_TOOLS:
        return review_delivery_failure(session, tenant_id, arguments)
    if tool in DROP_SHIP_TOOLS:
        return review_drop_shipment(session, tenant_id, arguments)
    if tool in ORDER_LINE_ITEM_TOOLS:
        return review_item_assignment(session, tenant_id, arguments)
    if tool in CREDIT_HOLD_TOOLS:
        return review_credit_release(session, tenant_id, arguments)
    if tool in PREPAYMENT_RELEASE_TOOLS:
        return review_prepayment_release(session, tenant_id, arguments)
    if tool in BILLING_DOCUMENT_TOOLS:
        return review_billing_document(session, tenant_id, tool, arguments)
    if tool in COMMITMENT_ACTION_TOOLS:
        return review_commitment_action(session, tenant_id, tool, arguments)
    if tool == "order_create":
        from reality.services.order_actions import review_order

        return review_order(session, tenant_id, arguments)
    if tool == "movement_correct":
        from reality.services.movement_correction_actions import review_correction

        return review_correction(session, tenant_id, arguments)
    if not eligible(tool, arguments):
        raise InvalidOperation(code="delivery_review_action_unsupported")
    if any(key.startswith("_") for key in arguments):
        raise InvalidOperation(code="review_metadata_in_intent")
    allowed = {
        "commitment_id",
        "quantity",
        "handling_unit_id",
        "lot_id",
        "serial_unit_id",
    }
    if tool == "movement_create":
        allowed |= {
            "movement_type",
            "item_id",
            "from_location_id",
            "to_location_id",
            "source_record_id",
            "occurred_at",
            "reason",
            "resolves_movement_id",
            "return_announcement_id",
            "unit",
            # Spec 304: a receipt may block part of what it brings in.
            "blocked_quantity",
            "block_reason",
            # Spec 338: a surplus received on purpose, and a wrong item's line.
            "beyond_order",
            "meant_for_commitment_id",
        }
    if tool == "reserve":
        # Spec 303: the location the rest is reserved at, if not the promise's.
        allowed |= {"location_id"}
    if tool == "reservation_release":
        allowed = {"reservation_id"}
    if tool in HOLD_TOOLS:
        allowed = {"commitment_id"}
        if tool == "commitment_hold":
            allowed |= {"reason_code", "note"}
    if set(arguments) - allowed:
        raise InvalidOperation(code="delivery_action_fields_unsupported")
    intent = dict(arguments)
    reservation_state = None
    holds_state = None
    if tool in HOLD_TOOLS:
        holds_state, effect = review_hold(session, tenant_id, tool, intent)
        result = {}
    elif tool == "reservation_release":
        reservation_state = release_snapshot(
            session, tenant_id, str(intent.get("reservation_id", ""))
        )
        if reservation_state["status"] != "active":
            raise InvalidOperation(code="reservation_release_not_active")
        effect = {"released": reservation_state["quantity"]}
        result = {}
    elif tool == "reserve":
        result = _preview_reservation(session, tenant_id, **intent)
        if intent.get("quantity") is not None:
            from reality.services.core import positive

            intent["quantity"] = _quantity(positive(intent["quantity"]))
        effect = {
            "requested": _quantity(result["requested"]),
            "applied": _quantity(result["allocated"]),
            "shortage": _quantity(result["requested"] - result["allocated"]),
        }
    else:
        block_intent = {
            key: intent.pop(key)
            for key in ("blocked_quantity", "block_reason")
            if key in intent
        }
        result = _append_movement(session, tenant_id, **intent, validate_only=True)
        if block_intent.get("blocked_quantity"):
            from reality.services.stock_blocks import validate_block

            if intent.get("movement_type") != "receipt":
                raise InvalidOperation(code="stock_block_receipt_only")
            _, _, held, _ = validate_block(
                session,
                tenant_id,
                intent["item_id"],
                intent["to_location_id"],
                block_intent["blocked_quantity"],
                block_intent.get("block_reason") or "",
                handling_unit_id=intent.get("handling_unit_id"),
                lot_id=result.get("lot_id") or intent.get("lot_id"),
                serial_unit_id=intent.get("serial_unit_id"),
                _incoming=Decimal(str(result["quantity"])),
                _receipt=Decimal(str(result["quantity"])),
            )
            block_intent["blocked_quantity"] = _quantity(held)
        intent.update(block_intent)
        # Spec 301: a receipt stated in the purchase unit keeps what was stated
        # in the intent, which is executed again, and shows the stock-unit
        # quantity as its effect.
        intent["quantity"] = _quantity(
            result.get("stated_quantity", result["quantity"])
        )
        if tool == "movement_create":
            from reality.services.fulfillment_readiness import require_paid_prepayment

            require_paid_prepayment(
                session,
                tenant_id,
                intent.get("movement_type"),
                result.get("commitment_id") or intent.get("commitment_id"),
                result["quantity"],
            )
        effect = {
            "received"
            if intent["movement_type"] == "receipt"
            # Spec 303: a transfer moves stock between warehouses only.
            else "transferred"
            if intent["movement_type"] == "transfer"
            else "shipped": _quantity(result["quantity"])
        }
        if intent.get("blocked_quantity"):
            effect["blocked"] = intent["blocked_quantity"]
        if "stated_quantity" in result:
            effect["stated"] = {
                "quantity": _quantity(result["stated_quantity"]),
                "unit": result["stated_unit"],
            }
    if result.get("lot_id"):
        intent["lot_id"] = result["lot_id"]
    if tool == "movement_create" and not intent.get("commitment_id"):
        from reality.services.core import active_reserved, blocked_quantity, stock_at

        # A transfer is judged where it takes stock from.
        location_id = (
            intent.get("from_location_id")
            if intent.get("movement_type") == "transfer"
            else intent.get("to_location_id") or intent.get("from_location_id")
        )
        physical = stock_at(session, tenant_id, intent["item_id"], location_id)
        reserved = active_reserved(session, tenant_id, intent["item_id"], location_id)
        held_back = blocked_quantity(session, tenant_id, intent["item_id"], location_id)
        detail = {
            "case": {
                "commitment_id": None,
                "item_id": intent["item_id"],
                "location_id": location_id,
                "location": session.scalar(
                    select(Location.name).where(
                        Location.tenant_id == tenant_id, Location.id == location_id
                    )
                ),
            },
            "inventory": {
                "location_id": location_id,
                "physical": str(physical),
                "reserved": str(reserved),
                "blocked": str(held_back),
                "available": str(physical - reserved - held_back),
            },
        }
    else:
        detail = delivery_case(
            session, tenant_id, action_commitment(session, tenant_id, tool, intent)
        )
    location_key = (
        "location_id"
        if tool == "reserve"
        else "to_location_id"
        if intent.get("movement_type") in {"receipt", "return"}
        else "from_location_id"
    )
    if (
        tool in {"movement_create", "reserve"}
        and intent.get(location_key)
        and intent.get(location_key) != detail["case"]["location_id"]
    ):
        from reality.services.core import active_reserved, blocked_quantity, stock_at

        location_id = intent[location_key]
        item_id = intent.get("item_id") or detail["case"]["item_id"]
        physical = stock_at(session, tenant_id, item_id, location_id)
        reserved = active_reserved(session, tenant_id, item_id, location_id)
        held_back = blocked_quantity(session, tenant_id, item_id, location_id)
        detail["inventory"].update(
            location_id=location_id,
            physical=str(physical),
            reserved=str(reserved),
            blocked=str(held_back),
            available=str(physical - reserved - held_back),
        )
        named = session.scalar(
            select(Location.name).where(
                Location.tenant_id == tenant_id, Location.id == location_id
            )
        )
        if tool == "reserve":
            # The promise keeps its own warehouse; what is shown is where its
            # rest is reserved.
            detail["inventory"]["location"] = named
        else:
            detail["case"]["location"] = named
    state = {"case": detail["case"], "inventory": detail["inventory"], "effect": effect}
    warnings = []
    if (
        tool == "movement_create"
        and intent.get("movement_type") in {"shipment", "receipt", "return"}
        and not any(
            intent.get(key)
            for key in (
                "commitment_id",
                "source_record_id",
                "return_announcement_id",
                "resolves_movement_id",
                "shipment_package_id",
            )
        )
    ):
        warnings.append(
            {
                "code": "unexplained_movement",
                "message": (
                    "No commitment, return, shipment or source explains this movement. "
                    "Confirming it will create an unexplained-movement exception."
                ),
            }
        )
    if (
        tool == "movement_create"
        and intent.get("movement_type") == "transfer"
        and Decimal(str(result["quantity"])) > Decimal(detail["inventory"]["available"])
    ):
        # Spec 303: the stock reserved there for other orders goes with it,
        # and those reservations are left without stock.
        warnings.append(
            {
                "code": "transfer_takes_reserved_stock",
                "message": (
                    "This transfer takes stock that is reserved at its warehouse; "
                    "the orders reserved there lose their stock."
                ),
            }
        )
    if reservation_state is not None:
        state["reservation"] = reservation_state
    if holds_state is not None:
        state["holds"] = holds_state
    state = json.loads(_json(state))
    fingerprint = hashlib.sha256(
        _json(
            {"tenant": tenant_id, "tool": tool, "intent": intent, "state": state}
        ).encode()
    ).hexdigest()
    return {
        "version": 1,
        "tool": tool,
        "intent": intent,
        "effect": effect,
        "state": state,
        "warnings": warnings,
        "token": fingerprint,
    }


def prepare_delivery_action(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    *,
    request_id: str,
    actor_id: str = "local",
) -> ChangeProposal:
    from reality.tools.application import create_change_proposal

    if not request_id or len(request_id) > 200:
        raise InvalidOperation(code="request_identity_invalid")
    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise NotFound(code="tenant_not_found")
    if tenant.purpose == "playground":
        raise InvalidOperation(code="delivery_practice_policy_required")
    lock_delivery_state(session, tenant_id)
    identity = (
        "act_"
        + hashlib.sha256(_json([tenant_id, actor_id, request_id]).encode()).hexdigest()[
            :32
        ]
    )
    old = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == identity
        )
    )
    if old:
        saved = json.loads(old.input)
        if old.type != f"tool:{tool}" or saved[REVIEW_KEY][
            "request_arguments"
        ] != json.loads(_json(arguments)):
            raise InvalidOperation(code="request_identity_other_intent")
        return old
    assert_no_unresolved_action(session, tenant_id, tool, arguments)
    review = review_delivery(session, tenant_id, tool, arguments)
    review["request_arguments"] = json.loads(_json(arguments))
    # Reached only through the tenant HTTP endpoints, so the person at the
    # keyboard is the proposing actor. Agents propose through the MCP catalog.
    proposal = create_change_proposal(
        session,
        tenant_id,
        tool,
        review["intent"],
        actor_type="human",
        _commit=False,
        _proposal_id=identity,
    )
    proposal.input = _json({**review["intent"], REVIEW_KEY: review})
    proposal.output = _json({**json.loads(proposal.output), **review})
    session.commit()
    return proposal


def validate_review(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    token: str | None,
    confirmed: bool,
) -> dict[str, Any]:
    review = arguments.get(REVIEW_KEY)
    if not review or not confirmed or token != review["token"]:
        raise InvalidOperation(code="review_confirmation_required")
    intent = {key: value for key, value in arguments.items() if key != REVIEW_KEY}
    current = review_delivery(session, tenant_id, tool, intent)
    if current["token"] != review["token"]:
        raise (
            InvalidOperation(code="review_payment_context_changed")
            if tool in PAYMENT_TOOLS
            else InvalidOperation(code="review_financial_context_changed")
            if tool == "ledger_reverse"
            else InvalidOperation(code="review_item_import_changed")
            if tool == "item_create"
            else InvalidOperation(code="review_stock_context_changed")
            if is_opening(tool, arguments)
            else InvalidOperation(code="review_customer_hold_changed")
            if tool in CUSTOMER_HOLD_TOOLS
            else InvalidOperation(code="review_delivery_changed")
        )
    if (
        tool == "commitment_revise"
        and current["effect"].get("selection_required")
        and not current["intent"].get("retained_allocations")
    ):
        raise InvalidOperation(code="retained_reservations_choice_required")
    return intent


def get_delivery_proposal(
    session: Session, tenant_id: str, proposal_id: str
) -> ChangeProposal:
    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id
        )
    )
    if proposal is None:
        raise NotFound(code="proposal_not_found")
    if not eligible(proposal.type.removeprefix("tool:"), json.loads(proposal.input)):
        raise InvalidOperation(code="proposal_uses_existing_workspace")
    return proposal


def review_existing(
    session: Session, tenant_id: str, proposal_id: str
) -> ChangeProposal:
    from reality.services.tenant_policy import require_proposal_decision

    require_proposal_decision(session, tenant_id, proposal_id, "proposal_execute")
    lock_delivery_state(session, tenant_id)
    proposal = get_delivery_proposal(session, tenant_id, proposal_id)
    arguments = json.loads(proposal.input)
    if proposal.status != "proposed":
        return proposal
    stored = arguments.get(REVIEW_KEY)
    intent = {key: value for key, value in arguments.items() if key != REVIEW_KEY}
    # A stored review fingerprints the delivery state of the moment it was made, so a
    # decision approved since then leaves every other pending review stale. Reviewing
    # again is the operator asking what is true now; confirmation still measures against
    # exactly this stored review, never against one approval computes for itself.
    try:
        review = review_delivery(
            session, tenant_id, proposal.type.removeprefix("tool:"), intent
        )
    except (InvalidOperation, NotFound):
        # The intent cannot be reviewed against current state at all. Keeping the stored
        # review leaves the decision exactly as reviewable — and as rejectable — as it was
        # before renewal existed; confirmation still refuses it.
        if stored:
            return proposal
        raise
    if stored and stored["token"] == review["token"]:
        return proposal
    if stored and "request_arguments" in stored:
        review["request_arguments"] = stored["request_arguments"]
    proposal.input = _json({**intent, REVIEW_KEY: review})
    proposal.output = _json(review)
    session.commit()
    return proposal


def delivery_proposal_detail(
    session: Session, tenant_id: str, proposal_id: str
) -> dict[str, Any]:
    from reality.services.proposal_reviews import proposal_next_step

    proposal = get_delivery_proposal(session, tenant_id, proposal_id)
    return {
        **_delivery_proposal_detail(session, tenant_id, proposal),
        "next_step": proposal_next_step(proposal),
    }


def _delivery_proposal_detail(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict[str, Any]:
    proposal_id = proposal.id
    from decimal import Decimal

    from reality.db.core import BusinessEvent, Movement, Reservation
    from reality.services.shipment_actions import (
        is_shipment_action,
        shipment_proposal_detail,
    )

    if is_shipment_action(proposal.type.removeprefix("tool:")):
        return shipment_proposal_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in CUSTOMER_HOLD_TOOLS:
        return customer_hold_detail(session, tenant_id, proposal)
    if is_opening(proposal.type.removeprefix("tool:"), json.loads(proposal.input)):
        return opening_detail(session, tenant_id, proposal)
    if proposal.type == "tool:item_create" and "import_file" in json.loads(
        proposal.input
    ):
        from reality.services.item_imports import item_import_detail

        return item_import_detail(session, tenant_id, proposal)
    if proposal.type == "tool:sales_credit_record":
        return _credit_detail(session, tenant_id, proposal)
    if proposal.type == "tool:ledger_reverse":
        return _reversal_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in PAYMENT_TOOLS:
        return _payment_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in INVOICE_TOOLS:
        return _invoice_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in SUPPLY_ASSIGNMENT_TOOLS:
        return supply_assignment_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in RETURN_DISPOSITION_TOOLS:
        return return_disposition_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in CUSTOMER_EXCHANGE_TOOLS:
        return customer_exchange_proposal_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in DELIVERY_FAILURE_TOOLS:
        return delivery_failure_proposal_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in DROP_SHIP_TOOLS:
        return drop_shipment_proposal_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in ORDER_LINE_ITEM_TOOLS:
        return item_assignment_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in CREDIT_HOLD_TOOLS:
        return credit_release_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in PREPAYMENT_RELEASE_TOOLS:
        return prepayment_release_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in BILLING_DOCUMENT_TOOLS:
        return billing_document_detail(session, tenant_id, proposal)
    if proposal.type.removeprefix("tool:") in COMMITMENT_ACTION_TOOLS:
        return commitment_action_detail(session, tenant_id, proposal)
    if proposal.type == "tool:order_create":
        from reality.services.order_actions import order_detail

        return order_detail(session, tenant_id, proposal)
    if proposal.type == "tool:movement_correct":
        from reality.services.movement_correction_actions import correction_detail

        return correction_detail(session, tenant_id, proposal)
    arguments = json.loads(proposal.input)
    review = arguments.get(REVIEW_KEY)
    result = {
        "id": proposal.id,
        "tool": proposal.type.removeprefix("tool:"),
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
    if review and proposal.status in {"executing", "executed"}:
        if result["tool"] == "reservation_release":
            _verify_release(session, tenant_id, proposal, result)
        if result["tool"] in HOLD_TOOLS:
            verify_hold(session, tenant_id, proposal, result)
        event_type = (
            "reservation.created"
            if result["tool"] == "reserve"
            else "movement.recorded"
        )
        events = list(
            session.scalars(
                select(BusinessEvent)
                .where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.action_id == proposal_id,
                    BusinessEvent.event_type == event_type,
                )
                .limit(2)
            )
        )
        if len(events) == 1 and result["tool"] not in {
            "reservation_release",
            *HOLD_TOOLS,
        }:
            event = events[0]
            payload = json.loads(event.payload)
            expected = review["effect"].get(
                "applied",
                review["effect"].get(
                    "shipped",
                    review["effect"].get(
                        "received", review["effect"].get("transferred")
                    ),
                ),
            )
            identity = all(
                payload.get(key) == arguments.get(key)
                for key in (
                    "commitment_id",
                    "handling_unit_id",
                    "lot_id",
                    "serial_unit_id",
                )
            )
            model = Reservation if result["tool"] == "reserve" else Movement
            record = session.scalar(
                select(model).where(
                    model.tenant_id == tenant_id, model.id == event.subject_id
                )
            )
            identity = (
                identity
                and payload.get("item_id") == review["state"]["case"]["item_id"]
            )
            location_key = (
                "location_id"
                if result["tool"] == "reserve"
                else "to_location_id"
                if arguments.get("movement_type") == "receipt"
                else "from_location_id"
            )
            expected_location = (
                arguments.get("location_id") or review["state"]["case"]["location_id"]
                if result["tool"] == "reserve"
                else arguments.get(location_key)
            )
            identity = identity and payload.get(location_key) == expected_location
            if result["tool"] == "movement_create":
                identity = (
                    identity
                    and record is not None
                    and record.type == arguments.get("movement_type")
                )
            receipt_matches = True
            if proposal.status == "executed":
                receipt = result["receipt"] or {}
                if result["tool"] == "reserve":
                    receipt_matches = (
                        receipt.get("proposal_id") == proposal_id
                        and receipt.get("commitment_id") == arguments["commitment_id"]
                        and receipt.get("reservation_id") == event.subject_id
                        and receipt.get("event_id") == event.id
                        and Decimal(str(receipt.get("applied", "-1")))
                        == Decimal(expected)
                    )
                else:
                    receipt_matches = receipt.get("records") == [
                        {"family": "movement", "id": event.subject_id}
                    ]
            if (
                record
                and identity
                and receipt_matches
                and Decimal(str(payload.get("quantity", "-1"))) == Decimal(expected)
            ):
                result["verification"] = (
                    "verified"
                    if proposal.status == "executed"
                    else "recorded_unsettled"
                )
                result["links"] = [
                    {"kind": event.subject_type, "id": event.subject_id},
                    {"kind": "business_event", "id": event.id},
                ]
        elif (
            proposal.status == "executed"
            and Decimal(review["effect"].get("applied", "-1")) == 0
            and Decimal(str((result["receipt"] or {}).get("applied", "-1"))) == 0
            and not (result["receipt"] or {}).get("reservation_id")
            and not (result["receipt"] or {}).get("event_id")
        ):
            result["verification"] = "verified"
    try:
        result["observation"] = delivery_case(
            session,
            tenant_id,
            action_commitment(session, tenant_id, result["tool"], arguments),
        )
    except (NotFound, InvalidOperation) as error:
        result["observation_error"] = str(error)
    except SQLAlchemyError:
        session.rollback()
        result["observation_error"] = (
            "Current observation unavailable. Refresh this view."
        )
    return result


def _verify_release(
    session: Session, tenant_id: str, proposal: ChangeProposal, result: dict[str, Any]
) -> None:
    from reality.db.core import BusinessEvent

    review = result["review"]
    saved = review["state"].get("reservation")
    if not saved:
        return
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == "reservation.released",
            )
            .limit(2)
        )
    )
    if len(events) != 1:
        return
    event = events[0]
    if event.subject_type != "reservation" or event.subject_id != saved["id"]:
        return
    if json.loads(event.payload).get("commitment_id") != saved["commitment_id"]:
        return
    current = release_snapshot(session, tenant_id, saved["id"])
    if current != {**saved, "status": "released"}:
        return
    receipt = {"records": [{"family": "reservation", "id": saved["id"]}]}
    if proposal.status == "executed" and result["receipt"] != receipt:
        return
    result["verification"] = (
        "verified" if proposal.status == "executed" else "recorded_unsettled"
    )
    result["links"] = [
        {"kind": "reservation", "id": saved["id"]},
        {"kind": "business_event", "id": event.id},
    ]


def assert_no_unresolved_action(
    session: Session,
    tenant_id: str,
    tool: str,
    arguments: dict[str, Any],
    exclude: str | None = None,
) -> None:
    from reality.services.shipment_actions import is_shipment_action

    if is_shipment_action(tool):
        return
    assert_customer_hold_overlap(session, tenant_id, tool, arguments, exclude)
    if tool in CUSTOMER_HOLD_TOOLS:
        return
    assert_opening_overlap(session, tenant_id, tool, arguments, exclude)
    if is_opening(tool, arguments):
        return
    if tool == "item_create" and "import_file" in arguments:
        from reality.services.item_imports import assert_import_overlap

        return assert_import_overlap(session, tenant_id, arguments, exclude)
    if tool == "sales_credit_record" and "invoice_id" in arguments:
        return _assert_credit_overlap(session, tenant_id, arguments, exclude)
    if tool == "ledger_reverse":
        return _assert_financial_overlap(session, tenant_id, tool, arguments, exclude)
    if tool in PAYMENT_TOOLS:
        return _assert_no_unresolved_payment(
            session, tenant_id, arguments, exclude, tool
        )
    if tool in INVOICE_TOOLS:
        return _assert_no_unresolved_invoice(session, tenant_id, arguments, exclude)
    if tool in SUPPLY_ASSIGNMENT_TOOLS:
        return assert_no_unresolved_supply_assignment(
            session, tenant_id, arguments, exclude
        )
    if tool in RETURN_DISPOSITION_TOOLS:
        return assert_no_unresolved_return_disposition(
            session, tenant_id, arguments, exclude
        )
    if tool in CUSTOMER_EXCHANGE_TOOLS:
        return assert_no_unresolved_customer_exchange(
            session, tenant_id, arguments, exclude
        )
    if tool in DELIVERY_FAILURE_TOOLS:
        return assert_no_unresolved_delivery_failure(
            session, tenant_id, arguments, exclude
        )
    if tool in DROP_SHIP_TOOLS:
        return assert_no_unresolved_drop_shipment(
            session, tenant_id, arguments, exclude
        )
    if tool in ORDER_LINE_ITEM_TOOLS:
        return assert_no_unresolved_item_assignment(
            session, tenant_id, arguments, exclude
        )
    if tool in CREDIT_HOLD_TOOLS:
        return assert_no_unresolved_credit_release(
            session, tenant_id, arguments, exclude
        )
    if tool in PREPAYMENT_RELEASE_TOOLS:
        return assert_no_unresolved_prepayment_release(
            session, tenant_id, arguments, exclude
        )
    if tool in BILLING_DOCUMENT_TOOLS:
        return assert_no_unresolved_billing_document(
            session, tenant_id, tool, arguments, exclude
        )
    if tool in COMMITMENT_ACTION_TOOLS:
        return assert_no_unresolved_commitment_action(
            session, tenant_id, tool, arguments, exclude
        )
    if tool == "order_create":
        from reality.services.order_actions import assert_no_unresolved_order

        return assert_no_unresolved_order(session, tenant_id, arguments, exclude)
    from reality.services.movement_correction_actions import assert_no_unresolved

    assert_no_unresolved(session, tenant_id, tool, arguments, exclude)
    if tool == "movement_correct":
        return
    if tool == "movement_create" and not arguments.get("commitment_id"):
        return
    commitment_id = action_commitment(session, tenant_id, tool, arguments)
    assert_no_unresolved_delivery(session, tenant_id, commitment_id, exclude)
    if tool == "movement_create":
        location = (
            arguments.get("to_location_id")
            if arguments.get("movement_type") == "receipt"
            else arguments.get("from_location_id")
        )
    elif tool == "reservation_release":
        location = release_snapshot(session, tenant_id, arguments["reservation_id"])[
            "location_id"
        ]
    else:
        location = None
    if location:
        assert_no_unresolved_delivery(
            session, tenant_id, commitment_id, exclude, location_id=location
        )


def assert_no_unresolved_delivery(
    session: Session,
    tenant_id: str,
    commitment_id: str,
    exclude: str | None = None,
    *,
    location_id: str | None = None,
) -> None:
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id, Commitment.id == commitment_id
        )
    )
    if commitment is None:
        raise NotFound(code="delivery_not_found")
    pool_location = location_id or commitment.location_id
    same_pool = select(Commitment.id).where(
        Commitment.tenant_id == tenant_id,
        Commitment.item_id == commitment.item_id,
        Commitment.location_id == pool_location,
    )
    intent = cast(ChangeProposal.input, JSONB)
    unresolved = select(ChangeProposal.id).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.status == "executing",
        ChangeProposal.type.in_(
            [
                "tool:reserve",
                "tool:movement_create",
                "tool:reservation_release",
                "tool:commitment_hold",
                "tool:commitment_hold_release",
            ]
        ),
        or_(
            intent["commitment_id"].astext.in_(same_pool),
            intent["reservation_id"].astext.in_(
                select(Reservation.id).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.commitment_id.in_(same_pool),
                )
            ),
            and_(
                intent["item_id"].astext == commitment.item_id,
                intent["to_location_id"].astext == pool_location,
            ),
            and_(
                intent["item_id"].astext == commitment.item_id,
                intent["from_location_id"].astext == pool_location,
            ),
        ),
    )
    if exclude:
        unresolved = unresolved.where(ChangeProposal.id != exclude)
    if session.scalar(unresolved.limit(1)):
        raise InvalidOperation(code="delivery_execution_unresolved")


def reconcile_delivery(
    session: Session, tenant_id: str, proposal_id: str
) -> dict[str, Any]:
    lock_delivery_state(session, tenant_id)
    detail = delivery_proposal_detail(session, tenant_id, proposal_id)
    from reality.services.shipment_actions import is_shipment_action

    if (
        detail["status"] == "executing"
        and detail["verification"] == "recorded_unsettled"
        and is_shipment_action(detail["tool"])
    ):
        proposal = get_delivery_proposal(session, tenant_id, proposal_id)
        proposal.status = "executed"
        proposal.output = _json(detail["recorded_receipt"])
        session.commit()
        return delivery_proposal_detail(session, tenant_id, proposal_id)
    if (
        detail["status"] == "executing"
        and detail["verification"] == "recorded_unsettled"
    ):
        proposal = get_delivery_proposal(session, tenant_id, proposal_id)
        review = detail["review"]
        if detail.get("movement_type") == "opening_stock" or detail["tool"] in {
            *CUSTOMER_HOLD_TOOLS,
            "item_create",
            "movement_correct",
            "order_create",
            "ledger_reverse",
            "sales_credit_record",
            *INVOICE_TOOLS,
            *PAYMENT_TOOLS,
            *SUPPLY_ASSIGNMENT_TOOLS,
            *RETURN_DISPOSITION_TOOLS,
            *CUSTOMER_EXCHANGE_TOOLS,
            *DELIVERY_FAILURE_TOOLS,
            *DROP_SHIP_TOOLS,
            *ORDER_LINE_ITEM_TOOLS,
            *CREDIT_HOLD_TOOLS,
            *PREPAYMENT_RELEASE_TOOLS,
            *BILLING_DOCUMENT_TOOLS,
            *COMMITMENT_ACTION_TOOLS,
        }:
            proposal.status = "executed"
            proposal.output = _json(detail["recorded_receipt"])
            session.commit()
            return delivery_proposal_detail(session, tenant_id, proposal_id)
        record, event = detail["links"]
        if detail["tool"] in HOLD_TOOLS:
            from reality.db.core import BusinessEvent

            recorded = session.scalar(
                select(BusinessEvent).where(
                    BusinessEvent.tenant_id == tenant_id,
                    BusinessEvent.id == event["id"],
                    BusinessEvent.action_id == proposal_id,
                )
            )
            receipt = hold_receipt(recorded)
        elif detail["tool"] == "reserve":
            effect = review["effect"]
            receipt = {
                "proposal_id": proposal_id,
                "capability": "reserve",
                "reservation_id": record["id"],
                "commitment_id": review["intent"]["commitment_id"],
                **effect,
                "reserved": effect["applied"],
                "event_id": event["id"],
                **{
                    key: review["intent"].get(key)
                    for key in ("handling_unit_id", "lot_id", "serial_unit_id")
                },
            }
        else:
            receipt = {
                "records": [
                    {
                        "family": "reservation"
                        if detail["tool"] == "reservation_release"
                        else "movement",
                        "id": record["id"],
                    }
                ]
            }
        proposal.status = "executed"
        proposal.output = _json(receipt)
        session.commit()
        return delivery_proposal_detail(session, tenant_id, proposal_id)
    return detail


def require_delivery_principal(session: Session, tenant_id: str, principal) -> None:
    """Recheck the existing company policy within the effect transaction."""
    if principal is None:
        return  # Trusted local CLI / explicitly disabled authentication.
    from reality.db.core import AppUser, TenantMembership

    user = session.scalar(
        select(AppUser)
        .where(AppUser.id == principal.user_id)
        .execution_options(populate_existing=True)
    )
    if user is None or (user.status != "active" and not user.is_platform_admin):
        raise NotFound(code="company_not_found")
    if not user.is_platform_admin and not session.scalar(
        select(TenantMembership.id).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == principal.user_id,
            TenantMembership.status == "active",
        )
    ):
        raise NotFound(code="company_not_found")
