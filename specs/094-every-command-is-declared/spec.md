# Feature Specification: An Operation Nobody Declared

**Feature Branch**: `094-every-command-is-declared`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "Spec 091 found five shipped classes unreachable because posting an invoice was in no catalog and on no surface. The tenant isolation catalog is complete by discovery; the command catalog is hand-maintained and nothing checks it. So the same thing can happen again tomorrow."

## Context and Intent

### Problem

Spec 091 fixed a defect and named its cause. Booking an invoice was implemented, tenant-scoped
and proven, and reachable from nothing — because the command catalog, which says what a person
or an agent can do, is written by hand and **nothing checks that it is complete**.

The tenant isolation catalog next to it is complete by discovery: it finds every public service
and fails when one is unmapped. That gate has caught an unregistered operation in four of the
last six specifications. The command catalog has no equivalent, so an operation can be built,
made tenant-safe, wired to a surface, and never declared — or, as in 091, never wired at all and
nobody notices.

Measuring it rather than asserting it: of the 86 services the isolation catalog classifies as
mutations, 68 are reachable from an endpoint, an agent tool or the CLI, and **14 of those are not
declared as commands**. Eight of the fourteen are business operations that simply should be
declared — including releasing a reservation, which has had an agent tool and no catalog entry
for its whole life.

### Scope

- A gate: every mutating service reachable from a surface must be a declared command, or listed
  as not one with a reason.
- Declare the eight that are business operations.
- Record the six that are not, each with the reason it is not.

### Non-Goals

- **Gating reads.** A read reaches people through the capability guidance, which has its own
  completeness rules. Pulling reads in would add fourteen exemptions saying "this is a read" and
  drown the six that carry information.
- **Gating internal building blocks.** `post_ledger`, `emit_business_event` and
  `create_master_source_record` are mutations and are not commands; they are how commands are
  built. The gate asks whether an operation is *reachable*, because reachability is what failed.
- **Deciding what belongs on which surface.** The gate says an operation must be declared, not
  which adapters it should have.
- **Changing any behaviour.** Nothing an operation does changes. Eight of them become visible in
  a catalog they should always have been in.
- **Promoting chat session handling or the import worker to business commands.** They are
  reachable and they are not things an operator asks the business to do. They are recorded as
  exemptions with that reason, which is a claim a reviewer can disagree with in one place.

### Existing Contracts

