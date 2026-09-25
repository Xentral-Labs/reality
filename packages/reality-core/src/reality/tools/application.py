from __future__ import annotations

import json
from collections.abc import Callable
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
MEMBERSHIP_MUTATION_TOOLS = {
    "member_invite",
    "invitation_resend",
    "invitation_revoke",
    "member_remove",
}


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
        raise InvalidOperation("Membership changes require a confirming human owner.")
    return Principal(user_id)


def _member_invite(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
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
    revoke_invitation(
        session,
        tenant_id,
        _human_principal(arguments),
        str(arguments["invitation_id"]),
    )
    return {"status": "revoked", "invitation_id": arguments["invitation_id"]}


def _member_remove(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
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
    return _projection_read(session, tenant_id, INVENTORY, arguments)


def _exceptions(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return operational_exception_rows(session, tenant_id)


def _exception_explain(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return explain_operational_exception(session, tenant_id, arguments["exception_id"])


def _interpretation_coverage(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return interpretation_coverage(
        session, tenant_id, arguments.get("source_record_id")
    )


def _commitments(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return _projection_read(session, tenant_id, COMMITMENT_REGISTER, arguments)


def _finance_balances(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.read_contracts import finance_balances

    return finance_balances(session, tenant_id)


def _dunning_context(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.dunning import dunning_context

    return dunning_context(session, tenant_id, arguments)


def _dunning_notices(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    del arguments
    from reality.services.dunning import notices

    return notices(session, tenant_id)


def _dunning_notice(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    from reality.services.dunning import notice_detail

    return notice_detail(session, tenant_id, arguments["notice_id"])


def _fulfillment_queue(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _projection_read(session, tenant_id, FULFILLMENT_QUEUE, arguments)


def _fulfillment_blockers(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _projection_read(session, tenant_id, FULFILLMENT_BLOCKERS, arguments)


def _item_supply_demand(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _projection_read(session, tenant_id, ITEM_SUPPLY_DEMAND, arguments)


def _order_explain(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return explain_order_projection(session, tenant_id, arguments["order_reference"])


def _shipments_list(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return shipments_list(session, tenant_id, **arguments)


def _shipment_explain(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return shipment_explain(session, tenant_id, arguments["shipment_id"])


def _shipment_notice_record(session, tenant_id, arguments):
    values = dict(arguments)
    values["action_id"] = values.pop("_action_id", None)
    shipment, package, event = record_shipment_notice(session, tenant_id, **values)
    return {"shipment_id": shipment.id, "package_id": package.id, "event_id": event.id}


def _shipment_execution(direction: str):
    def handler(session, tenant_id, arguments):
        values = dict(arguments)
        values["direction"] = direction
        values["action_id"] = values.pop("_action_id", None)
        return record_packaged_execution(session, tenant_id, **values)

    return handler


def _shipment_event_record(session, tenant_id, arguments):
    values = dict(arguments)
    values["action_id"] = values.pop("_action_id", None)
    event = record_shipment_event(session, tenant_id, **values)
    return {"shipment_id": event.shipment_id, "event_id": event.id}


def _shipment_event_supersede(session, tenant_id, arguments):
    values = dict(arguments)
    values["action_id"] = values.pop("_action_id", None)
    correction = supersede_shipment_event(session, tenant_id, **values)
    return {
        "event_id": correction.superseded_event_id,
        "supersession_id": correction.id,
    }


def _reserve(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    result = reserve(
        session,
        tenant_id,
        arguments["commitment_id"],
        arguments.get("quantity"),
        handling_unit_id=arguments.get("handling_unit_id"),
        lot_id=arguments.get("lot_id"),
        serial_unit_id=arguments.get("serial_unit_id"),
        action_id=arguments.get("_action_id"),
    )
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
    tenant = get_tenant(session, tenant_id)
    ensure_demo(session, tenant)
    return {"tenant_id": tenant.id, "result": "demo_ready"}


def _normal_month(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return run_normal_month(session, tenant_id)


def _source_ingest(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
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


def _item_create(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
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
    return gap_detail(session, tenant_id, str(arguments["gap_id"]))


def _reality_gap_simulate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return simulate_rule(
        session,
        tenant_id,
        str(arguments["rule_id"]),
        limit=int(arguments.get("limit", 100)),
    )


def _reality_gap_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    gap = capture_gap(
        session,
        tenant_id,
        **{key: value for key, value in arguments.items() if not key.startswith("_")},
    )
    return {"gap_id": gap.id, "status": gap.status, "revision": gap.revision}


def _reality_gap_entry_add(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
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
    rule = activate_rule(session, tenant_id, str(arguments["rule_id"]))
    return {"rule_id": rule.id, "status": rule.status}


def _reality_gap_disable(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    rule = disable_rule(session, tenant_id, str(arguments["rule_id"]))
    return {"rule_id": rule.id, "status": rule.status}


def _reality_gap_replay(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return replay_rule(
        session,
        tenant_id,
        str(arguments["rule_id"]),
        source_ids=arguments.get("source_ids"),
        limit=int(arguments.get("limit", 500)),
        cursor=arguments.get("cursor"),
    )


def _discover(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
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
    arguments = dict(arguments)
    arguments["action_id"] = arguments.pop("_action_id", None)
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
    return _entity_result(
        "document", correct_manual_document(session, tenant_id, **arguments)
    )


def _document_source_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    source, job = record_corrected_document_source(session, tenant_id, **arguments)
    return {
        "source_record_id": source.id,
        "import_job_id": job.id,
        "status": job.status,
    }


def _document_lines_correct(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return correct_manual_document_lines(session, tenant_id, **arguments)


def _handling_unit_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "handling_unit", create_handling_unit(session, tenant_id, **arguments)
    )


def _lot_create(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return _entity_result("lot", create_lot(session, tenant_id, **arguments))


def _lot_expiry_state(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
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
    arguments["action_id"] = arguments.pop("_action_id", None)
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
    return _entity_result("lot", expired_lots(session, tenant_id))


def _serial_unit_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "serial_unit", create_serial_unit(session, tenant_id, **arguments)
    )


def _movement_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments = dict(arguments)
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("occurred_at") is not None:
        arguments["occurred_at"] = utc_datetime(arguments["occurred_at"])
    return _entity_result("movement", record_movement(session, tenant_id, **arguments))


def _movement_explanation(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.movement_explanations import movement_explanation

    return movement_explanation(session, tenant_id, arguments["movement_id"])


def _reservation_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments = dict(arguments)
    arguments["action_id"] = arguments.pop("_action_id", None)
    return _entity_result(
        "reservation", release_reservation(session, tenant_id, **arguments)
    )


def _commitment_hold(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    return _entity_result(
        "commitment_hold", hold_commitment(session, tenant_id, **arguments)
    )


def _commitment_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    return _entity_result(
        "commitment_hold", release_commitment_hold(session, tenant_id, **arguments)
    )


def _document_hold(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    return _entity_result(
        "commitment_hold", hold_document_commitments(session, tenant_id, **arguments)
    )


def _document_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "commitment_hold", release_document_holds(session, tenant_id, **arguments)
    )


def _party_hold(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    return _entity_result(
        "party_hold", hold_party_delivery(session, tenant_id, **arguments)
    )


def _party_hold_release(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments = dict(arguments)
    if "_action_id" in arguments:
        arguments["action_id"] = arguments.pop("_action_id")
    return _entity_result(
        "party_hold", release_party_delivery_hold(session, tenant_id, **arguments)
    )


def _lifecycle(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    models = {
        "party": Party,
        "item": Item,
        "location": Location,
        "payment_term": PaymentTerm,
    }
    model_name = str(arguments.pop("model"))
    model = models.get(model_name)
    if model is None:
        raise InvalidOperation("Unsupported master data type.")
    return _entity_result(
        model_name, set_master_data_active(session, tenant_id, model, **arguments)
    )


def _payment_term_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "payment_term", create_payment_term(session, tenant_id, **arguments)
    )


def _payment_term_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "payment_term", update_payment_term(session, tenant_id, **arguments)
    )


def _price_list_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "price_list", create_price_list(session, tenant_id, **arguments)
    )


def _price_list_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "price_list", update_price_list(session, tenant_id, **arguments)
    )


def _price_tier_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "price_list_entry", create_price_list_entry(session, tenant_id, **arguments)
    )


def _party_price_list_assign(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "party_price_list", assign_party_price_list(session, tenant_id, **arguments)
    )


def _party_group_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "party_group", create_party_group(session, tenant_id, **arguments)
    )


def _party_group_update(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "party_group", update_party_group(session, tenant_id, **arguments)
    )


def _source_record_ingest(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    source, job = enqueue_source(session, tenant_id, **arguments)
    return {
        "source_record_id": source.id,
        "import_job_id": job.id,
        "status": job.status,
    }


def _party_group_member_add(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "party_group_member", add_party_group_member(session, tenant_id, **arguments)
    )


def _group_price_list_assign(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "party_group_price_list",
        assign_group_price_list(session, tenant_id, **arguments),
    )


def _sales_invoice_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return record_sales_invoice(session, tenant_id, **arguments)


def _supplier_invoice_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return record_supplier_invoice(session, tenant_id, **arguments)


def _supply_assign(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    action_id = arguments.pop("_action_id", None)
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
    return supply_coverage(session, tenant_id, **arguments)


def _return_disposition(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
    row = record_return_disposition(session, tenant_id, **arguments)
    return {"movement_id": row.id, "source_record_id": row.source_record_id}


def _return_disposition_summary(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.delivery_reads import return_disposition_case

    return return_disposition_case(session, tenant_id, **arguments)


def _sales_credit_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return record_sales_credit(session, tenant_id, **arguments)


def _invoice_credit_context(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.credit_actions import invoice_credit_context

    return invoice_credit_context(session, tenant_id, arguments["invoice_id"])


def _supplier_invoice_free_record(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.services.invoice_actions import record_free_supplier_invoice

    arguments["action_id"] = arguments.pop("_action_id", None)
    return record_free_supplier_invoice(session, tenant_id, **arguments)


def _payment(kind: str) -> ToolHandler:
    service = post_customer_payment if kind == "customer" else post_supplier_payment

    def handler(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
        arguments["action_id"] = arguments.pop("_action_id", None)
        if arguments.get("effective_at") is not None:
            arguments["effective_at"] = utc_datetime(arguments["effective_at"])
        return _entity_result("ledger_entry", service(session, tenant_id, **arguments))

    return handler


def _return_announce(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
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
    arguments["action_id"] = arguments.pop("_action_id", None)
    return withdraw_return_announcement(
        session,
        tenant_id,
        arguments["announcement_id"],
        note=arguments.get("note", "") or "",
    )


def _return_announcements(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
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
    return preview_payment_run(
        session, tenant_id, pay_by=utc_datetime(arguments["pay_by"])
    )


def _payment_run(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
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
    return preview_stale_promise_closure(
        session,
        tenant_id,
        direction=arguments["direction"],
        due_before=utc_datetime(arguments["due_before"]),
    )


def _stale_closure(session: Session, tenant_id: str, arguments: dict[str, Any]) -> Any:
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
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return _posting_result(post_sales_invoice(session, tenant_id, **arguments))


def _supplier_invoice_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return _posting_result(post_supplier_invoice(session, tenant_id, **arguments))


def _document_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
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
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return _posting_result(post_sales_credit_note(session, tenant_id, **arguments))


def _credit_note_allocate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "settlement_allocation", allocate_credit_note(session, tenant_id, **arguments)
    )


def _customer_refund_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return _entity_result(
        "ledger_entry", post_customer_refund(session, tenant_id, **arguments)
    )


def _supplier_credit_note_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return _posting_result(post_supplier_credit_note(session, tenant_id, **arguments))


def _supplier_credit_note_allocate(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "settlement_allocation",
        allocate_supplier_credit_note(session, tenant_id, **arguments),
    )


def _supplier_refund_post(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    if arguments.get("effective_at") is not None:
        arguments["effective_at"] = utc_datetime(arguments["effective_at"])
    return _entity_result(
        "ledger_entry", post_supplier_refund(session, tenant_id, **arguments)
    )


def _commitment_revise(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    arguments["action_id"] = arguments.pop("_action_id", None)
    for field in ("due_at", "stated_at"):
        if arguments.get(field) is not None:
            arguments[field] = utc_datetime(arguments[field])
    return _entity_result(
        "commitment_revision", revise_commitment(session, tenant_id, **arguments)
    )


def _commitment_cancel(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    from reality.db.core import BusinessEvent
    from reality.services.core import cancel_commitment

    action_id = arguments.pop("_action_id", None)
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
    return _entity_result(
        "source_system", create_source_system(session, tenant_id, **arguments)
    )


def _connector_install(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "source_system", install_connector_shell(session, tenant_id, **arguments)
    )


def _source_system_lifecycle(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "source_system", set_source_system_active(session, tenant_id, **arguments)
    )


def _source_capability_create(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "source_capability", create_source_capability(session, tenant_id, **arguments)
    )


def _source_capability_lifecycle(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    return _entity_result(
        "source_capability",
        set_source_capability_active(session, tenant_id, **arguments),
    )


def _capability_describe(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    del session, tenant_id
    from reality.catalogs import load_application_catalog

    requested_name = str(arguments.get("tool_name", "")).strip()
    catalog = load_application_catalog()["capability_guidance"]
    canonical_name = requested_name if requested_name in catalog else ""
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
    guidance = catalog.get(canonical_name)
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
    if guidance is None:
        raise NotFound("Capability not found.")
    return {"canonical_public_name": canonical_name, **guidance}


def _capability_catalog(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    """Answer the topic index, or one topic's capabilities (spec 270)."""
    from reality.services.capability_catalog import topic_capabilities, topic_index

    topic = str(arguments.get("topic") or "").strip()
    if not topic:
        return topic_index(session, tenant_id)
    return topic_capabilities(session, tenant_id, topic)


def _proposals_awaiting_approval(
    session: Session, tenant_id: str, arguments: dict[str, Any]
) -> Any:
    del arguments
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
        or movement.source_record_id is not None
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
    """The receipt and reconciliation of one proposal, with who settled it."""
    from reality.services.decision_attribution import decision_attributions

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
            "observation": detail["observation"],
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


TOOLS = {
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
    "fulfillment_queue": Tool(
        "fulfillment_queue",
        "Read the materialized order fulfillment queue.",
        False,
        _fulfillment_queue,
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
        "Record that a counterparty now states a different date or quantity.",
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
    tool = TOOLS.get(tool_name)
    if tool is None:
        raise NotFound("Tool not found.")
    if tool.mutating:
        raise InvalidOperation("Mutating tools require a confirmed proposal.")
    return _json_value(tool.handler(session, tenant_id, arguments or {}))


# Finance account writes are dispatched only inside confirmed atomic execution.
from reality.services.finance.accounts import list_accounts, lock_finance
from reality.tools.finance import (
    ADJUSTMENT_COMMAND,
    ASSIGNMENT_COMMAND,
    DEPOSIT_CLEAR_COMMAND,
    DEPOSIT_RECORD_COMMAND,
    DUNNING_COMMAND,
    DUNNING_REVERSE_COMMAND,
    FINANCE_COMMANDS,
    OPENING_COMMAND,
    REFERENCE_COMMANDS,
    SETTLEMENT_COMMAND,
    SOURCE_MAPPING_COMMAND,
    execute_finance_command,
    validate_finance_request,
)


def _confirmed_account_only(session, tenant_id, arguments):
    raise InvalidOperation("Finance changes require a confirmed proposal.")


def _adjustment_context_read(session, tenant_id, arguments):
    from reality.services.finance.settlement import adjustment_context

    return adjustment_context(session, tenant_id, arguments["invoice_id"])


def _settlement_context_read(session, tenant_id, arguments):
    from reality.services.finance.settlement_flows import settlement_context

    return settlement_context(session, tenant_id, **arguments)


def _credits_read(session, tenant_id, arguments):
    """Available customer or supplier credit: original payments and credit notes not yet used (feature 169)."""
    from reality.services.finance.credits import available_credit_items

    side = str(arguments.get("side") or "customer")
    status = str(arguments.get("status") or "outstanding")
    limit = max(1, min(int(arguments.get("limit") or 50), 200))
    page = available_credit_items(
        session,
        tenant_id,
        side=side,
        query=str(arguments.get("query") or ""),
        status=status,
        page=1,
        size=limit,
    )
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
    """Where each customer or supplier stands: open, overdue, credit, balance (feature 170)."""
    from reality.services.finance.balances import party_balances

    side = str(arguments.get("side") or "customer")
    limit = max(1, min(int(arguments.get("limit") or 50), 200))
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
    """Recorded payments with allocated and unallocated amounts (feature 169)."""
    from reality.services.core import payment_rows

    supported_arguments = {"direction", "only_unallocated", "query", "limit"}
    unsupported_arguments = sorted(set(arguments) - supported_arguments)
    if unsupported_arguments:
        raise InvalidOperation(
            "Unsupported payment filter: " + ", ".join(unsupported_arguments) + "."
        )
    raw_direction = arguments.get("direction")
    direction = str(raw_direction) if raw_direction is not None else ""
    if raw_direction is not None and direction not in {"incoming", "outgoing"}:
        raise InvalidOperation("Payment direction must be incoming or outgoing.")
    only_unallocated = bool(arguments.get("only_unallocated") or False)
    query = str(arguments.get("query") or "").strip().lower()
    limit = max(1, min(int(arguments.get("limit") or 50), 200))
    items = []
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
    from reality.services.finance.opening import opening_context

    return opening_context(session, tenant_id, **arguments)


def _reference_list_read(session, tenant_id, arguments):
    from reality.services.finance.references import list_references

    return list_references(session, tenant_id, **arguments)


def _reference_history_read(session, tenant_id, arguments):
    from reality.services.finance.references import reference_history

    return reference_history(session, tenant_id, **arguments)


def _component_context_read(session, tenant_id, arguments):
    from reality.services.finance.components import component_context

    return component_context(session, tenant_id, **arguments)


def _component_history_read(session, tenant_id, arguments):
    from reality.services.finance.components import component_history

    return component_history(session, tenant_id, **arguments)


def _matrix_read(session, tenant_id, arguments):
    from reality.services.finance.accounts import transaction_matrix

    if arguments:
        raise InvalidOperation("Transaction matrix takes no business arguments.")
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
TOOLS["finance.accounts.list"] = Tool(
    "finance.accounts.list",
    "Read permitted operational accounts and defaults.",
    False,
    lambda session, tenant_id, arguments: list_accounts(session, tenant_id),
)
from reality.tools.costing import commercial_match as _commercial_match_tool
from reality.tools.costing import contribution as _contribution_preview_tool
from reality.tools.costing import evidence as _cost_evidence_tool
from reality.tools.costing import inventory as _inventory_cost_tool
from reality.tools.costing import query as _cost_query_tool
from reality.tools.costing import receipt as _receipt_cost_tool
from reality.tools.costing import record as _cost_record_tool
from reality.tools.costing import reviewed_contribution as _reviewed_contribution_tool

TOOLS["cost.query.get"] = Tool(
    "cost.query.get",
    "Read an exact retained cost answer with constrained cutoffs, scope and freshness.",
    False,
    _cost_query_tool,
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


def create_change_proposal(
    session: Session,
    tenant_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    actor_type: str = "agent",
    _commit: bool = True,
) -> ChangeProposal:
    require_proposal_creation(session, tenant_id, tool_name, arguments)
    tool = TOOLS.get(tool_name)
    if tool is None:
        raise NotFound("Tool not found.")
    if not tool.mutating:
        raise InvalidOperation("Read tools do not need a proposal.")
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
    if tool_name in FINANCE_COMMANDS:
        normalized_arguments = validate_finance_request(tool_name, arguments)
    if delivery_review:
        normalized_arguments = {
            **delivery_review["intent"],
            REVIEW_KEY: delivery_review,
        }
    preview: dict[str, Any] = {
        "tool": tool_name,
        "arguments": _json_value(normalized_arguments),
        "effect": tool.description,
        "requires_human_confirmation": True,
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
    if tool_name == "ledger_reverse" and not delivery_review:
        preview = preview_ledger_reversal(
            session,
            tenant_id,
            normalized_arguments["posting_group_id"],
            reason=normalized_arguments["reason"],
        )
        normalized_arguments["expected_revision"] = preview["revision"]
        normalized_arguments["preview_fingerprint"] = preview["request_fingerprint"]
    if tool_name == "fact_observe":
        preview = {
            "source_record_id": normalized_arguments["source_record_id"],
            "subject_type": normalized_arguments["subject_type"],
            "subject_id": normalized_arguments["subject_id"],
            "predicate": normalized_arguments["predicate"],
            "value": normalized_arguments["value"],
            "observed_at": normalized_arguments["observed_at"],
            "requires_human_confirmation": True,
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
            "requires_human_confirmation": True,
        }
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
    proposal = ChangeProposal(
        id=uid("act"),
        tenant_id=tenant_id,
        type=f"tool:{tool_name}",
        actor_type=actor_type,
        status="proposed",
        input=json.dumps(normalized_arguments, sort_keys=True),
        output=json.dumps(preview, sort_keys=True, default=str),
    )
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
    principal: Principal | None, settling_token_id: str | None
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
    }


#: The attribution a proposal loses when it returns to `proposed`.
UNDECIDED = {
    "decided_at": None,
    "decided_by_user_id": None,
    "decided_via_token_id": None,
}


def _record_decision(
    proposal: ChangeProposal,
    principal: Principal | None,
    settling_token_id: str | None = None,
) -> ChangeProposal:
    """Attribute a settled proposal to the moment and to whoever settled it."""
    for column, value in _decider_values(principal, settling_token_id).items():
        setattr(proposal, column, value)
    return proposal


def _undecide(proposal: ChangeProposal) -> None:
    for column, value in UNDECIDED.items():
        setattr(proposal, column, value)


def approve_and_execute_proposal(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    *,
    confirming_principal: Principal | None = None,
    review_token: str | None = None,
    confirmed: bool = False,
    settling_token_id: str | None = None,
) -> ChangeProposal:
    candidate = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
        )
    )
    if candidate is None:
        raise NotFound("Proposal not found.")
    if candidate.type == "tool:cost.change":
        from reality.services.costing import _owner

        if not confirmed:
            raise InvalidOperation(
                "Explicit confirmation is required for cost decisions."
            )
        _owner(session, tenant_id, confirming_principal)
    if candidate.type == "tool:graph.reports.change":
        from reality.services.analytics.proposals import reveal

        reveal(session, tenant_id, confirming_principal, json.loads(candidate.input))
        if not confirmed:
            from reality.services.analytics.errors import AnalyticsError

            raise AnalyticsError(
                "Explicit confirmation is required for a private report change."
            )
    if "_delivery_review" in json.loads(candidate.input):
        from reality.services.delivery_actions import require_delivery_principal

        require_delivery_principal(session, tenant_id, confirming_principal)
    if candidate.status == "executed":
        return candidate
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_execute")
    if candidate.status == "executing":
        raise InvalidOperation(
            "Proposal execution is in progress or its outcome is unknown; reconcile by proposal ID before taking further action."
        )
    if candidate.status == "rejected":
        raise NotFound("Active tool proposal not found.")
    if candidate.status != "proposed":
        raise InvalidOperation(
            f"Proposal cannot be confirmed from status {candidate.status}."
        )
    tool_name = candidate.type.removeprefix("tool:")
    tool = TOOLS.get(tool_name)
    if tool is None or not tool.mutating:
        raise InvalidOperation("Proposal references an invalid mutation tool.")
    arguments = json.loads(candidate.input)
    if tool_name in MEMBERSHIP_MUTATION_TOOLS and confirming_principal is None:
        raise InvalidOperation("Membership changes require a confirming human owner.")

    from reality.db.core import Tenant
    from reality.services.delivery_actions import REVIEW_KEY, eligible, validate_review

    reviewed_action = REVIEW_KEY in arguments

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
        raise InvalidOperation(
            "Obtain a delivery review before confirming this proposal."
        )
    if REVIEW_KEY in arguments and (
        not confirmed or review_token != arguments[REVIEW_KEY]["token"]
    ):
        raise InvalidOperation(
            "A current review and explicit confirmation are required."
        )

    if tool_name in FINANCE_COMMANDS:
        import os

        from reality.services.memberships import require_owner

        if confirming_principal is not None:
            require_owner(session, tenant_id, confirming_principal)
        elif os.environ.get("REALITY_AUTH_MODE") != "disabled":
            raise InvalidOperation(
                "Account changes require a confirming company owner."
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
                raise InvalidOperation(
                    "Proposal is no longer available for confirmation."
                )
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
            _record_decision(proposal, confirming_principal, settling_token_id)
            proposal.output = json.dumps(_json_value(result), sort_keys=True)
            session.commit()
            return proposal
        except Exception:
            session.rollback()
            raise

    claimed_id = session.scalar(
        update(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
            ChangeProposal.status == "proposed",
        )
        .values(
            status="executing",
            **_decider_values(confirming_principal, settling_token_id),
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
            raise NotFound("Proposal not found.")
        if proposal.status == "executed":
            return proposal
        if proposal.status == "executing":
            raise InvalidOperation(
                "Proposal execution is in progress or its outcome is unknown; reconcile by proposal ID before taking further action."
            )
        raise InvalidOperation(
            f"Proposal cannot be confirmed from status {proposal.status}."
        )
    proposal = session.get(ChangeProposal, {"tenant_id": tenant_id, "id": claimed_id})
    if REVIEW_KEY in arguments:
        from reality.services.business_locks import lock_delivery_state

        try:
            lock_delivery_state(session, tenant_id)
            require_delivery_principal(session, tenant_id, confirming_principal)
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
    if tool_name in {
        "party_create",
        "item_create",
        "location_create",
        "party_update",
        "item_update",
        "location_update",
    }:
        from reality.services.business_locks import lock_delivery_state
        from reality.services.core import _assert_update_revision

        try:
            lock_delivery_state(session, tenant_id)
            session.expire_all()
            from reality.services.delivery_actions import require_delivery_principal

            if tenant and tenant.purpose != "playground":
                require_delivery_principal(session, tenant_id, confirming_principal)
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
    if tool_name in MEMBERSHIP_MUTATION_TOOLS:
        arguments["_confirming_user_id"] = confirming_principal.user_id
    from reality.playground.actions import MASTER_TOOLS
    from reality.services.tenant_policy import master_tool_execution

    if tool_name == "graph.requests.create":
        from reality.services.analytics.proposals import execute_request

        with executing_proposal(tenant_id, proposal.id):
            result = execute_request(
                session, tenant_id, confirming_principal, arguments
            )
    elif tool_name == "graph.reports.change":
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
            if not reviewed_action:
                raise
            session.rollback()
            session.execute(
                update(ChangeProposal)
                .where(
                    ChangeProposal.tenant_id == tenant_id,
                    ChangeProposal.id == proposal_id,
                    ChangeProposal.status == "executing",
                )
                .values(
                    status="failed",
                    output=json.dumps(
                        {
                            "business_effect": "none",
                            "error_type": type(error).__name__,
                            "message": str(error),
                        },
                        sort_keys=True,
                    ),
                )
            )
            session.commit()
            raise
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
) -> ChangeProposal:
    existing = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
        )
    )
    if existing is None:
        raise NotFound("Proposal not found.")
    if existing.status == "rejected":
        return existing
    if existing.status != "proposed":
        raise InvalidOperation(
            f"Proposal cannot be rejected from status {existing.status}."
        )
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_reject")
    proposal = existing
    proposal.status = "rejected"
    _record_decision(proposal, confirming_principal, settling_token_id)
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
    from reality.services.finance.source_mappings import list_source_mappings

    return list_source_mappings(session, tenant_id, **arguments)


def _source_mapping_history_read(session, tenant_id, arguments):
    from reality.services.finance.source_mappings import source_mapping_history

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
        return invoke_graph(session, tenant_id, name, arguments)

    TOOLS[_graph_name] = Tool(
        _graph_name,
        _GRAPH_DESCRIPTIONS[_graph_name],
        False,
        _graph_read,
    )


def _private_report_confirmation_only(session, tenant_id, arguments):
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
    raise InvalidOperation(
        "Requesting an analysis requires an authenticated proposal confirmation."
    )


TOOLS["graph.requests.create"] = Tool(
    "graph.requests.create",
    "Propose asking an analysis question, answered now or by the worker.",
    True,
    _requested_analysis_confirmation_only,
)
