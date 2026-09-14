# Feature Specification: Storyline Mode

**Feature Branch**: `182-storyline-mode`
**Created**: 2026-09-12
**Status**: Approved (scope and schema, owner, 2026-09-12); implementation in progress
**Language**: English
**Input**: Owner request (German, 2026-09-12): a dedicated playground for the core where people
are invited to test and play like in an adventure game. Create an order, look at it, decide
what happens next: a payment comes in, but the customer paid too much; goods arrive; the
shipment is blocked, something is missing; reorder; the month closes and an invoice is still
unpaid, so it has to be dunned. Whatever story is told, the person must always be able to
follow, slowly and step by step, which tools, actions and views were called and what changed
in the data model. One screen: on the right the calls that were made, below that what was
added to the Fact timeline, so the concept can always be explained alongside.

## Context and Intent

### Problem

Reality explains itself well once a reader knows where to look: the Timeline, the Context
Graph, the Facts register and the Inspector all exist. What is missing is the guided path that
makes a newcomer look at the right place at the right moment. The Learning Playground (spec 096)
had a step engine and lessons, but its browser surface was retired with spec 143 and it never
showed the calls behind a step or the delta a step produced. The guided demo script in
`docs/DEMO_SPEC.md` is a CLI walk and the Agent Playbooks are prose. None of them lets a person
act, watch the system react, and read the mechanism at the same time.

### Scope

- A **Storyline** destination in the unified app that walks a person through a business story
  in chapters, each chapter being a situation, one suggested command, an inspectable result and
  an explanation in Reality's primitives.
- A **three-zone screen**: the narrator on the left, the ordinary app view in the middle, a
  protocol on the right that lists the calls of the current chapter and the delta they produced
  in events, Facts, records, exceptions and the Context Graph.
- A **storyline package**: one declarative file per storyline, validated against the existing
  catalogs, carrying the seed, the chapter texts in every UI language, the suggested command and
  its inputs, the view to open, the expected exceptions and the branches a chapter may offer.
  The same file is the exchange format: it can be downloaded, sent to someone else and imported.
- A **storyline library** per account that lists the built-in storylines and the imported ones,
  with export of any storyline and import of a file someone sent.
- **Recording**: a played run, including free play, can be exported as a storyline draft, so a
  new story is written by playing it, not by hand.
- A **call trace per run** that records read tools and views as well as proposals and
  confirmations, so the protocol can show reads, not only mutations.
- A **delta read** that returns everything recorded after a sequence marker: events, Facts,
  records, raised and cleared exceptions and new Context Graph edges.
- One shipped storyline, **Order to close**, with fourteen chapters on its default path:
  create an order, note the customer reference as a Fact, receive a short delivery, reserve,
  attempt a dispatch that the customer hold refuses, explain the hold (read), record an
  overpayment, release the hold, ship, bill the shipped order, allocate the credit, check the
  stock (read), reorder, and a month-end review (read). Three chapters offer branches whose
  alternatives are four further chapters (look at the balance, refund the credit, keep the
  credit, reorder 20). Dunning and period close are follow-up features (specs 183 and 184)
  that replace the two read chapters in version 2.
- A **presentation mode** that plays the storyline without clicks, and **free play** that lets
  the person leave the script while the protocol keeps recording.

### Non-Goals

- No movable clock, no time travel and no global date change (spec 096 non-goals). Chapters
  that need the past, such as an overdue invoice, get it from a backdated seed; every chapter
  itself happens today. Records that cannot be backdated through their command (a customer
  hold) are seeded as of today.
- No dunning notice and no period close in this feature: neither has a command or a record
  today. They are specified separately (specs 183 and 184) and enter the storyline as version 2.
- No new business rules, no second command path and no browser-side derivation: every chapter
  runs the same proposal, confirmation and read tools the app, the CLI and MCP use.
- No stored delta, no stored explanation and no stored graph: the protocol is a read over the
  event sequence, the Facts, the exceptions and the record links (Constitution VIII).
- No reinstatement of the retired `/playground` browser URLs (spec 143); they stay retired.
- No visual storyline editor. The package file is the authoring surface; built-in storylines
  are repository content reviewed like the catalogs, imported ones live in the account's library.
- No executable content in packages: a storyline names catalog commands and declarative inputs,
  never code, queries or URLs the system would call. An imported file cannot do anything the
  importing person could not do by hand through proposals.
- No public marketplace or hosted gallery in this feature; exchange is a file. The docs list the
  built-in storylines for download.
