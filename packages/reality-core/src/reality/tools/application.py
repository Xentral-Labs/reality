from __future__ import annotations

import json
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Commitment,
    Item,
    Location,
    Movement,
    Party,
    PaymentTerm,
    Reservation,
    now,
    uid,
)
from reality.demo.normal_month import run_normal_month
from reality.services.artifacts import get_artifact, mark_artifact_attached
from reality.services.core import (
    InvalidOperation,
    NotFound,
    add_party_group_member,
    allocate_credit_note,
    allocate_supplier_credit_note,
    announce_customer_return,
    assign_group_price_list,
    assign_party_price_list,
    close_stale_promises,
    correct_lot_expiry,
    correct_manual_document,
    correct_manual_document_lines,
    correct_movement,
    create_handling_unit,
    create_items,
    create_locations,
    create_lot,
    create_manual_document_with_lines,
    create_manual_order,
    create_parties,
    create_party_group,
    create_payment_term,
    create_price_list,
    create_price_list_entry,
    create_serial_unit,
    create_source_capability,
    create_source_system,
    discover_business_records,
    enqueue_source,
    ensure_demo,
    execute_payment_run,
    executing_proposal,
    expired_lots,
    get_tenant,
    hold_commitment,
    hold_document_commitments,
    hold_party_delivery,
    install_connector_shell,
    interpretation_coverage,
    observe_fact,
    post_customer_payment,
    post_customer_refund,
    post_sales_credit_note,
    post_sales_invoice,
    post_supplier_credit_note,
    post_supplier_invoice,
    post_supplier_payment,
    post_supplier_refund,
    preview_ledger_reversal,
    preview_master_data_updates,
    preview_movement_correction,
    preview_payment_run,
    preview_stale_promise_closure,
    record_corrected_document_source,
    record_movement,
    record_sales_credit,
    record_sales_invoice,
    record_supplier_invoice,
    release_commitment_hold,
    release_document_holds,
    release_party_delivery_hold,
    release_reservation,
    reserve,
    return_announcements,
    reverse_ledger_posting_group,
    revise_commitment,
    set_master_data_active,
    set_source_capability_active,
    set_source_system_active,
    state_lot_expiry,
    update_items,
    update_locations,
    update_parties,
    update_party_group,
    update_payment_term,
    update_price_list,
    utc_datetime,
    withdraw_return_announcement,
)
from reality.services.customer_exchanges import record_customer_exchange
from reality.services.exceptions import (
    explain_operational_exception,
    operational_exception_rows,
)
from reality.services.memberships import (
    Principal,
    create_invitation,
    normalize_email,
    remove_member,
    resend_invitation,
    revoke_invitation,
)
from reality.services.projections import (
    COMMITMENT_REGISTER,
    FULFILLMENT_BLOCKERS,
    FULFILLMENT_QUEUE,
    INVENTORY,
    ITEM_SUPPLY_DEMAND,
    explain_order_projection,
    materialized_resolve_price,
    projection_rows,
)
from reality.services.reality_gaps import (
    activate_rule,
    add_gap_entry,
    capture_gap,
    decide_gap,
    disable_rule,
    gap_detail,
    list_gaps,
    prepare_implementation,
    recommend_gap,
    replay_rule,
    simulate_rule,
)
from reality.services.return_dispositions import record_return_disposition
from reality.services.shipments import (
    record_packaged_execution,
    record_shipment_event,
    record_shipment_notice,
    shipment_explain,
    shipments_list,
    supersede_shipment_event,
)
from reality.services.supply_assignments import assign_supply, supply_coverage
from reality.services.tenant_policy import (
    require_proposal_creation,
    require_proposal_decision,
)

ToolHandler = Callable[[Session, str, dict[str, Any]], Any]
from reality.domain.proposal_decisions import (
    ACCOUNT_MUTATION_TOOLS,
    MEMBERSHIP_MUTATION_TOOLS,
    REFERENCE_MUTATION_TOOLS,
)
from reality.services.proposal_decisions import (
    require_decision_authority,
    resolve_decision_policy,
)


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    mutating: bool
    handler: ToolHandler


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "id"):
        return value.id
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _human_principal(arguments: dict[str, Any]) -> Principal:
    user_id = str(arguments.pop("_confirming_user_id", ""))
    if not user_id:
        raise InvalidOperation(code="membership_change_owner_required")
    return Principal(user_id)


