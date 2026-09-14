# Implementation Plan: A Fee Is a Charge, Not a Smaller Credit

**Branch**: `095-a-fee-is-a-charge` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two tests and a paragraph of guidance. Nothing the queue computes changes, because nothing about
it is wrong.

The value is that a recording trap becomes a documented choice, and that the behaviour somebody
would otherwise have "fixed" is pinned so it cannot be broken by a later well-meant change.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: none beyond the existing catalogs
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service; no adapter changes
**Constraints**: no derivation change; the guidance must be provable
**Scale/Scope**: Two tests, one guidance paragraph, one guidance test

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Unchanged. The document says what was credited and what was charged; the queue reads both as they are | PASS |
| Reality owns operational state | Unchanged | PASS |
| Proven schema only | No schema change | PASS |
| Tenant + shared service boundaries | Unchanged | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The class's guidance gains the one thing an operator needs before recording a fee | PASS |
| Received values not recomputed | Unchanged; a charge is a figure somebody stated, not a deduction Reality works out | PASS |
| Smallest coherent design | Two alternatives rejected below, both of which would have added a second way to say one thing | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Teach the class to ignore a shortfall a charge explains.** It would need a rule linking a
  charge to a return, which is a second answer to "what counts as credit" and could disagree with
  the first. The charge line already carries the meaning; the class does not need to interpret
  it.
- **Add a way to mark part of a return as uncreditable.** Same objection, plus it would make a
  restocking fee, a damage deduction and a write-off three shapes instead of one.

## Repository Structure and Layer Changes

```text
packages/reality-core/tests/operational_exceptions/test_derivation.py  # both recordings
packages/reality-core/tests/operational_exceptions/test_coverage.py    # the guidance says it
packages/reality-core/config/operational_exception_catalog.yaml        # the guidance
docs/features/operational_exceptions.md
apps/docs/content/catalogs/ (+ de/)                                     # generated, regenerated
docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### Why the model is already right

`returned_not_credited` gathers crediting lines by the order line they name. A charge line names
none, so it is not counted as credit for goods — and it should not be, because it is not credit
for goods. `line_type` appears nowhere in the exceptions module, which is the shape of a rule
that has stayed simple.

The measurement that settled it, run before any of this was written:

```
fee as a reduced credit quantity   -> uncredited_quantity 2.0000
fee as a full credit plus a charge -> no entry, credit note total 72.00
```

### What is actually built

Two tests, so both recordings are pinned. The first proves the intended one clears; the second
proves the other reports, because that behaviour is correct and somebody reading a bug report
about "a false entry on restocking fees" might otherwise remove it.

That second test is the more important of the two. **It exists to stop a future fix.**

And a guidance paragraph on the class, with a test that the guidance says it — the same shape as
the discount class's asymmetry test in Spec 088, where a gate that only checks guidance exists
cannot check what it says.

### Data and migration impact

None.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_a_restocking_fee_is_a_charge_not_a_smaller_credit` | the charge is counted as credit |
| FR-002 | story | `test_a_restocking_fee_is_a_charge_not_a_smaller_credit` | a partial credit is silently forgiven |
| FR-003 | story | `test_a_restocking_fee_is_a_charge_not_a_smaller_credit` | a charge line counts as goods credit |
| FR-004 | unit | `test_coverage.py::test_the_return_guidance_says_how_to_record_a_fee` | guidance omits it |
| FR-005 | review | no diff under `services/` | — |
| DR-001 | review | no migration and no service diff | — |
| DR-002 | story | both recordings asserted in one test | one recording is unpinned |
| DR-003 | unit | `test_coverage.py` closed registry test | passes unchanged |

The two recordings live in one test so neither can be changed without the other being read.

## Rollout and Rollback

No behaviour changes at all. Rollback is a plain revert.

## Review Risks

- **This looked like a defect and is not, which is the interesting part.** The right response to
  "the queue reports a restocking fee for ever" was to check what the queue actually does with
  each recording, and the answer was that one of them is already right. A reviewer expecting a
  fix should read the measurement in the design section first.
- **A tenant that records fees the wrong way still gets a permanent entry**, and guidance is the
  only remedy, because Reality cannot know what was meant by a credit note for eight. That is a
  real limit and it is stated rather than solved.
- **A small specification for a paragraph will look like ceremony.** The paragraph is what an
  operator reads to decide what a class means, and the test is what stops it becoming untrue.
  Both are cheap; the alternative was a feature nobody needed.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
