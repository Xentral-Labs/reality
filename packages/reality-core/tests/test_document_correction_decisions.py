"""Spec 356: current retained review owns manual header and line corrections."""

import inspect
import json
from datetime import timedelta
from decimal import Decimal

import pytest
from intake_review_support import (
    accept_shopify_order,
    explicit_owner,
    reviewed_manual_document_with_lines,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    SourceRecord,
    UserSession,
    now,
    uid,
)
from reality.domain.intake import canonical_json
from reality.services import core
from reality.tools import application

OPERATIONS = {"document_correct": "correct_manual_document", "document_lines_correct": "correct_manual_document_lines"}


def case(session, business, tool):
    document, _ = reviewed_manual_document_with_lines(session, business.tenant.id,
        "sales_order", "CORRECTION-ORIGINAL", business.customer.id,
        [{"item_id": business.item.id, "source_line_id": "1", "quantity": "2", "unit_price": "13", "gross_amount": "31"}], "31")
    if tool == "document_correct":
        return {"document_id": document.id, "document_type": "sales_order", "number": "CORRECTION-STATED", "party_id": business.customer.id, "amount": "37", "currency": "EUR", "customer_reference": "Actual corrected PO"}
    snapshot = core.manual_document_line_snapshot(session, business.tenant.id, document.id)
    return {"document_id": document.id, "expected_revision": snapshot["revision"],
        "lines": [{**line, "description": "Actual corrected description", "quantity": "3", "gross_amount": "41"} for line in snapshot["lines"]]}


def state(session, tenant):
    return {model.__tablename__: canonical_json([
        {column.name: getattr(row, column.name) for column in model.__table__.columns}
        for row in session.scalars(select(model).where(model.tenant_id == tenant).order_by(model.id))
    ]) for model in (Document, DocumentLine, BusinessEvent, SourceRecord, Commitment, Movement, LedgerEntry)}


