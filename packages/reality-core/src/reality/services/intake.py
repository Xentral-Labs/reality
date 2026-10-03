"""Prepare, retain and atomically accept exact source meaning (spec 351)."""

import json
import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any

from sqlalchemy import Numeric, event, inspect, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    CompanyTimeZone,
    Document,
    ImportJob,
    Item,
    LedgerEntry,
    Location,
    Party,
    SourceRecord,
    SourceStream,
    SubledgerAccount,
)
from reality.domain.intake import (
    PACKAGE_BYTES,
    CalendarState,
    Effect,
    PreparedIntake,
    ReferenceState,
    canonical_json,
    content_digest,
)
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.delivery_actions import require_delivery_principal
from reality.services.finance.accounts import lock_finance
from reality.services.memberships import Principal, require_owner

INTAKE_TYPE = "tool:intake_apply"
_MODELS = {
    "party": Party,
    "item": Item,
    "location": Location,
    "document": Document,
    "ledger_entry": LedgerEntry,
    "account": SubledgerAccount,
}


@dataclass(frozen=True)
class _ApprovedEffects:
    session: Session
    transaction: Any
    nested_transaction: Any
    tenant_id: str
    proposal_id: str
    digest: str


_approved: ContextVar[_ApprovedEffects | None] = ContextVar(
    "intake_approved_effects", default=None
)


@contextmanager
def _effect_scope(session: Session, tenant_id: str, proposal_id: str, digest: str):
    token = _approved.set(
        _ApprovedEffects(
            session,
            session.get_transaction(),
            session.get_nested_transaction(),
            tenant_id,
            proposal_id,
            digest,
        )
    )

    def deny_commit(_session: Session) -> None:
        if (
            _session.get_nested_transaction() is not None
            and _session.get_nested_transaction()
            is not _approved.get().nested_transaction
        ):
            return  # A canonical service may release its own inner savepoint.
        raise core.InvalidOperation(code="intake_partial_commit_forbidden")

    event.listen(session, "before_commit", deny_commit)
    try:
        yield
    finally:
        event.remove(session, "before_commit", deny_commit)
        _approved.reset(token)


def _require_intake_scope(session: Session, tenant_id: str, proposal_id: str) -> None:
    scope = _approved.get()
    if (
        scope is None
        or scope.session is not session
        or scope.transaction is not session.get_transaction()
        or scope.nested_transaction is not session.get_nested_transaction()
        or scope.tenant_id != tenant_id
        or scope.proposal_id != proposal_id
    ):
        raise core.InvalidOperation(code="intake_approval_required")


_EFFECT_OPERATIONS = {
    "document": frozenset({"create_manual_document_with_lines", "emit_business_event"}),
    "commitment": frozenset({"create_commitment", "emit_business_event"}),
    "customer_payment": frozenset(
        {
            "record_customer_payment",
            "create_document",
            "post_ledger",
            "emit_business_event",
        }
    ),
    "source_document": frozenset({"create_document", "emit_business_event"}),
    "return_announcement": frozenset(
        {"announce_customer_return", "emit_business_event"}
    ),
    "credit_hold": frozenset({"emit_business_event"}),
    "commitment_revision": frozenset(
        {"revise_commitment", "emit_business_event", "release_reservation"}
    ),
    "commitment_cancellation": frozenset(
        {
            "cancel_commitment",
            "emit_business_event",
            "release_reservation",
            "release_commitment_hold",
        }
    ),
    "payment_allocation": frozenset({"allocate_settlement", "emit_business_event"}),
}
_active_effect: ContextVar[str | None] = ContextVar(
    "intake_active_effect", default=None
)


def _require_scoped_operation(session: Session, tenant_id: str, operation: str) -> None:
    """An approved package grants only its currently dispatched canonical effect."""
    scope = _approved.get()
    if scope is None:
        return
    nested = session.get_nested_transaction()
    while nested is not None and nested is not scope.nested_transaction:
        nested = nested.parent
    if (
        scope.session is not session
        or scope.tenant_id != tenant_id
        or scope.transaction is not session.get_transaction()
        or nested is not scope.nested_transaction
        or operation not in _EFFECT_OPERATIONS.get(_active_effect.get(), ())
    ):
        raise core.InvalidOperation(code="intake_approval_required")


