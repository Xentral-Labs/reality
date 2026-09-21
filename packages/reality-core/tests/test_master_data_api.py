from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from conftest import record_by_id
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    AppUser,
    ChatMessage,
    ChatSession,
    CompanyInvitation,
    Document,
    DocumentLine,
    InvitationDelivery,
    SecurityAuditEvent,
    TenantMembership,
    UserSession,
    now,
    uid,
)
from reality.services.core import (
    InvalidOperation,
    active_reserved,
    create_commitment,
    create_document,
    create_item,
    create_manual_document_with_lines,
    create_price_list,
    create_price_list_entry,
    create_source_capability,
    create_source_system,
    create_tenant,
    ensure_demo,
    ingest_shopify_order,
    observe_fact,
    open_invoice_amount,
    post_customer_payment,
    post_sales_invoice,
    record_movement,
    store_source_record,
)
from reality.services.memberships import Principal
from reality.services.reality_gaps import decide_gap
from reality.tools.application import (
    approve_and_execute_proposal,
    propose_tool,
    reject_proposal,
)
from reality.web import api as api_module
from reality.web import app as web_module
from reality.web import auth as auth_module

app = web_module.app


def api_client(session):
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def override_session():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = override_session
    return TestClient(app)


def test_reality_gap_http_exposes_conditional_rule_and_simulation(session, business):
    source, _, _, _ = ingest_shopify_order(
        session,
        business.tenant.id,
        {
            "id": "http-conditional",
            "name": "#HTTP-CONDITIONAL",
            "created_at": "2026-09-04T10:00:00Z",
            "currency": "EUR",
            "total_price": "1200.00",
            "line_items": [
                {
                    "id": "http-line",
                    "sku": business.item.sku,
                    "name": business.item.name,
                    "quantity": 1,
                    "price": "1200.00",
                }
            ],
        },
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    client = api_client(session)
    try:
        created = client.post(
            f"/api/tenants/{business.tenant.id}/reality-gaps",
            json={
                "question": "Which orders need review?",
                "intended_use": "Create a review queue",
                "origin": "web",
                "idempotency_key": "http-conditional-gap",
            },
        )
        assert created.status_code == 201
        gap = created.json()["gap"]
        decided = decide_gap(
            session,
            business.tenant.id,
            gap["id"],
            destination="fact",
            rationale="Explicit source threshold",
            expected_revision=gap["revision"],
            actor_user_id=None,
        )
        prepared = client.post(
            f"/api/tenants/{business.tenant.id}/reality-gaps/{gap['id']}/implementation",
            json={
                "expected_revision": decided.revision,
                "draft": {
                    "logical_name": "HTTP high-value review",
                    "source_system": "shopify",
                    "source_type": "order",
                    "conditions": [
                        {
                            "path": "total_price",
                            "operator": "greater_or_equal",
                            "value_type": "decimal",
                            "operand": "1000",
                        }
                    ],
                    "output_mode": "constant",
                    "constant_value": True,
                    "predicate": "order.requires_manual_review",
                    "subject_type": "commitment",
                    "subject_resolver": "source_document_commitments",
                    "value_type": "boolean",
                    "observed_at_mode": "source_received_at",
                },
            },
        )
        assert prepared.status_code == 200
        rule = prepared.json()["rules"][0]
        assert rule["conditions"][0]["operator"] == "greater_or_equal"
        assert rule["output_mode"] == "constant"
        assert rule["constant_value"] is True
        simulated = client.post(
            f"/api/tenants/{business.tenant.id}/reality-gaps/{gap['id']}/rules/{rule['id']}/simulate"
        )
        assert simulated.status_code == 200
        assert simulated.json()["expected_facts"] == 1
        assert simulated.json()["examples"][0]["source_record_id"] == source.id
    finally:
        app.dependency_overrides.clear()


def test_copilot_archive_retains_messages_and_decisions_are_tenant_wide(session):
    tenant = create_tenant(session, "Decision queue company")
    other = create_tenant(session, "Other decision company")
    client = api_client(session)
    try:
        created = client.post(f"/api/tenants/{tenant.id}/copilot/sessions")
        session_id = created.json()["id"]
        proposal = propose_tool(session, tenant.id, "demo_seed", {})
        foreign = propose_tool(session, other.id, "demo_seed", {})

        client.post(
            f"/api/tenants/{tenant.id}/copilot/sessions/{session_id}/messages",
            json={"message": "Explain Source Evidence Reality"},
        )
        message_ids = list(
            session.scalars(
                select(ChatMessage.id).where(ChatMessage.session_id == session_id)
            )
        )
        projected = client.get(f"/api/tenants/{tenant.id}/copilot").json()
        assert projected["sessions"][0]["message_count"] == len(message_ids)

        archived = client.delete(
            f"/api/tenants/{tenant.id}/copilot/sessions/{session_id}"
        )
        active = client.get(f"/api/tenants/{tenant.id}/copilot").json()
        archive = client.get(
            f"/api/tenants/{tenant.id}/copilot", params={"archived": True}
        ).json()
        pending = client.get(
            f"/api/tenants/{tenant.id}/change-proposals", params={"status": "pending"}
        ).json()["items"]

        assert archived.status_code == 204
        assert active["sessions"] == []
        assert active["proposals"] == []
        assert archive["sessions"][0]["id"] == session_id
        assert {row["id"] for row in pending} == {proposal.id}
        assert foreign.id not in {row["id"] for row in pending}
        assert (
            list(
                session.scalars(
                    select(ChatMessage.id).where(ChatMessage.session_id == session_id)
                )
            )
            == message_ids
        )

        restored = client.post(
            f"/api/tenants/{tenant.id}/copilot/sessions/{session_id}/restore"
        )
        assert restored.status_code == 204
        assert (
            client.get(f"/api/tenants/{tenant.id}/copilot").json()["sessions"][0]["id"]
            == session_id
        )
    finally:
        app.dependency_overrides.clear()


def test_copilot_removal_permanently_deletes_only_empty_tenant_session(session):
    tenant = create_tenant(session, "Empty chat company")
    other = create_tenant(session, "Other empty chat company")
    proposal = propose_tool(session, tenant.id, "demo_seed", {})
    client = api_client(session)
    try:
        created = client.post(f"/api/tenants/{tenant.id}/copilot/sessions")
        session_id = created.json()["id"]
        projected = client.get(f"/api/tenants/{tenant.id}/copilot").json()

        assert projected["sessions"][0]["message_count"] == 0
        assert (
            client.delete(
                f"/api/tenants/{other.id}/copilot/sessions/{session_id}"
            ).status_code
            == 404
        )

        removed = client.delete(
            f"/api/tenants/{tenant.id}/copilot/sessions/{session_id}"
        )

        assert removed.status_code == 204
        assert record_by_id(session, ChatSession, session_id) is None
        assert (
            client.delete(
                f"/api/tenants/{tenant.id}/copilot/sessions/{session_id}"
            ).status_code
            == 404
        )
        assert client.get(f"/api/tenants/{tenant.id}/copilot").json()["sessions"] == []
        assert (
            client.get(
                f"/api/tenants/{tenant.id}/copilot", params={"archived": True}
            ).json()["sessions"]
            == []
        )
        assert (
            client.post(
                f"/api/tenants/{tenant.id}/copilot/sessions/{session_id}/restore"
            ).status_code
            == 404
        )
        session.refresh(proposal)
        assert proposal.status == "proposed"
    finally:
        app.dependency_overrides.clear()


def _person(session, email: str, display_name: str) -> AppUser:
    user = AppUser(
        id=uid("usr"),
        email=email,
        password_hash="x",
        display_name=display_name,
        status="active",
    )
    session.add(user)
    session.commit()
    return user


def test_a_decision_records_when_and_by_whom_it_was_settled(session):
    """An approval boundary exists to record who crossed it."""
    tenant = create_tenant(session, "Attributed company")
    approver = _person(session, "approver@example.com", "Approver One")
    approved = propose_tool(session, tenant.id, "demo_seed", {})
    rejected = propose_tool(session, tenant.id, "demo_seed", {})
    unattended = propose_tool(session, tenant.id, "demo_seed", {})

    approve_and_execute_proposal(
        session, tenant.id, approved.id, confirming_principal=Principal(approver.id)
    )
    reject_proposal(
        session, tenant.id, rejected.id, confirming_principal=Principal(approver.id)
    )
    # A decision reached without a signed-in principal, such as through the CLI.
    reject_proposal(session, tenant.id, unattended.id)

    assert approved.decided_by_user_id == approver.id
    assert approved.decided_at is not None
    assert rejected.decided_by_user_id == approver.id
    assert rejected.decided_at is not None
    # The moment is still recorded; only the person is left unnamed.
    assert unattended.decided_by_user_id is None
    assert unattended.decided_at is not None


def test_history_names_the_decision_maker_without_becoming_a_directory(session):
    tenant = create_tenant(session, "Named company")
    other = create_tenant(session, "Other company")
    approver = _person(session, "decider@example.com", "Decider One")
    stranger = _person(session, "stranger@example.com", "Stranger One")
    mine = propose_tool(session, tenant.id, "demo_seed", {})
    theirs = propose_tool(session, other.id, "demo_seed", {})
    reject_proposal(
        session, tenant.id, mine.id, confirming_principal=Principal(approver.id)
    )
    reject_proposal(
        session, other.id, theirs.id, confirming_principal=Principal(stranger.id)
    )

    client = api_client(session)
    try:
        history = client.get(
            f"/api/tenants/{tenant.id}/change-proposals", params={"status": "history"}
        ).json()["items"]
        assert [row["decided_by"] for row in history] == ["Decider One"]
        assert history[0]["decided_at"] is not None
        # A person who only decided in another company is never resolved here.
        assert "Stranger One" not in str(history)
    finally:
        app.dependency_overrides.clear()


def test_history_leaves_an_unattributed_decision_unnamed(session):
    """Decisions settled before attribution existed keep an honest blank."""
    tenant = create_tenant(session, "Legacy company")
    proposal = propose_tool(session, tenant.id, "demo_seed", {})
    reject_proposal(session, tenant.id, proposal.id)
    proposal.decided_at = None
    session.commit()

    client = api_client(session)
    try:
        history = client.get(
            f"/api/tenants/{tenant.id}/change-proposals", params={"status": "history"}
        ).json()["items"]
        assert history[0]["decided_by"] is None
        assert history[0]["decided_at"] is None
    finally:
        app.dependency_overrides.clear()


def test_decision_history_is_paged_and_searchable_in_the_database(session):
    """History only grows, so the reader must page and filter before it returns."""
    tenant = create_tenant(session, "Busy company")
    client = api_client(session)
    try:
        for index in range(7):
            proposal = propose_tool(
                session,
                tenant.id,
                "demo_seed" if index % 2 else "location_create",
                {"index": index},
            )
            client.post(
                f"/api/tenants/{tenant.id}/change-proposals/{proposal.id}/reject",
                json={"session_id": None},
            )

        first = client.get(
            f"/api/tenants/{tenant.id}/change-proposals",
            params={"status": "history", "page": 1, "size": 3},
        ).json()
        second = client.get(
            f"/api/tenants/{tenant.id}/change-proposals",
            params={"status": "history", "page": 2, "size": 3},
        ).json()
        searched = client.get(
            f"/api/tenants/{tenant.id}/change-proposals",
            params={"status": "history", "size": 50, "q": "location"},
        ).json()
        beyond = client.get(
            f"/api/tenants/{tenant.id}/change-proposals",
            params={"status": "history", "page": 99, "size": 3},
        ).json()

        assert first["page"] == {
            "number": 1,
            "size": 3,
            "total": 7,
            "pages": 3,
            "has_previous": False,
            "has_next": True,
        }
        assert len(first["items"]) == 3
        assert second["page"]["has_previous"] is True
        # A page boundary may neither repeat nor skip a decision.
        assert not {row["id"] for row in first["items"]} & {
            row["id"] for row in second["items"]
        }
        assert searched["page"]["total"] == 4
        assert {row["tool"] for row in searched["items"]} == {"location_create"}
        # An out-of-range page clamps to the last page instead of failing.
        assert beyond["page"]["number"] == 3
        assert beyond["items"]
    finally:
        app.dependency_overrides.clear()


def test_decision_history_stays_inside_its_own_tenant(session):
    tenant = create_tenant(session, "Own company")
    other = create_tenant(session, "Other company")
    mine = propose_tool(session, tenant.id, "demo_seed", {})
    theirs = propose_tool(session, other.id, "demo_seed", {})
    client = api_client(session)
    try:
        for owner, proposal in ((tenant, mine), (other, theirs)):
            client.post(
                f"/api/tenants/{owner.id}/change-proposals/{proposal.id}/reject",
                json={"session_id": None},
            )
        history = client.get(
            f"/api/tenants/{tenant.id}/change-proposals", params={"status": "history"}
        ).json()
        assert {row["id"] for row in history["items"]} == {mine.id}
        assert history["page"]["total"] == 1
    finally:
        app.dependency_overrides.clear()


def test_dashboard_treats_proposal_history_as_real_activity(session):
    tenant = create_tenant(session, "Proposal-only company")
    proposal = propose_tool(session, tenant.id, "demo_seed", {})
    client = api_client(session)
    try:
        dashboard = client.get(f"/api/tenants/{tenant.id}/dashboard").json()
        assert dashboard["capabilities"]["activity"] is True
        assert dashboard["totals"]["pending_decisions"] == 1

        rejected = client.post(
            f"/api/tenants/{tenant.id}/change-proposals/{proposal.id}/reject",
            json={"session_id": None},
        )
        assert rejected.status_code == 200
        dashboard = client.get(f"/api/tenants/{tenant.id}/dashboard").json()
        history = client.get(
            f"/api/tenants/{tenant.id}/change-proposals", params={"status": "history"}
        ).json()["items"]
        assert dashboard["capabilities"]["activity"] is True
        assert dashboard["totals"]["pending_decisions"] == 0
        assert dashboard["totals"]["decision_history"] == 1
        assert history[0]["status"] == "rejected"
    finally:
        app.dependency_overrides.clear()


def test_movement_correction_preview_execute_and_inspector_contract(session, business):
    movement = record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        3,
        to_location_id=business.location.id,
    )
    client = api_client(session)
    path = f"/api/tenants/{business.tenant.id}/movements/{movement.id}/correction"
    try:
        snapshot = client.get(path)
        assert snapshot.status_code == 200
        assert snapshot.json()["role"] == "normal"
        preview = client.post(
            f"{path}/preview", json={"reason": "Duplicate warehouse receipt"}
        )
        assert preview.status_code == 200
        assert preview.json()["compensation"]["type"] == "correction"
        corrected = client.post(
            path,
            json={
                "expected_revision": preview.json()["revision"],
                "preview_fingerprint": preview.json()["request_fingerprint"],
                "reason": "Duplicate warehouse receipt",
                "actor_context": {"surface": "web"},
            },
        )
        assert corrected.status_code == 200
        assert corrected.json()["replayed"] is False
        inspector = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/movement/{movement.id}"
        )
        assert inspector.status_code == 200
        assert inspector.json()["status"] == "Corrected"
        correction_section = next(
            section
            for section in inspector.json()["sections"]
            if section["title"] == "Correction chain"
        )
        assert any(row["label"] == "Reason" for row in correction_section["rows"])
        listed = client.get(f"/api/tenants/{business.tenant.id}/movements")
        original_row = next(row for row in listed.json() if row["id"] == movement.id)
        assert original_row["correction_role"] == "corrected"
        foreign = create_tenant(session, "Foreign API tenant")
        assert (
            client.get(
                f"/api/tenants/{foreign.id}/movements/{movement.id}/correction"
            ).status_code
            == 404
        )
    finally:
        app.dependency_overrides.clear()


