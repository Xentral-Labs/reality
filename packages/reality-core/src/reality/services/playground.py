"""Private run lifecycle. Initial reference setup is atomic, not lesson execution."""

import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

from pydantic import ValidationError
from sqlalchemy import event, func, select, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from reality.db.core import (
    AppUser,
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Document,
    DocumentLine,
    Item,
    Location,
    Movement,
    Party,
    PlaygroundRun,
    PlaygroundStep,
    Reservation,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.playground import catalog
from reality.playground.actions import (
    MASTER_TOOLS,
    OpeningStockInput,
    PlaygroundInvoiceInput,
    PlaygroundMasterInput,
    PlaygroundOrderInput,
    PlaygroundPaymentInput,
    PlaygroundReceiptInput,
    PlaygroundRefundInput,
    PlaygroundReleaseInput,
    PlaygroundReservationInput,
    PlaygroundReturnInput,
    PlaygroundShipmentInput,
    validate_master_input,
)
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    business_events,
    create_item,
    create_location,
    create_party,
    fulfilled_quantity,
    master_data_update_snapshot,
    open_invoice_amount,
    open_quantity,
    returned_quantity,
    stock_at,
    uncredited_return_quantity,
    validate_commitment_movement_quantity,
)
from reality.services.memberships import Principal
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    _decision_scope,
    _proposal_creation_scope,
    _seed_scope,
    require_playground_account,
    require_playground_run,
)

logger = logging.getLogger(__name__)

INVOICE_TOOLS = {
    "sales_invoice_record",
    "supplier_invoice_record",
    "sales_credit_record",
}
PAYMENT_TOOLS = {
    "customer_payment_post",
    "supplier_payment_post",
    "customer_refund_post",
}
FINANCE_TOOLS = INVOICE_TOOLS | PAYMENT_TOOLS


def _master_state(session: Session, tenant_id: str, tool: str, arguments: dict) -> dict:
    family, mode = tool.split("_")
    if mode == "create":
        return {}
    return master_data_update_snapshot(
        session, tenant_id, family, arguments["records"][0]["id"]
    )


def _release_state(session: Session, tenant_id: str, arguments: dict) -> dict:
    reservation = session.scalar(
        select(Reservation).where(
            Reservation.tenant_id == tenant_id,
            Reservation.id == arguments["reservation_id"],
        )
    )
    if reservation is None:
        raise NotFound("Playground reservation not found.")
    return {
        "reservation_id": reservation.id,
        "commitment_id": reservation.commitment_id,
        "quantity": str(reservation.quantity),
        "status": reservation.status,
    }


def _finance_state(session: Session, tenant_id: str, arguments: dict) -> dict:
    if "order_line_id" in arguments:
        line = session.scalar(
            select(DocumentLine).where(
                DocumentLine.tenant_id == tenant_id,
                DocumentLine.id == arguments["order_line_id"],
            )
        )
        if line is None:
            raise NotFound("Playground order line not found.")
        document_id = line.document_id
        billed = list(
            session.scalars(
                select(DocumentLine.id)
                .where(
                    DocumentLine.tenant_id == tenant_id,
                    DocumentLine.billed_document_line_id == line.id,
                )
                .order_by(DocumentLine.id)
            )
        )
        if billed:
            billed = sorted(
                set(billed)
                | set(
                    session.scalars(
                        select(DocumentLine.id).where(
                            DocumentLine.tenant_id == tenant_id,
                            DocumentLine.billed_document_line_id.in_(billed),
                        )
                    )
                )
            )
        commitments = list(
            session.scalars(
                select(Commitment.id).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.document_line_id == line.id,
                    Commitment.type.in_(["customer_delivery", "supplier_delivery"]),
                )
            )
        )
        delivered = sum(
            (fulfilled_quantity(session, tenant_id, id_) for id_ in commitments),
            Decimal(0),
        )
        state = {
            "order_line_id": line.id,
            "quantity": str(line.quantity),
            "billed_lines": billed,
            "item_id": line.item_id,
            "unit": line.unit,
            "unit_price": str(line.unit_price),
            "delivered_quantity": str(delivered),
            "uncredited_return_quantity": str(
                uncredited_return_quantity(session, tenant_id, line.id)
            ),
        }
    else:
        document_id = arguments.get("invoice_id") or arguments["credit_note_id"]
        state = {
            "open_amount": str(open_invoice_amount(session, tenant_id, document_id))
        }
    document = session.scalar(
        select(Document).where(
            Document.tenant_id == tenant_id, Document.id == document_id
        )
    )
    if document is None:
        raise NotFound("Playground financial evidence not found.")
    return {
        **state,
        "document_id": document.id,
        "document_type": document.type,
        "number": document.number,
        "party_id": document.party_id,
        "currency": document.currency,
        "gross_amount": str(document.gross_amount),
    }


def _store_finance_observation(
    session: Session, run: PlaygroundRun, step: PlaygroundStep, proposal: ChangeProposal
) -> None:
    if step.receipt_observation is not None:
        return
    related = [
        event
        for event in business_events(session, run.tenant_id)
        if event.action_id == proposal.id
    ]
    expected = {"document.recorded", "ledger.posted"}
    if proposal.type.removeprefix("tool:") in PAYMENT_TOOLS:
        expected.add("settlement.allocated")
    if not expected.issubset({event.event_type for event in related}):
        return
    args = json.loads(proposal.input)
    output = json.loads(proposal.output)
    records = list(output.get("records", []))
    for entry in related:
        record = {"family": entry.subject_type, "id": entry.subject_id}
        if record not in records:
            records.append(record)
    if proposal.type.removeprefix("tool:") in INVOICE_TOOLS:
        invoice_id = next(
            record["id"] for record in records if record["family"] == "document"
        )
        after = _finance_state(session, run.tenant_id, {"invoice_id": invoice_id})
    else:
        after = _finance_state(session, run.tenant_id, args)
    step.receipt_observation = {
        "kind": proposal.type.removeprefix("tool:"),
        "evaluated_at": now().isoformat(),
        "before": (step.before_observation or {}).get("state", {}),
        "after": after,
        "records": records,
        "event_ids": [event.id for event in related],
    }
    step.observed_at = now()
    session.commit()


def _opening_state(session: Session, tenant_id: str, arguments: dict) -> dict:
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == arguments["item_id"])
    )
    location = session.scalar(
        select(Location).where(
            Location.tenant_id == tenant_id, Location.id == arguments["to_location_id"]
        )
    )
    if item is None or location is None:
        raise NotFound("Playground reference not found.")
    return {
        "physical": str(stock_at(session, tenant_id, item.id, location.id)),
        "item": {
            "id": item.id,
            "name": item.name,
            "unit": item.unit,
            "active": item.is_active,
            "type": item.item_type,
            "tracking": item.tracking_type,
        },
        "location": {
            "id": location.id,
            "name": location.name,
            "active": location.is_active,
            "allows_stock": location.allows_stock,
        },
    }


