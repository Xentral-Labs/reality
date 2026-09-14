# Implementation Plan: A Return Is Not Finished When It Arrives

**Branch**: `082-return-resolved` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One nullable column on `movement`, the validation that keeps it honest, and the class it makes
derivable. The second schema change in this line of work and the same shape as the first: an
edge that turns a question nobody could answer into one derived at read time.

The catalog goes from nineteen classes to twenty, and the last gap the trading survey found
closes.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; one nullable self-referencing column on `movement`
**Testing**: pytest business stories under `tests/` and `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities; opaque IDs; strict tenant scope
**Scale/Scope**: One column, one validation, one derivation, one more use of a learned norm

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The reference is Reality about Reality: which movement settled which. The trace reaches both movements, the promise behind the return and the SourceRecord by opaque identity | PASS |
| Reality owns operational state | Nothing gains a status and no outcome is labelled. What happened is what the resolving movement is, and the outstanding quantity is derived per read | PASS |
| Proven schema only | The column exists solely to make one named condition derivable, and that class ships with it. Without it the condition can only be guessed at, and a guess is what the alternative below was rejected for | PASS |
| Tenant + shared service boundaries | Validation and every derivation filter `tenant_id`, including the norm | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry returns what came back, what was settled, what is outstanding and the norm it is judged against | PASS |
| Received values not recomputed | No value a source stated is touched. Quantities are movements added up at read time and stored nowhere | PASS |
| Smallest coherent design | Three alternatives rejected below, including the one that needs no schema | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Derive it from what is left in the returns location.** No schema at all, and rejected
  because stock is fungible: five back and five out later says nothing about whether those
  were the same five. It would produce a condition that is sometimes right, which is the one
  thing this catalog does not ship.
- **A relation table, as movement correction uses.** Correct for a correction, which relates
  three movements and carries its own reason and fingerprint. A resolution relates two and
  carries nothing of its own, so a table would be a row per link with no columns worth having.
- **An outcome field on the return — restocked, scrapped, sent back.** A label that can
  disagree with the movements it summarises, and a second authority for something already
  stated. The resolving movement's own type says what happened.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/db/core.py                     # the column
packages/reality-core/migrations/versions/0038_*.py              # its revision
packages/reality-core/src/reality/services/core.py               # validation on record
packages/reality-core/src/reality/web/api.py                     # the field on the movement write model
packages/reality-core/src/reality/mcp/catalog.py                 # the movement tool schema
packages/reality-core/src/reality/services/exceptions.py         # the norm, the derivation, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the class and its guidance
packages/reality-core/config/tenant_isolation_catalog.yaml       # any new public read
packages/reality-core/tests/                                     # write path, derivation and explanation proof
docs/DATA_MODEL.md                                               # the new relationship
docs/features/movements.md                                       # a movement may resolve a return
docs/features/operational_exceptions.md                          # taxonomy row
apps/docs/content/catalogs/exceptions.md (+ de/)                  # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

## Design

### The column

`movement` gains `resolves_movement_id`, a nullable self-referencing foreign key. Nullable is
the design: almost every movement settles no return, and `null` says exactly that rather than
leaving it unknown.

The revision is `0038_return_resolution`, following `0037_invoice_order_link`. It adds one
column and nothing else, so downgrade drops it and no data moves either way.

### Validation

Four checks, each of which makes the link mean something:

- The target is a `return` movement of the same tenant.
- The resolving movement concerns the same item.
- It takes goods **out of the location the return brought them into**. This is the only
  physical check available, and without it any outward movement could claim to settle any
  return. It is also the feature's real limit: a business that shuttles returns through an
  inspection area first will have that first move counted as the resolution.
- The resolutions of one return never exceed what came back, counted the correction-aware way.

Instants are deliberately not policed. A resolution recorded as happening before its return is
accepted, because movement times are caller-supplied everywhere in this product and nothing
else checks their order; it simply contributes a lag of zero, the way Spec 080 clamps a
backdated shipment.

### The class

`return_unresolved` walks returns with quantity still unresolved and reports those older than
a learned threshold.

The norm is the third use of Spec 080's helper and needs no new machinery: the median of the
most recent resolved returns, times the product multiple, never below a floor, and nothing at
all claimed below the minimum history. A company that inspects returns weekly and one that
inspects quarterly should not share a number, and neither should have to type one.

The carrier is the return Movement, which is already a record type.

### Identity, ordering and guidance

The identity is `exc__return_unresolved__{movement_id}`. It sorts beside the other return
classes, and each entry sorts on when the goods came back, so the longest-standing is first.

Spec 071's cross-reference rule applies. `return_unresolved` and `returned_not_credited` are
the two halves of one return's life — goods sitting versus money not given back — and must
name each other. `unexplained_movement` should say that a return naming its delivery and
resolved by a later movement is explained at both ends.

### Data and migration impact

One nullable column, one Alembic revision, no backfill. Returns already recorded stay as they
are and are simply unresolved, which is what they are.

### Failure, security, and tenant behavior

Every refusal happens at the point of recording with a message naming what is wrong. Every
derivation filters `tenant_id`, including the norm, so one company's speed can never judge
another's.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_returns.py::test_a_movement_may_resolve_a_return` | column does not exist |
| FR-002 | unit | `tests/test_returns.py::test_a_resolution_is_validated` | a non-return and a foreign return are accepted |
| FR-003 | unit | `test_a_resolution_is_validated` | another item and another location are accepted |
| FR-004 | unit | `tests/test_returns.py::test_resolutions_may_not_exceed_what_came_back` | over-resolution accepted |
| FR-004a | unit | `tests/test_returns.py::test_a_backdated_resolution_is_accepted` | the movement is refused |
| FR-005 | unit | `tests/test_returns.py::test_a_return_may_be_resolved_in_parts` | a second resolution is refused |
| FR-006 | story | `test_derivation.py::test_return_unresolved` | absence treated as unknown |
| FR-007 | story | `test_derivation.py::test_return_unresolved` | class is not derived |
| FR-008 | story | `test_derivation.py::test_the_resolution_norm_describes_this_tenant` | no norm is derived |
| FR-009 | story | `test_derivation.py::test_a_voided_resolution_stops_counting` | a voided resolution still settles |
| FR-010 | service | `test_derivation.py::test_return_unresolved_exposes_full_entry_shape` | causal values missing |
| FR-011 | service | `test_return_unresolved_exposes_full_entry_shape` | trace keys missing |
| FR-012 | story | `test_derivation.py::test_return_unresolved_clears_through_reality` | entry persists after restocking |
| FR-013 | service | `test_explanation.py::test_return_unresolved_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-014 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-015 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-016 | story | `test_derivation.py::test_return_unresolved_orders_longest_first` | order varies between reads |
| DR-001 | story | `test_return_unresolved_clears_through_reality` | state is written |
| DR-002 | story | `test_return_unresolved_clears_through_reality` | derivation is not read-time |
| DR-003 | story | `test_a_voided_resolution_stops_counting` | a second count appears |
| DR-004 | service | `test_return_unresolved_exposes_full_entry_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_resolution_norm_is_learned_per_tenant` | one tenant's speed judges another |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-007 | review | no outcome field exists on any model | — |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

The revision adds one nullable column, so it applies to a populated database without locking
anything meaningful and downgrades by dropping it. Movements without a reference behave
exactly as they do today.

The demo month records a return with no commitment and no resolution. Whether to teach the
demo the new link is a decision about the demo, and
`test_the_month_ends_with_exactly_these_exceptions` forces it to be made rather than drift.

## Review Risks

- **The location check is the whole physical guarantee, and it is thin.** It stops nonsense
  and it also decides how a two-step returns process is recorded. A business that inspects
  elsewhere before deciding will find its transfer counted as the resolution, which is
  arguably correct and arguably not.
- **Absence as a statement, a third time.** The class concludes from a missing resolution
  exactly as Spec 076 concludes from a missing bill and Spec 079 from a missing credit. The
  contract that every resolving movement sets its reference is now load bearing in three
  places, and nothing enforces it.
- **The second schema change here.** A column is a different kind of commitment from a
  derivation. It is justified by one class, where Spec 076's was justified by three, and a
  reviewer should judge whether one is enough given that the alternative was a guess.
- **A third learned norm.** Reusing Spec 080's helper is cheap and makes three classes share a
  statistic whose constants nobody has measured. If those constants are wrong, they are now
  wrong in three places at once.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
