"""Proposal guidance describes the same authority that approval enforces."""

import json

import pytest
from intake_review_support import reviewed_manual_order, reviewed_reserve

from reality.db.core import AppUser, ChangeProposal, TenantMembership, uid
from reality.services import core
from reality.services.memberships import Principal
from reality.services.proposal_reviews import proposal_next_step, proposal_review
from reality.tools.application import approve_and_execute_proposal, reject_proposal


def _held_release(session, business):
    from reality.mcp.catalog import MCP_TOOL_REGISTRY

    party = reviewed_create_party(
        session,
        business.tenant.id,
        "Credit policy customer",
        "customer",
        credit_limit="100",
    )
    _, order, _, commitments = reviewed_manual_order(
        session,
        business.tenant.id,
        "sales",
        "POLICY-323",
        business.company.id,
        party.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "100",
                "gross_amount": "200",
            }
        ],
        "200",
    )
    prepared = MCP_TOOL_REGISTRY["credit_hold_release_propose"].handler(
        session,
        business.tenant.id,
        {"document_id": order.id, "reason": "Reviewed prepayment"},
    )
    proposal = session.get(
        ChangeProposal, (business.tenant.id, prepared["proposal_id"])
    )
    return proposal, commitments


def _member(session, tenant_id, *, admin=False):
    user = AppUser(
        id=uid("usr"),
        email=f"{uid('mail')}@example.test",
        password_hash="unused",
        status="active",
        is_platform_admin=admin,
    )
    session.add(user)
    session.flush()
    membership = TenantMembership(
        id=uid("tmb"),
        tenant_id=tenant_id,
        user_id=user.id,
        role="member",
        status="active",
    )
    session.add(membership)
    session.flush()
    return user, membership


@pytest.mark.parametrize(
    ("tool", "arguments", "authority"),
    [
        ("finance.account.create", {}, "company_owner"),
        ("finance.settlement.apply", {}, "company_owner"),
        ("cost.change", {}, "company_owner"),
        ("credit_hold_release", {"_delivery_review": {}}, "company_owner"),
        ("shipment_dispatch", {"_delivery_review": {}}, "company_member"),
        ("party_create", {}, "company_member"),
        ("graph.reports.change", {}, "private_report_author"),
        ("graph.requests.create", {}, "private_report_author"),
        ("business_journey_vote_set", {}, "account_user"),
        ("member_remove", {}, "company_owner"),
        ("reserve", {}, "action_context"),
        ("retired_action", {}, "unavailable"),
    ],
)
def test_action_policy_separates_authority_decision_and_channels(
    tool, arguments, authority
):
    """
    BUSINESS TEST:
    Action policy separates authority decision and channels.
    GIVEN:
    Parameterized tool/arguments/authority cases cover owner, member, report author, account user, action context and retired actions.
    WHEN:
    Resolve next-step policy for each proposal.
    THEN:
    Approval authority matches parameter; rejection stays action_context; explicit decision and external confirmation channels are required without built-in chat confirmation or autonomous delegation claims.
    """
    proposal = ChangeProposal(type=f"tool:{tool}", input=json.dumps(arguments))
    step = proposal_next_step(proposal)
    policy = step["decision_policy"]
    assert policy["approval"]["authority"] == authority
    assert policy["rejection"]["authority"] == "action_context"
    assert policy["explicit_authorized_decision"] is True
    assert policy["confirmation_channels"] == [
        "web",
        "external_mcp",
        "trusted_local_cli",
    ]
    assert policy["built_in_chat_can_confirm"] is False
    assert policy["autonomous_agent_delegation"] is False
    assert policy["human_involvement_verified"] is False


def test_credit_owner_guidance_and_execution_agree(
    session, business, scheduled_owner, monkeypatch
):
    """
    BUSINESS TEST:
    Credit owner guidance and execution agree.
    GIVEN:
    Credit-release proposal exists with a member and active owner.
    WHEN:
    Compare delivery/proposal guidance and confirm as member then owner with authentication required.
    THEN:
    Guidance agrees on owner authority; member is refused and hold stays; owner confirmation clears it.
    """
    from reality.services.credit_exposure import active_credit_holds

    proposal, commitments = _held_release(session, business)
    member, _ = _member(session, business.tenant.id)
    review = proposal_review(session, business.tenant.id, proposal.id)
    from reality.services.delivery_actions import delivery_proposal_detail

    delivery = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert delivery["next_step"] == review["next_step"]
    assert review["next_step"]["required_principal"] == "authenticated_active_owner"
    assert (
        review["next_step"]["decision_policy"]["approval"]["authority"]
        == "company_owner"
    )
    token = json.loads(proposal.input)["_delivery_review"]["token"]
    monkeypatch.setenv("REALITY_AUTH_MODE", "required")
    with pytest.raises(core.InvalidOperation, match="owner"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(member.id),
            review_token=token,
            confirmed=True,
        )
    assert active_credit_holds(session, business.tenant.id, [c.id for c in commitments])
    approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(scheduled_owner.id),
        review_token=token,
        confirmed=True,
    )
    assert not active_credit_holds(
        session, business.tenant.id, [c.id for c in commitments]
    )


