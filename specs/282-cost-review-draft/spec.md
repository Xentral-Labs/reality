# Feature Specification: Drafted cost reviews

**Feature Branch**: `282-cost-review-draft`
**Created**: 2026-09-26
**Status**: Draft
**Language**: English
**Input**: "Create the follow-up spec for the cost review draft." It comes from the spec 279 live
walk-through, which found that a clerk cannot get from "not evidenced" to a proven value.

## Context and Intent

### Problem

Spec 279 made every missing cost basis explain itself. It gives an ordered path: confirm each
receipt's cost, prepare the item's cost review, a company owner confirms. For "prepare the
review" it hands a request to chat. The live walk-through on 2026-09-26
(`specs/279-missing-basis-guidance/quickstart.md`) showed that this step cannot be completed.

- **The agent asks for internals.** It needs `owner_party_id`, method, currency, base unit,
  history start, cutoff, the classification of every movement, receipt manifest IDs and
  ownership evidence IDs. After a plain-language answer it still asked for the company
  party's ID and the opening movement's ID, and it offered to create the opening stock again
  although it already existed.
- **Opening cost has no evidence.** An opening stock recorded through the form has no source
  record, but an inventory review must cite evidence for every opening's acquisition cost.
  Even a perfect request could not be accepted.
- **Nothing is proposed, so the owner has nothing to confirm.**

Almost all of those inputs are already held. The demo seed builds the same review from held
records in code (`services/demo_profile.py`). A contribution review is fully determined by
the current contribution preview: its candidate hash, economic date and fixed profile. What
is missing is a shared, read-only service that drafts the review from what Reality holds. It
should name only what a person genuinely has to decide or state.

### Scope

- A shared read, **cost review draft**. For one inventory or contribution scope it returns:
  - the complete arguments for the existing `cost.change` proposal when everything is
    derivable;
  - otherwise the open inputs a person must provide, in business terms;
  - the held records it used, by opaque ID.

  It writes nothing and stores nothing.
- The same draft through Web, MCP and chat. The chat handoff from spec 279 asks the agent to
  use it, so a request in plain language becomes a proposal without anyone typing an ID.
- A web review dialog for the "Prepare the item's cost review" and "Prepare the contribution
  review" steps. It shows the draft in business language, collects only the open inputs,
  and creates the proposal through the existing proposal path. The owner confirms in
  Decisions as today.
- The opening stock form also takes the opening's acquisition cost and an evidence
  reference. It records them as a SourceRecord linked to the movement, so that an opening
  stock can be reviewed at all.

### Non-Goals

- Changing who may propose or confirm a cost change, or skipping owner confirmation.
- Computing any cost a source does not state (Constitution VIII). The draft copies stated
  values and derived identities; it never invents an acquisition cost, a unit cost or a price.
- Drafting receipt cost assignments (matching supplier invoice lines to receipts). That needs
  judgment beyond held links and gets its own spec. The draft reports an incomplete receipt
  as an open input that points to the existing receipt step.
- Batch reviews across several items or lines. The single-scope draft comes first.
- Selling-cost (DB2) reviews. The contribution draft covers DB1; selling categories stay
  unreviewed, as the review allows today.
- A cost policy editor or a company-wide default method. The valuation method is asked in
  each draft.
- A separate "opening cost statement" document. An opening recorded earlier without cost
  gets its cost through the existing movement correction: the opening is replaced by one
  recorded with cost.

### Existing Contracts

- `docs/features/receipt-costing.md`: inventory and contribution reviews, owner
  confirmation, and the guidance steps since spec 279.
- `specs/279-missing-basis-guidance/`: the guidance, the chat handoff and the live findings.
- `docs/WEB_SPEC.md`: guidance for missing basis, the AI and MCP boundary, and the decision
  review (spec 276).
- `docs/features/chat.md`: chat preview and confirmation.
- Constitution I (evidence chain), IV (shared services, no ORM writes from agents) and VIII
  (received values are recorded, never recomputed).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The contribution review is drafted from the preview (Priority: P1)