def _receipt_state(session: Session, tenant_id: str, arguments: dict) -> dict:
    is_return = arguments.get("movement_type") == "return"
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == arguments["commitment_id"],
        )
    )
    if commitment is None:
        raise NotFound("Playground goods commitment not found.")
    if (
        commitment.type != ("customer_delivery" if is_return else "supplier_delivery")
        or commitment.item_id != arguments["item_id"]
        or commitment.location_id != arguments["to_location_id"]
    ):
        raise InvalidOperation(
            "Receipt or return must match the commitment type, item and location."
        )
    return {
        **_opening_state(session, tenant_id, arguments),
        "commitment_id": commitment.id,
        "order_line_id": commitment.document_line_id,
        "open_quantity": str(open_quantity(session, tenant_id, commitment.id)),
        **(
            {
                "returnable_quantity": str(
                    fulfilled_quantity(session, tenant_id, commitment.id)
                    - returned_quantity(session, tenant_id, commitment.id)
                )
            }
            if is_return
            else {}
        ),
    }


def _order_state(session: Session, tenant_id: str, arguments: dict) -> dict:
    line = (arguments.get("lines") or [{}])[0]
    item_id = arguments.get("item_id") or line.get("item_id")
    item = session.scalar(
        select(Item).where(Item.tenant_id == tenant_id, Item.id == item_id)
    )
    location = session.scalar(
        select(Location).where(
            Location.tenant_id == tenant_id, Location.id == arguments["location_id"]
        )
    )
    company = session.scalar(
        select(Party).where(
            Party.tenant_id == tenant_id, Party.id == arguments["company_party_id"]
        )
    )
    customer = session.scalar(
        select(Party).where(
            Party.tenant_id == tenant_id, Party.id == arguments["counterparty_id"]
        )
    )
    if any(value is None for value in (item, location, company, customer)):
        raise NotFound("Playground reference not found.")
    return {
        "item": {"id": item.id, "name": item.name, "sku": item.sku, "unit": item.unit},
        "location": {"id": location.id, "name": location.name},
        "company": {"id": company.id, "name": company.name},
        "customer": {"id": customer.id, "name": customer.name},
    }


def _shipment_state(session: Session, tenant_id: str, arguments: dict) -> dict:
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == arguments["commitment_id"],
        )
    )
    if commitment is None:
        raise NotFound("Playground commitment not found.")
    return {
        "commitment_id": commitment.id,
        "item_id": commitment.item_id,
        "location_id": commitment.location_id,
        "open_quantity": str(open_quantity(session, tenant_id, commitment.id)),
        "status": commitment.status,
        "physical": str(
            stock_at(session, tenant_id, commitment.item_id, commitment.location_id)
        ),
    }


def _preview_revision(arguments: dict, state: dict) -> str:
    return sha256(
        json.dumps({"arguments": arguments, "state": state}, sort_keys=True).encode()
    ).hexdigest()


def _owned_step(
    session: Session, run: PlaygroundRun, step_id: str
) -> tuple[PlaygroundStep, ChangeProposal]:
    result = session.execute(
        select(PlaygroundStep, ChangeProposal)
        .join(
            ChangeProposal,
            (ChangeProposal.id == PlaygroundStep.proposal_id)
            & (ChangeProposal.tenant_id == PlaygroundStep.tenant_id),
        )
        .where(
            PlaygroundStep.tenant_id == run.tenant_id,
            PlaygroundStep.run_id == run.id,
            PlaygroundStep.id == step_id,
        )
    ).one_or_none()
    if result is None:
        raise NotFound("Playground step not found.")
    return result


def _unapplied_overdelivery(
    session: Session, run: PlaygroundRun, step: PlaygroundStep, proposal: ChangeProposal
) -> bool:
    """Narrow legacy proof; absence alone or elapsed time never proves failure.

    Writes using this proof must hold the run mutation lock. The old movement
    handler rejected this impossible quantity before writing any movement, and
    committed its movement and action events atomically. Retain unknown outcomes.
    """
    if (
        proposal.status != "executing"
        or proposal.type != "tool:movement_create"
        or step.receipt_observation is not None
    ):
        return False
    args = json.loads(proposal.input)
    state = (step.before_observation or {}).get("state", {})
    if (
        args.get("movement_type") != "shipment"
        or not args.get("commitment_id")
        or state.get("commitment_id") != args["commitment_id"]
        or state.get("item_id") != args.get("item_id")
        or state.get("location_id") != args.get("from_location_id")
        or state.get("open_quantity") is None
        or Decimal(str(args.get("quantity", "0"))) <= Decimal(state["open_quantity"])
    ):
        return False
    event = session.scalar(
        select(BusinessEvent.id)
        .where(
            BusinessEvent.tenant_id == run.tenant_id,
            BusinessEvent.action_id == proposal.id,
        )
        .limit(1)
    )
    movement = session.scalar(
        select(Movement.id)
        .where(
            Movement.tenant_id == run.tenant_id,
            Movement.commitment_id == args["commitment_id"],
        )
        .limit(1)
    )
    return event is None and movement is None


def read_step(session: Session, user_id: str, run_id: str, step_id: str) -> dict:
    """Read original proposal state separately from its explanatory observation."""
    from reality.tools.application import run_read_tool

    run = require_playground_run(session, run_id, user_id)
    step, proposal = _owned_step(session, run, step_id)
    status = run_read_tool(
        session,
        run.tenant_id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )
    return {
        **_step_preview(step, proposal),
        "can_discard": _unapplied_overdelivery(session, run, step, proposal),
        "verification": status["verification"],
        "reconciliation_evidence": status.get("reconciliation_evidence"),
        "receipt": step.receipt_observation,
        "observation": "available"
        if step.receipt_observation is not None
        else "unavailable",
    }


def read_reality(session: Session, user_id: str, run_id: str) -> dict:
    """Read bounded sandbox Reality through the shared read tools and event journal."""
    from reality.tools.application import run_read_tool

    run = require_playground_run(session, run_id, user_id)
    if run.status not in {"active", "archived"}:
        return {"inventory": [], "exceptions": [], "events": [], "event_sequence": 0}
    inventory = run_read_tool(session, run.tenant_id, "inventory")
    exceptions = run_read_tool(session, run.tenant_id, "exceptions")
    events = business_events(session, run.tenant_id)
    serialized_events = [
        {
            "id": event.id,
            "sequence": event.sequence,
            "event_type": event.event_type,
            "subject_type": event.subject_type,
            "subject_id": event.subject_id,
            "occurred_at": event.occurred_at,
            "payload": json.loads(event.payload),
        }
        for event in events[-50:]
    ]
    return {
        "inventory": inventory,
        "exceptions": exceptions,
        "events": serialized_events,
        "event_sequence": events[-1].sequence if events else 0,
    }


def _store_opening_observation(
    session: Session, run: PlaygroundRun, step: PlaygroundStep, proposal: ChangeProposal
) -> None:
    from reality.tools.application import run_read_tool

    if step.receipt_observation is not None:
        return
    status = run_read_tool(
        session,
        run.tenant_id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )
    if (
        status["status"] != "executed"
        or status["verification"]["operational_state"] != "verified"
    ):
        return
    if step.before_observation is None:
        return
    evidence = status["reconciliation_evidence"]
    evaluated_at = now()
    step.receipt_observation = {
        "kind": "opening_stock",
        "evaluated_at": evaluated_at.isoformat(),
        "before": step.before_observation["state"],
        "after": _opening_state(session, run.tenant_id, json.loads(proposal.input)),
        "records": [{"family": "movement", "id": evidence["movement_id"]}],
        "event_ids": [evidence["event_id"]],
        "event_sequence": evidence["event_sequence"],
    }
    step.observed_at = evaluated_at
    session.commit()


