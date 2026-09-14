# Implementation Plan: Customer Promise and Stock Coverage Exceptions

**Branch**: `068-promise-coverage-exceptions` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add two derived classes to the closed operational exception catalog: an open
customer-delivery commitment whose due date has passed with quantity outstanding, and an
item whose active reservations exceed observed stock. Both are read-time derivations over
records that already exist. No schema, no migration, no persisted exception state, and no
frontend change: the queue already renders severity, title and impact generically.

The work is concentrated in one service module, one catalog file, and the catalog gate
that keeps the two in step. The only structural change is to the gate itself: it must
allow one business reason to be named by more than one class, because the reservation
shortfall becomes a cause of the overdue class as well.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no new table, column, or index
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities; UTC instants; opaque IDs; strict tenant scope
**Scale/Scope**: Two classes, one reused cause, one catalog gate relaxation

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Both classes derive from tenant-owned Commitment, Reservation and Movement records; the overdue class carries the existing commitment trace to Document and SourceRecord, the stock class references item, reservations and commitments by opaque identity only | PASS |
| Reality owns operational state | Derived per read, cleared by reality changing; no ticket, no acknowledgement, no status written to Documents or Commitments | PASS |
| Proven schema only | No schema change, no migration, no field added for derivation; every input already exists and is already read by the Inventory view | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; all surfaces keep consuming `reality.services.exceptions` with no surface-specific derivation | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below, and each catalog entry names its executable evidence | PASS |
| Explainable web behavior | Explanation re-derives the current queue and returns causal values plus the shortest trace, identical to existing classes | PASS |
| Smallest coherent design | Three simpler alternatives considered and rejected below with reasons | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Add `past_due` as a cause of `outgoing_commitment_at_risk` instead of a new class.**
  Rejected: the title "Customer commitment at risk" would then describe a promise that is
  already broken, and the queue could not order late promises ahead of merely risky ones,
  because ordering works on class and severity, not on causes.
- **Derive over-subscription per competing commitment instead of per item.** Rejected by
  DR-007: naming a victim requires an allocation priority the model does not define.
- **Report over-subscription as an `uncovered_reservation` cause on every competing
  commitment instead of as an item-level class.** This would need no new record type and
  would keep every entry anchored on a transaction, and it is not blame attribution: when
  an item is short, no reservation on it is safely backed, so all competing commitments
  carry the same reason without any allocation priority. Rejected on queue economics and
  subject: one shortage is one decision — buy more or reprioritise — and would arrive as
  as many rows as there are competing promises, which is the row multiplication Spec 020
  already refused on the other axis. "This order is unreserved" is an order question the
  at-risk class answers; "this item is promised twice" is a supply question whose subject
  is the item. The affected orders stay one click away because DR-003 requires the
  explanation to list the competing reservations and commitments.
- **Share one ordered class constant between `catalogs.py` and `services/exceptions.py`.**
  Rejected: verified import cycle. `catalogs.py` imports `reality.tools.application` at
  module level, which imports `reality.services.exceptions` at module level, so the
  exception module cannot import the catalog module at import time. The duplication is
  instead pinned by an equality test.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py   # both derivations, registry, order