- No anonymous access: Storyline runs in a practice company owned by the signed-in person, under
  the admission and quota rules of specs 104 and 146.
- No production companies: Storyline is refused for companies that are not practice or demo
  companies.

### Existing Contracts

- [Learning Playground](../096-learning-playground/spec.md), [free operations](../103-playground-free-operations/spec.md),
  [practice companies](../104-playground-practice-companies/spec.md), [companion](../106-playground-companion/spec.md):
  the run and step engine and its quota rules, whose services remain available after spec 143.
- [Retire legacy surfaces](../143-retire-legacy-surfaces/spec.md): the Playground browser surface is gone and stays gone.
- [Company setup and demo](../146-company-setup-demo/spec.md), [demo order to cash](../168-demo-order-to-cash/spec.md):
  practice companies, the canonical demo profile and the synthetic payment variants.
- [Sandbox read parity](../155-sandbox-read-parity/spec.md), [sandbox chat parity](../169-sandbox-chat-parity/spec.md):
  practice companies get the normal reads and the normal Copilot.
- [Reality Inspector](../138-reality-inspector/spec.md), [timeline recorder raster](../162-timeline-recorder-raster/spec.md),
  [Context Graph naming](../163-context-graph-naming/spec.md), [live activity signal](../061-live-activity-signal/spec.md):
  the surfaces and the sequence cursor the protocol builds on.
- The docs Tool Usage section (`apps/docs/.vitepress/data/tool-usage.json`, generated by `apps/docs/scripts/generate-catalog-reference.py`): the bilingual tool
  explanations and the `order_to_cash` process skeleton.
- [Shared language](../176-shared-language/spec.md): language resolution across app, site and docs.
- `docs/DEMO_SPEC.md`, `docs/features/learning-playground.md`, `docs/WEB_SPEC.md`.
- Clickable mockup of the screen, reviewed by the owner on 2026-09-12:
  an internal design artifact (link withheld).

## Screen

```
┌──────────────────────────────┬──────────────────────────────┐
│ Narrator        chapter 7/14 │ Calls in this chapter        │
│ "Two days later Nordlicht    │ view     /finance/open-items │
│  pays 1,300.00 € against     │ read     finance.settlement… │
│  RE-0389 (1,180.00 €)."      │ propose  finance.settlement… │
│ [Record payment] [Free play] │ confirm  finance.settlement… │
├──────────────────────────────┼──────────────────────────────┤
│                              │ What was added   #4831…#4835 │
│  ordinary app view:          │ events   +5                  │
│  Open items, new row lit     │ facts    +4                  │
│                              │ records  +2                  │
│                              │ exceptions ▲1 ✓2  (rule)     │
│                              │ Context Graph, new edges     │
└──────────────────────────────┴──────────────────────────────┘
```

The middle zone is the ordinary app. The narrator only navigates it; it never renders a copy.

## Storyline package

The contract in [contracts/storyline-package.md](contracts/storyline-package.md) is normative;
the example below is illustrative and abbreviated. A storyline is one file, `<key>.storyline.yaml` (JSON accepted on import), with a format version.
Everything in it is declarative. Identity inside the file is symbolic: parties, items and
locations are named in the seed and referenced as `$ref.<group>.<name>`; records a chapter
creates are referenced by the chapter that made them, such as `$chapter.order.output.order_id`.
Human-readable numbers and database ids never appear (Constitution II). Dates are relative to
the run start, such as `-42d` for the backdated invoice, so the same file plays on any day.

```yaml
storyline: 1                      # format version
key: order-to-close
version: 3
title: { en: Order to close, de: Auftrag bis Abschluss }
summary: { en: …, de: … }
author: { name: Reality team }    # free text, optional
seed:
  parties:   { nordlicht: { role: customer, name: Nordlicht Handels GmbH }, baltic: { role: supplier, name: Baltic Supply } }
  items:     { fjord: { sku: IT-FJORD, name: Fjord Thermo-Becher, price: "24.50" } }
  locations: { hamburg: { name: Hamburg } }
  history:                        # ordinary commands, played before chapter 1
    - command: movement_create
      at: -60d
      input: { movement_type: opening_stock, item_id: $ref.items.fjord, to_location_id: $ref.locations.hamburg, quantity: "8", occurred_at: -60d }
    - command: document_create
      at: -56d
      input: { document_type: sales_invoice, number: RE-0389, party_id: $ref.parties.nordlicht, gross_amount: "1180.00", document_date: -56d, payment_term_code: $ref.terms.net14, lines: […] }
      as: overdue_invoice
chapters:
  - key: order
    title: { en: Create the order, de: Auftrag anlegen }
    situation: { en: …, de: … }
    view: view:orders
    command: order_create
    input: { direction: sales, number: AT-0041, company_party_id: $company.party, counterparty_id: $ref.parties.nordlicht, location_id: $ref.locations.hamburg, gross_amount: "294.00", lines: […] }
    primary: { record_type: commitment, from: output.commitment_ids[0] }
    expect: { raised: [outgoing_commitment_at_risk], cleared: [] }
    explain: { en: …, de: … }
    next: reference
  - key: dispatch
    …
    branches:
      - { key: explain, label: { en: Understand the hold first, de: Erst die Sperre verstehen }, next: explain-hold, default: true }
      - { key: call, label: { en: Look at the customer's balance, de: Den Saldo des Kunden ansehen }, next: call-customer }
```