def test_manual_document_line_correction_api_contract(session, business):
    document, lines = create_manual_document_with_lines(
        session,
        business.tenant.id,
        "sales_order",
        "SO-API-CORRECTION",
        business.customer.id,
        [
            {
                "item_id": business.item.id,
                "source_line_id": "1",
                "quantity": "2",
                "unit_price": "10",
                "gross_amount": "20",
            }
        ],
        "20",
    )
    client = api_client(session)
    path = f"/api/tenants/{business.tenant.id}/documents/{document.id}/line-correction"
    try:
        other = create_tenant(session, "Other correction tenant")
        foreign = client.get(
            f"/api/tenants/{other.id}/documents/{document.id}/line-correction"
        )
        assert foreign.status_code == 404
        snapshot = client.get(path)
        assert snapshot.status_code == 200
        assert snapshot.json()["correctable"] is True
        assert snapshot.json()["lines"][0]["id"] == lines[0].id

        body = {
            "expected_revision": snapshot.json()["revision"],
            "lines": [{**snapshot.json()["lines"][0], "description": "API corrected"}],
        }
        corrected = client.put(path, json=body)
        assert corrected.status_code == 200
        assert corrected.json()["changed"] is True
        assert corrected.json()["lines"][0]["description"] == "API corrected"
        inspector = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/document/{document.id}"
        )
        assert inspector.status_code == 200
        assert any(
            section["title"] == "Correction" for section in inspector.json()["sections"]
        )
        assert "document.corrected" in {
            event["type"] for event in inspector.json()["events"]
        }

        retry = client.put(
            path,
            json={
                "expected_revision": snapshot.json()["revision"],
                "lines": corrected.json()["lines"],
            },
        )
        assert retry.status_code == 200
        assert retry.json()["changed"] is False

        stale = client.put(
            path,
            json={
                "expected_revision": snapshot.json()["revision"],
                "lines": [{**corrected.json()["lines"][0], "description": "Stale"}],
            },
        )
        assert stale.status_code == 409
        assert "stale" in stale.json()["detail"].lower()

        create_commitment(
            session,
            business.tenant.id,
            "customer_delivery",
            business.company.id,
            business.customer.id,
            business.item.id,
            business.location.id,
            2,
            "2026-09-03",
            document_id=document.id,
        )
        protected_snapshot = client.get(path).json()
        protected = client.put(
            path,
            json={
                "expected_revision": protected_snapshot["revision"],
                "lines": [{**protected_snapshot["lines"][0], "quantity": "3"}],
            },
        )
        assert protected.status_code == 400
        assert "Reality correction workflow" in protected.json()["detail"]
        assert client.get(path).json()["lines"] == protected_snapshot["lines"]

        source, _, _ = store_source_record(
            session,
            business.tenant.id,
            "shopify",
            "order",
            "external-correction-api",
            {"id": "external-correction-api"},
        )
        session.commit()
        external = create_document(
            session,
            business.tenant.id,
            "sales_order",
            "SO-EXTERNAL-CORRECTION",
            business.customer.id,
            "10",
            source_record_id=source.id,
        )
        external_path = (
            f"/api/tenants/{business.tenant.id}/documents/{external.id}/line-correction"
        )
        external_snapshot = client.get(external_path)
        assert external_snapshot.status_code == 200
        assert external_snapshot.json()["correctable"] is False
        assert external_snapshot.json()["lines"] == []
        external_put = client.put(
            external_path, json={"expected_revision": "", "lines": []}
        )
        assert external_put.status_code == 400
        assert "source version" in external_put.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_document_api_transports_and_explains_selected_price_entry(session, business):
    price_list = create_price_list(
        session,
        business.tenant.id,
        "WEB-PRICE",
        "Web price",
        "sales",
        "EUR",
        is_default=True,
    )
    entry = create_price_list_entry(
        session, business.tenant.id, price_list.id, business.item.id, 1, 10, "pcs"
    )
    client = api_client(session)
    try:
        created = client.post(
            f"/api/tenants/{business.tenant.id}/documents",
            json={
                "type": "sales_order",
                "number": "SO-PRICE-API",
                "party_id": business.customer.id,
                "currency": "EUR",
                "lines": [
                    {
                        "item_id": business.item.id,
                        "quantity": "1",
                        "unit": "pcs",
                        "unit_price": "10",
                        "gross_amount": "10",
                        "price_list_entry_id": entry.id,
                    }
                ],
                "gross_amount": "10",
            },
        )
        assert created.status_code == 201
        inspected = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/document/{created.json()['id']}"
        )
        assert inspected.status_code == 200
        section = next(
            row
            for row in inspected.json()["sections"]
            if row["title"] == "Historical pricing"
        )
        value = section["rows"][0]["value"]
        assert value.startswith("agreed EUR 10")
        assert entry.id in value
        assert "current EUR 10" in value
    finally:
        app.dependency_overrides.clear()


