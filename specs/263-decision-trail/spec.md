# Feature Specification: Decision Trail

**Feature Branch**: `263-decision-trail`
**Language**: English
**Created**: 2026-09-24
**Status**: Draft
**Input**: Owner, after an agent run set up a company through MCP (master data, payment terms, price lists, orders): every record to be created arrives as a decision and appears in the queue. Once confirmed it disappears, and it cannot be found in Activities or anywhere else. Why was something created, and who approved it? Is it stored and not shown, or is something structurally missing? I expected Activities, and the record itself, to show who confirmed the decision that created it.

## Context and Intent

### Problem

A decision is the moment a person accepts responsibility for a change. The product records most of that moment and then hides it, and for decisions confirmed through MCP it does not record the person at all. Measured on the local company "CanisPro Tiernahrung MCP-Reality-Test 2026-09-24" (40 proposals, all requested by an agent):

1. **Settled decisions have no surface.** The change proposal is kept forever, and `GET /change-proposals?status=history` already returns settled decisions with the decider's name (specs 054 and 055). No web code calls it: `DecisionsPage.tsx` requests only `pending`, and has done so since the initial public release. The decision history register of spec 054 (FR-001–FR-010) and the decider column of spec 055 (FR-006–FR-007) are therefore not delivered. A confirmed decision leaves the queue and cannot be reopened.
2. **A decision confirmed through MCP names nobody.** All 36 executed decisions of that company have `decided_by_user_id = NULL`. The MCP approval tool passes `confirming_principal=_analytics_caller()`, a context variable the MCP server never sets, and an MCP access token belongs to a company, not to a person. Reality cannot say which token confirmed, let alone on whose behalf. This loss is structural and cannot be repaired for decisions already taken.
3. **Some records cannot be traced to their decision at all.** The proposal id reaches a tool handler only when the tool is on a fixed allowlist in `approve_and_execute_proposal` (`tools/application.py`, `arguments["_action_id"] = proposal.id`). Parties, items, locations, orders and commitments are linked; payment terms (3 of 3), price lists (2 of 2), price tiers (24 of 24) and customer price-list assignments (2 of 2) are not. For these the business event carries no `action_id`, so neither the reason nor the decider can be reached from the record.
4. **The record and its activity do not say which decision made them.** The master-data registers render "Created here · name" (spec 211 FR-002), which stays blank because of (2) and (3) and never links to the decision itself. The Activities drawer shows a raw "Action ID" among technical details, with no label, no decider and no link.

### Principle

Every change made through a decision can be followed back to that decision, and the decision says who crossed the approval boundary, how, and when. Where Reality cannot know the person, it says precisely what it does know instead of leaving a blank or guessing a name.

An MCP confirmation is attributed to the token that sent it and to the owner who issued that token. That is an accountability statement, not a claim that the issuer pressed a button: Reality cannot observe the agent client, and the wording must not pretend otherwise.

### Scope

- Bind every newly issued MCP access token to the owner who issued it, and record on each decision settled through MCP which token settled it.
- Carry the proposal id to every business event written while a proposal executes, for every mutating tool, not an allowlist.
- Restore the decision history register (specs 054 and 055) on the Decisions page, including the decider and the MCP attribution.
- State on a record's origin and on each activity entry which decision caused it, who settled it and when, with a link that opens that decision.

### Non-Goals

- Reconstructing attribution for decisions already settled, or an issuer for tokens already issued; that information never existed.
- Personal MCP sign-in (OAuth per user); a token remains a company credential issued by an owner.
- Restricting MCP confirmation to the web; agents keep the right to confirm with `approved=true`.
- Attributing the *request* of a proposal to a token or person; the actor kind already stored remains the request attribution.
- Changing who may approve, the execution boundary, the two-step delivery review, or finance owner checks.
- Resolving proposals left in `executing` (3 in the measured company); outcome reconciliation is separate work.
- Linking events written without a proposal (demo seeding, scenarios, source interpretation); they correctly carry none.

### Existing Contracts

