"""Spec 354: a received payment is proposed before posting or allocation."""

import json

import pytest
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Document, LedgerEntry
from reality.services import core
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake


def prepared_payment(session, business, external_id="payment-1"):
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "bank",
        "customer_payment",
        external_id,
        {
            "party_id": business.customer.id,
            "amount": "41.29",
            "currency": "EUR",
            "effective_at": "2026-09-12T10:00:00Z",
            "external_payment_id": external_id,
            "payment_number": f"PAY-{external_id}",
            "references": [],
            "remittance_text": "Received bank statement",
        },
        context={"profile": "customer_payment.v1"},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    return source, proposal


def test_financial_prepare_is_non_posting(session, business):
    source, proposal = prepared_payment(session, business)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["effects"][0]["arguments"]["amount"] == "41.29"
    assert review["plan"]["source_record_id"] == source.id
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_unmatched_payment_can_be_accepted_explicitly(
    session, business, scheduled_owner
):
    from reality.services.memberships import Principal

    source, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    result = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    receipt = json.loads(result.output)
    assert receipt["source_record_id"] == source.id
    assert result.decided_by_user_id == scheduled_owner.id
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    assert session.scalar(select(Document)).gross_amount == core.decimal("41.29")
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.event_type == "ledger.posted",
        )
    )
    assert event.action_id == proposal.id
    assert event.source_record_id == source.id
    assert {row["id"] for row in json.loads(event.payload)["entries"]} == {
        row.id for row in session.scalars(select(LedgerEntry))
    }


def test_financial_review_does_not_grant_member_owner_authority(
    session, business, scheduled_owner
):
    from reality.db.core import TenantMembership
    from reality.services.memberships import Principal

    _, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    member = session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == business.tenant.id,
            TenantMembership.user_id == scheduled_owner.id,
        )
    )
    member.role = "member"
    session.commit()
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_unrelated_financial_sibling_does_not_stale_payment(
    session, business, scheduled_owner
):
    from reality.services import intake_batches, scheduled_jobs
    from reality.services.memberships import Principal

    entries = []
    for index in range(2):
        _, proposal = prepared_payment(session, business, f"independent-{index}")
        entries.append(
            {
                "proposal_id": proposal.id,
                "digest": review_intake(session, business.tenant.id, proposal.id)[
                    "digest"
                ],
            }
        )
    batch = intake_batches.prepare_batch(
        session, business.tenant.id, entries, request_id="independent-finance"
    )
    intake_batches.approve_batch(
        session,
        business.tenant.id,
        batch.id,
        json.loads(batch.input)["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    run = scheduled_jobs.claim_next(session, business.tenant.id)
    session.commit()
    scheduled_jobs.execute_claim(session, business.tenant.id, run.id, run.claim_token)
    session.commit()
    status = intake_batches.batch_status(session, business.tenant.id, batch.id)
    assert [row["disposition"] for row in status["results"]] == ["applied", "applied"]
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 4


def test_nested_payment_cannot_substitute_reviewed_cash_account(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services.memberships import Principal

    alternate = reviewed_create_account(
        session,
        business.tenant.id,
        code="cash-alternate",
        name="Alternate cash",
        role="cash",
    )
    _, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    original = core.post_ledger

    def changed(session, tenant_id, *args, **kwargs):
        kwargs["account_ids"] = {**kwargs["account_ids"], "cash": alternate["id"]}
        return original(session, tenant_id, *args, **kwargs)

    monkeypatch.setattr(core, "post_ledger", changed)
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_nested_payment_cannot_change_reviewed_document_day(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services.memberships import Principal

    _, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    original = core.create_document

    def changed(session, tenant_id, *args, **kwargs):
        kwargs["document_date"] = "2030-01-01"
        return original(session, tenant_id, *args, **kwargs)

    monkeypatch.setattr(core, "create_document", changed)
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def prepared_invoice(session, business, external_id="reviewed-invoice"):
    from test_payment_intake import _normalised_invoice, _order, _term

    _order(session, business, external_id=external_id)
    _term(session, business.tenant.id)
    invoice = _normalised_invoice(business, external_id, f"INV-{external_id}")
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "provider",
        "sales_invoice",
        external_id,
        invoice.model_dump(mode="json"),
        context={"profile": "sales_invoice.v1"},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    return source, proposal


def test_invoice_is_reviewed_before_evidence_and_posting(
    session, business, scheduled_owner
):
    from reality.services.memberships import Principal

    source, proposal = prepared_invoice(session, business)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.type == "sales_invoice")
        )
        == 0
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    result = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    receipt = json.loads(result.output)
    assert receipt["source_record_id"] == source.id
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.type == "sales_invoice")
        )
        == 1
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2
    again = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review["digest"],
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert json.loads(again.output) == receipt


