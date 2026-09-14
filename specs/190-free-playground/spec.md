# Feature Specification: Free Playground

**Feature Branch**: `190-free-playground`
**Language**: English

**Created**: 2026-09-14
**Status**: Implemented and verified locally; implementation authorized by the owner ("ja mach"), including the subsequent no-expiry/no-permanent-promise clarification.

## Context and Intent

### Problem
A prospective user meets unclear trial terms, admission review and company configuration before seeing useful business reality. The owner wants many people exploring freely and voluntarily supporting the public GitHub project.

### Scope
A free, verified-account Playground trial with an owner-private canonical demo, three read-only starting tasks, a bounded managed AI allowance and a voluntary GitHub invitation after a useful result. Preserve feature 189 admission controls.

### Non-Goals
Anonymous guest entry is a later increment. No production cloud pricing change, payment collection, subscription conversion, paid upgrade, star verification/rewards, external analytics SDK, production rollout, schema expansion or alternative business engine. GitHub clicks are not represented as stars. Cross-device prompt dismissal is not promised.

## User Scenarios & Testing

### User Story 1 - Reach useful demo data (Priority: P1)
As a prospect I understand the free offer and, after verifying my email, enter my own ready demo without completing a company questionnaire.

**Independent Test**: Register with Playground intent, verify, enter, reload and assert one owner-private canonical company with a working Home.

**Acceptance Scenarios**:
1. **Given** ordinary signup with explicit Playground creation consent and open admission, **When** email is verified, **Then** the authenticated entry creates the canonical international demo through shared services and opens Home.
2. **Given** failed initialization, **When** retrying, **Then** the same receipt/company completes; email verification stays valid.
3. **Given** manual admission, disabled Playground, invitation or an existing deep link, **When** entering, **Then** existing authorization and destination remain authoritative.

### User Story 2 - Explore before asking AI (Priority: P1)
As a new user I can find orders needing attention, explain an incomplete delivery and inspect open receivables from current service-backed records.

**Independent Test**: Each starting task opens the existing operational page; delivery completion requires an actual delivery detail. Reads work with no managed AI available.

**Acceptance Scenarios**:
1. **Given** the demo Home, **When** selecting a task, **Then** the corresponding existing reader and traceable records answer it without an AI request.
2. **Given** a task is loading or fails, **When** no valid result renders, **Then** no success invitation appears.
3. **Given** a successful result, **When** the user dismisses the voluntary GitHub invitation, **Then** it stays dismissed for that account in that browser.

### User Story 3 - Understand the free AI boundary (Priority: P2)
As a free user I see my remaining managed AI questions and exact daily reset without losing the ability to explore.

**Independent Test**: Twenty dispatched requests across conversations consume one account allowance; the next never reaches the provider; the next UTC day restores it.

**Acceptance Scenarios**:
1. **Given** concurrent requests at the last slot, **When** both dispatch, **Then** at most one reaches managed AI.
2. **Given** exhausted allowance, **When** composing a question, **Then** the draft is retained, reset is visible and operational pages remain accessible.
3. **Given** an own provider key or no configured managed provider, **When** using chat, **Then** no free managed allowance is consumed.

### Edge Cases
Owner isolation; request replay after pause or archive; partial initialization; explicit disabled policy; invitations and existing accounts; unavailable AI; UTC midnight; concurrent tabs and multiple companies; transport failures after provider dispatch; browser storage unavailable; late reads after company switch; empty successful reads versus uninitialized observations.

## Requirements