def _store_order_observation(
    session: Session, run: PlaygroundRun, step: PlaygroundStep, proposal: ChangeProposal
) -> None:
    if step.receipt_observation is not None or step.before_observation is None:
        return
    from reality.tools.application import run_read_tool

    status = run_read_tool(
        session,
        run.tenant_id,
        "proposal_execution_status",
        {"proposal_id": proposal.id},
    )
    if status["status"] != "executed":
        return
    receipt = json.loads(proposal.output)
    events = business_events(session, run.tenant_id)
    related = [event for event in events if event.action_id == proposal.id]
    evaluated_at = now()
    records = []
    for family, key in (
        ("source_record", "source_record_id"),
        ("document", "document_id"),
    ):
        if receipt.get(key):
            records.append({"family": family, "id": receipt[key]})
    records.extend(
        {"family": "document_line", "id": value}
        for value in receipt.get("document_line_ids", [])
    )
    records.extend(
        {"family": "commitment", "id": value}
        for value in receipt.get("commitment_ids", [])
    )
    step.receipt_observation = {
        "kind": f"{json.loads(proposal.input)['direction']}_order",
        "evaluated_at": evaluated_at.isoformat(),
        "before": step.before_observation["state"],
        "after": {**step.before_observation["state"], "records": records},
        "records": records,
        "event_ids": [event.id for event in related],
        "event_sequence": related[-1].sequence if related else None,
    }
    step.observed_at = evaluated_at
    session.commit()


def confirm_step(
    engine: Engine,
    user_id: str,
    run_id: str,
    step_id: str,
    preview_revision: str,
    *,
    confirmed: bool = False,
    db_session: Session | None = None,
) -> dict:
    """Confirm one reviewed opening action through the existing proposal executor."""
    from reality.tools.application import approve_and_execute_proposal

    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm the reviewed Playground action first.")
    with _mutation_session(engine, user_id, run_id, db_session=db_session) as (
        session,
        run,
    ):
        step, proposal = _owned_step(session, run, step_id)
        if proposal.status == "rejected":
            raise Conflict("This Playground proposal was rejected.")
        saved_revision = (step.before_observation or {}).get("preview_revision")
        if saved_revision is not None and preview_revision != saved_revision:
            raise Conflict("Confirmation does not match the saved Playground review.")
        if proposal.status == "executing":
            return read_step(session, user_id, run_id, step_id)
        if proposal.status == "proposed":
            preview = json.loads(proposal.output)
            args = json.loads(proposal.input)
            if proposal.type == "tool:movement_create":
                state = (
                    _opening_state(session, run.tenant_id, args)
                    if args.get("movement_type") == "opening_stock"
                    else _receipt_state(session, run.tenant_id, args)
                    if args.get("movement_type") in {"receipt", "return"}
                    else _shipment_state(session, run.tenant_id, args)
                )
            elif proposal.type.removeprefix("tool:") in MASTER_TOOLS:
                state = _master_state(
                    session, run.tenant_id, proposal.type.removeprefix("tool:"), args
                )
            elif proposal.type == "tool:reservation_release":
                state = _release_state(session, run.tenant_id, args)
            elif proposal.type.removeprefix("tool:") in FINANCE_TOOLS:
                state = _finance_state(session, run.tenant_id, args)
            elif proposal.type == "tool:order_create":
                state = _order_state(session, run.tenant_id, args)
            else:
                commitment = session.scalar(
                    select(Commitment).where(
                        Commitment.tenant_id == run.tenant_id,
                        Commitment.id == args["commitment_id"],
                    )
                )
                if commitment is None:
                    raise NotFound("Playground commitment not found.")
                state = {
                    "commitment_id": commitment.id,
                    "item_id": commitment.item_id,
                    "location_id": commitment.location_id,
                    "open_quantity": str(
                        open_quantity(session, run.tenant_id, commitment.id)
                    ),
                }
            if (
                preview.get("revision") != preview_revision
                or _preview_revision(args, state) != preview_revision
            ):
                raise Conflict(
                    "Playground preview changed. Reject it and prepare a fresh review."
                )
            _require_step_capacity(
                session, run.tenant_id, exclude_proposal_id=proposal.id
            )
            if (
                proposal.type == "tool:movement_create"
                and args.get("movement_type") == "shipment"
            ):
                validate_commitment_movement_quantity(
                    session, run.tenant_id, args["commitment_id"], args["quantity"]
                )
            if step.before_observation is None:
                step.before_observation = {
                    "requested_intent": preview["requested_intent"],
                    "state": state,
                    "evaluated_at": now().isoformat(),
                    "preview_revision": preview_revision,
                }
                session.commit()
            try:
                with _decision_scope(
                    session, run.id, user_id, proposal.id, "proposal_execute"
                ):
                    approve_and_execute_proposal(
                        session,
                        run.tenant_id,
                        proposal.id,
                        confirming_principal=Principal(user_id),
                    )
            except Exception:
                logger.exception(
                    "Playground proposal execution failed",
                    extra={"proposal_id": proposal.id},
                )
                session.rollback()
                return read_step(session, user_id, run_id, step_id)
        elif proposal.status != "executed":
            raise Conflict("Inspect this Playground proposal before continuing.")
        if step.receipt_observation is not None:
            return read_step(session, user_id, run_id, step_id)
        try:
            if proposal.type == "tool:movement_create" and json.loads(
                proposal.input
            ).get("movement_type") in {"receipt", "return"}:
                args = json.loads(proposal.input)
                related = [
                    entry
                    for entry in business_events(session, run.tenant_id)
                    if entry.action_id == proposal.id
                ]
                movements = [
                    entry
                    for entry in related
                    if entry.event_type == "movement.recorded"
                ]
                if len(movements) != 1:
                    return read_step(session, user_id, run_id, step_id)
                step.receipt_observation = {
                    "kind": args["movement_type"],
                    "evaluated_at": now().isoformat(),
                    "before": (step.before_observation or {}).get("state", {}),
                    "after": _receipt_state(session, run.tenant_id, args),
                    "records": [{"family": "movement", "id": movements[0].subject_id}],
                    "event_ids": [entry.id for entry in related],
                }
                step.observed_at = now()
                session.commit()
            elif proposal.type.removeprefix("tool:") in MASTER_TOOLS:
                records = json.loads(proposal.output)["records"]
                related = list(
                    session.scalars(
                        select(BusinessEvent).where(
                            BusinessEvent.tenant_id == run.tenant_id,
                            BusinessEvent.action_id == proposal.id,
                        )
                    )
                )
                step.receipt_observation = {
                    "kind": proposal.type.removeprefix("tool:"),
                    "before": (step.before_observation or {}).get("state", {}),
                    "after": master_data_update_snapshot(
                        session, run.tenant_id, records[0]["family"], records[0]["id"]
                    ),
                    "records": records,
                    "event_ids": [event.id for event in related],
                    "evaluated_at": now().isoformat(),
                }
                step.observed_at = now()
                session.commit()
            elif proposal.type.removeprefix("tool:") in FINANCE_TOOLS:
                _store_finance_observation(session, run, step, proposal)
            elif proposal.type == "tool:order_create":
                _store_order_observation(session, run, step, proposal)
            elif proposal.type == "tool:reservation_release":
                args = json.loads(proposal.input)
                related = list(
                    session.scalars(
                        select(BusinessEvent).where(
                            BusinessEvent.tenant_id == run.tenant_id,
                            BusinessEvent.action_id == proposal.id,
                            BusinessEvent.event_type == "reservation.released",
                        )
                    )
                )
                step.receipt_observation = {
                    "kind": "reservation_release",
                    "before": (step.before_observation or {}).get("state", {}),
                    "after": _release_state(session, run.tenant_id, args),
                    "records": [
                        {"family": "reservation", "id": args["reservation_id"]}
                    ],
                    "event_ids": [event.id for event in related],
                }
                step.observed_at = now()
                session.commit()
            elif proposal.type == "tool:reserve":
                receipt = json.loads(proposal.output)
                evaluated_at = now()
                step.receipt_observation = {
                    "kind": "reservation",
                    "evaluated_at": evaluated_at.isoformat(),
                    "before": step.before_observation["state"]
                    if step.before_observation
                    else {},
                    "after": {
                        **(
                            step.before_observation["state"]
                            if step.before_observation
                            else {}
                        ),
                        "reserved": receipt.get("reserved"),
                    },
                    "records": (
                        [{"family": "reservation", "id": receipt["reservation_id"]}]
                        if receipt.get("reservation_id")
                        else []
                    ),
                    "event_ids": (
                        [receipt["event_id"]] if receipt.get("event_id") else []
                    ),
                }
                step.observed_at = evaluated_at
                session.commit()
            elif (
                proposal.type == "tool:movement_create"
                and json.loads(proposal.input).get("movement_type") == "shipment"
            ):
                receipt = json.loads(proposal.output)
                evaluated_at = now()
                records = receipt.get("records", [])
                args = json.loads(proposal.input)
                before = (
                    step.before_observation["state"] if step.before_observation else {}
                )
                after = {
                    **before,
                    "physical": str(
                        stock_at(
                            session,
                            run.tenant_id,
                            args["item_id"],
                            args["from_location_id"],
                        )
                    ),
                    "records": records,
                }
                step.receipt_observation = {
                    "kind": "shipment",
                    "evaluated_at": evaluated_at.isoformat(),
                    "before": before,
                    "after": after,
                    "records": records,
                    "event_ids": [],
                }
                step.observed_at = evaluated_at
                session.commit()
            else:
                _store_opening_observation(session, run, step, proposal)
        except Exception:  # noqa: BLE001 - Unavailable observations must never retry the action.
            session.rollback()
        return read_step(session, user_id, run_id, step_id)


