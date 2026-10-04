"""Explicit real reviewer fixtures for stories requiring accepted source evidence.

These helpers submit exact retained decisions; they do not change any service,
permission check or runtime approval context. Refusal/preparation tests call the
real entrypoints directly.
"""

import json

from sqlalchemy import select

from reality.db.core import (
    AppUser,
    Commitment,
    Document,
    DocumentLine,
    ImportJob,
    SourceRecord,
    TenantMembership,
)
from reality.services import core, intake_batches
from reality.services.intake import apply_prepared_intake, review_intake
from reality.services.memberships import Principal


def explicit_owner(session, tenant_id):
    membership = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.role == "owner",
            TenantMembership.status == "active",
        )
    )
    if membership:
        return Principal(membership.user_id)
    owner = AppUser(
        id=core.uid("usr"),
        email=f"{core.uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        email_verified_at=core.now(),
    )
    session.add(owner)
    session.flush()
    session.add(
        TenantMembership(
            id=core.uid("tmb"),
            tenant_id=tenant_id,
            user_id=owner.id,
            role="owner",
            status="active",
        )
    )
    session.flush()
    return Principal(owner.id)


def accept_import_job(session, tenant_id, job_id):
    """Review and confirm one exact retained source, then return accepted evidence."""
    try:
        proposal = core.process_import_job(session, tenant_id, job_id)
    except core.InterpretationNeedsReview:
        return None
    if proposal is None:
        return None
    owner = explicit_owner(session, tenant_id)
    job = core._tenant_record_read(session, ImportJob, tenant_id, job_id)
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, job.source_record_id
    )
    if proposal.type == "tool:intake_batch_apply":
        intake_batches.approve_batch(
            session,
            tenant_id,
            proposal.id,
            json.loads(proposal.input)["digest"],
            confirmed=True,
            principal=owner,
        )
        while proposal.status != "executed":
            intake_batches.settle_chunk(
                session,
                tenant_id,
                proposal.id,
                continuation_id=json.loads(proposal.output)["continuation_id"],
            )
            session.commit()
        status = intake_batches.batch_status(session, tenant_id, proposal.id)
        receipts = []
        for row in status["results"]:
            if row["disposition"] in {"applied", "replayed"}:
                receipts.append(row["receipt"])
                continue
            # Related orders change the customer's reviewed exposure. The fixture
            # asks its real owner for a separate fresh review, never reuses bulk consent.
            assert (
                row["disposition"] == "review_required"
                and row["reason_code"] == "intake_review_stale"
            ), status
            from reality.db.core import ChangeProposal
            from reality.services.intake import renew_prepared_intake

            previous = core._tenant_record_read(
                session, ChangeProposal, tenant_id, row["proposal_id"]
            )
            child_job_id = json.loads(previous.input)["plan"]["import_job_id"]
            renewed = renew_prepared_intake(
                session,
                tenant_id,
                child_job_id,
                previous_proposal_id=previous.id,
                request_id=core.uid("fixture_review"),
            )
            fresh = review_intake(session, tenant_id, renewed.id)
            receipt = apply_prepared_intake(
                session,
                tenant_id,
                renewed.id,
                fresh["digest"],
                confirmed=True,
                principal=owner,
            )
            receipts.append(json.loads(receipt.output))
        target = json.loads(job.input).get("expected_target")
        ids = [
            record["id"]
            for receipt in receipts
            for record in receipt["records"]
            if record["type"]
            == {
                "sales_order": "document",
                "bank_statement": "document",
                "inventory_snapshot": "movement",
                "external_stock": "external_stock_statement",
            }.get(target, target)
        ]
        return {"target": target, "rows": len(ids), "created_ids": ids}
    held = review_intake(session, tenant_id, proposal.id)
    applied = apply_prepared_intake(
        session, tenant_id, proposal.id, held["digest"], confirmed=True, principal=owner
    )
    target = json.loads(job.input).get("expected_target")
    if target:
        records = json.loads(applied.output)["records"]
        kind = {
            "sales_order": "document",
            "bank_statement": "document",
            "inventory_snapshot": "movement",
            "external_stock": "external_stock_statement",
        }.get(target, target)
        ids = [row["id"] for row in records if row["type"] == kind]
        return {"target": target, "rows": len(ids), "created_ids": ids}
    if source.source_type == "order":
        from reality.services.shop_order_changes import order_for_source

        document = order_for_source(session, tenant_id, source)
    else:
        document = session.scalar(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.source_record_id == source.id
            )
        )
    assert applied.status == "executed"
    if document is None:
        return applied
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB

    from reality.db.core import ChangeProposal

    original = applied
    if document.source_record_id != source.id:
        original = session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.type == "tool:intake_apply",
                ChangeProposal.status == "executed",
                cast(ChangeProposal.output, JSONB)["source_record_id"].astext
                == document.source_record_id,
            )
        )
    records = json.loads(original.output)["records"]
    lines = [
        core._tenant_record_read(session, DocumentLine, tenant_id, record["id"])
        for record in records
        if record["type"] == "document_line"
    ]
    commitments = [
        core._tenant_record_read(session, Commitment, tenant_id, record["id"])
        for record in records
        if record["type"] == "commitment"
    ]
    return source, document, lines, commitments