def test_owner_only_approval_does_not_add_owner_only_rejection(
    session, business, monkeypatch
):
    """
    BUSINESS TEST:
    Owner only approval does not add owner only rejection.
    GIVEN:
    Credit-release proposal needs owner approval and a member principal exists.
    WHEN:
    Reject as member with authentication required.
    THEN:
    Policy keeps action-context rejection and proposal is rejected.
    """
    proposal, _ = _held_release(session, business)
    member, _ = _member(session, business.tenant.id)
    monkeypatch.setenv("REALITY_AUTH_MODE", "required")
    assert (
        proposal_next_step(proposal)["decision_policy"]["rejection"]["authority"]
        == "action_context"
    )
    rejected = reject_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(member.id),
    )
    assert rejected.status == "rejected"


def test_shared_member_check_rechecks_current_membership_and_preserves_admin(
    session, business
):
    """
    BUSINESS TEST:
    Shared member check rechecks current membership and preserves admin.
    GIVEN:
    Shipment decision policy and member principal exist.
    WHEN:
    Check authority, remove membership, recheck and check admin/unauthenticated compatibility paths.
    THEN:
    Removed member is not found; active admin and existing no-principal compatibility path are accepted.
    """
    from reality.services.proposal_decisions import (
        require_decision_authority,
        resolve_decision_policy,
    )

    user, membership = _member(session, business.tenant.id)
    policy = resolve_decision_policy("shipment_dispatch", {"_delivery_review": {}})
    require_decision_authority(
        session, business.tenant.id, policy, Principal(user.id), phase="locked"
    )
    membership.status = "removed"
    session.flush()
    with pytest.raises(core.NotFound):
        require_decision_authority(
            session, business.tenant.id, policy, Principal(user.id), phase="locked"
        )
    admin, _ = _member(session, business.tenant.id, admin=True)
    require_decision_authority(
        session, business.tenant.id, policy, Principal(admin.id), phase="locked"
    )
    require_decision_authority(
        session, business.tenant.id, policy, None, phase="locked"
    )


def test_policy_preserves_cost_and_finance_identity_exceptions(
    session, business, monkeypatch
):
    """
    BUSINESS TEST:
    Policy preserves cost and finance identity exceptions.
    GIVEN:
    Finance account and cost change decision policies exist.
    WHEN:
    Check missing-principal authority with authentication disabled and required.
    THEN:
    Finance permits disabled-auth compatibility but refuses required-auth; cost still refuses missing principal in confirmed preflight.
    """
    from reality.services.proposal_decisions import (
        require_decision_authority,
        resolve_decision_policy,
    )

    finance = resolve_decision_policy("finance.account.create", {})
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    require_decision_authority(
        session, business.tenant.id, finance, None, phase="execution"
    )
    monkeypatch.setenv("REALITY_AUTH_MODE", "required")
    with pytest.raises(core.InvalidOperation):
        require_decision_authority(
            session, business.tenant.id, finance, None, phase="execution"
        )
    cost = resolve_decision_policy("cost.change", {})
    monkeypatch.setenv("REALITY_AUTH_MODE", "disabled")
    with pytest.raises(core.InvalidOperation):
        require_decision_authority(
            session, business.tenant.id, cost, None, phase="preflight", confirmed=True
        )


def test_unknown_and_malformed_policy_never_claims_approval_authority():
    """
    BUSINESS TEST:
    Unknown and malformed policy never claims approval authority.
    GIVEN:
    Retired tool or malformed JSON reserve payload is used.
    WHEN:
    Resolve proposal next-step policy.
    THEN:
    Approval authority is unavailable for both cases.
    """
    for tool, payload in [("retired_action", "{}"), ("reserve", "not-json")]:
        step = proposal_next_step(ChangeProposal(type=f"tool:{tool}", input=payload))
        assert step["decision_policy"]["approval"]["authority"] == "unavailable"


def test_retired_executed_review_rechecks_membership_before_replay(session, business):
    """
    BUSINESS TEST:
    Retired executed review rechecks membership before replay.
    GIVEN:
    An executed retired reviewed proposal exists and its member was removed.
    WHEN:
    Attempt confirmation replay and inspect next-step policy.
    THEN:
    Removed member is not found and retired approval authority remains unavailable.
    """
    user, membership = _member(session, business.tenant.id)
    proposal = ChangeProposal(
        tenant_id=business.tenant.id,
        id=uid("act"),
        type="tool:retired_reviewed_action",
        actor_type="agent",
        status="executed",
        input=json.dumps({"_delivery_review": {}}),
        output="{}",
    )
    session.add(proposal)
    session.flush()
    membership.status = "removed"
    session.flush()
    with pytest.raises(core.NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(user.id),
        )
    assert (
        proposal_next_step(proposal)["decision_policy"]["approval"]["authority"]
        == "unavailable"
    )


