# Data Model: Human Chat Confirmation

No schema change is required.

## Existing records used

- **Change Proposal**: Chat may prepare this tenant-scoped opaque record. It remains `proposed`
  until a separate authorized principal confirms or rejects it.
- **Human decision attribution**: existing `decided_by_user_id` identifies a Web decision. Built-in
  Chat no longer settles proposals. External token attribution remains distinct.
- **Business Event and targets**: no target or proposal-attributed event exists before execution.

## State transitions

```text
Chat prepare: absent → proposed
Human confirm: proposed → executing → executed | failed | unresolved executing
Human reject: proposed → rejected
Chat model: no transition out of proposed
```

## Validation rules

- Conversation content cannot grant access.
- A tool call requires catalog exposure and dispatch permission.
- Human review retains principal, tenant, review-token and stale-state validation.