@contextmanager
def _dispatch_effect(operation: str):
    token = _active_effect.set(operation)
    try:
        yield
    finally:
        _active_effect.reset(token)


_call_intent: ContextVar[tuple[str, str] | None] = ContextVar(
    "intake_call_intent", default=None
)


# Omitted optional parameters still have exact canonical invocation values.
# Capture the definitions before an adapter/callback can wrap them.
_INTENT_DEFAULTS = {
    name: {
        key: parameter.default
        for key, parameter in signature(getattr(core, name)).parameters.items()
        if parameter.default is not Parameter.empty
    }
    for name in (
        "create_manual_document_with_lines",
        "create_commitment",
        "record_customer_payment",
        "allocate_settlement",
        "create_document",
        "announce_customer_return",
        "revise_commitment",
        "cancel_commitment",
    )
}


def _invoke(
    operation: str, handler: Any, session: Session, tenant_id: str, **arguments
):
    """Freeze invocation intent before entering a canonical writer or callback."""
    token = _call_intent.set(
        (operation, canonical_json({**_INTENT_DEFAULTS[operation], **arguments}))
    )
    try:
        return handler(session, tenant_id, **arguments)
    finally:
        _call_intent.reset(token)


def require_scoped_intent(operation: str, actual: dict[str, Any]) -> None:
    if _approved.get() is None:
        return
    intent = _call_intent.get()
    if intent is None:
        raise core.InvalidOperation(code="intake_approval_required")
    expected_operation, frozen = intent
    expected = json.loads(frozen)
    if operation == expected_operation:
        offered = {key: actual.get(key) for key in expected}
        if canonical_json(offered) != canonical_json(expected):
            raise core.InvalidOperation(code="intake_review_invalid")
    elif (
        expected_operation == "record_customer_payment"
        and operation == "create_document"
    ):
        for key, value in {
            "document_type": "customer_payment",
            "party_id": expected["party_id"],
            "currency": expected["currency"],
            "source_record_id": expected["source_record_id"],
            "action_id": expected["action_id"],
            "_commit": False,
        }.items():
            if actual.get(key) != value:
                raise core.InvalidOperation(code="intake_review_invalid")
        if core.decimal(actual["amount"]) != core.decimal(expected["amount"]):
            raise core.InvalidOperation(code="intake_review_invalid")
    elif expected_operation == "record_customer_payment" and operation == "post_ledger":
        if (
            actual["party_id"] != expected["party_id"]
            or actual["source_record_id"] != expected["source_record_id"]
            or actual["currency"] != expected["currency"]
        ):
            raise core.InvalidOperation(code="intake_review_invalid")
        postings = actual["postings"]
        if (
            len(postings) != 2
            or [(row[0], row[1]) for row in postings]
            != [("cash", "debit"), ("accounts_receivable", "credit")]
            or any(
                core.decimal(row[2]) != core.decimal(expected["amount"])
                for row in postings
            )
        ):
            raise core.InvalidOperation(code="intake_review_invalid")


def _state(record: Any) -> str:
    return content_digest(
        {
            column.key: (
                core.decimal(getattr(record, column.key))
                if isinstance(column.type, Numeric)
                and getattr(record, column.key) is not None
                else getattr(record, column.key)
            )
            for column in inspect(type(record)).columns
        }
    )


def _reference(
    session: Session, tenant_id: str, record_type: str, record_id: str
) -> ReferenceState:
    record = core._tenant_record_read(
        session, _MODELS[record_type], tenant_id, record_id
    )
    return ReferenceState(
        record_type=record_type, record_id=record.id, digest=_state(record)
    )


