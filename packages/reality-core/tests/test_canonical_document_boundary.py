"""Spec 356 FR-001–FR-003: normalized evidence needs actual consent."""
import pytest
from sqlalchemy import func, select

from reality.db.core import ChangeProposal, Document, DocumentLine
from reality.services import core
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def document_arguments(business):
    return {"document_type": "sales_order", "number": "EXACT-DOCUMENT", "party_id": business.customer.id,
            "lines": [{"item_id": business.item.id, "quantity": "2", "unit_price": "3", "gross_amount": "5"}], "gross_amount": "5"}


@pytest.mark.parametrize("auth_mode", ["enabled", "disabled"])
def test_direct_normalized_document_cannot_reuse_a_real_executed_action(session, business, monkeypatch, auth_mode):
    monkeypatch.setenv("REALITY_AUTH_MODE", auth_mode)
    tenant = business.tenant.id
    before = session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant))
    unrelated = session.scalar(select(ChangeProposal.id).where(ChangeProposal.tenant_id == tenant, ChangeProposal.status == "executed").limit(1))
    with core.executing_proposal(tenant, unrelated), pytest.raises(core.InvalidOperation) as refused:
        core.create_manual_document_with_lines(session, tenant, **document_arguments(business), action_id=unrelated, _commit=False)
    assert refused.value.code == "intake_approval_required"
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant)) == before
    assert session.scalar(select(func.count()).select_from(DocumentLine).where(DocumentLine.tenant_id == tenant)) == 0


def test_manual_document_without_actual_confirmation_has_no_effect(session, business):
    tenant = business.tenant.id
    proposal = create_change_proposal(session, tenant, "document_create", document_arguments(business))
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(session, tenant, proposal.id, confirmed=False)
    assert refused.value.code == "review_confirmation_required"
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant)) == 0


@pytest.mark.parametrize("attack", ["changed", "repeated", "early_commit", "sibling_header", "sibling_stock"])
def test_document_callback_cannot_change_repeat_or_extend_the_confirmation(session, business, monkeypatch, attack):
    from reality.tools import application
    tenant = business.tenant.id
    original = core.create_manual_document_with_lines
    proposal = create_change_proposal(session, tenant, "document_create", document_arguments(business))
    def callback(db, company, **arguments):
        if attack == "changed":
            arguments["gross_amount"] = "999"
            arguments["lines"] = [{**line, "gross_amount": "999"} for line in arguments["lines"]]
        result = original(db, company, **arguments)
        if attack == "repeated":
            original(db, company, **arguments)
        if attack == "early_commit":
            db.commit()
        if attack == "sibling_header":
            core.create_document(db, company, "sales_order", "UNREVIEWED", business.customer.id, "1", _commit=False)
        if attack == "sibling_stock":
            core.record_movement(db, company, "receipt", business.item.id, "1", to_location_id=business.location.id, _commit=False)
        return result
    monkeypatch.setattr(application, "create_manual_document_with_lines", callback)
    with pytest.raises(core.InvalidOperation) as refused:
        approve_and_execute_proposal(session, tenant, proposal.id, confirmed=True)
    assert refused.value.code in {"intake_review_invalid", "intake_approval_required", "intake_partial_commit_forbidden"}
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant)) == 0
    assert session.scalar(select(func.count()).select_from(DocumentLine).where(DocumentLine.tenant_id == tenant)) == 0


def test_confirmed_document_preserves_stated_amounts_and_retained_decision(session, business):
    import json

    from intake_review_support import explicit_owner

    from reality.db.core import BusinessEvent
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = create_change_proposal(session, tenant, "document_create", document_arguments(business))
    receipt = approve_and_execute_proposal(session, tenant, proposal.id, confirming_principal=owner, confirmed=True)
    result = json.loads(receipt.output)
    document = session.scalar(select(Document).where(Document.tenant_id == tenant, Document.id == result["document_id"]))
    line = session.scalar(select(DocumentLine).where(DocumentLine.tenant_id == tenant, DocumentLine.document_id == document.id))
    assert document.gross_amount == line.gross_amount == 5
    assert line.quantity == 2 and line.unit_price == 3
    assert session.scalar(select(BusinessEvent.action_id).where(BusinessEvent.tenant_id == tenant, BusinessEvent.subject_id == document.id, BusinessEvent.event_type == "document.recorded")) == receipt.id
    assert approve_and_execute_proposal(session, tenant, proposal.id, confirming_principal=owner, confirmed=True).id == receipt.id
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant)) == 1


@pytest.mark.parametrize("field", ["action_id", "_action_id", "_commit", "_carry_unstated_amount"])
def test_public_document_proposal_cannot_claim_private_execution_fields(session, business, field):
    arguments = {**document_arguments(business), field: True}
    with pytest.raises(core.InvalidOperation) as refused:
        create_change_proposal(session, business.tenant.id, "document_create", arguments)
    assert refused.value.code == "intake_review_invalid"


@pytest.mark.parametrize("path", ["documents", "manual-orders"])
def test_http_evidence_without_explicit_confirmation_does_not_prepare_or_write(session, business, path):
    from test_master_data_api import api_client
    before = session.scalar(select(func.count()).select_from(ChangeProposal).where(ChangeProposal.tenant_id == business.tenant.id))
    arguments = document_arguments(business)
    if path == "documents":
        arguments["type"] = arguments.pop("document_type")
    else:
        arguments = {"direction": "sales", "number": "NO-CONSENT", "company_party_id": business.company.id,
                     "counterparty_id": business.customer.id, "location_id": business.location.id,
                     "lines": arguments["lines"], "gross_amount": arguments["gross_amount"]}
    from reality.web.app import app
    client = api_client(session)
    try:
        response = client.post(f"/api/tenants/{business.tenant.id}/{path}", json=arguments)
    finally:
        client.close()
        app.dependency_overrides.clear()
    assert response.status_code == 400
    assert session.scalar(select(func.count()).select_from(ChangeProposal).where(ChangeProposal.tenant_id == business.tenant.id)) == before
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == business.tenant.id)) == 0



@pytest.mark.parametrize("writer", ["create_manual_document_with_lines", "create_commitment"])
def test_one_approved_import_command_cannot_repeat_its_canonical_invocation(session, business, monkeypatch, writer):
    from test_intake_admission import prepare

    from reality.db.core import Commitment
    from reality.services.intake import apply_prepared_intake, review_intake
    _, _, proposal = prepare(session, business)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    original = getattr(core, writer)
    def callback(*args, **arguments):
        result = original(*args, **arguments)
        original(*args, **arguments)
        return result
    monkeypatch.setattr(core, writer, callback)
    with pytest.raises(core.InvalidOperation) as refused:
        apply_prepared_intake(session, business.tenant.id, proposal.id, digest, confirmed=True)
    assert refused.value.code == "intake_approval_required"
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == business.tenant.id)) == 0
    assert session.scalar(select(func.count()).select_from(Commitment).where(Commitment.tenant_id == business.tenant.id)) == 0
