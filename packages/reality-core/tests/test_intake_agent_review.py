"""Spec 360: explicit owner mandates bound actual agents and exact complete reviews."""

import json
from datetime import timedelta

import pytest
from sqlalchemy import select
from test_intake_admission import prepare

from reality.db.core import Document
from reality.mcp.auth import create_mcp_access_token
from reality.mcp.principal import MCPPrincipal, mcp_principal_context
from reality.services import core
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def owner_mandate(session, business, owner, *, daily_units=10, scope_overrides=None):
    token, _ = create_mcp_access_token(
        session, business.tenant.id, "Named review agent", issued_by_user_id=owner.id
    )
    system = core.create_source_system(
        session, business.tenant.id, "shopify", "Reviewed shop"
    )
    capability = core.create_source_capability(
        session, business.tenant.id, system.id, "order", "sales_order"
    )
    scope = {
        "source_system_id": system.id,
        "capability_ids": [capability.id],
        "profiles": ["shopify.order"],
        "effects": ["document", "commitment"],
        "max_rows_per_unit": 500,
        "max_units_per_day": daily_units,
        "amount_rule": {
            "currency": "EUR",
            "max_amount_per_unit": "10000",
            "max_amount_per_day": "100000",
        },
    }
    scope.update(scope_overrides or {})
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "intake_mandate_grant",
        {
            "agent_token_id": token.id,
            "scope": scope,
            "expires_at": (core.now() + timedelta(days=1)).isoformat(),
        },
    )
    result = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirmed=True,
        confirming_principal=Principal(owner.id),
    )
    return json.loads(result.output)["mandate_id"], token


def agent_context(business, token):
    return mcp_principal_context(
        MCPPrincipal(
            authentication_kind="manual",
            credential_id=token.id,
            grant_id=None,
            user_id=None,
            tenant_id=business.tenant.id,
            client_id="",
            scopes=frozenset(),
            allowed_tools=frozenset({"*"}),
        )
    )


def reviewed_evidence(session, business, mandate_id, proposal):
    from reality.services.intake_review import agent_review_material

    material = agent_review_material(
        session, business.tenant.id, mandate_id, proposal.id
    )
    return {
        **material["evidence_template"],
        "verdict": "approve",
        "reasons": ["source_matches_prepared_meaning"],
    }


def test_unconfirmed_direct_mandate_grant_refuses(session, business, scheduled_owner):
    from reality.services.intake_review import grant_review_mandate

    with pytest.raises(core.InvalidOperation):
        grant_review_mandate(
            session, business.tenant.id, "forged-token", {}, core.now()
        )


def test_actual_named_agent_accepts_exact_review_with_honest_attribution(
    session, business, scheduled_owner
):
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        result = submit_agent_review(session, business.tenant.id, evidence)
    assert result.status == "executed"
    assert result.decided_by_user_id is None
    assert result.decided_via_token_id == token.id
    receipt = json.loads(result.output)
    assert receipt["agent_review"]["mandate_id"] == mandate_id
    assert receipt["agent_review"]["revision"] == 1
    assert session.scalar(select(Document)) is not None


def test_forged_hash_or_incomplete_source_coverage_cannot_authorize(
    session, business, scheduled_owner
):
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        for field, bad in [("source_digest", "0" * 64), ("reviewed_references", [])]:
            with pytest.raises(core.InvalidOperation):
                submit_agent_review(
                    session, business.tenant.id, {**evidence, field: bad}
                )
    assert session.scalar(select(Document)) is None
    assert proposal.status == "proposed"


def test_builtin_chat_and_missing_authenticated_agent_refuse(
    session, business, scheduled_owner
):
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
    with pytest.raises(core.InvalidOperation):
        submit_agent_review(session, business.tenant.id, evidence)
    assert session.scalar(select(Document)) is None


def test_uncertain_verdict_retains_review_without_business_effects(
    session, business, scheduled_owner
):
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        result = submit_agent_review(
            session,
            business.tenant.id,
            {
                **evidence,
                "verdict": "uncertain",
                "reasons": ["meaning_requires_human_review"],
            },
        )
    assert result.status == "proposed"
    assert json.loads(result.output)["agent_reviews"][-1]["verdict"] == "uncertain"
    assert session.scalar(select(Document)) is None


