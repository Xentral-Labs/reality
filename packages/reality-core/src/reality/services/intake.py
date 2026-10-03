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
    CustomerItemNumber,
    Document,
    DocumentLine,
    ImportJob,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    PaymentTerm,
    SourceArtifact,
    SourceRecord,
    SourceStream,
    SubledgerAccount,
)
from reality.domain.intake import (
    PACKAGE_BYTES,
    CalendarState,
    Effect,
    ObservationState,
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
_FINANCIAL_PROFILES = frozenset(
    {
        "customer_payment.v1",
        "supplier_payment.v1",
        "sales_invoice.v1",
        "artifact:bank_statement.v1",
    }
)
_MODELS = {
    "source_artifact": SourceArtifact,
    "customer_item_number": CustomerItemNumber,
    "party": Party,
    "item": Item,
    "location": Location,
    "document": Document,
    "document_line": DocumentLine,
    "payment_term": PaymentTerm,
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
    "master_item": frozenset({"create_item", "emit_business_event"}),
    "master_party": frozenset({"create_party", "emit_business_event"}),
    "master_location": frozenset({"create_location", "emit_business_event"}),
    "inventory_adjustment": frozenset({"record_movement", "emit_business_event"}),
    "external_stock_statement": frozenset(
        {"record_external_stock_source", "emit_business_event"}
    ),
    "invoice_post": frozenset({"post_ledger", "emit_business_event"}),
    "item_package": frozenset({"create_item", "emit_business_event"}),
    "document": frozenset({"create_manual_document_with_lines", "emit_business_event"}),
    "commitment": frozenset({"create_commitment", "emit_business_event"}),
    "customer_payment": frozenset(
        {
            "record_customer_payment",
            "post_ledger",
            "create_document",
            "emit_business_event",
        }
    ),
    "supplier_payment": frozenset(
        {
            "record_supplier_payment",
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


_payment_document: ContextVar[str | None] = ContextVar(
    "intake_payment_document", default=None
)


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
        "create_item",
        "create_party",
        "create_location",
        "record_movement",
        "record_supplier_payment",
        "post_ledger",
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

_INTENT_DEFAULTS["record_external_stock_source"] = {}


def _invoke(
    operation: str, handler: Any, session: Session, tenant_id: str, **arguments
):
    """Freeze invocation intent before entering a canonical writer or callback."""
    token = _call_intent.set(
        (operation, canonical_json({**_INTENT_DEFAULTS[operation], **arguments}))
    )
    document_token = _payment_document.set(None)
    try:
        return handler(session, tenant_id, **arguments)
    finally:
        _payment_document.reset(document_token)
        _call_intent.reset(token)


def require_scoped_intent(operation: str, actual: dict[str, Any]) -> None:
    if _approved.get() is None:
        return
    intent = _call_intent.get()
    if intent is None:
        raise core.InvalidOperation(code="intake_approval_required")
    expected_operation, frozen = intent
    expected = json.loads(frozen)
    payment_call = expected_operation in {
        "record_customer_payment",
        "record_supplier_payment",
    }
    supplier = expected_operation == "record_supplier_payment"
    control_role = "accounts_payable" if supplier else "accounts_receivable"
    if operation == expected_operation:
        offered = {key: actual.get(key) for key in expected}
        if canonical_json(offered) != canonical_json(expected):
            raise core.InvalidOperation(code="intake_review_invalid")
    elif payment_call and operation == "create_document":
        required = {
            **_INTENT_DEFAULTS["create_document"],
            "document_type": "supplier_payment" if supplier else "customer_payment",
            "party_id": expected["party_id"],
            "currency": expected["currency"],
            "source_record_id": expected["source_record_id"],
            "action_id": expected["action_id"],
            "document_date": core._company_day(
                actual["session"],
                actual["tenant_id"],
                core.utc_datetime(expected["effective_at"]),
            ).isoformat(),
            "_commit": False,
        }
        if expected["payment_number"] is not None:
            required["number"] = expected["payment_number"]
        if canonical_json({key: actual.get(key) for key in required}) != canonical_json(
            required
        ):
            raise core.InvalidOperation(code="intake_review_invalid")
        if core.decimal(actual["amount"]) != core.decimal(expected["amount"]):
            raise core.InvalidOperation(code="intake_review_invalid")
    elif payment_call and operation == "post_ledger":
        required = {
            "document_id": _payment_document.get(),
            "party_id": expected["party_id"],
            "source_record_id": expected["source_record_id"],
            "currency": expected["currency"],
            "action_id": expected["action_id"],
            "effective_at": expected["effective_at"],
            "account_ids": {
                control_role: expected["_control_account_id"],
                "cash": expected["_cash_account_id"],
            },
            "exchange_rate": None,
            "company_amounts": None,
            "_line_account_ids": None,
            "_commit": False,
        }
        if required["document_id"] is None or canonical_json(
            {key: actual.get(key) for key in required}
        ) != canonical_json(required):
            raise core.InvalidOperation(code="intake_review_invalid")
        postings = actual["postings"]
        if (
            len(postings) != 2
            or [(row[0], row[1]) for row in postings]
            != (
                [("accounts_payable", "debit"), ("cash", "credit")]
                if supplier
                else [("cash", "debit"), ("accounts_receivable", "credit")]
            )
            or any(
                core.decimal(row[2]) != core.decimal(expected["amount"])
                for row in postings
            )
        ):
            raise core.InvalidOperation(code="intake_review_invalid")
    else:
        raise core.InvalidOperation(code="intake_review_invalid")


def _bind_payment_document(session, tenant_id, document_id):
    if _approved.get() is None:
        return
    _require_scoped_operation(
        session,
        tenant_id,
        "record_supplier_payment"
        if _call_intent.get() and _call_intent.get()[0] == "record_supplier_payment"
        else "record_customer_payment",
    )
    intent = _call_intent.get()
    if (
        intent is None
        or intent[0] not in {"record_customer_payment", "record_supplier_payment"}
        or _payment_document.get() is not None
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    _payment_document.set(document_id)


def _payment_state(session, tenant_id, invoice_id):
    state = {"company_currency": core._book_currency(session, tenant_id)}
    if not invoice_id:
        return state
    invoice = core._tenant_record_read(session, Document, tenant_id, invoice_id)
    position = core.settlement_positions(session, tenant_id, [invoice]).get(invoice.id)
    if position is None:
        return {**state, "invoice_id": invoice.id, "position": None}
    allocations = core.active_settlement_allocations(
        session, tenant_id, entry_ids={position.control.id}
    )
    return {
        **state,
        "invoice_id": invoice.id,
        "control_id": position.control.id,
        "open": position.open,
        "role": position.role,
        "reversal_id": position.relation.id if position.relation else None,
        "allocations": sorted(
            (
                row.id,
                str(row.amount),
                row.payment_ledger_entry_id,
                row.invoice_ledger_entry_id,
            )
            for row in allocations
        ),
    }


def _stock_state(session, tenant_id, item_id, location_id):
    from sqlalchemy import or_

    core._tenant_record_read(session, Item, tenant_id, item_id)
    core._tenant_record_read(session, Location, tenant_id, location_id)
    movements = list(
        session.scalars(
            select(Movement)
            .where(
                Movement.tenant_id == tenant_id,
                Movement.item_id == item_id,
                or_(
                    Movement.from_location_id == location_id,
                    Movement.to_location_id == location_id,
                ),
            )
            .order_by(Movement.id)
            .execution_options(populate_existing=True)
        )
    )
    return {
        "quantity": str(core.stock_at(session, tenant_id, item_id, location_id)),
        "movements": [(row.id, _state(row)) for row in movements],
    }


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
    outgoing = json.loads(job.input).get("profile") == "supplier_payment.v1"
    if outgoing:
        from reality.services.finance.accounts import resolve_account

        if payment.references:
            raise core.InvalidOperation(code="intake_review_invalid")
        core._tenant_record_read(session, Party, tenant_id, payment.party_id)
        control = resolve_account(session, tenant_id, "accounts_payable")
        cash = resolve_account(session, tenant_id, "cash")
        prepared = {
            "arguments": {
                "party_id": payment.party_id,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "payment_number": payment.payment_number or None,
                "source_record_id": source.id,
                "effective_at": payment.effective_at.isoformat(),
                "_control_account_id": control.id,
                "_cash_account_id": cash.id,
            },
            "references": [
                ("party", payment.party_id),
                ("account", control.id),
                ("account", cash.id),
            ],
            "allocation": None,
            "issues": [
                "This records a received payment statement; it does not send funds or execute a bank transfer."
            ],
        }
    else:
        prepared = prepare_customer_payment(session, tenant_id, source, payment)
    operation = "supplier_payment" if outgoing else "customer_payment"
    effects = [Effect(operation=operation, arguments=prepared["arguments"])]
    if prepared["allocation"]:
        effects.append(
            Effect(operation="payment_allocation", arguments=prepared["allocation"])
        )
    invoice_id = next(
        (identity for kind, identity in prepared["references"] if kind == "document"),
        "",
    )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="supplier_payment.v1" if outgoing else "customer_payment.v1",
        finance_revision=None,
        observations=(
            ObservationState(
                kind="payment_state",
                arguments={"invoice_id": invoice_id},
                digest=content_digest(_payment_state(session, tenant_id, invoice_id)),
            ),
        ),
        mapping=json.loads(job.input),
        references=tuple(
            _reference(session, tenant_id, kind, record_id)
            for kind, record_id in prepared["references"]
        ),
        effects=tuple(effects),
        issues=tuple(prepared["issues"]),
        row_count=1,
    )


def _invoice_plan(session, tenant_id, source, job):
    from reality.services.finance.accounts import resolve_account
    from reality.services.payment_intake import NormalisedInvoice, _invoice_fields

    payload = json.loads(source.payload)
    if (source.source_system, source.source_type) == ("demo_data", "invoice"):
        from reality.integrations.demo_data import normalise_invoice

        invoice = normalise_invoice(payload)
    else:
        invoice = NormalisedInvoice.model_validate(payload)
    order, lines, term = _invoice_fields(session, tenant_id, source, invoice)
    control = resolve_account(session, tenant_id, "accounts_receivable")
    revenue = resolve_account(session, tenant_id, "sales_revenue")
    refs = [
        ("party", invoice.party_id),
        ("document", order.id),
        ("account", control.id),
        ("account", revenue.id),
    ]
    refs.extend(("document_line", row["billed_document_line_id"]) for row in lines)
    refs.extend(("item", row["item_id"]) for row in lines if row["item_id"])
    if term:
        refs.append(("payment_term", term.id))
    document = {
        "document_type": "sales_invoice",
        "number": invoice.number,
        "party_id": invoice.party_id,
        "lines": lines,
        "gross_amount": str(invoice.gross_amount),
        "currency": invoice.currency,
        "document_date": core._company_day(
            session, tenant_id, invoice.issued_at
        ).isoformat(),
        "payment_term_code": invoice.payment_term_code,
        "source_record_id": source.id,
    }
    posting = {
        "party_id": invoice.party_id,
        "postings": [
            ("accounts_receivable", "debit", str(invoice.gross_amount)),
            ("sales_revenue", "credit", str(invoice.gross_amount)),
        ],
        "account_ids": {"accounts_receivable": control.id, "sales_revenue": revenue.id},
        "currency": invoice.currency,
        "source_record_id": source.id,
        "effective_at": invoice.issued_at.isoformat(),
    }
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="sales_invoice.v1",
        mapping=json.loads(job.input),
        references=tuple(
            _reference(session, tenant_id, kind, identity)
            for kind, identity in sorted(set(refs))
        ),
        observations=(
            ObservationState(
                kind="payment_state",
                arguments={"invoice_id": ""},
                digest=content_digest(_payment_state(session, tenant_id, "")),
            ),
        ),
        effects=(
            Effect(operation="document", arguments=document),
            Effect(operation="invoice_post", arguments=posting),
        ),
        row_count=len(lines),
    )


def _freeze_effect_defaults(plan):
    """Retain canonical business defaults when meaning is prepared, before review."""
    operations = {
        "master_item": "create_item",
        "master_party": "create_party",
        "master_location": "create_location",
        "inventory_adjustment": "record_movement",
        "document": "create_manual_document_with_lines",
        "commitment": "create_commitment",
        "customer_payment": "record_customer_payment",
        "supplier_payment": "record_supplier_payment",
        "invoice_post": "post_ledger",
        "payment_allocation": "allocate_settlement",
        "source_document": "create_document",
        "return_announcement": "announce_customer_return",
        "commitment_revision": "revise_commitment",
        "commitment_cancellation": "cancel_commitment",
    }
    effects = []
    for effect in plan.effects:
        operation = operations.get(effect.operation)
        defaults = dict(_INTENT_DEFAULTS[operation]) if operation else {}
        for technical in (
            "action_id",
            "_commit",
            "_carry_unstated_price",
            "_carry_unstated_amount",
        ):
            defaults.pop(technical, None)
        if effect.operation == "commitment":
            for linkage in ("document_id", "document_line_id"):
                defaults.pop(linkage, None)
        effects.append(
            effect.model_copy(update={"arguments": {**defaults, **effect.arguments}})
        )
    return plan.model_copy(update={"effects": tuple(effects)})


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
    Retain source meaning or a safe preparation-phase refusal without accepted business effects.

    BUSINESS RULE intake.prepare_exact:
    Lock the owning source/job, isolate preparation, and retain exact meaning or its phase failure.
    """
    from pydantic import ValidationError

    # reality-rule: intake.prepare_exact
    lock_delivery_state(session, tenant_id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job_id)
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, job.source_record_id
    )
    current_id = json.loads(job.input).get("intake_proposal_id")
    if current_id:
        return core._tenant_record_read(session, ChangeProposal, tenant_id, current_id)
    try:
        with session.begin_nested():
            proposal = _prepare_intake(session, tenant_id, job_id, _commit=False)
    except (core.RealityError, ValidationError) as error:
        code = (
            error.code
            if isinstance(error, core.RealityError) and error.coded
            else "intake_review_invalid"
        )
        job.status = "failed"
        job.error = canonical_json({"phase": "prepare", "reason_code": code})
        job.next_attempt_at = None
        job.completed_at = None
        _outcome(
            session,
            tenant_id,
            source,
            job,
            "failed",
            interpreter_name="intake.prepare",
            reason_code=code,
            summary="The source could not be prepared; no business effects were accepted.",
        )
        if _commit:
            session.commit()
        else:
            session.flush()
        raise
    if _commit:
        session.commit()
    else:
        session.flush()
    return proposal


def renew_prepared_intake(
    session: Session,
    tenant_id: str,
    job_id: str,
    *,
    previous_proposal_id: str,
    request_id: str,
    _commit: bool = True,
) -> ChangeProposal:
    """
    BUSINESS PURPOSE:
    Prepare a fresh interpretation after explicit renewed review, without changing old accepted intent.

    BUSINESS RULE intake.renew_exact:
    Bind renewal to the current pending review and request identity; preserve old plans and completed receipts.
    """
    # reality-rule: intake.renew_exact
    lock_delivery_state(session, tenant_id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job_id)
    previous = core._tenant_record_read(
        session, ChangeProposal, tenant_id, previous_proposal_id
    )
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= 128:
        raise core.InvalidOperation(code="intake_review_invalid")
    context = json.loads(job.input)
    renewals = context.get("intake_renewals", {})
    if request_id in renewals:
        held = renewals[request_id]
        if held["previous_proposal_id"] != previous_proposal_id:
            raise core.InvalidOperation(code="intake_review_stale")
        return core._tenant_record_read(
            session, ChangeProposal, tenant_id, held["proposal_id"]
        )
    if len(renewals) >= 500:
        raise core.InvalidOperation(code="intake_package_too_large")
    if (
        context.get("intake_proposal_id") != previous.id
        or previous.type != INTAKE_TYPE
        or previous.status not in {"proposed", "rejected"}
        or job.status == "completed"
    ):
        raise core.InvalidOperation(code="intake_review_stale")
    with session.begin_nested():
        job.input = canonical_json(
            {
                key: value
                for key, value in context.items()
                if key != "intake_proposal_id"
            }
        )
        proposal = prepare_intake(session, tenant_id, job_id, _commit=False)
        current_context = json.loads(job.input)
        current_context["intake_renewals"] = {
            **renewals,
            request_id: {
                "previous_proposal_id": previous.id,
                "proposal_id": proposal.id,
            },
        }
        job.input = canonical_json(current_context)
    if _commit:
        session.commit()
    else:
        session.flush()
    return proposal


def _prepare_intake(
    session: Session, tenant_id: str, job_id: str, *, _commit: bool = True
) -> ChangeProposal:
    """Build retained meaning inside the caller-owned preparation savepoint."""
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
    if source.source_artifact_id and context.get("profile") == "item_csv.v1":
        from reality.services.reviewed_item_imports import prepare_item_package

        plan = prepare_item_package(session, tenant_id, source, job)
    elif source.source_artifact_id:
        from reality.services.artifact_batches import _prepare_artifact_or_batch

        plan = _prepare_artifact_or_batch(session, tenant_id, source, job)
        if isinstance(plan, ChangeProposal):
            job.input = canonical_json({**context, "intake_proposal_id": plan.id})
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
                summary="The exact artifact packages await a batch decision.",
            )
            if _commit:
                session.commit()
            else:
                session.flush()
            return plan
    elif (source.source_system, source.source_type) == ("shopify", "order"):
        from reality.services.shopify_intake import prepare_order

        plan = prepare_order(session, tenant_id, source, job)
    elif (source.source_system, source.source_type) == ("shopify", "refund"):
        from reality.services.shop_refunds import prepare_refund

        plan = prepare_refund(session, tenant_id, source, job)
    elif context.get("profile") == "sales_invoice.v1" or (
        source.source_system,
        source.source_type,
    ) == ("demo_data", "invoice"):
        plan = _invoice_plan(session, tenant_id, source, job)
    elif context.get("profile") in {"customer_payment.v1", "supplier_payment.v1"} or (
        source.source_system,
        source.source_type,
    ) == ("demo_data", "payment"):
        plan = _payment_plan(session, tenant_id, source, job, finance.revision)
    else:
        raise core.InvalidOperation(code="intake_profile_unsupported")
    plan = _freeze_effect_defaults(plan).model_copy(
        update={
            "calendar": calendar,
            "mapping": {
                key: value
                for key, value in plan.mapping.items()
                if key not in {"intake_proposal_id", "intake_renewals"}
            },
        }
    )
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
    job = core._tenant_record_read(session, ImportJob, tenant_id, plan.import_job_id)
    current_id = json.loads(job.input).get("intake_proposal_id")
    status = (
        "stale"
        if proposal.status == "proposed" and current_id != proposal.id
        else proposal.status
    )
    return {**review, "proposal_id": proposal.id, "status": status}


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
            if effect.operation in {
                "master_item",
                "master_party",
                "master_location",
                "inventory_adjustment",
            }:
                operation, record_type = {
                    "master_item": ("create_item", "item"),
                    "master_party": ("create_party", "party"),
                    "master_location": ("create_location", "location"),
                    "inventory_adjustment": ("record_movement", "movement"),
                }[effect.operation]
                row = _invoke(
                    operation,
                    getattr(core, operation),
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                records.append((record_type, row.id))
            elif effect.operation == "external_stock_statement":
                from reality.services.external_stock import _record_received_source

                rows = _invoke(
                    "record_external_stock_source",
                    _record_received_source,
                    session,
                    tenant_id,
                    **arguments,
                    action_id=proposal.id,
                )
                records.extend(("external_stock_statement", row.id) for row in rows)
            elif effect.operation == "item_package":
                from reality.services.item_imports import _validate_new_rows

                _validate_new_rows(session, tenant_id, arguments["rows"])
                with core._batch_reads(session):
                    for row in arguments["rows"]:
                        item = _invoke(
                            "create_item",
                            core.create_item,
                            session,
                            tenant_id,
                            **arguments["defaults"],
                            **row,
                            source_record_id=plan.source_record_id,
                            action_id=proposal.id,
                            _commit=False,
                        )
                        records.append(("item", item.id))
            elif effect.operation == "document":
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
            elif effect.operation in {"customer_payment", "supplier_payment"}:
                arguments["effective_at"] = core.utc_datetime(arguments["effective_at"])
                payment_entries = _invoke(
                    "record_supplier_payment"
                    if effect.operation == "supplier_payment"
                    else "record_customer_payment",
                    core.record_supplier_payment
                    if effect.operation == "supplier_payment"
                    else core.record_customer_payment,
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
            elif effect.operation == "invoice_post":
                if document is None or document.type != "sales_invoice":
                    raise core.InvalidOperation(code="intake_review_invalid")
                entries = _invoke(
                    "post_ledger",
                    core.post_ledger,
                    session,
                    tenant_id,
                    document_id=document.id,
                    **arguments,
                    action_id=proposal.id,
                    _commit=False,
                )
                records.extend(("ledger_entry", row.id) for row in entries)
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
    Accept only confirmed unchanged meaning, retaining atomic results or safe phase refusals.

    BUSINESS RULE intake.accept_exact:
    Authenticate an exact current decision, isolate application, and retain success or no-effect failure.
    """
    from reality.services.tenant_policy import require_proposal_decision

    # reality-rule: intake.accept_exact
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    require_delivery_principal(session, tenant_id, principal)
    require_proposal_decision(session, tenant_id, proposal_id, "proposal_execute")
    proposal = core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    if proposal.type != INTAKE_TYPE:
        raise core.NotFound(code="proposal_not_found")
    review = review_intake(session, tenant_id, proposal_id)
    plan = PreparedIntake.model_validate(review["plan"])
    if plan.finance_revision is not None or plan.profile in _FINANCIAL_PROFILES:
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
    try:
        with session.begin_nested():
            result = _apply_prepared_intake(
                session,
                tenant_id,
                proposal_id,
                digest,
                confirmed=True,
                principal=principal,
                settling_token_id=settling_token_id,
                settling_channel=settling_channel,
                _commit=False,
            )
    except core.RealityError as error:
        _retain_apply_failure(session, tenant_id, proposal_id, error)
        if _commit:
            session.commit()
        else:
            session.flush()
        raise
    if _commit:
        session.commit()
    else:
        session.flush()
    return result


def _retain_apply_failure(session, tenant_id, proposal_id, error):
    """Retain technical phase evidence after the failing business savepoint rolled back."""
    proposal = core._tenant_record_read(session, ChangeProposal, tenant_id, proposal_id)
    plan = PreparedIntake.model_validate(json.loads(proposal.input)["plan"])
    job = core._tenant_record_read(session, ImportJob, tenant_id, plan.import_job_id)
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, plan.source_record_id
    )
    if proposal.status == "executed" or job.status == "completed":
        return
    code = error.code if error.coded else "intake_review_invalid"
    job.status = "awaiting_decision"
    job.completed_at = None
    job.next_attempt_at = None
    job.error = canonical_json(
        {"phase": "apply", "reason_code": code, "proposal_id": proposal.id}
    )
    _outcome(
        session,
        tenant_id,
        source,
        job,
        "stale" if code == "intake_review_stale" else "failed",
        interpreter_name="intake.apply",
        reason_code=code,
        summary="The reviewed unit was refused without accepted business effects; review remains required.",
    )


def _validate_current_plan(
    session, tenant_id, proposal, plan, current_finance_revision
):
    """Check exact current meaning without dispatching any accepted business effect."""
    if (
        plan.finance_revision is not None
        and current_finance_revision != plan.finance_revision
    ):
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
            if key not in {"intake_proposal_id", "intake_renewals"}
        }
        != plan.mapping
    ):
        raise core.InvalidOperation(code="intake_review_stale")
    if plan.mapping.get("parent_source_id"):
        parent_source = core._tenant_record_read(
            session, SourceRecord, tenant_id, plan.mapping["parent_source_id"]
        )
        _source_current(session, tenant_id, parent_source)
        if parent_source.source_artifact_id != source.source_artifact_id:
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
        elif observation.kind == "stock_state":
            current = _stock_state(
                session,
                tenant_id,
                observation.arguments["item_id"],
                observation.arguments["location_id"],
            )
        elif observation.kind == "customer_item_resolution":
            from reality.services.customer_item_numbers import resolve_customer_item

            mapped = resolve_customer_item(
                session,
                tenant_id,
                observation.arguments["party_id"],
                observation.arguments["number"],
            )
            current = {
                "mapping_id": mapped.id if mapped else None,
                "item_id": mapped.item_id if mapped else None,
            }
        elif observation.kind == "payment_state":
            current = _payment_state(
                session, tenant_id, observation.arguments["invoice_id"]
            )
        else:
            from reality.services.shopify_intake import order_state

            current = order_state(session, tenant_id, observation.arguments["order_id"])
        if content_digest(current) != observation.digest:
            raise core.InvalidOperation(code="intake_review_stale")
    return source, job


