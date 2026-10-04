"""Spec 351 FR-013–016: required, explicit correspondence context for all partners."""

import json

import pytest
from sqlalchemy import func, select
from test_agent_email_handoffs import capture, claim, message, proposal, report

from reality.db.core import Fact, SourceRecord
from reality.services.core import InvalidOperation, NotFound, create_tenant
from reality.services.emails import capture_email, email_history
from reality.tools.application import approve_and_execute_proposal


def refs(business, kind="party"):
    return [
        {
            "kind": kind,
            "id": getattr(business, "supplier" if kind == "party" else kind).id,
        }
    ]


@pytest.mark.parametrize("references", [None, [], [{"kind": "party", "id": "missing"}]])
def test_context_required_before_any_source_write(session, business, references):
    before = session.scalar(select(func.count()).select_from(SourceRecord))
    args = {
        "origin": "agent",
        "retry_key": "required",
        "direction": "inbound",
        "message": message(),
    }
    if references is not None:
        args["business_references"] = references
    with pytest.raises((InvalidOperation, NotFound)):
        capture_email(session, business.tenant.id, args)
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before


def test_supplier_and_item_context_are_explicit_queryable_and_not_facts(
    session, business
):
    # Party role is business data; correspondence must not restrict it to customers.
    linked = refs(business) + refs(business, "item")
    before = session.scalar(select(func.count()).select_from(Fact))
    stored = capture(session, business.tenant.id, business_references=linked)
    for reference in linked:
        history = email_history(
            session, business.tenant.id, {"business_reference": reference}
        )
        assert history["page"]["total"] == 1
        assert history["items"][0]["source_id"] == stored["source_id"]
        assert history["items"][0]["subject"] == message()["subject"]
    original = email_history(
        session, business.tenant.id, {"source_id": stored["source_id"]}
    )
    assert [
        {"kind": r["kind"], "id": r["id"]} for r in original["business_references"]
    ] == sorted(linked, key=lambda r: (r["kind"], r["id"]))
    assert session.scalar(select(func.count()).select_from(Fact)) == before


def test_context_replay_and_correction_preserve_immutable_versions(session, business):
    first = capture(session, business.tenant.id, business_references=refs(business))
    assert (
        capture(session, business.tenant.id, business_references=refs(business))[
            "source_id"
        ]
        == first["source_id"]
    )
    corrected = capture(
        session, business.tenant.id, business_references=refs(business, "item")
    )
    assert corrected["source_id"] != first["source_id"]
    assert corrected["version"] == first["version"] + 1
    assert (
        email_history(
            session, business.tenant.id, {"business_reference": refs(business)[0]}
        )["items"][0]["source_id"]
        == first["source_id"]
    )


def test_context_refuses_cross_tenant_and_duplicate_memberships(session, business):
    other = create_tenant(session, "Other")
    with pytest.raises(NotFound):
        capture(session, other.id, business_references=refs(business))
    with pytest.raises(InvalidOperation):
        capture(session, business.tenant.id, business_references=refs(business) * 2)
    with pytest.raises(NotFound):
        email_history(session, other.id, {"business_reference": refs(business)[0]})
    with pytest.raises(NotFound):
        proposal(session, other.id, business_references=refs(business))


def test_context_history_pages_and_decision_report_chain(session, business):
    reference = refs(business)[0]
    for index in range(3):
        capture(
            session,
            business.tenant.id,
            retry_key=f"page-{index}",
            business_references=[reference],
        )
    first = email_history(
        session,
        business.tenant.id,
        {"business_reference": reference, "page": 1, "size": 2},
    )
    second = email_history(
        session,
        business.tenant.id,
        {"business_reference": reference, "page": 2, "size": 2},
    )
    assert first["page"]["total"] == 3
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert not (
        {r["source_id"] for r in first["items"]}
        & {r["source_id"] for r in second["items"]}
    )
    p = proposal(session, business.tenant.id, business_references=[reference])
    pending = email_history(
        session, business.tenant.id, {"business_reference": reference}
    )
    assert pending["related_decisions"][0]["proposal_id"] == p.id
    approve_and_execute_proposal(session, business.tenant.id, p.id, confirmed=True)
    execution = claim(session, business.tenant.id, p)
    assert execution["business_references"] == [reference]
    result = report(session, business.tenant.id, execution)
    actual = email_history(
        session, business.tenant.id, {"source_id": result["actual_source_id"]}
    )
    assert actual["business_references"][0]["id"] == reference["id"]
    assert actual["decision"]["proposal_id"] == p.id
    assert json.loads(p.input)["business_references"] == [reference]