### Functional Requirements
- **FR-001**: Public landing and signup MUST describe the Playground as available to try for free, with no credit card and no automatic paid conversion; MUST NOT promise permanent free access, separately from production cloud terms.
- **FR-002**: Ordinary signup MUST record explicit Playground intent/creation consent; invitations and historical users MUST NOT acquire inferred consent.
- **FR-003**: Verified active users with that intent MUST enter one owner-private canonical international demo through confirmed shared setup services, without the setup questionnaire. Read-only endpoints MUST NOT create it.
- **FR-004**: Entry MUST reuse the stable owner receipt across retries/concurrency, preserve completed live setup/pause controls, and never recreate an archived company. Explicit manual admission and disabled Playground remain authoritative; an unset Playground switch enables the free entry.
- **FR-005**: Playground Home MUST offer the three approved tasks through existing attention, delivery and receivables readers; all existing explainability and mutation confirmations remain.
- **FR-006**: A nonblocking, dismissible GitHub invitation MUST appear only after a matching current-company task result renders successfully. Delivery requires detail, not just a register. Dismissal/star-link click persists per account per browser; no gate or reward.
- **FR-007**: All newly created public-signup accounts MUST receive trial allowance independently of optional demo consent; omitting the demo flag MUST NOT bypass it. Managed AI for these accounts MUST allow at most 20 dispatched questions per account per UTC day across conversations and all their companies, so creating an ordinary company cannot bypass it. Existing accounts using Playground companies share this same limit. Trusted authenticated caller is charged; service calls without a user charge the owning account. Atomic reservation precedes provider dispatch, including the legacy companion path. Provider-dispatched failures count; validation/missing-provider/own-key requests do not. One question includes its existing bounded tool loop.
- **FR-008**: Chat MUST show authoritative allowance and next reset, refresh after sends/refusals, retain drafts at exhaustion and keep non-AI exploration usable. Own-provider and production behavior remain unchanged.
- **FR-009**: New UI text MUST support English, German, Dutch and Spanish, keyboard access and narrow screens. No new tracking provider or automated GitHub action is introduced.

- **FR-010**: Signup, email verification, session checks, initial workspace loading and demo preparation MUST show immediate visible, localized progress with an accessible status and spinner. Pending submissions MUST prevent duplicates, failures MUST restore retry, and navigation MUST preserve the selected language. No synthetic progress percentages or completion claims.

### Key Entities
Existing account and security events record consent and managed-provider dispatch. Existing PlaygroundRun owns the canonical company and durable initialization receipt. Existing business records remain the only operational authority. Browser preference stores only the optional invitation dismissal.

## Success Criteria
- **SC-001**: A verified open-admission prospect reaches a populated private demo with no additional setup fields or review step.
- **SC-002**: All three tasks reveal a current service-backed result without spending an AI question.
- **SC-003**: Concurrent allowance tests prove no 21st daily managed dispatch and successful UTC reset.
- **SC-004**: No subscription is introduced; voluntary GitHub clicks are never claimed as actual stars.

## Assumptions and Dependencies
The approved proposal supplies product scope. Existing auth, canonical demo services and scheduler/worker are reused. Live setup uses the existing durable completion marker and shared jobs. Hosted operation requires deployed code, open admission and enabled Playground plus configured managed provider for AI. The owner corrected the positioning to a free trial without a permanent-free promise. The owner explicitly chose an initial trial without an expiration date and without a permanent-free promise. Existing security event retention must retain the current UTC day's usage. Product growth can be assessed separately using existing signup records and public repository star totals; no new behavioral tracking is included.

## Requirement Traceability

All repository artifacts are written in English; user-facing translations support the existing languages.

| Requirement | Scenarios | Planned evidence |
| --- | --- | --- |
| FR-001 | US1 | Site offer contracts and localization audit |
| FR-002 | US1.1, US1.3 | Consent and invitation/admission API tests |
| FR-003 | US1.1–2 | Entry service/API and browser journey |
| FR-004 | US1.2–3 | Retry/archive/pause and policy tests |
| FR-005 | US2.1 | Task routing and rendered operational readers |
| FR-006 | US2.2–3 | Current-company result and dismissal checks |
| FR-007 | US3.1–3 | PostgreSQL concurrency, reset and provider-boundary tests |
| FR-008 | US3.2 | Allowance read, draft preservation and composer checks |
| FR-009 | All | Locale audits, keyboard/narrow-screen review |

## Loading feedback refinement (2026-09-14)