A clerk opens an invoice line whose DB1 is "not evidenced" and whose item cost is confirmed.
The next step is "Prepare the contribution review". The clerk chooses it and sees a summary:
- invoice line, customer and item;
- received net revenue as the invoice states it;
- the shipment and its confirmed goods cost;
- the resulting DB1, marked as a proposal until confirmed.

Nothing needs to be typed. The clerk submits, and a proposal waits for the owner.

**Why this priority**: The draft is fully derivable here, and invoice lines are where people
first meet "not evidenced". It proves the draft end to end with the smallest scope.

**Independent Test**: For a line whose preview is a candidate, request the draft. It returns
complete arguments that the existing proposal validation accepts unchanged, and no open
inputs.

**Acceptance Scenarios**:

1. **Given** a line whose contribution preview is a candidate, **When** the draft is
   requested, **Then** it returns complete `contribution_review` arguments: the candidate
   hash, the economic date and the current event sequence. It has no open inputs, and
   `preview_cost_change` accepts the arguments.
2. **Given** that draft, **When** the clerk submits it from the web dialog, **Then** a
   `tool:cost.change` proposal is created through the existing path. The guidance then shows
   the owner step linked to it.
3. **Given** a line whose preview is unavailable (for example, the item's cost is not
   confirmed), **When** the draft is requested, **Then** it returns no arguments and one
   open input that points to the upstream step.
4. **Given** that inputs change between drafting and submitting, **When** the clerk
   submits, **Then** the existing stale-preview check refuses it. The dialog re-drafts and
   says why instead of failing silently.

---

### User Story 2 - The inventory review is drafted from held movements (Priority: P1)

An item has receipts whose cost is confirmed. The clerk chooses "Prepare the item's cost
review" and sees the draft:
- owner: the company;
- valuation method;
- currency and unit;
- history from the first movement;
- every movement classified (receipts, shipments, returns, losses);
- the receipt cost manifests it will use.

The only question is the valuation method. FIFO is preselected; specific selection is offered
only for items tracked by serial or lot. The clerk confirms the draft, and the owner confirms
the proposal.

**Why this priority**: It is the step the walk-through could not complete, and it blocks both
stock value and DB1.

**Independent Test**: For an item whose receipts carry complete cost, request the draft. The
existing inventory check (`_check`) accepts the returned arguments once the open inputs are
filled.

**Acceptance Scenarios**:

1. **Given** an item whose receipts all carry complete cost, **When** the draft is
   requested, **Then** it derives the following from held records:
   - the owner party (the company party);
   - currency and base unit;
   - history start and cutoff;
   - the classification of every owned movement;
   - receipts with their current manifest and ownership evidence.

   The inventory check accepts these arguments.
2. **Given** a company without a party in the role "company", **When** the draft is
   requested, **Then** it lists that as an open input with a link to master data. It never
   guesses an owner.
3. **Given** a receipt whose cost is incomplete, **When** the draft is requested, **Then**
   it returns no arguments. The open input names that receipt and points to the receipt
   cost step.
4. **Given** a movement the draft cannot classify (for example, an adjustment of unknown
   meaning), **When** the draft is requested, **Then** it lists the movement as an open
   input for the person to classify. It never picks a class.

---

### User Story 3 - Opening stock can carry evidenced cost (Priority: P1)

A company starts with opening stock. When recording it, the clerk enters the acquisition cost
and what it is based on, for example "closing inventory list 2025-12-31". Reality records
that statement as a source, links it to the opening movement, and the draft uses it.

**Why this priority**: Without it no opening stock can ever be reviewed, which is the typical
state of a new company.

**Independent Test**: Record opening stock with cost and evidence through the form's
service, then request the draft. The opening appears with `evidence_source_record_id` and the
stated acquisition cost, and the inventory check accepts it.

**Acceptance Scenarios**:

1. **Given** an opening stock without cost evidence, **When** the draft is requested,
   **Then** the open input says the opening's acquisition cost and its evidence are
   missing. It never proposes a value.
2. **Given** an opening recorded through the form with acquisition cost and an evidence
   reference, **When** the draft is requested, **Then** the opening carries the created
   evidence record and the stated amount unchanged.