The package contract is a Pydantic model with a size bound, like the demo profile manifest.
Validation resolves every command, view, exception class and Fact predicate against the
catalogs and every `$ref` and `$chapter` against the file itself. A JSON Schema of the format
is published with the docs so a file can be written in any editor with completion.

## User Scenarios & Testing

### User Story 1 - Play one chapter and see what it did (Priority: P1)

A signed-in person opens Storyline, gets a practice company with the storyline's seed, reads the
first situation, previews the suggested command with its prefilled inputs, confirms it and sees,
without leaving the screen, the app view with the new row, the calls the chapter made and the
events, Facts, records and exceptions the chapter added.

**Why this priority**: This is the loop everything else repeats. One chapter with a truthful
protocol already teaches the model; without it the mode is a slideshow.

**Independent Test**: Start the shipped storyline, confirm chapter 1 and compare the protocol
with the tenant's timeline, Facts register and exceptions page: every listed item exists there
and nothing that was recorded is missing from the protocol.

**Acceptance Scenarios**:

1. **Given** a verified account without a running storyline, **When** the person opens
   Storyline and confirms the start, **Then** a practice company with the storyline's seed is
   created or the person's paused run is resumed, and no production company is touched.
2. **Given** chapter 1 is open, **When** the person chooses the suggested command, **Then** a
   preview of the prefilled proposal is shown and nothing has been recorded yet; the protocol
   lists the view read and the proposal as pending.
3. **Given** the preview is shown, **When** the person confirms, **Then** the command runs
   through the ordinary proposal confirmation, the middle zone shows the view named by the
   chapter with the new or changed rows marked, and the protocol lists the confirmation and the
   reads that followed it with their inputs and results.
4. **Given** the chapter has run, **When** the person reads the delta, **Then** it lists every
   business event recorded after the chapter's sequence marker with its sequence number, every
   Fact recorded after the marker as subject, predicate and value, every new record, every
   exception raised or cleared with the rule that decided it, and the record links added around
   the chapter's primary record.
5. **Given** the chapter has run, **When** the person rejects instead of confirming, **Then**
   the proposal is rejected through the ordinary path, the delta stays empty and the chapter can
   be tried again.
6. **Given** any call in the protocol, **When** the person expands it, **Then** the entry from
   the tool catalog is shown in the UI language: label, what the tool does, its parameters, its
   access class and the projections it writes to, with a link to the Tool Usage page.

---

### User Story 2 - Follow the whole story and understand the connections (Priority: P1)

The person plays the chapters of Order to close in order. Chapters build on each other: the
customer hold that refuses the shipment comes from the invoice that is explained next and
overpaid after that; the credit the overpayment leaves is what the billing chapter's branches
decide about, and the month-end review lists what a period close would carry into October.

**Why this priority**: The owner's request is a story, not a list of features. The connections
are what makes exceptions, rules and the Context Graph understandable.

**Independent Test**: Play all chapters in one run; the reserve chapter clears the finding the
order raised, the overpayment chapter clears the overdue receivable and raises the unmatched
financial event, the billing chapter clears the finding the shipment raised, and the month-end
review lists exactly the findings that remain.

**Acceptance Scenarios**:

1. **Given** chapter 2 has run, **When** its delta is read, **Then** the exception raised in
   chapter 1 is listed as cleared with the rule that cleared it, without any command that
   addressed it.
2. **Given** the dispatch chapter runs, **When** the person chooses the suggested command,
   **Then** the preparation is refused with the customer hold as the reason, the protocol lists
   the refused call, the delta stays empty, and the blockers view names the hold.