def test_daily_quota_covers_distinct_accepted_units_and_replay_is_free(
    session, business, scheduled_owner
):
    from reality.services.intake import prepare_intake
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner, daily_units=1)
    _, _, first = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, first)
        submit_agent_review(session, business.tenant.id, evidence)
        assert submit_agent_review(session, business.tenant.id, evidence).id == first.id
        payload = {
            "id": "SECOND",
            "name": "Second",
            "currency": "EUR",
            "total_price": "1",
            "line_items": [
                {
                    "id": "second-line",
                    "sku": business.item.sku,
                    "quantity": 1,
                    "price": "1",
                    "total_price": "1",
                }
            ],
        }
        _, job = core.enqueue_shopify_order(
            session,
            business.tenant.id,
            payload,
            business.company.id,
            business.customer.id,
            business.location.id,
        )
        second = prepare_intake(session, business.tenant.id, job.id)
        second_evidence = reviewed_evidence(session, business, mandate_id, second)
        with pytest.raises(core.InvalidOperation):
            submit_agent_review(session, business.tenant.id, second_evidence)
    assert len(list(session.scalars(select(Document)))) == 1


@pytest.mark.parametrize(
    "change",
    ["expiry", "revoked", "revision", "token", "issuer", "source", "capability"],
)
def test_current_authority_changes_refuse_retained_agent_verdict(
    session, business, scheduled_owner, change, monkeypatch
):
    from reality.db.core import SourceCapability, SourceSystem
    from reality.db.intake_review import IntakeReviewMandate
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        mandate = session.scalar(
            select(IntakeReviewMandate).where(IntakeReviewMandate.id == mandate_id)
        )
        if change == "expiry":
            expired_now = mandate.expires_at + timedelta(seconds=1)
            monkeypatch.setattr(core, "now", lambda: expired_now)
        elif change == "revoked":
            mandate.revoked_at = core.now()
        elif change == "revision":
            mandate.revision += 1
        elif change == "token":
            token.revoked_at = core.now()
        elif change == "issuer":
            scheduled_owner.status = "disabled"
        elif change == "source":
            session.scalar(
                select(SourceSystem).where(
                    SourceSystem.id == mandate.scope["source_system_id"]
                )
            ).is_active = False
        else:
            session.scalar(
                select(SourceCapability).where(
                    SourceCapability.id == mandate.scope["capability_ids"][0]
                )
            ).is_active = False
        session.flush()
        with pytest.raises(core.InvalidOperation):
            submit_agent_review(session, business.tenant.id, evidence)
    assert proposal.status == "proposed"
    assert session.scalar(select(Document)) is None


def test_source_pages_reconstruct_exact_original_bytes(
    session, business, scheduled_owner
):
    import base64

    from reality.db.core import SourceRecord
    from reality.services.intake_review import agent_review_source_page

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        page = agent_review_source_page(
            session, business.tenant.id, mandate_id, proposal.id
        )
        source = session.get(
            SourceRecord, (business.tenant.id, page["source_record_id"])
        )
        assert base64.b64decode(page["content"]) == source.payload.encode("utf-8")
        assert page["next_cursor"] is None
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        assert page["reference"] in evidence["reviewed_references"]
        for cursor in [-1, True, 1, 65536]:
            with pytest.raises(core.InvalidOperation):
                agent_review_source_page(
                    session, business.tenant.id, mandate_id, proposal.id, cursor=cursor
                )


def test_foreign_company_cannot_use_agent_mandates(session, business, scheduled_owner):
    from reality.services.intake_review import (
        agent_review_material,
        agent_review_source_page,
        submit_agent_review,
    )

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    foreign = core.create_tenant(session, "Foreign agent review")
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
        for call in [
            lambda: agent_review_material(session, foreign.id, mandate_id, proposal.id),
            lambda: agent_review_source_page(
                session, foreign.id, mandate_id, proposal.id
            ),
            lambda: submit_agent_review(session, foreign.id, evidence),
        ]:
            with pytest.raises(core.InvalidOperation):
                call()
    assert session.scalar(select(Document)) is None


def test_foreign_company_cannot_grant_or_revoke_mandates(
    session, business, scheduled_owner
):
    from reality.services.intake_review import (
        grant_review_mandate,
        revoke_review_mandate,
    )

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    foreign = core.create_tenant(session, "Foreign mandate changes")
    for call in [
        lambda: grant_review_mandate(session, foreign.id, token.id, {}, core.now()),
        lambda: revoke_review_mandate(session, foreign.id, mandate_id, 1),
    ]:
        with pytest.raises(core.InvalidOperation):
            call()