def reject_step(
    engine: Engine,
    user_id: str,
    run_id: str,
    step_id: str,
    *,
    confirmed: bool = False,
    db_session: Session | None = None,
) -> dict:
    from reality.tools.application import reject_proposal

    if confirmed is not True:
        raise PlaygroundOperationDenied(
            "Confirm rejecting this Playground proposal first."
        )
    with _mutation_session(engine, user_id, run_id, db_session=db_session) as (
        session,
        run,
    ):
        step, proposal = _owned_step(session, run, step_id)
        if proposal.status == "proposed":
            with _decision_scope(
                session, run.id, user_id, proposal.id, "proposal_reject"
            ):
                reject_proposal(
                    session,
                    run.tenant_id,
                    proposal.id,
                    confirming_principal=Principal(user_id),
                )
        elif _unapplied_overdelivery(session, run, step, proposal):
            from reality.services.tenant_policy import require_proposal_decision

            with _decision_scope(
                session, run.id, user_id, proposal.id, "proposal_reject"
            ):
                require_proposal_decision(
                    session, run.tenant_id, proposal.id, "proposal_reject"
                )
                # This is a confirmed non-execution decision, not a replay/reset.
                proposal.status = "rejected"
                proposal.decided_at = now()
                proposal.decided_by_user_id = user_id
                proposal.output = json.dumps(
                    {
                        **json.loads(proposal.output),
                        "recovery": "unapplied_overdelivery_discarded",
                    }
                )
                session.commit()
        elif proposal.status != "rejected":
            raise Conflict(
                "An executing or applied Playground action cannot be rejected."
            )
        return read_step(session, user_id, run_id, step.id)


def _require_step_capacity(
    session: Session, tenant_id: str, *, exclude_proposal_id: str | None = None
) -> None:
    pending = (
        select(ChangeProposal.id)
        .outerjoin(
            PlaygroundStep,
            (PlaygroundStep.proposal_id == ChangeProposal.id)
            & (PlaygroundStep.tenant_id == ChangeProposal.tenant_id),
        )
        .where(
            ChangeProposal.tenant_id == tenant_id,
            (ChangeProposal.status == "executing")
            | (
                (ChangeProposal.status == "executed")
                & PlaygroundStep.id.is_not(None)
                & PlaygroundStep.receipt_observation.is_(None)
            ),
        )
    )
    if exclude_proposal_id:
        pending = pending.where(ChangeProposal.id != exclude_proposal_id)
    if session.scalar(pending.limit(1)):
        raise Conflict(
            "Inspect the unresolved Playground action before preparing another."
        )
    applied = session.scalar(
        select(func.count())
        .select_from(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id, ChangeProposal.status == "executed"
        )
    )
    if applied >= _limit("REALITY_PLAYGROUND_STEP_LIMIT", 50):
        raise PlaygroundStepQuotaExceeded(
            "Playground applied-step limit reached. Saved history remains available.",
            {"applied_remaining": 0},
        )


def _step_preview(step: PlaygroundStep, proposal: ChangeProposal) -> dict:
    return {
        "tool_name": proposal.type.removeprefix("tool:"),
        "step_id": step.id,
        "proposal_id": proposal.id,
        "sequence": step.sequence,
        "status": proposal.status,
        "arguments": json.loads(proposal.input),
        "preview": json.loads(proposal.output)
        if proposal.status in {"proposed", "rejected"}
        else None,
    }


