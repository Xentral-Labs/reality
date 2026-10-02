# Proposal Decision Contract

next_step retains its existing fields and adds decision_policy:

- approval: authority (company_owner, company_member, private_report_author,
  account_user, action_context, unavailable), conditions and existing exceptions.
- rejection: authority action_context; no inherited approval-only owner restriction.
- explicit_authorized_decision: true.
- confirmation_channels: web, external_mcp, trusted_local_cli. Each channel retains
  its existing access controls; this list is descriptive, not permission.
- built_in_chat_can_confirm: false.
- autonomous_agent_delegation: false.
- human_involvement_verified: false.

required_principal remains a compatibility summary. company_owner maps to its
existing owner value; company_member/private_report_author map to member; other
available actions retain authorized_human. Unavailable actions do not gain execution
rights from the compatibility summary. approval authority governs approval only.