3. **Given** the overpayment chapter has run, **When** its delta is read, **Then** the payment
   is applied to the invoice, the unapplied rest is visible as available credit on the payment,
   the overdue receivable is listed as cleared and the unmatched financial event is listed as
   raised; the hold stays until its own chapter releases it.
4. **Given** the month-end review chapter has run, **When** its result is read, **Then** it
   lists every still open finding with its class and what clears it, and nothing was written.
5. **Given** any chapter has run, **When** the person opens a listed record, Fact or exception,
   **Then** the ordinary Inspector, Facts register or Exceptions page opens on that item.
6. **Given** the person reloads the page or returns days later, **When** Storyline opens,
   **Then** the run resumes at the first chapter that has not run, with the protocols of earlier
   chapters readable again from the recorded trace and sequence markers.

---

### User Story 3 - Choose a branch (Priority: P2)

At the end of a chapter that offers branches, the person picks one of two or three next moves
and the story continues with the chapter that branch names.

**Why this priority**: Branches turn a tutorial into play and let one storyline cover the
payment and delivery variants spec 168 already produces; the linear path works without them.

**Independent Test**: Run the billing chapter, choose "Refund the 120.00 €" instead of the
default; the next chapter proposes a refund and the delta shows the credit used up.

**Acceptance Scenarios**:

1. **Given** a chapter with branches has run, **When** the person chooses one, **Then** the choice
   is recorded on the run and the next chapter is the one the branch names.
2. **Given** a chapter with branches has run, **When** the person chooses nothing and continues,
   **Then** the default branch is taken.
3. **Given** a branch was taken, **When** the person reopens an earlier chapter, **Then** its
   protocol is shown read-only and the run is not replayed or forked.

---

### User Story 4 - Leave the script and come back (Priority: P2)

The person leaves the rails, works in the ordinary app or asks the Copilot, and the protocol
keeps recording. "Back to the story" returns to the current chapter.

**Why this priority**: The owner wants people to test and play, not only to follow. Free play is
what makes the practice company theirs.

**Independent Test**: In free play, create a second order through the ordinary order form; the
protocol lists the call and the delta lists its events although no chapter proposed it.

**Acceptance Scenarios**:

1. **Given** free play is on, **When** the person runs any confirmed command in the app or
   through the Copilot of the practice company, **Then** the protocol lists the call and the
   delta lists what it recorded, in the same form as for a chapter.
2. **Given** free play changed the company, **When** the person returns to the story, **Then**
   the current chapter still runs; if its preconditions no longer hold, the chapter says which
   Fact is missing and offers the restart of the run instead of failing on confirm.
3. **Given** the person restarts the run, **When** the restart is confirmed, **Then** a fresh
   practice company with the seed is created under the existing quota rules and the old one is
   kept, as spec 104 defines.

---

### User Story 5 - Present the story without clicking (Priority: P3)

A presenter switches on presentation mode; chapters preview, confirm and advance on a timer,
the protocol fills as it would by hand, and the presenter can pause and take over at any time.

**Why this priority**: The owner will show the concept to others; a mode that plays itself is
cheap once the loop exists.

**Independent Test**: Switch on presentation mode on a fresh run and wait; every chapter of the
default path runs and the final state equals a run played by hand.

**Acceptance Scenarios**:

1. **Given** presentation mode is on, **When** a chapter finishes, **Then** the next chapter
   starts after a readable pause and the same calls and deltas are recorded as by hand.
2. **Given** presentation mode is on, **When** the presenter interacts, **Then** the mode pauses
   at the current phase and can be resumed.
3. **Given** presentation mode reaches a chapter with branches, **When** no choice is made,
   **Then** the default branch is taken.

### User Story 6 - Offer, share and import storylines (Priority: P2)

A person opens the storyline library, sees the built-in storylines and their own imported ones,
downloads any of them as a file, and imports a file a colleague sent. The imported storyline is
validated, listed with its title, author, version and chapter count, and can be started like a
built-in one.

**Why this priority**: The owner wants to offer more stories quickly and let others send theirs.
One built-in story proves the mode; the library is what makes it grow without a release.

**Independent Test**: Export Order to close, change a chapter text and the key, import the file
and start it; the run plays the changed chapter.

**Acceptance Scenarios**:

1. **Given** the library is open, **When** the person downloads a storyline, **Then** a single
   file in the package format is delivered that validates unchanged on import.
2. **Given** a valid file from someone else, **When** it is imported, **Then** it appears in the
   person's library with title, author, version and chapter count, and only for that account.