def prepare_step(
    engine: Engine,
    user_id: str,
    run_id: str,
    request_key: str,
    tool_name: str,
    arguments: dict,
    *,
    db_session: Session | None = None,
) -> dict:
    """Prepare the first supported action only; never execute or infer a Movement."""
    from reality.tools.application import create_change_proposal

    with _mutation_session(engine, user_id, run_id, db_session=db_session) as (
        session,
        run,
    ):
        if (
            not isinstance(request_key, str)
            or not request_key
            or request_key != request_key.strip()
            or len(request_key) > 128
        ):
            raise InvalidOperation("A request key of 1 to 128 characters is required.")
        if tool_name == "movement_create":
            model_type = (
                OpeningStockInput
                if arguments.get("movement_type") == "opening_stock"
                else PlaygroundReceiptInput
                if arguments.get("movement_type") == "receipt"
                else PlaygroundReturnInput
                if arguments.get("movement_type") == "return"
                else PlaygroundShipmentInput
            )
        elif tool_name == "order_create":
            model_type = PlaygroundOrderInput
        elif tool_name == "reserve":
            model_type = PlaygroundReservationInput
        elif tool_name in MASTER_TOOLS:
            model_type = PlaygroundMasterInput
        elif tool_name == "reservation_release":
            model_type = PlaygroundReleaseInput
        elif tool_name in INVOICE_TOOLS:
            model_type = PlaygroundInvoiceInput
        elif tool_name == "customer_refund_post":
            model_type = PlaygroundRefundInput
        elif tool_name in PAYMENT_TOOLS:
            model_type = PlaygroundPaymentInput
        else:
            raise InvalidOperation("This guided action is not available yet.")
        try:
            supplied = model_type.model_validate(arguments)
        except ValidationError as exc:
            raise InvalidOperation("Invalid Playground guided action input.") from exc
        requested = supplied.model_dump(mode="json", exclude_none=True)
        if tool_name in MASTER_TOOLS:
            try:
                requested = validate_master_input(tool_name, requested)
            except ValueError as exc:
                raise InvalidOperation("Invalid Playground master-data input.") from exc
        if tool_name == "movement_create" and supplied.occurred_at is not None:
            requested["occurred_at"] = supplied.occurred_at.isoformat()
        requested_intent = {"tool": tool_name, "arguments": requested}
        existing = session.execute(
            select(PlaygroundStep, ChangeProposal)
            .join(
                ChangeProposal,
                (ChangeProposal.id == PlaygroundStep.proposal_id)
                & (ChangeProposal.tenant_id == PlaygroundStep.tenant_id),
            )
            .where(
                PlaygroundStep.tenant_id == run.tenant_id,
                PlaygroundStep.run_id == run.id,
                PlaygroundStep.request_key == request_key,
            )
        ).one_or_none()
        if existing is not None:
            step, proposal = existing
            # Execution replaces proposal.output. Its future claim must retain
            # this request identity alongside the before-observation metadata.
            previous = (step.before_observation or {}).get("requested_intent")
            if previous is None and proposal.status != "executed":
                previous = json.loads(proposal.output).get("requested_intent")
            if proposal.type != f"tool:{tool_name}" or previous != requested_intent:
                raise Conflict(
                    "The request key belongs to a different Playground action."
                )
            return _step_preview(step, proposal)
        _require_step_capacity(session, run.tenant_id)
        if tool_name in MASTER_TOOLS:
            normalized = requested
            state = _master_state(session, run.tenant_id, tool_name, normalized)
        elif tool_name == "reservation_release":
            normalized = requested
            state = _release_state(session, run.tenant_id, normalized)
            if state["status"] != "active":
                raise InvalidOperation("Only an active reservation can be released.")
        elif tool_name in FINANCE_TOOLS:
            normalized = {
                **requested,
                "effective_at": (supplied.effective_at or now()).isoformat(),
            }
            state = _finance_state(session, run.tenant_id, normalized)
            expected_type = {
                "sales_invoice_record": "sales_order",
                "supplier_invoice_record": "purchase_order",
                "customer_payment_post": "sales_invoice",
                "supplier_payment_post": "supplier_invoice",
                "sales_credit_record": "sales_order",
                "customer_refund_post": "credit_note",
            }[tool_name]
            if state["document_type"] != expected_type:
                raise InvalidOperation(
                    "Financial action does not match the evidence type."
                )
            if tool_name in INVOICE_TOOLS - {"sales_credit_record"} and (
                state["billed_lines"]
                or supplied.quantity > Decimal(state["delivered_quantity"])
            ):
                raise InvalidOperation(
                    "Choose delivered, not yet billed goods for this invoice lesson."
                )
            if tool_name == "sales_credit_record" and supplied.quantity > Decimal(
                state["uncredited_return_quantity"]
            ):
                raise InvalidOperation(
                    "Credit quantity exceeds returned, not yet credited goods."
                )
            if tool_name in PAYMENT_TOOLS and supplied.amount > Decimal(
                state["open_amount"]
            ):
                raise InvalidOperation("Payment exceeds the open amount.")
        elif tool_name == "reserve":
            commitment = session.scalar(
                select(Commitment).where(
                    Commitment.tenant_id == run.tenant_id,
                    Commitment.id == supplied.commitment_id,
                )
            )
            if commitment is None:
                raise NotFound("Playground commitment not found.")
            normalized = {
                "commitment_id": supplied.commitment_id,
                "quantity": str(supplied.quantity),
            }
            state = {
                "commitment_id": commitment.id,
                "item_id": commitment.item_id,
                "location_id": commitment.location_id,
                "open_quantity": str(
                    open_quantity(session, run.tenant_id, commitment.id)
                ),
            }
        elif tool_name == "movement_create":
            item_id = supplied.item_id
            location_id = (
                supplied.to_location_id
                if supplied.movement_type in {"opening_stock", "receipt", "return"}
                else supplied.from_location_id
            )
            item = session.scalar(
                select(Item).where(Item.tenant_id == run.tenant_id, Item.id == item_id)
            )
            location = session.scalar(
                select(Location).where(
                    Location.tenant_id == run.tenant_id, Location.id == location_id
                )
            )
        else:
            item_id, location_id = supplied.item_id, supplied.location_id
            item = session.scalar(
                select(Item).where(Item.tenant_id == run.tenant_id, Item.id == item_id)
            )
            location = session.scalar(
                select(Location).where(
                    Location.tenant_id == run.tenant_id, Location.id == location_id
                )
            )
        if tool_name not in FINANCE_TOOLS | MASTER_TOOLS | {
            "reserve",
            "reservation_release",
        } and (item is None or location is None):
            raise NotFound("Playground reference not found.")
        if tool_name == "movement_create" and (
            not item.is_active
            or item.item_type != "stocked"
            or item.tracking_type != "none"
            or not location.is_active
            or not location.allows_stock
        ):
            raise InvalidOperation(
                "Choose an active, untracked stock item and stock location."
            )
        if tool_name in FINANCE_TOOLS | MASTER_TOOLS | {
            "reserve",
            "reservation_release",
        }:
            # The normalized reservation intent was built above.
            pass
        elif tool_name == "movement_create":
            normalized = {
                **requested,
                "occurred_at": (supplied.occurred_at or now()).isoformat(),
            }
            if supplied.movement_type == "opening_stock":
                state = _opening_state(session, run.tenant_id, normalized)
            elif supplied.movement_type in {"receipt", "return"}:
                normalized["from_location_id"] = None
                state = _receipt_state(session, run.tenant_id, normalized)
                available_key = (
                    "returnable_quantity"
                    if supplied.movement_type == "return"
                    else "open_quantity"
                )
                if supplied.quantity > Decimal(state[available_key]):
                    raise InvalidOperation(
                        "Quantity exceeds the remaining goods eligible for this receipt or return."
                    )
            else:
                commitment = session.scalar(
                    select(Commitment).where(
                        Commitment.tenant_id == run.tenant_id,
                        Commitment.id == supplied.commitment_id,
                    )
                )
                if (
                    commitment is None
                    or commitment.item_id != supplied.item_id
                    or commitment.location_id != supplied.from_location_id
                ):
                    raise InvalidOperation(
                        "Shipment must match the commitment item and location."
                    )
                normalized["to_location_id"] = None
                state = _shipment_state(session, run.tenant_id, normalized)
                validate_commitment_movement_quantity(
                    session, run.tenant_id, supplied.commitment_id, supplied.quantity
                )
        else:
            normalized = {
                "direction": supplied.direction,
                "number": supplied.number,
                "company_party_id": supplied.company_party_id,
                "counterparty_id": supplied.counterparty_id,
                "location_id": supplied.location_id,
                "lines": [
                    {
                        "item_id": supplied.item_id,
                        "quantity": str(supplied.quantity),
                        "unit": item.unit,
                        "unit_price": str(supplied.unit_price),
                        "gross_amount": str(supplied.quantity * supplied.unit_price),
                    }
                ],
                "gross_amount": str(supplied.quantity * supplied.unit_price),
                "currency": supplied.currency,
            }
            state = _order_state(session, run.tenant_id, normalized)
        with _proposal_creation_scope(session, run.id, user_id, tool_name, normalized):
            proposal = create_change_proposal(
                session,
                run.tenant_id,
                tool_name,
                normalized,
                actor_type="human",
                _commit=False,
            )
        preview = json.loads(proposal.output)
        # Shared update tools add their authoritative expected revision.
        normalized = json.loads(proposal.input)
        targets = (
            [
                {
                    "family": tool_name.split("_")[0],
                    "id": requested["records"][0].get("id"),
                    "name": requested["records"][0]["name"],
                }
            ]
            if tool_name in MASTER_TOOLS
            else [{"family": "reservation", "id": supplied.reservation_id}]
            if tool_name == "reservation_release"
            else [
                {
                    "family": "document",
                    "id": state["document_id"],
                    "name": state["number"],
                }
            ]
            if tool_name in FINANCE_TOOLS
            else [{"family": "commitment", "id": supplied.commitment_id}]
            if tool_name == "reserve"
            else [
                {"family": "item", "id": item.id, "name": item.name, "unit": item.unit},
                {"family": "location", "id": location.id, "name": location.name},
            ]
        )
        preview.update(
            {
                "tool": tool_name,
                "revision": _preview_revision(normalized, state),
                "requested_intent": requested_intent,
                "defaults": ["occurred_at"]
                if tool_name == "movement_create" and supplied.occurred_at is None
                else [],
                "targets": targets,
            }
        )
        proposal.output = json.dumps(preview, sort_keys=True)
        sequence = (
            session.scalar(
                select(func.max(PlaygroundStep.sequence)).where(
                    PlaygroundStep.tenant_id == run.tenant_id,
                    PlaygroundStep.run_id == run.id,
                )
            )
            or 0
        )
        step = PlaygroundStep(
            id=uid("pgs"),
            tenant_id=run.tenant_id,
            run_id=run.id,
            sequence=sequence + 1,
            request_key=request_key,
            proposal_id=proposal.id,
        )
        session.add(step)
        session.commit()
        return _step_preview(step, proposal)


