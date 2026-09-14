# Implementation Plan: Operator Guidance in the Exception Catalog

**Branch**: `071-catalog-operator-guidance` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Three required fields on every exception class — a business description, an operational
owner and a clearing path — enforced by the catalog gate and rendered on the generated
reference. The two hand-written per-class tables are replaced by that reference.

No derivation, no queue behaviour and no schema changes. The proof that this worked is
that the exception suite is untouched and still green while the catalog refuses a class
without guidance.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: PyYAML for the closed catalog; the docs generator and Prettier
**Storage**: None. The catalog is source-controlled metadata
**Testing**: pytest under `tests/operational_exceptions/`
**Project Type**: catalog metadata plus a generated documentation artifact
**Constraints**: closed vocabularies; generated pages are never edited by hand
**Scale/Scope**: Eight classes, three fields, one validator, one generator

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Not applicable: guidance is metadata about a derived class and touches no business record. The derivations are unchanged | PASS |
| Reality owns operational state | Nothing is persisted and no operational state is added; guidance is never read to decide anything | PASS |
| Proven schema only | No schema change. The catalog is a source-controlled file | PASS |
| Tenant + shared service boundaries | Not applicable: the catalog is product metadata, identical for every tenant, and no tenant-scoped read is added | PASS |
| Spec/test traceability | Every FR and DR maps to a named test or a stated documentation review below | PASS |
| Explainable web behavior | The queue and its explanations are unchanged; the generated reference gains the explanation an operator needs | PASS |
| Smallest coherent design | Two alternatives rejected below; adding fields to the authority that already gates classes is the smaller of them | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Fix the two hand-written tables and leave the catalog alone.** Smaller today and
  rejected: it is what produced the defect. Both tables were written once and neither was
  updated when three classes arrived, so the same omission would recur at the next class.
- **Put the guidance in the feature contract and generate the page from there.** Rejected:
  the contract is prose authored for reviewers, not a machine-readable authority, and the
  catalog already gates every other required property of a class.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/operational_exception_catalog.yaml  # the three new fields
packages/reality-core/src/reality/catalogs.py                    # required-field validation
packages/reality-core/tests/operational_exceptions/test_coverage.py  # refusal and completeness proof
apps/docs/scripts/generate-catalog-reference.py                  # renders the guidance
apps/docs/content/catalogs/exceptions.md (+ de/)                 # generated, regenerated and formatted
apps/docs/content/concepts/business-reality-guide/09-exceptions-and-approvals.md  # narrative keeps, table goes
docs/features/operational_exceptions.md                          # clearing-path column goes
docs/SPEC_COVERAGE_MATRIX.md                                     # spec and evidence rows
```

**Files/layers affected**: catalog metadata, its validator, the generator and documentation.
No service, no adapter, no frontend. `services/exceptions.py` is deliberately untouched.

## Design

### The three fields

Each class gains `description`, `owner` and `clears_through`, all required non-empty text,
validated by the same `_required_text` helper that already guards `label`, `severity`,
`record_type` and `authority`. Adding them to that tuple is the whole validation change,
which is the point: guidance becomes as unskippable as evidence.

The text for the eight existing classes is written from what the repository already knows —
the conditions and owners in the handbook chapter for the original five, and the
specifications for the three added by Specs 068 and 069. `unexplained_movement` is the one
class whose clearing path is "nothing", and it says so rather than leaving the field vague.

Causes are untouched. A reason is read through the class that carries it, and requiring
guidance per cause would force text onto `insufficient_reservation` in two places.

### The generated reference

The generator renders the description as a sentence under the class heading, then the
existing metadata list, then the owner and the clearing path. English on both editions:
the surrounding headings stay localised, the guidance does not. That is consistent with
what those pages already do — derivation names, record types and test paths are English on
the German edition today.

### The two hand-written tables

`09-exceptions-and-approvals.md` keeps section 33, which explains how the two queues differ
and is not per-class, and keeps its narrative about recalculation. Its per-class table in
section 34 is replaced by a pointer to the generated reference.

`docs/features/operational_exceptions.md` keeps the class/cause/authority mapping, which is
specification-level, and loses the "Clears through" column, which now lives in the catalog.

### Data and migration impact

None.

### Failure, security, and tenant behavior

Unchanged. A catalog missing a field raises at load, which is the existing behaviour for a
missing label or authority, and the message names the class and the field.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `test_coverage.py::test_every_class_carries_operator_guidance` | production catalog has no such fields |
| FR-002 | unit | `test_coverage.py::test_catalog_rejects_missing_guidance` | blank fields are accepted |
| FR-003 | review | production catalog guidance read against each derivation | — |
| FR-004 | review | production catalog clearing paths read against each derivation | — |
| FR-005 | unit | `test_coverage.py::test_generated_reference_carries_guidance` | generated page lacks the text |
| FR-006 | review | documentation diff | — |
| FR-007 | review | documentation diff | — |
| FR-008 | review | documentation diff | — |
| FR-009 | story | the existing `test_derivation.py` and `test_explanation.py` suites | must stay green untouched |
| DR-001 | unit | `test_every_class_carries_operator_guidance` | — |
| DR-002 | unit | `test_catalog_rejects_missing_guidance` | — |
| DR-003 | unit | `test_catalog_rejects_missing_guidance` | requiring guidance on causes would fail it |
| DR-004 | unit | `test_generated_reference_carries_guidance` | — |

Three requirements are verified by review rather than by test, and say so. Whether a
sentence explains a condition in business terms is not a property a test can assert; what
a test can assert is that the sentence exists, is not blank, and reaches the page.

## Rollout and Rollback

Documentation and metadata only. Rollback is a plain revert. Nothing in the running product
changes, so there is no deployment order and no operational consequence.

## Review Risks

- **Guidance that restates the derivation.** The easy failure is a description that repeats
  the class name in a full sentence. FR-003 exists for that, and it is checked by reading,
  not by a test.
- **The German edition.** English guidance under German headings is a deliberate decision
  recorded in the spec, and it will look like an oversight to a reviewer who has not read
  it.
- **The generator still needs its formatting pass.** Without `npm run format` in
  `apps/docs` every catalog page shows a whitespace-only diff around the real change.
- **Removing content from the handbook.** Section 34's table is the only place some readers
  have seen this information. The replacement must point somewhere that genuinely answers
  the question, or the change is a regression for them.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
