# Implementation Plan: The Hold Nobody Lifted

**Branch**: `107-a-hold-nobody-lifted` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two operational exception classes over records the queue has never looked at, sharing one
derivation body and two learned populations. No schema, no new operation, no change to anything
that exists.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML
**Storage**: PostgreSQL; **no migration**
**Testing**: pytest, the derivation and coverage suites
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Nothing released, nothing suppressed, nothing stored; strict tenant scope
**Scale/Scope**: Two classes, one shared body, two thresholds, no new operation

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A hold is Reality the product already owns; nothing about the layers changes | PASS |
| Reality owns operational state | Both entries are derived per read from the hold's own timestamps. Nothing is stored and no hold is released | PASS |
| Proven schema only | No migration. Both records already carry when they were raised, why, by whom, and when they were released | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the learned rule is shared and each population is a tenant's own | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry names the reason somebody gave, who gave it, how long it has stood, and what it is holding back | PASS |
| Received values not recomputed | Reason, note and author are reported exactly as recorded. The only derived figures are a duration and a count | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### The reachability check, done first

Spec 091 found five shipped classes that could never fire on a real tenant, because the operation
that would clear them was reachable from nothing. So before designing anything here: **can a
person lift these holds?**

`release_commitment_hold` and `release_party_delivery_hold` are both declared, both as related
services of their hold commands, on **CLI, Web, API, MCP and Chat**. The clearing path is real from
every surface. That check is the whole reason this class is safe to add, and it is recorded rather
than assumed.

### Simpler alternatives considered

- **Release a hold after a while.** The obvious "fix" and the wrong one twice over: a hold is a
  person's statement that they are dealing with something, and releasing it would remove the
  protection that makes holds worth having. Reality would also be deciding something nobody asked
  it to — the same argument Spec 097 used for reserved stock.
- **One class over both records.** A class carries one `record_type`, and these are two records.
  Two ids sharing one parameterised body is what the return classes and the open-item classes
  already do here, so the shape is established rather than invented.
- **Split by reason code.** A credit check and an address clarification take different times, so
  six thresholds would be more precise in principle. Nobody has measured any of them, and Spec 080
  learns from a population rather than a configured number precisely to avoid inventing figures.
  One rhythm per hold kind is what the evidence supports.
- **Report holds on closed promises too.** They are unreleased, so they qualify on paper. They hold
  nothing back, so nobody can clear them by doing anything useful, and Spec 088 already refused a
  class on that ground. Cancelling a promise not releasing its holds is the real oddity, and it is
  named as a limit rather than fixed in a specification about reporting.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py         # one body, two derivations
packages/reality-core/src/reality/catalogs.py                    # two class ids in the order
packages/reality-core/config/operational_exception_catalog.yaml  # their guidance
packages/reality-core/tests/operational_exceptions/test_derivation.py
docs/features/operational_exceptions.md, commitment_holds.md, party_delivery_holds.md
apps/docs/content/catalogs/ (+ de/), docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### Why a forgotten hold is worse than untidy

`close_stale_promises` is the only operation that closes many promises at once, and `_stale_promises`
skips anything with an active commitment hold or whose party has an active delivery hold. That
protection is right — a sweep must not close something out from under the person dealing with it —
and it has **no expiry**. A hold raised for a check somebody finished a year ago goes on shielding
its promise from the only sweep that could close it.

A customer delivery hold does more than shield. While it stands, `record_movement` refuses every
shipment to that customer, including orders taken after the hold was raised by people who never
knew about it. That is why the two classes differ in severity: one blocks a promise, the other
blocks a customer.

### One body, two classes, two histories

`_unreleased_hold_exceptions` takes the record, the class id, the title and the way to describe
what is held back. `commitment_hold_unreleased` and `party_hold_unreleased` are its two callers,
which is the shape `_return_exceptions` and `_open_item_exceptions` already have here.

Two learned populations, not one. A promise hold and a customer delivery hold are different
processes with different people behind them, and Spec 089's first draft would have let one posting
rhythm judge another before that was caught. **Share the rule, never the history** — and never
another tenant's history either.

