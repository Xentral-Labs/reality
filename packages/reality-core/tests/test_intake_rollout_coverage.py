"""Spec 356: legacy queue entrypoints prepare meaning before any accepted effect."""

import json

import pytest
from intake_review_support import reviewed_create_payment_term
from sqlalchemy import func, select
from test_intake_admission import FIXTURE

from reality.db.core import ChangeProposal, Commitment, Document
from reality.services import core


def test_pending_job_cutover_is_safe(session, business):
    payload = json.loads(FIXTURE.read_text())
    _, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    prepared = core.process_import_job(session, business.tenant.id, job.id)
    assert isinstance(prepared, ChangeProposal)
    assert prepared.type == "tool:intake_apply" and prepared.status == "proposed"
    assert job.status == "awaiting_decision" and job.completed_at is None
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert session.scalar(select(func.count()).select_from(Commitment)) == 0
    assert (
        core.process_import_job(session, business.tenant.id, job.id).id == prepared.id
    )


def test_historical_provenance_is_honest(session, business):
    from reality.db.core import BusinessEvent, InterpretationOutcome

    payload = json.loads(FIXTURE.read_text())
    source, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    # Represent a pre-cutover terminal job without a retained Decision.
    job.status = "completed"
    job.completed_at = core.now()
    session.commit()
    original = (source.payload, job.input, job.completed_at, job.attempts)
    events = session.scalar(select(func.count()).select_from(BusinessEvent))
    proposals_before = session.scalar(select(func.count()).select_from(ChangeProposal))
    assert core.process_import_job(session, business.tenant.id, job.id) is None
    assert (source.payload, job.input, job.completed_at, job.attempts) == original
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == proposals_before
    assert session.scalar(select(func.count()).select_from(InterpretationOutcome)) == 0
    assert session.scalar(select(func.count()).select_from(BusinessEvent)) == events
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_unavailable_reviewer_does_not_turn_intake_into_business_effects(
    session, business
):
    from reality.demo.international import DEMO_DATA_CUSTOMERS
    from reality.integrations.demo_data import produce

    refs = {
        "parties": {
            "company": business.company.id,
            DEMO_DATA_CUSTOMERS[0][0]: business.customer.id,
        },
        "items": {key: business.item.id for key in ("P01", "P02", "P11", "P12")},
        "locations": {"A": business.location.id},
    }
    payload = produce(
        "reviewed-schedule", "reviewed-occurrence", "reviewed-seed", core.now(), refs
    )
    _, job = core.enqueue_source(
        session,
        business.tenant.id,
        "demo_data",
        "order",
        "reviewed-demo-order",
        payload,
        _commit=False,
    )
    prepared = core.process_import_job_bound(session, business.tenant.id, job.id)
    assert isinstance(prepared, ChangeProposal)
    assert prepared.status == "proposed"
    assert job.status == "awaiting_decision"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert session.scalar(select(func.count()).select_from(Commitment)) == 0


def test_unconfirmed_fixed_setup_cannot_accept_business_effects(session):
    import pytest

    tenant = core.create_tenant(session, "Unconfirmed fixed setup")
    with pytest.raises(core.InvalidOperation):
        core.ensure_demo(session, tenant)
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_live_demo_uses_real_decisions(session, business, scheduled_owner):
    from test_intake_agent_review import agent_context, owner_mandate, reviewed_evidence

    from reality.demo.international import DEMO_DATA_CUSTOMERS
    from reality.integrations.demo_data import produce
    from reality.services.intake_review import submit_agent_review

    tenant = business.tenant.id
    origin = core.create_source_system(session, tenant, "demo_data", "Reviewed demo")
    capability = core.create_source_capability(
        session, tenant, origin.id, "order", "sales_order"
    )
    refs = {
        "parties": {
            "company": business.company.id,
            DEMO_DATA_CUSTOMERS[0][0]: business.customer.id,
        },
        "items": {key: business.item.id for key in ("P01", "P02", "P11", "P12")},
        "locations": {"A": business.location.id},
    }
    payload = produce("named-review", "first-arrival", "seed", core.now(), refs)
    source, job = core.enqueue_source(
        session, tenant, "demo_data", "order", "named-demo-arrival", payload
    )
    proposal = core.process_import_job_bound(session, tenant, job.id)
    assert proposal.status == "proposed" and job.status == "awaiting_decision"
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    mandate_id, token = owner_mandate(
        session,
        business,
        scheduled_owner,
        scope_overrides={
            "source_system_id": origin.id,
            "capability_ids": [capability.id],
            "profiles": ["demo.order"],
            "amount_rule": {
                "currency": payload["currency"],
                "max_amount_per_unit": "10000",
                "max_amount_per_day": "100000",
            },
        },
    )
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        result = submit_agent_review(session, tenant, evidence)
    assert result.status == "executed"
    assert result.decided_via_token_id == token.id
    assert result.decided_by_user_id is None
    assert json.loads(result.output)["agent_review"]["mandate_id"] == mandate_id
    assert job.status == "completed"
    assert json.loads(source.payload) == payload
    assert session.scalar(select(func.count()).select_from(Document)) == 1


