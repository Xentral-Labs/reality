# Feature Specification: The Link Nothing Enforced

**Feature Branch**: `100-the-link-nothing-enforced`
**Created**: 2026-09-07
**Status**: Draft
**Language**: English
**Input**: "Absence is load bearing in three classes. Each rests on the contract that every billing, crediting or settling record sets its link, and nothing enforces it."

## Context and Intent

### Problem

Four references on the queue's own records are **nullable, meaningful, and unenforced**:

| Reference | What it says |
|---|---|
| `DocumentLine.billed_document_line_id` | which order line this invoice or credit line bills |
| `Movement.resolves_movement_id` | which return this movement settles |
| `Movement.return_announcement_id` | which announced return these goods fulfil |
| `Commitment.document_line_id` | which order line this promise came from |

Each was added by a specification that needed it (076, 082, 099, and the order baseline). Each is
optional, because in each case a record legitimately exists without it — a manual invoice with no
order behind it, a transfer that settles no return, a promise not raised from an order line.

**Sixteen of thirty-two classes read one of them**, and eleven *conclude* from one — the rest only
name it in the evidence they report. Across the four references that is twenty-five
reference-and-class pairs, and a missing reference does not make one thing go wrong. It makes two
opposite things go wrong:

**Six pairs cry wolf.** The class concludes *from absence*, so a missing reference reports work
that was actually done — `shipped_not_billed`, `receipt_unbilled`, `returned_not_credited` and
`supplier_return_not_credited` when the billing link is missing, `return_unresolved` and
`announced_return_not_arrived` when theirs is. The cost is a queue that stops being believed.

**Thirteen pairs go blind.** The class *starts* from the reference, so a missing one means it never
looks at that record at all. Ten distinct classes are in this direction, and it is the dangerous
one: `billed_not_received` going quiet means a company pays for goods that never arrived and
nothing notices.

**The remaining six pairs only trace.** A class that puts a reference in its evidence is unharmed
when it is absent, and no discovery can tell that apart from a conclusion — so the direction has
to be declared by a person and argued.

Four classes are in *both* failure directions at once. `shipped_not_billed` cries wolf when an
invoice line does not say what it bills, and goes blind when the promise does not say which order
line it came from. The same class, two references, two opposite failures.

And nothing in the repository says any of this. There is no list of which references the queue
leans on, no test that a new writing path sets them, and no test that a surface a person or an
agent actually uses can even carry them.

### Two things already broken

Written before the gate, so the gate has something real to prove:

- **The MCP schema does not advertise `billed_document_line_id`.** `document_create_propose`
  declares `lines` as a free-form object array, so the field passes through if sent — and an agent
  reads a schema to know what exists. A field a schema does not name will never be set by an
  agent, which means every invoice an agent records makes four classes cry wolf and five go blind.
- **The web app cannot send it either.** `ManualLine` has no such field, so a person recording a
  manual invoice in the Cockpit cannot say what it bills. The API model accepts it, the service
  validates it, nine classes read it, and the only human surface for manual invoices has no box
  for it. Same shape of gap as Spec 091: the operation existed and nothing reached it.

### Scope

- Write down which references the queue leans on, what depends on them, and which way each fails.
- Gate that the list is complete by discovery, so a new nullable reference cannot be added without
  saying what it is.
- Gate that every path that writes one of those records passes the reference through.
- Gate that every surface declared for such a command can carry it.
- Fix what the gate finds.

### Non-Goals

- **Making the references required.** Each is optional because a record legitimately exists
  without it. A manual invoice for a service, a transfer that settles nothing, a promise raised by
  hand — requiring the link would refuse honest records to protect a derivation.
- **Reporting a record whose link is missing.** A class for "an invoice line that names no order
  line" was considered and refused: most such lines are correct, so it would be a wall of entries
  nobody can clear, and Spec 088 already settled that a condition nobody can end is a report
  rather than an exception.
- **Guessing the link.** Matching an invoice line to an order line by item and amount is exactly
  the guess Spec 099 refused for announcements, and it would be worse here: a wrong link makes a
  class confidently wrong rather than blind.
- **Changing any class.** Every derivation behaves exactly as it does today. This specification
  writes down and gates what the classes already depend on, and gives the surfaces the ability to
  satisfy it.