@pytest.mark.parametrize("tool", OPERATIONS)
def test_direct_canonical_document_correction_requires_a_current_decision(session, business, tool):
    values = case(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        getattr(core, OPERATIONS[tool])(session, business.tenant.id, **values)
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_document_correction_requires_explicit_confirmation_of_actual_input(session, business, tool):
    values = case(session, business, tool)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner)
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("attack", ["changed", "repeated", "early_commit", "post_write_failure", "sibling_header"])
def test_document_correction_refuses_changed_or_partial_effects(session, business, monkeypatch, tool, attack):
    values = case(session, business, tool)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    before = state(session, business.tenant.id)
    original = getattr(application, OPERATIONS[tool])

    def callback(*args, **kwargs):
        bound = inspect.signature(original).bind(*args, **kwargs)
        if attack == "changed":
            if tool == "document_correct":
                bound.arguments["number"] = "Unreviewed replacement number"
            else:
                bound.arguments["lines"] = [{**line, "description": "Unreviewed replacement line"} for line in bound.arguments["lines"]]
            return original(*bound.args, **bound.kwargs)
        if attack == "early_commit":
            session.commit()
        if attack == "sibling_header":
            core.create_document(session, business.tenant.id, "sales_order", "UNRELATED-CORRECTION", business.customer.id, "97")
        result = original(*args, **kwargs)
        if attack == "repeated":
            original(*args, **kwargs)
        if attack == "post_write_failure":
            raise RuntimeError("Actual post-write correction failure")
        return result

    monkeypatch.setattr(application, OPERATIONS[tool], callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_document_correction_preserves_stated_values_actual_person_and_receipt_replay(session, business, tool):
    values = case(session, business, tool)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    receipt = application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    assert receipt.decided_by_user_id == owner.user_id
    assert receipt.status == "executed"
    output = json.loads(receipt.output)
    if tool == "document_correct":
        assert output["records"][0]["id"] == values["document_id"]
        row = session.get(Document, (business.tenant.id, values["document_id"]))
        assert row.number == values["number"] and row.gross_amount == Decimal(values["amount"])
    else:
        assert output["changed"] is True
        assert output["lines"][0]["description"] == "Actual corrected description"
        assert Decimal(output["lines"][0]["gross_amount"]) == Decimal(41)
    before = state(session, business.tenant.id)
    application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_document_correction_does_not_silently_adopt_changed_actual_document_context(session, business, tool):
    values = case(session, business, tool)
    owner = explicit_owner(session, business.tenant.id)
    initial = application.create_change_proposal(session, business.tenant.id, tool, values)
    second = application.create_change_proposal(session, business.tenant.id, "document_correct", {
        "document_id": values["document_id"], "document_type": "sales_order", "number": "SECOND-CONFIRMED", "party_id": business.customer.id, "amount": "31", "currency": "EUR",
    })
    application.approve_and_execute_proposal(session, business.tenant.id, second.id, confirming_principal=owner, confirmed=True)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(session, business.tenant.id, initial.id, confirming_principal=owner, confirmed=True)
    assert refused.value.code == "intake_review_stale"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("private", ["_commit", "_document_correction_review"])
def test_document_correction_callers_cannot_supply_private_execution_or_review_authority(session, business, tool, private):
    values = case(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        application.create_change_proposal(session, business.tenant.id, tool, {**values, private: False if private == "_commit" else {}})
    assert refused.value.code == "intake_review_invalid"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("confirmed", [False, True])
def test_document_correction_authenticated_http_requires_explicit_actual_person_confirmation(session, business, monkeypatch, tool, confirmed):
    from fastapi.testclient import TestClient

    from reality.web import api, app, auth

    values = case(session, business, tool)
    identity = values.pop("document_id")
    owner = explicit_owner(session, business.tenant.id)
    factory = sessionmaker(session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint")
    for module in (api, app, auth):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    token = uid("actual_correction_cookie")
    session.add(UserSession(id=uid("ses"), user_id=owner.user_id, token_hash=auth.digest(token), expires_at=now() + timedelta(days=1)))
    session.commit()
    before = state(session, business.tenant.id)
    proposals_before = set(session.scalars(select(core.ChangeProposal.id).where(core.ChangeProposal.tenant_id == business.tenant.id)))
    if tool == "document_correct":
        values["type"] = values.pop("document_type")
    if confirmed:
        values["confirmed"] = True
    suffix = "/line-correction" if tool == "document_lines_correct" else ""
    method = "PUT" if suffix else "PATCH"
    with TestClient(app.app) as browser:
        browser.cookies.set(auth.COOKIE_NAME, token)
        response = browser.request(method, f"/api/tenants/{business.tenant.id}/documents/{identity}{suffix}", json=values)
    session.expire_all()
    proposals = list(session.scalars(select(core.ChangeProposal).where(core.ChangeProposal.tenant_id == business.tenant.id, core.ChangeProposal.id.not_in(proposals_before))))
    if not confirmed:
        assert response.status_code == 400, response.text
        assert not proposals
        assert state(session, business.tenant.id) == before
    else:
        assert response.status_code == 200, response.text
        assert len(proposals) == 1
        assert proposals[0].status == "executed"
        assert proposals[0].decided_by_user_id == owner.user_id
        assert "confirmed" not in response.json()
        assert session.get(Document, (business.tenant.id, identity)).number == ("CORRECTION-STATED" if not suffix else "CORRECTION-ORIGINAL")


def test_corrected_external_source_version_is_raw_queue_intake_without_new_document_acceptance(session, business):
    from pathlib import Path

    payload = json.loads((Path(__file__).parents[1] / "fixtures/shopify/order_10473.json").read_text())
    original, document, _, _ = accept_shopify_order(session, business.tenant.id, payload, business.company.id, business.customer.id, business.location.id)
    retained_payload = original.payload
    before = {key: value for key, value in state(session, business.tenant.id).items() if key not in {"source_record", "business_event"}}
    updated = {**payload, "total_price": "71.23", "upstream_note": {"received": "actual changed source value"}}
    source, job = core.record_corrected_document_source(session, business.tenant.id, document.id, updated, source_version_at=now())
    assert job.status == "pending"
    assert source.id != original.id
    assert json.loads(source.payload) == updated
    assert original.payload == retained_payload
    try:
        core.process_import_job(session, business.tenant.id, job.id)
    except core.InterpretationNeedsReview:
        pass
    session.expire_all()
    after = {key: value for key, value in state(session, business.tenant.id).items() if key not in {"source_record", "business_event"}}
    assert after == before
    assert session.get(SourceRecord, (business.tenant.id, original.id)).payload == retained_payload


@pytest.mark.parametrize("tool", OPERATIONS)
def test_document_correction_retains_actual_decimal_statements_without_recalculation(session, business, tool):
    values = case(session, business, tool)
    stated = Decimal("37.1234")
    if tool == "document_correct":
        values["amount"] = stated
    else:
        values["lines"][0]["gross_amount"] = stated
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    prepared = json.loads(proposal.input)
    if tool == "document_correct":
        assert prepared["amount"] == "37.1234"
    else:
        assert prepared["lines"][0]["gross_amount"] == "37.1234"
    application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    model = Document if tool == "document_correct" else DocumentLine
    rows = list(session.scalars(select(model).where(model.tenant_id == business.tenant.id)))
    assert len(rows) == 1
    assert rows[0].gross_amount == stated


@pytest.mark.parametrize("tool", OPERATIONS)
def test_document_correction_prepares_public_defaults_before_execution(session, business, tool):
    values = case(session, business, tool)
    proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    prepared = json.loads(proposal.input)
    if tool == "document_correct":
        assert prepared["ship_to_party_id"] is None
        assert prepared["payment_term_code"] == ""
        assert prepared["document_date"] == ""
        assert prepared["ordered_at"] is None
    else:
        assert prepared["actor_context"] is None
    assert "_commit" not in prepared


@pytest.mark.parametrize("tool", OPERATIONS)
def test_document_correction_requires_renewed_review_after_an_actual_reference_decision(session, business, tool):
    from intake_review_support import (
        reviewed_create_payment_term,
        reviewed_update_item,
        reviewed_update_payment_term,
    )

    values = case(session, business, tool)
    if tool == "document_correct":
        term = reviewed_create_payment_term(session, business.tenant.id, "CORR14", "Correction term", 14)
        values["payment_term_code"] = term.code
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    if tool == "document_correct":
        reviewed_update_payment_term(session, business.tenant.id, term.id, term.code, term.name, 30)
    else:
        item = business.item
        reviewed_update_item(session, business.tenant.id, item.id, item.sku, "Separately confirmed item change", item.unit)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)changed|review|stale"):
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    assert state(session, business.tenant.id) == before