def test_company_settings_api_exposes_commercial_and_agent_configuration(
    session, business, monkeypatch
):
    monkeypatch.setenv("MCP_URL", "https://mcp.runreality.ai/")
    client = api_client(session)
    tenant_id = business.tenant.id
    try:
        term = client.post(
            f"/api/tenants/{tenant_id}/payment-terms",
            json={"code": "NET14", "name": "Net 14", "due_days": 14},
        )
        price_list = client.post(
            f"/api/tenants/{tenant_id}/price-lists",
            json={
                "code": "D2C",
                "name": "Direct customers",
                "direction": "sales",
                "currency": "EUR",
            },
        )
        group = client.post(
            f"/api/tenants/{tenant_id}/pricing-groups",
            json={"code": "VIP", "name": "VIP customers"},
        )

        assert term.status_code == 201
        assert price_list.status_code == 201
        assert group.status_code == 201
        assert (
            client.get(f"/api/tenants/{tenant_id}/payment-terms").json()[0]["code"]
            == "NET14"
        )
        payment_term_choices = client.get(
            f"/api/tenants/{tenant_id}/suggestions/payment-terms"
        )
        assert payment_term_choices.status_code == 200
        assert payment_term_choices.json() == {
            "items": [
                {
                    "value": "NET14",
                    "label": "NET14 · Net 14",
                    "description": "14 days",
                    "status": "active",
                }
            ],
            "allow_custom": False,
        }
        assert (
            client.get(f"/api/tenants/{tenant_id}/price-lists").json()[0]["code"]
            == "D2C"
        )
        assert (
            client.get(f"/api/tenants/{tenant_id}/pricing-groups").json()[0]["code"]
            == "VIP"
        )

        updated_term = client.put(
            f"/api/tenants/{tenant_id}/payment-terms/{term.json()['id']}",
            json={"code": "NET30", "name": "Net 30", "due_days": 30},
        )
        updated_price_list = client.put(
            f"/api/tenants/{tenant_id}/price-lists/{price_list.json()['id']}",
            json={
                "code": "D2C",
                "name": "Direct sales",
                "direction": "sales",
                "currency": "EUR",
            },
        )
        updated_group = client.put(
            f"/api/tenants/{tenant_id}/pricing-groups/{group.json()['id']}",
            json={"code": "VIP", "name": "Preferred customers"},
        )

        assert updated_term.status_code == 200
        assert updated_term.json()["code"] == "NET30"
        assert updated_term.json()["due_days"] == 30
        assert updated_price_list.status_code == 200
        assert updated_price_list.json()["name"] == "Direct sales"
        assert updated_group.status_code == 200
        assert updated_group.json()["name"] == "Preferred customers"

        ai = client.get(f"/api/tenants/{tenant_id}/settings/ai")
        assert ai.status_code == 200
        copilot = ai.json()["copilot"]
        assert copilot["managed"] is True
        assert copilot["available"] is False
        assert copilot["provider_name"] == "Anthropic"
        assert copilot["provider_preset"] == "managed"
        assert copilot["has_company_api_key"] is False
        assert {row["id"] for row in copilot["presets"]} >= {
            "managed",
            "anthropic",
            "openai",
            "google",
            "mistral",
            "groq",
            "openrouter",
            "custom",
        }
        assert "provider_preset" not in ai.json()
        assert "model" not in ai.json()
        assert "has_api_key" not in ai.json()
        assert ai.json()["mcp_url"] == "https://mcp.runreality.ai/"

        own_key = client.put(
            f"/api/tenants/{tenant_id}/settings/ai",
            json={"provider_preset": "company", "api_key": "company-anthropic-key"},
        )
        assert own_key.status_code == 200
        assert own_key.json()["copilot"]["credential_mode"] == "company"
        assert own_key.json()["copilot"]["has_company_api_key"] is True
        assert "company-anthropic-key" not in own_key.text

        managed = client.put(
            f"/api/tenants/{tenant_id}/settings/ai",
            json={"provider_preset": "managed"},
        )
        assert managed.status_code == 200
        assert managed.json()["copilot"]["credential_mode"] == "managed"
        assert managed.json()["copilot"]["has_company_api_key"] is False

        token = client.post(
            f"/api/tenants/{tenant_id}/settings/mcp/tokens",
            json={"name": "External agent", "allowed_tools": ["*"]},
        )
        assert token.status_code == 201
        assert token.json()["token"].startswith("ros_mcp_")
        token_id = token.json()["id"]
        revoked = client.post(
            f"/api/tenants/{tenant_id}/settings/mcp/tokens/{token_id}/revoke"
        )
        assert revoked.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_company_management_api_covers_the_complete_lifecycle(session):
    active = create_tenant(session, "Active Company")
    client = api_client(session)
    try:
        created = client.post("/api/v1/companies", json={"name": "New Company"})
        assert created.status_code == 201
        created_id = created.json()["id"]

        companies = client.get("/api/v1/companies")
        assert companies.status_code == 200
        rows = {row["id"]: row for row in companies.json()}
        assert rows[active.id]["state"] == "empty"
        assert rows[created_id]["archived_at"] is None

        archived = client.post(f"/api/v1/companies/{created_id}/archive")
        assert archived.status_code == 200
        assert archived.json()["archived_at"] is not None
        assert all(
            tenant["id"] != created_id
            for tenant in client.get("/api/v1/bootstrap").json()["tenants"]
        )

        restored = client.post(f"/api/v1/companies/{created_id}/restore")
        assert restored.status_code == 200
        assert restored.json()["archived_at"] is None

        client.post(f"/api/v1/companies/{created_id}/archive")
        rejected = client.post(
            f"/api/v1/companies/{created_id}/delete",
            json={"confirmation_name": "Wrong", "confirmation_word": "DELETE"},
        )
        assert rejected.status_code == 400
        deleted = client.post(
            f"/api/v1/companies/{created_id}/delete",
            json={"confirmation_name": "New Company", "confirmation_word": "DELETE"},
        )
        assert deleted.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_independent_frontend_bootstrap_and_dashboard(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "4",
        "2026-09-01T10:00:00+00:00",
    )
    client = api_client(session)
    try:
        bootstrap = client.get("/api/v1/bootstrap")
        dashboard = client.get(f"/api/tenants/{business.tenant.id}/dashboard")
        inventory = client.get(f"/api/tenants/{business.tenant.id}/inventory-control")
        commitments = client.get(
            f"/api/tenants/{business.tenant.id}/commitment-control"
        )
        documents = client.get(f"/api/tenants/{business.tenant.id}/evidence-documents")
        timeline = client.get(f"/api/tenants/{business.tenant.id}/timeline")
        activity_signal = client.get(
            f"/api/tenants/{business.tenant.id}/activity-signal?after_sequence=0"
        )

        assert bootstrap.status_code == 200
        assert bootstrap.json() == {
            "tenants": [{"id": business.tenant.id, "name": "Acme Bikes GmbH"}],
            "default_tenant_id": business.tenant.id,
        }
        assert dashboard.status_code == 200
        assert dashboard.json()["tenant"]["id"] == business.tenant.id
        assert dashboard.json()["totals"]["stocked_items"] == 1
        assert "facts" in dashboard.json()["totals"]
        assert "capabilities" in dashboard.json()
        assert inventory.json()["items"][0]["sku"] == "BIKE-LIGHT"
        assert commitments.status_code == 200
        assert commitments.json()["items"][0]["id"] == commitment.id
        assert commitments.json()["items"][0]["risk"] == "at_risk"
        assert documents.status_code == 200
        assert documents.json()["items"] == []
        assert timeline.status_code == 200
        assert activity_signal.status_code == 200
        assert activity_signal.json()["latest_sequence"] >= 1
        assert activity_signal.json()["new_events"] >= 1
        assert timeline.json()["summary"]["events"] >= 1
        assert len(timeline.json()["chart"]) == 24
        assert timeline.json()["activities"][0]["business_title"]
        assert "business_detail" in timeline.json()["activities"][0]
        assert timeline.json()["activities"][0]["events"][0]["business_title"]
        assert "business_detail" in timeline.json()["activities"][0]["events"][0]
        assert all(
            event["subject_id"] != "ten_cross_tenant"
            for event in timeline.json()["events"]
        )
    finally:
        app.dependency_overrides.clear()