- **Auditing existing tenant data.** A tool that finds invoice lines with no reference in a live
  tenant is a useful thing and a different one. Nothing here reads a real tenant.

### Existing Contracts

- [`specs/094-every-command-is-declared/spec.md`](../094-every-command-is-declared/spec.md) — the
  gate shape this follows: two facts composed, one complete by discovery
- [`specs/076-invoice-order-link/spec.md`](../076-invoice-order-link/spec.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [Constitution](../../.specify/memory/constitution.md), principles II, V and VIII

## Clarifications

### Session 2026-09-07

- Q: Which references count? → A: Every **nullable foreign key** on the four records the queue
  reasons about — document line, movement, commitment, return announcement — discovered from the
  mapper rather than listed by hand. Each must then be declared either load-bearing or trace-only
  with a reason. A hand-picked list is exactly what this gate exists to replace.
- Q: Why not simply make the references required? → A: Because each record legitimately exists
  without one. Requiring the link would refuse an honest manual invoice to protect a derivation,
  which is the wrong way round.
- Q: Then what does the gate actually prevent? → A: Three things. A new nullable reference added
  without saying what it is. A new writing path that drops a reference the queue leans on. And a
  surface that cannot carry one — which is how the field ends up unset in practice.
- Q: Is a passthrough adapter good enough? → A: For a person, yes; for an agent, no. An agent
  knows only what a schema names, so a field absent from the schema will never be sent. A
  passthrough may be declared exempt for a human adapter and never for MCP.
- Q: Should a missing link be reported? → A: No. Most lines with no link are correct, so the class
  would be a wall nobody can clear — and Spec 088 already refused a class on that ground.
- Q: Should the gate prove the failure directions, or just declare them? → A: Prove them. A
  declared direction nobody has watched fail is a comment. One recording per direction per
  reference, deleting the link and reading the queue.
- Q: What about a real tenant's existing data? → A: Out of scope and named as such. This gate is
  about paths, not rows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Map (Priority: P1)

A reviewer can read which references the queue leans on, which classes depend on each, and which
way each class fails without it — and the build fails if that list stops matching the code.

**Why this priority**: The other two halves are hand-picked lists without it.

**Independent Test**: Add a nullable reference to one of the four records and run the gate.

**Acceptance Scenarios**:

1. **Given** the four records, **When** the gate runs, **Then** every nullable foreign key on them
   is declared either load-bearing or trace-only, and an undeclared one fails the build.
   *(Load-bearing at the reference level; a class that merely traces a load-bearing reference is
   declared as tracing it, because no discovery can tell a conclusion from a mention.)*
2. **Given** a declaration for a reference that no longer exists, **When** the gate runs, **Then**
   it fails, because a stale entry hides the next real one.
3. **Given** each load-bearing reference, **When** the gate runs, **Then** the classes declared to
   depend on it are exactly those whose derivations read it.
4. **Given** each declared dependency, **When** the gate runs, **Then** it names one of the two
   directions, and a recording proves that direction is what actually happens.

### User Story 2 - The Writers (Priority: P1)

**Acceptance Scenarios**:

1. **Given** every place in the source that constructs one of the four records, **When** the gate
   runs, **Then** each either passes every load-bearing reference for that record or is declared
   exempt with a stated reason.
2. **Given** an exemption for a construction that no longer exists, **When** the gate runs,
   **Then** it fails.
3. **Given** a new path that builds an invoice line without the reference, **When** the gate runs,
   **Then** it names that path.

### User Story 3 - The Surfaces (Priority: P1)

**Acceptance Scenarios**:

1. **Given** every command whose service constructs one of the four records, **When** the gate
   runs, **Then** each adapter it declares can carry the load-bearing references, or is exempt
   with a reason.
2. **Given** the MCP schema, **When** the gate runs, **Then** it must name the reference, because
   an agent knows only what a schema names — a passthrough is never enough there.
3. **Given** a person recording a manual invoice in the web app, **When** they record a line,
   **Then** they can say which order line it bills.

### Edge Cases

- A reference declared load-bearing that no derivation reads.
- A class that starts reading a reference without the declaration being updated.
- An exemption with an empty reason.
- A construction site both declared exempt and passing the reference.
- A record type gaining a nullable reference in a migration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every nullable foreign key on `DocumentLine`, `Movement`, `Commitment` and
  `ReturnAnnouncement` MUST be declared either load-bearing or trace-only, and the set of
  references MUST be discovered from the mapper rather than listed.
- **FR-002**: Every trace-only declaration MUST state a reason, and every reason MUST be non-empty.
- **FR-003**: Every load-bearing reference MUST declare the operational exception classes that
  depend on it, and that list MUST equal the classes whose derivations read it.
- **FR-004**: Every declared dependency MUST name one of three readings — reporting work that was
  done, never looking at the record, or only naming the reference in its evidence — and each of the
  two failing readings MUST have a recording that proves it.
- **FR-005**: Every place in the source that constructs one of the four records MUST pass every
  load-bearing reference for that record, or be declared exempt with a stated reason.
- **FR-006**: Every adapter declared by a command whose service constructs one of those records
  MUST be able to carry the load-bearing references, or be declared exempt with a stated reason.
- **FR-007**: An MCP schema MUST NOT be exempted on the ground that it passes arguments through,
  because an agent can only send what a schema names.
- **FR-008**: The gate MUST fail in both directions: an undeclared reference, class, construction
  or adapter, and a declaration or exemption that no longer matches anything.
- **FR-009**: The MCP schema for recording a manual document MUST name the billed-line reference.
- **FR-010**: A person recording a manual document line in the web app MUST be able to state which
  order line it bills, both when recording and when correcting.
- **FR-011**: No operational exception class, derivation, register or projection may change
  behaviour.

### Domain and Traceability Requirements

- **DR-001**: No migration. Every reference and record this concerns already exists.
- **DR-002**: The reference declaration MUST live in configuration, beside the catalogs it
  describes, and MUST be validated when it is loaded rather than only by a test.
- **DR-003**: The discovered facts MUST come from the mapper and the source, never from a list
  maintained beside them.
- **DR-004**: No operational exception class or cause is added, and the closed registry stays
  closed.
- **DR-005**: Nothing may guess or generate a reference; a missing one stays missing.
- **DR-006**: Every read and derivation added MUST be tenant-scoped where it touches tenant data.

### Key Entities *(when data is involved)*

- **DocumentLine**, **Movement**, **Commitment**, **ReturnAnnouncement**: unchanged. The four
  records the operational exception queue reasons about, and the only ones whose nullable
  references this gate governs.

## Success Criteria *(mandatory)*

- **SC-001**: Which references the queue leans on is written down, and the build fails when the
  writing stops being true.
- **SC-002**: A new path that drops one of those references cannot reach the default branch.
- **SC-003**: A surface a person or an agent uses can always set them.
- **SC-004**: Both failure directions are recorded, so a reader knows which classes cry wolf and
  which go blind.
- **SC-005**: Nothing about any existing class changes.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The references stay optional. This gate protects the paths, not the rows.
- Existing tenant data is out of scope; a live tenant may hold records with no reference and
  nothing here reports them.
- The gate is about what the code can do, not about what somebody remembered to type. A person
  who leaves the box empty still leaves it empty — the gate only guarantees there is a box.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | reference catalog completeness test |
| FR-002 | Edge cases | empty reason refused test |
| FR-003 | US1 scenario 3 | declared consumers equal discovered consumers test |
| FR-004 | US1 scenario 4 | one recording per direction |
| FR-005 | US2 scenarios 1, 3 | construction site gate test |
| FR-006 | US3 scenario 1 | adapter gate test |
| FR-007 | US3 scenario 2 | MCP exemption refused test |
| FR-008 | US1 scenario 2; US2 scenario 2; Edge cases | both-directions test |
| FR-009 | US3 scenario 2 | the adapter gate, satisfied |
| FR-010 | US3 scenario 3 | the web app's line shape |
| FR-011 | — | the existing suites, unchanged |
| DR-001 | — | no migration added |
| DR-002 | US1 scenario 1 | the loader's own validation test |
| DR-003 | US1 scenarios 1, 3 | the gate reads the mapper and the source |
| DR-004 | — | the closed registry test |
| DR-005 | — | no matching or generation is added |
| DR-006 | — | the existing isolation suites |