def test_selected_invoice_allocation_change_refuses_combined_payment(
    session, business, scheduled_owner
):
    from test_payment_intake import _invoice

    from reality.services.memberships import Principal

    _, invoice, _, _ = _invoice(session, business)
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "bank",
        "customer_payment",
        "matched-payment",
        {
            "party_id": business.customer.id,
            "amount": "41.29",
            "currency": "EUR",
            "effective_at": "2026-09-12T10:00:00Z",
            "external_payment_id": "matched-payment",
            "payment_number": "PAY-MATCHED",
            "references": [{"type": "invoice_number", "value": invoice.number}],
        },
        context={"profile": "customer_payment.v1"},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert len(review["plan"]["effects"]) == 2
    core.post_customer_payment(session, business.tenant.id, invoice.id, "10")
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            review["digest"],
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before
    assert (
        session.scalar(select(Document).where(Document.source_record_id == source.id))
        is None
    )


def test_nested_payment_posting_cannot_use_another_document(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services.memberships import Principal

    existing = core.record_customer_payment(
        session,
        business.tenant.id,
        business.customer.id,
        "41.29",
        payment_number="EXISTING-PAYMENT",
    )
    _, proposal = prepared_payment(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    before = session.scalar(select(func.count()).select_from(Document))
    original = core.post_ledger

    def changed(session, tenant_id, document_id, *args, **kwargs):
        return original(session, tenant_id, existing[0].document_id, *args, **kwargs)

    monkeypatch.setattr(core, "post_ledger", changed)
    with pytest.raises(core.InvalidOperation):
        apply_prepared_intake(
            session,
            business.tenant.id,
            proposal.id,
            digest,
            confirmed=True,
            principal=Principal(scheduled_owner.id),
        )
    assert session.scalar(select(func.count()).select_from(Document)) == before
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


def test_unrelated_posting_does_not_stale_selected_invoice_payment(
    session, business, scheduled_owner
):
    from test_payment_intake import _invoice

    from reality.services.memberships import Principal

    _, invoice, _, _ = _invoice(session, business)
    _, job = core.enqueue_source(
        session,
        business.tenant.id,
        "bank",
        "customer_payment",
        "matched-independent",
        {
            "party_id": business.customer.id,
            "amount": "41.29",
            "currency": "EUR",
            "effective_at": "2026-09-12T10:00:00Z",
            "external_payment_id": "matched-independent",
            "references": [{"type": "invoice_number", "value": invoice.number}],
        },
        context={"profile": "customer_payment.v1"},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    core.record_customer_payment(
        session,
        business.tenant.id,
        business.customer.id,
        "15",
        payment_number="UNRELATED",
    )
    result = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert result.status == "executed"
    assert core.open_invoice_amount(
        session, business.tenant.id, invoice.id
    ) == core.decimal("58.71")


def test_outgoing_payment_review_does_not_execute_bank_transfer(
    session, business, scheduled_owner
):
    from reality.services.memberships import Principal

    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "bank",
        "supplier_payment",
        "outgoing-1",
        {
            "party_id": business.supplier.id,
            "amount": "18.75",
            "currency": "EUR",
            "effective_at": "2026-09-12T10:00:00Z",
            "external_payment_id": "outgoing-1",
            "payment_number": "OUT-1",
        },
        context={"profile": "supplier_payment.v1"},
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    result = apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        digest,
        confirmed=True,
        principal=Principal(scheduled_owner.id),
    )
    assert json.loads(result.output)["source_record_id"] == source.id
    payment = session.scalar(
        select(Document).where(Document.type == "supplier_payment")
    )
    assert payment.gross_amount == core.decimal("18.75")
    assert sorted(
        (row.account, row.debit_credit, row.amount)
        for row in session.scalars(select(LedgerEntry))
    ) == [
        ("accounts_payable", "debit", core.decimal("18.75")),
        ("cash", "credit", core.decimal("18.75")),
    ]


def test_prepared_financial_review_names_canonical_defaults(session, business):
    _, proposal = prepared_payment(session, business)
    arguments = review_intake(session, business.tenant.id, proposal.id)["plan"][
        "effects"
    ][0]["arguments"]
    assert arguments["payment_number"] == "PAY-payment-1"
    _, invoice = prepared_invoice(session, business, "explicit-defaults")
    effects = review_intake(session, business.tenant.id, invoice.id)["plan"]["effects"]
    assert effects[0]["arguments"]["sales_channel"] == ""
    assert effects[1]["arguments"]["exchange_rate"] is None
    assert effects[1]["arguments"]["company_amounts"] is None


from intake_review_support import reviewed_create_account