def _member_invite(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Invite one company member.

    BUSINESS RULE application.member_invite.1:
    Route this company-scoped request to create_invitation. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.member_invite.1
    invitation = create_invitation(
        session,
        tenant_id,
        _human_principal(arguments),
        str(arguments["email"]),
        locale=str(arguments.get("locale", "en")),
    )
    return {"status": "pending", "invitation_id": invitation.id if invitation else None}


def _invitation_resend(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Resend one company invitation.

    BUSINESS RULE application.invitation_resend.1:
    Route this company-scoped request to resend_invitation. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.invitation_resend.1
    invitation = resend_invitation(
        session,
        tenant_id,
        _human_principal(arguments),
        str(arguments["invitation_id"]),
    )
    return {"status": invitation.status, "invitation_id": invitation.id}


def _invitation_revoke(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Revoke one company invitation.

    BUSINESS RULE application.invitation_revoke.1:
    Route this company-scoped request to revoke_invitation. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.invitation_revoke.1
    revoke_invitation(
        session,
        tenant_id,
        _human_principal(arguments),
        str(arguments["invitation_id"]),
    )
    return {"status": "revoked", "invitation_id": arguments["invitation_id"]}


def _member_remove(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Remove one active non-owner member.

    BUSINESS RULE application.member_remove.1:
    Route this company-scoped request to remove_member. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.member_remove.1
    remove_member(
        session,
        tenant_id,
        _human_principal(arguments),
        str(arguments["membership_id"]),
    )
    return {"status": "removed", "membership_id": arguments["membership_id"]}


def _read_format(arguments: dict[str, Any]) -> str:
    value = arguments.get("response_format", "legacy")
    if value not in {"legacy", "page"}:
        raise InvalidOperation("Response format must be page or legacy.")
    if value == "legacy" and arguments.get("cursor") is not None:
        raise InvalidOperation("A cursor requires page response format.")
    return value


def _projection_read(
    session: Session, tenant_id: str, name: str, arguments: dict[str, Any]
) -> Any:
    if _read_format(arguments) == "page":
        from reality.services.read_contracts import operational_page

        return operational_page(session, tenant_id, name, arguments)
    if (
        arguments.get("item_id")
        or arguments.get("location_id")
        or arguments.get("view", "aggregate") != "aggregate"
    ):
        raise InvalidOperation("Inventory filters require page response format.")
    return projection_rows(session, tenant_id, name)


def _inventory(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read derived inventory.

    BUSINESS RULE application.inventory.1:
    Route this company-scoped request to _projection_read. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.inventory.1
    return _projection_read(session, tenant_id, INVENTORY, arguments)


def _exceptions(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read derived operational exceptions.

    BUSINESS RULE application.exceptions.1:
    Route this company-scoped request to operational_exception_rows. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.exceptions.1
    return operational_exception_rows(session, tenant_id)


def _exception_explain(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Explain one current operational exception.

    BUSINESS RULE application.exception_explain.1:
    Route this company-scoped request to explain_operational_exception. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.exception_explain.1
    return explain_operational_exception(session, tenant_id, arguments["exception_id"])


def _interpretation_coverage(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read explicit source interpretation outcomes without raw payloads.

    BUSINESS RULE application.interpretation_coverage.1:
    Route this company-scoped request to interpretation_coverage. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.interpretation_coverage.1
    return interpretation_coverage(
        session, tenant_id, arguments.get("source_record_id")
    )


def _commitments(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read operational obligations.

    BUSINESS RULE application.commitments.1:
    Route this company-scoped request to _projection_read. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.commitments.1
    return _projection_read(session, tenant_id, COMMITMENT_REGISTER, arguments)


def _finance_balances(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read balances derived from the journal.

    BUSINESS RULE application.finance_balances.1:
    Route this company-scoped request to finance_balances. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.read_contracts import finance_balances

    # reality-rule: application.finance_balances.1
    return finance_balances(session, tenant_id)


def _dunning_context(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Preview one manual dunning notice and return its finance revision.

    BUSINESS RULE application.dunning_context.1:
    Route this company-scoped request to dunning_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.dunning import dunning_context

    # reality-rule: application.dunning_context.1
    return dunning_context(session, tenant_id, arguments)


def _dunning_notices(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    List manual dunning notices with fee and reversal trace.

    BUSINESS RULE application.dunning_notices.1:
    Route this company-scoped request to notices. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    del arguments
    from reality.services.dunning import notices

    # reality-rule: application.dunning_notices.1
    return notices(session, tenant_id)


def _dunning_schedule(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read the company dunning schedule: waiting days and fixed fee per level.

    BUSINESS RULE application.dunning_schedule.1:
    Route this company-scoped request to schedule. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.dunning_runs import schedule

    # reality-rule: application.dunning_schedule.1
    return schedule(session, tenant_id)


def _credit_exposure(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read a customer's credit exposure: open invoices plus open uninvoiced orders minus available credits against the limit, with overdue invoices and payables named.

    BUSINESS RULE application.credit_exposure.1:
    Route this company-scoped request to _json_exposure, credit_exposure. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.credit_exposure import _json_exposure, credit_exposure

    # reality-rule: application.credit_exposure.1
    return _json_exposure(
        credit_exposure(
            session,
            tenant_id,
            str(arguments.get("party_id") or ""),
            as_of=arguments.get("as_of"),
        )
    )


def _payment_returns(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    List returned customer payments (returned direct debits and chargebacks) with their reason, fee and reopened invoices.

    BUSINESS RULE application.payment_returns.1:
    Route this company-scoped request to returns. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.payment_returns import returns

    # reality-rule: application.payment_returns.1
    return returns(session, tenant_id)


def _payment_return(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read one returned customer payment with its reason, reference, fee and reopened invoices.

    BUSINESS RULE application.payment_return.1:
    Route this company-scoped request to return_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.payment_returns import return_detail

    # reality-rule: application.payment_return.1
    return return_detail(session, tenant_id, str(arguments.get("return_id") or ""))


def _payouts(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    List marketplace and payment-provider payouts with their net amount and the lines nothing booked yet.

    BUSINESS RULE application.payouts.1:
    Route this company-scoped request to payouts. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.payouts import payouts

    # reality-rule: application.payouts.1
    return payouts(session, tenant_id)


def _payout(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read one payout: every stated line with what it booked (payment, refund, chargeback, fee), the invoices it settled, the shipment a tracking number names, or why it stays unbooked.

    BUSINESS RULE application.payout.1:
    Route this company-scoped request to payout_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.payouts import payout_detail

    # reality-rule: application.payout.1
    return payout_detail(session, tenant_id, str(arguments.get("payout_id") or ""))


def _payment_authorizations(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    List card and wallet payment authorizations, optionally for one order, with what was captured, what is left and whether each is live, expired or captured.

    BUSINESS RULE application.payment_authorizations.1:
    Route this company-scoped request to authorizations. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.payment_authorizations import authorizations

    # reality-rule: application.payment_authorizations.1
    return authorizations(
        session,
        tenant_id,
        order_document_id=arguments.get("order_document_id") or None,
        as_of=arguments.get("as_of") or None,
    )


def _dunning_run_context(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Preview a dunning run: overdue items per customer, currency and level, items ready for collection and items left out with their reason.

    BUSINESS RULE application.dunning_run_context.1:
    Route this company-scoped request to run_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.dunning_runs import run_context

    # reality-rule: application.dunning_run_context.1
    return run_context(
        session,
        tenant_id,
        run_date=arguments.get("run_date"),
        party_ids=arguments.get("party_ids") or None,
    )


def _collection_handovers(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    List collection handovers with their invoices and delivery hold.

    BUSINESS RULE application.collection_handovers.1:
    Route this company-scoped request to handovers. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.dunning_runs import handovers

    # reality-rule: application.collection_handovers.1
    return handovers(session, tenant_id)


def _collection_handover(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read one collection handover with its invoices, last notices and delivery hold.

    BUSINESS RULE application.collection_handover.1:
    Route this company-scoped request to handover_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.dunning_runs import handover_detail

    # reality-rule: application.collection_handover.1
    return handover_detail(session, tenant_id, str(arguments.get("handover_id") or ""))


def _dunning_notice(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read one manual dunning notice with fee and reversal trace.

    BUSINESS RULE application.dunning_notice.1:
    Route this company-scoped request to notice_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.dunning import notice_detail

    # reality-rule: application.dunning_notice.1
    return notice_detail(session, tenant_id, arguments["notice_id"])


def _fulfillment_queue(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read the materialized order fulfillment queue.

    BUSINESS RULE application.fulfillment_queue.1:
    Route this company-scoped request to _projection_read. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.fulfillment_queue.1
    return _projection_read(session, tenant_id, FULFILLMENT_QUEUE, arguments)


def _fulfillment_readiness(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read the canonical fulfillment decision for one commitment.

    BUSINESS RULE application.fulfillment_readiness.1:
    Route this company-scoped request to fulfillment_readiness. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.fulfillment_readiness import fulfillment_readiness

    # reality-rule: application.fulfillment_readiness.1
    return fulfillment_readiness(
        session, tenant_id, arguments["commitment_id"]
    ).as_dict()


def _fulfillment_blockers(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read materialized order and item blockers.

    BUSINESS RULE application.fulfillment_blockers.1:
    Route this company-scoped request to _projection_read. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.fulfillment_blockers.1
    return _projection_read(session, tenant_id, FULFILLMENT_BLOCKERS, arguments)


def _item_supply_demand(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read materialized supply and demand by item.

    BUSINESS RULE application.item_supply_demand.1:
    Route this company-scoped request to _projection_read. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.item_supply_demand.1
    return _projection_read(session, tenant_id, ITEM_SUPPLY_DEMAND, arguments)


def _order_explain(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Explain one order through Source, Evidence, and Reality.

    BUSINESS RULE application.order_explain.1:
    Route this company-scoped request to explain_order_projection. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.order_explain.1
    return explain_order_projection(session, tenant_id, arguments["order_reference"])


def _shipments_list(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    List real physical shipments, distinct from delivery commitments.

    BUSINESS RULE application.shipments_list.1:
    Route this company-scoped request to shipments_list. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.shipments_list.1
    return shipments_list(session, tenant_id, **arguments)


def _shipment_explain(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Explain packages, tracking observations and physical Movements for one shipment.

    BUSINESS RULE application.shipment_explain.1:
    Route this company-scoped request to shipment_explain. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.shipment_explain.1
    return shipment_explain(session, tenant_id, arguments["shipment_id"])


def _shipment_notice_record(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Record a physical shipment notice without moving stock.

    BUSINESS RULE application.shipment_notice_record.1:
    Route this company-scoped request to record_shipment_notice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    values = dict(arguments)
    values["action_id"] = values.pop("_action_id", None)
    # reality-rule: application.shipment_notice_record.1
    shipment, package, event = record_shipment_notice(session, tenant_id, **values)
    return {"shipment_id": shipment.id, "package_id": package.id, "event_id": event.id}


def _shipment_execution(direction: str):
    def handler(session, tenant_id, arguments):
        """
        BUSINESS PURPOSE:
        Record packaged dispatch or receipt using the direction captured by the registered adapter.

        BUSINESS RULE application.shipment_execution.handler.1:
        Set the captured execution direction rather than accepting another direction from the argument object.

        BUSINESS RULE application.shipment_execution.handler.2:
        Call the canonical packaged-execution service with the company, captured direction and action identity; validation and physical effects remain in that service.
        """
        values = dict(arguments)
        # reality-rule: application.shipment_execution.handler.1
        values["direction"] = direction
        values["action_id"] = values.pop("_action_id", None)
        # reality-rule: application.shipment_execution.handler.2
        return record_packaged_execution(session, tenant_id, **values)

    return handler


def _shipment_event_record(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Append one attributed logistics observation.

    BUSINESS RULE application.shipment_event_record.1:
    Route this company-scoped request to record_shipment_event. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    values = dict(arguments)
    values["action_id"] = values.pop("_action_id", None)
    # reality-rule: application.shipment_event_record.1
    event = record_shipment_event(session, tenant_id, **values)
    return {"shipment_id": event.shipment_id, "event_id": event.id}


def _shipment_event_supersede(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Supersede one incorrect logistics observation without deleting it.

    BUSINESS RULE application.shipment_event_supersede.1:
    Route this company-scoped request to supersede_shipment_event. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    values = dict(arguments)
    values["action_id"] = values.pop("_action_id", None)
    # reality-rule: application.shipment_event_supersede.1
    correction = supersede_shipment_event(session, tenant_id, **values)
    return {
        "event_id": correction.superseded_event_id,
        "supersession_id": correction.id,
    }


def _reserve(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Allocate stock to a customer commitment.

    BUSINESS RULE application.reserve.1:
    Apply the requested promise, quantity, location and tracking identities through the shared reservation service.

    BUSINESS RULE application.reserve.2:
    Report no effect when allocated quantity is zero, complete when shortage is zero, and partial otherwise; retain the shared requested, allocated and shortage quantities.
    """
    # reality-rule: application.reserve.1
    result = reserve(
        session,
        tenant_id,
        arguments["commitment_id"],
        arguments.get("quantity"),
        handling_unit_id=arguments.get("handling_unit_id"),
        lot_id=arguments.get("lot_id"),
        serial_unit_id=arguments.get("serial_unit_id"),
        location_id=arguments.get("location_id"),
        action_id=arguments.get("_action_id"),
    )
    # reality-rule: application.reserve.2
    effect = (
        "none"
        if result.reserved == 0
        else "complete"
        if result.shortage == 0
        else "partial"
    )
    return {
        "proposal_id": arguments.get("_action_id"),
        "capability": "reserve",
        "reservation_id": result.reservation.id if result.reservation else None,
        "commitment_id": arguments["commitment_id"],
        "requested": result.requested,
        "applied": result.reserved,
        "reserved": result.reserved,
        "shortage": result.shortage,
        "effect": effect,
        "remaining_work": result.shortage,
        "verification_reads": [
            "proposal_execution_status",
            "inventory",
            "commitment_register",
        ],
        "event_id": result.event.id if result.event else None,
        "handling_unit_id": (
            result.reservation.handling_unit_id if result.reservation else None
        ),
        "lot_id": result.reservation.lot_id if result.reservation else None,
        "serial_unit_id": (
            result.reservation.serial_unit_id if result.reservation else None
        ),
    }


def _movement_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Correct one immutable Movement through an exact inverse and optional replacement.

    BUSINESS RULE application.movement_correct.1:
    Route this company-scoped request to correct_movement. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.movement_correct.1
    result = correct_movement(
        session,
        tenant_id,
        arguments["movement_id"],
        reason=arguments["reason"],
        replacement=arguments.get("replacement"),
        actor_context={"surface": "agent", "proposal": True},
        expected_revision=arguments.get("expected_revision"),
        preview_fingerprint=arguments.get("preview_fingerprint"),
        action_id=arguments.get("_action_id"),
    )
    return {
        "correction_id": result.correction_id,
        "original_movement_id": result.original_movement_id,
        "compensating_movement_id": result.compensating_movement_id,
        "replacement_movement_id": result.replacement_movement_id,
        "replayed": result.replayed,
    }


def _ledger_reverse(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Reverse one complete immutable Ledger posting group.

    BUSINESS RULE application.ledger_reverse.1:
    Route this company-scoped request to reverse_ledger_posting_group. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.ledger_reverse.1
    result = reverse_ledger_posting_group(
        session,
        tenant_id,
        arguments["posting_group_id"],
        reason=arguments["reason"],
        action_id=arguments.get("_action_id"),
        actor_context={"surface": "agent", "proposal": True},
        expected_revision=arguments.get("expected_revision"),
        preview_fingerprint=arguments.get("preview_fingerprint"),
    )
    return {
        "reversal_id": result.reversal_id,
        "original_posting_group_id": result.original_posting_group_id,
        "reversing_posting_group_id": result.reversing_posting_group_id,
        "replayed": result.replayed,
    }


def _seed_demo(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Build the compact demo company in an empty tenant.

    BUSINESS RULE application.seed_demo.1:
    Route this company-scoped request to get_tenant. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.seed_demo.1
    tenant = get_tenant(session, tenant_id)
    ensure_demo(session, tenant)
    return {"tenant_id": tenant.id, "result": "demo_ready"}


def _normal_month(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Run the deterministic September 2026 business month in an empty tenant.

    BUSINESS RULE application.normal_month.1:
    Route this company-scoped request to run_normal_month. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.normal_month.1
    return run_normal_month(session, tenant_id)


def _source_ingest(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Attach an immutable uploaded artifact to Source evidence and queue interpretation.

    BUSINESS RULE application.source_ingest.1:
    Route this company-scoped request to get_artifact. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.source_ingest.1
    artifact = get_artifact(session, tenant_id, arguments["artifact_id"])
    expected_target = (
        arguments.get("expected_target", "data_drop").strip() or "data_drop"
    )
    payload = {
        "artifact": {
            "filename": artifact.filename,
            "content_type": artifact.content_type,
            "byte_size": artifact.byte_size,
            "sha256": artifact.sha256,
            "storage": "managed",
        },
        "expected_target": expected_target,
    }
    source, job = enqueue_source(
        session,
        tenant_id,
        arguments.get("source_system", "manual_upload"),
        arguments.get("source_type", expected_target),
        arguments.get("external_id") or artifact.sha256,
        payload,
        context={
            "expected_target": expected_target,
            "artifact_id": artifact.id,
            "column_mapping": arguments.get("column_mapping") or {},
        },
        source_artifact_id=artifact.id,
    )
    mark_artifact_attached(artifact)
    return {
        "artifact_id": artifact.id,
        "source_record_id": source.id,
        "import_job_id": job.id,
        "import_status": job.status,
    }


def _party_create(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Create one or more Parties after confirmation.

    BUSINESS RULE application.party_create.1:
    Route this company-scoped request to create_parties. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.party_create.1
    return {
        "records": [
            {"family": "party", "id": record.id}
            for record in create_parties(
                session,
                tenant_id,
                arguments["records"],
                action_id=arguments.get("_action_id"),
            )
        ]
    }


def _company_party_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record the company itself as a business partner with the role company after confirmation.

    BUSINESS RULE application.company_party_record.1:
    Route this company-scoped request to record_company_party. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.company_party import record_company_party

    # reality-rule: application.company_party_record.1
    return record_company_party(
        session, tenant_id, arguments, action_id=arguments.get("_action_id")
    )


def _item_create(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Create one or more Items after confirmation.

    BUSINESS RULE application.item_create.1:
    IF an import file is supplied, use the shared item-import recorder. ELSE create the supplied item batch through the canonical master-data service.
    """
    # reality-rule: application.item_create.1
    if "import_file" in arguments:
        from reality.services.item_imports import record_item_import

        return record_item_import(session, tenant_id, arguments)
    return {
        "records": [
            {"family": "item", "id": record.id}
            for record in create_items(
                session,
                tenant_id,
                arguments["records"],
                action_id=arguments.get("_action_id"),
            )
        ]
    }


def _location_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Create one or more Locations after confirmation.

    BUSINESS RULE application.location_create.1:
    Route this company-scoped request to create_locations. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.location_create.1
    return {
        "records": [
            {"family": "location", "id": record.id}
            for record in create_locations(
                session,
                tenant_id,
                arguments["records"],
                action_id=arguments.get("_action_id"),
            )
        ]
    }


def _master_data_update_result(family: str, records: list[Any]) -> dict[str, Any]:
    return {"records": [{"family": family, "id": record.id} for record in records]}


def _party_update(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Update one or more Parties after confirmation.

    BUSINESS RULE application.party_update.1:
    Route this company-scoped request to update_parties. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.party_update.1
    return _master_data_update_result(
        "party",
        update_parties(
            session,
            tenant_id,
            arguments["records"],
            action_id=arguments.get("_action_id"),
        ),
    )


def _item_update(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Update one or more Items after confirmation.

    BUSINESS RULE application.item_update.1:
    Route this company-scoped request to update_items. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.item_update.1
    return _master_data_update_result(
        "item",
        update_items(
            session,
            tenant_id,
            arguments["records"],
            action_id=arguments.get("_action_id"),
        ),
    )


def _location_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Update one or more Locations after confirmation.

    BUSINESS RULE application.location_update.1:
    Route this company-scoped request to update_locations. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.location_update.1
    return _master_data_update_result(
        "location",
        update_locations(
            session,
            tenant_id,
            arguments["records"],
            action_id=arguments.get("_action_id"),
        ),
    )


def _fact_observe(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Record one source-supported operational observation after confirmation.

    BUSINESS RULE application.fact_observe.1:
    Route this company-scoped request to observe_fact. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.fact_observe.1
    fact = observe_fact(
        session,
        tenant_id,
        source_record_id=str(arguments["source_record_id"]),
        subject_type=str(arguments["subject_type"]),
        subject_id=str(arguments["subject_id"]),
        predicate=str(arguments["predicate"]),
        value=arguments["value"],
        observed_at=str(arguments["observed_at"]),
        idempotency_key=str(arguments["idempotency_key"]),
        action_id=arguments.get("_action_id"),
    )
    return {"fact_id": fact.id, "event_type": "fact.observed"}


def _reality_gaps(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    List missing-information work.

    BUSINESS RULE application.reality_gaps.1:
    Route this company-scoped request to list_gaps. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gaps.1
    result = list_gaps(session, tenant_id, **arguments)
    return {
        **result,
        "items": [
            {
                "id": row.id,
                "question": row.question,
                "intended_use": row.intended_use,
                "origin": row.origin,
                "status": row.status,
                "destination": row.destination,
                "revision": row.revision,
                "updated_at": row.updated_at,
            }
            for row in result["items"]
        ],
    }


def _reality_gap_get(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Inspect one missing-information item.

    BUSINESS RULE application.reality_gap_get.1:
    Route this company-scoped request to gap_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_get.1
    return gap_detail(session, tenant_id, str(arguments["gap_id"]))


def _reality_gap_simulate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Simulate a safe Fact rule without effects.

    BUSINESS RULE application.reality_gap_simulate.1:
    Route this company-scoped request to simulate_rule. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_simulate.1
    return simulate_rule(
        session,
        tenant_id,
        str(arguments["rule_id"]),
        limit=int(arguments.get("limit", 100)),
    )


def _reality_gap_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Capture missing business information.

    BUSINESS RULE application.reality_gap_create.1:
    Route this company-scoped request to capture_gap. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_create.1
    gap = capture_gap(
        session,
        tenant_id,
        **{key: value for key, value in arguments.items() if not key.startswith("_")},
    )
    return {"gap_id": gap.id, "status": gap.status, "revision": gap.revision}


def _reality_gap_entry_add(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Add investigation evidence or an answer.

    BUSINESS RULE application.reality_gap_entry_add.1:
    Route this company-scoped request to add_gap_entry. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_entry_add.1
    row = add_gap_entry(
        session,
        tenant_id,
        str(arguments["gap_id"]),
        str(arguments["entry_type"]),
        dict(arguments["payload"]),
        expected_revision=int(arguments["expected_revision"]),
    )
    return {"entry_id": row.id, "gap_id": row.gap_id}


def _reality_gap_recommend(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Prepare a modeling recommendation.

    BUSINESS RULE application.reality_gap_recommend.1:
    Route this company-scoped request to recommend_gap. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_recommend.1
    row = recommend_gap(
        session,
        tenant_id,
        str(arguments["gap_id"]),
        expected_revision=int(arguments["expected_revision"]),
    )
    return {"entry_id": row.id, "recommendation": json.loads(row.payload)}


def _reality_gap_decide(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Settle the modeling destination.

    BUSINESS RULE application.reality_gap_decide.1:
    Route this company-scoped request to decide_gap. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_decide.1
    gap = decide_gap(
        session,
        tenant_id,
        str(arguments["gap_id"]),
        destination=str(arguments["destination"]),
        rationale=str(arguments["rationale"]),
        expected_revision=int(arguments["expected_revision"]),
        actor_user_id=arguments.get("_confirming_user_id"),
    )
    return {"gap_id": gap.id, "status": gap.status, "revision": gap.revision}


def _reality_gap_prepare(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Prepare a safe rule or developer package.

    BUSINESS RULE application.reality_gap_prepare.1:
    Route this company-scoped request to prepare_implementation. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_prepare.1
    result = prepare_implementation(
        session,
        tenant_id,
        str(arguments["gap_id"]),
        arguments.get("draft"),
        expected_revision=int(arguments["expected_revision"]),
        actor_user_id=arguments.get("_confirming_user_id"),
    )
    return {
        "gap_id": str(arguments["gap_id"]),
        "implementation_id": result.id,
        "kind": "fact_rule" if hasattr(result, "logical_name") else "developer_package",
    }


def _reality_gap_activate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Activate a reviewed Fact rule.

    BUSINESS RULE application.reality_gap_activate.1:
    Route this company-scoped request to activate_rule. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_activate.1
    rule = activate_rule(session, tenant_id, str(arguments["rule_id"]))
    return {"rule_id": rule.id, "status": rule.status}


def _reality_gap_disable(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Disable a Fact rule for future sources.

    BUSINESS RULE application.reality_gap_disable.1:
    Route this company-scoped request to disable_rule. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_disable.1
    rule = disable_rule(session, tenant_id, str(arguments["rule_id"]))
    return {"rule_id": rule.id, "status": rule.status}


def _reality_gap_replay(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Replay a Fact rule over reviewed sources.

    BUSINESS RULE application.reality_gap_replay.1:
    Route this company-scoped request to replay_rule. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.reality_gap_replay.1
    return replay_rule(
        session,
        tenant_id,
        str(arguments["rule_id"]),
        source_ids=arguments.get("source_ids"),
        limit=int(arguments.get("limit", 500)),
        cursor=arguments.get("cursor"),
    )


def _discover(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Discover tenant business records and opaque IDs.

    BUSINESS RULE application.discover.1:
    IF page format is requested, use the shared paged discovery reader. ELSE use ordinary company-scoped discovery with family, query, limit and optional opaque record identity.
    """
    # reality-rule: application.discover.1
    if _read_format(arguments) == "page":
        from reality.services.read_contracts import discovery_page

        return discovery_page(session, tenant_id, arguments)
    return discover_business_records(
        session,
        tenant_id,
        str(arguments["family"]),
        query=str(arguments.get("query", "")),
        limit=arguments.get("limit", 25),
        record_id=arguments.get("record_id"),
    )


def _price_quote(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the authoritative party-aware price and its selection provenance.

    BUSINESS RULE application.price_quote.1:
    Use the supplied evaluation time or current time; retain quantity as a decimal, normalize direction and currency, and preserve the requested unit.

    BUSINESS RULE application.price_quote.2:
    Read the materialized price-resolution service for this exact partner, item and pricing context.

    BUSINESS RULE application.price_quote.3:
    Return whether a price matched together with the complete evaluation context and any returned price evidence; do not invent a fallback price.
    """
    # reality-rule: application.price_quote.1
    evaluated_at = utc_datetime(arguments.get("at")) or now()
    quantity = Decimal(str(arguments["quantity"]))
    context = {
        "party_id": str(arguments["party_id"]),
        "item_id": str(arguments["item_id"]),
        "quantity": str(quantity),
        "direction": str(arguments["direction"]).lower(),
        "currency": str(arguments["currency"]).upper(),
        "unit": str(arguments["unit"]),
        "evaluated_at": evaluated_at.isoformat(),
    }
    # reality-rule: application.price_quote.2
    result = materialized_resolve_price(
        session,
        tenant_id,
        context["party_id"],
        context["item_id"],
        quantity,
        context["direction"],
        context["currency"],
        context["unit"],
        at=evaluated_at,
    )
    # reality-rule: application.price_quote.3
    return {"matched": result is not None, **context, **(result or {})}


def _entity_result(family: str, value: Any) -> dict[str, Any]:
    values = value if isinstance(value, list) else [value]
    return {"records": [{"family": family, "id": item.id} for item in values]}


def _posting_result(entries: list[Any]) -> dict[str, Any]:
    """Ledger entries plus the posting group they share, which a reversal names."""
    result = _entity_result("ledger_entry", entries)
    groups = {entry.posting_group_id for entry in entries if entry.posting_group_id}
    if len(groups) == 1:
        result["posting_group_id"] = groups.pop()
    return result


def _manual_order(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Create one sales or purchase order.

    BUSINESS RULE application.manual_order.1:
    Route this company-scoped request to create_manual_order. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments = dict(arguments)
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.manual_order.1
    source, document, lines, commitments = create_manual_order(
        session, tenant_id, **arguments
    )
    return {
        "source_record_id": source.id,
        "document_id": document.id,
        "document_line_ids": [line.id for line in lines],
        "commitment_ids": [commitment.id for commitment in commitments],
    }


def _document_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Correct manual Document evidence.

    BUSINESS RULE application.document_correct.1:
    Route this company-scoped request to correct_manual_document. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.document_correct.1
    return _entity_result(
        "document", correct_manual_document(session, tenant_id, **arguments)
    )


def _document_source_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Append corrected immutable source evidence.

    BUSINESS RULE application.document_source_correct.1:
    Route this company-scoped request to record_corrected_document_source. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.document_source_correct.1
    source, job = record_corrected_document_source(session, tenant_id, **arguments)
    return {
        "source_record_id": source.id,
        "import_job_id": job.id,
        "status": job.status,
    }


def _document_lines_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Correct a complete manual DocumentLine snapshot.

    BUSINESS RULE application.document_lines_correct.1:
    Route this company-scoped request to correct_manual_document_lines. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.document_lines_correct.1
    return correct_manual_document_lines(session, tenant_id, **arguments)


def _handling_unit_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Create a handling unit.

    BUSINESS RULE application.handling_unit_create.1:
    Route this company-scoped request to create_handling_unit. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.handling_unit_create.1
    return _entity_result(
        "handling_unit", create_handling_unit(session, tenant_id, **arguments)
    )


def _lot_create(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Create an inventory lot.

    BUSINESS RULE application.lot_create.1:
    Route this company-scoped request to create_lot. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.lot_create.1
    return _entity_result("lot", create_lot(session, tenant_id, **arguments))


def _lot_expiry_state(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record the best-before date somebody read off the goods.

    BUSINESS RULE application.lot_expiry_state.1:
    Route this company-scoped request to state_lot_expiry. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.lot_expiry_state.1
    return _entity_result(
        "lot",
        [
            state_lot_expiry(
                session, tenant_id, arguments["lot_id"], arguments["expires_at"]
            )
        ],
    )


def _lot_expiry_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record that a stated best-before was read wrong and what it says instead.

    BUSINESS RULE application.lot_expiry_correct.1:
    Route this company-scoped request to correct_lot_expiry. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.lot_expiry_correct.1
    return _entity_result(
        "lot",
        [
            correct_lot_expiry(
                session,
                tenant_id,
                arguments["lot_id"],
                arguments.get("expires_at"),
                expected_expires_at=arguments.get("expected_expires_at"),
                reason=arguments["reason"],
            )
        ],
    )


def _expired_lots(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    List the batches whose stated best-before date has passed.

    BUSINESS RULE application.expired_lots.1:
    Route this company-scoped request to expired_lots. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.expired_lots.1
    return _entity_result("lot", expired_lots(session, tenant_id))


def _serial_unit_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Create a serialized unit.

    BUSINESS RULE application.serial_unit_create.1:
    Route this company-scoped request to create_serial_unit. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.serial_unit_create.1
    return _entity_result(
        "serial_unit", create_serial_unit(session, tenant_id, **arguments)
    )


def _movement_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record an immutable physical Movement.

    BUSINESS RULE application.movement_create.1:
    An opening-cost statement is permitted only with opening-stock movement and an action identity; retain its source before recording the movement.

    BUSINESS RULE application.movement_create.2:
    Require the shared prepayment gate before movement execution.

    BUSINESS RULE application.movement_create.3:
    Without a blocked quantity, record the movement directly through the canonical movement service.

    BUSINESS RULE application.movement_create.4:
    When blocked quantity is supplied, permit receipt only.

    BUSINESS RULE application.movement_create.5:
    Record receipt and stock block without intermediate commits, retaining identical stock tracking identities; commit both together.
    """
    arguments = dict(arguments)
    arguments["action_id"] = arguments.pop("_action_id", None)
    opening_cost = arguments.pop("opening_cost", None)
    if arguments.get("occurred_at") is not None:
        arguments["occurred_at"] = utc_datetime(arguments["occurred_at"])
    # reality-rule: application.movement_create.1
    if opening_cost is not None:
        from reality.services.opening_cost import record_opening_cost_statement

        if (
            arguments.get("movement_type") != "opening_stock"
            or not arguments["action_id"]
        ):
            raise InvalidOperation(code="movement_cost_requires_opening_stock")
        # Spec 282: the opening points to the statement of its stated cost.
        arguments["source_record_id"] = record_opening_cost_statement(
            session,
            tenant_id,
            action_id=arguments["action_id"],
            item_id=arguments["item_id"],
            quantity=str(arguments["quantity"]),
            opening_cost=opening_cost,
        ).id
    from reality.services.fulfillment_readiness import require_paid_prepayment

    # reality-rule: application.movement_create.2
    require_paid_prepayment(
        session,
        tenant_id,
        arguments.get("movement_type"),
        arguments.get("commitment_id"),
        arguments.get("quantity", "0"),
    )
    # Spec 304: a receipt may hold back part or all of what it brings in.
    blocked = arguments.pop("blocked_quantity", None)
    block_reason = arguments.pop("block_reason", None)
    # reality-rule: application.movement_create.3
    if not blocked:
        return _entity_result(
            "movement", record_movement(session, tenant_id, **arguments)
        )
    from reality.services.stock_blocks import block_stock

    # reality-rule: application.movement_create.4
    if arguments.get("movement_type") != "receipt":
        raise InvalidOperation(code="stock_block_receipt_only")
    # reality-rule: application.movement_create.5
    movement = record_movement(session, tenant_id, **arguments, _commit=False)
    block = block_stock(
        session,
        tenant_id,
        movement.item_id,
        movement.to_location_id,
        blocked,
        block_reason or "",
        handling_unit_id=movement.handling_unit_id,
        lot_id=movement.lot_id,
        serial_unit_id=movement.serial_unit_id,
        action_id=arguments.get("action_id"),
        _movement_id=movement.id,
        _receipt=movement.quantity,
        _commit=False,
    )
    session.commit()
    result = _entity_result("movement", movement)
    result["records"].append({"family": "stock_block", "id": block.id})
    return result


def _movement_explanation(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Explain why an immutable physical Movement exists from its shortest true links.

    BUSINESS RULE application.movement_explanation.1:
    Route this company-scoped request to movement_explanation. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.movement_explanations import movement_explanation

    # reality-rule: application.movement_explanation.1
    return movement_explanation(session, tenant_id, arguments["movement_id"])


def _reservation_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Release one active reservation.

    BUSINESS RULE application.reservation_release.1:
    Route this company-scoped request to release_reservation. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments = dict(arguments)
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.reservation_release.1
    return _entity_result(
        "reservation", release_reservation(session, tenant_id, **arguments)
    )


def _commitment_hold(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Hold one open commitment.

    BUSINESS RULE application.commitment_hold.1:
    Route this company-scoped request to hold_commitment. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    # reality-rule: application.commitment_hold.1
    return _entity_result(
        "commitment_hold", hold_commitment(session, tenant_id, **arguments)
    )


def _commitment_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Release commitment holds.

    BUSINESS RULE application.commitment_hold_release.1:
    Route this company-scoped request to release_commitment_hold, frozenset. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    # reality-rule: application.commitment_hold_release.1
    return _entity_result(
        "commitment_hold",
        release_commitment_hold(
            session,
            tenant_id,
            **arguments,
            _keep_reason_codes=frozenset({"credit_check"}),
        ),
    )


def _document_hold(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Hold open commitments evidenced by a document.

    BUSINESS RULE application.document_hold.1:
    Route this company-scoped request to hold_document_commitments. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.document_hold.1
    return _entity_result(
        "commitment_hold", hold_document_commitments(session, tenant_id, **arguments)
    )


def _document_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Release document commitment holds.

    BUSINESS RULE application.document_hold_release.1:
    Route this company-scoped request to release_document_holds. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.document_hold_release.1
    return _entity_result(
        "commitment_hold", release_document_holds(session, tenant_id, **arguments)
    )


def _party_hold(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Place a party delivery hold.

    BUSINESS RULE application.party_hold.1:
    Route this company-scoped request to hold_party_delivery. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    # reality-rule: application.party_hold.1
    return _entity_result(
        "party_hold", hold_party_delivery(session, tenant_id, **arguments)
    )


def _party_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Release party delivery holds.

    BUSINESS RULE application.party_hold_release.1:
    Route this company-scoped request to release_party_delivery_hold. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    # reality-rule: application.party_hold_release.1
    return _entity_result(
        "party_hold", release_party_delivery_hold(session, tenant_id, **arguments)
    )


def _lifecycle(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Activate or deactivate master data.

    BUSINESS RULE application.lifecycle.1:
    Permit party, item, location and payment-term families only; refuse unknown master-data families.

    BUSINESS RULE application.lifecycle.2:
    Apply the supplied active flag through the shared lifecycle service and return the changed record identity.
    """
    models = {
        "party": Party,
        "item": Item,
        "location": Location,
        "payment_term": PaymentTerm,
    }
    model_name = str(arguments.pop("model"))
    model = models.get(model_name)
    # reality-rule: application.lifecycle.1
    if model is None:
        raise InvalidOperation("Unsupported master data type.")
    # reality-rule: application.lifecycle.2
    return _entity_result(
        model_name, set_master_data_active(session, tenant_id, model, **arguments)
    )


def _payment_term_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Create a payment term.

    BUSINESS RULE application.payment_term_create.1:
    Route this company-scoped request to create_payment_term. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.payment_term_create.1
    return _entity_result(
        "payment_term", create_payment_term(session, tenant_id, **arguments)
    )


def _payment_term_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Update a payment term.

    BUSINESS RULE application.payment_term_update.1:
    Route this company-scoped request to update_payment_term. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.payment_term_update.1
    return _entity_result(
        "payment_term", update_payment_term(session, tenant_id, **arguments)
    )


def _price_list_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Create a price list.

    BUSINESS RULE application.price_list_create.1:
    Route this company-scoped request to create_price_list. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.price_list_create.1
    return _entity_result(
        "price_list", create_price_list(session, tenant_id, **arguments)
    )


def _price_list_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Update a price list.

    BUSINESS RULE application.price_list_update.1:
    Route this company-scoped request to update_price_list. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.price_list_update.1
    return _entity_result(
        "price_list", update_price_list(session, tenant_id, **arguments)
    )


def _price_tier_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Add a price tier.

    BUSINESS RULE application.price_tier_create.1:
    Route this company-scoped request to create_price_list_entry. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.price_tier_create.1
    return _entity_result(
        "price_list_entry", create_price_list_entry(session, tenant_id, **arguments)
    )


def _party_price_list_assign(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Assign a price list to a party.

    BUSINESS RULE application.party_price_list_assign.1:
    Route this company-scoped request to assign_party_price_list. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.party_price_list_assign.1
    return _entity_result(
        "party_price_list", assign_party_price_list(session, tenant_id, **arguments)
    )


def _party_group_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Create a pricing party group.

    BUSINESS RULE application.party_group_create.1:
    Route this company-scoped request to create_party_group. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.party_group_create.1
    return _entity_result(
        "party_group", create_party_group(session, tenant_id, **arguments)
    )


def _party_group_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Update a pricing party group.

    BUSINESS RULE application.party_group_update.1:
    Route this company-scoped request to update_party_group. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.party_group_update.1
    return _entity_result(
        "party_group", update_party_group(session, tenant_id, **arguments)
    )


def _source_record_ingest(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Store and queue one arbitrary lossless source payload.

    BUSINESS RULE application.source_record_ingest.1:
    Route this company-scoped request to enqueue_source. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.source_record_ingest.1
    source, job = enqueue_source(session, tenant_id, **arguments)
    return {
        "source_record_id": source.id,
        "import_job_id": job.id,
        "status": job.status,
    }


def _party_group_member_add(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Add a party to a pricing group.

    BUSINESS RULE application.party_group_member_add.1:
    Route this company-scoped request to add_party_group_member. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.party_group_member_add.1
    return _entity_result(
        "party_group_member", add_party_group_member(session, tenant_id, **arguments)
    )


def _group_price_list_assign(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Assign a price list to a group.

    BUSINESS RULE application.group_price_list_assign.1:
    Route this company-scoped request to assign_group_price_list. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.group_price_list_assign.1
    return _entity_result(
        "party_group_price_list",
        assign_group_price_list(session, tenant_id, **arguments),
    )


def _sales_invoice_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record stated invoice evidence and post its receivable.

    BUSINESS RULE application.sales_invoice_record.1:
    Route this company-scoped request to record_sales_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.sales_invoice_record.1
    return record_sales_invoice(session, tenant_id, **arguments)


def _supplier_invoice_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record stated supplier invoice evidence and post its payable.

    BUSINESS RULE application.supplier_invoice_record.1:
    Route this company-scoped request to record_supplier_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.supplier_invoice_record.1
    return record_supplier_invoice(session, tenant_id, **arguments)


def _supply_assign(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Assign supplier supply to customer demand or stock replenishment.

    BUSINESS RULE application.supply_assign.1:
    Route this company-scoped request to assign_supply. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    action_id = arguments.pop("_action_id", None)
    # reality-rule: application.supply_assign.1
    row = assign_supply(
        session,
        tenant_id,
        **arguments,
        request_id=action_id or uid("supply-request"),
    )
    return {"supply_assignment_id": row.id, "source_record_id": row.source_record_id}


def _supply_coverage(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Show assigned, replenishment, received, open, and unassigned supply.

    BUSINESS RULE application.supply_coverage.1:
    Route this company-scoped request to supply_coverage. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.supply_coverage.1
    return supply_coverage(session, tenant_id, **arguments)


def _return_disposition(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Resolve arrived customer-return quantity through one explicit physical outcome.

    BUSINESS RULE application.return_disposition.1:
    Route this company-scoped request to record_return_disposition. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.return_disposition.1
    row = record_return_disposition(session, tenant_id, **arguments)
    return {"movement_id": row.id, "source_record_id": row.source_record_id}


def _customer_exchange_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Settle part of a customer return with a free replacement instead of a credit.

    BUSINESS RULE application.customer_exchange_record.1:
    Route this company-scoped request to record_customer_exchange. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.customer_exchange_record.1
    exchange = record_customer_exchange(session, tenant_id, **arguments)
    return {
        "exchange_id": exchange.id,
        "replacement_commitment_id": exchange.replacement_commitment_id,
        "source_record_id": exchange.source_record_id,
    }


def _shipment_delivery_failure(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record that a customer shipment came back undeliverable, was refused or was lost, reopening its promise.

    BUSINESS RULE application.shipment_delivery_failure.1:
    Route this company-scoped request to record_delivery_failure. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.delivery_failures import (
        delivery_failure_summary,
        record_delivery_failure,
    )

    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.shipment_delivery_failure.1
    failure = record_delivery_failure(session, tenant_id, **arguments)
    claim = delivery_failure_summary(
        session, tenant_id, delivery_failure_id=failure.id
    )["claim"]
    return {
        "delivery_failure_id": failure.id,
        "shipment_id": failure.shipment_id,
        "claim_document_id": claim["document_id"] if claim else None,
        "source_record_id": failure.source_record_id,
    }


def _drop_shipment_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record that a supplier shipped an assigned purchase straight to the customer, keeping both promises.

    BUSINESS RULE application.drop_shipment_record.1:
    Route this company-scoped request to record_drop_shipment. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.drop_shipping import record_drop_shipment

    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.drop_shipment_record.1
    return record_drop_shipment(session, tenant_id, **arguments)


def _drop_shipments(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read a promise's drop shipping: the purchase assigned to it and what the supplier shipped straight to the customer.

    BUSINESS RULE application.drop_shipments.1:
    Route this company-scoped request to drop_shipments. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.drop_shipping import drop_shipments

    # reality-rule: application.drop_shipments.1
    return drop_shipments(session, tenant_id, **arguments)


def _delivery_failure_summary(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read a failed delivery: what happened, what it reversed and the carrier claim it opened.

    BUSINESS RULE application.delivery_failure_summary.1:
    Route this company-scoped request to delivery_failure_summary. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.delivery_failures import delivery_failure_summary

    # reality-rule: application.delivery_failure_summary.1
    return delivery_failure_summary(session, tenant_id, **arguments)


def _down_payment_invoice_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record and post a down-payment invoice for a sales order: a receivable against received down payments that bills no quantity.

    BUSINESS RULE application.down_payment_invoice_record.1:
    Route this company-scoped request to record_down_payment_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.down_payments import record_down_payment_invoice

    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.down_payment_invoice_record.1
    return record_down_payment_invoice(session, tenant_id, **arguments)


def _proforma_invoice_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record a pro-forma invoice for a sales order as evidence only: it posts nothing, is no open item and bills no quantity.

    BUSINESS RULE application.proforma_invoice_record.1:
    Route this company-scoped request to record_proforma_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.down_payments import record_proforma_invoice

    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.proforma_invoice_record.1
    return record_proforma_invoice(session, tenant_id, **arguments)


def _month_end_billing(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read the month-end billing lists: order lines shipped and not invoiced, and invoiced and not shipped, from the findings at one instant.

    BUSINESS RULE application.month_end_billing.1:
    Route this company-scoped request to month_end_billing. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.month_end_billing import month_end_billing

    # reality-rule: application.month_end_billing.1
    return month_end_billing(session, tenant_id, as_of=arguments.get("as_of"))


def _credit_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Release an order's credit holds with a stated reason; an owner confirms.

    BUSINESS RULE application.credit_hold_release.1:
    Route this company-scoped request to release_credit_holds. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.credit_hold_actions import release_credit_holds

    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.credit_hold_release.1
    return release_credit_holds(session, tenant_id, **arguments)


def _stock_blocks(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the stock held back by blocks, with item, location, quantity and reason.

    BUSINESS RULE application.stock_blocks.1:
    Route this company-scoped request to stock_blocks. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.stock_blocks import stock_blocks

    # reality-rule: application.stock_blocks.1
    return stock_blocks(
        session,
        tenant_id,
        item_id=arguments.get("item_id") or None,
        location_id=arguments.get("location_id") or None,
        status=arguments.get("status") or "active",
    )


def _stock_block(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Block stock where it lies with a reason; it stays put and is not available.

    BUSINESS RULE application.stock_block.1:
    Route this company-scoped request to block_stock. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.stock_blocks import block_stock

    # reality-rule: application.stock_block.1
    block = block_stock(
        session,
        tenant_id,
        arguments["item_id"],
        arguments["location_id"],
        arguments["quantity"],
        arguments["reason_code"],
        arguments.get("note", ""),
        handling_unit_id=arguments.get("handling_unit_id"),
        lot_id=arguments.get("lot_id"),
        serial_unit_id=arguments.get("serial_unit_id"),
        action_id=arguments.get("_action_id"),
    )
    return _entity_result("stock_block", block)


def _stock_block_resolve(scrap: bool) -> ToolHandler:
    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
        """
        BUSINESS PURPOSE:
        Resolve a reviewed stock block through the registered release or scrap operation.

        BUSINESS RULE application.stock_block_resolve.handler.1:
        Validate the reviewed stock-block state before resolving it.

        BUSINESS RULE application.stock_block_resolve.handler.2:
        Use scrap_stock_block when this adapter was registered for scrap; otherwise use release_stock_block.

        BUSINESS RULE application.stock_block_resolve.handler.3:
        Apply the selected shared operation to the block identity, requested quantity, reason and action identity.
        """
        from reality.services.stock_blocks import (
            check_reviewed_block,
            release_stock_block,
            scrap_stock_block,
        )

        # reality-rule: application.stock_block_resolve.handler.1
        check_reviewed_block(
            session, tenant_id, arguments["block_id"], arguments.get("reviewed")
        )
        # reality-rule: application.stock_block_resolve.handler.2
        resolve = scrap_stock_block if scrap else release_stock_block
        # reality-rule: application.stock_block_resolve.handler.3
        return resolve(
            session,
            tenant_id,
            arguments["block_id"],
            arguments.get("quantity"),
            reason=arguments["reason"],
            action_id=arguments.get("_action_id"),
        )

    return handler


def _backorders_serve(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Reserve arrived stock for waiting customer orders in the serving order: assigned first, then by due date.

    BUSINESS RULE application.backorders_serve.1:
    Route this company-scoped request to serve_backorders. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.backorders import serve_backorders

    # reality-rule: application.backorders_serve.1
    return serve_backorders(
        session,
        tenant_id,
        arguments["item_id"],
        arguments["location_id"],
        arguments["lines"],
        supplier_commitment_id=arguments.get("supplier_commitment_id") or None,
        reviewed=arguments.get("reviewed"),
        action_id=arguments.get("_action_id"),
    )


def _available_to_promise(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read from when and how much of an item can be promised: free stock now, then each open purchase with its date.

    BUSINESS RULE application.available_to_promise.1:
    Route this company-scoped request to available_to_promise. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.backorders import available_to_promise

    # reality-rule: application.available_to_promise.1
    return available_to_promise(session, tenant_id, arguments["item_id"])


def _customer_item_number_set(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    State which of our items a customer's own article number names, with the customer's name for it.

    BUSINESS RULE application.customer_item_number_set.1:
    Route this company-scoped request to set_customer_item_number. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.customer_item_numbers import (
        UNCHECKED,
        set_customer_item_number,
    )

    # reality-rule: application.customer_item_number_set.1
    row = set_customer_item_number(
        session,
        tenant_id,
        arguments["party_id"],
        arguments["item_id"],
        arguments["customer_item_number"],
        arguments.get("customer_item_name", ""),
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )
    return _entity_result("customer_item_number", row)


def _customer_item_number_remove(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Withdraw a customer's article number; lines ordered by it keep it as stated.

    BUSINESS RULE application.customer_item_number_remove.1:
    Route this company-scoped request to remove_customer_item_number. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.customer_item_numbers import (
        UNCHECKED,
        remove_customer_item_number,
    )

    # reality-rule: application.customer_item_number_remove.1
    return remove_customer_item_number(
        session,
        tenant_id,
        arguments["party_id"],
        arguments["customer_item_number"],
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )


def _company_currency_set(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    State the company currency the books are kept in; refused once the company has posted anything.

    BUSINESS RULE application.company_currency_set.1:
    Route this company-scoped request to set_company_currency. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.company_currency import (
        UNCHECKED,
        set_company_currency,
    )

    # reality-rule: application.company_currency_set.1
    return set_company_currency(
        session,
        tenant_id,
        arguments["currency"],
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )


def _company_currency(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read the company currency and whether the company has posted anything.

    BUSINESS RULE application.company_currency.1:
    Route this company-scoped request to company_currency_state. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.company_currency import company_currency_state

    # reality-rule: application.company_currency.1
    return company_currency_state(session, tenant_id)


def _supplier_item_terms_set(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    State a supplier's minimum order quantity and order multiple for an item.

    BUSINESS RULE application.supplier_item_terms_set.1:
    Route this company-scoped request to set_supplier_item_terms. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.supplier_item_terms import (
        UNCHECKED,
        set_supplier_item_terms,
    )

    # reality-rule: application.supplier_item_terms_set.1
    row = set_supplier_item_terms(
        session,
        tenant_id,
        arguments["party_id"],
        arguments["item_id"],
        arguments.get("minimum_quantity"),
        arguments.get("order_multiple"),
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )
    return _entity_result("supplier_item_terms", row)


def _supplier_item_terms_remove(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Withdraw a supplier's minimum order quantity and order multiple for an item.

    BUSINESS RULE application.supplier_item_terms_remove.1:
    Route this company-scoped request to remove_supplier_item_terms. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.supplier_item_terms import (
        UNCHECKED,
        remove_supplier_item_terms,
    )

    # reality-rule: application.supplier_item_terms_remove.1
    return remove_supplier_item_terms(
        session,
        tenant_id,
        arguments["party_id"],
        arguments["item_id"],
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )


def _supplier_item_terms(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read suppliers' minimum order quantities and order multiples.

    BUSINESS RULE application.supplier_item_terms.1:
    Route this company-scoped request to supplier_item_terms. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.supplier_item_terms import supplier_item_terms

    # reality-rule: application.supplier_item_terms.1
    return supplier_item_terms(
        session,
        tenant_id,
        party_id=arguments.get("party_id") or None,
        item_id=arguments.get("item_id") or None,
    )


def _purchase_match(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read whether each line of a purchase order is ordered = received = billed at the agreed price, or what differs.

    BUSINESS RULE application.purchase_match.1:
    Route this company-scoped request to purchase_match. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.purchase_match import purchase_match

    # reality-rule: application.purchase_match.1
    return purchase_match(session, tenant_id, arguments["document_id"])


def _customer_item_numbers(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read a customer's own article numbers for our items, or the numbers customers use for one item.

    BUSINESS RULE application.customer_item_numbers.1:
    Route this company-scoped request to customer_item_numbers. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.customer_item_numbers import customer_item_numbers

    # reality-rule: application.customer_item_numbers.1
    return customer_item_numbers(
        session,
        tenant_id,
        party_id=arguments.get("party_id") or None,
        item_id=arguments.get("item_id") or None,
    )


def _outbound_delivery_plan(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Plan an outbound delivery of one customer's open promises, with recipient, address, booked slot and staging location.

    BUSINESS RULE application.outbound_delivery_plan.1:
    Route this company-scoped request to plan_outbound_delivery. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.outbound_deliveries import plan_outbound_delivery

    values = dict(arguments)
    action_id = values.pop("_action_id", None)
    # reality-rule: application.outbound_delivery_plan.1
    delivery = plan_outbound_delivery(session, tenant_id, action_id=action_id, **values)
    return _entity_result("outbound_delivery", delivery)


def _outbound_delivery_revise(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Revise a planned delivery before it ships; every statement is kept.

    BUSINESS RULE application.outbound_delivery_revise.1:
    Route this company-scoped request to revise_outbound_delivery. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.outbound_deliveries import revise_outbound_delivery

    values = dict(arguments)
    action_id = values.pop("_action_id", None)
    # reality-rule: application.outbound_delivery_revise.1
    delivery = revise_outbound_delivery(
        session,
        tenant_id,
        values.pop("outbound_delivery_id"),
        action_id=action_id,
        **values,
    )
    return _entity_result("outbound_delivery", delivery)


def _outbound_delivery_pick(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Pick a planned delivery into its staging location; the reservation moves with the goods.

    BUSINESS RULE application.outbound_delivery_pick.1:
    Route this company-scoped request to pick_outbound_delivery. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.outbound_deliveries import pick_outbound_delivery

    # reality-rule: application.outbound_delivery_pick.1
    delivery = pick_outbound_delivery(
        session,
        tenant_id,
        arguments["outbound_delivery_id"],
        arguments["lines"],
        reviewed=arguments.get("reviewed"),
        action_id=arguments.get("_action_id"),
    )
    return _entity_result("outbound_delivery", delivery)


def _outbound_delivery_put_back(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Put picked goods back out of staging; an open promise's reservation moves back with them.

    BUSINESS RULE application.outbound_delivery_put_back.1:
    Route this company-scoped request to put_back_outbound_delivery. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.outbound_deliveries import put_back_outbound_delivery

    # reality-rule: application.outbound_delivery_put_back.1
    delivery = put_back_outbound_delivery(
        session,
        tenant_id,
        arguments["outbound_delivery_id"],
        arguments["lines"],
        reviewed=arguments.get("reviewed"),
        action_id=arguments.get("_action_id"),
    )
    return _entity_result("outbound_delivery", delivery)


def _outbound_deliveries(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read the planned deliveries, newest first, with their state and per line planned, picked, to put back and shipped.

    BUSINESS RULE application.outbound_deliveries.1:
    Route this company-scoped request to outbound_deliveries. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.outbound_deliveries import outbound_deliveries

    # reality-rule: application.outbound_deliveries.1
    return outbound_deliveries(
        session,
        tenant_id,
        customer_id=arguments.get("customer_id") or None,
        open_only=bool(arguments.get("open_only")),
    )


def _outbound_delivery_detail(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read one planned delivery: lines, picks, statements, shipment and the dispatch arguments.

    BUSINESS RULE application.outbound_delivery_detail.1:
    Route this company-scoped request to outbound_delivery_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.outbound_deliveries import outbound_delivery_detail

    # reality-rule: application.outbound_delivery_detail.1
    return outbound_delivery_detail(
        session, tenant_id, arguments["outbound_delivery_id"]
    )


def _stock_count(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Record a count of a location and post every difference as an adjustment; a loss comes off free stock first, then blocks.

    BUSINESS RULE application.stock_count.1:
    Route this company-scoped request to record_stock_count. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.stock_counts import record_stock_count

    # reality-rule: application.stock_count.1
    count = record_stock_count(
        session,
        tenant_id,
        arguments["location_id"],
        arguments["lines"],
        arguments.get("note", ""),
        reviewed=arguments.get("reviewed"),
        action_id=arguments.get("_action_id"),
    )
    return _entity_result("stock_count", count)


def _external_stock_state(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.external_stock import record_external_stock

    rows = record_external_stock(
        session,
        tenant_id,
        arguments["lines"],
        arguments.get("reporter_party_id"),
        arguments.get("note", ""),
        action_id=arguments.get("_action_id"),
    )
    return {
        "statement_ids": [row.id for row in rows],
        "source_record_id": rows[0].source_record_id if rows else None,
    }


def _external_stock(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    from reality.services.external_stock import external_stock

    return external_stock(
        session,
        tenant_id,
        item_id=arguments.get("item_id") or None,
        location_id=arguments.get("location_id") or None,
        differing_only=bool(arguments.get("differing_only")),
    )


def _stock_counts(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the counts of a location or of the company, newest first.

    BUSINESS RULE application.stock_counts.1:
    Route this company-scoped request to stock_counts. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.stock_counts import stock_counts

    # reality-rule: application.stock_counts.1
    return stock_counts(
        session, tenant_id, location_id=arguments.get("location_id") or None
    )


def _stock_count_detail(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read one count: each line as counted, the book at its counting time, and the adjustments that posted it.

    BUSINESS RULE application.stock_count_detail.1:
    Route this company-scoped request to stock_count_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.stock_counts import stock_count_detail

    # reality-rule: application.stock_count_detail.1
    return stock_count_detail(session, tenant_id, arguments["stock_count_id"])


def _delivery_rule_set(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    State how a customer or one order is delivered: partial allowed, ship complete or no backorders, with a reason.

    BUSINESS RULE application.delivery_rule_set.1:
    Route this company-scoped request to state_delivery_rule. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.delivery_rules import UNCHECKED, state_delivery_rule

    # reality-rule: application.delivery_rule_set.1
    rule = state_delivery_rule(
        session,
        tenant_id,
        arguments["rule"],
        arguments["reason"],
        party_id=arguments.get("party_id") or None,
        document_id=arguments.get("document_id") or None,
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )
    return _entity_result("delivery_rule", rule)


def _delivery_rules(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the delivery rule in force for a customer or an order, where it comes from, and every earlier statement.

    BUSINESS RULE application.delivery_rules.1:
    Route this company-scoped request to delivery_rules. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.delivery_rules import delivery_rules

    # reality-rule: application.delivery_rules.1
    return delivery_rules(
        session,
        tenant_id,
        party_id=arguments.get("party_id") or None,
        document_id=arguments.get("document_id") or None,
    )


def _reorder_points(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the reorder points of the company, of one item or of one location.

    BUSINESS RULE application.reorder_points.1:
    Route this company-scoped request to reorder_points. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.reorder_points import reorder_points

    # reality-rule: application.reorder_points.1
    return reorder_points(
        session,
        tenant_id,
        item_id=arguments.get("item_id") or None,
        location_id=arguments.get("location_id") or None,
    )


def _reorder_point_set(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Set or change the reorder point and reorder quantity of an item at a location.

    BUSINESS RULE application.reorder_point_set.1:
    Route this company-scoped request to set_reorder_point. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.reorder_points import UNCHECKED, set_reorder_point

    # reality-rule: application.reorder_point_set.1
    point = set_reorder_point(
        session,
        tenant_id,
        arguments["item_id"],
        arguments["location_id"],
        arguments["reorder_point"],
        arguments["reorder_quantity"],
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )
    return _entity_result("reorder_point", point)


def _reorder_point_remove(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Remove the reorder point of an item at a location.

    BUSINESS RULE application.reorder_point_remove.1:
    Route this company-scoped request to remove_reorder_point. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.reorder_points import UNCHECKED, remove_reorder_point

    # reality-rule: application.reorder_point_remove.1
    return remove_reorder_point(
        session,
        tenant_id,
        arguments["item_id"],
        arguments["location_id"],
        action_id=arguments.get("_action_id"),
        _expected=arguments.get("reviewed", UNCHECKED),
    )


def _kits(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the kits of the company, or of one item, with their components and what each location can build.

    BUSINESS RULE application.kits.1:
    Route this company-scoped request to kits. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.kits import kits

    # reality-rule: application.kits.1
    return kits(session, tenant_id, item_id=arguments.get("item_id") or None)


def _kit_split(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read how a kit's order or invoice line splits its stated net, tax and gross across the components.

    BUSINESS RULE application.kit_split.1:
    Route this company-scoped request to kit_split. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.kits import kit_split

    # reality-rule: application.kit_split.1
    return kit_split(session, tenant_id, str(arguments.get("document_line_id") or ""))


def _kit_define(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    State the components of a kit: each component item, how many one kit takes and optionally its share of the price.

    BUSINESS RULE application.kit_define.1:
    Route this company-scoped request to define_kit. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.kits import define_kit

    # reality-rule: application.kit_define.1
    components = define_kit(
        session,
        tenant_id,
        arguments["kit_item_id"],
        arguments["components"],
        action_id=arguments.get("_action_id"),
    )
    return {
        "kit_item_id": arguments["kit_item_id"],
        "component_ids": [component.id for component in components],
        "source_record_id": components[0].source_record_id,
    }


def _kit_assemble(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Assemble kits at a location: consume the components and produce the kits, all or nothing.

    BUSINESS RULE application.kit_assemble.1:
    Route this company-scoped request to assemble_kit. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.kits import assemble_kit

    # reality-rule: application.kit_assemble.1
    return assemble_kit(
        session,
        tenant_id,
        arguments["kit_item_id"],
        arguments["location_id"],
        arguments["quantity"],
        occurred_at=arguments.get("occurred_at"),
        note=arguments.get("note"),
        action_id=arguments.get("_action_id"),
    )


def _party_merge(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Merge a duplicate business partner into the one that survives, with a reason; both histories stay as stated.

    BUSINESS RULE application.party_merge.1:
    Route this company-scoped request to merge_party. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.party_merges import merge_party

    # reality-rule: application.party_merge.1
    merge = merge_party(
        session,
        tenant_id,
        arguments["duplicate_party_id"],
        arguments["surviving_party_id"],
        arguments["reason"],
        action_id=arguments.get("_action_id"),
    )
    return {
        "merge_id": merge.id,
        "duplicate_party_id": merge.duplicate_party_id,
        "surviving_party_id": merge.surviving_party_id,
        "source_record_id": merge.source_record_id,
    }


def _party_merges(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Read the business partner merges, or those one partner took part in.

    BUSINESS RULE application.party_merges.1:
    Route this company-scoped request to party_merges. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.party_merges import party_merges

    # reality-rule: application.party_merges.1
    return party_merges(session, tenant_id, party_id=arguments.get("party_id") or None)


def _commitment_substitute_accept(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Accept another item in place of what a purchase line ordered, with a reason; receipts of it then fulfil the line.

    BUSINESS RULE application.commitment_substitute_accept.1:
    Route this company-scoped request to accept_substitute. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.receipt_deviations import accept_substitute

    # reality-rule: application.commitment_substitute_accept.1
    row = accept_substitute(
        session,
        tenant_id,
        arguments["commitment_id"],
        arguments["item_id"],
        arguments["reason"],
        action_id=arguments.get("_action_id"),
    )
    return {
        "substitute_id": row.id,
        "commitment_id": row.commitment_id,
        "item_id": row.item_id,
        "source_record_id": row.source_record_id,
    }


def _order_line_item_assign(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Give an order line whose stated SKU matched no item its item and create its delivery promise.

    BUSINESS RULE application.order_line_item_assign.1:
    Route this company-scoped request to assign_line_item. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.order_line_items import assign_line_item

    arguments["action_id"] = arguments.pop("_action_id", None)
    arguments["remember_for_customer"] = bool(arguments.get("remember_for_customer"))
    # reality-rule: application.order_line_item_assign.1
    result = assign_line_item(session, tenant_id, **arguments)
    return {
        "document_line_id": result["document_line_id"],
        "item_id": result["item_id"],
        "commitment_id": result["commitment_id"],
    }


def _customer_exchange(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read what a customer exchange replaced, what it sent and what it still settles.

    BUSINESS RULE application.customer_exchange.1:
    Route this company-scoped request to customer_exchange_detail. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.customer_exchanges import customer_exchange_detail

    # reality-rule: application.customer_exchange.1
    return customer_exchange_detail(session, tenant_id, **arguments)


def _return_disposition_summary(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read arrived, resolved and unresolved customer-return quantity by disposition.

    BUSINESS RULE application.return_disposition_summary.1:
    Route this company-scoped request to return_disposition_case. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.delivery_reads import return_disposition_case

    # reality-rule: application.return_disposition_summary.1
    return return_disposition_case(session, tenant_id, **arguments)


def _sales_credit_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record an invoice-linked customer credit with explicit netting, or a legacy return credit; no refund or stock movement.

    BUSINESS RULE application.sales_credit_record.1:
    Route this company-scoped request to record_sales_credit. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.sales_credit_record.1
    return record_sales_credit(session, tenant_id, **arguments)


def _invoice_credit_context(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read eligible invoice positions and remaining customer-credit capacity.

    BUSINESS RULE application.invoice_credit_context.1:
    Route this company-scoped request to invoice_credit_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.credit_actions import invoice_credit_context

    # reality-rule: application.invoice_credit_context.1
    return invoice_credit_context(session, tenant_id, arguments["invoice_id"])


def _invoice_billable_positions(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read a party's delivered or received order positions not yet fully billed, grouped by order.

    BUSINESS RULE application.invoice_billable_positions.1:
    Route this company-scoped request to billable_positions. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.invoice_billing import billable_positions

    # reality-rule: application.invoice_billable_positions.1
    return billable_positions(session, tenant_id, **arguments)


def _supplier_invoice_free_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record source-stated supplier invoice evidence and its payable without an order.

    BUSINESS RULE application.supplier_invoice_free_record.1:
    Route this company-scoped request to record_free_supplier_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.invoice_actions import record_free_supplier_invoice

    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.supplier_invoice_free_record.1
    return record_free_supplier_invoice(session, tenant_id, **arguments)


def _payment(kind: str) -> ToolHandler:
    service = post_customer_payment if kind == "customer" else post_supplier_payment

    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
        """
        BUSINESS PURPOSE:
        Apply the customer or supplier payment service selected by this registered adapter.

        BUSINESS RULE application.payment.handler.1:
        Normalize a supplied effective time to UTC before routing.

        BUSINESS RULE application.payment.handler.2:
        Delegate invoice-payment recording and allocation to the captured customer/supplier payment service and return ledger-entry identities.
        """
        arguments["action_id"] = arguments.pop("_action_id", None)
        # reality-rule: application.payment.handler.1
        if arguments.get("effective_at") is not None:
            arguments["effective_at"] = utc_datetime(arguments["effective_at"])
        # reality-rule: application.payment.handler.2
        return _entity_result("ledger_entry", service(session, tenant_id, **arguments))

    return handler


def _return_announce(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record that a customer says goods are coming back.

    BUSINESS RULE application.return_announce.1:
    Route this company-scoped request to announce_customer_return. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.return_announce.1
    return announce_customer_return(
        session,
        tenant_id,
        arguments["commitment_id"],
        arguments["quantity"],
        reference=arguments.get("reference", "") or "",
        reason=arguments.get("reason", "") or "",
        expected_by=arguments.get("expected_by"),
    )


def _return_announcement_withdraw(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record that a customer is not sending announced goods back after all.

    BUSINESS RULE application.return_announcement_withdraw.1:
    Route this company-scoped request to withdraw_return_announcement. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.return_announcement_withdraw.1
    return withdraw_return_announcement(
        session,
        tenant_id,
        arguments["announcement_id"],
        note=arguments.get("note", "") or "",
    )


def _return_announcements(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    List the returns customers have announced and what is still expected.

    BUSINESS RULE application.return_announcements.1:
    Route this company-scoped request to return_announcements. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.return_announcements.1
    return _entity_result(
        "return_announcement",
        return_announcements(
            session,
            tenant_id,
            commitment_id=arguments.get("commitment_id"),
            status=arguments.get("status"),
        ),
    )


def _payment_run_preview(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Show which supplier invoices are worth paying now.

    BUSINESS RULE application.payment_run_preview.1:
    Route this company-scoped request to preview_payment_run. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.payment_run_preview.1
    return preview_payment_run(
        session, tenant_id, pay_by=utc_datetime(arguments["pay_by"])
    )


def _payment_run(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Pay the supplier invoices and amounts somebody confirmed, in one transaction.

    BUSINESS RULE application.payment_run.1:
    Route this company-scoped request to execute_payment_run. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    # reality-rule: application.payment_run.1
    return execute_payment_run(
        session,
        tenant_id,
        payments=list(arguments["payments"]),
        currency=arguments["currency"],
        expected_total=arguments["expected_total"],
        reason=arguments["reason"],
        action_id=arguments["action_id"],
    )


def _stale_closure_preview(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Show which stale promises a closure would close.

    BUSINESS RULE application.stale_closure_preview.1:
    Route this company-scoped request to preview_stale_promise_closure. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.stale_closure_preview.1
    return preview_stale_promise_closure(
        session,
        tenant_id,
        direction=arguments["direction"],
        due_before=utc_datetime(arguments["due_before"]),
    )


def _stale_closure(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    """
    BUSINESS PURPOSE:
    Close stale promises somebody previewed and counted.

    BUSINESS RULE application.stale_closure.1:
    Route this company-scoped request to close_stale_promises. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.stale_closure.1
    return close_stale_promises(
        session,
        tenant_id,
        direction=arguments["direction"],
        due_before=utc_datetime(arguments["due_before"]),
        expected_count=int(arguments["expected_count"]),
        reason=arguments["reason"],
    )


def _sales_invoice_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Book a recorded sales invoice into the ledger.

    BUSINESS RULE application.sales_invoice_post.1:
    Route this company-scoped request to post_sales_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.sales_invoice_post.1
    return _posting_result(post_sales_invoice(session, tenant_id, **arguments))


def _supplier_invoice_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Book a recorded supplier invoice into the ledger.

    BUSINESS RULE application.supplier_invoice_post.1:
    Route this company-scoped request to post_supplier_invoice. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.supplier_invoice_post.1
    return _posting_result(post_supplier_invoice(session, tenant_id, **arguments))


def _document_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record manual document evidence with its normalized lines.

    BUSINESS RULE application.document_create.1:
    Route this company-scoped request to create_manual_document_with_lines. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.document_create.1
    document, lines = create_manual_document_with_lines(session, tenant_id, **arguments)
    # The same shape the manual order returns: flat identities, no business
    # fields restated.
    return {
        "document_id": document.id,
        "document_line_ids": [line.id for line in lines],
        "status": document.status,
    }


def _credit_note_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Post a credit note as the reverse of a sales invoice.

    BUSINESS RULE application.credit_note_post.1:
    Route this company-scoped request to post_sales_credit_note. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.credit_note_post.1
    return _posting_result(post_sales_credit_note(session, tenant_id, **arguments))


def _credit_note_allocate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Net a posted credit note against an open invoice.

    BUSINESS RULE application.credit_note_allocate.1:
    Route this company-scoped request to allocate_credit_note. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.credit_note_allocate.1
    return _entity_result(
        "settlement_allocation", allocate_credit_note(session, tenant_id, **arguments)
    )


def _customer_refund_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record an actual customer refund and allocate it to an open credit note. Partial refunds are supported; this does not initiate a bank transfer.

    BUSINESS RULE application.customer_refund_post.1:
    Route this company-scoped request to post_customer_refund. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.customer_refund_post.1
    return _entity_result(
        "ledger_entry", post_customer_refund(session, tenant_id, **arguments)
    )


def _supplier_credit_note_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Book a supplier credit note as the reverse of its invoice.

    BUSINESS RULE application.supplier_credit_note_post.1:
    Route this company-scoped request to post_supplier_credit_note. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.supplier_credit_note_post.1
    return _posting_result(post_supplier_credit_note(session, tenant_id, **arguments))


def _supplier_credit_note_allocate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Net a booked supplier credit against an open supplier invoice.

    BUSINESS RULE application.supplier_credit_note_allocate.1:
    Route this company-scoped request to allocate_supplier_credit_note. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.supplier_credit_note_allocate.1
    return _entity_result(
        "settlement_allocation",
        allocate_supplier_credit_note(session, tenant_id, **arguments),
    )


def _supplier_refund_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Take money back from a supplier and settle the credit note.

    BUSINESS RULE application.supplier_refund_post.1:
    Route this company-scoped request to post_supplier_refund. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    # reality-rule: application.supplier_refund_post.1
    return _entity_result(
        "ledger_entry", post_supplier_refund(session, tenant_id, **arguments)
    )


def _commitment_revise(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Record that a counterparty now states a different date, quantity or, for a purchase, unit price.

    BUSINESS RULE application.commitment_revise.1:
    Route this company-scoped request to revise_commitment. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    arguments["action_id"] = arguments.pop("_action_id", None)
    for field in ("due_at", "stated_at"):
        if arguments.get(field) is not None:
            arguments[field] = utc_datetime(arguments[field])
    # reality-rule: application.commitment_revise.1
    return _entity_result(
        "commitment_revision", revise_commitment(session, tenant_id, **arguments)
    )


def _commitment_cancel(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Cancel the open remainder of one commitment for an explicit reason.

    BUSINESS RULE application.commitment_cancel.1:
    Route this company-scoped request to cancel_commitment. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.db.core import BusinessEvent
    from reality.services.core import cancel_commitment

    action_id = arguments.pop("_action_id", None)
    # reality-rule: application.commitment_cancel.1
    commitment = cancel_commitment(session, tenant_id, action_id=action_id, **arguments)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.action_id == action_id,
            BusinessEvent.event_type == "commitment.cancelled",
            BusinessEvent.subject_id == commitment.id,
        )
    )
    return {"commitment_id": commitment.id, "event_id": event.id if event else None}


def _source_system_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Define a source system.

    BUSINESS RULE application.source_system_create.1:
    Route this company-scoped request to create_source_system. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.source_system_create.1
    return _entity_result(
        "source_system", create_source_system(session, tenant_id, **arguments)
    )


def _connector_install(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Install a credential-free connector shell.

    BUSINESS RULE application.connector_install.1:
    Route this company-scoped request to install_connector_shell. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.connector_install.1
    return _entity_result(
        "source_system", install_connector_shell(session, tenant_id, **arguments)
    )


def _source_system_lifecycle(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Activate or deactivate a source system.

    BUSINESS RULE application.source_system_lifecycle.1:
    Route this company-scoped request to set_source_system_active. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.source_system_lifecycle.1
    return _entity_result(
        "source_system", set_source_system_active(session, tenant_id, **arguments)
    )


def _source_capability_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Define a source capability.

    BUSINESS RULE application.source_capability_create.1:
    Route this company-scoped request to create_source_capability. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.source_capability_create.1
    return _entity_result(
        "source_capability", create_source_capability(session, tenant_id, **arguments)
    )


def _source_capability_lifecycle(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Activate or deactivate a source capability.

    BUSINESS RULE application.source_capability_lifecycle.1:
    Route this company-scoped request to set_source_capability_active. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    # reality-rule: application.source_capability_lifecycle.1
    return _entity_result(
        "source_capability",
        set_source_capability_active(session, tenant_id, **arguments),
    )


def _capability_describe(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Describe the safe use and verification path of one public agent capability.

    BUSINESS RULE application.capability_describe.1:
    Resolve the exact public tool name or an unambiguous registered application-tool mapping; refuse ambiguous identities rather than guessing.

    BUSINESS RULE application.capability_describe.2:
    Read guidance for the resolved canonical public name.

    BUSINESS RULE application.capability_describe.3:
    When registered guidance is absent but a tool is registered, return its actual registry description, schema, access kind and confirmation requirement.

    BUSINESS RULE application.capability_describe.4:
    Refuse an unknown capability instead of returning invented guidance.
    """
    del session, tenant_id
    from reality.catalogs import runtime_application_catalog_section

    requested_name = str(arguments.get("tool_name", "")).strip()
    catalog = runtime_application_catalog_section("capability_guidance")
    canonical_name = requested_name if requested_name in catalog else ""
    # reality-rule: application.capability_describe.1
    if not canonical_name:
        candidates = [
            name
            for name, entry in catalog.items()
            if entry.get("application_tool") == requested_name
        ]
        if len(candidates) > 1:
            raise InvalidOperation(
                "Capability identity is ambiguous; use one canonical public name: "
                + ", ".join(sorted(candidates))
            )
        if candidates:
            canonical_name = candidates[0]
    if not canonical_name:
        from reality.mcp.catalog import MCP_TOOL_REGISTRY

        if requested_name in MCP_TOOL_REGISTRY:
            canonical_name = requested_name
        else:
            candidates = [
                name
                for name, definition in MCP_TOOL_REGISTRY.items()
                if getattr(definition.handler, "application_name", name)
                == requested_name
            ]
            if len(candidates) > 1:
                raise InvalidOperation(
                    "Capability identity is ambiguous; use one canonical public name: "
                    + ", ".join(sorted(candidates))
                )
            if candidates:
                canonical_name = candidates[0]
    # reality-rule: application.capability_describe.2
    guidance = catalog.get(canonical_name)
    # reality-rule: application.capability_describe.3
    if guidance is None and canonical_name:
        from reality.mcp.catalog import MCP_TOOL_REGISTRY

        definition = MCP_TOOL_REGISTRY[canonical_name]
        application_name = getattr(
            definition.handler, "application_name", canonical_name
        )
        return {
            "canonical_public_name": canonical_name,
            "tool_name": canonical_name,
            "application_tool": application_name,
            "kind": "proposal" if definition.access == "propose" else definition.access,
            "purpose": definition.description,
            "input_schema": definition.input_schema,
            "confirmation": "required"
            if definition.access in {"propose", "confirm"}
            else "not_required",
        }
    # reality-rule: application.capability_describe.4
    if guidance is None:
        raise NotFound("Capability not found.")
    return {"canonical_public_name": canonical_name, **guidance}


def _capability_catalog(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    Answer the topic index, or one topic's capabilities (spec 270).

    BUSINESS PURPOSE:
    Discover the business areas this Reality covers and which of them this credential may use.

    BUSINESS RULE application.capability_catalog.1:
    IF no topic was supplied, return the topic index. ELSE read the capabilities of the selected topic.
    """
    from reality.services.capability_catalog import topic_capabilities, topic_index

    topic = str(arguments.get("topic") or "").strip()
    # reality-rule: application.capability_catalog.1
    if not topic:
        return topic_index(session, tenant_id)
    return topic_capabilities(session, tenant_id, topic)


def _proposals_awaiting_approval(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    BUSINESS PURPOSE:
    Read tenant proposals that still require approval.

    BUSINESS RULE application.proposals_awaiting_approval.1:
    Route this company-scoped request to proposals_awaiting_approval. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    del arguments
    # reality-rule: application.proposals_awaiting_approval.1
    return [
        {
            "proposal_id": proposal.id,
            "tool": proposal.type.removeprefix("tool:"),
            "arguments": json.loads(proposal.input),
            "created_at": proposal.created_at.isoformat(),
            "status": proposal.status,
        }
        for proposal in proposals_awaiting_approval(session, tenant_id)
    ]


def _opening_statement_of(
    session: Session, tenant_id: str, movement: Movement, proposal: ChangeProposal
) -> bool:
    from reality.services.opening_cost import is_statement_of

    return is_statement_of(session, tenant_id, movement.source_record_id, proposal.id)


def _opening_movement_evidence(
    session: Session, tenant_id: str, proposal: ChangeProposal
) -> dict | None:
    """Verify one opening Movement against exact action evidence, not elapsed time."""
    expected = json.loads(proposal.input)
    if expected.get("movement_type") != "opening_stock":
        return None
    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == "movement.recorded",
                BusinessEvent.subject_type == "movement",
            )
            .limit(2)
        )
    )
    if len(events) != 1:
        return None
    event = events[0]
    movement = session.scalar(
        select(Movement).where(
            Movement.tenant_id == tenant_id, Movement.id == event.subject_id
        )
    )
    if movement is None or (
        movement.type != "opening_stock"
        or movement.item_id != expected.get("item_id")
        or movement.to_location_id != expected.get("to_location_id")
        or movement.quantity != Decimal(str(expected.get("quantity")))
        or movement.from_location_id is not None
        or movement.commitment_id is not None
        or (
            movement.source_record_id is not None
            and not _opening_statement_of(session, tenant_id, movement, proposal)
        )
        or movement.handling_unit_id is not None
        or movement.lot_id is not None
        or movement.serial_unit_id is not None
        or (
            expected.get("occurred_at") is not None
            and movement.occurred_at != utc_datetime(expected["occurred_at"])
        )
    ):
        return None
    if proposal.status == "executed" and json.loads(proposal.output).get("records") != [
        {"family": "movement", "id": movement.id}
    ]:
        return None
    return {
        "event_id": event.id,
        "event_sequence": event.sequence,
        "movement_id": movement.id,
    }


def _proposal_execution_status(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """
    The receipt and reconciliation of one proposal, with who settled it.

    BUSINESS PURPOSE:
    Reconcile one proposal with its stored receipt and authoritative Reality records.

    BUSINESS RULE application.proposal_execution_status.1:
    Route this company-scoped request to _proposal_execution_receipt. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.decision_attribution import decision_attributions

    # reality-rule: application.proposal_execution_status.1
    status = _proposal_execution_receipt(session, tenant_id, arguments)
    return {
        **status,
        "decision": decision_attributions(
            session, tenant_id, [status["proposal_id"]]
        ).get(status["proposal_id"]),
    }


def _proposal_execution_receipt(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == arguments["proposal_id"],
        )
    )
    if proposal is None:
        raise NotFound("Proposal not found.")
    if proposal.status == "failed":
        failure = json.loads(proposal.output)
        return {
            "proposal_id": proposal.id,
            "status": proposal.status,
            "capability": proposal.type.removeprefix("tool:"),
            "receipt": None,
            "verification": {
                "execution": "failed",
                "operational_state": "no_effect",
                "business_outcome": "not_proven",
            },
            "failure": failure,
        }
    if (
        "_delivery_review" in json.loads(proposal.input)
        and proposal.type != "tool:reserve"
    ):
        from reality.services.delivery_actions import delivery_proposal_detail

        detail = delivery_proposal_detail(session, tenant_id, proposal.id)
        return {
            "proposal_id": proposal.id,
            "status": proposal.status,
            "capability": proposal.type.removeprefix("tool:"),
            "receipt": detail["receipt"],
            "verification": {
                "execution": "recorded"
                if proposal.status == "executed"
                else detail["verification"],
                "operational_state": detail["verification"],
                "business_outcome": "not_proven",
            },
            "reconciliation_evidence": detail["links"],
            "observation": detail.get("observation"),
            "observation_error": detail.get("observation_error"),
        }
    tool_name = proposal.type.removeprefix("tool:")
    result: dict[str, Any] = {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "capability": tool_name,
        "receipt": json.loads(proposal.output)
        if proposal.status == "executed"
        else None,
        "verification": {
            "execution": "pending" if proposal.status == "proposed" else "unknown",
            "operational_state": "not_checked",
            "business_outcome": "not_proven",
        },
    }
    if (
        tool_name == "movement_create"
        and proposal.status in {"executing", "executed"}
        and json.loads(proposal.input).get("movement_type") == "opening_stock"
    ):
        evidence = _opening_movement_evidence(session, tenant_id, proposal)
        result["verification"]["execution"] = (
            "recorded" if proposal.status == "executed" else "unknown"
        )
        if evidence:
            result["reconciliation_evidence"] = evidence
            result["verification"]["operational_state"] = "verified"
            if proposal.status == "executing":
                result["verification"]["execution"] = (
                    "effect_observed_proposal_unsettled"
                )
        else:
            result["verification"]["operational_state"] = "unresolved"
        return result
    if proposal.status == "executing" and tool_name == "reserve":
        event = session.scalar(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == "reservation.created",
                BusinessEvent.subject_type == "reservation",
            )
            .order_by(BusinessEvent.sequence)
        )
        reservation = (
            session.scalar(
                select(Reservation).where(
                    Reservation.tenant_id == tenant_id,
                    Reservation.id == event.subject_id,
                )
            )
            if event
            else None
        )
        expected_commitment_id = json.loads(proposal.input).get("commitment_id")
        if event and reservation:
            result["reconciliation_evidence"] = {
                "event_id": event.id,
                "reservation_id": reservation.id,
                "commitment_id": reservation.commitment_id,
                "applied": json.loads(event.payload)["quantity"],
            }
            matches = reservation.commitment_id == expected_commitment_id
            result["verification"] = {
                "execution": "effect_observed_proposal_unsettled",
                "operational_state": "verified" if matches else "unresolved",
                "business_outcome": "not_proven",
            }
        return result
    if proposal.status != "executed" or tool_name != "reserve":
        if proposal.status == "executed":
            result["verification"]["execution"] = "recorded"
        return result

    receipt = result["receipt"]
    proposal_input = json.loads(proposal.input)
    reservation_id = receipt.get("reservation_id")
    event_id = receipt.get("event_id")
    reservation = (
        session.scalar(
            select(Reservation).where(
                Reservation.tenant_id == tenant_id,
                Reservation.id == reservation_id,
            )
        )
        if reservation_id
        else None
    )
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.id == receipt.get("commitment_id"),
        )
    )
    event = (
        session.scalar(
            select(BusinessEvent).where(
                BusinessEvent.tenant_id == tenant_id,
                BusinessEvent.id == event_id,
                BusinessEvent.action_id == proposal.id,
                BusinessEvent.event_type == "reservation.created",
                BusinessEvent.subject_type == "reservation",
                BusinessEvent.subject_id == reservation_id,
            )
        )
        if event_id and reservation_id
        else None
    )
    applied = Decimal(str(receipt.get("applied", "0")))
    checks = {
        "proposal_matches": receipt.get("proposal_id") == proposal.id,
        "capability_matches": receipt.get("capability") == "reserve",
        "commitment_matches": (
            commitment is not None
            and receipt.get("commitment_id") == proposal_input.get("commitment_id")
        ),
        "reservation_matches": (
            (applied == 0 and reservation is None)
            or (
                reservation is not None
                and reservation.commitment_id == receipt.get("commitment_id")
                and event is not None
                and Decimal(str(json.loads(event.payload).get("quantity", "-1")))
                == applied
            )
        ),
        "event_matches": (applied == 0 and event_id is None) or event is not None,
    }
    verified = all(checks.values())
    result["verification"] = {
        "execution": "verified" if verified else "unresolved",
        "operational_state": "verified" if verified else "unresolved",
        "business_outcome": "not_proven",
        "checks": checks,
    }
    return result


from reality.tools.business_journeys import (
    business_journey_guide as _business_journey_guide,
)
from reality.tools.business_journeys import (
    business_journey_proposal_create as _business_journey_proposal_create,
)
from reality.tools.business_journeys import (
    business_journey_vote_set as _business_journey_vote_set,
)


def _business_logic_discover(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Discover actual registered business logic and live source availability.

    BUSINESS RULE application.business_logic_discover.1:
    Validate discovery arguments with the registered input model and read the shared runtime business catalog. This generic source catalog does not query company business records.
    """
    from reality.domain.business_blueprints import DiscoveryInput
    from reality.services.business_blueprints import discover

    # reality-rule: application.business_logic_discover.1
    return discover(**DiscoveryInput.model_validate(arguments).model_dump())


def _business_logic_explain(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Explain actual running business source, decisions and executable test cases.

    BUSINESS RULE application.business_logic_explain.1:
    Accept only kind, key and language inputs; refuse extra explanation inputs.

    BUSINESS RULE application.business_logic_explain.2:
    Read the verified live business explanation service and serialize its actual result; this adapter does not create its own narrative.
    """
    from reality.services.business_blueprints import explain

    # reality-rule: application.business_logic_explain.1
    if set(arguments) - {"kind", "key", "language"}:
        raise ValueError("Unknown explanation input")
    # reality-rule: application.business_logic_explain.2
    return explain(**arguments).model_dump(mode="json")


def _business_logic_source(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Inspect approved source evidence from the running business implementation.

    BUSINESS RULE application.business_logic_source.1:
    Read the exact approved source evidence requested through the shared source reader. This generic code inspection does not query company business records or execute the business function.
    """
    from reality.services.business_blueprints import source_for

    # reality-rule: application.business_logic_source.1
    return source_for(**arguments)


def _business_logic_compare(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Compare supplied or authorized conditions with actual tested cases without executing a mutation.

    BUSINESS RULE application.business_logic_compare.1:
    Route this company-scoped request to compare. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.business_blueprints import compare

    # reality-rule: application.business_logic_compare.1
    return compare(session, tenant_id, arguments)


TOOLS = {
    "business_logic_discover": Tool(
        "business_logic_discover",
        "Discover actual registered business logic and live source availability.",
        False,
        _business_logic_discover,
    ),
    "business_logic_explain": Tool(
        "business_logic_explain",
        "Explain actual running business source, decisions and executable test cases.",
        False,
        _business_logic_explain,
    ),
    "business_logic_source": Tool(
        "business_logic_source",
        "Inspect approved source evidence from the running business implementation.",
        False,
        _business_logic_source,
    ),
    "business_logic_compare": Tool(
        "business_logic_compare",
        "Compare supplied or authorized conditions with actual tested cases without executing a mutation.",
        False,
        _business_logic_compare,
    ),
    "business_journey_guide": Tool(
        "business_journey_guide",
        "Ask what Reality supports and receive cited Business Journey Guide evidence.",
        False,
        _business_journey_guide,
    ),
    "business_journey_proposal_create": Tool(
        "business_journey_proposal_create",
        "Create a reviewed Business Journey suggestion for the confirming account.",
        True,
        _business_journey_proposal_create,
    ),
    "business_journey_vote_set": Tool(
        "business_journey_vote_set",
        "Set or withdraw the confirming account's vote for a Business Journey suggestion.",
        True,
        _business_journey_vote_set,
    ),
    "capability_describe": Tool(
        "capability_describe",
        "Describe the safe use and verification path of one public agent capability.",
        False,
        _capability_describe,
    ),
    "capability_catalog": Tool(
        "capability_catalog",
        "Discover the business areas this Reality covers and which of them this credential may use.",
        False,
        _capability_catalog,
    ),
    "proposals_awaiting_approval": Tool(
        "proposals_awaiting_approval",
        "Read tenant proposals that still require approval.",
        False,
        _proposals_awaiting_approval,
    ),
    "proposal_execution_status": Tool(
        "proposal_execution_status",
        "Reconcile one proposal with its stored receipt and authoritative Reality records.",
        False,
        _proposal_execution_status,
    ),
    "interpretation_coverage": Tool(
        "interpretation_coverage",
        "Read explicit source interpretation outcomes without raw payloads.",
        False,
        _interpretation_coverage,
    ),
    "business_discover": Tool(
        "business_discover",
        "Discover tenant business records and opaque IDs.",
        False,
        _discover,
    ),
    "price_quote": Tool(
        "price_quote",
        "Read the authoritative party-aware price and its selection provenance.",
        False,
        _price_quote,
    ),
    "inventory": Tool("inventory", "Read derived inventory.", False, _inventory),
    "exceptions": Tool(
        "exceptions", "Read derived operational exceptions.", False, _exceptions
    ),
    "exception_explain": Tool(
        "exception_explain",
        "Explain one current operational exception.",
        False,
        _exception_explain,
    ),
    "commitments": Tool(
        "commitments", "Read operational obligations.", False, _commitments
    ),
    "finance_balances": Tool(
        "finance_balances",
        "Read balances derived from the journal.",
        False,
        _finance_balances,
    ),
    "finance.dunning.context": Tool(
        "finance.dunning.context",
        "Preview one manual dunning notice and return its finance revision.",
        False,
        _dunning_context,
    ),
    "finance.dunning.notices": Tool(
        "finance.dunning.notices",
        "List manual dunning notices with fee and reversal trace.",
        False,
        _dunning_notices,
    ),
    "finance.dunning.notice": Tool(
        "finance.dunning.notice",
        "Read one manual dunning notice with fee and reversal trace.",
        False,
        _dunning_notice,
    ),
    "finance.dunning.schedule": Tool(
        "finance.dunning.schedule",
        "Read the company dunning schedule: waiting days and fixed fee per level.",
        False,
        _dunning_schedule,
    ),
    "credit_exposure": Tool(
        "credit_exposure",
        "Read a customer's credit exposure: open invoices plus open uninvoiced orders minus available credits against the limit, with overdue invoices and payables named.",
        False,
        _credit_exposure,
    ),
    "finance.payment_returns": Tool(
        "finance.payment_returns",
        "List returned customer payments (returned direct debits and chargebacks) with their reason, fee and reopened invoices.",
        False,
        _payment_returns,
    ),
    "finance.payment_return": Tool(
        "finance.payment_return",
        "Read one returned customer payment with its reason, reference, fee and reopened invoices.",
        False,
        _payment_return,
    ),
    "finance.payouts": Tool(
        "finance.payouts",
        "List marketplace and payment-provider payouts with their net amount and the lines nothing booked yet.",
        False,
        _payouts,
    ),
    "finance.payout": Tool(
        "finance.payout",
        "Read one payout: every stated line with what it booked (payment, refund, chargeback, fee), the invoices it settled, the shipment a tracking number names, or why it stays unbooked.",
        False,
        _payout,
    ),
    "finance.payment_authorizations": Tool(
        "finance.payment_authorizations",
        "List card and wallet payment authorizations, optionally for one order, with what was captured, what is left and whether each is live, expired or captured.",
        False,
        _payment_authorizations,
    ),
    "finance.dunning.run_context": Tool(
        "finance.dunning.run_context",
        "Preview a dunning run: overdue items per customer, currency and level, items ready for collection and items left out with their reason.",
        False,
        _dunning_run_context,
    ),
    "finance.dunning.collection_handovers": Tool(
        "finance.dunning.collection_handovers",
        "List collection handovers with their invoices and delivery hold.",
        False,
        _collection_handovers,
    ),
    "finance.dunning.collection_handover": Tool(
        "finance.dunning.collection_handover",
        "Read one collection handover with its invoices, last notices and delivery hold.",
        False,
        _collection_handover,
    ),
    "fulfillment_queue": Tool(
        "fulfillment_queue",
        "Read the materialized order fulfillment queue.",
        False,
        _fulfillment_queue,
    ),
    "fulfillment_readiness": Tool(
        "fulfillment_readiness",
        "Read the canonical fulfillment decision for one commitment.",
        False,
        _fulfillment_readiness,
    ),
    "fulfillment_blockers": Tool(
        "fulfillment_blockers",
        "Read materialized order and item blockers.",
        False,
        _fulfillment_blockers,
    ),
    "item_supply_demand": Tool(
        "item_supply_demand",
        "Read materialized supply and demand by item.",
        False,
        _item_supply_demand,
    ),
    "order_explain": Tool(
        "order_explain",
        "Explain one order through Source, Evidence, and Reality.",
        False,
        _order_explain,
    ),
    "shipments_list": Tool(
        "shipments_list",
        "List real physical shipments, distinct from delivery commitments.",
        False,
        _shipments_list,
    ),
    "shipment_explain": Tool(
        "shipment_explain",
        "Explain packages, tracking observations and physical Movements for one shipment.",
        False,
        _shipment_explain,
    ),
    "shipment_notice_record": Tool(
        "shipment_notice_record",
        "Record a physical shipment notice without moving stock.",
        True,
        _shipment_notice_record,
    ),
    "shipment_dispatch": Tool(
        "shipment_dispatch",
        "Dispatch one reviewed physical package and its exact Movements.",
        True,
        _shipment_execution("outbound"),
    ),
    "shipment_receive": Tool(
        "shipment_receive",
        "Receive one reviewed physical package and its exact Movements.",
        True,
        _shipment_execution("inbound"),
    ),
    "shipment_event_record": Tool(
        "shipment_event_record",
        "Append one attributed logistics observation.",
        True,
        _shipment_event_record,
    ),
    "shipment_event_supersede": Tool(
        "shipment_event_supersede",
        "Supersede one incorrect logistics observation without deleting it.",
        True,
        _shipment_event_supersede,
    ),
    "reserve": Tool(
        "reserve", "Allocate stock to a customer commitment.", True, _reserve
    ),
    "movement_correct": Tool(
        "movement_correct",
        "Correct one immutable Movement through an exact inverse and optional replacement.",
        True,
        _movement_correct,
    ),
    "ledger_reverse": Tool(
        "ledger_reverse",
        "Reverse one complete immutable Ledger posting group.",
        True,
        _ledger_reverse,
    ),
    "demo_seed": Tool(
        "demo_seed",
        "Build the compact demo company in an empty tenant.",
        True,
        _seed_demo,
    ),
    "normal_month": Tool(
        "normal_month",
        "Run the deterministic September 2026 business month in an empty tenant.",
        True,
        _normal_month,
    ),
    "source_ingest": Tool(
        "source_ingest",
        "Attach an immutable uploaded artifact to Source evidence and queue interpretation.",
        True,
        _source_ingest,
    ),
    "fact_observe": Tool(
        "fact_observe",
        "Record one source-supported operational observation after confirmation.",
        True,
        _fact_observe,
    ),
    "reality_gaps": Tool(
        "reality_gaps", "List missing-information work.", False, _reality_gaps
    ),
    "reality_gap_get": Tool(
        "reality_gap_get",
        "Inspect one missing-information item.",
        False,
        _reality_gap_get,
    ),
    "reality_gap_simulate": Tool(
        "reality_gap_simulate",
        "Simulate a safe Fact rule without effects.",
        False,
        _reality_gap_simulate,
    ),
    "reality_gap_create": Tool(
        "reality_gap_create",
        "Capture missing business information.",
        True,
        _reality_gap_create,
    ),
    "reality_gap_entry_add": Tool(
        "reality_gap_entry_add",
        "Add investigation evidence or an answer.",
        True,
        _reality_gap_entry_add,
    ),
    "reality_gap_recommend": Tool(
        "reality_gap_recommend",
        "Prepare a modeling recommendation.",
        True,
        _reality_gap_recommend,
    ),
    "reality_gap_decide": Tool(
        "reality_gap_decide",
        "Settle the modeling destination.",
        True,
        _reality_gap_decide,
    ),
    "reality_gap_implementation_prepare": Tool(
        "reality_gap_implementation_prepare",
        "Prepare a safe rule or developer package.",
        True,
        _reality_gap_prepare,
    ),
    "reality_gap_rule_activate": Tool(
        "reality_gap_rule_activate",
        "Activate a reviewed Fact rule.",
        True,
        _reality_gap_activate,
    ),
    "reality_gap_rule_disable": Tool(
        "reality_gap_rule_disable",
        "Disable a Fact rule for future sources.",
        True,
        _reality_gap_disable,
    ),
    "reality_gap_rule_replay": Tool(
        "reality_gap_rule_replay",
        "Replay a Fact rule over reviewed sources.",
        True,
        _reality_gap_replay,
    ),
    "party_create": Tool(
        "party_create",
        "Create one or more Parties after confirmation.",
        True,
        _party_create,
    ),
    "company_party_record": Tool(
        "company_party_record",
        "Record the company itself as a business partner with the role company "
        "after confirmation.",
        True,
        _company_party_record,
    ),
    "item_create": Tool(
        "item_create",
        "Create one or more Items after confirmation.",
        True,
        _item_create,
    ),
    "location_create": Tool(
        "location_create",
        "Create one or more Locations after confirmation.",
        True,
        _location_create,
    ),
    "party_update": Tool(
        "party_update",
        "Update one or more Parties after confirmation.",
        True,
        _party_update,
    ),
    "item_update": Tool(
        "item_update",
        "Update one or more Items after confirmation.",
        True,
        _item_update,
    ),
    "location_update": Tool(
        "location_update",
        "Update one or more Locations after confirmation.",
        True,
        _location_update,
    ),
    "order_create": Tool(
        "order_create", "Create one sales or purchase order.", True, _manual_order
    ),
    "document_correct": Tool(
        "document_correct", "Correct manual Document evidence.", True, _document_correct
    ),
    "document_source_correct": Tool(
        "document_source_correct",
        "Append corrected immutable source evidence.",
        True,
        _document_source_correct,
    ),
    "document_lines_correct": Tool(
        "document_lines_correct",
        "Correct a complete manual DocumentLine snapshot.",
        True,
        _document_lines_correct,
    ),
    "handling_unit_create": Tool(
        "handling_unit_create", "Create a handling unit.", True, _handling_unit_create
    ),
    "lot_create": Tool("lot_create", "Create an inventory lot.", True, _lot_create),
    "serial_unit_create": Tool(
        "serial_unit_create", "Create a serialized unit.", True, _serial_unit_create
    ),
    "movement_create": Tool(
        "movement_create",
        "Record an immutable physical Movement.",
        True,
        _movement_create,
    ),
    "movement_explanation": Tool(
        "movement_explanation",
        "Explain why an immutable physical Movement exists from its shortest true links.",
        False,
        _movement_explanation,
    ),
    "return_disposition": Tool(
        "return_disposition",
        "Resolve arrived customer-return quantity through one explicit physical outcome.",
        True,
        _return_disposition,
    ),
    "shipment_delivery_failure": Tool(
        "shipment_delivery_failure",
        "Record that a customer shipment came back undeliverable, was refused or was lost, reopening its promise.",
        True,
        _shipment_delivery_failure,
    ),
    "drop_shipment_record": Tool(
        "drop_shipment_record",
        "Record that a supplier shipped an assigned purchase straight to the customer, keeping both promises.",
        True,
        _drop_shipment_record,
    ),
    "customer_exchange_record": Tool(
        "customer_exchange_record",
        "Settle part of a customer return with a free replacement instead of a credit.",
        True,
        _customer_exchange_record,
    ),
    "down_payment_invoice_record": Tool(
        "down_payment_invoice_record",
        "Record and post a down-payment invoice for a sales order: a receivable against received down payments that bills no quantity.",
        True,
        _down_payment_invoice_record,
    ),
    "proforma_invoice_record": Tool(
        "proforma_invoice_record",
        "Record a pro-forma invoice for a sales order as evidence only: it posts nothing, is no open item and bills no quantity.",
        True,
        _proforma_invoice_record,
    ),
    "month_end_billing": Tool(
        "month_end_billing",
        "Read the month-end billing lists: order lines shipped and not invoiced, and invoiced and not shipped, from the findings at one instant.",
        False,
        _month_end_billing,
    ),
    "stock_blocks": Tool(
        "stock_blocks",
        "Read the stock held back by blocks, with item, location, quantity and reason.",
        False,
        _stock_blocks,
    ),
    "stock_block": Tool(
        "stock_block",
        "Block stock where it lies with a reason; it stays put and is not available.",
        True,
        _stock_block,
    ),
    "stock_block_release": Tool(
        "stock_block_release",
        "Release a stock block, wholly or partly, with a reason.",
        True,
        _stock_block_resolve(False),
    ),
    "stock_block_scrap": Tool(
        "stock_block_scrap",
        "Scrap blocked stock, wholly or partly, with a reason and one adjustment.",
        True,
        _stock_block_resolve(True),
    ),
    "backorders_serve": Tool(
        "backorders_serve",
        "Reserve arrived stock for waiting customer orders in the serving order: assigned first, then by due date.",
        True,
        _backorders_serve,
    ),
    "available_to_promise": Tool(
        "available_to_promise",
        "Read from when and how much of an item can be promised: free stock now, then each open purchase with its date.",
        False,
        _available_to_promise,
    ),
    "company_currency_set": Tool(
        "company_currency_set",
        "State the company currency the books are kept in; refused once the company has posted anything.",
        True,
        _company_currency_set,
    ),
    "company_currency": Tool(
        "company_currency",
        "Read the company currency and whether the company has posted anything.",
        False,
        _company_currency,
    ),
    "supplier_item_terms_set": Tool(
        "supplier_item_terms_set",
        "State a supplier's minimum order quantity and order multiple for an item.",
        True,
        _supplier_item_terms_set,
    ),
    "supplier_item_terms_remove": Tool(
        "supplier_item_terms_remove",
        "Withdraw a supplier's minimum order quantity and order multiple for an item.",
        True,
        _supplier_item_terms_remove,
    ),
    "supplier_item_terms": Tool(
        "supplier_item_terms",
        "Read suppliers' minimum order quantities and order multiples.",
        False,
        _supplier_item_terms,
    ),
    "purchase_match": Tool(
        "purchase_match",
        "Read whether each line of a purchase order is ordered = received = billed at the agreed price, or what differs.",
        False,
        _purchase_match,
    ),
    "customer_item_number_set": Tool(
        "customer_item_number_set",
        "State which of our items a customer's own article number names, with the customer's name for it.",
        True,
        _customer_item_number_set,
    ),
    "customer_item_number_remove": Tool(
        "customer_item_number_remove",
        "Withdraw a customer's article number; lines ordered by it keep it as stated.",
        True,
        _customer_item_number_remove,
    ),
    "customer_item_numbers": Tool(
        "customer_item_numbers",
        "Read a customer's own article numbers for our items, or the numbers customers use for one item.",
        False,
        _customer_item_numbers,
    ),
    "outbound_delivery_plan": Tool(
        "outbound_delivery_plan",
        "Plan an outbound delivery of one customer's open promises, with recipient, address, booked slot and staging location.",
        True,
        _outbound_delivery_plan,
    ),
    "outbound_delivery_revise": Tool(
        "outbound_delivery_revise",
        "Revise a planned delivery before it ships; every statement is kept.",
        True,
        _outbound_delivery_revise,
    ),
    "outbound_delivery_pick": Tool(
        "outbound_delivery_pick",
        "Pick a planned delivery into its staging location; the reservation moves with the goods.",
        True,
        _outbound_delivery_pick,
    ),
    "outbound_delivery_put_back": Tool(
        "outbound_delivery_put_back",
        "Put picked goods back out of staging; an open promise's reservation moves back with them.",
        True,
        _outbound_delivery_put_back,
    ),
    "outbound_deliveries": Tool(
        "outbound_deliveries",
        "Read the planned deliveries, newest first, with their state and per line planned, picked, to put back and shipped.",
        False,
        _outbound_deliveries,
    ),
    "outbound_delivery_detail": Tool(
        "outbound_delivery_detail",
        "Read one planned delivery: lines, picks, statements, shipment and the dispatch arguments.",
        False,
        _outbound_delivery_detail,
    ),
    "stock_count": Tool(
        "stock_count",
        "Record a count of a location and post every difference as an adjustment; a loss comes off free stock first, then blocks.",
        True,
        _stock_count,
    ),
    "external_stock_state": Tool(
        "external_stock_state",
        "Record stock someone outside states per item and location, such as a 3PL's report; it never moves stock and a difference becomes a finding.",
        True,
        _external_stock_state,
    ),
    "external_stock": Tool(
        "external_stock",
        "Read the latest external stock statement per item and location with Reality's stock at the stated time and the difference.",
        False,
        _external_stock,
    ),
    "stock_counts": Tool(
        "stock_counts",
        "Read the counts of a location or of the company, newest first.",
        False,
        _stock_counts,
    ),
    "stock_count_detail": Tool(
        "stock_count_detail",
        "Read one count: each line as counted, the book at its counting time, and the adjustments that posted it.",
        False,
        _stock_count_detail,
    ),
    "delivery_rule_set": Tool(
        "delivery_rule_set",
        "State how a customer or one order is delivered: partial allowed, ship complete or no backorders, with a reason.",
        True,
        _delivery_rule_set,
    ),
    "delivery_rules": Tool(
        "delivery_rules",
        "Read the delivery rule in force for a customer or an order, where it comes from, and every earlier statement.",
        False,
        _delivery_rules,
    ),
    "reorder_points": Tool(
        "reorder_points",
        "Read the reorder points of the company, of one item or of one location.",
        False,
        _reorder_points,
    ),
    "reorder_point_set": Tool(
        "reorder_point_set",
        "Set or change the reorder point and reorder quantity of an item at a location.",
        True,
        _reorder_point_set,
    ),
    "reorder_point_remove": Tool(
        "reorder_point_remove",
        "Remove the reorder point of an item at a location.",
        True,
        _reorder_point_remove,
    ),
    "kits": Tool(
        "kits",
        "Read the kits of the company, or of one item, with their components and what each location can build.",
        False,
        _kits,
    ),
    "kit_split": Tool(
        "kit_split",
        "Read how a kit's order or invoice line splits its stated net, tax and gross across the components.",
        False,
        _kit_split,
    ),
    "kit_define": Tool(
        "kit_define",
        "State the components of a kit: each component item, how many one kit takes and optionally its share of the price.",
        True,
        _kit_define,
    ),
    "commitment_substitute_accept": Tool(
        "commitment_substitute_accept",
        "Accept another item in place of what a purchase line ordered, with a reason; receipts of it then fulfil the line.",
        True,
        _commitment_substitute_accept,
    ),
    "kit_assemble": Tool(
        "kit_assemble",
        "Assemble kits at a location: consume the components and produce the kits, all or nothing.",
        True,
        _kit_assemble,
    ),
    "party_merge": Tool(
        "party_merge",
        "Merge a duplicate business partner into the one that survives, with a reason; both histories stay as stated.",
        True,
        _party_merge,
    ),
    "party_merges": Tool(
        "party_merges",
        "Read the business partner merges, or those one partner took part in.",
        False,
        _party_merges,
    ),
    "credit_hold_release": Tool(
        "credit_hold_release",
        "Release an order's credit holds with a stated reason; an owner confirms.",
        True,
        _credit_hold_release,
    ),
    "order_line_item_assign": Tool(
        "order_line_item_assign",
        "Give an order line whose stated SKU matched no item its item and create its delivery promise.",
        True,
        _order_line_item_assign,
    ),
    "customer_exchange": Tool(
        "customer_exchange",
        "Read what a customer exchange replaced, what it sent and what it still settles.",
        False,
        _customer_exchange,
    ),
    "drop_shipments": Tool(
        "drop_shipments",
        "Read a promise's drop shipping: the purchase assigned to it and what the supplier shipped straight to the customer.",
        False,
        _drop_shipments,
    ),
    "delivery_failure_summary": Tool(
        "delivery_failure_summary",
        "Read a failed delivery: what happened, what it reversed and the carrier claim it opened.",
        False,
        _delivery_failure_summary,
    ),
    "return_disposition_summary": Tool(
        "return_disposition_summary",
        "Read arrived, resolved and unresolved customer-return quantity by disposition.",
        False,
        _return_disposition_summary,
    ),
    "reservation_release": Tool(
        "reservation_release",
        "Release one active reservation.",
        True,
        _reservation_release,
    ),
    "commitment_revise": Tool(
        "commitment_revise",
        "Record that a counterparty now states a different date, quantity or, for a purchase, unit price.",
        True,
        _commitment_revise,
    ),
    "commitment_cancel": Tool(
        "commitment_cancel",
        "Cancel the open remainder of one commitment for an explicit reason.",
        True,
        _commitment_cancel,
    ),
    "commitment_hold": Tool(
        "commitment_hold", "Hold one open commitment.", True, _commitment_hold
    ),
    "commitment_hold_release": Tool(
        "commitment_hold_release",
        "Release commitment holds.",
        True,
        _commitment_hold_release,
    ),
    "document_hold": Tool(
        "document_hold",
        "Hold open commitments evidenced by a document.",
        True,
        _document_hold,
    ),
    "document_hold_release": Tool(
        "document_hold_release",
        "Release document commitment holds.",
        True,
        _document_hold_release,
    ),
    "party_delivery_hold": Tool(
        "party_delivery_hold", "Place a party delivery hold.", True, _party_hold
    ),
    "party_delivery_hold_release": Tool(
        "party_delivery_hold_release",
        "Release party delivery holds.",
        True,
        _party_hold_release,
    ),
    "master_data_lifecycle": Tool(
        "master_data_lifecycle", "Activate or deactivate master data.", True, _lifecycle
    ),
    "payment_term_create": Tool(
        "payment_term_create", "Create a payment term.", True, _payment_term_create
    ),
    "payment_term_update": Tool(
        "payment_term_update", "Update a payment term.", True, _payment_term_update
    ),
    "price_list_create": Tool(
        "price_list_create", "Create a price list.", True, _price_list_create
    ),
    "price_list_update": Tool(
        "price_list_update", "Update a price list.", True, _price_list_update
    ),
    "price_tier_create": Tool(
        "price_tier_create", "Add a price tier.", True, _price_tier_create
    ),
    "party_price_list_assign": Tool(
        "party_price_list_assign",
        "Assign a price list to a party.",
        True,
        _party_price_list_assign,
    ),
    "party_group_create": Tool(
        "party_group_create", "Create a pricing party group.", True, _party_group_create
    ),
    "party_group_update": Tool(
        "party_group_update", "Update a pricing party group.", True, _party_group_update
    ),
    "party_group_member_add": Tool(
        "party_group_member_add",
        "Add a party to a pricing group.",
        True,
        _party_group_member_add,
    ),
    "group_price_list_assign": Tool(
        "group_price_list_assign",
        "Assign a price list to a group.",
        True,
        _group_price_list_assign,
    ),
    "customer_payment_post": Tool(
        "customer_payment_post",
        "Post and allocate a customer payment.",
        True,
        _payment("customer"),
    ),
    "return_announce": Tool(
        "return_announce",
        "Record that a customer says goods are coming back.",
        True,
        _return_announce,
    ),
    "return_announcement_withdraw": Tool(
        "return_announcement_withdraw",
        "Record that a customer is not sending announced goods back after all.",
        True,
        _return_announcement_withdraw,
    ),
    "return_announcements": Tool(
        "return_announcements",
        "List the returns customers have announced and what is still expected.",
        False,
        _return_announcements,
    ),
    "lot_expiry_state": Tool(
        "lot_expiry_state",
        "Record the best-before date somebody read off the goods.",
        True,
        _lot_expiry_state,
    ),
    "lot_expiry_correct": Tool(
        "lot_expiry_correct",
        "Record that a stated best-before was read wrong and what it says instead.",
        True,
        _lot_expiry_correct,
    ),
    "expired_lots": Tool(
        "expired_lots",
        "List the batches whose stated best-before date has passed.",
        False,
        _expired_lots,
    ),
    "payment_run_preview": Tool(
        "payment_run_preview",
        "Show which supplier invoices are worth paying now.",
        False,
        _payment_run_preview,
    ),
    "payment_run": Tool(
        "payment_run",
        "Pay the supplier invoices and amounts somebody confirmed, in one transaction.",
        True,
        _payment_run,
    ),
    "stale_closure_preview": Tool(
        "stale_closure_preview",
        "Show which stale promises a closure would close.",
        False,
        _stale_closure_preview,
    ),
    "stale_closure": Tool(
        "stale_closure",
        "Close stale promises somebody previewed and counted.",
        True,
        _stale_closure,
    ),
    "document_create": Tool(
        "document_create",
        "Record manual document evidence with its normalized lines.",
        True,
        _document_create,
    ),
    "sales_invoice_post": Tool(
        "sales_invoice_post",
        "Book a recorded sales invoice into the ledger.",
        True,
        _sales_invoice_post,
    ),
    "supplier_invoice_post": Tool(
        "supplier_invoice_post",
        "Book a recorded supplier invoice into the ledger.",
        True,
        _supplier_invoice_post,
    ),
    "sales_invoice_record": Tool(
        "sales_invoice_record",
        "Record stated invoice evidence and post its receivable.",
        True,
        _sales_invoice_record,
    ),
    "supplier_invoice_record": Tool(
        "supplier_invoice_record",
        "Record stated supplier invoice evidence and post its payable.",
        True,
        _supplier_invoice_record,
    ),
    "supply_assign": Tool(
        "supply_assign",
        "Assign supplier supply to customer demand or stock replenishment.",
        True,
        _supply_assign,
    ),
    "supply_coverage": Tool(
        "supply_coverage",
        "Show assigned, replenishment, received, open, and unassigned supply.",
        False,
        _supply_coverage,
    ),
    "sales_credit_record": Tool(
        "sales_credit_record",
        "Record an invoice-linked customer credit with explicit netting, or a legacy return credit; no refund or stock movement.",
        True,
        _sales_credit_record,
    ),
    "invoice_credit_context": Tool(
        "invoice_credit_context",
        "Read eligible invoice positions and remaining customer-credit capacity.",
        False,
        _invoice_credit_context,
    ),
    "invoice_billable_positions": Tool(
        "invoice_billable_positions",
        "Read a party's delivered or received order positions not yet fully billed, grouped by order.",
        False,
        _invoice_billable_positions,
    ),
    "supplier_invoice_free_record": Tool(
        "supplier_invoice_free_record",
        "Record source-stated supplier invoice evidence and its payable without an order.",
        True,
        _supplier_invoice_free_record,
    ),
    "credit_note_post": Tool(
        "credit_note_post",
        "Post a credit note as the reverse of a sales invoice.",
        True,
        _credit_note_post,
    ),
    "credit_note_allocate": Tool(
        "credit_note_allocate",
        "Net a posted credit note against an open invoice.",
        True,
        _credit_note_allocate,
    ),
    "customer_refund_post": Tool(
        "customer_refund_post",
        "Record an actual customer refund and allocate it to an open credit note. Partial refunds are supported; this does not initiate a bank transfer.",
        True,
        _customer_refund_post,
    ),
    "supplier_payment_post": Tool(
        "supplier_payment_post",
        "Post and allocate a supplier payment.",
        True,
        _payment("supplier"),
    ),
    "supplier_credit_note_post": Tool(
        "supplier_credit_note_post",
        "Book a supplier credit note as the reverse of its invoice.",
        True,
        _supplier_credit_note_post,
    ),
    "supplier_credit_note_allocate": Tool(
        "supplier_credit_note_allocate",
        "Net a booked supplier credit against an open supplier invoice.",
        True,
        _supplier_credit_note_allocate,
    ),
    "supplier_refund_post": Tool(
        "supplier_refund_post",
        "Take money back from a supplier and settle the credit note.",
        True,
        _supplier_refund_post,
    ),
    "connector_install": Tool(
        "connector_install",
        "Install a credential-free connector shell.",
        True,
        _connector_install,
    ),
    "source_system_create": Tool(
        "source_system_create", "Define a source system.", True, _source_system_create
    ),
    "source_record_ingest": Tool(
        "source_record_ingest",
        "Store and queue one arbitrary lossless source payload.",
        True,
        _source_record_ingest,
    ),
    "source_system_lifecycle": Tool(
        "source_system_lifecycle",
        "Activate or deactivate a source system.",
        True,
        _source_system_lifecycle,
    ),
    "source_capability_create": Tool(
        "source_capability_create",
        "Define a source capability.",
        True,
        _source_capability_create,
    ),
    "source_capability_lifecycle": Tool(
        "source_capability_lifecycle",
        "Activate or deactivate a source capability.",
        True,
        _source_capability_lifecycle,
    ),
    "member_invite": Tool(
        "member_invite", "Invite one company member.", True, _member_invite
    ),
    "invitation_resend": Tool(
        "invitation_resend", "Resend one company invitation.", True, _invitation_resend
    ),
    "invitation_revoke": Tool(
        "invitation_revoke", "Revoke one company invitation.", True, _invitation_revoke
    ),
    "member_remove": Tool(
        "member_remove", "Remove one active non-owner member.", True, _member_remove
    ),
}


def run_read_tool(
    session: Session,
    tenant_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    """
    BUSINESS PURPOSE:
    Invoke an exact registered read-only application tool through the common dispatcher.

    BUSINESS RULE application.run_read_tool.1:
    Refuse an unknown registered name.

    BUSINESS RULE application.run_read_tool.2:
    Refuse mutating tools; they require a confirmed proposal.

    BUSINESS RULE application.run_read_tool.3:
    Invoke the registered handler with the current company and supplied arguments, defaulting to an empty object, and serialize its result.
    """
    tool = TOOLS.get(tool_name)
    # reality-rule: application.run_read_tool.1
    if tool is None:
        raise NotFound("Tool not found.")
    # reality-rule: application.run_read_tool.2
    if tool.mutating:
        raise InvalidOperation("Mutating tools require a confirmed proposal.")
    # reality-rule: application.run_read_tool.3
    return _json_value(tool.handler(session, tenant_id, arguments or {}))


# Finance account writes are dispatched only inside confirmed atomic execution.
from reality.services.finance.accounts import list_accounts, lock_finance
from reality.tools.finance import (
    ADJUSTMENT_COMMAND,
    ASSIGNMENT_COMMAND,
    AUTHORIZATION_RECORD_COMMAND,
    CAPTURE_RECORD_COMMAND,
    COLLECTION_HANDOVER_COMMAND,
    DEPOSIT_CLEAR_COMMAND,
    DEPOSIT_RECORD_COMMAND,
    DUNNING_COMMAND,
    DUNNING_REVERSE_COMMAND,
    DUNNING_RUN_COMMAND,
    DUNNING_SCHEDULE_COMMAND,
    FINANCE_COMMANDS,
    OPENING_COMMAND,
    PAYMENT_RETURN_COMMAND,
    PAYOUT_SETTLE_COMMAND,
    REFERENCE_COMMANDS,
    SETTLEMENT_COMMAND,
    SOURCE_MAPPING_COMMAND,
    execute_finance_command,
    validate_finance_request,
)


def _confirmed_account_only(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Apply a reviewed finance change with owner confirmation.

    BUSINESS RULE application.confirmed_account_only.1:
    Refuse direct invocation: this operation is available only through the authenticated confirmed-proposal execution path.
    """
    # reality-rule: application.confirmed_account_only.1
    raise InvalidOperation(code="finance_change_confirmation_required")


def _adjustment_context_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read invoice claim and permitted reduction counterpart.

    BUSINESS RULE application.adjustment_context_read.1:
    Route this company-scoped request to adjustment_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.settlement import adjustment_context

    # reality-rule: application.adjustment_context_read.1
    return adjustment_context(session, tenant_id, arguments["invoice_id"])


def _settlement_context_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read invoice or credit, account eligibility and review revision.

    BUSINESS RULE application.settlement_context_read.1:
    Route this company-scoped request to settlement_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.settlement_flows import settlement_context

    # reality-rule: application.settlement_context_read.1
    return settlement_context(session, tenant_id, **arguments)


def _credits_read(session, tenant_id, arguments):
    """
    Available customer or supplier credit: original payments and credit notes not yet used (feature 169).

    BUSINESS PURPOSE:
    Read available customer or supplier credit: payments and credit notes with an unused remainder.

    BUSINESS RULE application.credits_read.1:
    Clamp the first-page size to between one and 200, using 50 when no effective limit was supplied.

    BUSINESS RULE application.credits_read.2:
    Read available credit items through the shared service for the selected side, search and status; default to customer and outstanding.

    BUSINESS RULE application.credits_read.3:
    Expose the shared original, used and available amounts as strings, retaining currency, party identity, state, totals and whether further results exist.
    """
    from reality.services.finance.credits import available_credit_items

    side = str(arguments.get("side") or "customer")
    status = str(arguments.get("status") or "outstanding")
    # reality-rule: application.credits_read.1
    limit = max(1, min(int(arguments.get("limit") or 50), 200))
    # reality-rule: application.credits_read.2
    page = available_credit_items(
        session,
        tenant_id,
        side=side,
        query=str(arguments.get("query") or ""),
        status=status,
        page=1,
        size=limit,
    )
    # reality-rule: application.credits_read.3
    return {
        "side": side,
        "status": status,
        "items": [
            {
                "document_id": row["document_id"],
                "number": row["number"],
                "document_type": row["document_type"],
                "party_id": row["party_id"],
                "party": row["party"],
                "original": str(row["gross"]),
                "used": str(row["settled"]),
                "available": str(row["open"]),
                "currency": row["currency"],
                "state": row["status"],
                "document_date": row.get("document_date"),
            }
            for row in page["items"]
        ],
        "totals": page.get("totals", []),
        "more": bool(page.get("page", {}).get("has_next")),
    }


def _party_balances_read(session, tenant_id, arguments):
    """
    Where each customer or supplier stands: open, overdue, credit, balance (feature 170).

    BUSINESS PURPOSE:
    Read where each customer or supplier stands: open, of which overdue, available credit and balance per party and currency.

    BUSINESS RULE application.party_balances_read.1:
    Clamp the first-page size between one and 200, defaulting to 50.

    BUSINESS RULE application.party_balances_read.2:
    Read partner balances through the shared service for the selected customer/supplier side, search and optional credit-only filter; retain the service's evaluation time and currency totals.
    """
    from reality.services.finance.balances import party_balances

    side = str(arguments.get("side") or "customer")
    # reality-rule: application.party_balances_read.1
    limit = max(1, min(int(arguments.get("limit") or 50), 200))
    # reality-rule: application.party_balances_read.2
    page = party_balances(
        session,
        tenant_id,
        side=side,
        credit_only=bool(arguments.get("credit_only")),
        query=str(arguments.get("query") or ""),
        page=1,
        size=limit,
    )
    return {
        "side": side,
        "as_of": page["as_of"],
        "items": page["items"],
        "totals": page["totals"],
        "count": page["page"]["total"],
    }


def _payments_read(session, tenant_id, arguments):
    """
    Recorded payments with allocated and unallocated amounts (feature 169).

    BUSINESS PURPOSE:
    Read recorded payments with allocated and unallocated amounts.

    BUSINESS RULE application.payments_read.1:
    Refuse filters other than direction, only-unallocated, query and limit.

    BUSINESS RULE application.payments_read.2:
    IF direction is supplied, accept incoming or outgoing only.

    BUSINESS RULE application.payments_read.3:
    Read canonical payment rows, filter by direction, positive unallocated amount when requested, and case-insensitive document-number/party search. Return at most the clamped limit; report reversal state before allocation state.
    """
    from reality.services.core import payment_rows

    supported_arguments = {"direction", "only_unallocated", "query", "limit"}
    unsupported_arguments = sorted(set(arguments) - supported_arguments)
    # reality-rule: application.payments_read.1
    if unsupported_arguments:
        raise InvalidOperation(
            "Unsupported payment filter: " + ", ".join(unsupported_arguments) + "."
        )
    raw_direction = arguments.get("direction")
    direction = str(raw_direction) if raw_direction is not None else ""
    # reality-rule: application.payments_read.2
    if raw_direction is not None and direction not in {"incoming", "outgoing"}:
        raise InvalidOperation("Payment direction must be incoming or outgoing.")
    only_unallocated = bool(arguments.get("only_unallocated") or False)
    query = str(arguments.get("query") or "").strip().lower()
    limit = max(1, min(int(arguments.get("limit") or 50), 200))
    items = []
    # reality-rule: application.payments_read.3
    for row in payment_rows(session, tenant_id):
        document = row["document"]
        if direction and row["direction"] != direction:
            continue
        if only_unallocated and row["unallocated"] <= 0:
            continue
        if query and query not in f"{document.number} {row['party']}".lower():
            continue
        cash = row["cash_entry"]
        items.append(
            {
                "payment_id": document.id,
                "number": document.number,
                "party_id": cash.party_id,
                "party": row["party"],
                "direction": row["direction"],
                "amount": str(cash.amount),
                "allocated": str(row["allocated"]),
                "unallocated": str(row["unallocated"]),
                "currency": cash.currency,
                "effective_at": cash.effective_at,
                "state": (
                    "reversed"
                    if row.get("reversal_role") in {"reversed_original", "reversing"}
                    else "unallocated"
                    if row["allocated"] == 0
                    else "partially_allocated"
                    if row["unallocated"] > 0
                    else "allocated"
                ),
            }
        )
        if len(items) >= limit:
            break
    return {"items": items, "limit": limit}


def _opening_context_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read opening import accounts, parties and review revision.

    BUSINESS RULE application.opening_context_read.1:
    Route this company-scoped request to opening_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.opening import opening_context

    # reality-rule: application.opening_context_read.1
    return opening_context(session, tenant_id, **arguments)


def _reference_list_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read managed internal finance references.

    BUSINESS RULE application.reference_list_read.1:
    Route this company-scoped request to list_references. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.references import list_references

    # reality-rule: application.reference_list_read.1
    return list_references(session, tenant_id, **arguments)


def _reference_history_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read immutable reference change evidence.

    BUSINESS RULE application.reference_history_read.1:
    Route this company-scoped request to reference_history. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.references import reference_history

    # reality-rule: application.reference_history_read.1
    return reference_history(session, tenant_id, **arguments)


def _component_context_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read received financial detail and internal attribution.

    BUSINESS RULE application.component_context_read.1:
    Route this company-scoped request to component_context. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.components import component_context

    # reality-rule: application.component_context_read.1
    return component_context(session, tenant_id, **arguments)


def _component_history_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read immutable component attribution revisions.

    BUSINESS RULE application.component_history_read.1:
    Route this company-scoped request to component_history. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.components import component_history

    # reality-rule: application.component_history_read.1
    return component_history(session, tenant_id, **arguments)


def _matrix_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read fixed operations and configured default accounts; no transaction authorization.

    BUSINESS RULE application.matrix_read.1:
    Refuse business arguments; the transaction matrix is a fixed read.

    BUSINESS RULE application.matrix_read.2:
    Return the shared operation/account matrix for this company without granting authorization.
    """
    from reality.services.finance.accounts import transaction_matrix

    # reality-rule: application.matrix_read.1
    if arguments:
        raise InvalidOperation("Transaction matrix takes no business arguments.")
    # reality-rule: application.matrix_read.2
    return transaction_matrix(session, tenant_id)


TOOLS["finance.matrix.read"] = Tool(
    "finance.matrix.read",
    "Read fixed operations and configured default accounts; no transaction authorization.",
    False,
    _matrix_read,
)
TOOLS["finance.components.context"] = Tool(
    "finance.components.context",
    "Read received financial detail and internal attribution.",
    False,
    _component_context_read,
)
TOOLS["finance.component.history"] = Tool(
    "finance.component.history",
    "Read immutable component attribution revisions.",
    False,
    _component_history_read,
)
TOOLS["finance.references.list"] = Tool(
    "finance.references.list",
    "Read managed internal finance references.",
    False,
    _reference_list_read,
)
TOOLS["finance.references.history"] = Tool(
    "finance.references.history",
    "Read immutable reference change evidence.",
    False,
    _reference_history_read,
)
TOOLS["finance.opening.context"] = Tool(
    "finance.opening.context",
    "Read opening import accounts, parties and review revision.",
    False,
    _opening_context_read,
)
TOOLS["finance.settlement.context"] = Tool(
    "finance.settlement.context",
    "Read invoice or credit, account eligibility and review revision.",
    False,
    _settlement_context_read,
)
TOOLS["finance.credits.list"] = Tool(
    "finance.credits.list",
    "Read available customer or supplier credit: payments and credit notes with an unused remainder.",
    False,
    _credits_read,
)
TOOLS["finance.party_balances.list"] = Tool(
    "finance.party_balances.list",
    "Read where each customer or supplier stands: open, of which overdue, available credit and balance per party and currency.",
    False,
    _party_balances_read,
)
TOOLS["finance.payments.list"] = Tool(
    "finance.payments.list",
    "Read recorded payments with allocated and unallocated amounts.",
    False,
    _payments_read,
)
TOOLS["finance.adjustment.context"] = Tool(
    "finance.adjustment.context",
    "Read invoice claim and permitted reduction counterpart.",
    False,
    _adjustment_context_read,
)


def _finance_accounts_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read the company's configured finance accounts through the canonical account service.

    BUSINESS RULE application.finance_accounts_read.1:
    Return list_accounts for the current session and company. Extra argument values are ignored, preserving the original adapter contract.
    """
    # reality-rule: application.finance_accounts_read.1
    return list_accounts(session, tenant_id)


TOOLS["finance.accounts.list"] = Tool(
    "finance.accounts.list",
    "Read permitted operational accounts and defaults.",
    False,
    _finance_accounts_read,
)
from reality.tools.costing import commercial_match as _commercial_match_tool
from reality.tools.costing import contribution as _contribution_preview_tool
from reality.tools.costing import evidence as _cost_evidence_tool
from reality.tools.costing import inventory as _inventory_cost_tool
from reality.tools.costing import query as _cost_query_tool
from reality.tools.costing import receipt as _receipt_cost_tool
from reality.tools.costing import record as _cost_record_tool
from reality.tools.costing import review_draft as _cost_review_draft_tool
from reality.tools.costing import reviewed_contribution as _reviewed_contribution_tool

TOOLS["cost.query.get"] = Tool(
    "cost.query.get",
    "Read an exact retained cost answer with constrained cutoffs, scope and freshness.",
    False,
    _cost_query_tool,
)
TOOLS["cost.review.draft"] = Tool(
    "cost.review.draft",
    "Draft the inventory or contribution cost review the held records support, with any open inputs.",
    False,
    _cost_review_draft_tool,
)
TOOLS["cost.record.get"] = Tool(
    "cost.record.get",
    "Inspect retained cost evidence, decisions and exact member pages.",
    False,
    _cost_record_tool,
)
TOOLS["cost.contribution.get"] = Tool(
    "cost.contribution.get",
    "Read confirmed whole-line DB1 and independently reviewed DB2, or their exact retained history.",
    False,
    _reviewed_contribution_tool,
)
TOOLS["cost.commercial-match.get"] = Tool(
    "cost.commercial-match.get",
    "Read a retained partial commercial match and its derived DB1 observation.",
    False,
    _commercial_match_tool,
)
TOOLS["cost.contribution.preview"] = Tool(
    "cost.contribution.preview",
    "Read an unconfirmed exact revenue/consumption candidate; finalized margins stay unavailable.",
    False,
    _contribution_preview_tool,
)
TOOLS["cost.inventory.get"] = Tool(
    "cost.inventory.get",
    "Read confirmed inventory acquisition costs and retained basis.",
    False,
    _inventory_cost_tool,
)
TOOLS["cost.receipt.get"] = Tool(
    "cost.receipt.get",
    "Read receipt costs and retained review history.",
    False,
    _receipt_cost_tool,
)
TOOLS["cost.evidence.get"] = Tool(
    "cost.evidence.get",
    "Read exact received acquisition-cost evidence.",
    False,
    _cost_evidence_tool,
)

for _name in FINANCE_COMMANDS:
    TOOLS[_name] = Tool(
        _name,
        "Apply a reviewed finance change with owner confirmation.",
        True,
        _confirmed_account_only,
    )


#: The conversation whose turn is running, set by `send_chat_message` for the
#: duration of one chat turn (spec 328). A proposal made meanwhile records it;
#: MCP, CLI and service callers leave it unset, so their proposals belong to no chat.
CHAT_SESSION: ContextVar[str | None] = ContextVar("chat_session", default=None)


def create_change_proposal(
    session: Session,
    tenant_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    actor_type: str = "agent",
    _commit: bool = True,
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Prepare a reviewable intention for a registered mutating tool without executing its business handler.

    BUSINESS RULE application.create_change_proposal.1:
    Require the shared proposal-creation policy before preparing the intention.

    BUSINESS RULE application.create_change_proposal.2:
    Refuse a proposal for a read-only tool.

    BUSINESS RULE application.create_change_proposal.3:
    For registered finance commands, validate the request through the shared finance validator before preparing its preview.

    BUSINESS RULE application.create_change_proposal.4:
    For master-data updates, attach each record's current expected revision to the stored intention and retain the reviewed record previews.

    BUSINESS RULE application.create_change_proposal.5:
    For a movement correction without delivery review, retain the shared preview revision and request fingerprint in the intention.

    BUSINESS RULE application.create_change_proposal.6:
    For a ledger reversal without delivery review, retain the shared preview revision and request fingerprint in the intention.

    BUSINESS RULE application.create_change_proposal.7:
    Store normalized arguments and review output in a company-scoped proposed ChangeProposal. This statement records an intention; it does not run the selected business handler.
    """
    # reality-rule: application.create_change_proposal.1
    require_proposal_creation(session, tenant_id, tool_name, arguments)
    tool = TOOLS.get(tool_name)
    if tool is None:
        raise NotFound(code="proposal_tool_not_found")
    # reality-rule: application.create_change_proposal.2
    if not tool.mutating:
        raise InvalidOperation(code="proposal_read_tool_not_needed")
    if tool_name == "document_create":
        from reality.services.core import validate_manual_operational_document_type

        arguments = {
            **arguments,
            "document_type": validate_manual_operational_document_type(
                arguments.get("document_type")
            ),
        }
    if tool_name == "supplier_invoice_free_record":
        from reality.services.invoice_actions import preview_free_supplier_invoice

        preview_free_supplier_invoice(session, tenant_id, arguments)
    if tool_name == "movement_create":
        from reality.services.delivery_actions import validate_public_movement_type

        arguments = {
            **arguments,
            "movement_type": validate_public_movement_type(
                arguments.get("movement_type")
            ),
        }
    from reality.db.core import Tenant
    from reality.services.delivery_actions import REVIEW_KEY, eligible, review_delivery

    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    delivery_review = None
    raw_opening = (
        tool_name == "movement_create"
        and arguments.get("movement_type") == "opening_stock"
    )
    # Raw opening proposals keep the established general-tool contract: no state-bound
    # review is attached here, and the unified opening adapter attaches its stricter one
    # explicitly. The intent is still proved now, because confirmation demands that same
    # review — a decision nobody could ever approve should not be created for a person to
    # find.
    if tenant and tenant.purpose != "playground" and raw_opening:
        from reality.services.opening_stock_actions import review_opening

        review_opening(session, tenant_id, arguments)
    if (
        tenant
        and tenant.purpose != "playground"
        and eligible(tool_name, arguments)
        and not raw_opening
        and tool_name not in {"party_delivery_hold", "party_delivery_hold_release"}
    ):
        from reality.services.business_locks import lock_delivery_state

        lock_delivery_state(session, tenant_id)
        delivery_review = review_delivery(session, tenant_id, tool_name, arguments)
    normalized_arguments = dict(arguments)
    if tool_name == "company_party_record":
        from reality.services.company_party import proposal_arguments

        normalized_arguments = proposal_arguments(session, tenant_id, arguments)
    # reality-rule: application.create_change_proposal.3
    if tool_name in FINANCE_COMMANDS:
        normalized_arguments = validate_finance_request(tool_name, arguments)
    backorder_review = None
    if tool_name == "backorders_serve":
        from reality.services.backorders import review_backorder_serving

        normalized_arguments, backorder_review = review_backorder_serving(
            session, tenant_id, arguments
        )
    stock_block_review = None
    if tool_name in {"stock_block", "stock_block_release", "stock_block_scrap"}:
        from reality.services.stock_blocks import review_stock_block

        normalized_arguments, stock_block_review = review_stock_block(
            session, tenant_id, tool_name, arguments
        )
    supplier_terms_review = None
    if tool_name in {"supplier_item_terms_set", "supplier_item_terms_remove"}:
        from reality.services.supplier_item_terms import review_supplier_item_terms

        normalized_arguments, supplier_terms_review = review_supplier_item_terms(
            session, tenant_id, tool_name, arguments
        )
    customer_item_review = None
    if tool_name in {"customer_item_number_set", "customer_item_number_remove"}:
        from reality.services.customer_item_numbers import (
            review_customer_item_number,
        )

        normalized_arguments, customer_item_review = review_customer_item_number(
            session, tenant_id, tool_name, arguments
        )
    company_currency_review = None
    if tool_name == "company_currency_set":
        from reality.services.finance.company_currency import review_company_currency

        normalized_arguments, company_currency_review = review_company_currency(
            session, tenant_id, arguments
        )
    outbound_delivery_review = None
    if tool_name in {
        "outbound_delivery_plan",
        "outbound_delivery_revise",
        "outbound_delivery_pick",
        "outbound_delivery_put_back",
    }:
        from reality.services.outbound_deliveries import review_outbound_delivery

        normalized_arguments, outbound_delivery_review = review_outbound_delivery(
            session, tenant_id, tool_name, arguments
        )
    external_stock_review = None
    if tool_name == "external_stock_state":
        from reality.services.external_stock import review_external_stock

        normalized_arguments, external_stock_review = review_external_stock(
            session, tenant_id, arguments
        )
    stock_count_review = None
    if tool_name == "stock_count":
        from reality.services.stock_counts import review_stock_count

        normalized_arguments, stock_count_review = review_stock_count(
            session, tenant_id, arguments
        )
    delivery_rule_review = None
    if tool_name == "delivery_rule_set":
        from reality.services.delivery_rules import review_delivery_rule

        normalized_arguments, delivery_rule_review = review_delivery_rule(
            session, tenant_id, arguments
        )
    kit_review = None
    if tool_name in {"kit_define", "kit_assemble"}:
        from reality.services.kits import review_kit

        normalized_arguments, kit_review = review_kit(
            session, tenant_id, tool_name, arguments
        )
    party_merge_review = None
    if tool_name == "party_merge":
        from reality.services.party_merges import review_party_merge

        normalized_arguments, party_merge_review = review_party_merge(
            session, tenant_id, tool_name, arguments
        )
    substitute_review = None
    if tool_name == "commitment_substitute_accept":
        from reality.services.receipt_deviations import review_substitute

        normalized_arguments, substitute_review = review_substitute(
            session, tenant_id, arguments
        )
    reorder_review = None
    if tool_name in {"reorder_point_set", "reorder_point_remove"}:
        from reality.services.reorder_points import review_reorder_point

        normalized_arguments, reorder_review = review_reorder_point(
            session, tenant_id, tool_name, arguments
        )
    if delivery_review:
        normalized_arguments = {
            **delivery_review["intent"],
            REVIEW_KEY: delivery_review,
        }
    preview: dict[str, Any] = {
        "tool": tool_name,
        "arguments": _json_value(normalized_arguments),
        "effect": tool.description,
        "requires_confirmation": True,
    }
    from reality.domain.target_mappings import COMMANDS as TARGET_COMMANDS

    if tool_name == "cost.change":
        from reality.services.analytics.reports import CALLER
        from reality.services.costing import preview_cost_change

        preview["costing"] = preview_cost_change(
            session, tenant_id, normalized_arguments, principal=CALLER.get()
        )
    if tool_name in TARGET_COMMANDS:
        from reality.services.finance.target_mappings import preview_change

        preview["target_configuration"] = preview_change(
            session, tenant_id, tool_name, normalized_arguments
        )
    if tool_name == SOURCE_MAPPING_COMMAND:
        from reality.services.finance.source_mappings import preview_source_mapping

        preview["source_mapping"] = preview_source_mapping(
            session, tenant_id, normalized_arguments
        )
    if tool_name == ASSIGNMENT_COMMAND:
        from reality.services.finance.components import preview_assignment

        preview["assignment"] = preview_assignment(
            session, tenant_id, normalized_arguments
        )
    if tool_name in REFERENCE_COMMANDS:
        from reality.services.finance.references import preview_reference

        preview["reference"] = preview_reference(
            session, tenant_id, normalized_arguments
        )
    if tool_name == ADJUSTMENT_COMMAND:
        from reality.services.finance.settlement import preview_adjustment

        preview["adjustment"] = preview_adjustment(
            session, tenant_id, normalized_arguments
        )
    if tool_name == SETTLEMENT_COMMAND:
        from reality.services.finance.settlement_flows import preview_settlement

        preview["settlement"] = preview_settlement(
            session, tenant_id, normalized_arguments
        )
    if tool_name == OPENING_COMMAND:
        from reality.services.finance.opening import preview_opening

        preview["opening"] = preview_opening(session, tenant_id, normalized_arguments)
    if tool_name == DUNNING_COMMAND:
        from reality.services.dunning import preview_notice

        preview["dunning"] = preview_notice(session, tenant_id, normalized_arguments)
    if kit_review is not None:
        preview["kit"] = kit_review
    if substitute_review is not None:
        preview["substitute"] = substitute_review
    if party_merge_review is not None:
        preview["party_merge"] = party_merge_review
    if reorder_review is not None:
        preview["reorder_point"] = reorder_review
    if delivery_rule_review is not None:
        preview["delivery_rule"] = delivery_rule_review
    if stock_count_review is not None:
        preview["stock_count"] = stock_count_review
    if external_stock_review is not None:
        preview["external_stock"] = external_stock_review
    if outbound_delivery_review is not None:
        preview["outbound_delivery"] = outbound_delivery_review
    if customer_item_review is not None:
        preview["customer_item_number"] = customer_item_review
    if supplier_terms_review is not None:
        preview["supplier_item_terms"] = supplier_terms_review
    if company_currency_review is not None:
        preview["company_currency"] = company_currency_review
    if stock_block_review is not None:
        preview["stock_block"] = stock_block_review
    if backorder_review is not None:
        preview["backorder_serving"] = backorder_review
    if tool_name == DUNNING_SCHEDULE_COMMAND:
        from reality.services.dunning_runs import _stated_levels, schedule

        preview["dunning_schedule"] = {
            "current": schedule(session, tenant_id)["levels"],
            "proposed": _stated_levels(
                session, tenant_id, normalized_arguments["levels"]
            ),
        }
    if tool_name == DUNNING_RUN_COMMAND:
        from reality.services.dunning_runs import (
            _run_items,
            run_context,
            run_outcome,
        )

        chosen = _run_items(session, tenant_id, normalized_arguments["items"])
        context = run_context(
            session,
            tenant_id,
            run_date=normalized_arguments["run_date"],
            party_ids=normalized_arguments["party_ids"],
        )
        if (
            context["schedule_source_record_id"]
            != normalized_arguments["schedule_source_record_id"]
        ):
            raise InvalidOperation(code="dunning_preview_stale")
        selected, will_skip = run_outcome(session, tenant_id, context, chosen)
        preview["dunning_run"] = {
            "run_date": context["run_date"],
            "notices": [
                {**context["notices"][index], "items": items}
                for index, items in sorted(selected.items())
            ],
            "will_skip": will_skip,
            "not_selected": sorted(
                {
                    item["invoice_id"]
                    for notice in context["notices"]
                    for item in notice["items"]
                }
                - set(chosen)
            ),
        }
    if tool_name == PAYMENT_RETURN_COMMAND:
        from reality.services.payment_returns import preview_return

        preview["payment_return"] = preview_return(
            session, tenant_id, normalized_arguments
        )
    if tool_name == PAYOUT_SETTLE_COMMAND:
        from reality.services.payouts import preview_payout

        preview["payout"] = preview_payout(session, tenant_id, normalized_arguments)
    if tool_name == AUTHORIZATION_RECORD_COMMAND:
        from reality.services.payment_authorizations import preview_authorization

        preview["payment_authorization"] = preview_authorization(
            session, tenant_id, normalized_arguments
        )
    if tool_name == CAPTURE_RECORD_COMMAND:
        from reality.services.payment_authorizations import preview_capture

        preview["payment_capture"] = preview_capture(
            session, tenant_id, normalized_arguments
        )
    if tool_name == COLLECTION_HANDOVER_COMMAND:
        from reality.services.dunning_runs import preview_handover

        preview["collection_handover"] = preview_handover(
            session, tenant_id, normalized_arguments
        )
    if tool_name == DUNNING_REVERSE_COMMAND:
        from reality.services.dunning import notice_detail

        preview["dunning_reversal"] = notice_detail(
            session, tenant_id, normalized_arguments["notice_id"]
        )
    if tool_name == DEPOSIT_CLEAR_COMMAND:
        from reality.services.finance.deposits import preview_clearing

        preview["deposit_clearing"] = preview_clearing(
            session,
            tenant_id,
            **{
                key: normalized_arguments[key]
                for key in (
                    "deposit_document_id",
                    "invoice_id",
                    "amount",
                    "expected_revision",
                )
            },
        )
    if tool_name == DEPOSIT_RECORD_COMMAND:
        preview["deposit"] = {
            key: normalized_arguments[key]
            for key in (
                "side",
                "party_id",
                "amount",
                "currency",
                "reference",
                "effective_at",
            )
        }
    update_families = {
        "party_update": "party",
        "item_update": "item",
        "location_update": "location",
    }
    # reality-rule: application.create_change_proposal.4
    if tool_name in update_families:
        records_preview = preview_master_data_updates(
            session,
            tenant_id,
            update_families[tool_name],
            normalized_arguments["records"],
        )
        normalized_records = []
        for record, record_preview in zip(
            normalized_arguments["records"], records_preview, strict=True
        ):
            normalized_records.append(
                {**record, "expected_revision": record_preview["expected_revision"]}
            )
        normalized_arguments["records"] = normalized_records
        preview = {"records": records_preview}
    # reality-rule: application.create_change_proposal.5
    if tool_name == "movement_correct" and not delivery_review:
        preview = preview_movement_correction(
            session,
            tenant_id,
            normalized_arguments["movement_id"],
            reason=normalized_arguments["reason"],
            replacement=normalized_arguments.get("replacement"),
        )
        normalized_arguments["expected_revision"] = preview["revision"]
        normalized_arguments["preview_fingerprint"] = preview["request_fingerprint"]
    # reality-rule: application.create_change_proposal.6
    if tool_name == "ledger_reverse" and not delivery_review:
        preview = preview_ledger_reversal(
            session,
            tenant_id,
            normalized_arguments["posting_group_id"],
            reason=normalized_arguments["reason"],
        )
        normalized_arguments["expected_revision"] = preview["revision"]
        normalized_arguments["preview_fingerprint"] = preview["request_fingerprint"]
    if tool_name == "company_party_record":
        preview["company_party"] = dict(normalized_arguments)
    if tool_name == "fact_observe":
        preview = {
            "source_record_id": normalized_arguments["source_record_id"],
            "subject_type": normalized_arguments["subject_type"],
            "subject_id": normalized_arguments["subject_id"],
            "predicate": normalized_arguments["predicate"],
            "value": normalized_arguments["value"],
            "observed_at": normalized_arguments["observed_at"],
            "requires_confirmation": True,
        }
    if tool_name in MEMBERSHIP_MUTATION_TOOLS:
        target_key = (
            "email"
            if tool_name == "member_invite"
            else ("membership_id" if tool_name == "member_remove" else "invitation_id")
        )
        target_value = normalized_arguments[target_key]
        if target_key == "email":
            target_value = normalize_email(str(target_value))
            normalized_arguments[target_key] = target_value
        preview = {
            "action": tool_name,
            "company_id": tenant_id,
            "target": {target_key: target_value},
            "requires_confirmation": True,
        }
    if tool_name == "business_journey_proposal_create":
        from reality.services.business_journeys import prepare_proposal

        preview = prepare_proposal(session, **normalized_arguments)
    if tool_name == "business_journey_vote_set":
        from reality.services.business_journeys import prepare_vote

        preview = prepare_vote(
            session,
            None,
            str(normalized_arguments.get("proposal_id", "")),
            active=bool(normalized_arguments.get("active", True)),
        )
    if tool_name == "graph.reports.change":
        from reality.services.analytics.proposals import prepare
        from reality.services.analytics.reports import CALLER

        normalized_arguments, preview = prepare(
            session, tenant_id, CALLER.get(), arguments, report_kind="graph"
        )
    if tool_name == "graph.requests.create":
        from reality.services.analytics.proposals import prepare_request
        from reality.services.analytics.reports import CALLER

        normalized_arguments, preview = prepare_request(
            session, tenant_id, CALLER.get(), arguments
        )
    # reality-rule: application.create_change_proposal.7
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=tenant_id,
        type=f"tool:{tool_name}",
        actor_type=actor_type,
        status="proposed",
        input=json.dumps(normalized_arguments, sort_keys=True),
        output=json.dumps(preview, sort_keys=True, default=str),
    )
    if chat_session_id := CHAT_SESSION.get():
        proposal.chat_session_id = chat_session_id
    if delivery_review:
        proposal.output = json.dumps(_json_value(delivery_review), sort_keys=True)
    session.add(proposal)
    if _commit:
        session.commit()
    else:
        session.flush()
    return proposal


def _proposal(session: Session, tenant_id: str, proposal_id: str) -> ChangeProposal:
    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
            ChangeProposal.status == "proposed",
        )
    )
    if proposal is None:
        raise NotFound("Active tool proposal not found.")
    return proposal


def proposals_awaiting_approval(
    session: Session, tenant_id: str
) -> list[ChangeProposal]:
    return list(
        session.scalars(
            select(ChangeProposal)
            .where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.status == "proposed",
            )
            .order_by(ChangeProposal.created_at)
        )
    )


def _decider_values(
    principal: Principal | None,
    settling_token_id: str | None,
    settling_channel: str | None = None,
) -> dict[str, Any]:
    """Who settled a proposal, as the columns that record it.

    A signed-in person is the strongest statement Reality can make and wins. A
    decision that arrived through MCP names the token that sent it and never a
    person: the token's issuer answers for it, but Reality did not see them decide
    (spec 263 FR-003). A decision with neither, such as one taken through the CLI,
    still records when it happened and leaves the rest unnamed.
    """
    return {
        "decided_at": now(),
        "decided_by_user_id": principal.user_id if principal else None,
        "decided_via_token_id": None if principal else settling_token_id,
        "decided_via_channel": None
        if principal or settling_token_id
        else settling_channel,
    }


#: The attribution a proposal loses when it returns to `proposed`.
UNDECIDED = {
    "decided_at": None,
    "decided_by_user_id": None,
    "decided_via_token_id": None,
    "decided_via_channel": None,
}


def _record_decision(
    proposal: ChangeProposal,
    principal: Principal | None,
    settling_token_id: str | None = None,
    settling_channel: str | None = None,
) -> ChangeProposal:
    """Attribute a settled proposal to the moment and to whoever settled it."""
    for column, value in _decider_values(
        principal, settling_token_id, settling_channel
    ).items():
        setattr(proposal, column, value)
    return proposal


def _undecide(proposal: ChangeProposal) -> None:
    for column, value in UNDECIDED.items():
        setattr(proposal, column, value)


def _finalize_known_no_effect_failure(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    error: InvalidOperation | NotFound,
) -> None:
    """Persist a terminal receipt only when no action-attributed effect survived."""
    session.rollback()
    if session.scalar(
        select(BusinessEvent.id)
        .where(
            BusinessEvent.tenant_id == tenant_id,
            BusinessEvent.action_id == proposal_id,
        )
        .limit(1)
    ):
        # Some legacy handlers commit internally. If a later validation refuses
        # the call, the outcome is not a verified no-effect refusal: retain the
        # durable execution claim so reconciliation can expose the observed effect.
        return
    session.execute(
        update(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
            ChangeProposal.status.in_(("proposed", "executing")),
        )
        .values(
            status="failed",
            output=json.dumps(
                {
                    "business_effect": "none",
                    "error": {
                        # Spec 286: the refusal code where one exists, else the class.
                        "code": error.code
                        if error.coded
                        else (
                            "not_found"
                            if isinstance(error, NotFound)
                            else "invalid_operation"
                        ),
                        "type": type(error).__name__,
                        "message": str(error),
                        **({"values": error.values} if error.coded else {}),
                    },
                    "verification": "verified_no_effect",
                    "safe_next_action": "correct_input_or_prepare_new_proposal",
                },
                sort_keys=True,
            ),
        )
    )
    session.commit()


def approve_and_execute_proposal(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    *,
    confirming_principal: Principal | None = None,
    review_token: str | None = None,
    confirmed: bool = False,
    settling_token_id: str | None = None,
    settling_channel: str | None = None,
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Apply one explicitly authorized prepared proposal through the shared application boundary and retain its execution receipt.

    BUSINESS RULE application.approve_and_execute_proposal.1:
    Require decision authority against the selected proposal's actual tool and input before execution.

    BUSINESS RULE application.approve_and_execute_proposal.2:
    Return the retained receipt for an already executed proposal.

    BUSINESS RULE application.approve_and_execute_proposal.3:
    Refuse an in-progress proposal because its execution outcome may still be unknown.

    BUSINESS RULE application.approve_and_execute_proposal.4:
    When a review is retained, require explicit confirmation and its exact token.

    BUSINESS RULE application.approve_and_execute_proposal.5:
    For finance commands, acquire the shared locks, reread the proposal, execute through the canonical finance dispatcher and commit the execution receipt in the same transaction; retain known-no-effect failures or roll back other failures.

    BUSINESS RULE application.approve_and_execute_proposal.6:
    Atomically claim only a currently proposed company proposal by setting executing and recording decision attribution; only the successful claimant may continue.

    BUSINESS RULE application.approve_and_execute_proposal.7:
    For retained delivery review, acquire the shared delivery lock, recheck authority and unresolved actions, and validate the exact current review; on a known refusal restore proposed state and clear decision attribution.

    BUSINESS RULE application.approve_and_execute_proposal.8:
    After the selected execution path returns, mark the proposal executed, serialize its returned receipt and commit.
    """
    candidate = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
        )
    )
    if candidate is None:
        raise NotFound(code="proposal_not_found")
    authority_policy = resolve_decision_policy(
        candidate.type.removeprefix("tool:"), json.loads(candidate.input)
    )
    # reality-rule: application.approve_and_execute_proposal.1
    require_decision_authority(
        session,
        tenant_id,
        authority_policy,
        confirming_principal,
        phase="preflight",
        confirmed=confirmed,
    )
    if "report_author" in authority_policy.checks:
        from reality.services.analytics.proposals import reveal

        reveal(session, tenant_id, confirming_principal, json.loads(candidate.input))
        if not confirmed:
            from reality.services.analytics.errors import AnalyticsError

            raise AnalyticsError(
                "Explicit confirmation is required for a private report change."
            )
    require_decision_authority(
        session, tenant_id, authority_policy, confirming_principal, phase="locked"
    )
    # reality-rule: application.approve_and_execute_proposal.2
    if candidate.status == "executed":
        return candidate
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_execute")
    # reality-rule: application.approve_and_execute_proposal.3
    if candidate.status == "executing":
        raise InvalidOperation(code="proposal_execution_in_progress")
    if candidate.status == "rejected":
        raise NotFound(code="proposal_active_not_found")
    if candidate.status != "proposed":
        raise InvalidOperation(
            code="proposal_confirm_status_invalid", values={"status": candidate.status}
        )
    tool_name = candidate.type.removeprefix("tool:")
    tool = TOOLS.get(tool_name)
    if tool is None or not tool.mutating:
        raise InvalidOperation(code="proposal_mutation_tool_invalid")
    arguments = json.loads(candidate.input)
    require_decision_authority(
        session, tenant_id, authority_policy, confirming_principal, phase="identity"
    )

    from reality.db.core import Tenant
    from reality.services.delivery_actions import REVIEW_KEY, eligible, validate_review

    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if (
        tenant
        and tenant.purpose != "playground"
        and eligible(tool_name, arguments)
        and REVIEW_KEY not in arguments
        and not (
            tool_name == "movement_create"
            and arguments.get("movement_type") == "opening_stock"
        )
        and tool_name not in {"party_delivery_hold", "party_delivery_hold_release"}
    ):
        raise InvalidOperation(code="delivery_review_required")
    # reality-rule: application.approve_and_execute_proposal.4
    if REVIEW_KEY in arguments and (
        not confirmed or review_token != arguments[REVIEW_KEY]["token"]
    ):
        raise InvalidOperation(code="review_confirmation_required")

    # reality-rule: application.approve_and_execute_proposal.5
    if tool_name in FINANCE_COMMANDS:
        require_decision_authority(
            session,
            tenant_id,
            authority_policy,
            confirming_principal,
            phase="execution",
        )
        try:
            if tool_name in {
                ADJUSTMENT_COMMAND,
                SETTLEMENT_COMMAND,
                OPENING_COMMAND,
                ASSIGNMENT_COMMAND,
                "cost.change",
            }:
                from reality.services.business_locks import lock_delivery_state

                lock_delivery_state(session, tenant_id)
            lock_finance(session, tenant_id)
            proposal = session.scalar(
                select(ChangeProposal)
                .where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.id == proposal_id,
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if proposal.status == "executed":
                return proposal
            if proposal.status != "proposed":
                raise InvalidOperation(code="proposal_no_longer_available")
            with executing_proposal(tenant_id, proposal.id):
                result = execute_finance_command(
                    session,
                    tenant_id,
                    tool_name,
                    arguments,
                    action_id=proposal.id,
                    actor_id=(
                        confirming_principal.user_id if confirming_principal else None
                    ),
                )
            proposal.status = "executed"
            _record_decision(
                proposal, confirming_principal, settling_token_id, settling_channel
            )
            proposal.output = json.dumps(_json_value(result), sort_keys=True)
            session.commit()
            return proposal
        except (InvalidOperation, NotFound) as error:
            _finalize_known_no_effect_failure(session, tenant_id, proposal_id, error)
            raise
        except Exception:
            session.rollback()
            raise

    # reality-rule: application.approve_and_execute_proposal.6
    claimed_id = session.scalar(
        update(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
            ChangeProposal.status == "proposed",
        )
        .values(
            status="executing",
            **_decider_values(
                confirming_principal, settling_token_id, settling_channel
            ),
        )
        .returning(ChangeProposal.id)
    )
    session.commit()
    if claimed_id is None:
        proposal = session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id == proposal_id,
            )
        )
        if proposal is None:
            raise NotFound(code="proposal_not_found")
        if proposal.status == "executed":
            return proposal
        if proposal.status == "executing":
            raise InvalidOperation(code="proposal_execution_in_progress")
        raise InvalidOperation(
            code="proposal_confirm_status_invalid", values={"status": proposal.status}
        )
    proposal = session.get(ChangeProposal, {"tenant_id": tenant_id, "id": claimed_id})
    # reality-rule: application.approve_and_execute_proposal.7
    if REVIEW_KEY in arguments:
        from reality.services.business_locks import lock_delivery_state

        try:
            lock_delivery_state(session, tenant_id)
            require_decision_authority(
                session,
                tenant_id,
                authority_policy,
                confirming_principal,
                phase="locked",
            )
            from reality.services.delivery_actions import assert_no_unresolved_action

            assert_no_unresolved_action(
                session, tenant_id, tool_name, arguments, exclude=proposal.id
            )
            arguments = validate_review(
                session, tenant_id, tool_name, arguments, review_token, confirmed
            )
        except (InvalidOperation, NotFound):
            # The handler has not been called: restoring review cannot replay an effect.
            proposal.status = "proposed"
            _undecide(proposal)
            session.commit()
            raise
    if tool_name in REFERENCE_MUTATION_TOOLS:
        from reality.services.business_locks import lock_delivery_state
        from reality.services.core import _assert_update_revision

        try:
            lock_delivery_state(session, tenant_id)
            session.expire_all()
            if tenant and tenant.purpose != "playground":
                require_decision_authority(
                    session,
                    tenant_id,
                    authority_policy,
                    confirming_principal,
                    phase="reference",
                )
            if tool_name.endswith("_update"):
                for record in arguments["records"]:
                    _assert_update_revision(
                        session, tenant_id, tool_name.removesuffix("_update"), record
                    )
        except (InvalidOperation, NotFound):
            # No handler ran, so a stale review can safely remain proposed.
            proposal.status = "proposed"
            _undecide(proposal)
            session.commit()
            raise
    if tool_name in {
        "party_update",
        "item_update",
        "location_update",
        "fact_observe",
        "reserve",
        "movement_create",
        "movement_correct",
        "reservation_release",
        "party_delivery_hold",
        "party_delivery_hold_release",
        "commitment_hold",
        "commitment_hold_release",
        "party_create",
        "item_create",
        "location_create",
        "order_create",
        "customer_payment_post",
        "sales_invoice_record",
        "supplier_payment_post",
        "supplier_invoice_record",
        "supplier_invoice_free_record",
        "supply_assign",
        "return_disposition",
        "customer_exchange_record",
        "shipment_delivery_failure",
        "drop_shipment_record",
        "order_line_item_assign",
        "credit_hold_release",
        "reorder_point_set",
        "reorder_point_remove",
        "kit_define",
        "kit_assemble",
        "party_merge",
        "commitment_substitute_accept",
        "stock_block",
        "stock_block_release",
        "stock_block_scrap",
        "backorders_serve",
        "delivery_rule_set",
        "stock_count",
        "external_stock_state",
        "outbound_delivery_plan",
        "outbound_delivery_revise",
        "outbound_delivery_pick",
        "outbound_delivery_put_back",
        "customer_item_number_set",
        "customer_item_number_remove",
        "supplier_item_terms_set",
        "supplier_item_terms_remove",
        "company_currency_set",
        "down_payment_invoice_record",
        "proforma_invoice_record",
        "commitment_revise",
        "commitment_cancel",
        "sales_credit_record",
        "customer_refund_post",
        "ledger_reverse",
        "shipment_notice_record",
        "shipment_dispatch",
        "shipment_receive",
        "shipment_event_record",
        "shipment_event_supersede",
    }:
        arguments["_action_id"] = proposal.id
    if tool_name in ACCOUNT_MUTATION_TOOLS:
        arguments["_confirming_user_id"] = confirming_principal.user_id
    from reality.playground.actions import MASTER_TOOLS
    from reality.services.tenant_policy import master_tool_execution

    if "request_author" in authority_policy.checks:
        from reality.services.analytics.proposals import execute_request

        with executing_proposal(tenant_id, proposal.id):
            result = execute_request(
                session, tenant_id, confirming_principal, arguments
            )
    elif "report_author" in authority_policy.checks:
        from reality.services.analytics.proposals import execute_change

        try:
            with executing_proposal(tenant_id, proposal.id):
                result = execute_change(
                    session, tenant_id, confirming_principal, arguments
                )
        except (InvalidOperation, NotFound):
            # A refused save wrote nothing, so the outcome is known, not unknown.
            # Leaving the claim in place would strand the proposal: every further
            # confirmation would answer "execution is in progress" and the reader
            # would never learn that a retry key was reused or a revision moved on.
            session.rollback()
            session.execute(
                update(ChangeProposal)
                .where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.id == proposal_id,
                    ChangeProposal.status == "executing",
                )
                .values(status="proposed", **UNDECIDED)
            )
            session.commit()
            raise
    elif tool_name in MASTER_TOOLS:
        with (
            master_tool_execution(session, tenant_id, tool_name, arguments),
            executing_proposal(tenant_id, proposal.id),
        ):
            result = tool.handler(session, tenant_id, arguments)
    else:
        try:
            with executing_proposal(tenant_id, proposal.id):
                result = tool.handler(session, tenant_id, arguments)
        except (InvalidOperation, NotFound) as error:
            # A synchronous domain refusal from a reviewed application handler is a
            # known no-effect outcome: the handler did not return and its current
            # transaction is rolled back. Retain that terminal fact instead of
            # stranding the action in `executing` or making rejected input retryable.
            # Unexpected exceptions still leave the durable execution claim intact.
            _finalize_known_no_effect_failure(session, tenant_id, proposal_id, error)
            raise
    # reality-rule: application.approve_and_execute_proposal.8
    proposal.status = "executed"
    proposal.output = json.dumps(_json_value(result), sort_keys=True)
    session.commit()
    return proposal


def reject_proposal(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    *,
    confirming_principal: Principal | None = None,
    settling_token_id: str | None = None,
    settling_channel: str | None = None,
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Reject one prepared company proposal without executing its business mutation.

    BUSINESS RULE application.reject_proposal.1:
    Return an already rejected proposal unchanged.

    BUSINESS RULE application.reject_proposal.2:
    Refuse rejection of a proposal in any other state.

    BUSINESS RULE application.reject_proposal.3:
    After shared decision-policy validation, record rejected state and decision attribution and commit.
    """
    existing = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
        )
    )
    if existing is None:
        raise NotFound(code="proposal_not_found")
    # reality-rule: application.reject_proposal.1
    if existing.status == "rejected":
        return existing
    # reality-rule: application.reject_proposal.2
    if existing.status != "proposed":
        raise InvalidOperation(
            code="proposal_reject_status_invalid", values={"status": existing.status}
        )
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_reject")
    proposal = existing
    # reality-rule: application.reject_proposal.3
    proposal.status = "rejected"
    _record_decision(
        proposal, confirming_principal, settling_token_id, settling_channel
    )
    session.commit()
    return proposal


# Storyline mode (spec 182, FR-004): every read, proposal, confirmation and
# rejection in a company that belongs to a storyline run leaves a trace entry. The
# wrappers are inert for every other tenant.
from reality.storyline import recorder as _storyline_recorder

run_read_tool = _storyline_recorder.wrap_read(run_read_tool)
create_change_proposal = _storyline_recorder.wrap_propose(create_change_proposal)
approve_and_execute_proposal = _storyline_recorder.wrap_decision(
    approve_and_execute_proposal, "confirm"
)
reject_proposal = _storyline_recorder.wrap_decision(reject_proposal, "reject")

# The engine room (spec 266): the tool layer tells the open interaction what it
# did. It opens one itself only where no boundary is above it (the CLI).
from reality.services import interaction_recorder as _interactions


def _observed_read(function):
    def run_read_tool(session, tenant_id, tool_name, arguments=None):
        with _interactions.tool_boundary(tenant_id, tool_name):
            result = function(session, tenant_id, tool_name, arguments)
            _interactions.note_result(result)
            return result

    run_read_tool.__wrapped__ = function  # type: ignore[attr-defined]
    return run_read_tool


def _observed_proposal(function):
    def create_change_proposal(session, tenant_id, tool_name, arguments, **kwargs):
        with _interactions.tool_boundary(tenant_id, tool_name):
            _interactions.note_kind("propose")
            proposal = function(session, tenant_id, tool_name, arguments, **kwargs)
            _interactions.note_proposal(
                getattr(proposal, "id", None), getattr(proposal, "status", None)
            )
            return proposal

    create_change_proposal.__wrapped__ = function  # type: ignore[attr-defined]
    return create_change_proposal


def _observed_decision(function, name):
    def decide(session, tenant_id, proposal_id, **kwargs):
        with _interactions.tool_boundary(tenant_id, name):
            _interactions.note_kind("decide")
            _interactions.note_proposal(proposal_id, None)
            result = function(session, tenant_id, proposal_id, **kwargs)
            _interactions.note_proposal(
                proposal_id, getattr(result, "status", None) or "decided"
            )
            return result

    decide.__name__ = function.__name__
    decide.__wrapped__ = function  # type: ignore[attr-defined]
    return decide


run_read_tool = _observed_read(run_read_tool)
create_change_proposal = _observed_proposal(create_change_proposal)
approve_and_execute_proposal = _observed_decision(
    approve_and_execute_proposal, "proposal.approve"
)
reject_proposal = _observed_decision(reject_proposal, "proposal.reject")

# Compatibility aliases for adapters migrating from the previous terminology.
propose_tool = create_change_proposal
proposed_tools = proposals_awaiting_approval
confirm_tool = approve_and_execute_proposal
reject_tool = reject_proposal


def _source_mappings_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read exact source-code mappings and available references.

    BUSINESS RULE application.source_mappings_read.1:
    Route this company-scoped request to list_source_mappings. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.source_mappings import list_source_mappings

    # reality-rule: application.source_mappings_read.1
    return list_source_mappings(session, tenant_id, **arguments)


def _source_mapping_history_read(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Read source classification revision history.

    BUSINESS RULE application.source_mapping_history_read.1:
    Route this company-scoped request to source_mapping_history. The called implementation owns validation, selection and any business effects; this adapter returns its evidence rather than calculating an alternative result.
    """
    from reality.services.finance.source_mappings import source_mapping_history

    # reality-rule: application.source_mapping_history_read.1
    return source_mapping_history(session, tenant_id, **arguments)


TOOLS["finance.source_mappings.list"] = Tool(
    "finance.source_mappings.list",
    "Read exact source-code mappings and available references.",
    False,
    _source_mappings_read,
)
TOOLS["finance.source_mappings.history"] = Tool(
    "finance.source_mappings.history",
    "Read source classification revision history.",
    False,
    _source_mapping_history_read,
)

from reality.services.finance import target_mappings as _target_mapping_services

for _name, _handler in {
    "finance.targets.list": _target_mapping_services.list_targets,
    "finance.target_references.list": _target_mapping_services.list_target_references,
    "finance.target_mappings.list": _target_mapping_services.list_mappings,
    "finance.target_mappings.history": _target_mapping_services.mapping_history,
    "finance.target_mappings.preview": _target_mapping_services.preview_document,
}.items():

    def _target_read(session, tenant_id, arguments, handler=_handler):
        """
        BUSINESS PURPOSE:
        Read Finance target configuration or mapping resolution without changing financial evidence.

        BUSINESS RULE application.target_read.1:
        Invoke the exact target-configuration service captured when this adapter was registered, forwarding the company and supplied arguments; no financial evidence is changed by this read.
        """
        # reality-rule: application.target_read.1
        return handler(session, tenant_id, **arguments)

    TOOLS[_name] = Tool(
        _name,
        "Read Finance target configuration or mapping resolution without changing financial evidence.",
        False,
        _target_read,
    )


# The reporting graph shares the same dispatcher shape: discover what can be asked,
# then ask it. A refusal carries its stable code out through the same path.
from reality.tools.graph import SCHEMAS as GRAPH_SCHEMAS
from reality.tools.graph import invoke as invoke_graph

_GRAPH_DESCRIPTIONS = {
    "graph.company_generation.current": "Read the verified currently published company cost generation metadata for explicit fixed analysis selection; no values are calculated.",
    "graph.captured_reports.list": "List sealed captured report generations for explicit fixed analysis selection; no financial approval is implied.",
    "graph.contribution_reviews.list": "List retained joint contribution confirmations for explicit historical report selection; no cache readiness or value is implied.",
    "graph.inventory_reviews.list": "List retained joint inventory confirmations for explicit historical report selection; no cache readiness or value is implied.",
    "graph.format": "Format a checked graph question as an editable path with parameters.",
    "graph.interpret": "Interpret a business question with the configured AI provider and existing usage allowance; does not execute it.",
    "graph.templates": "List the questions worth starting from, each one already checked against the model.",
    "graph.catalog": "Discover the business nodes, how they connect, and what each measure means.",
    "graph.ask": "Ask the reporting graph a question along declared edges and measures.",
    "graph.reports.list": "List the caller's own saved graph reports.",
    "graph.reports.get": "Open one of the caller's own saved graph reports.",
    "graph.requests.list": "List the caller's own requested analyses and where each one stands.",
    "graph.requests.get": "Collect a requested analysis, with the question and the moment it was answered.",
}

for _graph_name in GRAPH_SCHEMAS:

    def _graph_read(session, tenant_id, arguments, name=_graph_name):
        """
        BUSINESS PURPOSE:
        Route the selected registered analysis operation to its shared graph implementation.

        BUSINESS RULE application.graph_read.route:
        Pass the current company, supplied arguments and the operation name bound by this registration to invoke_graph. The selected implementation determines the data and result; this shared adapter does not supply a second set of analysis rules.
        """
        # reality-rule: application.graph_read.route
        return invoke_graph(session, tenant_id, name, arguments)

    TOOLS[_graph_name] = Tool(
        _graph_name,
        _GRAPH_DESCRIPTIONS[_graph_name],
        False,
        _graph_read,
    )


def _private_report_confirmation_only(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Propose saving, renaming or removing a private graph report for its author.

    BUSINESS RULE application.private_report_confirmation_only.1:
    Refuse direct invocation: this operation is available only through the authenticated confirmed-proposal execution path.
    """
    # reality-rule: application.private_report_confirmation_only.1
    raise InvalidOperation(
        "Private report changes require an authenticated proposal confirmation."
    )


TOOLS["graph.reports.change"] = Tool(
    "graph.reports.change",
    "Propose saving, renaming or removing a private graph report for its author.",
    True,
    _private_report_confirmation_only,
)


def _requested_analysis_confirmation_only(session, tenant_id, arguments):
    """
    BUSINESS PURPOSE:
    Propose asking an analysis question, answered now or by the worker.

    BUSINESS RULE application.requested_analysis_confirmation_only.1:
    Refuse direct invocation: this operation is available only through the authenticated confirmed-proposal execution path.
    """
    # reality-rule: application.requested_analysis_confirmation_only.1
    raise InvalidOperation(
        "Requesting an analysis requires an authenticated proposal confirmation."
    )


TOOLS["graph.requests.create"] = Tool(
    "graph.requests.create",
    "Propose asking an analysis question, answered now or by the worker.",
    True,
    _requested_analysis_confirmation_only,
)