3. **Given** a file that names a command, view, exception class or predicate the catalogs do not
   know, or a `$ref` the file does not define, **When** it is imported, **Then** the import is
   refused with the list of unknown names and nothing is stored.
4. **Given** a file with the same key and version as an existing library entry, **When** it is
   imported, **Then** the person is asked whether to replace it; runs of the old version keep
   their recorded chapters.
5. **Given** an imported storyline names a command the person may not confirm, **When** the
   chapter is reached, **Then** the ordinary authorization refuses the confirmation and the
   chapter says so; the import itself only warns.

---

### User Story 7 - Record a storyline by playing it (Priority: P3)

A person plays freely in a practice company, then exports the run as a storyline draft. The
draft carries the commands and inputs that were confirmed, in order, with identities rewritten to
symbolic references and dates rewritten relative to the run start, and empty text fields ready
to be written.

**Why this priority**: Writing chapters by hand is slow; playing them is how the owner already
thinks about stories. It depends on the trace and the package format and comes last.

**Independent Test**: Play three confirmed commands in free play, export the draft, fill in the
texts, import it and play it; the same three commands are proposed in order.

**Acceptance Scenarios**:

1. **Given** a run with confirmed commands, **When** it is exported as a draft, **Then** the draft
   validates against the package contract except for the texts marked as missing.
2. **Given** a command referred to a seed party, item or location, **When** the draft is
   exported, **Then** the reference is `$ref.<group>.<name>`, not an id or a number.
3. **Given** a command referred to a record an earlier command created, **When** the draft is
   exported, **Then** the reference is `$chapter.<key>.output.<field>`.
4. **Given** a confirmed command cannot be expressed in the package format, **When** the draft is
   exported, **Then** the draft names the command as unsupported at that position instead of
   dropping it silently.

### Edge Cases

- The storyline's seed cannot be created (quota, capacity): the start is refused with the reason
  the Playground services give today, nothing half-created remains.
- A confirmation fails inside the command: the protocol lists the call with its error, the delta
  stays at the marker and the chapter can be retried; the run is not advanced.
- Two browser tabs on the same run: the second tab sees the run state of the first after reload;
  a chapter cannot run twice because the step is owned by the run (spec 096 idempotency).
- A storyline file names a command, view, exception class or predicate the catalogs do not
  know: the storyline fails validation at build time and is not shipped.
- The delta read is asked for a marker older than the timeline retention: it reports the range
  it can serve and marks the rest as unavailable instead of silently truncating.
- The person's language changes mid-run: chapter texts and tool explanations switch, the
  recorded trace does not change.
- A practice company that is not a storyline company opens Storyline: the person is offered a
  new storyline run, the existing company is not converted.
- An imported file is larger than the package bound or is not YAML or JSON: refused before
  parsing the content, with the bound named.
- A built-in storyline is updated in a release while a person has a run of the old version:
  the run keeps playing the version it started with; the library offers the new one.
- An imported storyline's seed history fails on a command halfway: the start is rolled back as
  one unit, the person sees which seed command failed and why, no half-seeded company remains.

## Requirements

### Functional Requirements

- **FR-001**: The unified app MUST offer a Storyline destination that starts or resumes a
  storyline run in a practice company owned by the signed-in person, under the admission and
  quota rules of specs 104 and 146, and MUST refuse production companies.
- **FR-002**: A storyline MUST be one declarative package file with a format version, a key, a
  version, titles and summaries, a seed (named parties, items, locations, payment terms and a
  history of ordinary commands with relative dates) and an ordered set of chapters, each with
  texts, either one suggested command with prefilled inputs or a list of reads, optional context
  reads whose results feed the inputs, the view to open, the primary record, the findings
  expected to be raised or cleared, optional preconditions and either a next chapter or
  branches that name the next chapter. English is required for every text; built-in packages
  carry all four UI languages (FR-015). `command` names the proposal tool. Identities inside
  the file MUST be symbolic references (seed, company, seed result, earlier chapter, context,
  composed finding id), never ids or human-readable numbers; a chapter reference MUST name a
  chapter that lies on every path to the referencing chapter. A package MUST be validated
  against the command, view, exception and Fact catalogs, against each command's input schema
  and against its own references; built-in packages MUST fail the build and imported packages
  MUST be refused when a reference is unknown.
- **FR-003**: Each chapter MUST run through the ordinary proposal preview, confirmation and
  rejection services; Storyline MUST NOT execute a command by another path and MUST NOT
  derive anything in the browser.