3. **Given** an opening recorded earlier without cost, **When** the clerk corrects it with
   the existing movement correction to a replacement opening with cost, **Then** the draft
   uses the replacement and ignores the corrected original.
4. **Given** the opening form without a cost, **When** it is submitted, **Then** it still
   records the opening as today. Cost stays optional, and the draft lists it as an open
   input.

---

### User Story 4 - Chat turns a plain request into a proposal (Priority: P2)

A clerk writes "Prepare the cost review for Desk Lamp". The agent reads the draft. It asks
only the open inputs, in business words, then proposes. The clerk never sees an ID or a
field name.

**Why this priority**: It completes the spec 279 chat handoff. The web dialog (US1 and US2)
already gives a deterministic path, so chat follows it.

**Independent Test**: An agent-facing test drives the chat tool sequence for a derivable
item. The proposal is created with arguments equal to the draft.

**Acceptance Scenarios**:

1. **Given** a derivable contribution scope, **When** the chat agent handles the prepared
   request, **Then** it calls the draft, proposes exactly the drafted arguments, and asks no
   question. For a derivable inventory scope, it asks only for the valuation method, unless
   the person already named it (FR-011).
2. **Given** a scope with one open input, **When** the agent handles the request, **Then**
   it asks one business-language question for that input, and nothing else.
3. **Given** the capability guidance for `cost_change_propose`, **When** the agent prepares
   a review, **Then** the guidance directs it to the draft first.

### Edge Cases

- **Stale draft**: a draft is tied to an event sequence. Submitting an outdated draft is
  refused by the existing check, and the dialog re-drafts.
- **Bounds**: more than 20 receipts or 100 movements exceed the review bounds. The draft says
  the item cannot be reviewed in one step, and it does not truncate silently.
- **Consignment and multiple owners**: ownership parts are drafted only from held ownership
  evidence. Where ownership is ambiguous, the draft lists an open input.
- **Returns and settlements**: customer returns need exact original issue portions. When the
  held links do not determine them, the draft lists an open input.
- **Tenant boundary**: every lookup is tenant-scoped. Cross-company scope or evidence IDs
  behave as not found.
- **Practice and demo companies**: the draft is readable, but submitting follows the
  existing policy. Spec 279 already says that cost decisions cannot be confirmed there.
- **Concurrency**: two clerks submitting the same draft produce at most one proposal that
  can be executed; the existing bound proposal and stale checks decide.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a read-only cost review draft for one inventory scope
  (item) or one contribution scope (invoice line). It returns either complete `cost.change`
  arguments or a list of open inputs, plus the held records it used.
- **FR-002**: A contribution draft MUST take the candidate hash, the economic date and the
  event sequence from the current contribution preview, and the fixed profile
  `commercial_v1`. It MUST NOT alter any value the preview reports.
- **FR-003**: An inventory draft MUST derive the owner party, currency, base unit, history
  start, cutoff and movement classification, and each receipt's current manifest and
  ownership evidence, only from held records.
- **FR-004**: The draft MUST NOT invent a value a source does not state. Missing acquisition
  cost, ambiguous ownership, unclassifiable movements, an absent company party and an
  undecided valuation method MUST become open inputs with a business-language label, a
  stable code and the step or page that resolves them.
- **FR-005**: Arguments returned as complete MUST pass the existing proposal validation
  (`preview_cost_change`) unchanged at the draft's event sequence.
- **FR-006**: The web MUST offer a review dialog from the guidance steps "Prepare the item's
  cost review" and "Prepare the contribution review". It shows the draft in business
  language, collects only the open inputs, and creates the proposal through the existing
  proposal path. It MUST NOT show opaque IDs or field names outside a collapsed technical
  section.
- **FR-007**: A stale draft MUST be refused by the existing checks. The dialog MUST re-draft
  and explain the change.
- **FR-008**: The opening stock form and its shared service MUST accept an optional
  acquisition cost with a required evidence reference when a cost is given. The service
  records them as a SourceRecord linked to the opening movement, and the inventory draft uses
  the amount unchanged. Openings without cost MUST keep working as today.
