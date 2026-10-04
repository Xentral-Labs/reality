"""Derived decision requirements, independent of transport or persistence."""

from dataclasses import dataclass
from typing import Any, Literal

ApprovalAuthority = Literal[
    "company_owner",
    "company_member",
    "private_report_author",
    "account_user",
    "action_context",
    "unavailable",
]
AuthorityCheck = Literal[
    "cost_owner",
    "credit_owner",
    "finance_owner",
    "mandate_owner",
    "reviewed_member",
    "email_retry_review",
    "reference_member",
    "membership_identity",
    "account_identity",
    "membership_owner",
    "report_author",
    "request_author",
]

MEMBERSHIP_MUTATION_TOOLS = frozenset(
    {
        "member_invite",
        "invitation_resend",
        "invitation_revoke",
        "member_remove",
    }
)
ACCOUNT_MUTATION_TOOLS = MEMBERSHIP_MUTATION_TOOLS | {
    "business_journey_proposal_create",
    "business_journey_vote_set",
}
REFERENCE_MUTATION_TOOLS = frozenset(
    {
        "party_create",
        "item_create",
        "location_create",
        "party_update",
        "item_update",
        "location_update",
    }
)


@dataclass(frozen=True)
class ProposalDecisionPolicy:
    """Describe existing checks without granting decision or delegation rights."""

    authority: ApprovalAuthority
    checks: tuple[AuthorityCheck, ...] = ()
    exceptions: tuple[str, ...] = ()

    @property
    def required_principal(self) -> str:
        """Compatibility summary; never evidence that a human made the decision."""
        if self.authority == "company_owner":
            return "authenticated_active_owner"
        if self.authority in {"company_member", "private_report_author"}:
            return "authenticated_active_member"
        return "authorized_human"

    def as_dict(self) -> dict[str, Any]:
        return {
            "approval": {
                "authority": self.authority,
                "conditions": list(self.checks),
                "exceptions": list(self.exceptions),
            },
            "rejection": {"authority": "action_context"},
            "explicit_authorized_decision": True,
            "confirmation_channels": ["web", "trusted_local_cli"]
            if "email_retry_review" in self.checks
            else ["web", "external_mcp", "trusted_local_cli"],
            "built_in_chat_can_confirm": False,
            "autonomous_agent_delegation": False,
            "human_involvement_verified": False,
        }
