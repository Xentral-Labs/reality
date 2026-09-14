# Implementation Plan: A Document's Total Is Received, Not Computed

**Branch**: `077-received-document-total` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Remove the one place the core produces a figure a source owns. The total becomes required
where a document with lines is recorded, and the sum of the lines moves into the interface
as a prefilled, editable suggestion.

Small in code, and the first change made under Constitution 1.2.0.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript for the two forms
**Primary Dependencies**: SQLAlchemy 2, Pydantic v2, React
**Storage**: PostgreSQL; no schema change, no stored value changes
**Testing**: pytest for the service, the endpoint and the tool schema; frontend build
**Project Type**: backend service plus two interface forms
**Constraints**: Decimal for money; the stated total is stored verbatim
**Scale/Scope**: Two required amounts through three entry points, two forms, seven tests

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The total is Evidence stated when the document is recorded; the ledger keeps posting it and no link changes | PASS |
| Reality owns operational state | No status or derived state moves; only the origin of one number | PASS |
| Proven schema only | No schema change. `gross_amount` exists and stops being optional | PASS |
| Tenant + shared service boundaries | Untouched; the same shared operation is called by every entry point | PASS |
| Spec/test traceability | Every FR and DR maps to a named test or a stated review below | PASS |
| Explainable web behavior | The interface shows the number it will send and lets a person change it, which is more explainable than the silent sum it replaces | PASS |
| Received values not recomputed | This feature is the correction that makes the row true: after it, no document total is produced by the core | PASS |
| Smallest coherent design | Two alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Keep the fallback and validate it against the lines.** Rejected: a validation makes our
  rounding the arbiter again, and refusing a difference hides exactly the case the change
  exists to reveal.
- **Require the total only for documents that represent something external.** Rejected: the
  code cannot tell a typed-in supplier invoice from an order the company originates, and a
  rule that depends on intent is a rule nobody can apply.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py   # the parameter, at both operations
packages/reality-core/src/reality/mcp/catalog.py     # the order tool schema
packages/reality-core/src/reality/web/api.py         # both write models
apps/web/src/App.tsx                                 # both forms prefill and send it
packages/reality-core/tests/                         # existing call sites state a total
packages/reality-core/config/command_catalog.yaml    # the new parameter is documented
apps/docs/content/**/02-data-model.md                # the handbook states the rule, en and de
```

## Design

### The two parameters

Both computed figures go. `_normalize_manual_line_input` stops deriving a line's amount
from quantity times unit price and requires it, and `create_manual_document_with_lines`
takes `gross_amount` as a required keyword with the branch that falls back to the sum
deleted rather than made conditional. Fixing only the header would have left every line's
money produced by the core — and line amounts are exactly what a later line-level
reconciliation would compare.
`create_manual_order` gains the same required keyword and passes it through; both of its
callers — the agent tool and the order endpoint — supply it.

The calculated total is not replaced by a validation. A document whose stated total differs
from its lines is recorded as stated, because that difference is the finding.

### The interface

Both forms compute the sum of the lines they hold and place it in a total field, which the
person can change before sending. The computation is presentation: it produces a suggestion
on screen, and the number becomes real only when somebody sends it. That is the whole
resolution of the double-entry objection — the convenience stays, the authority moves.

### The tool schema

`order_create` gains `gross_amount` in its required list. An agent proposing an order is
reading something, and the total should come from what it reads. Leaving it optional would
put the core back in charge of inventing it for the caller most likely to have a source.

### Data and migration impact

None. No column changes, no stored value changes, and no document is rewritten.

### Failure, security, and tenant behavior

A missing total is refused where the document is recorded, before anything is written, with
a message naming what is missing. Nothing about tenancy changes.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_documents.py::test_recording_requires_a_stated_total` | the call succeeds without one |
| FR-002 | unit | `tests/test_documents.py::test_stated_amounts_are_stored_verbatim` | the products and the sum overwrite the statements |
| FR-003 | unit | `test_recording_requires_a_stated_total` | no message names the total |
| FR-004 | unit | `tests/test_documents.py::test_total_may_differ_from_the_lines` | a difference is rejected or corrected |
| FR-005 | unit | `tests/test_documents.py::test_zero_total_is_a_statement` | zero is treated as absent |
| FR-006 | review | the two forms, read as a reviewer | — |
| FR-007 | unit | `tests/test_application_catalog.py` tool schema assertion | the total is not required |
| DR-001 | unit | `test_stated_total_is_stored_verbatim` | — |
| DR-002 | story | the existing derivation suites, unchanged | — |
| DR-003 | story | `tests/test_ledger.py`, unchanged | posting no longer matches the stated total |

FR-006 is verified by reading rather than by test. Whether a field is prefilled and editable
is a property of the form; the suite proves what is sent and stored, not what a person sees.

### What this change does not reach

The Shopify adapter still stores `quantity * price` as a line amount, because the payload
states no line total. That is a violation of the same principle, and it is left standing
deliberately: closing it means deciding what Reality holds when a source states nothing,
and that question belongs to a specification about sources rather than to this one.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert. The one visible effect
is that a caller omitting the total is now refused — inside this repository that is the
seven test call sites and the two forms, all of which change with it.

## Review Risks

- **A required argument is a breaking change for callers outside this repository.** There
  are none today, and that is the reason to make it now rather than later.
- **The prefill can drift from the core.** The interface adds up lines the way it displays
  them. If that ever differs from how the core would have, the person sees the number and
  can correct it — which is the design, not a defect, but a reviewer should be comfortable
  that the suggestion is visible rather than applied silently.
- **The temptation to validate.** The next reader will want to refuse a total that does not
  match the lines. The specification says why that would undo the change; the reason should
  stay visible in the code as well.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