packages/reality-core/src/reality/catalogs.py              # class order, cause vocabulary gate
packages/reality-core/config/operational_exception_catalog.yaml  # closed product authority
packages/reality-core/tests/operational_exceptions/        # derivation, coverage, explanation proof
docs/features/operational_exceptions.md                    # durable business contract
apps/docs/content/catalogs/exceptions.md (+ de/)           # generated, regenerated
docs/SPEC_COVERAGE_MATRIX.md                               # spec and evidence rows
```

**Files/layers affected**: service and catalog only; dependency direction unchanged
(`services` → `db`, `catalogs` → `services`). No `apps/web` change: `ExceptionRow` in
`apps/web/src/api.ts` carries only `severity`, `title`, `id` and `impact`, and
`ExceptionItem` renders exactly those, so both classes appear without touching the
frontend. No `domain/` change: neither rule needs a pure-domain home beyond the
derivation itself.

## Design

### Reality flow

`overdue_outgoing_customer_commitment` reads open `customer_delivery` Commitments, derives
the shipped quantity from Movements linked to the commitment, and compares `due_at`
against the evaluation instant. It reuses the existing `_commitment_exceptions` pass, so
one iteration over commitments still produces every commitment-borne class and the
exclusivity rule lives in one place: when a commitment is overdue, the overdue entry is
emitted and carries `insufficient_reservation` as a cause whenever active reservations do
not cover the remaining quantity; the at-risk branch is then skipped for that commitment.

`reservation_exceeds_stock` detects a reservation that lost its backing, not goods
promised twice: `reserve` in `services/core.py` allocates
`min(requested, stock_at - active_reserved)` per item and location, so the write path
cannot over-allocate. `_append_movement` has no matching guard, so stock may leave through
an adjustment, a write-off, or a shipment on another promise while the reservation stays
active. The commitment-level check then still passes, because the reservation exists and
still covers the remaining quantity. The derivation itself is unaffected by this: the
condition remains reserved quantity above observed stock.

The derivation first selects the distinct items holding at least one active
Reservation in the tenant, then compares `active_reserved` against `stock_at` per
candidate — the same two functions the Inventory view uses, which satisfies DR-004 by
construction rather than by convention. Candidate selection keeps the loop bounded to
items that are actually reserved instead of the full item catalog.

The impact summary follows one rule for every class: it states the condition of the class
and appends a clause for an attached cause only where that clause adds a number the
condition does not already carry. An overdue commitment therefore reads
`40 remain overdue` on its own, `40 remain overdue, 15 of them unreserved` when part of
the remainder is unreserved, and `40 remain overdue` again when none of it is reserved,
because the second clause would then repeat the first. That case is the common one after
importing an established order book, so the condition is what keeps the row readable.
Both values are already computed in the same pass and already travel in `causal_values`,
so this costs formatting only.

Ordering context differs between the two. The commitment class sorts on `due_at` like
its supplier-side sibling. The item class has no natural instant of its own, so it sorts
on the earliest `reserved_at` among the contributing active reservations: the
longest-standing over-subscription surfaces first, the value is already loaded for the
reference list, and it keeps the sort total instead of falling back to an opaque id.

Identity stays `exc__{class_id}__{authoritative_record_id}`: the commitment id for the
first class, the item id for the second. `item` becomes the first non-transactional
record type in the catalog; the explanation path needs no change for it, because the
`raw_source` branch is keyed on `import_job` and already defaults to `None` otherwise.

### Service and adapter flow

Both derivations are registered in `DERIVATION_REGISTRY` and both class ids are appended
to `CLASS_ORDER` in `services/exceptions.py` and to `OPERATIONAL_EXCEPTION_CLASS_ORDER` in
`catalogs.py`. The declared order becomes:

1. `overdue_outgoing_customer_commitment`
2. `outgoing_commitment_at_risk`
3. `overdue_incoming_supplier_commitment`
4. `reservation_exceeds_stock`
5. `source_interpretation_failure`
6. `unexplained_movement`
7. `unmatched_financial_event`

Late outgoing promises therefore sort ahead of risky ones at equal severity (FR-009), and
the item-level coverage entry sits after the commitment-borne rows because it is context
for them rather than a separate action. Every adapter — `web/read_models.py`,
`web/api.py`, `tools/application.py`, `services/projections.py`, `services/core.py` —
keeps calling the same two entry points and needs no edit.

### Catalog gate change

`validate_operational_exception_catalog` currently collects cause ids into one catalog-wide
set, rejects any repeat as a duplicate, and asserts the whole set equals
`{"insufficient_reservation"}`. Reusing that reason on the overdue class must therefore
become legal without weakening drift detection. The gate changes to:

- duplicate detection scoped **within** a class, so one class still cannot list a cause twice;
- the union of cause ids compared against a new named constant
  `OPERATIONAL_EXCEPTION_CAUSE_VOCABULARY` in `catalogs.py`, keeping the vocabulary closed
  and the failure message unchanged in shape;
- each declaration keeps its own non-empty evidence, so the same reason must be proven
  separately on each class that claims it.

This gate change is safe on its own: scoping duplicates per class and naming the existing
vocabulary in a constant are both no-ops for the catalog as it stands today, so it can and
must land before any new class is declared.

Activating a class is the opposite: it is **atomic**. The validator requires the catalog
ids to equal `OPERATIONAL_EXCEPTION_CLASS_ORDER` exactly and the catalog derivations to
equal the `DERIVATION_REGISTRY` keys exactly. A YAML entry without its constant, or a
constant without its YAML entry, makes every catalog load raise — which means every test
that touches the catalog fails, not only the new ones. The derivation, its registry entry,
both order constants and the catalog entry for one class therefore belong in a single
step. Two classes may be activated one after the other, because each intermediate state is
internally consistent.

### Data and migration impact

None. No table, column, index, constraint, backfill, or migration. Rollback is a revert.

### Failure, security, and tenant behavior

Every query filters `tenant_id`, including the new candidate-item selection. Explanation
re-derives the queue, so a malformed, unknown, cleared, or foreign identity produces the
existing `NotFound` response with the same message. A commitment crossing its due date
changes class and therefore changes exception identity; the old identity stops resolving,
which is the same behavior as any cleared condition and is covered by an explicit test.
Nothing here mutates, so no confirmation, proposal, or idempotency key is involved.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_overdue_outgoing_customer_commitment` | class is not derived; queue is empty |
| FR-002 | story | `test_derivation.py::test_overdue_outgoing_boundaries` | absent/future due date, closed status and zero remainder are not yet distinguished |
| FR-003 | story | `test_derivation.py::test_overdue_outgoing_supersedes_at_risk` | at-risk entry is still emitted for the same commitment |
| FR-003a | story | `test_derivation.py::test_overdue_outgoing_supersedes_at_risk` | impact states only the overdue remainder, without the unreserved clause |
| FR-004 | story | `test_derivation.py::test_at_risk_unchanged_before_due_date` | passes only once exclusivity is scoped to overdue commitments |
| FR-005 | story | `test_derivation.py::test_reservation_exceeds_stock` | class is not derived |
| FR-005a | story | `test_derivation.py::test_reservation_exceeds_stock_impact` | impact carries no shortfall or competing count |
| FR-006 | service | `test_derivation.py::test_new_classes_expose_full_entry_shape` | causal values and trace keys missing |
| FR-007 | story | `test_derivation.py::test_new_classes_clear_through_reality` | entries persist after shipment, receipt, or release |
| FR-008 | service | `test_explanation.py::test_new_class_explanation_and_not_found_parity` | identities are unknown to explanation |
| FR-009 | service | `test_derivation.py::test_queue_order_places_overdue_before_at_risk` | class order constant lacks the new ids |
| FR-010 | unit | `test_coverage.py::test_production_operational_exception_catalog_has_closed_registry` | registry drift: classes missing from catalog or code |
| FR-010 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | gate still asserts the old single-cause set |
| FR-010 | unit | `test_coverage.py::test_class_order_constants_agree` | duplicated order constants can diverge undetected |
| FR-011 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes than the service |
| DR-001 | story | `test_derivation.py::test_new_classes_clear_through_reality` | nothing persists, so failure proves derivation is missing |
| DR-002 | service | `test_derivation.py::test_overdue_outgoing_customer_commitment` | commitment trace absent |
| DR-003 | service | `test_derivation.py::test_reservation_exceeds_stock_references_are_opaque` | trace restates business fields |
| DR-004 | service | `test_derivation.py::test_queue_and_inventory_agree_on_availability` | queue computes its own availability |
| DR-005 | story | `test_derivation.py::test_new_classes_are_tenant_scoped` | cross-tenant rows leak |
| DR-006 | unit | `test_coverage.py::test_shared_cause_is_declared_on_both_classes` | catalog rejects the reused cause |
| DR-007 | service | `test_derivation.py::test_reservation_exceeds_stock_references_are_opaque` | entry names a failing commitment |