def test_confirmed_revocation_increments_revision_and_blocks_prior_review(
    session, business, scheduled_owner
):
    from reality.db.intake_review import IntakeReviewMandate
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, intake = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, intake)
    revoke = create_change_proposal(
        session,
        business.tenant.id,
        "intake_mandate_revoke",
        {"mandate_id": mandate_id, "expected_revision": 1},
    )
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        revoke.id,
        confirmed=True,
        confirming_principal=Principal(scheduled_owner.id),
    )
    mandate = session.get(IntakeReviewMandate, (business.tenant.id, mandate_id))
    assert mandate.revision == 2 and mandate.revoked_at is not None
    with agent_context(business, token), pytest.raises(core.InvalidOperation):
        submit_agent_review(session, business.tenant.id, evidence)
    assert session.scalar(select(Document)) is None


@pytest.mark.parametrize(
    "change", ["currency", "unit_amount", "daily_amount", "effects", "owner_demotion"]
)
def test_agent_scope_and_commercial_limits_cannot_be_bypassed(
    session, business, scheduled_owner, change
):
    from reality.db.core import TenantMembership
    from reality.services.intake_review import submit_agent_review

    overrides = {}
    amounts = {
        "currency": "EUR",
        "max_amount_per_unit": "10000",
        "max_amount_per_day": "100000",
    }
    if change == "currency":
        amounts["currency"] = "USD"
    elif change == "unit_amount":
        amounts["max_amount_per_unit"] = "1"
    elif change == "daily_amount":
        amounts["max_amount_per_day"] = "1"
    elif change == "effects":
        overrides["effects"] = ["document"]
    overrides["amount_rule"] = amounts
    mandate_id, token = owner_mandate(
        session, business, scheduled_owner, scope_overrides=overrides
    )
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        if change == "effects":
            with pytest.raises(core.InvalidOperation):
                reviewed_evidence(session, business, mandate_id, proposal)
        else:
            evidence = reviewed_evidence(session, business, mandate_id, proposal)
            if change == "owner_demotion":
                membership = session.scalar(
                    select(TenantMembership).where(
                        TenantMembership.tenant_id == business.tenant.id,
                        TenantMembership.user_id == scheduled_owner.id,
                    )
                )
                membership.role = "member"
                session.flush()
            with pytest.raises(core.InvalidOperation):
                submit_agent_review(session, business.tenant.id, evidence)
    assert session.scalar(select(Document)) is None


def test_agent_settlement_is_a_mutating_mcp_confirmation_tool():
    from reality.mcp.catalog import MCP_TOOL_CATALOG

    tool = next(
        tool
        for tool in MCP_TOOL_CATALOG
        if tool.name == "intake_agent_review_and_execute"
    )
    assert tool.access == "confirm"
    assert tool.mutating


@pytest.mark.parametrize("change", ["scope", "expiry", "token", "revision"])
def test_current_mandate_cannot_expand_original_owner_decision(
    session, business, scheduled_owner, change
):
    from reality.db.intake_review import IntakeReviewMandate
    from reality.services.intake_review import submit_agent_review

    mandate_id, token = owner_mandate(session, business, scheduled_owner)
    _, _, proposal = prepare(session, business)
    with agent_context(business, token):
        evidence = reviewed_evidence(session, business, mandate_id, proposal)
    mandate = session.get(IntakeReviewMandate, (business.tenant.id, mandate_id))
    if change == "scope":
        mandate.scope = {**mandate.scope, "max_units_per_day": 100000}
    elif change == "expiry":
        mandate.expires_at += timedelta(days=100)
    elif change == "token":
        replacement, _ = create_mcp_access_token(
            session,
            business.tenant.id,
            "Unapproved replacement",
            issued_by_user_id=scheduled_owner.id,
        )
        mandate.agent_token_id = replacement.id
        token = replacement
    else:
        mandate.revision += 1
        evidence = {**evidence, "revision": mandate.revision}
    session.flush()
    with agent_context(business, token), pytest.raises(core.InvalidOperation):
        submit_agent_review(session, business.tenant.id, evidence)
    assert proposal.status == "proposed"
    assert session.scalar(select(Document)) is None
