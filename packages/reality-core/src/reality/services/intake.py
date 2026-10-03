"""Prepare, retain and atomically accept exact source meaning (spec 351)."""

import json
import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from sqlalchemy import event, inspect, select
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
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


def _state(record: Any) -> str:
    return content_digest(
        {
            column.key: getattr(record, column.key)
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


def _shopify_plan(
    session: Session, tenant_id: str, source: SourceRecord, job: ImportJob
) -> PreparedIntake:
    if session.scalar(
        select(Document.id).where(
            Document.tenant_id == tenant_id, Document.source_record_id == source.id
        )
    ):
        raise core.InvalidOperation(code="intake_source_already_accepted")
    if source.version != 1:
        raise core.ShopifyUpdateNeedsReview()
    payload = json.loads(source.payload)
    if not 1 <= len(payload.get("line_items", [])) <= 500:
        raise core.InvalidOperation(code="intake_package_too_large")
    mapping = json.loads(job.input)
    company_id = mapping["company_party_id"]
    customer_id = core._surviving_party_id(
        session, tenant_id, mapping["customer_party_id"]
    )
    location_id = mapping["location_id"]
    customer = core._tenant_record_read(session, Party, tenant_id, customer_id)
    if customer.credit_limit > 0:
        # Until credit effects have an exact frozen review, refuse rather than skip the guard.
        raise core.InvalidOperation(code="intake_profile_unsupported")
    references = [
        _reference(session, tenant_id, "party", company_id),
        _reference(session, tenant_id, "party", customer_id),
        _reference(session, tenant_id, "location", location_id),
    ]
    promised_at = next(
        (
            str(row.get("value") or "")
            for row in payload.get("note_attributes", [])
            if row.get("name") == "requested_delivery"
        ),
        "",
    )
    lines = []
    promises = []
    issues = []
    for index, raw in enumerate(payload.get("line_items", [])):
        sku = str(raw.get("sku") or "")
        item = (
            session.scalar(
                select(Item).where(Item.tenant_id == tenant_id, Item.sku == sku)
            )
            if sku
            else None
        )
        quantity = str(core.positive(raw.get("quantity", 0)))
        price = raw.get("price")
        if price is None or str(price).strip() == "":
            price = None
            issues.append(f"line:{index}:price_unstated")
        else:
            price = str(core.decimal(price))
        # Never compute the source's line total from quantity and price.
        stated_amount = raw.get("total_price", raw.get("gross_amount"))
        if stated_amount is None:
            raise core.InvalidOperation(code="intake_source_line_amount_required")
        amount = str(core.decimal(stated_amount))
        ships = raw.get("requires_shipping", True) is not False
        if item:
            references.append(_reference(session, tenant_id, "item", item.id))
        else:
            issues.append(f"line:{index}:item_unknown")
        lines.append(
            {
                "source_line_id": str(raw.get("id") or index + 1),
                "item_id": item.id if item else None,
                "sku": sku,
                "description": str(
                    raw.get("name") or raw.get("title") or (item.name if item else sku)
                ),
                "quantity": quantity,
                "unit_price": price,
                "gross_amount": amount,
                "promised_at": promised_at,
                "unit": item.unit if item else "pcs",
                "line_type": "item" if ships else "service",
            }
        )
        if item and ships:
            promises.append(
                Effect(
                    operation="commitment",
                    arguments={
                        "commitment_type": "customer_delivery",
                        "from_party_id": company_id,
                        "to_party_id": customer_id,
                        "item_id": item.id,
                        "location_id": location_id,
                        "quantity": quantity,
                        "due_at": promised_at or None,
                        "amount": amount,
                        "currency": payload.get("currency", "EUR"),
                        "line_index": index,
                    },
                )
            )
    document = {
        "document_type": "sales_order",
        "number": str(payload.get("name") or source.external_id),
        "party_id": customer_id,
        "lines": lines,
        "gross_amount": str(core.decimal(payload["total_price"])),
        "currency": payload.get("currency", "EUR"),
        "document_date": core._document_day(payload.get("created_at")),
        "ordered_at": payload.get("created_at"),
        "requested_delivery_at": promised_at or None,
        "sales_channel": "shopify",
        "source_record_id": source.id,
    }
    core._preview_manual_document_input(
        session, tenant_id, **document, _carry_unstated_price=True
    )
    return PreparedIntake(
        tenant_id=tenant_id,
        source_record_id=source.id,
        source_hash=source.payload_hash,
        source_version=source.version,
        import_job_id=job.id,
        profile="shopify.order",
        mapping=mapping,
        references=tuple(
            {(row.record_type, row.record_id): row for row in references}.values()
        ),
        effects=(Effect(operation="document", arguments=document), *promises),
        issues=tuple(issues),
        row_count=len(lines),
    )


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
    if source.source_artifact_id:
        raise core.InvalidOperation(code="intake_profile_unsupported")
    if (source.source_system, source.source_type) == ("shopify", "order"):
        plan = _shopify_plan(session, tenant_id, source, job)
    elif context.get("profile") == "customer_payment.v1" or (
        source.source_system,
        source.source_type,
    ) == ("demo_data", "payment"):
        plan = _payment_plan(session, tenant_id, source, job, finance.revision)
    else:
        raise core.InvalidOperation(code="intake_profile_unsupported")
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
    for effect in plan.effects:
        arguments = dict(effect.arguments)
        if effect.operation == "document":
            document, lines = core.create_manual_document_with_lines(
                session,
                tenant_id,
                **arguments,
                action_id=proposal.id,
                _carry_unstated_price=True,
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
            payment_entries = core.record_customer_payment(
                session, tenant_id, **arguments, action_id=proposal.id, _commit=False
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
                row for row in payment_entries if row.account == "accounts_receivable"
            )
            allocation = core.allocate_settlement(
                session,
                tenant_id,
                control.id,
                **arguments,
                action_id=proposal.id,
                _commit=False,
            )
            records.append(("settlement_allocation", allocation.id))
        else:
            index = arguments.pop("line_index")
            if document is None or not 0 <= index < len(lines):
                raise core.InvalidOperation(code="intake_review_invalid")
            commitment = core.create_commitment(
                session,
                tenant_id,
                **arguments,
                action_id=proposal.id,
                document_id=document.id,
                document_line_id=lines[index].id,
                _commit=False,
            )
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
    """Own one effect transaction; a savepoint also preserves a worker's outer unit."""
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
    with session.begin_nested():
        with (
            _effect_scope(session, tenant_id, proposal.id, digest),
            core.executing_proposal(tenant_id, proposal.id),
        ):
            records = _apply_effects(session, tenant_id, proposal, plan)
        _record_decision(proposal, principal, settling_token_id, settling_channel)
        proposal.status = "executed"
        proposal.output = canonical_json(
            {
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
    """Reject retained meaning without losing raw input or inventing business effects."""
    from reality.services.tenant_policy import require_proposal_decision
    from reality.tools.application import _record_decision

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
