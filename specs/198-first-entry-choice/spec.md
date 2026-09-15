# Feature Specification: Choose how the first company starts

**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope (owner: a fresh account should choose between a demo company
with live orders and an empty company, and may add demo data afterwards)

## Context and Intent
A verified account that asked for the Playground is currently sent into a canonical
demo company with live simulation the moment it first opens the app; the decision is
made for it. People who want to put their own data in first meet a company full of
synthetic orders and have to create a second company to get out of it.

Feature 190 deliberately removed the company questionnaire so that entry stays
frictionless, and this feature keeps that promise: the choice is two cards and one
click, with no name, environment or option form. The existing company setup dialog
remains the place for everything beyond those two starts.

### Non-Goals
The content of the canonical demo profile, the live simulation rate, admission,
verification, quotas, archiving, the ordinary company setup dialog, or any change to
accounts that already hold a company.

## User Scenarios & Testing
### US1 — Start with the demo company (P1)
A verified account entering for the first time chooses the demo company with live
orders in one click and reaches the same ready company, with the same live simulation,
that the previous automatic entry produced.

### US2 — Start empty (P1)
The same account may instead choose an empty company in one click and reaches a ready,
empty Sandbox. The receipt now reports a ready company, so the next entry goes straight
there instead of offering the choice again.

### US3 — Add the demo data later (P2)
An account that started empty can connect and start Demo Data in that company through
the existing controls, or leave it empty. Nothing about the empty start forecloses it.

### Edge cases
A lost response, a reload during creation or an explicit retry must produce the same
company, not a second one. An account that already holds a company is never asked.
Choosing one start and then retrying with the other is refused rather than silently
creating a different company. An archived demo company keeps its existing message.

## Requirements
- **FR-001**: Home entry for an account that requested the Playground and has no ready
  receipt yet presents exactly two starts — demo company with live orders, or empty
  company — and creates nothing until one is chosen. This replaces the automatic
  creation that ran under exactly the same condition; a deep link keeps its own
  destination, as before.
- **FR-002**: The demo start creates the canonical international demo Sandbox with
  live simulation, exactly as the automatic entry did.
- **FR-003**: The empty start creates a ready, empty Sandbox in which Demo Data can
  later be connected and started.
- **FR-004**: Both starts use the same account-scoped request key, so the receipt
  records which start was taken, the choice is not offered again, and a retry or lost
  response replays the same company. A retry stating the other start is refused.
- **FR-005**: The choice requires an authenticated, verified and eligible account and
  explicit confirmation; no start is created by navigation, reads or reloads.
- **FR-006**: Both cards and their explanations are available in all four interface
  languages and stay readable on a narrow viewport.

## Success Criteria
A new verified account sees two starts, creates nothing before clicking, and reaches
either a demo company with live orders or an empty Sandbox. A second entry goes
straight to that company. A repeated request replays one company; the conflicting
start is refused. Demo Data connects in a company that started empty.

## Assumptions and Dependencies
`free_playground.enter` and the account-scoped `POST /api/company-setup/playground`
stay the single entry path and gain the chosen content; `company_setup.create_company`
already enforces request-key idempotency, the choice fingerprint and Sandbox admission.
`demo_data.eligible` already accepts the `company-empty` preset, which is what lets an
empty start add demo data later. No schema change and no migration.

## Requirement Traceability
| Requirement | Proof |
|---|---|
| FR-001, FR-004, FR-005 | Service tests for both contents, replay, conflicting retry and eligibility |
| FR-002, FR-003 | Service tests over the created company plus a Demo Data connection after an empty start |
| FR-001, FR-006 | Web contract tests and a browser run over both cards in four languages and a narrow viewport |