def test_fact_register_and_inspector_preserve_source_trace(session, business):
    source, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "ORDER-42",
        {"id": "ORDER-42", "priority": "express"},
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        "2026-09-15T10:00:00Z",
    )
    fact = observe_fact(
        session,
        business.tenant.id,
        source_record_id=source.id,
        subject_type="commitment",
        subject_id=commitment.id,
        predicate="order.shipping_priority",
        value="express",
        observed_at="2026-09-02T14:06:00Z",
        idempotency_key="api-inspector-order-42-priority",
    )
    other = create_tenant(session, "Other company")
    client = api_client(session)
    try:
        register = client.get(f"/api/tenants/{business.tenant.id}/facts")
        inspector = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/fact/{fact.id}"
        )
        cross_tenant = client.get(f"/api/tenants/{other.id}/inspector/fact/{fact.id}")

        assert register.status_code == 200
        assert register.json()["items"][0]["source"] == {
            "system": "shopify",
            "type": "order",
            "external_id": "ORDER-42",
        }
        assert inspector.status_code == 200
        payload = inspector.json()
        assert (
            payload["meaning"]
            == "This is a recorded observation, not a current-state guarantee."
        )
        assert payload["business_reference"] == {
            "label": "Shopify order",
            "value": "ORDER-42",
        }
        assert payload["guidance"] is None
        assert payload["trail"][0]["label"] == "Source"
        assert payload["technical_rows"] == [
            {
                "label": "Fact ID",
                "value": fact.id,
                "tone": "",
                "link": None,
            },
            {
                "label": "Subject ID",
                "value": commitment.id,
                "tone": "",
                "link": None,
            },
            {
                "label": "Exact predicate",
                "value": "order.shipping_priority",
                "tone": "",
                "link": None,
            },
            {
                "label": "Source record ID",
                "value": source.id,
                "tone": "",
                "link": None,
            },
        ]
        assert payload["source_payload"] == source.payload
        assert cross_tenant.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_frontend_evidence_endpoint_serializes_document_dates(session):
    tenant = create_tenant(session, "Evidence API")
    ensure_demo(session, tenant)
    client = api_client(session)
    try:
        response = client.get(f"/api/tenants/{tenant.id}/evidence-documents")
        assert response.status_code == 200
        assert date.fromisoformat(response.json()["items"][0]["date"])
        assert response.json()["items"][0]["source"]["system"] == "shopify"
    finally:
        app.dependency_overrides.clear()


def test_manual_document_api_records_header_and_lines_as_evidence(session, business):
    client = api_client(session)
    try:
        response = client.post(
            f"/api/tenants/{business.tenant.id}/documents",
            json={
                "type": "sales_order",
                "number": "MANUAL-1001",
                "party_id": business.customer.id,
                "currency": "EUR",
                "document_date": "2026-08-30",
                "customer_reference": "PO-44",
                "lines": [
                    {
                        "item_id": business.item.id,
                        "quantity": "2",
                        "unit": "pcs",
                        "unit_price": "12.50",
                        "gross_amount": "25.00",
                    }
                ],
                "gross_amount": "25.00",
            },
        )

        assert response.status_code == 201
        assert response.json()["line_count"] == 1
        document = session.scalar(
            select(Document).where(Document.id == response.json()["id"])
        )
        line = session.scalar(
            select(DocumentLine).where(DocumentLine.document_id == document.id)
        )
        assert document.number == "MANUAL-1001"
        assert str(document.gross_amount) == "25.0000"
        assert document.source_record_id is None
        assert line.item_id == business.item.id
        assert line.sku == business.item.sku
        assert line.description == business.item.name
        assert str(line.quantity) == "2.0000"
    finally:
        app.dependency_overrides.clear()


def test_inspector_explains_commitment_and_enforces_tenant_scope(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "5",
        # The inspector reads the queue at the current instant, so the promise
        # has to stay ahead of its due date for the at-risk class to apply.
        (now() + timedelta(days=30)).isoformat(),
    )
    other = create_tenant(session, "Inspector Other")
    exception_id = f"exc__outgoing_commitment_at_risk__{commitment.id}"
    client = api_client(session)
    try:
        response = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/exception/{exception_id}"
        )
        cross_tenant = client.get(
            f"/api/tenants/{other.id}/inspector/exception/{exception_id}"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["kind"] == "exception"
        assert payload["status"] == "Needs review"
        assert payload["meaning"] == (
            "Customer commitment at risk. 5.0000 remains unreserved."
        )
        assert payload["business_reference"] == {
            "label": "Affected commitment",
            "value": f"{business.customer.name} · {business.item.name}",
        }
        assert payload["guidance"] == (
            "Reserving the remaining quantity, shipping it, or cancelling the commitment."
        )
        assert [row["label"] for row in payload["technical_rows"]] == [
            "Exception ID",
            "Exception class",
            "Record ID",
        ]
        assert payload["metrics"][-1] == {
            "label": "Uncovered",
            "value": "5.0000",
            "display_parts": [{"type": "number", "value": "5.0000"}],
            "tone": "danger",
            "link": None,
        }
        assert [step["label"] for step in payload["trail"]] == [
            "Source",
            "Evidence",
            "Reality",
        ]
        assert cross_tenant.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_same_titled_exceptions_show_their_distinct_source_orders(session, business):
    commitments = []
    for order_number in ("ORDER-101", "ORDER-202"):
        source, _, _ = store_source_record(
            session,
            business.tenant.id,
            "shopify",
            "order",
            order_number,
            {"id": order_number},
        )
        document = create_document(
            session,
            business.tenant.id,
            "sales_order",
            order_number,
            business.customer.id,
            "100",
            source_record_id=source.id,
        )
        commitments.append(
            create_commitment(
                session,
                business.tenant.id,
                "customer_delivery",
                business.company.id,
                business.customer.id,
                business.item.id,
                business.location.id,
                "1",
                (now() + timedelta(days=30)).isoformat(),
                document_id=document.id,
            )
        )
    client = api_client(session)
    try:
        payloads = [
            client.get(
                f"/api/tenants/{business.tenant.id}/inspector/exception/"
                f"exc__outgoing_commitment_at_risk__{commitment.id}"
            ).json()
            for commitment in commitments
        ]

        assert [payload["title"] for payload in payloads] == [
            "Customer commitment at risk",
            "Customer commitment at risk",
        ]
        assert [payload["business_reference"] for payload in payloads] == [
            {"label": "Shopify order", "value": "ORDER-101"},
            {"label": "Shopify order", "value": "ORDER-202"},
        ]
        assert [payload["trail"][0]["value"] for payload in payloads] == [
            "shopify · ORDER-101",
            "shopify · ORDER-202",
        ]
        from reality.services.exceptions import operational_exceptions

        traces = {
            row.record_id: row.trace
            for row in operational_exceptions(session, business.tenant.id)
        }
        assert [
            (
                trace["document_number"],
                trace["source_system"],
                trace["source_external_id"],
                trace["customer_reference"],
            )
            for trace in (traces[commitment.id] for commitment in commitments)
        ] == [
            ("ORDER-101", "shopify", "ORDER-101", None),
            ("ORDER-202", "shopify", "ORDER-202", None),
        ]
    finally:
        app.dependency_overrides.clear()


def test_inspector_shows_the_shortfall_on_an_overdue_promise(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "5",
        (now() - timedelta(days=2)).isoformat(),
    )
    exception_id = f"exc__overdue_outgoing_customer_commitment__{commitment.id}"
    client = api_client(session)
    try:
        response = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/exception/{exception_id}"
        )

        assert response.status_code == 200
        payload = response.json()
        # The reservation shortfall rides on the overdue entry as a cause, so
        # the Inspector must keep showing it without knowing the class.
        assert payload["metrics"][-1] == {
            "label": "Uncovered",
            "value": "5.0000",
            "display_parts": [{"type": "number", "value": "5.0000"}],
            "tone": "danger",
            "link": None,
        }
    finally:
        app.dependency_overrides.clear()