class PlaygroundQuotaExceeded(InvalidOperation):
    code = "playground_run_quota_exceeded"

    def __init__(self, message: str, capacity: dict):
        super().__init__(message)
        self.capacity = capacity


class PlaygroundStepQuotaExceeded(PlaygroundQuotaExceeded):
    code = "playground_step_quota_exceeded"


@contextmanager
def _dedicated_connection(engine: Engine | Connection) -> Iterator[Connection]:
    """Never return a session-locked or disconnected backend to the shared pool."""
    if isinstance(engine, Connection):
        # Test/embedded adapters may deliberately supply their already-scoped
        # connection. Production passes an Engine and gets a private backend.
        yield engine
        return
    with engine.connect() as connection:
        driver = connection.connection.driver_connection
        connection.detach()
        try:
            yield connection
        finally:
            # SQLAlchemy invalidation of a detached connection drops its driver
            # reference without closing it. Keep and close our own reference.
            driver.close()
            if not connection.closed and not connection.invalidated:
                connection.invalidate()


@contextmanager
def _mutation_session(
    engine: Engine | Connection,
    user_id: str,
    run_id: str,
    *,
    db_session: Session | None = None,
) -> Iterator[tuple[Session, PlaygroundRun]]:
    """Pin run serialization across service commits; grant no mutation authority.

    The caller must use this session for its entire step operation. It must still
    enforce intent, confirmation, quotas, unresolved outcomes and operation policy.
    Never bind to a caller's transaction or commit unrelated pending changes.
    """
    # A stable, namespaced signed bigint across workers. A hash collision only
    # serializes unrelated runs; it can never grant access or skip ownership.
    key = int.from_bytes(
        sha256(f"reality:playground:mutation:{run_id}".encode()).digest()[:8],
        "big",
        signed=True,
    )
    if db_session is not None:
        connection = db_session.connection()
        acquired = False
        try:
            require_playground_run(db_session, run_id, user_id, for_write=True)
            acquired = bool(
                connection.scalar(
                    text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
                )
            )
            if not acquired:
                raise Conflict("Playground run is busy. Inspect its current step.")
            run = require_playground_run(db_session, run_id, user_id, for_write=True)
            yield db_session, run
            db_session.commit()
        except BaseException:
            db_session.rollback()
            raise
        finally:
            if acquired and not connection.invalidated and not connection.closed:
                try:
                    released = connection.scalar(
                        text("SELECT pg_advisory_unlock(:key)"), {"key": key}
                    )
                    if not released:
                        raise PlaygroundOperationDenied(
                            "Playground mutation lock was lost."
                        )
                except BaseException:  # noqa: BLE001 - invalidate on unknown lock state.
                    # A request-scoped connection cannot be safely returned with
                    # an unknown session lock state. Closing it releases the lock.
                    connection.invalidate()
        return

    with _dedicated_connection(engine) as connection:
        with Session(bind=connection, close_resets_only=False) as session:
            require_playground_run(session, run_id, user_id, for_write=True)
            session.rollback()
        acquired = False

        def deny_reconnection(conn, *_args, **_kwargs) -> None:
            if conn.invalidated or conn.closed:
                raise PlaygroundOperationDenied(
                    "Playground connection was lost; inspect the step before retrying."
                )

        event.listen(connection, "before_execute", deny_reconnection)
        try:
            try:
                acquired = bool(
                    connection.scalar(
                        text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
                    )
                )
                connection.commit()
            except BaseException:
                # The server may have acquired the lock before its reply was lost.
                connection.invalidate()
                raise
            if not acquired:
                raise Conflict("Playground run is busy. Inspect its current step.")
            with Session(bind=connection, close_resets_only=False) as session:
                # Recheck after acquisition: the pre-lock read is not authority.
                run = require_playground_run(session, run_id, user_id, for_write=True)
                yield session, run
        finally:
            event.remove(connection, "before_execute", deny_reconnection)
            if acquired and not connection.invalidated and not connection.closed:
                try:
                    connection.rollback()
                    released = connection.scalar(
                        text("SELECT pg_advisory_unlock(:key)"), {"key": key}
                    )
                    connection.commit()
                    if not released:
                        raise PlaygroundOperationDenied(
                            "Playground mutation lock was lost."
                        )
                except BaseException:
                    connection.invalidate()
                    raise


def _locked_owner(session: Session, user_id: str) -> AppUser:
    session.scalar(select(AppUser.id).where(AppUser.id == user_id).with_for_update())
    return require_playground_account(session, user_id)


def _limit(name: str, default: int) -> int:
    try:
        result = int(os.environ.get(name, str(default)))
        if result < 1:
            raise ValueError
        return result
    except ValueError as exc:
        raise InvalidOperation("Playground quota configuration is invalid.") from exc


def _capacity(session: Session, user_id: str) -> dict:
    day = datetime.combine(now().date(), datetime.min.time(), UTC)
    owned = (
        select(func.count())
        .select_from(PlaygroundRun)
        .where(PlaygroundRun.owner_user_id == user_id)
    )
    retained = session.scalar(owned)
    daily = session.scalar(owned.where(PlaygroundRun.created_at >= day))
    return {
        "daily_remaining": max(
            0, _limit("REALITY_PLAYGROUND_DAILY_RUN_LIMIT", 5) - daily
        ),
        "retained_remaining": max(
            0, _limit("REALITY_PLAYGROUND_RETAINED_RUN_LIMIT", 20) - retained
        ),
        "daily_resets_at": day + timedelta(days=1),
    }


