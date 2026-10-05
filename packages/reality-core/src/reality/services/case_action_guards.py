"""Synchronous case guards at shared proposal and actual effect boundaries."""

import json
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    Commitment,
    DocumentLine,
    Movement,
    OutboundDeliveryLine,
    Reservation,
    Shipment,
    ShipmentAdviceLine,
    ShipmentEvent,
    ShipmentPackage,
)
from reality.db.operational_cases import CaseProposalLink
from reality.services import core
from reality.services import operational_cases as cases
from reality.services.business_locks import lock_delivery_state
from reality.services.memberships import Principal

_execution = ContextVar("operational_case_execution", default=None)


@contextmanager
def execution_context(
    session: Session,
    tenant_id: str,
    *,
    automatic: bool,
    proposal_id: str | None = None,
    source_record_id: str | None = None,
    principal: Principal | None = None,
):
    token = _execution.set(
        (session, tenant_id, automatic, proposal_id, source_record_id, principal)
    )
    try:
        yield
    finally:
        _execution.reset(token)


@contextmanager
def automated_execution(
    session: Session, tenant_id: str, *, proposal_id: str | None = None
):
    """Trusted internal execution context; never a user/tool input parameter."""
    with execution_context(session, tenant_id, automatic=True, proposal_id=proposal_id):
        yield


def is_automatic(session: Session, tenant_id: str):
    context = _execution.get()
    if context is not None and context[:2] == (session, tenant_id):
        return context[2]
    from reality.mcp.principal import current_mcp_principal

    # An external token never becomes a verified human by asserting confirmed=True.
    return current_mcp_principal() is not None


