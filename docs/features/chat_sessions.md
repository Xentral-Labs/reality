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
- Standalone Chat directly exposes History and New chat in the existing upper-right
  page header, with visible labels and no additional toolbar or menu to open first. Saved/archived sessions open in a bounded overlay on request,
  initially closed even on revisit (spec225 FR-020). New chat is always available.
- The message area never needs a separate conversation header; the selected title stays
  in the session list.
- message history
- composer
- structured action result/confirmation cards where relevant