def _check_capacity(session: Session, user_id: str) -> None:
    capacity = _capacity(session, user_id)
    if not capacity["daily_remaining"] or not capacity["retained_remaining"]:
        raise PlaygroundQuotaExceeded(
            "Playground run limit reached. Resume or inspect a saved run.", capacity
        )


def _run_summary(run: PlaygroundRun, company_name: str) -> dict:
    ready = run.status in {"active", "archived"}
    return {
        "id": run.id,
        "sandbox_kind": run.sandbox_kind,
        "company_name": company_name,
        "tenant_id": run.tenant_id if ready else None,
        "status": run.status,
        "preset_key": run.preset_key,
        "preset_version": run.preset_version,
        "lesson_key": run.lesson_key,
        "lesson_version": run.lesson_version,
        "created_at": run.created_at,
        "ready_at": run.ready_at,
        "archived_at": run.archived_at,
        "initialization_error_code": run.initialization_error_code,
    }


def read_run(session: Session, user_id: str, run_id: str) -> dict:
    """Read owned setup state; partial reference maps are never inspection authority."""
    require_playground_account(session, user_id)
    run = require_playground_run(session, run_id, user_id)
    steps = []
    if run.status in {"active", "archived"}:
        rows = session.execute(
            select(PlaygroundStep, ChangeProposal)
            .join(
                ChangeProposal,
                (ChangeProposal.id == PlaygroundStep.proposal_id)
                & (ChangeProposal.tenant_id == PlaygroundStep.tenant_id),
            )
            .where(
                PlaygroundStep.tenant_id == run.tenant_id,
                PlaygroundStep.run_id == run.id,
            )
            .order_by(PlaygroundStep.sequence.asc())
        )
        steps = [_step_preview(step, proposal) for step, proposal in rows]
    return {
        **_run_summary(run, session.get(Tenant, run.tenant_id).name),
        "request_key": run.client_request_key,
        "references": run.initialization_progress
        if run.status in {"active", "archived"}
        else None,
        "steps": steps,
    }


def list_runs(
    session: Session, user_id: str, *, limit: int = 25, offset: int = 0
) -> dict:
    """Bounded private entry read; quotas are guidance, rechecked under lock on start."""
    require_playground_account(session, user_id)
    if not 1 <= limit <= 100 or offset < 0:
        raise InvalidOperation(
            "Use a page size from 1 to 100 and a non-negative offset."
        )
    owned = (
        select(PlaygroundRun, Tenant.name)
        .join(Tenant, Tenant.id == PlaygroundRun.tenant_id)
        .join(
            TenantMembership,
            (TenantMembership.tenant_id == PlaygroundRun.tenant_id)
            & (TenantMembership.user_id == user_id),
        )
        .where(
            PlaygroundRun.owner_user_id == user_id,
            Tenant.purpose == "playground",
            TenantMembership.role == "owner",
            TenantMembership.status == "active",
        )
    )
    total = session.scalar(select(func.count()).select_from(owned.subquery()))
    runs = session.execute(
        owned.order_by(
            (PlaygroundRun.sandbox_kind == "practice").desc(),
            PlaygroundRun.created_at.desc(),
            PlaygroundRun.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "runs": [_run_summary(run, name) for run, name in runs],
        "total": total,
        "limit": limit,
        "offset": offset,
        "entry_enabled": True,
        "chat_available": False,
        "presets": list(catalog.PRESETS),
        "quotas": _capacity(session, user_id),
    }


def _seed_references(session: Session, run: PlaygroundRun) -> dict:
    """Create the entire fixed preset without an internal commit or source fiction."""
    parties = {
        key: create_party(
            session,
            run.tenant_id,
            session.get(Tenant, run.tenant_id).name
            if key == "company" and run.sandbox_kind == "practice"
            else name,
            role,
            _commit=False,
        ).id
        for key, name, role in catalog.PARTIES
    }
    location = create_location(session, run.tenant_id, catalog.WAREHOUSE, _commit=False)
    items = {
        sku: create_item(
            session,
            run.tenant_id,
            sku,
            name,
            default_location_id=location.id,
            _commit=False,
        ).id
        for sku, name in catalog.ITEMS
    }
    return {"parties": parties, "locations": {"warehouse": location.id}, "items": items}


def _initialize(session: Session, run_id: str, user_id: str) -> PlaygroundRun:
    company_run = require_playground_run(session, run_id, user_id)
    if company_run.storyline_key is not None:
        from reality.services.storyline import initialize as initialize_storyline

        return initialize_storyline(session, run_id, user_id)
    if company_run.preset_key in {
        "company-empty",
        "international-demo",
        "atlas-execution",
    }:
        from reality.services.company_setup import initialize_profile

        return initialize_profile(session, run_id, user_id)
    # Metadata is already durable. Reacquire the owner lock after that commit;
    # every reference and the ready transition share this second transaction.
    _locked_owner(session, user_id)
    run = require_playground_run(session, run_id, user_id)
    if run.status in {"active", "archived"}:
        session.commit()
        return run
    preset = catalog.find_preset(run.preset_key, run.preset_version)
    if preset is None or (run.lesson_key, run.lesson_version) != (
        preset["lesson_key"],
        preset["lesson_version"],
    ):
        raise InvalidOperation("Unsupported Playground setup version.")
    if run.initialization_progress:
        raise Conflict("Incomplete Playground setup requires review before retry.")
    if session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.id != run.id,
            (PlaygroundRun.status == "initializing")
            | (
                (PlaygroundRun.status == "active")
                & (PlaygroundRun.sandbox_kind == "temporary")
                & (run.sandbox_kind == "temporary")
            ),
        )
    ):
        raise Conflict("Resume the existing run before retrying another setup.")
    tenant = session.get(Tenant, run.tenant_id)
    if tenant.archived_at is not None:
        raise PlaygroundOperationDenied("Archived Playground setup is unavailable.")
    run.status = "initializing"
    run.initialization_error_code = None
    session.flush()
    try:
        with session.begin_nested():
            with _seed_scope(session, run.id, user_id):
                references = _seed_references(session, run)
            run.initialization_progress = references
            run.status = "active"
            run.ready_at = now()
            session.flush()
    except Exception:  # noqa: BLE001 - Persist a safe outcome after rolling back the entire seed.
        # Keep owner locking while rolling back only the atomic setup attempt.
        # Raw exception text can contain secrets and is never stored in the run.
        run.status = "initialization_failed"
        run.initialization_error_code = "seed_failed"
        run.initialization_progress = {}
        run.ready_at = None
    session.commit()
    return run


