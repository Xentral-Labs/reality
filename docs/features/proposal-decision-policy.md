# Proposal Decision Policy

Specification: [323](../../specs/323-proposal-decision-policy/spec.md).

Preparation, common review and specialized delivery review return `next_step.decision_policy`, derived from the same
approval policy that dispatches the existing authorization checks. No policy is
stored as new business authority. Confirmation still executes through the shared
application boundary and preserves tenant scope, review tokens, stale-state checks,
transactional member rechecks, reconciliation and replay behavior.

## Approval authority

| Authority | Meaning |
|---|---|
| `company_owner` | Existing owner checks apply; costing also checks active user status. |
| `company_member` | Existing active company-member checks apply in the stated context. |
| `private_report_author` | Active membership and the original sealed report/request author are required. |
| `account_user` | Existing account identity is required; this does not introduce company-owner authority. |
| `action_context` | Existing channel, tenant-policy and action-service authority apply; no new role is invented. |
| `unavailable` | Unknown, retired, nonmutating or malformed-input actions gain no approval authority. |

`approval.conditions` names the applicable checks. `approval.exceptions` explains
existing bounded exceptions, including disabled-auth identity-free finance/credit,
trusted local delivery calls, delivery platform admins, Playground reference actions
and transaction-bound cost-profile initialization. These descriptors never authorize
an exception independently of its server-side context. The legacy delivery
`delivery_trusted_local` exception names the existing missing-principal branch;
it does not verify caller locality. Adapter scope/tool checks still govern external
calls, including permissioned token-only calls that have no user principal. This
feature does not turn that branch into proof of membership or human involvement.

Rejection is separately `action_context`: approval-only owner or private-author
checks do not become rejection requirements. For example, an owner-only financial
proposal does not imply owner-only rejection.

## Decision and channels

`explicit_authorized_decision` is required. Authenticated Web, permissioned external
MCP and existing trusted local CLI paths retain their own access controls. Built-in
Chat remains read/propose only and hands off to human Web review. External MCP
confirmation requires confirmation scope and tool permission plus the action's
business-authority checks. An approval boolean is an assertion, not proof that a
human made the decision. Token attribution never invents a human identity.

`autonomous_agent_delegation` and `human_involvement_verified` are both false.
Agent-to-agent or autonomous approval requires a separate approved design.

## Compatibility

`next_step.required_principal` remains a deprecated compatibility summary:
owner maps to `authenticated_active_owner`, member or private author to
`authenticated_active_member`, and other cases retain `authorized_human`.
That historical label is not a stored role or evidence of verified human involvement.
Consumers should use the structured policy and treat approval authority separately
from rejection. Web tolerates a missing policy during rolling deployment.

## Implementation and verification

- Pure value: `domain/proposal_decisions.py`.
- Shared resolution/enforcement: `services/proposal_decisions.py`.
- Shared guidance: `services/proposal_reviews.py`.
- Shared execution: `tools/application.py`; specialized author and membership-target
  validation remain in their existing services.
- Verification evidence: [quickstart](../../specs/323-proposal-decision-policy/quickstart.md).