def _apply_prepared_intake(
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
    """Execute exact accepted intent within the caller-owned apply savepoint."""
    from reality.services.tenant_policy import require_proposal_decision
    from reality.tools.application import _record_decision

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
    if plan.finance_revision is not None or plan.profile in _FINANCIAL_PROFILES:
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
    source, job = _validate_current_plan(
        session, tenant_id, proposal, plan, finance.revision
    )
    with session.begin_nested():
        with (
            _effect_scope(session, tenant_id, proposal.id, digest),
            core.executing_proposal(tenant_id, proposal.id),
        ):
            records = _apply_effects(session, tenant_id, proposal, plan)
        from reality.services.intake_review import _current_agent_authorization

        agent_authorization = _current_agent_authorization(
            session, tenant_id, proposal.id
        )
        _record_decision(
            proposal,
            None if agent_authorization else principal,
            settling_token_id,
            settling_channel,
        )
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
                **(
                    {"agent_review": agent_authorization} if agent_authorization else {}
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
        from reality.services.intake_review import _current_agent_authorization

        agent_authorization = _current_agent_authorization(
            session, tenant_id, proposal.id
        )
        proposal.status = "rejected"
        _record_decision(
            proposal,
            None if agent_authorization else principal,
            settling_token_id,
            settling_channel,
        )
        proposal.output = canonical_json(
            {
                "proposal_id": proposal.id,
                "source_record_id": source.id,
                "digest": review["digest"],
                **(
                    {"agent_review": agent_authorization} if agent_authorization else {}
                ),
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