def _calendar_state(session: Session, tenant_id: str) -> CalendarState:
    row = session.scalar(
        select(CompanyTimeZone)
        .where(CompanyTimeZone.tenant_id == tenant_id)
        .execution_options(populate_existing=True)
    )
    calendar = CalendarState(
        time_zone=row.time_zone if row else "UTC",
        source_record_id=row.source_record_id if row else None,
    )
    # Refresh the existing read accelerator after acquiring the shared Tenant lock.
    session.info.setdefault("company_time_zone", {})[tenant_id] = calendar.time_zone
    return calendar


def _payment_plan(
    session: Session,
    tenant_id: str,
    source: SourceRecord,
    job: ImportJob,
    finance_revision: int,
) -> PreparedIntake:
    from reality.services.payment_intake import (
        NormalisedPayment,
        prepare_customer_payment,
    )

    payload = json.loads(source.payload)
    if (source.source_system, source.source_type) == ("demo_data", "payment"):
        from reality.integrations.demo_data import normalise_payment

        payment = normalise_payment(payload)
    else:
        payment = NormalisedPayment.model_validate(payload)
    prepared = prepare_customer_payment(session, tenant_id, source, payment)
    effects = [Effect(operation="customer_payment", arguments=prepared["arguments"])]
    if prepared["allocation"]:
        effects.append(
            Effect(operation="payment_allocation", arguments=prepared["allocation"])
        )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="customer_payment.v1",
        finance_revision=finance_revision,
        mapping=json.loads(job.input),
        references=tuple(
            _reference(session, tenant_id, kind, record_id)
            for kind, record_id in prepared["references"]
        ),
        effects=tuple(effects),
        issues=tuple(prepared["issues"]),
        row_count=1,
    )


