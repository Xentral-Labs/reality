# Implementation Plan: An Operation Nobody Declared

**Branch**: `094-every-command-is-declared` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One gate composed from two catalogs that are already gated, eight declarations it immediately
finds, and six exemptions that each say why.

No schema, no service change, no behaviour change. The catalog gains what it should always have
had and a reason it cannot fall behind again.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: PyYAML, the two existing catalogs
**Storage**: none; this is a build-time gate
**Testing**: pytest, in the catalog test family beside the isolation gate it mirrors
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: No third list of what exists; the gate must fail in both directions
**Scale/Scope**: One test, eight catalog entries, six exemptions

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Nothing about business records changes; this governs the vocabulary that describes operations | PASS |
| Reality owns operational state | No state, no derivation, no runtime effect | PASS |
| Proven schema only | No schema change | PASS |
| Tenant + shared service boundaries | The gate reads the isolation catalog as its source of what mutates, so the two vocabularies stay consistent by construction | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Unchanged; the eight new declarations make existing operations describable where they were not | PASS |
| Received values not recomputed | Nothing is computed from business data | PASS |
| Smallest coherent design | Three alternatives rejected below, each with the count it would have produced | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

Each was measured rather than guessed, which is the reason the chosen one is defensible:

- **Gate every mutation in the isolation catalog.** 28 undeclared, and most are the building
  blocks commands are made of — `post_ledger`, `emit_business_event`,
  `create_master_source_record`. Every one would need an exemption reading "this is internal",
  and the six entries that say something would be lost among them.
- **Gate every service any surface calls.** Adds fourteen reads whose exemptions would all read
  "this is a read", when reads already have completeness rules of their own in the capability
  guidance.
- **Gate only what an HTTP endpoint calls.** 17 undeclared and it misses the agent tools, which
  is where the most interesting omission lives: releasing a reservation has had a tool and no
  catalog entry for its whole life.

## Repository Structure and Layer Changes

```text
packages/reality-core/tests/test_application_catalog.py   # the gate, beside the isolation one
packages/reality-core/config/command_catalog.yaml         # eight declarations, six exemptions
docs/features/operational_fields.md                        # what the catalog now guarantees
apps/docs/content/catalogs/ (+ de/)                        # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                               # specification row
```

## Design

### The population is two gated facts, intersected

Mutation comes from the tenant isolation catalog, which is complete by discovery and fails when a
service is unmapped. Reachability comes from reading the three surface modules. Neither is a new
source of truth, which is what keeps this gate from becoming another hand-maintained list that
falls behind — the exact failure it exists to prevent.

```
86 services classified as mutations
68 of them reachable from an endpoint, an agent tool or the CLI
14 of those undeclared  →  8 declared here, 6 recorded as not commands
```

### What the eight are

Two are plainly commands that were never written down:

- **Releasing a reservation.** It has had the `reservation_release` agent tool since reservations
  existed and has never been in the catalog. An agent could do it; the catalog said the product
  could not.
- **Updating a pricing group.** Creating one is a command. Updating one was not.

Six are bulk forms of commands that already exist — `create_items`, `create_parties`,
`create_locations` and their update counterparts. They belong as related services of the
single-record commands, which is what `related_services` is for and how `update_payment_term`
already sits beside `create_payment_term`.

### What the six are not

Five are chat session handling and one is the import worker step. They mutate and they are
reachable, and neither is a thing an operator asks the business to do. That is a claim rather
than a fact, so each is written as one line a reviewer can disagree with — which is more than the
zero lines it has today.

### The gate fails in both directions

An undeclared operation fails it. So does an exemption naming a service that is not in the
population — because a stale exemption is how a list like this rots: the operation it named stops
being reachable, the entry stays, and the next operation with that name inherits a silence
nobody chose.

### Data and migration impact

None.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `test_application_catalog.py::test_every_reachable_mutation_is_declared_or_explained` | fourteen undeclared |
| FR-002 | unit | `test_application_catalog.py::test_the_command_gate_fails_in_both_directions` | an empty reason passes |
| FR-003 | unit | `test_the_command_gate_fails_in_both_directions` | a service is both |
| FR-004 | unit | `test_the_command_gate_fails_in_both_directions` | a stale exemption passes |
| FR-005 | unit | `test_every_reachable_mutation_is_declared_or_explained` | the failure names no service |
| FR-006 | unit | `test_application_catalog.py::test_the_eight_operations_the_gate_found_are_declared` | not a command |
| FR-007 | unit | `test_the_eight_operations_the_gate_found_are_declared` | not a command |
| FR-008 | unit | `test_the_eight_operations_the_gate_found_are_declared` | not related services |
| FR-009 | review | the gate imports the two catalogs and reads the surface modules, and defines no list of its own | — |
| FR-010 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | no diff under `services/` and none under `migrations/versions/` | — |
| DR-002 | unit | `test_every_reachable_mutation_is_declared_or_explained` reads them from the catalog | exemptions live in a test |
| DR-003 | unit | `test_the_command_gate_fails_in_both_directions` | drift passes one way |
| DR-004 | unit | `test_coverage.py` closed registry test | passes unchanged |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

A test and a catalog. Nothing runs differently. Rollback is a plain revert.

The eight declarations change what the generated catalog reference says the product can do, which
is the point: it could always do these things and did not say so.

## Review Risks

- **An exemption list can become a way to silence the gate.** It is the obvious failure mode and
  there are two defences: each entry must say why, and a stale entry fails the build. Neither
  stops somebody writing "not a command" and moving on, and nothing can. What it does is make
  that a visible line in a reviewed file rather than an absence nobody sees.
- **Reachability is detected by reading the surface modules.** A service reached through an
  indirection that detection cannot follow would be missed. The staleness check limits how long
  such a hole survives, but a reviewer should know the gate is textual rather than semantic.
- **Six of the fourteen are judgement calls.** Chat session handling and the import worker are
  mutations somebody can invoke. Calling them not-commands is defensible and it is a call; it is
  in one file, one line each, precisely so it can be argued with.
- **The gate depends on the isolation catalog's classification.** If something is misclassified
  there it is invisible here. That catalog is discovery-gated, which is the strongest foundation
  available, and it is still a dependency rather than a guarantee.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