- [`specs/091-invoices-can-be-booked/spec.md`](../091-invoices-can-be-booked/spec.md)
- [`specs/019-tenant-isolation-catalog/spec.md`](../019-tenant-isolation-catalog/spec.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [Constitution](../../.specify/memory/constitution.md), principle IV

## Clarifications

### Session 2026-09-06

- Q: What is the right population to gate? → A: Mutating **and** reachable. Mutation comes from
  the isolation catalog, which is complete by discovery; reachability comes from the surfaces.
  Composing two facts that are each already gated gives a population of 68 with no new source of
  truth invented.
- Q: Why not gate every mutation? → A: It would pull in the building blocks commands are made of
  — `post_ledger`, `emit_business_event` — and every one would need an exemption saying "this is
  internal". Twenty-eight entries of noise around the ones that matter. The bug in 091 was
  reachability, so the gate is about reachability.
- Q: Why not gate reads too? → A: Reads have their own completeness rules in the capability
  guidance. Fourteen exemptions reading "this is a read" would bury the six that say something.
- Q: What happens to the fourteen the measurement found? → A: Eight are declared, because they
  are business operations and always were. Six are recorded as exemptions with a reason each.
- Q: Is an exemption list not just a way to silence the gate? → A: It is, and that is why each
  entry states why the operation is not a command. A reviewer disagreeing with one has a single
  line to argue with, which is more than exists today.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An Undeclared Operation Fails the Build (Priority: P1)

Somebody wires a new mutating service to a surface without declaring it, and the suite says so.

**Why this priority**: It is the entire feature. Everything else follows from the gate existing.

**Independent Test**: Take a declared command out of the catalog and watch the gate name it.

**Acceptance Scenarios**:

1. **Given** a mutating service reachable from a surface and not declared, **When** the suite
   runs, **Then** it fails, naming the service.
2. **Given** the same service declared as a command, **When** the suite runs, **Then** it passes.
3. **Given** the same service listed as not a command with a reason, **When** the suite runs,
   **Then** it passes.
4. **Given** an exemption for a service that is declared as a command, **When** the suite runs,
   **Then** it fails, because a service cannot be both.
5. **Given** an exemption for a service nobody can reach, **When** the suite runs, **Then** it
   fails, because a stale exemption hides the next real one.

### User Story 2 - The Eight That Should Have Been Declared (Priority: P1)

The operations the gate found are declared, so a person and an agent can see them.

**Acceptance Scenarios**:

1. **Given** the catalog, **When** it is read, **Then** releasing a reservation is a command.
2. **Given** the catalog, **When** it is read, **Then** updating a pricing group is a command.
3. **Given** the catalog, **When** it is read, **Then** each bulk master-data operation is named
   beside the single-record command it belongs to.

### Edge Cases

- An exemption with an empty reason.
- A service both declared and exempt.
- An exemption naming a service that does not exist.
- A mutating service reachable only from the CLI.
- A service that stops being reachable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every service the tenant isolation catalog classifies as a mutation and that is
  reachable from an endpoint, an agent tool or the CLI MUST be declared as a command, as a
  related service of one, or as explicitly not a command.
- **FR-002**: An entry saying an operation is not a command MUST carry a non-empty reason.
- **FR-003**: A service MUST NOT be both declared and recorded as not a command.
- **FR-004**: An entry recorded as not a command MUST name a service that exists and is in the
  gated population, so a stale entry cannot hide the next real one.
- **FR-005**: The gate MUST name the offending services when it fails, not merely count them.
- **FR-006**: Releasing a reservation MUST be a declared command.
- **FR-007**: Updating a pricing group MUST be a declared command.
- **FR-008**: Each bulk master-data operation MUST be declared beside the single-record command
  it belongs to.
- **FR-009**: The gate MUST derive its population from the two existing catalogs and the
  surfaces, and MUST NOT introduce a third list of what exists.
- **FR-010**: Every existing operation, class and surface MUST behave exactly as it does today.

### Domain and Traceability Requirements

- **DR-001**: No schema changes and no service logic changes.
- **DR-002**: The exemptions MUST live in the command catalog, so they are reviewed where
  commands are reviewed rather than hidden in a test.
- **DR-003**: The gate MUST fail on drift in either direction: an undeclared operation and a
  stale exemption.
- **DR-004**: No operational exception class is added or changed.

### Key Entities *(when data is involved)*

- **Command catalog**: What a person or an agent can ask the business to do, and now also what is
  deliberately not that.
- **Tenant isolation catalog**: Already complete by discovery, and the source of what counts as a
  mutation.

## Success Criteria *(mandatory)*

- **SC-001**: A mutating operation cannot be wired to a surface without being declared or
  explained.
- **SC-002**: The eight operations the measurement found are declared.
- **SC-003**: Every operation deliberately not a command says why, in one reviewable place.
- **SC-004**: The gate fails on a stale exemption as well as a missing declaration.
- **SC-005**: Nothing that worked before behaves differently.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The gate is only as complete as the isolation catalog's idea of a mutation, which is itself
  gated by discovery. That is the strongest existing foundation and it is a dependency worth
  naming.
- Reachability is detected from the surface modules. A service reached through an indirection the
  detection cannot see would be missed; the exemption list's staleness check is what limits how
  long such a hole can hide.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 2, 3 | completeness gate test |
| FR-002 | Edge cases | empty reason test |
| FR-003 | US1 scenario 4 | both-at-once test |
| FR-004 | US1 scenario 5; Edge cases | stale exemption test |
| FR-005 | US1 scenario 1 | failure message test |
| FR-006 | US2 scenario 1 | catalog entry |
| FR-007 | US2 scenario 2 | catalog entry |
| FR-008 | US2 scenario 3 | catalog entries |
| FR-009 | — | the gate reads only the two catalogs and the surfaces |
| FR-010 | — | the existing suites, unchanged |
| DR-001 | — | no migration and no service diff |
| DR-002 | US1 scenario 3 | exemptions live in the command catalog |
| DR-003 | US1 scenarios 1, 5 | drift in both directions test |
| DR-004 | — | the closed registry expectation, unchanged |
