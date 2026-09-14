# Implementation Plan: Silent Source Detection

**Branch**: `072-silent-source` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

A ninth exception class on the declared source capability: it has stopped delivering,
judged against the rhythm it has shown itself. The expectation is computed from the receipt
times of its own recent records, so nothing is configured and every tenant is judged by the
same rule.

No schema, no migration, no persisted state, no frontend change. The one thing this feature
touches outside its own class is the description of `source_interpretation_failure`, which
must now name its new sibling — the rule Spec 071 established for confusable pairs.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no new table, column, or index
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: UTC instants; opaque IDs; strict tenant scope; no tenant-tunable values
**Scale/Scope**: One class, no new cause, four product constants

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Derived from the tenant's own SourceCapability, SourceSystem and SourceRecord; the trace reaches all three by opaque identity. The condition lives entirely on the Source stage, which is where the gap is | PASS |
| Reality owns operational state | Derived per read, cleared by a record arriving; no status field on a capability, no ticket, no acknowledgement | PASS |
| Proven schema only | No schema change. Capabilities, their systems and record receipt times already exist | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`, including the record history behind each capability; all surfaces keep consuming `reality.services.exceptions` | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below, and the catalog entry names its executable evidence | PASS |
| Explainable web behavior | Explanation re-derives the current condition and returns the learned pause alongside the silence, so the judgement can be checked rather than believed | PASS |
| Smallest coherent design | Three alternatives rejected below, including the configured interval the specification rules out | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A configured expected interval per capability.** Rejected in the specification: it
  would be the product's first tenant-tunable parameter, and it would be less accurate than
  the behaviour it replaces.
- **The median gap multiplied by a factor.** Considered first and rejected on a concrete
  counter-example: a source delivering hourly during business hours has a median gap of an
  hour and pauses twelve every night, so any small multiple of the median reports a failure
  every night and every weekend. The longest observed pause absorbs those rhythms because
  they are part of the history.
- **Watching the source stream instead of the capability.** Rejected: a stream belongs to
  one external object and falls silent whenever that object stops changing, which is the
  normal end of its life rather than a fault.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py  # derivation, registry, order
packages/reality-core/src/reality/catalogs.py             # class order
packages/reality-core/config/operational_exception_catalog.yaml  # class and its guidance
packages/reality-core/tests/operational_exceptions/       # derivation, coverage, explanation proof
docs/features/operational_exceptions.md                   # durable business contract
apps/docs/content/catalogs/exceptions.md (+ de/)          # generated, regenerated and formatted
docs/SPEC_COVERAGE_MATRIX.md                              # spec and evidence rows
```

**Files/layers affected**: one service module and the catalog. No adapter and no frontend:
the queue row contract is unchanged. No new public service function, which also keeps the
tenant isolation catalog untouched — the lesson from Spec 069, where a public lookup
tripped that gate for no benefit.

## Design

### The expected pause

One name throughout: the **expected pause** is the longest interval between consecutive
receipts inside the history window. The specification, this plan, the causal values and the
operator guidance all use that term, so a reader never has to work out whether a "learned
rhythm" and an "observed pause" are the same thing.

For each active capability, resolve its system code, load the receipt times of its most
recent records for that system and source type, and walk them in order:

- fewer than the minimum history — say nothing at all, and do not fall back to a default;
- otherwise, the expected pause is the longest interval between consecutive receipts inside
  the window;
- the silence is the interval from the most recent receipt to the evaluation instant;
- the entry appears when the silence exceeds both twice the expected pause and the absolute
  minimum.

The four constants live together at the top of the module with the reasoning attached, so
that a future reader changes them deliberately or not at all:

```text
SILENT_SOURCE_HISTORY = 20      # records considered
SILENT_SOURCE_MIN_HISTORY = 5   # below this, no rhythm is claimed
SILENT_SOURCE_MULTIPLE = 2      # of the longest observed pause
SILENT_SOURCE_FLOOR = 24 hours  # never report a shorter silence
```

Two degenerate histories deserve their behaviour stated. If every record arrived in the
same second the longest pause is zero, and the floor alone decides — which is right: such a
source has shown no rhythm to speak of, so only the absolute minimum applies. If one
unusually long pause dominates the window, the expectation is generous for a while and
tightens as that pause leaves the window. Both are consequences of learning from history,
not defects to be smoothed away.

