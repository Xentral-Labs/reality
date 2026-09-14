# Feature: Tenant-scoped Chat Sessions

## Goal

Allow multiple persistent conversations per tenant.

## Rules

- A chat session belongs to exactly one tenant.
- Messages belong to exactly one session and tenant.
- Switching tenants never shows another tenant's sessions.
- Chat calls the shared tool/service layer; it does not write domain tables directly.
- Mutations should be represented as structured proposed actions and confirmed before execution in interactive use.
- A deterministic/no-network provider must exist for automated tests.

## Minimum UI

- With no saved session, the page shows only one centered first-use surface containing
  the introduction, contextual suggestions, and composer. It does not render an empty
  session list or conversation header.
- With saved sessions, the session list and new-conversation control are visible.
- The message area never needs a separate conversation header; the selected title stays
  in the session list.
- message history
- composer
- structured action result/confirmation cards where relevant