- **FR-004**: Every run MUST record a call trace: each read tool call, proposal, confirmation
  and rejection made in the run's company with tool name, access class, input, result or
  error, duration, actor and the chapter it belongs to when one is active, and each view a
  person opens with its route, parameters and status. The trace MUST be tenant-scoped,
  bounded per entry and per run, inert for every other company and never used as a business
  record.
- **FR-005**: Every chapter MUST record a sequence marker before its first mutating call. The
  tenant API MUST offer a delta read that returns, for a marker, the business events recorded
  after it with their sequence numbers, the Facts recorded after it as subject, predicate and
  value, the records created after it, the exceptions raised or cleared after it with the rule
  that decided them, and the record links added around a named record. The delta MUST be
  derived at read time and MUST NOT be stored.
- **FR-006**: The Storyline screen MUST show three zones: the narrator with chapter list,
  situation, suggested command, preview, result explanation and branches; the ordinary app view
  the chapter names, with rows created or changed since the marker marked; and the protocol
  with the calls of the current chapter and the delta. On narrow viewports the zones MUST
  stack; the page MUST NOT scroll horizontally.
- **FR-007**: Every call in the protocol MUST expand to the tool catalog entry: the label in
  the UI language where the resource catalog records one and in English otherwise (spec 178
  rule), the catalog description, parameters, access class, the projections it writes to and
  a link to the corresponding Tool Usage page.
- **FR-008**: Every item in the delta MUST open its ordinary surface: records in the Inspector,
  Facts in the Facts register, exceptions on the Exceptions page, the graph excerpt in the
  Context Graph.
- **FR-009**: A run MUST resume where it stopped after reload or re-login, and the protocols of
  chapters that have run MUST be readable again from the trace and the markers.
- **FR-010**: A chapter with branches MUST record the chosen branch on the run and continue with
  the chapter the branch names; without a choice the default branch applies. Earlier chapters
  MUST be readable but MUST NOT be replayed or forked.
- **FR-011**: Free play MUST keep recording calls and deltas for any confirmed command in the
  run's company, including commands proposed through the Copilot, and MUST let the person
  return to the current chapter. A chapter whose preconditions no longer hold (a reference that
  no longer resolves, a finding the chapter requires present or absent) MUST say which record
  or finding is missing and offer a restart instead of failing on confirm.
- **FR-012**: A restart MUST create a fresh practice company with the seed under the existing
  quota rules and keep the previous company, as spec 104 defines.
- **FR-013**: Presentation mode MUST advance chapters on a timer through the same services,
  MUST pause on any interaction and MUST take the default branch.
- **FR-014**: The shipped storyline Order to close MUST contain the fourteen default-path
  chapters and four branch alternatives named in the scope, with a backdated seed that provides
  opening stock, an overdue posted invoice under a 14-day term, a customer delivery hold and an
  overdue purchase order, and MUST offer branches after the refused dispatch, the billing and
  the stock check. At least one chapter MUST record a Fact. Chapters whose preparation is
  refused by the system (the dispatch under a hold) MUST be presented as an outcome, not as an
  error of the storyline, and MUST keep their step with the refused call in the trace. Read
  chapters MUST use live reads. Expected findings are shown as expected against observed and
  never block a run. The seed MUST be part of the package and versioned with it (decision
  2026-09-12, replaces the profile reference).
- **FR-015**: All texts of the Storyline screen and of the shipped storyline MUST exist in all
  four UI languages and MUST use the ERP vocabulary the resource catalog records; the term
  Context Graph is invariant (spec 163).
- **FR-016**: The Storyline destination MUST be reachable from the home entry of practice and
  demo companies and from the docs Tool Usage process page for order to cash; retired
  `/playground` URLs MUST keep explaining their retirement (spec 143).
- **FR-017**: Built-in storylines MUST live as package files in the repository, MUST be covered
  by a contract test that validates them against the catalogs, and MUST be listed in the docs
  with a download of the file.
- **FR-018**: Every account MUST have a storyline library that lists built-in and imported
  storylines with title, author, version, chapter count and origin, MUST export any of them as
  the package file, and MUST import a package file into that account only. Imports MUST be
  bounded in size, MUST be validated before anything is stored, and MUST report every unknown
  reference at once.
- **FR-019**: An imported storyline MUST run under exactly the rules a built-in one runs under:
  the same proposal path, the same authorization, the same quotas. A package MUST NOT carry code,
  queries, URLs or anything the system would execute or fetch.
- **FR-020**: A storyline run MUST remember the key and version it started with and MUST keep
  playing that version when the library receives a newer one.
