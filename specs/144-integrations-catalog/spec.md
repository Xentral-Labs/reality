# Feature Specification: Integration preparation catalog

**Feature Branch**: `feat/integrations-catalog`
**Created**: 2026-09-08
**Status**: Accepted scope
**Input**: User approved provider catalog and preparation dialogs, including Shopware 6; actual connections follow separately.

## Context and Intent
### Problem
Generic source registration does not explain which systems users can prepare or what data they intend to receive.
### Scope
Recognizable provider catalog, guided preparation, session drafts and retained source inspection.
### Non-Goals
No connector execution, credentials, OAuth, sync, new business schema, provider ranking or live connection claims.

## User Scenarios & Testing
### User Story 1 - Choose a provider (Priority: P1)
Users open Add integration and find Shopify, Shopware 6, Xentral, Shopify Payments, Stripe, PayPal, HubSpot, Salesforce, Akeneo and Pimcore by name or category.
**Independent Test**: Search Shopware and select its preparation flow; unmatched searches show an empty message.
**Acceptance Scenarios**:
1. Given the integrations page, when Add integration opens, then all ten providers have a business purpose and preparation status.
2. Given the catalog, when a category or search changes, then only matching providers remain.

### User Story 2 - Prepare an instance (Priority: P1)
Users name an instance, select intended data areas and review before saving a session draft.
**Independent Test**: Prepare two shops, reload, edit one, cancel another and remove a draft without network mutations.
**Acceptance Scenarios**:
1. Given a provider, when name and at least one area are supplied, then review summarizes them and Save draft creates a visibly unconnected draft.
2. Given Shopify Payments, when preparing it, then a related shop name is required as planning context, not an asserted connection.
3. Given another company or user, when opening integrations, then previous drafts are not visible.
4. Given unavailable storage, when saving, then a visible error appears and the dialog retains input.

### User Story 3 - Inspect received data (Priority: P2)
Existing registered sources, received data, documents, source configuration and CSV import remain available.
**Independent Test**: Open a registered source's received records and its evidence through existing scoped routes.
**Acceptance Scenarios**:
1. Given registered sources, when opening source management, then existing records and actions remain available separately from drafts.
2. Given an empty or failed source read, then catalog preparation remains available without pretending the read succeeded.

## Requirements
- **FR-001**: Provide all ten named providers, category/search filtering and business descriptions; never claim a popularity ranking or working connector.
- **FR-002**: Provide a keyboard-accessible modal with name, intended data selection, review, Back, Close and Escape. Require nonblank name (maximum 100 characters), at least one data area and a related shop name for Shopify Payments.
- **FR-003**: Save, reopen, edit and remove drafts scoped to current user and company for this browser session only. Explain lifetime and absence of a live connection. Support multiple instances per provider. Handle invalid or unavailable storage without false success.
- **FR-004**: Never ask for credentials or send connector/business mutation requests from preparation. Use only preparation statuses and no fabricated timestamps or connection health.
- **FR-005**: Retain the received-data tab and contextual document URLs and existing source configuration/CSV workflows, visibly separated from drafts.
- **FR-006**: Support mobile and desktop, existing themes and all four interface languages; brand names remain original text. Modal focus returns to its trigger.

- **FR-007**: Received data and Documents MUST place page size and pagination once in the shared compact footer after the table, aligned right, without selection/export controls. This restores the Spec 137 register footer invariant. Existing pagination behavior is unchanged.

- **FR-008**: Integrations navigation MUST contain only My integrations and Received data. Existing document URLs remain accessible as a contextual register. Received records open one detail dialog with lossless original, import status and bounded actual source links to parties, items, locations, movements, documents, Facts, ledger entries and recorded events. Event navigation may lead to its recorded subject (including parties/items); never infer creation or origin from matching names. Label limits and missing links. All reads remain tenant-scoped.

### Key Entities
Provider definition; personal session preparation draft; existing registered source (unchanged).

## Success Criteria
- **SC-001**: A user can select any of ten providers and save a preparation in three guided steps after selection.
- **SC-002**: Preparation causes zero business writes or external provider requests.
- **SC-003**: Drafts survive reload within their session and never appear under another company/user.

## Assumptions and Dependencies
User's approval covers the described UI-only scope. Session-only personal drafts are a UI convenience, not shared company configuration. Data areas are planning choices, not promises of connector support. Existing services own all received data and actual source configuration. No unresolved clarification remains.

## Requirement Traceability

**Language**: English.

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001 | T002, T003 | Browser provider/category/search journey |
| FR-002 | T002, T004 | Browser validation, review, cancellation and focus |
| FR-003 | T002, T004, T005 | Browser reload, user/company scope, storage failure |
| FR-004 | T002, T003, T004 | Browser zero mutation assertion, no credentials |
| FR-005 | T002, T006 | Existing sources browser regression |
| FR-006 | T002, T007, T008 | Browser mobile/themes/languages, localization audit |
| FR-007 | T009 | Source browser regression asserts one footer after each table and no top page-size control |

FR-008 → T010; source inspector service regression and source browser navigation regression. This approved follow-up extends the earlier UI-only preparation scope with read-only source traceability; no connector or schema changes.