The floor is a week, matching `STALLED_ORDER_FLOOR`. A hold is an active statement that somebody is
on it, so a few days is ordinary and a week is the shortest span in which "forgotten" means
anything.

### What the entry says a hold is holding back

This is the figure that makes the class useful rather than decorative: a hold on nothing is a
formality somebody forgot, and a hold on a real backlog is money standing still.

- **A promise hold** reports the quantity still open on the promise it holds, in that promise's own
  unit.
- **A party hold** reports the **count** of open customer deliveries to that party. Not a summed
  quantity — quantities across different items do not add up, which Spec 076 settled, and a count
  is the honest figure available. A hold blocking nothing is still reported, because it will refuse
  the next order too.

### Every hold type, named

Only `delivery` party holds exist; Spec 098 considered a payment hold and did not build one. The
class reports **every** unreleased party hold and names its type, rather than filtering to the one
type that exists today — because filtering is how a rule stays correct until a second case arrives
and then quietly stops being. Spec 099 measured seventeen branches with that shape.

The consequence is stated in the specification rather than left to be discovered: a future hold
type will be reported by this class, so it must arrive with its own release path.

### Data and migration impact

None. Both records already carry `created_at`, `released_at`, `reason_code`, `note` and
`created_by`. Nothing is written.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_commitment_hold_unreleased` and `::test_party_hold_unreleased` | no entry |
| FR-002 | story | `test_derivation.py::test_a_hold_is_judged_by_this_company_s_own_rhythm` | a configured number appears |
| FR-003 | story | `test_a_hold_is_judged_by_this_company_s_own_rhythm` | an entry inside a week |
| FR-004 | story | `test_commitment_hold_unreleased` | the entry omits what is held |
| FR-005 | story | `test_party_hold_unreleased` | a summed quantity appears |
| FR-006 | story | `test_commitment_hold_unreleased` | a closed promise is reported |
| FR-007 | story | `test_party_hold_unreleased` | the type is absent |
| FR-008 | unit | the catalog and its guidance | severities equal |
| FR-009 | story | both derivation tests | the entry survives release |
| FR-010 | story | `test_derivation.py::test_a_hold_suppresses_nothing` | a class went quiet |
| FR-011 | story | every existing suite, unchanged | an existing behaviour moved |
| DR-001 | review | no migration, no command added | — |
| DR-002 | unit | `test_coverage.py` closed registry test | catalog drift |
| DR-003 | story | `test_derivation.py::test_each_hold_kind_learns_its_own_rhythm` | one history judges both |
| DR-004 | story | `test_commitment_hold_unreleased` | something was stored |
| DR-005 | story | `test_derivation.py::test_holds_are_tenant_scoped` | another tenant is reachable |
| DR-006 | review | the reachability check above | — |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no behaviour change. On deploy, a tenant with fewer than five lifted holds of a
kind is not judged for that kind at all, so the classes are silent until a company has a rhythm.
Rollback removes two catalog entries and one derivation body.

The demo month holds nothing and its pinned queue is unchanged.

## Review Risks

- **The threshold is a fifth unmeasured constant.** Two more classes now depend on the Spec 080
  helper, whose numbers have never been checked against a real business. That is the largest
  standing risk in this queue and this specification adds to it rather than reducing it. The
  argument for doing it anyway is that a learned rhythm is still better evidence than a configured
  number, and the alternative here is no visibility at all.
- **Holds on cancelled promises stay where they are.** They are not reported and not cleaned up, so
  a tenant accumulates them quietly. Releasing them on cancel is the right fix and it is a
  behaviour change to a shipped operation, which is a different specification.
- **A count is a weak figure for a party hold.** "Blocking nine deliveries" says nothing about
  whether they matter. Summing quantities across items would be worse — it would be a number that
  means nothing — and naming the promises individually would be a wall. The count is the honest
  figure available, and a reviewer who wants more is arguing for a read model rather than a class.
- **Two classes for one condition.** They share a body and differ only in the record they hang on,
  which is a catalog constraint rather than a domain distinction. If `record_type` ever becomes a
  set, these two are the first candidates to fold together.

## Complexity Tracking

No Constitution exception is claimed. No schema change, no new entity, no new operation, no new
cause, and no change to any existing behaviour.