def test_document_inspector_connects_source_evidence_and_reality(session):
    tenant = create_tenant(session, "Inspector Demo")
    ensure_demo(session, tenant)
    document = session.scalar(select(Document).where(Document.tenant_id == tenant.id))
    assert document is not None
    client = api_client(session)
    try:
        response = client.get(
            f"/api/tenants/{tenant.id}/inspector/document/{document.id}"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["kind"] == "document"
        expected_lines = list(
            session.scalars(
                select(DocumentLine).where(
                    DocumentLine.tenant_id == tenant.id,
                    DocumentLine.document_id == document.id,
                )
            )
        )
        assert {row["id"] for row in payload["evidence_lines"]} == {
            row.id for row in expected_lines
        }
        for row in payload["evidence_lines"]:
            stored = next(line for line in expected_lines if line.id == row["id"])
            assert Decimal(row["gross_amount"]) == stored.gross_amount
        assert payload["trail"][0]["active"] is True
        assert payload["trail"][1]["active"] is True
        assert payload["trail"][2]["active"] is True
        assert payload["source_payload"] is not None
        assert any(
            section["title"] == "Operational Reality" and section["rows"]
            for section in payload["sections"]
        )
    finally:
        app.dependency_overrides.clear()


def test_react_registers_and_reference_inspectors_are_tenant_scoped(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        4,
        "2026-09-03",
    )
    other = create_tenant(session, "Other React Registers")
    client = api_client(session)
    try:
        reserved = client.post(
            f"/api/tenants/{business.tenant.id}/reservations",
            json={"commitment_id": commitment.id, "quantity": "3"},
        )
        reservations = client.get(f"/api/tenants/{business.tenant.id}/reservations")
        movements = client.get(f"/api/tenants/{business.tenant.id}/movements")
        other_reservations = client.get(f"/api/tenants/{other.id}/reservations")
        party = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/party/{business.customer.id}"
        )
        item = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/item/{business.item.id}"
        )
        location = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/location/{business.location.id}"
        )

        assert reserved.status_code == 201
        assert reservations.status_code == 200
        assert reservations.json()[0]["commitment_id"] == commitment.id
        assert movements.status_code == 200
        assert movements.json()[0]["type"] == "opening_stock"
        assert other_reservations.json() == []
        assert party.status_code == 200
        assert party.json()["title"] == "Müller GmbH"
        assert item.status_code == 200
        assert item.json()["metrics"][0]["value"] == "10.0000"
        assert location.status_code == 200
        assert location.json()["metrics"][0]["value"] == 1
    finally:
        app.dependency_overrides.clear()


def test_frontend_finance_endpoints_are_tenant_scoped_and_currency_safe(
    session, business
):
    from reality.services.projections import OPEN_FINANCIAL_ITEMS, rebuild_projections

    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "INV-API-1",
        business.customer.id,
        "1470.00",
        document_date="2026-08-30",
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    post_customer_payment(session, business.tenant.id, invoice.id, "500.00")
    rebuild_projections(session, business.tenant.id, (OPEN_FINANCIAL_ITEMS,))
    other = create_tenant(session, "Other Finance API")
    client = api_client(session)
    try:
        open_items = client.get(f"/api/tenants/{business.tenant.id}/finance/open-items")
        payments = client.get(f"/api/tenants/{business.tenant.id}/finance/payments")
        other_open_items = client.get(f"/api/tenants/{other.id}/finance/open-items")

        assert open_items.status_code == 200
        assert open_items.json()["items"]
        assert open_items.json()["totals"][0]["currency"] == "EUR"
        assert open_items.json()["totals"][0]["open"] == "970.0000"
        outstanding = client.get(
            f"/api/tenants/{business.tenant.id}/finance/open-items"
            "?flow=receivable&item_status=outstanding&size=1"
        ).json()
        assert outstanding["page"]["total"] == 1
        assert outstanding["items"][0]["status"] == "partial"
        assert outstanding["totals"][0]["open"] == "970.0000"
        post_customer_payment(session, business.tenant.id, invoice.id, "970.00")
        rebuild_projections(session, business.tenant.id, (OPEN_FINANCIAL_ITEMS,))
        settled = client.get(
            f"/api/tenants/{business.tenant.id}/finance/open-items"
            "?item_status=outstanding"
        ).json()
        assert settled["items"] == []
        assert settled["totals"] == []
        assert payments.status_code == 200
        assert payments.json()["totals"][0]["amount"] == "500.0000"
        assert other_open_items.status_code == 200
        assert other_open_items.json()["items"] == []
        assert other_open_items.json()["totals"] == []
    finally:
        app.dependency_overrides.clear()


def test_outstanding_items_filter_before_paging_and_totals(session, business):
    from reality.services.core import post_supplier_invoice
    from reality.services.projections import OPEN_FINANCIAL_ITEMS, rebuild_projections

    tenant = business.tenant.id
    for index in range(3):
        invoice = create_document(
            session,
            tenant,
            "sales_invoice",
            f"OUT-{index}",
            business.customer.id,
            "100.00",
        )
        post_sales_invoice(session, tenant, invoice.id)
        if index == 1:
            post_customer_payment(session, tenant, invoice.id, "40.00")
        if index == 2:
            post_customer_payment(session, tenant, invoice.id, "100.00")
    supplier = create_document(
        session,
        tenant,
        "supplier_invoice",
        "SUP-OUT",
        business.customer.id,
        "80.00",
    )
    post_supplier_invoice(session, tenant, supplier.id)
    rebuild_projections(session, tenant, (OPEN_FINANCIAL_ITEMS,))
    client = api_client(session)
    try:
        path = f"/api/tenants/{tenant}/finance/open-items"
        first = client.get(
            path + "?flow=receivable&item_status=outstanding&size=1"
        ).json()
        second = client.get(
            path + "?flow=receivable&item_status=outstanding&size=1&page=2"
        ).json()
        assert first["page"]["total"] == 2
        assert first["page"]["has_next"]
        assert first["items"][0]["document_id"] != second["items"][0]["document_id"]
        assert first["totals"][0]["open"] == "160.0000"
        assert second["totals"] == first["totals"]
        payable = client.get(path + "?flow=payable&item_status=outstanding").json()
        assert payable["page"]["total"] == 1
        assert payable["items"][0]["document_id"] == supplier.id
        assert payable["totals"][0]["open"] == "80.0000"
        assert client.get(path + "?flow=receivable").json()["page"]["total"] == 3
    finally:
        app.dependency_overrides.clear()


def test_frontend_integrations_registry_and_activation(session):
    tenant = create_tenant(session, "Integration API")
    ensure_demo(session, tenant)
    system = create_source_system(session, tenant.id, "shopify", "Shopify")
    create_source_capability(session, tenant.id, system.id, "order", "sales_order")
    client = api_client(session)
    try:
        registry = client.get(f"/api/tenants/{tenant.id}/integrations")

        assert registry.status_code == 200
        assert registry.json()["systems"][0]["code"] == "shopify"
        assert registry.json()["systems"][0]["record_count"] == 1
        capability = registry.json()["capabilities"][0]
        assert capability["interpreter_available"] is True

        changed = client.patch(
            f"/api/tenants/{tenant.id}/source-capabilities/{capability['id']}/active",
            json={"is_active": False},
        )
        refreshed = client.get(f"/api/tenants/{tenant.id}/integrations")
        assert changed.status_code == 200
        assert refreshed.json()["capabilities"][0]["is_active"] is False
    finally:
        app.dependency_overrides.clear()