def _source_current(session: Session, tenant_id: str, source: SourceRecord) -> None:
    core._lock_source_identity(
        session, tenant_id, source.source_system, source.source_type, source.external_id
    )
    stream = session.scalar(
        select(SourceStream)
        .where(
            SourceStream.tenant_id == tenant_id,
            SourceStream.source_system == source.source_system,
            SourceStream.source_type == source.source_type,
            SourceStream.external_id == source.external_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if stream is None or stream.current_source_record_id != source.id:
        raise core.InvalidOperation(code="intake_review_stale")


def _outcome(
    session: Session,
    tenant_id: str,
    source: SourceRecord,
    job: ImportJob,
    classification: str,
    **kwargs,
) -> None:
    job.attempts += 1
    core._append_interpretation_outcome(
        session, tenant_id, source, job, job.attempts, classification, **kwargs
    )


def prepare_intake(
    session: Session, tenant_id: str, job_id: str, *, _commit: bool = True
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Retain the current source interpretation without accepted business effects.

    BUSINESS RULE intake.prepare_exact:
    Lock and validate current source identity, retain exact meaning and append its prepared outcome.
    """
    # reality-rule: intake.prepare_exact
    lock_delivery_state(session, tenant_id)
    finance = lock_finance(session, tenant_id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job_id)
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, job.source_record_id
    )
    _source_current(session, tenant_id, source)
    job = session.scalar(
        select(ImportJob)
        .where(ImportJob.tenant_id == tenant_id, ImportJob.id == job_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    context = json.loads(job.input)
    if context.get("intake_proposal_id"):
        return core._tenant_record_read(
            session, ChangeProposal, tenant_id, context["intake_proposal_id"]
        )
    calendar = _calendar_state(session, tenant_id)
    if source.source_artifact_id:
        raise core.InvalidOperation(code="intake_profile_unsupported")
    if (source.source_system, source.source_type) == ("shopify", "order"):
        from reality.services.shopify_intake import prepare_order

        plan = prepare_order(session, tenant_id, source, job)
    elif (source.source_system, source.source_type) == ("shopify", "refund"):
        from reality.services.shop_refunds import prepare_refund

        plan = prepare_refund(session, tenant_id, source, job)
    elif context.get("profile") == "customer_payment.v1" or (
        source.source_system,
        source.source_type,
    ) == ("demo_data", "payment"):
        plan = _payment_plan(session, tenant_id, source, job, finance.revision)
    else:
        raise core.InvalidOperation(code="intake_profile_unsupported")
    plan = plan.model_copy(update={"calendar": calendar})
    retained = {"plan": plan.model_dump(mode="json"), "digest": plan.review_digest()}
    if len(canonical_json(retained).encode("utf-8")) > PACKAGE_BYTES:
        raise core.InvalidOperation(code="intake_package_too_large")
    proposal = ChangeProposal(
        id=core.uid("act"),
        tenant_id=tenant_id,
        type=INTAKE_TYPE,
        status="proposed",
        input=canonical_json(retained),
        output=canonical_json(retained),
    )
    session.add(proposal)
    session.flush()
    job.input = canonical_json({**context, "intake_proposal_id": proposal.id})
    job.status = "awaiting_decision"
    job.error = ""
    job.next_attempt_at = None
    _outcome(
        session,
        tenant_id,
        source,
        job,
        "prepared",
        reason_code="intake_awaiting_decision",
        summary="The source meaning awaits an exact decision.",
    )
    if _commit:
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
    else:
        session.flush()
    return proposal


def review_intake(session: Session, tenant_id: str, proposal_id: str) -> dict[str, Any]:
    """
    BUSINESS PURPOSE:
    Read the exact retained interpretation within its tenant.

    BUSINESS RULE intake.review_exact:
    Refuse foreign, wrong-kind or modified retained plans before returning their digest.
    """
    # reality-rule: intake.review_exact
    proposal = core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    if proposal.type != INTAKE_TYPE:
        raise core.NotFound(code="proposal_not_found")
    review = json.loads(proposal.input)
    plan = PreparedIntake.model_validate(review["plan"])
    if plan.tenant_id != tenant_id or plan.review_digest() != review["digest"]:
        raise core.InvalidOperation(code="intake_review_invalid")
    return {**review, "proposal_id": proposal.id, "status": proposal.status}


def _apply_effects(
    session: Session, tenant_id: str, proposal: ChangeProposal, plan: PreparedIntake
) -> list[tuple[str, str]]:
    _require_intake_scope(session, tenant_id, proposal.id)
    document = None
    lines = []
    records = []
    payment_entries = []
    commitments = []
    for effect in plan.effects:
        with _dispatch_effect(effect.operation):
            arguments = dict(effect.arguments)
            if effect.operation == "document":
                document, lines = _invoke(
                    "create_manual_document_with_lines",
                    core.create_manual_document_with_lines,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    _carry_unstated_price=True,
                    _carry_unstated_amount=True,
                    _commit=False,
                )
                records.extend(
                    [
                        ("document", document.id),
                        *(("document_line", row.id) for row in lines),
                    ]
                )
            elif effect.operation == "customer_payment":
                arguments["effective_at"] = core.utc_datetime(arguments["effective_at"])
                payment_entries = _invoke(
                    "record_customer_payment",
                    core.record_customer_payment,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                document = core._tenant_record_read(
                    session, Document, tenant_id, payment_entries[0].document_id
                )
                records.extend(
                    [
                        ("document", document.id),
                        *(("ledger_entry", row.id) for row in payment_entries),
                    ]
                )
            elif effect.operation == "payment_allocation":
                if not payment_entries:
                    raise core.InvalidOperation(code="intake_review_invalid")
                control = next(
                    row
                    for row in payment_entries
                    if row.account == "accounts_receivable"
                )
                allocation = _invoke(
                    "allocate_settlement",
                    core.allocate_settlement,
                    session,
                    tenant_id,
                    payment_ledger_entry_id=control.id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                records.append(("settlement_allocation", allocation.id))
            elif effect.operation == "source_document":
                document = _invoke(
                    "create_document",
                    core.create_document,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                records.append(("document", document.id))
            elif effect.operation == "return_announcement":
                announcement = _invoke(
                    "announce_customer_return",
                    core.announce_customer_return,
                    session,
                    tenant_id,
                    **arguments,
                    _commit=False,
                )
                records.append(("return_announcement", announcement.id))
            elif effect.operation == "credit_hold":
                from reality.services.credit_exposure import _place_holds

                indices = arguments.pop("commitment_indices")
                if any(not 0 <= index < len(commitments) for index in indices):
                    raise core.InvalidOperation(code="intake_review_invalid")
                holds = _place_holds(
                    session,
                    tenant_id,
                    [commitments[index] for index in indices],
                    **arguments,
                    action_id=proposal.id,
                )
                records.extend(("commitment_hold", hold.id) for hold in holds)
            elif effect.operation == "commitment_revision":
                revision = _invoke(
                    "revise_commitment",
                    core.revise_commitment,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                records.append(("commitment_revision", revision.id))
            elif effect.operation == "commitment_cancellation":
                cancelled = _invoke(
                    "cancel_commitment",
                    core.cancel_commitment,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                records.append(("commitment", cancelled.id))
            else:
                index = arguments.pop("line_index")
                if document is None or not 0 <= index < len(lines):
                    raise core.InvalidOperation(code="intake_review_invalid")
                commitment = _invoke(
                    "create_commitment",
                    core.create_commitment,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    document_id=document.id,
                    document_line_id=lines[index].id,
                    _commit=False,
                )
                commitments.append(commitment)
                records.append(("commitment", commitment.id))
    session.flush()
    return records


def apply_prepared_intake(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    digest: str,
    *,
    confirmed: bool,
    principal: Principal | None = None,
    settling_token_id: str | None = None,
    settling_channel: str | None = None,
    _commit: bool = True,
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Accept only the confirmed unchanged interpretation with its decision and receipt.

    BUSINESS RULE intake.accept_exact:
    Recheck current authority and source, mapping and reference state before atomically dispatching canonical effects.
    """
    from reality.services.tenant_policy import require_proposal_decision
    from reality.tools.application import _record_decision

    # reality-rule: intake.accept_exact
    lock_delivery_state(session, tenant_id)
    finance = lock_finance(session, tenant_id)
    require_delivery_principal(session, tenant_id, principal)
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_execute")
    proposal = session.scalar(
        select(ChangeProposal)
        .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if proposal is None or proposal.type != INTAKE_TYPE:
        raise core.NotFound(code="proposal_not_found")
    review = review_intake(session, tenant_id, proposal.id)
    plan = PreparedIntake.model_validate(review["plan"])
    if plan.finance_revision is not None:
        if principal is not None:
            require_owner(session, tenant_id, principal)
        elif os.environ.get("REALITY_AUTH_MODE") != "disabled":
            raise core.InvalidOperation(code="company_owner_access_required")
    if not confirmed or digest != review["digest"]:
        raise core.InvalidOperation(code="review_confirmation_required")
    if proposal.status == "executed":
        return proposal
    if proposal.status != "proposed":
        raise core.InvalidOperation(code="proposal_no_longer_available")
    plan = PreparedIntake.model_validate(review["plan"])
    if plan.finance_revision is not None and finance.revision != plan.finance_revision:
        raise core.InvalidOperation(code="intake_review_stale")
    if plan.calendar != _calendar_state(session, tenant_id):
        raise core.InvalidOperation(code="intake_review_stale")
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, plan.source_record_id
    )
    _source_current(session, tenant_id, source)
    job = session.scalar(
        select(ImportJob)
        .where(ImportJob.tenant_id == tenant_id, ImportJob.id == plan.import_job_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        job is None
        or job.source_record_id != source.id
        or source.payload_hash != plan.source_hash
        or source.version != plan.source_version
        or json.loads(job.input).get("intake_proposal_id") != proposal.id
        or {
            key: value
            for key, value in json.loads(job.input).items()
            if key != "intake_proposal_id"
        }
        != plan.mapping
    ):
        raise core.InvalidOperation(code="intake_review_stale")
    for reference in sorted(
        plan.references, key=lambda row: (row.record_type, row.record_id)
    ):
        model = _MODELS[reference.record_type]
        record = session.scalar(
            select(model)
            .where(model.tenant_id == tenant_id, model.id == reference.record_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if record is None or _state(record) != reference.digest:
            raise core.InvalidOperation(code="intake_review_stale")
    for observation in plan.observations:
        if observation.kind == "credit_exposure":
            from reality.services.credit_exposure import credit_exposure

            current = credit_exposure(
                session,
                tenant_id,
                observation.arguments["party_id"],
                as_of=core.utc_datetime(observation.arguments["as_of"]),
            )
        else:
            from reality.services.shopify_intake import order_state

            current = order_state(session, tenant_id, observation.arguments["order_id"])
        if content_digest(current) != observation.digest:
            raise core.InvalidOperation(code="intake_review_stale")
    with session.begin_nested():
        with (
            _effect_scope(session, tenant_id, proposal.id, digest),
            core.executing_proposal(tenant_id, proposal.id),
        ):
            records = _apply_effects(session, tenant_id, proposal, plan)
        _record_decision(proposal, principal, settling_token_id, settling_channel)
        proposal.status = "executed"
        from reality.services.intake_batches import _current_child_authorization

        parent_authorization = _current_child_authorization(
            session, tenant_id, proposal.id
        )
        proposal.output = canonical_json(
            {
                **(
                    {"batch_authorization": parent_authorization}
                    if parent_authorization
                    else {}
                ),
                "proposal_id": proposal.id,
                "source_record_id": source.id,
                "digest": digest,
                "records": [
                    {"type": kind, "id": record_id} for kind, record_id in records
                ],
                "verification": "applied",
            }
        )
        job.status = "completed"
        job.completed_at = core.now()
        job.error = ""
        job.next_attempt_at = None
        _outcome(
            session,
            tenant_id,
            source,
            job,
            "interpreted",
            reason_code="intake_applied",
            summary="The exact reviewed meaning was accepted.",
            references=records,
        )
    if _commit:
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
    else:
        session.flush()
    return proposal


def reject_prepared_intake(
    session: Session,
    tenant_id: str,
    proposal_id: str,
    *,
    principal: Principal | None = None,
    settling_token_id: str | None = None,
    settling_channel: str | None = None,
    _commit: bool = True,
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Reject retained meaning while preserving received evidence.

    BUSINESS RULE intake.reject_exact:
    Validate tenant and reviewer authority, then retain one rejection and outcome without accepted business effects.
    """
    from reality.services.tenant_policy import require_proposal_decision
    from reality.tools.application import _record_decision

    # reality-rule: intake.reject_exact
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    require_delivery_principal(session, tenant_id, principal)
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_reject")
    proposal = session.scalar(
        select(ChangeProposal)
        .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id == proposal_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if proposal is None or proposal.type != INTAKE_TYPE:
        raise core.NotFound(code="proposal_not_found")
    if proposal.status == "rejected":
        return proposal
    if proposal.status != "proposed":
        raise core.InvalidOperation(code="proposal_no_longer_available")
    review = review_intake(session, tenant_id, proposal_id)
    plan = PreparedIntake.model_validate(review["plan"])
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, plan.source_record_id
    )
    core._lock_source_identity(
        session, tenant_id, source.source_system, source.source_type, source.external_id
    )
    job = session.scalar(
        select(ImportJob)
        .where(ImportJob.tenant_id == tenant_id, ImportJob.id == plan.import_job_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if job is None or job.source_record_id != source.id:
        raise core.InvalidOperation(code="intake_review_invalid")
    with session.begin_nested():
        proposal.status = "rejected"
        _record_decision(proposal, principal, settling_token_id, settling_channel)
        proposal.output = canonical_json(
            {
                "proposal_id": proposal.id,
                "source_record_id": source.id,
                "digest": review["digest"],
                "verification": "rejected_no_effect",
            }
        )
        job.status = "rejected"
        job.error = ""
        job.next_attempt_at = None
        job.completed_at = core.now()
        _outcome(
            session,
            tenant_id,
            source,
            job,
            "rejected",
            reason_code="intake_rejected",
            summary="The reviewed source meaning was rejected without business effects.",
        )
    if _commit:
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
    else:
        session.flush()
    return proposal