def test_demo_review_required_is_distinct_from_failed_execution(
    session, scheduled_owner, monkeypatch
):
    from conftest import record_by_id
    from test_demo_data_intake import _running_demo, _tick

    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.services import demo_data

    def ambiguous(*args, **kwargs):
        raise core.InterpretationNeedsReview("private unsupported meaning")

    monkeypatch.setattr("reality.services.intake._demo_order_plan", ambiguous)
    tenant, schedule = _running_demo(
        session, monkeypatch, scheduled_owner.id, "retained-review-case"
    )
    run_id, _ = _tick(session, tenant, schedule)
    run = record_by_id(session, ScheduledJobRun, run_id)
    assert run.status == "succeeded"
    assert run.result["counts"]["failed"] == 0
    assert run.result["counts"]["review_required"] == 1
    state = demo_data.status(session, tenant, scheduled_owner.id)
    assert state["review_required"] == state["pending"] == 1
    assert state["failed"] == state["imported"] == state["awaiting_decision"] == 0
    assert state["derived_state"] == "review_required"
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant)
        )
        == 0
    )


def test_confirmed_fixed_setup_does_not_authorize_later_intake(session):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    tenant = core.create_tenant(session, "Confirmed fixed setup")
    proposal = create_change_proposal(session, tenant.id, "demo_seed", {})
    result = approve_and_execute_proposal(
        session, tenant.id, proposal.id, confirmed=True
    )
    assert result.status == "executed"
    assert session.scalar(select(func.count()).select_from(Document)) == 1
    import pytest

    with pytest.raises(core.InvalidOperation):
        core.ensure_demo(
            session, core.create_tenant(session, "Other unconfirmed setup")
        )


def test_retired_interpreters_cannot_reuse_raw_or_action_id_as_approval(
    session, business
):
    import pytest

    from reality.services import (
        file_interpreters,
        payment_intake,
        shop_order_changes,
        shop_refunds,
    )

    source, _ = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        json.loads(FIXTURE.read_text()),
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    calls = [
        core._shopify_interpretation,
        file_interpreters.interpret_artifact,
        payment_intake.interpret_sales_invoice,
        payment_intake.interpret_customer_payment,
        shop_order_changes.apply_order_version,
        shop_refunds.interpret_shop_refund,
    ]
    with core.executing_proposal(business.tenant.id, "forged-post-hoc-action"):
        for call in calls:
            with pytest.raises(core.InvalidOperation) as refusal:
                call(session, business.tenant.id, source, {})
            assert refusal.value.code == "intake_approval_required"
    assert session.scalar(select(func.count()).select_from(Document)) == 0