Owner reported a white transition after signup and requested a live reproduction. The local account reached its demo successfully, but session loading had an unlabeled spinner, workspace and entry-policy reads had only skeletons, verification had no busy guard, and signup lost its explicit language on navigation. Accepted scope: make these existing asynchronous transitions legible without changing admission, setup, or data services. FR-010 maps to delayed-response browser checks, duplicate-submit/error recovery checks, locale checks and the real local signup smoke test.

## Current hosted offer refinement

Owner confirms that only a free hosted trial exists and requests removal of the paid Cloud card and limited-capacity banner. This supersedes the original non-goal of retaining paid Cloud positioning.

- **FR-011**: The platform Cloud card MUST describe only the current free trial: no card, no automatic paid subscription, initially no fixed expiry and no permanent-free promise. It MUST NOT advertise monthly pricing, founding prices, usage purchases or future paid pricing. Remove the entire public capacity/waitlist banner and its footnote. Keep signup, self-hosting and backend admission controls unchanged.

Acceptance: on `/platform`, the hosted card offers free signup, the paid terms and capacity banner are absent, and all four locales render correctly on desktop and mobile.

- **FR-012**: The Packages page MUST end after the hosted trial and self-hosted options, followed by the shared footer. Remove the agent-ecosystem introduction, architecture diagram, named-agent examples and compatibility footnote from this page. Other public pages remain unchanged. The owner approved this focused removal.

- **FR-013**: Trial the shared public header with a compact single-line brand, neutral navigation (Overview, How it works, Cloud & Self-hosted, Docs), a subdued language control and one prominent free-trial CTA. Preserve destinations, language handoff, accessible menu behavior and responsive layouts. The owner authorized a local design preview.

- **FR-014**: The platform hero eyebrow, heading and description MUST share the left edge of the offer cards across desktop and mobile widths. Preserve readable text widths and existing vertical spacing.

- **FR-015**: Refine the public pages with more readable heading tracking/line height, a consistent responsive section-spacing rhythm and consistent free-trial CTA wording/color. Place the platform trial note near its introduction and reduce the gap before offers. Preserve routing, content meaning, existing dark/light sections, accessible focus and mobile layouts. Owner approved this first visual-polish round.

- **FR-016**: Preview a product-led ERP Lite section using actual delivery-detail screenshots from the canonical demo, paired with a concise explanation of a partially fulfilled commitment. Capture real desktop/mobile rendering in en/de/nl/es, show no user identity or app navigation, label the example as demo data and retain accessible text equivalents. No fabricated UI, altered business values, live-data claims or interactive screenshot controls. Preserve existing capability content and signup.

- **FR-017**: Replace the illustrative Analytics artwork with actual demo weekly order-count chart and matching value-table captures in all four languages and desktop/mobile layouts. Identify static demo data and the exact ISO weeks; preserve the analytics documentation link and existing capability explanation. Provide text equivalents and no interactive-image or live-data claims.

- **FR-018**: Shorten the default How it works reading path while preserving comprehension: principle, Source → Evidence → Reality → Context → Decision, one worked delivery example, shared agent/cockpit entry and confirmation boundaries. Move vocabulary, finance, corrections and repeated background into clearly named, keyboard-accessible native disclosures. Keep all existing deep content and links available, localize disclosure labels, preserve the how-it-works anchor, and reduce initial page height by at least 30% at desktop and mobile widths.

## Verification email return link — FR-019

**FR-019**: Verification emails include an HTML action and plain-text link to the configured Product App verification page. A fresh tab restores the recipient from a URL fragment, clears that fragment after storing it in tab-local state, and still requires explicit code submission. Never embed the code in the URL or verify on GET. Missing tab context permits manual email entry. Expose the existing resend-code action for expired codes with generic feedback; preserve verification expiry, admission, demo consent and invitation behavior.

## Availability policy supersession (spec 193)

[Always Available Storylines and Playground](../193-always-available-playground/spec.md)
supersedes the historical deployment-switch/disabled-entry policy in this feature.
Storyline, Playground, Sandbox setup and requested free-trial entry are regular
capabilities. Account admission, ownership, confirmation, quotas, archive state,
source controls and idempotency remain authoritative.
