"""Shared proposal authority selection and existing authorization boundaries."""

import os
from typing import Any, Literal

from sqlalchemy.orm import Session

from reality.domain.proposal_decisions import (
    ACCOUNT_MUTATION_TOOLS,
    MEMBERSHIP_MUTATION_TOOLS,
    REFERENCE_MUTATION_TOOLS,
    ApprovalAuthority,
    AuthorityCheck,
    ProposalDecisionPolicy,
)
from reality.services.core import InvalidOperation
from reality.services.memberships import Principal

#: Releases only a company owner confirms: credit holds (spec 298) and shipping a
#: prepayment order before it is paid (spec 347).
OWNER_RELEASE_TOOLS = frozenset({"credit_hold_release", "prepayment_release"})


def resolve_decision_policy(
    tool: str,
    arguments: dict[str, Any],
    *,
    available: bool = True,
) -> ProposalDecisionPolicy:
    """Select checks by action; review evidence never replaces stronger authority."""
    from reality.tools.application import TOOLS
    from reality.tools.finance import FINANCE_COMMANDS

    definition = TOOLS.get(tool)
    approval_available = available and definition is not None and definition.mutating
    checks: list[AuthorityCheck] = []
    exceptions: list[str] = []
    authority: ApprovalAuthority = "action_context"
    financial_intake = tool == "intake_apply" and any(
        effect.get("operation") in {"customer_payment", "payment_allocation"}
        for effect in arguments.get("plan", {}).get("effects", [])
    )
    if tool in FINANCE_COMMANDS or tool in OWNER_RELEASE_TOOLS or financial_intake:
        authority = "company_owner"
        checks.append(
            "credit_owner" if tool in OWNER_RELEASE_TOOLS else "finance_owner"
        )
        exceptions.append("identity_free_only_when_auth_disabled")
    if tool == "cost.change":
        checks.insert(0, "cost_owner")
        exceptions = ["transaction_bound_cost_profile_initialization"]
    if tool in {"graph.reports.change", "graph.requests.create"}:
        authority = "private_report_author"
        checks.append(
            "report_author" if tool == "graph.reports.change" else "request_author"
        )
    if tool in MEMBERSHIP_MUTATION_TOOLS:
        checks.append("membership_identity")
        checks.append("membership_owner")
        authority = "company_owner"
    elif tool in ACCOUNT_MUTATION_TOOLS:
        authority = "account_user"
        checks.append("account_identity")
    if "_delivery_review" in arguments or tool in {
        "intake_apply",
        "intake_batch_apply",
    }:
        checks.append("reviewed_member")
        if authority == "action_context":
            authority = "company_member"
        exceptions.extend(["delivery_platform_admin", "delivery_trusted_local"])
    if tool in REFERENCE_MUTATION_TOOLS:
        checks.append("reference_member")
        authority = "company_member"
        exceptions.extend(
            [
                "reference_playground",
                "delivery_platform_admin",
                "delivery_trusted_local",
            ]
        )
    # Retired actions cannot execute anew, but executed replay retains its original
    # pre-replay authority checks, including reviewed membership and private author.
    return ProposalDecisionPolicy(
        authority if approval_available else "unavailable",
        tuple(checks),
        tuple(dict.fromkeys(exceptions)),
    )


def require_decision_authority(
    session: Session,
    tenant_id: str,
    policy: ProposalDecisionPolicy,
    principal: Principal | None,
    *,
    phase: Literal["preflight", "identity", "execution", "locked", "reference"],
    confirmed: bool = False,
) -> None:
    """Run existing checks at their original lifecycle and transaction phases.

    Private authors and membership owner checks remain in their specialized
    services because they validate held sealed arguments or the exact removal target.
    The caller supplies the non-Playground context for the reference phase.
    """
    from reality.services.delivery_actions import require_delivery_principal
    from reality.services.memberships import require_owner

    if phase == "preflight":
        if "cost_owner" in policy.checks:
            from reality.services.costing import _owner

            if not confirmed:
                raise InvalidOperation(code="cost_decision_confirmation_required")
            _owner(session, tenant_id, principal)
        if "credit_owner" in policy.checks:
            if principal is not None:
                require_owner(session, tenant_id, principal)
            elif os.environ.get("REALITY_AUTH_MODE") != "disabled":
                raise InvalidOperation(code="company_owner_access_required")
    if phase == "identity":
        if "membership_identity" in policy.checks and principal is None:
            raise InvalidOperation(code="membership_change_owner_required")
        if "account_identity" in policy.checks and principal is None:
            raise InvalidOperation(code="account_confirmation_required")
    if phase == "execution" and "finance_owner" in policy.checks:
        if principal is not None:
            require_owner(session, tenant_id, principal)
        elif os.environ.get("REALITY_AUTH_MODE") != "disabled":
            raise InvalidOperation(code="account_change_owner_required")
    if phase == "locked" and "reviewed_member" in policy.checks:
        require_delivery_principal(session, tenant_id, principal)
    if phase == "reference" and "reference_member" in policy.checks:
        require_delivery_principal(session, tenant_id, principal)