def test_history_selector_is_exclusive(session, business):
    with pytest.raises(InvalidOperation):
        email_history(
            session,
            business.tenant.id,
            {"source_id": "missing", "business_reference": refs(business)[0]},
        )


def test_order_invoice_and_other_party_roles_use_existing_business_objects(
    session, business
):
    from reality.services.core import create_commitment, create_document, create_party

    order = create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "2",
        None,
    )
    invoice = create_document(
        session,
        business.tenant.id,
        "supplier_invoice",
        "SUP-1",
        business.supplier.id,
        "20",
    )
    carrier = create_party(
        session, business.tenant.id, "Carrier service supplier", "supplier"
    )
    references = [
        {"kind": "party", "id": business.supplier.id},
        {"kind": "party", "id": carrier.id},
        {"kind": "commitment", "id": order.id},
        {"kind": "document", "id": invoice.id},
    ]
    captured = capture(session, business.tenant.id, business_references=references)
    for reference in references:
        history = email_history(
            session, business.tenant.id, {"business_reference": reference}
        )
        assert history["items"][0]["source_id"] == captured["source_id"]
    unrelated = email_history(
        session,
        business.tenant.id,
        {"business_reference": {"kind": "party", "id": business.customer.id}},
    )
    assert unrelated["items"] == []


def test_api_context_contract_and_inspector_navigation(session, business):
    from fastapi.testclient import TestClient

    from reality.web.api import database_session
    from reality.web.app import app

    def database():
        yield session

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            args = {
                "origin": "agent",
                "retry_key": "api-linked",
                "direction": "inbound",
                "message": message(),
            }
            assert client.post(base + "/email/capture", json=args).status_code == 422
            args["business_references"] = refs(business)
            stored = client.post(base + "/email/capture", json=args)
            assert stored.status_code == 200, stored.text
            history = client.get(
                base + "/email/history",
                params={"business_kind": "party", "business_id": business.supplier.id},
            )
            assert history.status_code == 200, history.text
            assert history.json()["items"][0]["source_id"] == stored.json()["source_id"]
            inspector = client.get(base + f"/inspector/party/{business.supplier.id}")
            assert inspector.json()["email_history_identity"] == {
                "business_kind": "party",
                "business_id": business.supplier.id,
            }
            source = client.get(
                base + f"/inspector/source_record/{stored.json()['source_id']}"
            )
            assert source.json()["email_history_identity"] == {
                "source_id": stored.json()["source_id"]
            }
            from reality.services.core import create_lot

            business.item.tracking_type = "lot"
            session.flush()
            lot = create_lot(
                session,
                business.tenant.id,
                business.item.id,
                "LOT-EMAIL",
                expires_at="2026-12-01",
            )
            lot_inspector = client.get(base + f"/inspector/lot/{lot.id}")
            assert lot_inspector.status_code == 200, lot_inspector.text
            assert lot_inspector.json()["email_history_identity"] == {
                "business_kind": "lot",
                "business_id": lot.id,
            }

            assert (
                client.get(
                    base + "/email/history", params={"business_kind": "party"}
                ).status_code
                == 400
            )
    finally:
        app.dependency_overrides.pop(database_session, None)


def test_imported_context_cannot_fabricate_memberships(session, business):
    from reality.services.core import enqueue_source

    source, _ = enqueue_source(
        session,
        business.tenant.id,
        "fake-agent",
        "email_message",
        "forged",
        {
            "direction": "inbound",
            "message": message(),
            "business_references": refs(business),
        },
    )
    assert (
        email_history(session, business.tenant.id, {"source_id": source.id})[
            "context_missing"
        ]
        is True
    )
    assert (
        email_history(
            session, business.tenant.id, {"business_reference": refs(business)[0]}
        )["items"]
        == []
    )


def test_attachment_context_uses_its_linked_original_message(session, business):
    stored = capture(
        session,
        business.tenant.id,
        business_references=refs(business),
        message=message(
            attachments=[
                {
                    "part_id": "missing-file",
                    "filename": "Original.pdf",
                    "missing_reason": "Not supplied",
                }
            ]
        ),
    )
    attachment = email_history(
        session, business.tenant.id, {"source_id": stored["attachment_source_ids"][0]}
    )
    assert attachment["business_references"][0]["id"] == business.supplier.id
    assert attachment["context_missing"] is False