def start_run(
    session: Session,
    user_id: str,
    request_key: str,
    *,
    preset_key: str = catalog.PRESET_KEY,
    preset_version: int = catalog.PRESET_VERSION,
    sandbox_kind: str = "temporary",
    company_name: str | None = None,
    confirmed: bool = False,
    live_simulation: bool = False,
    initialize: bool = True,
) -> PlaygroundRun:
    """Confirm one private run; retries resume its atomic seed, never duplicate it.

    With `initialize=False` the durable metadata is committed and the caller owns the
    initialization, which is how company setup keeps the seed out of its request.
    """
    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm Playground creation first.")
    if not request_key or request_key != request_key.strip() or len(request_key) > 128:
        raise InvalidOperation("A request key of 1 to 128 characters is required.")
    if type(live_simulation) is not bool or (
        live_simulation
        and (preset_key != "international-demo" or sandbox_kind != "practice")
    ):
        raise InvalidOperation(
            "Live simulation requires an international demo Sandbox."
        )
    name = company_name.strip() if isinstance(company_name, str) else ""
    if (
        sandbox_kind not in {"temporary", "practice"}
        or (sandbox_kind == "practice" and (not name or len(name) > 120))
        or (sandbox_kind == "temporary" and company_name is not None)
    ):
        raise InvalidOperation(
            "Choose a sandbox kind and a practice company name of 1 to 120 characters."
        )
    tenant_name = name if sandbox_kind == "practice" else "Playground · Trading"
    _locked_owner(session, user_id)
    from reality.db.company_setup import OrdinaryCompanyCreation
    from reality.services.company_setup import PRESETS, fingerprint

    if session.scalar(
        select(OrdinaryCompanyCreation.id).where(
            OrdinaryCompanyCreation.actor_id == user_id,
            OrdinaryCompanyCreation.request_key == request_key,
        )
    ):
        raise Conflict("The request key belongs to an ordinary company creation.")
    if preset_key in PRESETS.values() and sandbox_kind != "practice":
        raise InvalidOperation("Company profiles require a named practice company.")
    existing = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.client_request_key == request_key,
        )
    )
    if existing is not None:
        if (
            existing.preset_key,
            existing.preset_version,
            existing.sandbox_kind,
            session.get(Tenant, existing.tenant_id).name,
        ) != (
            preset_key,
            preset_version,
            sandbox_kind,
            tenant_name,
        ):
            raise Conflict("The request key belongs to a different Playground preset.")
        return (
            existing if not initialize else _initialize(session, existing.id, user_id)
        )
    preset = catalog.find_preset(preset_key, preset_version)
    if preset is None:
        raise InvalidOperation("Unsupported Playground preset version.")
    _check_capacity(session, user_id)
    if session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.owner_user_id == user_id,
            (PlaygroundRun.status == "initializing")
            | (
                (PlaygroundRun.status == "active")
                & (PlaygroundRun.sandbox_kind == "temporary")
                & (sandbox_kind == "temporary")
            ),
        )
    ):
        raise Conflict(
            "Resume the existing run; a fresh run requires explicit restart."
        )
    tenant = Tenant(id=uid("ten"), name=tenant_name, purpose="playground")
    session.add(tenant)
    session.flush()
    from reality.services.finance.accounts import _bootstrap_accounts

    _bootstrap_accounts(session, tenant.id)
    run = PlaygroundRun(
        id=uid("pgr"),
        tenant_id=tenant.id,
        owner_user_id=user_id,
        preset_key=preset_key,
        sandbox_kind=sandbox_kind,
        preset_version=preset_version,
        lesson_key=preset["lesson_key"],
        lesson_version=preset["lesson_version"],
        client_request_key=request_key,
        status="initializing",
    )
    if preset_key in PRESETS.values():
        content = next(key for key, value in PRESETS.items() if value == preset_key)
        run.initialization_progress = {
            "creation_intent": {
                "name": tenant_name,
                "environment": "sandbox",
                "content": content,
                "live_simulation": live_simulation,
                "fingerprint": fingerprint(
                    tenant_name, "sandbox", content, live_simulation
                ),
            },
            "anchor": datetime.combine(
                now().date(), datetime.min.time(), UTC
            ).isoformat(),
        }
    session.add_all(
        [
            run,
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=user_id,
                role="owner",
                status="active",
            ),
        ]
    )
    session.commit()
    return run if not initialize else _initialize(session, run.id, user_id)


def restart_run(
    session: Session,
    user_id: str,
    run_id: str,
    *,
    preset_key: str | None = None,
    preset_version: int | None = None,
    request_key: str | None = None,
    confirmed: bool = False,
) -> PlaygroundRun:
    """Archive one unresolved active run and create a fresh private dataset.

    The old tenant and its uncertain action remain preserved and read-only. This
    is deliberately an explicit recovery path; it never retries the unknown action.
    """
    if confirmed is not True:
        raise PlaygroundOperationDenied(
            "Confirm starting a fresh Playground run first."
        )
    _locked_owner(session, user_id)
    run = require_playground_run(session, run_id, user_id)
    selected_key = preset_key if preset_key is not None else run.preset_key
    if run.sandbox_kind == "practice":
        raise PlaygroundOperationDenied(
            "Practice companies cannot be replaced by a fresh experiment."
        )
    selected_version = (
        preset_version if preset_version is not None else run.preset_version
    )
    if catalog.find_preset(selected_key, selected_version) is None:
        raise InvalidOperation("Unsupported Playground preset version.")
    if request_key is not None:
        if (
            not request_key
            or request_key != request_key.strip()
            or len(request_key) > 128
        ):
            raise InvalidOperation("A request key of 1 to 128 characters is required.")
        if session.scalar(
            select(PlaygroundRun.id).where(
                PlaygroundRun.owner_user_id == user_id,
                PlaygroundRun.client_request_key == request_key,
            )
        ):
            return start_run(
                session,
                user_id,
                request_key,
                preset_key=selected_key,
                preset_version=selected_version,
                confirmed=True,
            )
    require_playground_run(session, run_id, user_id, for_write=True)
    if run.status != "active":
        raise Conflict("Only an active Playground run can be archived for restart.")
    _check_capacity(session, user_id)
    run.status = "archived"
    run.archived_at = now()
    session.flush()
    return start_run(
        session,
        user_id,
        request_key or f"restart-{run.id}-{uid('req')}",
        preset_key=selected_key,
        preset_version=selected_version,
        confirmed=True,
    )


def archive_run(
    session: Session, user_id: str, run_id: str, *, confirmed: bool = False
) -> PlaygroundRun:
    """Hide an owned sandbox or practice company from the company switcher (spec 186).

    Nothing is deleted: the playground tenant and its records stay, read-only, and the
    run can be restored. The status flip is the same one restart and storyline restart use.
    """
    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm archiving the sandbox first.")
    _locked_owner(session, user_id)
    run = require_playground_run(session, run_id, user_id)
    if run.status == "archived":
        raise Conflict("The sandbox is already archived.")
    if run.status not in {"active", "initialization_failed"}:
        raise Conflict("Only a ready or failed sandbox can be archived.")
    run.status = "archived"
    run.archived_at = now()
    # The API session does not commit on its own; every lifecycle service persists itself.
    session.commit()
    return run


def restore_run(
    session: Session, user_id: str, run_id: str, *, confirmed: bool = False
) -> PlaygroundRun:
    """Bring an archived sandbox back to the switcher (spec 186)."""
    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm restoring the sandbox first.")
    _locked_owner(session, user_id)
    run = require_playground_run(session, run_id, user_id)
    if run.status != "archived":
        raise Conflict("Only an archived sandbox can be restored.")
    if session.get(Tenant, run.tenant_id).archived_at is not None:
        raise Conflict("The sandbox tenant is archived and cannot be restored here.")
    if run.storyline_key is not None and session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.storyline_key == run.storyline_key,
            PlaygroundRun.status == "active",
        )
    ):
        raise Conflict(
            "Another active company already runs this storyline. Archive it first."
        )
    run.status = "active"
    run.archived_at = None
    session.commit()
    return run