- **FR-021**: A run MUST be exportable as a storyline draft: confirmed commands in order with
  their inputs, seed identities rewritten to `$ref` references, records created in the run
  rewritten to `$chapter` references, dates rewritten relative to the run start, text fields
  marked as missing, and commands the format cannot express named as unsupported in place.

### Key Entities

- **Storyline package**: one declarative file with format version, key, version, titles, author,
  seed and chapters. Built-in packages are repository files; imported packages are stored per
  account as received, with the validation result and origin.
- **Seed**: named parties, items and locations plus a history of ordinary commands with
  relative dates that the run plays before chapter 1; replaces a movable clock.
- **Chapter**: a package element with texts per language, suggested command and inputs, view,
  primary record, expected exceptions, branches. Not a database entity of its own.
- **Storyline library**: the per-account list of built-in and imported packages.
- **Storyline run**: the person's progress through a storyline in one practice company: the
  package key and version it started with, current chapter, chosen branches, one step per run
  chapter. Extends
  the existing Playground run and step records rather than adding a second run model.
- **Sequence marker**: the last business event sequence of the run's company before a chapter's
  first mutating call, stored on the chapter's step.
- **Call trace entry**: one recorded call in a run: tool, access class, input, result or error,
  duration, actor, chapter, recorded at. Bounded per run, tenant-scoped, not a business record.
- **Delta**: the read-time answer for a marker: events, Facts, records, raised and cleared
  exceptions, graph edges. Never stored.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A person who has never seen Reality can play chapter 1 to its explanation in under
  three minutes without leaving the screen or reading documentation.
- **SC-002**: For every chapter of the shipped storyline, every event, Fact, record and
  exception the protocol lists exists on the ordinary surfaces of the practice company, and the
  business-story test finds nothing recorded in the chapter that the protocol omits.
- **SC-003**: The default path played by hand and in presentation mode ends in the same
  company state: same events by type and count, same Facts, same open exceptions; the browser
  check proves the timed run issued the same ordered prepare, confirm and branch calls.
- **SC-004**: A storyline that references an unknown command, view, exception class or
  predicate fails the catalog contract test before it reaches a branch build.
- **SC-005**: The screen renders without horizontal page overflow at 390px and 1440px and
  without page errors in the browser check, in all four languages.
- **SC-006**: The delta read for one chapter of the shipped storyline answers within the same
  bound the Inspector reads meet after spec 179.
- **SC-007**: A built-in storyline exported, imported under another key and played ends in the
  same company state as the built-in one.
- **SC-008**: A package with one unknown command, one unknown view and one undefined `$ref` is
  refused with all three names in one answer, and no library entry exists afterwards.
- **SC-009**: A draft exported from a three-command free-play run needs only its texts filled in
  to import and play.

## Assumptions and Dependencies

- The Playground run and step services survive spec 143 unchanged and can carry a storyline
  key, a chapter key, a sequence marker and a chosen branch without a second run model.
- Business events carry the proposal that caused them, so proposals and confirmations can be
  attributed to a chapter from the sequence alone; reads need the new trace because nothing
  records them today.
- Facts can be ordered by recording, not only by business time, so a delta over Facts is
  possible; if the current model orders Facts by observation time only, the plan adds the
  recording order rather than a stored delta.
- The backdated seed removes the need for a clock: an invoice due six weeks ago is seeded
  and every chapter acts on it today; the hold cannot be backdated and is seeded as of today.
- The tool explanations come from the same catalog source the docs generator reads, so the
  protocol and the Tool Usage pages cannot drift apart.
- Branch alternatives are ordinary commands and reads of the catalog; no new business
  behaviour is needed for them.
- Copilot commands in a practice company already run through proposals (spec 169), so free
  play through chat needs no new write path.
- The command catalog's input schemas are expressive enough to describe every chapter input
  declaratively; where a command needs an id the seed cannot name symbolically, the format
  grows a reference kind rather than allowing raw ids.
- Imported packages are stored per account, not per company, because practice companies are
  personal (spec 104) and a storyline outlives the company it was last played in.

## Requirement Traceability

Filled as implementation lands; rows without evidence are still open (see tasks.md).