def resolve_cases(
    session: Session,
    tenant_id: str,
    operation: str,
    arguments: dict[str, Any],
    *,
    ensure: bool = False,
):
    from reality.tools.finance import FINANCE_COMMANDS

    # These channels stage evidence or own an independent goal. A reference to
    # an order is a dependency, not ownership of its fulfillment work.
    if operation in FINANCE_COMMANDS or operation in {
        "source_ingest",
        "source_record_ingest",
        "return_announce",
        "announce_customer_return",
    }:
        return [], False
    if operation == "intake_apply":
        plan = arguments.get("plan", arguments)
        owned_operations = {
            "commitment": "create_commitment",
            "commitment_revision": "revise_commitment",
            "commitment_cancellation": "cancel_commitment",
            "credit_hold": "hold_commitment",
            "inventory_adjustment": "record_movement",
        }
        found, uncovered = set(), False
        for effect in plan.get("effects", []):
            name = owned_operations.get(effect["operation"])
            if name is not None:
                resolved, unknown = resolve_cases(
                    session, tenant_id, name, effect["arguments"], ensure=ensure
                )
                found.update(resolved)
                uncovered |= unknown
        return sorted(found), uncovered
    ids = set()
    commitments = set()
    announcements = set()
    unknown = False
    return_work = (
        operation
        in {
            "record_return_disposition",
            "record_customer_exchange",
            "return_disposition",
            "customer_exchange_record",
        }
        or arguments.get("movement_type") == "return"
        or arguments.get("purpose") == "customer_return"
    )

    def walk(values):
        nonlocal unknown
        if isinstance(values, list):
            for value in values:
                walk(value)
            return
        if not isinstance(values, dict):
            return
        for key, value in values.items():
            if key in {
                "payload",
                "actor_context",
                "reviewed",
                "_delivery_review",
                "_case_business_review",
                "references",
                "observations",
            }:
                continue
            if key == "commitment_ids" and isinstance(value, list):
                commitments.update(value)
            elif isinstance(value, (list, dict)):
                walk(value)
            elif value and key in {
                "commitment_id",
                "meant_for_commitment_id",
                "customer_commitment_id",
            }:
                commitments.add(value)
            elif value and key in {"return_announcement_id", "announcement_id"}:
                announcements.add(value)
            elif value and key in {
                "movement_id",
                "return_movement_id",
                "resolves_movement_id",
            }:
                row = core._tenant_record_read(session, Movement, tenant_id, value)
                if row.return_announcement_id:
                    announcements.add(row.return_announcement_id)
                elif row.type == "return":
                    unknown = True
                elif row.commitment_id:
                    commitments.add(row.commitment_id)
            elif value and key in {"shipment_id", "shipment_package_id", "event_id"}:
                if key == "event_id" and operation not in {
                    "supersede_shipment_event",
                    "shipment_event_supersede",
                }:
                    continue
                model = {
                    "shipment_id": Shipment,
                    "shipment_package_id": ShipmentPackage,
                    "event_id": ShipmentEvent,
                }[key]
                row = core._tenant_record_read(session, model, tenant_id, value)
                shipment_id = row.id if key == "shipment_id" else row.shipment_id
                commitments.update(
                    session.scalars(
                        select(ShipmentAdviceLine.commitment_id).where(
                            ShipmentAdviceLine.tenant_id == tenant_id,
                            ShipmentAdviceLine.shipment_id == shipment_id,
                        )
                    )
                )
                movements = session.scalars(
                    select(Movement)
                    .join(
                        ShipmentPackage,
                        (ShipmentPackage.tenant_id == Movement.tenant_id)
                        & (ShipmentPackage.id == Movement.shipment_package_id),
                    )
                    .where(
                        Movement.tenant_id == tenant_id,
                        ShipmentPackage.shipment_id == shipment_id,
                    )
                )
                for movement in movements:
                    if movement.return_announcement_id:
                        announcements.add(movement.return_announcement_id)
                    elif movement.commitment_id:
                        commitments.add(movement.commitment_id)
                    if (
                        movement.type == "return"
                        and not movement.return_announcement_id
                    ):
                        unknown = True
            elif value and key == "reservation_id":
                row = core._tenant_record_read(session, Reservation, tenant_id, value)
                commitments.add(row.commitment_id)
            elif value and key == "outbound_delivery_id":
                commitments.update(
                    session.scalars(
                        select(OutboundDeliveryLine.commitment_id).where(
                            OutboundDeliveryLine.tenant_id == tenant_id,
                            OutboundDeliveryLine.outbound_delivery_id == value,
                        )
                    )
                )
            elif value and key in {"document_line_id", "line_id"}:
                row = core._tenant_record_read(session, DocumentLine, tenant_id, value)
                commitments.update(
                    session.scalars(
                        select(Commitment.id).where(
                            Commitment.tenant_id == tenant_id,
                            Commitment.document_id == row.document_id,
                            Commitment.type == "customer_delivery",
                        )
                    )
                )
            elif value and key in {"document_id", "order_id", "order_document_id"}:
                commitments.update(
                    session.scalars(
                        select(Commitment.id).where(
                            Commitment.tenant_id == tenant_id,
                            Commitment.document_id == value,
                            Commitment.type == "customer_delivery",
                        )
                    )
                )

    walk(arguments)
    if operation in {
        "hold_party_delivery",
        "release_party_delivery_hold",
        "party_delivery_hold",
        "party_delivery_hold_release",
    } and arguments.get("party_id"):
        commitments.update(
            session.scalars(
                select(Commitment.id).where(
                    Commitment.tenant_id == tenant_id,
                    Commitment.to_party_id == arguments["party_id"],
                    Commitment.type == "customer_delivery",
                    Commitment.status == "open",
                )
            )
        )
    if (
        operation in {"close_stale_promises", "stale_closure"}
        and "due_before" in arguments
    ):
        commitments.update(
            row.id
            for row in core._stale_promises(
                session,
                tenant_id,
                direction=arguments["direction"],
                due_before=arguments["due_before"],
            )
        )
    # Physical customer shipment writes need an authoritative promise anchor.
    # Omitting it must not turn case-controlled work into unowned inventory work.
    if operation in {"record_movement", "movement_record"} and (
        arguments.get("movement_type") == "shipment" and not commitments
    ):
        unknown = True
    if return_work and not announcements:
        unknown = True
        commitments.clear()
    for ann_id in sorted(announcements):
        if ensure:
            cases.ensure_return(session, tenant_id, ann_id)
        resolved = cases.object_cases(session, tenant_id, "return_announcement", ann_id)
        ids.update(resolved)
        unknown |= not bool(resolved)
    if announcements and return_work:
        commitments.clear()  # Return owns work; original fulfillment is only related.
    for com_id in sorted(commitments):
        row = core._tenant_record_read(session, Commitment, tenant_id, com_id)
        if row.type != "customer_delivery":
            continue
        if ensure:
            cases.ensure_commitment(session, tenant_id, com_id)
        resolved = cases.object_cases(session, tenant_id, "commitment", com_id)
        ids.update(resolved)
        unknown |= not bool(resolved)
    return sorted(ids), unknown