def accept_shopify_order(
    session, tenant_id, payload, company_party_id, customer_party_id, location_id
):
    _, job = core.enqueue_shopify_order(
        session, tenant_id, payload, company_party_id, customer_party_id, location_id
    )
    return accept_import_job(session, tenant_id, job.id)


def accept_pending_import_jobs(session, tenant_id):
    ids = list(
        session.scalars(
            select(ImportJob.id).where(
                ImportJob.tenant_id == tenant_id, ImportJob.status == "pending"
            )
        )
    )
    accepted = failed = 0
    for job_id in ids:
        try:
            result = accept_import_job(session, tenant_id, job_id)
        except core.RealityError:
            failed += 1
        else:
            accepted += int(result is not None)
    return accepted, failed


def accept_fixed_setup(session, tenant_id, tool):
    """Confirm the retained closed setup definition with a real company owner."""
    from reality.db.core import ChangeProposal
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    proposal = session.scalar(
        select(ChangeProposal)
        .where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == f"tool:{tool}",
            ChangeProposal.status == "executed",
        )
        .order_by(ChangeProposal.created_at)
        .limit(1)
    )
    if proposal is None:
        proposal = create_change_proposal(session, tenant_id, tool, {})
    return approve_and_execute_proposal(
        session,
        tenant_id,
        proposal.id,
        confirmed=True,
        confirming_principal=explicit_owner(session, tenant_id),
    )


def accept_demo_setup(session, tenant):
    return accept_fixed_setup(session, tenant.id, "demo_seed")


def accept_normal_month(session, tenant_id):
    from decimal import Decimal

    proposal = accept_fixed_setup(session, tenant_id, "normal_month")
    output = json.loads(proposal.output)
    return {
        key: Decimal(value) if key in {"physical", "reserved", "receivable"} else value
        for key, value in output.items()
    }


def _accept_financial_fixture(session, tenant_id, source, stated, profile):
    """Retain fully stated fixture evidence, then ask its real owner for an exact decision."""
    from reality.services.intake import prepare_intake

    commit = not session.in_nested_transaction()
    if (
        "party_id" in json.loads(source.payload)
        or json.loads(source.payload).get("schema_version") == 1
    ):
        job = session.scalar(
            select(ImportJob).where(
                ImportJob.tenant_id == tenant_id,
                ImportJob.source_record_id == source.id,
            )
        )
    else:
        body = stated.model_dump(mode="json")
        source, job = core.enqueue_source(
            session,
            tenant_id,
            source.source_system,
            source.source_type,
            source.external_id,
            body,
            context={"profile": profile},
            _commit=commit,
        )
    proposal = prepare_intake(session, tenant_id, job.id, _commit=commit)
    digest = review_intake(session, tenant_id, proposal.id)["digest"]
    proposal = apply_prepared_intake(
        session,
        tenant_id,
        proposal.id,
        digest,
        confirmed=True,
        principal=explicit_owner(session, tenant_id),
        _commit=commit,
    )
    assert proposal.status == "executed"
    records = json.loads(proposal.output)["records"]
    document = next(
        core._tenant_record_read(session, Document, tenant_id, row["id"])
        for row in records
        if row["type"] == "document"
    )
    return source, document, records


def accept_normalized_invoice(session, tenant_id, source, invoice):
    from reality.db.core import LedgerEntry

    source, document, records = _accept_financial_fixture(
        session, tenant_id, source, invoice, "sales_invoice.v1"
    )
    lines = [
        core._tenant_record_read(session, DocumentLine, tenant_id, row["id"])
        for row in records
        if row["type"] == "document_line"
    ]
    entries = [
        core._tenant_record_read(session, LedgerEntry, tenant_id, row["id"])
        for row in records
        if row["type"] == "ledger_entry"
    ]
    return source, document, lines, entries


def accept_normalized_payment(session, tenant_id, source, payment):
    from reality.db.core import LedgerEntry, SettlementAllocation
    from reality.services.payment_intake import (
        Resolution,
        prepare_customer_payment,
        resolve_references,
    )

    resolution = resolve_references(
        session,
        tenant_id,
        payment.party_id,
        payment.currency,
        payment.references,
        source_system="demo_data"
        if source.source_system == "normalized_fixture"
        else source.source_system,
    )
    details = prepare_customer_payment(session, tenant_id, source, payment)
    resolution = Resolution(resolution.invoices, tuple(details["issues"]))
    source, document, records = _accept_financial_fixture(
        session, tenant_id, source, payment, "customer_payment.v1"
    )
    entries = [
        core._tenant_record_read(session, LedgerEntry, tenant_id, row["id"])
        for row in records
        if row["type"] == "ledger_entry"
    ]
    allocations = [
        core._tenant_record_read(session, SettlementAllocation, tenant_id, row["id"])
        for row in records
        if row["type"] == "settlement_allocation"
    ]
    return (
        source,
        document,
        entries,
        allocations[0] if allocations else None,
        resolution,
    )