### Reality flow

The authoritative record is the `SourceCapability`; the identity is
`exc__silent_source__{capability_id}`. `source_capability` becomes the seventh record type.
The entry sorts on the last receipt, so the longest-silent capability comes first.

Inactive capabilities are skipped, and so are capabilities with no records at all — the
second is a different condition and an explicit non-goal, not an oversight.

### Confusable pair

Spec 071 requires the distinction between two confusable classes to be written into both.
This class and `source_interpretation_failure` are the clearest such pair — both are about
a source not producing business records — so this feature also edits the existing class's
description. One reports a delivery that arrived and could not be understood; the other
reports that nothing arrived at all.

### Catalog activation

Atomic, as established in Spec 068, and now including the operator guidance that Spec 071
made mandatory: the derivation, its registry entry, both order constants and the catalog
entry with its description, owner and clearing path land in one step. No cause is added.

### Data and migration impact

None.

### Failure, security, and tenant behavior

Every query filters `tenant_id`, including the record history. Explanation re-derives, so a
malformed, unknown, resumed or foreign identity produces the existing `NotFound`. A record
whose receipt time is later than the evaluation instant yields a negative silence, which
fails the comparison and produces no entry rather than an error.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_silent_source` | class is not derived |
| FR-002 | story | `test_derivation.py::test_silent_source` | silence measured from the wrong point |
| FR-003 | story | `test_derivation.py::test_silent_source_learns_the_rhythm` | a weekend-shaped history is reported as silent |
| FR-004 | story | `test_derivation.py::test_silent_source_floor_protects_fast_sources` | a minute-rhythm source reports after minutes |
| FR-005 | story | `test_derivation.py::test_silent_source_says_nothing_without_history` | fresh, sparse and inactive capabilities appear |
| FR-006 | service | `test_derivation.py::test_silent_source_entry_shape` | causal values missing |
| FR-007 | service | `test_derivation.py::test_silent_source_entry_shape` | trace keys missing |
| FR-008 | story | `test_derivation.py::test_silent_source_clears_when_delivery_resumes` | entry persists after a new record |
| FR-009 | service | `test_explanation.py::test_silent_source_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-010 | service | `test_derivation.py::test_silent_source_orders_longest_silence_first` | order constants lack the id |
| FR-011 | unit | `test_coverage.py::test_production_operational_exception_catalog_has_closed_registry` and the guidance tests | registry drift; missing guidance |
| FR-012 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| DR-001 | story | `test_silent_source_clears_when_delivery_resumes` | nothing persists |
| DR-002 | story | `test_silent_source_learns_the_rhythm` | expectation independent of history |
| DR-003 | unit | `test_derivation.py::test_silent_source_constants_are_product_wide` | constants absent or per-tenant |
| DR-004 | service | `test_silent_source_entry_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_silent_source_is_tenant_scoped` | cross-tenant history leaks |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged; guards that no cause was added |

## Rollout and Rollback

No migration, so rollback is a plain revert. The first-deployment consequence is the
opposite of the last two features: this class reports nothing at all until a capability has
five records and has then fallen silent, so an import of historical data cannot light it
up. The volume question that mattered for Specs 068 and 069 does not arise, and the risk
runs the other way — the class may be too quiet to notice it works, which is why the
learned-rhythm tests carry realistic shapes rather than minimal ones.

## Review Risks

- **The four constants.** They are judgement, and they are the feature. The plan and the
  specification record them together with the reasoning so a reviewer can disagree with a
  number rather than with an unexplained behaviour.
- **A rhythm that genuinely changes.** A daily feed that becomes monthly reports once and
  then settles as the new pause enters its window. Accepted and stated; it is the honest
  consequence of learning.
- **Capabilities without records and records without capabilities.** Ingestion validates
  neither direction, so both exist. Only the declared side is watched, and a capability
  declared under a system code nobody delivers to will simply never have history.
- **Silence is measured at Reality's door.** Receipt times record arrival here, not creation
  in the source system, so a connector that delivers stale data on time is not reported.
  That is a different condition and not this one.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