Documentation evidence: `docs/features/operational_exceptions.md` gains both taxonomy rows
with their clearing paths, and the generated catalog pages are refreshed with
`PYTHONPATH=packages/reality-core/src .venv/bin/python apps/docs/scripts/generate-catalog-reference.py`
so the English and German references match the catalog.

## Rollout and Rollback

No migration, so deployment order is irrelevant and rollback is a plain revert of the
service, catalog, and gate changes. One operational consequence is expected and must not
be read as a defect: on first deployment a tenant that imported an established order book
can see a large number of overdue promises at once, because orders that are dead in
practice were never closed at the source. The specification treats this as a true finding;
the remedy is closing or correcting those orders, not suppressing the class. Reviewers
should look at the queue of a realistic demo tenant before merge to see the actual volume.

## Review Risks

- **Exclusivity correctness.** If the reservation shortfall is not attached as a cause of
  the overdue entry, the change silently removes information an operator has today. The
  cause assertion in `test_overdue_outgoing_supersedes_at_risk` is the guard.
- **Backlog volume.** The overdue class can dominate the queue on realistic data; ordering
  and severity choices should be re-examined against a real tenant, not a fixture.
- **Gate relaxation.** Scoping duplicate causes per class must not turn into accepting an
  unknown cause. The vocabulary constant, not the absence of a check, is what keeps the
  catalog closed.
- **Bounded iteration.** Candidate selection keeps `stock_at` off the full item catalog,
  but the per-item pass remains a loop; if a tenant reserves across very many items this is
  the first place to look before optimizing anything else.
- **First non-transactional record type.** `item` as an authoritative record should be
  reviewed against every consumer that reads `record_type`, currently only the
  `import_job` branch of the explanation path.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