def test_frontend_explorer_is_bounded_searchable_and_tenant_scoped(session, business):
    other = create_tenant(session, "Explorer Other")
    create_item(session, other.id, "SECRET-SKU", "Invisible item")
    client = api_client(session)
    try:
        result = client.get(
            f"/api/tenants/{business.tenant.id}/explorer",
            params={"q": "BIKE-LIGHT"},
        )
        cross_tenant = client.get(
            f"/api/tenants/{business.tenant.id}/explorer",
            params={"q": "SECRET-SKU"},
        )

        assert result.status_code == 200
        assert result.json()["limit_per_collection"] == 10
        collections = [
            collection
            for section in result.json()["sections"]
            for collection in section["collections"]
        ]
        items = next(row for row in collections if row["name"] == "item")
        assert items["records"][0]["title"] == "Bike Light"
        assert all(len(collection["records"]) <= 10 for collection in collections)
        assert all(
            not collection["records"]
            for section in cross_tenant.json()["sections"]
            for collection in section["collections"]
        )
    finally:
        app.dependency_overrides.clear()


def test_frontend_copilot_requires_explicit_proposal_approval(session, business):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        3,
        to_location_id=business.location.id,
    )
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        3,
        "2026-09-03",
    )
    other = create_tenant(session, "Other Copilot")
    client = api_client(session)
    try:
        created = client.post(f"/api/tenants/{business.tenant.id}/copilot/sessions")
        session_id = created.json()["id"]
        sent = client.post(
            f"/api/tenants/{business.tenant.id}/copilot/sessions/{session_id}/messages",
            json={"message": f"reserve {commitment.id}"},
        )
        workbench = client.get(
            f"/api/tenants/{business.tenant.id}/copilot",
            params={"session_id": session_id},
        )

        assert created.status_code == 201
        assert sent.status_code == 200
        assert active_reserved(session, business.tenant.id, business.item.id) == 0
        proposal = workbench.json()["proposals"][0]
        assert proposal["tool"] == "reserve"
        assert (
            client.get(
                f"/api/tenants/{other.id}/copilot", params={"session_id": session_id}
            ).status_code
            == 404
        )

        approved = client.post(
            f"/api/tenants/{business.tenant.id}/change-proposals/{proposal['id']}/approve",
            json={
                "session_id": session_id,
                "review_token": proposal["input"]["_delivery_review"]["token"],
                "confirmed": True,
            },
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "executed"
        assert active_reserved(session, business.tenant.id, business.item.id) == 3
        refreshed = client.get(
            f"/api/tenants/{business.tenant.id}/copilot",
            params={"session_id": session_id},
        )
        assert refreshed.json()["proposals"] == []
        # Delivery receipts are recovered by proposal identity; approval adds no duplicate chat notice.
        assert len(refreshed.json()["messages"]) == len(workbench.json()["messages"])
    finally:
        app.dependency_overrides.clear()


def test_copilot_http_uses_authenticated_user_presentation(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    tenant = create_tenant(session, "Localized Chat Company")
    user = AppUser(
        id=uid("usr"),
        email="localized-chat@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
        language="de",
        locale="de-DE",
        timezone="Europe/Berlin",
    )
    token = "localized-chat-session"
    session.add(user)
    session.flush()
    session.add_all(
        [
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=user.id,
                role="owner",
                status="active",
            ),
            UserSession(
                id=uid("ses"),
                user_id=user.id,
                token_hash=auth_module.digest(token),
                expires_at=now() + timedelta(days=1),
            ),
        ]
    )
    session.commit()
    captured = {}

    def send(*args, **kwargs):
        captured.update(kwargs)
        return (
            ChatMessage(
                id="msg_user",
                tenant_id=tenant.id,
                session_id=args[2],
                role="user",
                content=args[3],
            ),
            ChatMessage(
                id="msg_assistant",
                tenant_id=tenant.id,
                session_id=args[2],
                role="assistant",
                content="Antwort",
            ),
        )

    monkeypatch.setattr(api_module, "send_chat_message", send)
    client = api_client(session)
    client.cookies.set(auth_module.COOKIE_NAME, token)
    try:
        chat = client.post(f"/api/tenants/{tenant.id}/copilot/sessions")
        result = client.post(
            f"/api/tenants/{tenant.id}/copilot/sessions/{chat.json()['id']}/messages",
            json={"message": "Welche Guthaben gibt es?"},
        )
        assert result.status_code == 200, result.text
        assert captured["language"] == "de"
        assert captured["locale"] == "de-DE"
        assert captured["timezone"] == "Europe/Berlin"
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_membership_proposal_http_confirmation_propagates_owner_actor(
    session, monkeypatch
):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setattr(api_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    tenant = create_tenant(session, "Confirmed Membership Company")
    foreign = create_tenant(session, "Foreign Membership Company")
    owner = AppUser(
        id=uid("usr"),
        email="confirmed-owner@example.com",
        password_hash="unused",
        status="active",
        email_verified_at=now(),
    )
    clear_session_token = "confirmed-owner-session"
    session.add(owner)
    session.flush()
    session.add_all(
        [
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=owner.id,
                role="owner",
                status="active",
            ),
            UserSession(
                id=uid("ses"),
                user_id=owner.id,
                token_hash=auth_module.digest(clear_session_token),
                expires_at=now() + timedelta(days=1),
            ),
        ]
    )
    session.commit()
    proposal = propose_tool(
        session,
        tenant.id,
        "member_invite",
        {"email": "confirmed-member@example.com"},
    )
    assert session.query(CompanyInvitation).filter_by(tenant_id=tenant.id).count() == 0
    assert session.query(InvitationDelivery).filter_by(tenant_id=tenant.id).count() == 0

    browser = TestClient(web_module.app)
    try:
        unauthenticated = browser.post(
            f"/api/tenants/{tenant.id}/change-proposals/{proposal.id}/approve",
            json={},
        )
        assert unauthenticated.status_code == 401
        assert (
            session.query(CompanyInvitation).filter_by(tenant_id=tenant.id).count() == 0
        )

        browser.cookies.set(auth_module.COOKIE_NAME, clear_session_token)
        foreign_response = browser.post(
            f"/api/tenants/{foreign.id}/change-proposals/{proposal.id}/approve",
            json={},
        )
        assert foreign_response.status_code == 404
        assert (
            session.query(CompanyInvitation).filter_by(tenant_id=tenant.id).count() == 0
        )

        approved = browser.post(
            f"/api/tenants/{tenant.id}/change-proposals/{proposal.id}/approve",
            json={},
        )
        assert approved.status_code == 200
        invitation = (
            session.query(CompanyInvitation)
            .filter_by(
                tenant_id=tenant.id, normalized_email="confirmed-member@example.com"
            )
            .one()
        )
        audit = (
            session.query(SecurityAuditEvent)
            .filter_by(
                tenant_id=tenant.id,
                subject_type="company_invitation",
                subject_id=invitation.id,
                event_type="invitation.created",
            )
            .one()
        )
        assert audit.actor_user_id == owner.id
    finally:
        browser.close()


def test_api_ingests_arbitrary_source_as_unmapped(session, business):
    client = api_client(session)
    try:
        response = client.post(
            f"/api/tenants/{business.tenant.id}/sources",
            json={
                "source_system": "warehouse-x",
                "source_type": "cycle_count",
                "external_id": "COUNT-1",
                "payload": {"counted": [{"sku": business.item.sku, "quantity": 4}]},
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["source"]["external_id"] == "COUNT-1"
        assert body["import_job"]["status"] == "unmapped"
    finally:
        app.dependency_overrides.clear()


def test_api_source_reads_expose_the_direct_predecessor(session, business):
    first, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "versioned-api-source",
        {"id": 1, "state": "first"},
    )
    second, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "versioned-api-source",
        {"id": 1, "state": "changed"},
    )
    client = api_client(session)
    try:
        response = client.get(f"/api/tenants/{business.tenant.id}/sources")
        assert response.status_code == 200
        rows = {row["id"]: row for row in response.json()}
        assert rows[first.id]["supersedes_source_record_id"] is None
        assert rows[second.id]["supersedes_source_record_id"] == first.id
    finally:
        app.dependency_overrides.clear()


def test_suggestions_are_tenant_scoped_and_source_dependent(session, business):
    other = create_tenant(session, "Suggestion Other")
    shop = create_source_system(session, business.tenant.id, "shop_de", "Shop DE")
    create_source_capability(
        session, business.tenant.id, shop.id, "order", "sales_order"
    )
    create_source_system(session, other.id, "private_shop", "Private Shop")
    client = api_client(session)
    path = f"/api/tenants/{business.tenant.id}/suggestions"
    try:
        parties_response = client.get(f"{path}/parties", params={"q": "müll"})
        source_types = client.get(
            f"{path}/source-types", params={"source_system_id": shop.id}
        )
        systems = client.get(f"{path}/source-system-codes")

        assert parties_response.status_code == 200
        assert parties_response.json()["items"][0]["value"] == business.customer.id
        assert source_types.json() == {
            "items": [
                {
                    "value": "order",
                    "label": "order",
                    "description": "Known operational vocabulary",
                    "status": "active",
                }
            ],
            "allow_custom": True,
        }
        assert {x["value"] for x in systems.json()["items"]} == {"shop_de"}
    finally:
        app.dependency_overrides.clear()


def test_json_api_master_data_lifecycle(session, business):
    client = api_client(session)
    tenant_path = f"/api/tenants/{business.tenant.id}"
    cases = [
        (
            "parties",
            {
                "name": "API Customer",
                "type": "customer",
                "source_system": "crm",
                "external_id": "CRM-42",
                "source_payload": {"id": "CRM-42", "custom": "preserved"},
            },
            {
                "name": "Edited API Customer",
                "type": "supplier",
                "source_system": "crm",
                "external_id": "CRM-42",
            },
        ),
        (
            "items",
            {"sku": "API-1", "name": "API Item", "unit": "pcs"},
            {"sku": "API-2", "name": "Edited API Item", "unit": "box"},
        ),
        (
            "locations",
            {"name": "API Warehouse", "type": "warehouse"},
            {"name": "Edited API Warehouse", "type": "returns"},
        ),
    ]
    try:
        for collection, create_body, update_body in cases:
            created = client.post(f"{tenant_path}/{collection}", json=create_body)
            assert created.status_code == 201
            record_id = created.json()["id"]
            assert created.json()["tenant_id"] == business.tenant.id
            assert created.json()["is_active"] is True
            if collection == "parties":
                assert created.json()["source_system"] == "crm"
                assert created.json()["external_id"] == "CRM-42"
                assert created.json()["source_record_id"].startswith("src_")

            listed = client.get(f"{tenant_path}/{collection}")
            assert listed.status_code == 200
            assert record_id in {row["id"] for row in listed.json()}

            updated = client.put(
                f"{tenant_path}/{collection}/{record_id}", json=update_body
            )
            assert updated.status_code == 200
            assert updated.json()["name"] == update_body["name"]

            deactivated = client.patch(
                f"{tenant_path}/{collection}/{record_id}/active",
                json={"is_active": False},
            )
            assert deactivated.status_code == 200
            assert deactivated.json()["is_active"] is False

            fetched = client.get(f"{tenant_path}/{collection}/{record_id}")
            assert fetched.status_code == 200
            assert fetched.json()["name"] == update_body["name"]
            assert fetched.json()["is_active"] is False
    finally:
        app.dependency_overrides.clear()


def test_location_update_api_preserves_shared_source_versioning(session, business):
    client = api_client(session)
    path = f"/api/tenants/{business.tenant.id}/locations/{business.location.id}"
    try:
        response = client.put(
            path,
            json={
                "name": "Sourced Warehouse",
                "type": "warehouse",
                "source_system": "wms",
                "external_id": "WH-42",
                "source_payload": {"id": "WH-42", "zone": "south"},
            },
        )
        assert response.status_code == 200
        assert response.json()["source_system"] == "wms"
        assert response.json()["external_id"] == "WH-42"
        assert response.json()["source_record_id"].startswith("src_")
    finally:
        app.dependency_overrides.clear()


def test_json_api_rejects_invalid_and_cross_tenant_mutations(session, business):
    other = create_tenant(session, "API Other Tenant")
    client = api_client(session)
    try:
        invalid = client.post(
            f"/api/tenants/{business.tenant.id}/parties",
            json={"name": "", "type": "customer"},
        )
        cross_tenant = client.put(
            f"/api/tenants/{other.id}/items/{business.item.id}",
            json={"sku": "WRONG", "name": "Wrong", "unit": "pcs"},
        )

        assert invalid.status_code == 400
        assert cross_tenant.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_json_api_holds_and_releases_commitment(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-05",
    )
    client = api_client(session)
    path = f"/api/tenants/{business.tenant.id}/commitments/{commitment.id}/holds"
    try:
        held = client.post(path, json={"reason_code": "compliance", "note": "Review"})
        released = client.post(f"{path}/release")

        assert held.status_code == 201
        assert held.json()["reason_code"] == "compliance"
        assert released.status_code == 200
        assert released.json()[0]["released_at"] is not None
    finally:
        app.dependency_overrides.clear()


def test_json_api_previews_and_executes_ledger_reversal(session, business):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "API-REV",
        business.customer.id,
        25,
    )
    entries = post_sales_invoice(session, business.tenant.id, invoice.id)
    path = (
        f"/api/tenants/{business.tenant.id}/ledger/posting-groups/"
        f"{entries[0].posting_group_id}/reversal"
    )
    client = api_client(session)
    try:
        preview = client.post(f"{path}/preview", json={"reason": "Incorrect invoice"})
        assert preview.status_code == 200
        assert len(preview.json()["inverse_entries"]) == 2
        executed = client.post(
            path,
            json={
                "reason": "Incorrect invoice",
                "expected_revision": preview.json()["revision"],
                "preview_fingerprint": preview.json()["request_fingerprint"],
            },
        )
        assert executed.status_code == 200
        assert executed.json()["reversing_posting_group_id"].startswith("pst_")
        snapshot = client.get(path)
        assert snapshot.json()["role"] == "reversed_original"
    finally:
        app.dependency_overrides.clear()