- **FR-011**: The inventory draft MUST ask for the valuation method in every draft: FIFO
  preselected, specific selection offered only for serial- or lot-tracked items. No
  company-wide default is stored.
- **FR-009**: The draft MUST be available through MCP and chat as a read tool. The capability
  guidance for `cost_change_propose` and the spec 279 chat prompts MUST direct the agent to
  it first.
- **FR-010**: The draft MUST respect the inventory review bounds and report when a scope
  exceeds them.

### Domain and Traceability Requirements

- **DR-001**: The draft is a read-time derivation. It MUST NOT be stored, and it MUST NOT
  create or change Facts, reviews, proposals or source records (Constitution VIII).
- **DR-002**: Every drafted argument MUST reference existing records by opaque ID and the
  shortest true link: movement, manifest, ownership evidence, candidate hash.
- **DR-003**: The draft MUST be one shared service called by Web, MCP and chat. No adapter
  may assemble review arguments on its own (Constitution IV).
- **DR-004**: Every lookup MUST be tenant-scoped, and cross-company references MUST behave
  as not found.
- **DR-005**: Opening cost evidence MUST enter through the Source → Evidence chain: a
  SourceRecord that states the amount as received, linked to the opening movement by the
  shortest true relationship. It MUST NOT be a typed field on the movement.

### Key Entities

- **Cost review draft**: a derived, unstored description of the review the held records
  support for one scope. It holds complete arguments or open inputs, and the records used.
- **Open input**: one thing a person must decide or state before the review can be proposed,
  with its business label and the path that resolves it.
- **Opening cost evidence**: a source statement of an opening stock's acquisition cost, which
  the inventory review cites.

## Success Criteria *(mandatory)*

- **SC-001**: Re-running the spec 279 walk-through
  (`apps/web/scripts/missing-basis-walkthrough-live.mjs`) in a business company reaches a
  proven acquisition value and DB1. No one types an ID, a field name or a tool name.
- **SC-002**: For a derivable contribution scope, the chat path creates the proposal without
  asking the person anything. For a derivable inventory scope, it asks only for the
  valuation method, and for any other scope one question per open input.
- **SC-003**: Every drafted "complete" argument set in the demo profile's reviewed scopes
  equals, or is accepted in place of, the arguments the demo seed builds today.
- **SC-004**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Proposing a cost change requires an active member, and confirming requires an active owner
  (verified in spec 279).
- The company's own party is the party with role `company` (`services/core.py` party roles).
  A company may have none; that is an open input, not an error.
- The demo seed's argument assembly in `services/demo_profile.py` is the reference for what
  held records can determine; the draft service replaces none of it in this feature.
- The receipt cost step (assign and review) keeps its current tools. Drafting it is a
  separate spec.

## Open Questions

None. Decided by the owner on 2026-09-26:

- Opening cost evidence is entered in the opening stock form (option a). Openings recorded
  earlier without cost use the existing movement correction.
- The draft asks for the valuation method every time (FIFO preselected). There is no
  company-wide default.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 1, US2 1 | draft service tests for both kinds |
| FR-002 | US1 1 | contribution draft equals preview values |
| FR-003 | US2 1 | inventory draft accepted by `_check` |
| FR-004 | US1 3, US2 2–4, US3 1 | open-input tests per cause |
| FR-005 | US1 1, US2 1 | draft arguments pass `preview_cost_change` |
| FR-006 | US1 2 | browser test of the review dialog |
| FR-007 | US1 4 | stale draft refused and re-drafted |
| FR-008 | US3 1–4 | opening form service with cost and evidence; without cost unchanged |
| FR-009 | US4 1–3 | MCP parity and agent tool-sequence test |
| FR-010 | Edge case bounds | bound test |
| FR-011 | US2 | method input: FIFO preselected, specific only when tracked |
| DR-001 | all | no-write assertion |
| DR-002 | US2 1 | references by opaque ID |
| DR-003 | US4 | Web, MCP and chat call the same service |
| DR-004 | US3 3 | cross-tenant not-found tests |
| DR-005 | US3 2 | evidence stored as SourceRecord linked to the movement |
| SC-003 | — | draft versus demo seed comparison test |