@pytest.mark.parametrize("prepayment", [False, True])
def test_unstated_order_total_stays_unknown_in_delivery_readiness(
    session, business, tmp_path, monkeypatch, prepayment
):
    from intake_review_support import explicit_owner
    from test_artifact_intake_admission import prepare_file

    from reality.services.fulfillment_readiness import fulfillment_readiness
    from reality.services.intake import apply_prepared_intake, review_intake

    tenant = business.tenant.id
    if prepayment:
        term = reviewed_create_payment_term(
            session,
            tenant,
            "UNSTATED-PREPAY",
            "Prepayment",
            0,
            requires_prepayment=True,
        )
        business.customer.payment_term_id = term.id
        session.commit()
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        "2",
        to_location_id=business.location.id,
    )
    content = f"order_id,sku,party_name,location,quantity,unit_price\nUNSTATED-DELIVERY,{business.item.sku},{business.customer.name},{business.location.name},2,10\n".encode()
    _, proposal = prepare_file(
        session, business, "sales_order", content, tmp_path, monkeypatch
    )
    review = review_intake(session, tenant, proposal.id)
    receipt = apply_prepared_intake(
        session,
        tenant,
        proposal.id,
        review["digest"],
        confirmed=True,
        principal=explicit_owner(session, tenant),
    )
    commitment_id = next(
        row["id"]
        for row in json.loads(receipt.output)["records"]
        if row["type"] == "commitment"
    )
    if prepayment:
        # Fixture the retained policy of an accepted order; its total remains unstated.
        order = session.get(
            Document,
            (tenant, session.get(Commitment, (tenant, commitment_id)).document_id),
        )
        order.payment_term_id = term.id
        session.flush()
    core.reserve(session, tenant, commitment_id)
    readiness = fulfillment_readiness(session, tenant, commitment_id)
    assert readiness.required_amount is None
    assert readiness.as_dict()["required_amount"] is None
    assert readiness.ship_ready is not prepayment
    if prepayment:
        assert readiness.blocker_codes == ("prepayment_amount_unstated",)
        assert readiness.remaining_amount is None


def test_fixed_setup_proposal_requires_explicit_confirmation(session):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    tenant = core.create_tenant(session, "Explicit fixed definition")
    proposal = create_change_proposal(session, tenant.id, "demo_seed", {})
    with pytest.raises(core.InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, tenant.id, proposal.id, confirmed=False)
    session.refresh(proposal)
    assert proposal.status == "proposed" and proposal.decided_at is None
    assert session.scalar(select(func.count()).select_from(Document)) == 0


@pytest.mark.parametrize("origin", ["demo_data", "received_bank_custom"])
def test_explicit_normalized_financial_profile_keeps_its_source_origin(
    session, business, origin
):
    from reality.services.intake import review_intake

    payload = {
        "party_id": business.customer.id,
        "amount": "17.19",
        "currency": "EUR",
        "effective_at": "2026-09-10T08:00:00Z",
        "external_payment_id": "normalized-demo",
        "references": [],
    }
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        origin,
        "payment",
        "normalized-demo",
        payload,
        context={"profile": "customer_payment.v1"},
    )
    proposal = core.process_import_job(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["profile"] == "customer_payment.v1"
    assert review["plan"]["source_record_id"] == source.id
    assert json.loads(source.payload) == payload
    assert source.source_system == origin
    assert job.status == "awaiting_decision"
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_unknown_declared_profile_keeps_raw_without_prepared_or_accepted_effects(
    session, business
):
    proposals_before = session.scalar(select(func.count()).select_from(ChangeProposal))
    payload = {"amount": "17.19", "arbitrary_instruction": "approve this payment"}
    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "received_bank_custom",
        "payment",
        "unsupported-profile",
        payload,
        context={"profile": "approve_everything.v1"},
    )
    assert job.status == "unmapped"
    assert core.process_import_job(session, business.tenant.id, job.id) is None
    assert (
        core.retry_import_job(session, business.tenant.id, job.id).status == "unmapped"
    )
    assert json.loads(source.payload) == payload
    assert session.scalar(select(func.count()).select_from(Document)) == 0
    assert session.scalar(select(func.count()).select_from(ChangeProposal)) == proposals_before


def test_completed_fixed_setup_receipt_replays_without_new_confirmation(session):
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    tenant = core.create_tenant(session, "Retained fixed receipt")
    proposal = create_change_proposal(session, tenant.id, "demo_seed", {})
    first = approve_and_execute_proposal(
        session, tenant.id, proposal.id, confirmed=True
    )
    retained = first.output
    replay = approve_and_execute_proposal(session, tenant.id, proposal.id)
    assert replay.id == first.id and replay.output == retained
    assert session.scalar(select(func.count()).select_from(Document)) == 1


def test_retired_external_stock_file_writer_cannot_accept_raw(session, business):
    from reality.db.core import ExternalStockStatement
    from reality.services.core import executing_proposal
    from reality.services.external_stock import _record_file_rows

    rows = [
        {"sku": business.item.sku, "location": business.location.name, "quantity": "7"}
    ]
    source, _, _ = core.store_source_record(
        session,
        business.tenant.id,
        "csv",
        "external_stock",
        "retired-stock",
        {"rows": rows},
    )
    for action in [None, "forged-stock-approval"]:
        with executing_proposal(business.tenant.id, action):
            with pytest.raises(core.InvalidOperation) as refusal:
                _record_file_rows(session, business.tenant.id, source, rows)
            assert refusal.value.code == "intake_approval_required"
        assert (
            session.scalar(select(func.count()).select_from(ExternalStockStatement))
            == 0
        )