def test_inspector_explains_a_line_class_without_knowing_it(session, business):
    """The eighth record type reaches the Inspector through the shared contract.

    Nothing in the adapter is taught about `document_line`: what proves the
    contract holds is that an entry carried by one explains without it.
    """
    from tests.operational_exceptions.test_derivation import order, ship, stock

    stock(session, business)
    _, line, commitment = order(session, business, number="SO-INSPECTOR")
    ship(session, business, commitment, 6)
    exception_id = f"exc__shipped_not_billed__{line.id}"
    client = api_client(session)
    try:
        response = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/exception/{exception_id}"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["title"] == "Shipped and not billed"
        assert payload["guidance"].startswith("Billing the outstanding quantity")
        assert payload["metrics"][0]["label"] == "Class"
        assert payload["metrics"][0]["value"] == "shipped_not_billed"
        assert payload["metrics"][1]["value"] == line.id
        assert payload["trail"][-1] == {
            "label": "Reality",
            "value": line.id,
            "active": True,
        }

        other = create_tenant(session, "Other line inspector tenant")
        foreign = client.get(
            f"/api/tenants/{other.id}/inspector/exception/{exception_id}"
        )
        assert foreign.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_inspector_explains_a_party_class_without_knowing_it(session, business):
    """The ninth record type reaches the Inspector through the shared contract.

    A Party is a relationship rather than a transaction, and nothing in the
    adapter is taught about it: what proves the contract holds is that an entry
    carried by one explains without it.
    """
    from tests.operational_exceptions.test_derivation import customer, invoice

    party = customer(session, business, limit="100", name="Inspected GmbH")
    invoice(session, business, party, "RE-INSPECTOR", "450.00")
    exception_id = f"exc__credit_limit_exceeded__{party.id}"
    client = api_client(session)
    try:
        response = client.get(
            f"/api/tenants/{business.tenant.id}/inspector/exception/{exception_id}"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["title"] == "Credit limit exceeded"
        assert payload["guidance"].startswith("Settling enough")
        assert payload["metrics"][0]["value"] == "credit_limit_exceeded"
        assert payload["metrics"][1]["value"] == party.id
        assert payload["trail"][-1] == {
            "label": "Reality",
            "value": party.id,
            "active": True,
        }

        other = create_tenant(session, "Other party inspector tenant")
        foreign = client.get(
            f"/api/tenants/{other.id}/inspector/exception/{exception_id}"
        )
        assert foreign.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_payment_term_api_records_an_early_payment_discount(session, business):
    client = api_client(session)
    tenant_id = business.tenant.id
    try:
        created = client.post(
            f"/api/tenants/{tenant_id}/payment-terms",
            json={
                "code": "SK2_10",
                "name": "2% 10 days, net 30",
                "due_days": 30,
                "discount_percent": "2",
                "discount_days": 10,
            },
        )

        assert created.status_code == 201
        # Compared as a number rather than as text: what matters is the rate the
        # company stated, not how many trailing zeros a round trip gives it.
        assert Decimal(created.json()["discount_percent"]) == Decimal(2)
        assert created.json()["discount_days"] == 10

        choices = client.get(f"/api/tenants/{tenant_id}/suggestions/payment-terms")
        assert choices.json()["items"][0]["description"] == "30 days, 2% within 10"

        # Half a discount condition is refused at the boundary as it is in the
        # service, rather than being half-stored.
        half = client.post(
            f"/api/tenants/{tenant_id}/payment-terms",
            json={
                "code": "HALF",
                "name": "Rate only",
                "due_days": 30,
                "discount_percent": "2",
            },
        )
        assert half.status_code == 400

        # The positive control: a term that states neither figure still works
        # exactly as it did, through the same endpoint.
        plain = client.post(
            f"/api/tenants/{tenant_id}/payment-terms",
            json={"code": "NET7", "name": "Net 7", "due_days": 7},
        )
        assert plain.status_code == 201
        assert plain.json()["discount_percent"] is None

        updated = client.put(
            f"/api/tenants/{tenant_id}/payment-terms/{plain.json()['id']}",
            json={
                "code": "NET7",
                "name": "Net 7",
                "due_days": 7,
                "discount_percent": "1.5",
                "discount_days": 3,
            },
        )
        assert updated.status_code == 200
        assert Decimal(updated.json()["discount_percent"]) == Decimal("1.5")
    finally:
        app.dependency_overrides.clear()


# --- An invoice somebody can actually book (spec 091) ----------------------


def _record_invoice(
    client, tenant_id, party_id, *, number, amount, kind, day, item_id=None, term=""
):
    return client.post(
        f"/api/tenants/{tenant_id}/documents",
        json={
            "type": kind,
            "number": number,
            "party_id": party_id,
            "gross_amount": amount,
            "document_date": day,
            "payment_term_code": term,
            "lines": [
                {
                    "item_id": item_id,
                    "quantity": "1",
                    "unit": "pcs",
                    "unit_price": amount,
                    "gross_amount": amount,
                }
            ],
        },
    )


def test_a_sales_invoice_can_be_booked_over_the_api(session, business):
    client = api_client(session)
    tenant_id = business.tenant.id
    try:
        recorded = _record_invoice(
            client,
            tenant_id,
            business.customer.id,
            number="RE-091",
            amount="1000.00",
            kind="sales_invoice",
            day="2026-07-01",
        )
        assert recorded.status_code == 201
        invoice_id = recorded.json()["id"]

        # Recording is not booking. Until it is booked the ledger holds nothing
        # for it, which is why every money class was blind to it.
        with pytest.raises(InvalidOperation):
            open_invoice_amount(session, tenant_id, invoice_id)

        booked = client.post(
            f"/api/tenants/{tenant_id}/finance/sales-invoices/postings",
            json={"document_id": invoice_id},
        )

        assert booked.status_code == 201
        assert len(booked.json()["ledger_entry_ids"]) == 2
        # Every figure is the document's own; no surface introduced one.
        assert open_invoice_amount(session, tenant_id, invoice_id) == Decimal(1000)

        # Booking twice is refused, and so is the wrong type and the unknown.
        again = client.post(
            f"/api/tenants/{tenant_id}/finance/sales-invoices/postings",
            json={"document_id": invoice_id},
        )
        assert again.status_code == 400
        supplier_side = _record_invoice(
            client,
            tenant_id,
            business.supplier.id,
            number="ER-091-WRONG",
            amount="10.00",
            kind="supplier_invoice",
            day="2026-07-01",
        )
        wrong_type = client.post(
            f"/api/tenants/{tenant_id}/finance/sales-invoices/postings",
            json={"document_id": supplier_side.json()["id"]},
        )
        assert wrong_type.status_code == 400
        unknown = client.post(
            f"/api/tenants/{tenant_id}/finance/sales-invoices/postings",
            json={"document_id": "doc_missing"},
        )
        assert unknown.status_code == 404

        foreign = create_tenant(session, "Foreign booking tenant")
        across = client.post(
            f"/api/tenants/{foreign.id}/finance/sales-invoices/postings",
            json={"document_id": invoice_id},
        )
        assert across.status_code == 404

        # And a booked invoice is settleable the way it always could have been,
        # once something could book it: a credit note nets against it through
        # the existing relation.
        credit = _record_invoice(
            client,
            tenant_id,
            business.customer.id,
            number="GS-091",
            amount="150.00",
            kind="credit_note",
            day="2026-07-05",
        )
        client.post(
            f"/api/tenants/{tenant_id}/finance/credit-notes/postings",
            json={"credit_note_id": credit.json()["id"]},
        )
        netted = client.post(
            f"/api/tenants/{tenant_id}/finance/credit-notes/allocations",
            json={
                "credit_note_id": credit.json()["id"],
                "invoice_id": invoice_id,
                "amount": "150.00",
            },
        )
        assert netted.status_code == 201
        assert open_invoice_amount(session, tenant_id, invoice_id) == Decimal(850)
    finally:
        app.dependency_overrides.clear()


def test_a_supplier_invoice_can_be_booked_over_the_api(session, business):
    client = api_client(session)
    tenant_id = business.tenant.id
    try:
        recorded = _record_invoice(
            client,
            tenant_id,
            business.supplier.id,
            number="ER-091",
            amount="400.00",
            kind="supplier_invoice",
            day="2026-07-01",
        )
        assert recorded.status_code == 201
        invoice_id = recorded.json()["id"]

        booked = client.post(
            f"/api/tenants/{tenant_id}/finance/supplier-invoices/postings",
            json={"document_id": invoice_id},
        )

        assert booked.status_code == 201
        assert open_invoice_amount(session, tenant_id, invoice_id) == Decimal(400)

        again = client.post(
            f"/api/tenants/{tenant_id}/finance/supplier-invoices/postings",
            json={"document_id": invoice_id},
        )
        assert again.status_code == 400

        # The positive control for the type guard: a sales invoice is refused
        # here and accepted by its own operation.
        sales_side = _record_invoice(
            client,
            tenant_id,
            business.customer.id,
            number="RE-091-WRONG",
            amount="10.00",
            kind="sales_invoice",
            day="2026-07-01",
        )
        wrong_type = client.post(
            f"/api/tenants/{tenant_id}/finance/supplier-invoices/postings",
            json={"document_id": sales_side.json()["id"]},
        )
        assert wrong_type.status_code == 400
        right_type = client.post(
            f"/api/tenants/{tenant_id}/finance/sales-invoices/postings",
            json={"document_id": sales_side.json()["id"]},
        )
        assert right_type.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_booking_makes_the_money_classes_reachable(session, business):
    """The claim the whole specification rests on, driven through the API alone.

    Five conditions needed a posted invoice and no surface could produce one, so
    on any tenant that never ran the demo they could not fire. Two of them are
    driven end to end here.
    """
    from reality.services.exceptions import operational_exceptions

    client = api_client(session)
    tenant_id = business.tenant.id
    as_of = datetime(2026, 8, 31, 12, tzinfo=UTC)
    try:
        client.post(
            f"/api/tenants/{tenant_id}/payment-terms",
            json={
                "code": "SK2_10",
                "name": "2% 10 days, net 30",
                "due_days": 30,
                "discount_percent": "2",
                "discount_days": 10,
            },
        )
        receivable = _record_invoice(
            client,
            tenant_id,
            business.customer.id,
            number="RE-091-QUEUE",
            amount="900.00",
            kind="sales_invoice",
            day="2026-07-01",
            term="SK2_10",
        )
        payable = _record_invoice(
            client,
            tenant_id,
            business.supplier.id,
            number="ER-091-QUEUE",
            amount="500.00",
            kind="supplier_invoice",
            day="2026-08-25",
            term="SK2_10",
        )

        # Recorded and unbooked: the queue cannot see either of them, which was
        # the state of every real tenant.
        reported = {
            row.class_id
            for row in operational_exceptions(session, tenant_id, as_of=as_of)
        }
        assert "overdue_receivable" not in reported
        assert "purchase_discount_available" not in reported

        client.post(
            f"/api/tenants/{tenant_id}/finance/sales-invoices/postings",
            json={"document_id": receivable.json()["id"]},
        )
        client.post(
            f"/api/tenants/{tenant_id}/finance/supplier-invoices/postings",
            json={"document_id": payable.json()["id"]},
        )

        reported = {
            row.class_id: row
            for row in operational_exceptions(session, tenant_id, as_of=as_of)
        }
        assert reported["overdue_receivable"].record_id == receivable.json()["id"]
        assert reported["purchase_discount_available"].record_id == payable.json()["id"]
    finally:
        app.dependency_overrides.clear()


def test_company_lifecycle_endpoints_require_owner_membership(
    session, company_setup_login, monkeypatch
):
    """Spec 186 FR-009: members see the danger zone but the API refuses their actions."""
    from reality.db.core import Tenant

    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(auth_module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    create_tenant(session, "Active Company")
    target = create_tenant(session, "Shared Company")
    client = api_client(session)
    try:
        actor = company_setup_login(client)
        session.add(
            TenantMembership(
                id=uid("mem"), tenant_id=target.id, user_id=actor.id, role="member"
            )
        )
        session.commit()

        payload = {"confirmation_name": target.name, "confirmation_word": "DELETE"}
        for path, body in (
            ("archive", None),
            ("restore", None),
            ("delete", payload),
        ):
            response = client.post(f"/api/v1/companies/{target.id}/{path}", json=body)
            assert response.status_code == 403, path
        assert session.get(Tenant, target.id).archived_at is None

        membership = session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == target.id,
                TenantMembership.user_id == actor.id,
            )
        )
        membership.role = "owner"
        session.commit()
        archived = client.post(f"/api/v1/companies/{target.id}/archive")
        assert archived.status_code == 200
        deleted = client.post(f"/api/v1/companies/{target.id}/delete", json=payload)
        assert deleted.status_code == 204
        assert session.scalar(select(Tenant.id).where(Tenant.id == target.id)) is None
    finally:
        app.dependency_overrides.clear()