| Requirement | Evidence |
| --- | --- |
| FR-002, FR-017, FR-019, SC-004, SC-008 | `reality.storyline.package` (contract, four validation passes, built-ins, JSON Schema), `reality.storyline.references`; `packages/reality-core/tests/test_storyline_package.py`; built-in `packages/reality-core/storylines/order-to-close.storyline.yaml` |
| FR-004 | `reality.storyline.recorder` (scope, bounds, ring, wrappers in `tools/application.py`, view middleware in `web/app.py`); `packages/reality-core/tests/test_storyline_trace.py` |
| FR-005 (primitives) | `fact.recorded_at`, step markers and trace table in `db/core.py` and `migrations/versions/0058_storyline.py`; forward `after_sequence` in `services/core.py:timeline_activity`; `packages/reality-core/tests/test_storyline_delta.py`; `packages/reality-core/tests/test_migrations.py` (storyline migration test) |
| FR-007 (labels) | `catalogs.load_catalog_labels`; test in `packages/reality-core/tests/test_storyline_package.py` |
| FR-014 | `packages/reality-core/storylines/order-to-close.storyline.yaml`; built-in validation in `test_storyline_package.py`; scenario test pending (T027) |
| FR-001, FR-003, FR-005 (delta read), FR-009, FR-010, FR-012 | `services/storyline.py` (start, seed, derived state, prepare, confirm, reject, branches, restart), `storyline/delta.py`; `packages/reality-core/tests/test_storyline_runs.py` |
| FR-001, FR-003, FR-004, FR-005, FR-007, FR-018 (HTTP) | `web/storyline_api.py`; `packages/reality-core/tests/test_storyline_library_api.py` |
| FR-006, FR-007, FR-008, FR-015 (web) | `apps/web/src/unified/StorylinePage.tsx`, `StorylineNarrator.tsx`, `StorylineStage.tsx`, `StorylineProtocol.tsx`, `storylineState.ts`, `routing.ts`, `Shell.tsx`; `apps/web/scripts/storyline-contract.test.mjs`; `apps/web/scripts/storyline-browser.mjs` (library start, prepare and confirm through the storyline route, protocol, delta, stage marks, docs link, record link, 16 localized layouts without overflow) |
| FR-009, FR-010, FR-014, SC-002 (story) | `packages/reality-core/tests/scenarios/test_storyline_order_to_close.py` (default path, two alternative paths, refused dispatch, read chapters, completeness of the deltas); second built-in `storylines/purchase-to-pay.storyline.yaml` with `tests/scenarios/test_storyline_purchase_to_pay.py` (default path and credit branch, research R9); resume test in `tests/test_storyline_runs.py`; browser section 5b in `apps/web/scripts/storyline-browser.mjs` (reload resumes, earlier chapter read-only, finding opens the Exceptions page) |
| FR-016, FR-017, FR-018, FR-019, FR-020, SC-007, SC-008 | `services/storyline.py` (`export_package`, `import_package`, `delete_package`), account routes in `web/storyline_api.py`; `tests/test_storyline_library_api.py` (round trip, refusal with every error, bounds, replace, built-in protection, warning for commands the person may not confirm); `tests/scenarios/test_storyline_order_to_close.py` (exported, re-imported and replayed package ends in the same state); docs generator writes `content/storylines/index.md` (EN, DE), `content/public/storylines/*.storyline.yaml` and `storyline.schema.json`, the process page links the storyline, sidebar and CI stale-output guard extended; web library with download, import and removal (`StorylinePage.tsx`), home button, browser section 1 |
| FR-011, FR-012 (free play, preconditions, restart) | `services/storyline.py` (`prepare` refuses a chapter whose precondition no longer holds and names it, `trace(free=True)`, `delta(ordinal=…)`), `storyline/recorder.py`; `tests/test_storyline_runs.py` (free play recorded with its own marker and delta, blocked chapter names the missing finding, restart); web free play mode, "Free play" and "Back to the story", missing list with restart in `StorylinePage.tsx`, `StorylineNarrator.tsx`, `StorylineProtocol.tsx`; browser sections 7 and 8 in `apps/web/scripts/storyline-browser.mjs` |
| FR-013, SC-003 (presentation) | `storylineState.ts` (`nextPresentationAction`, beats, pace), autoplay control in the step card (`StorylineNarrator.tsx`) and runner in `StorylinePage.tsx`; `apps/web/scripts/storyline-contract.test.mjs`; browser section 9 (timed run issues the same ordered chapter calls as by hand, any click pauses, language switch while paused changes texts and not the trace, an error pauses) |
| FR-021, SC-009 (draft export) | `storyline/export.py`, `services/storyline.py:export_draft`, `GET /api/storyline/runs/{run_id}/draft`; `packages/reality-core/tests/test_storyline_export.py` (refs, chapter references, offsets, missing texts, unsupported in place, the filled draft imports and plays to the same events, HTTP); "Export as storyline draft" in the library, browser section 10 |