@pytest.mark.parametrize(
    "operation,model,args",
    [
        ("create_party", "Party", ("Unapproved customer", "customer")),
        ("create_item", "Item", ("UNAPPROVED-SKU", "Unapproved item")),
        ("create_location", "Location", ("Unapproved warehouse",)),
    ],
)
@pytest.mark.parametrize("auth_mode", ["enabled", "disabled"])
def test_direct_canonical_master_calls_require_a_decision(
    session, business, monkeypatch, operation, model, args, auth_mode
):
    from reality.db import core as records

    monkeypatch.setenv("REALITY_AUTH_MODE", auth_mode)
    table = getattr(records, model)
    before = session.scalar(select(func.count()).select_from(table))
    with core.executing_proposal(business.tenant.id, "arbitrary-action-tag"):
        with pytest.raises(core.InvalidOperation) as refusal:
            getattr(core, operation)(session, business.tenant.id, *args, _commit=False)
        assert refusal.value.code == "intake_approval_required"
    assert session.scalar(select(func.count()).select_from(table)) == before


@pytest.mark.parametrize("attack", ["replace_intent", "repeat_effect", "commit_midway"])
def test_master_confirmation_cannot_authorize_callback_changes(session, business, monkeypatch, attack):
    from intake_review_support import explicit_owner

    from reality.db.core import Party, SourceRecord
    from reality.tools.application import (
        approve_and_execute_proposal,
        create_change_proposal,
    )

    before = {model: session.scalar(select(func.count()).select_from(model)) for model in [Party, SourceRecord]}
    proposal = create_change_proposal(session, business.tenant.id, "party_create", {"records": [{"name": "Exact reviewed partner", "roles": ["customer"]}]})
    original = core.create_party

    def changed(db, tenant, **arguments):
        if attack == "replace_intent":
            arguments["name"] = "Different unreviewed partner"
        if attack == "repeat_effect":
            original(db, tenant, **arguments)
        result = original(db, tenant, **arguments)
        if attack == "commit_midway":
            db.commit()
        return result

    monkeypatch.setattr(core, "create_party", changed)
    with pytest.raises(core.InvalidOperation) as refusal:
        approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=explicit_owner(session, business.tenant.id), confirmed=True)
    assert refusal.value.code == {"replace_intent": "intake_review_invalid", "repeat_effect": "intake_approval_required", "commit_midway": "intake_partial_commit_forbidden"}[attack]
    for model, count in before.items():
        assert session.scalar(select(func.count()).select_from(model)) == count
    assert session.get(ChangeProposal, (business.tenant.id, proposal.id)).status == "failed"


@pytest.mark.parametrize("attack", ["replace_intent", "repeat_effect", "commit_midway"])
def test_confirmed_company_creation_cannot_authorize_extra_effects(
    session, scheduled_owner, monkeypatch, attack
):
    from reality.db.core import Party, SourceRecord, Tenant
    from reality.services import company_setup

    models = [Tenant, Party, SourceRecord]
    before = {model: session.scalar(select(func.count()).select_from(model)) for model in models}
    original = core.create_party

    def changed(db, tenant, **arguments):
        if attack == "replace_intent":
            arguments["name"] = "Unreviewed company partner"
        if attack == "repeat_effect":
            original(db, tenant, **arguments)
        result = original(db, tenant, **arguments)
        if attack == "commit_midway":
            db.commit()
        return result

    monkeypatch.setattr(company_setup, "create_party", changed)
    with pytest.raises(core.InvalidOperation) as refusal:
        company_setup.create_company(
            session, scheduled_owner.id, f"boundary-company-{attack}",
            "Exactly confirmed company", "business", "empty", confirmed=True,
        )
    assert refusal.value.code == {
        "replace_intent": "intake_review_invalid",
        "repeat_effect": "intake_approval_required",
        "commit_midway": "intake_partial_commit_forbidden",
    }[attack]
    for model, count in before.items():
        assert session.scalar(select(func.count()).select_from(model)) == count