- [Decision History Register](../054-decision-history-table/spec.md)
- [Decision Attribution](../055-decision-attribution/spec.md)
- [Record Provenance](../211-record-provenance/spec.md)
- [Separate MCP Runtime](../018-separate-mcp-runtime/spec.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Know who confirmed through an agent (Priority: P1)

As an owner whose agent sets up a company through MCP, I can see for every decision it confirmed which token confirmed it and which owner issued that token.

**Why this priority**: Without it the agent path, which is the path this company was built on, has no accountable approver at all, and every later day of such a run widens a gap that can never be closed retroactively.

**Independent Test**: Issue an MCP token as an owner, have a client propose and confirm a change through MCP, then read the decision.

**Acceptance Scenarios**:

1. **Given** an owner issued an MCP token after this feature, **When** a client confirms a proposal with that token, **Then** the decision records the token and the history names the token and its issuer, worded as confirmed through that token rather than by that person.
2. **Given** a token issued before this feature, **When** a client confirms with it, **Then** the confirmation still succeeds, the decision records the token, and the issuer reads as unknown.
3. **Given** a client rejects a proposal through MCP, **When** the decision is read, **Then** the rejection is attributed the same way as an approval.
4. **Given** a signed-in person confirms in the web, **When** the decision is read, **Then** it names that person as today and records no token.
5. **Given** a token is later revoked or its issuer removed from the company, **When** past decisions are read, **Then** they keep naming the token and state that it is revoked, without exposing the issuer to another company.

### User Story 2 - Every confirmed change leads back to its decision (Priority: P1)

As an owner, I can reach from any record created or changed through a decision to the decision that caused it, whatever kind of record it is.

**Why this priority**: A trail that holds for items but not for prices is not a trail; the missing families are exactly the commercial terms that are most often questioned later.

**Independent Test**: Confirm one proposal for each mutating tool and check that every business event it wrote names that proposal.

**Acceptance Scenarios**:

1. **Given** a payment term, price list, price tier or price-list assignment is created through a confirmed proposal, **When** its business event is read, **Then** it names that proposal.
2. **Given** any mutating tool in the catalog executes through a confirmed proposal, **When** its business events are read, **Then** every one of them names that proposal.
3. **Given** a new mutating tool is added to the catalog, **When** the suite runs, **Then** it fails until that tool's events name the proposal, so the allowlist cannot silently drift again.

### User Story 3 - Reopen a settled decision (Priority: P2)

As an operator, I can open the Decisions page after confirming and still find what was decided, by whom and how it ended.

**Why this priority**: It restores already-approved behavior (054, 055) over data that is already stored; it needs no migration of its own, but its MCP attribution depends on story 1.

**Independent Test**: Confirm and reject a few proposals, open the Decisions history, search for one and open its detail.

**Acceptance Scenarios**:

1. **Given** decisions were settled, **When** the history tab of the Decisions page opens, **Then** it shows the register of spec 054 with outcome, requester, decider and moment of decision per row.
2. **Given** a decision was settled through MCP, **When** its row renders, **Then** the decider column names the token and its issuer as in story 1, distinct from a signed-in decider and from an unknown one.
3. **Given** a decision's link is opened from a record or an activity, **When** the page loads, **Then** that decision is shown with its arguments and result, whether it is pending or settled.

### User Story 4 - See the decision on the record and in Activities (Priority: P2)

As an owner looking at an item, party, price list or any other record, I can see which decision created it and who settled that decision, and each entry in Activities says the same for the change it shows.

**Why this priority**: This is where the question is actually asked; but it only becomes truthful once stories 1 and 2 record what it displays.

**Independent Test**: Open a record created through an MCP-confirmed decision and one created through a web-confirmed decision, and read their origin and their activity entries.

**Acceptance Scenarios**:

1. **Given** a record without a source was created through a decision, **When** its origin is displayed, **Then** it names the decision's action, the decider (person, or token and issuer) and the moment, and links to the decision.
2. **Given** an activity entry was caused by a decision, **When** it is shown, **Then** it names the decision's action and decider and links to the decision instead of showing a bare identifier.
3. **Given** a record or activity has no decision, **When** it is displayed, **Then** no decision line is shown and nothing is guessed.
4. **Given** a record was created before this feature through a decision without an attributed decider, **When** its origin is displayed, **Then** it still links to the decision and reads the decider as unknown.

### Edge Cases

- One proposal writes many events and many records (a batch of 12 items); every record links to the same decision.
- A record was created by one decision and changed by later ones; its origin names the creating decision, its activities name each changing one.
- A proposal executes several tools' effects (order create writes a document, lines and commitments).
- The token that confirmed was issued by an owner who has since left the company.
- The same token is used by several clients or agents; Reality attributes to the token, not to a client.
- A decision is read for a company the member does not belong to.
- A proposal fails during execution and is restored to `proposed`; no event names it and no decider remains recorded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Issuing an MCP access token MUST record the owner who issued it; tokens issued before this feature MUST remain usable and MUST record no issuer.
- **FR-002**: Settling a proposal through MCP, by approval or rejection, MUST record which access token settled it, in addition to the moment.
- **FR-003**: A decision settled through MCP MUST NOT record the token's issuer as the deciding person; the person field remains reserved for a signed-in principal (spec 055 FR-002).
- **FR-004**: Wherever a decider is shown, an MCP decision MUST read as confirmed or rejected through the named token, issued by the named owner or by an unknown issuer, and MUST be distinguishable from a signed-in decider and from an unknown decider.
- **FR-005**: Every business event written while a confirmed proposal executes MUST reference that proposal, for every mutating tool in the catalog.
- **FR-006**: The suite MUST prove FR-005 for the whole mutating-tool catalog, failing for any tool, present or future, whose events do not reference the proposal.
- **FR-007**: The Decisions page MUST offer the settled-decision register specified by spec 054 FR-001–FR-010 and spec 055 FR-006–FR-008, extended by FR-004.
- **FR-008**: A single decision MUST be openable by its identifier from the Decisions page, whether pending or settled, showing its arguments, result, requester, outcome and decider.
- **FR-009**: The origin of a record without a source that was created through a decision MUST name the decision's action, its decider per FR-004 and the moment, and MUST link to the decision (extending spec 211 FR-002).
- **FR-010**: An activity entry whose event references a decision MUST name the decision's action and decider and MUST link to the decision, replacing the bare identifier as the primary presentation.
- **FR-011**: A record or activity without a decision MUST show no decision statement, and an unattributed decision MUST read as unknown, never as a guessed person.
- **FR-012**: Every English string added by this feature MUST carry German, Dutch and Spanish translations, using the agreed German ERP vocabulary.

### Domain and Traceability Requirements

- **DR-001**: The link from an event to its decision MUST be the existing `business_event.action_id`; no record or document table gains a decision reference (shortest true link).
- **DR-002**: The token attribution MUST be a nullable reference from the decision to the access token, and the issuer a nullable reference from the token to the user; both additive, reversible and without backfill.
- **DR-003**: Every reader that resolves deciders, tokens or issuers MUST be tenant-scoped and discoverable by the tenant isolation catalog; a token or issuer of another company MUST never be resolved.
- **DR-004**: Web, MCP and CLI MUST read decision attribution through the same service; the browser MUST NOT derive attribution from raw fields.
- **DR-005**: This feature MUST NOT change who may approve, the execution boundary, the delivery review, finance owner checks, or any existing recorded value.

### Key Entities *(when data is involved)*

- **Decision (change proposal)**: gains a nullable reference to the MCP access token that settled it.
- **MCP access token**: gains a nullable reference to the owner who issued it.
- **Decision attribution**: a read model joining a decision to its moment and to exactly one of a signed-in person, a token with its issuer or unknown issuer, or unknown.

## Success Criteria *(mandatory)*

- **SC-001**: Repeating the measured agent run after this feature, 100 % of executed decisions name their token, and 100 % of those confirmed with a newly issued token name its issuer.
- **SC-002**: Repeating the run, 100 % of business events written by its executed proposals reference their proposal, including payment terms and prices (today 0 of 31).
- **SC-003**: From any record created in that run, the deciding decision is reachable in one click, and from the Decisions page any settled decision is found within 10 seconds.
- **SC-004**: No decision, record or activity ever shows an attribution that was not recorded.
- **SC-005**: The migration applies and reverses without data loss and without a backfill step.
- **SC-006**: The localization audit reports zero missing and zero invalid entries; every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Owners issue MCP tokens through the signed-in web settings (`require_company_owner`), so the issuer is known at issue time; tokens created by other paths (CLI, tests) legitimately record no issuer.
- The MCP runtime resolves the access token on every call, so the settling token can be passed to the shared approval service without a new authentication mechanism.
- `proposal_review` already reads a proposal of any status and is the basis for opening a single decision.
- `business_event.action_id` and its composite foreign key to the proposal already exist; FR-005 widens its use, not the schema.
- The history endpoint and name resolution from specs 054/055 still exist in the API and are reused rather than rebuilt.
- The owner decided on 2026-09-24: attribute MCP confirmations to token and issuer (not per-user OAuth, not web-only confirmation), and keep existing tokens usable with an unknown issuer.

## Open Questions

None. The two product decisions above were taken by the owner; the absence of historical attribution is a fact about existing data.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-004 | US1 scenarios 1-5 | Service tests for MCP approve/reject with new, legacy and revoked tokens; web-confirmed control case; attribution read-model test |
| FR-005-FR-006 | US2 scenarios 1-3 | Catalog-wide test executing every mutating tool through a proposal and asserting every written event references it; targeted regression for payment term, price list, price tier, price-list assignment |
| FR-007-FR-008 | US3 scenarios 1-3 | History payload tests with MCP attribution; web contract tests for the register and single-decision view |
| FR-009-FR-011 | US4 scenarios 1-4 | Provenance service tests; Activities and origin rendering contracts; negative control for records without a decision |
| FR-012 | US1-US4 | Localization audit across English, German, Dutch and Spanish |
| DR-001-DR-002 | US1, US2 | Migration upgrade/downgrade test; diff review for no new record-table columns |
| DR-003-DR-005 | US1 scenario 5, US3 | Tenant isolation catalog coverage, cross-tenant token/issuer test, unchanged approval-permission tests |
| SC-001-SC-006 | All scenarios | Re-run of the agent setup against a fresh company, measured with the same queries; full required quality gates |