def test_member_removal_requires_owner_even_when_removing_self(session, business):
    """
    BUSINESS TEST:
    Member removal requires owner even when removing self.
    GIVEN:
    A member creates a proposal to remove their own membership.
    WHEN:
    Inspect policy and attempt self-confirmation.
    THEN:
    Owner authority is required, confirmation is refused and membership stays active.
    """
    from reality.tools.application import create_change_proposal

    user, membership = _member(session, business.tenant.id)
    proposal = create_change_proposal(
        session, business.tenant.id, "member_remove", {"membership_id": membership.id}
    )
    assert (
        proposal_next_step(proposal)["decision_policy"]["approval"]["authority"]
        == "company_owner"
    )
    with pytest.raises(core.InvalidOperation, match="owner"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(user.id),
            confirmed=True,
        )
    session.refresh(membership)
    assert membership.status == "active"


def test_shipment_member_guidance_and_execution_agree(session, business):
    """
    BUSINESS TEST:
    Shipment member guidance and execution agree.
    GIVEN:
    Delivery fixture has two reserved units and an active member.
    WHEN:
    Prepare shipment and confirm using its review token as member.
    THEN:
    Policy requires company_member; proposal executes and returns shipment identity.
    """
    from unified_fixtures import delivery_fixture

    from reality.tools.application import create_change_proposal

    fixture = delivery_fixture(session, business, quantity="2")
    reviewed_reserve(session, business.tenant.id, fixture.commitment.id)
    member, _ = _member(session, business.tenant.id)
    proposal = create_change_proposal(
        session,
        business.tenant.id,
        "shipment_dispatch",
        {
            "purpose": "customer_delivery",
            "counterparty_id": business.customer.id,
            "movements": [
                {
                    "commitment_id": fixture.commitment.id,
                    "item_id": business.item.id,
                    "from_location_id": business.location.id,
                    "quantity": "2",
                }
            ],
        },
    )
    assert (
        proposal_next_step(proposal)["decision_policy"]["approval"]["authority"]
        == "company_member"
    )
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=Principal(member.id),
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )
    assert executed.status == "executed"
    assert json.loads(executed.output)["shipment_id"]


@pytest.mark.parametrize("admin_outsider", [False, True])
def test_private_report_requires_original_author_but_rejection_does_not(
    session, business, scheduled_owner, admin_outsider
):
    """
    BUSINESS TEST:
    Private report requires original author but rejection does not.
    GIVEN:
    A member authored a private report proposal; admin_outsider parameter controls another owner's admin flag.
    WHEN:
    Attempt approval as outsider, approve as author, then reject delete proposal as outsider.
    THEN:
    Outsider approval is refused even as admin; author creates report and outsider may reject deletion.
    """
    from uuid import uuid4

    from reality.services.analytics.errors import AnalyticsError
    from reality.services.analytics.reports import caller, list_reports
    from reality.tools.application import create_change_proposal

    scheduled_owner.is_platform_admin = admin_outsider
    session.flush()
    author, _ = _member(session, business.tenant.id)
    principal = Principal(author.id)
    with caller(principal):
        proposal = create_change_proposal(
            session,
            business.tenant.id,
            "graph.reports.change",
            {
                "operation": "create",
                "request_id": str(uuid4()),
                "name": "Policy acceptance report",
                "question": {
                    "from": "order",
                    "as": "o",
                    "measures": ["stated_order_amount"],
                    "group_by": [{"field": "o.currency"}],
                },
            },
        )
    assert (
        proposal_next_step(proposal)["decision_policy"]["approval"]["authority"]
        == "private_report_author"
    )
    with pytest.raises(AnalyticsError, match="original author"):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=Principal(scheduled_owner.id),
            confirmed=True,
        )
    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=principal,
        confirmed=True,
    )
    assert executed.status == "executed"
    assert (
        len(
            list_reports(session, business.tenant.id, principal, report_kind="graph")[
                "records"
            ]
        )
        == 1
    )
    with caller(principal):
        rejected = create_change_proposal(
            session,
            business.tenant.id,
            "graph.reports.change",
            {
                "operation": "delete",
                "request_id": str(uuid4()),
                "report_id": list_reports(
                    session, business.tenant.id, principal, report_kind="graph"
                )["records"][0]["id"],
                "expected_revision": 1,
            },
        )
    assert (
        reject_proposal(
            session,
            business.tenant.id,
            rejected.id,
            confirming_principal=Principal(scheduled_owner.id),
        ).status
        == "rejected"
    )


from intake_review_support import reviewed_create_party