def guard_operation(
    session: Session, tenant_id: str, operation: str, arguments: dict[str, Any]
):
    if not cases.coordination_enabled(session, tenant_id) or not is_automatic(
        session, tenant_id
    ):
        return
    lock_delivery_state(session, tenant_id)
    if operation in {"record_customer_exchange", "customer_exchange_record"} or (
        operation == "create_commitment"
        and arguments.get("commitment_type") == "customer_delivery"
        and not arguments.get("document_id")
    ):
        raise core.InvalidOperation(code="case_coverage_unavailable")
    case_ids, unknown = resolve_cases(
        session, tenant_id, operation, arguments, ensure=True
    )
    if unknown:
        raise core.InvalidOperation(code="case_coverage_unavailable")
    context = _execution.get()
    proposal_id = (
        context[3]
        if context is not None and context[:2] == (session, tenant_id)
        else arguments.get("action_id")
    )
    accepted_source = (
        context[4]
        if context is not None and context[:2] == (session, tenant_id)
        else None
    )
    for case_id in case_ids:
        case = cases._case(session, tenant_id, case_id, lock=True)
        if case.control_mode != "automation":
            raise core.InvalidOperation(code="case_human_owned")
        if proposal_id:
            binding = session.get(CaseProposalLink, (tenant_id, case_id, proposal_id))
            if (
                binding is None
                or binding.bound_control_revision != case.control_revision
            ):
                raise core.InvalidOperation(code="case_action_stale")
        gaps = cases._coverage_gaps(session, tenant_id, case)
        if any(row["source_record_id"] != accepted_source for row in gaps):
            raise core.InvalidOperation(code="case_source_unresolved")


def _load_review_state(session, tenant_id, operation, arguments):
    if not cases.coordination_enabled(session, tenant_id):
        return
    lock_delivery_state(session, tenant_id)
    ids, _ = resolve_cases(session, tenant_id, operation, arguments, ensure=True)
    # Load the same canonical records before both business and case snapshots.
    # Binding afterwards must not change the Numeric representation of the review.
    for case_id in ids:
        cases.business_review(session, tenant_id, case_id)


def _refresh_bound_business_review(session, tenant_id, proposal_id, preview):
    links = list(
        session.scalars(
            select(CaseProposalLink).where(
                CaseProposalLink.tenant_id == tenant_id,
                CaseProposalLink.proposal_id == proposal_id,
            )
        )
    )
    if links:
        # Explicit business re-review does not change any old control binding.
        preview["_case_business_review"] = {
            link.case_id: cases.business_review(session, tenant_id, link.case_id)
            for link in links
        }
    return preview


def bind_arguments(
    session: Session,
    tenant_id: str,
    proposal_id: str | None,
    operation: str,
    arguments: dict[str, Any],
):
    if not cases.coordination_enabled(session, tenant_id):
        return []
    ids, _ = resolve_cases(session, tenant_id, operation, arguments, ensure=True)
    cases.bind_proposal(session, tenant_id, proposal_id, ids)
    if ids and operation != "intake_apply":
        proposal = core._tenant_record_read(
            session, ChangeProposal, tenant_id, proposal_id
        )
        preview = json.loads(proposal.output)
        if isinstance(preview, dict):
            if "_case_business_review" in preview:
                return ids
            preview["_case_business_review"] = {
                case_id: cases.business_review(session, tenant_id, case_id)
                for case_id in ids
            }
            proposal.output = json.dumps(preview, sort_keys=True, default=str)
            session.flush()
    return ids


def guard_proposal(
    session: Session, tenant_id: str, proposal_id: str | None, *, automatic: bool
):
    if not cases.coordination_enabled(session, tenant_id) or not automatic:
        return
    lock_delivery_state(session, tenant_id)
    proposal = core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    if proposal.status == "executed":
        return
    arguments = json.loads(proposal.input)
    ids, _ = resolve_cases(
        session, tenant_id, proposal.type.removeprefix("tool:"), arguments, ensure=True
    )
    if ids and proposal.type != "tool:intake_apply":
        review = json.loads(proposal.output).get("_case_business_review", {})
        if any(
            review.get(case_id) != cases.business_review(session, tenant_id, case_id)
            for case_id in ids
        ):
            raise core.InvalidOperation(code="case_review_stale")
    with execution_context(
        session,
        tenant_id,
        automatic=True,
        proposal_id=proposal_id,
        source_record_id=arguments.get("plan", arguments).get("source_record_id")
        if proposal.type == "tool:intake_apply"
        else None,
    ):
        guard_operation(
            session,
            tenant_id,
            proposal.type.removeprefix("tool:"),
            arguments,
        )


def human_principal(session: Session, tenant_id: str):
    context = _execution.get()
    if (
        context is None
        or context[:2] != (session, tenant_id)
        or context[2]
        or context[5] is None
    ):
        raise core.InvalidOperation(code="case_human_confirmation_required")
    return context[5]
