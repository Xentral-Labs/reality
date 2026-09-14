# Implementation Plan: Overdue Receivable Visibility

**Branch**: `069-overdue-receivables` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add one derived class to the closed operational exception catalog: a sales invoice past
its derived due date with money outstanding. The due date is not stored anywhere and does
not need to be — it is the invoice date advanced by the payment term, and that arithmetic
already exists twice in the repository with no caller.

The work is therefore a consolidation before an addition. One shared derivation answers
when an invoice is due and how late it is at a given instant; the queue consumes it, the
duplicated copy in the read model delegates to it, and the class is activated atomically
the way Spec 068 established. No schema, no migration, no persisted state, no frontend
change.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no new table, column, or index
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal amounts; UTC instants; opaque IDs; strict tenant scope
**Scale/Scope**: One class, no new cause, one duplicated rule consolidated

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Derived from the tenant's own sales invoice, its payment term and its control ledger entry; the trace reaches invoice, control entry and SourceRecord by opaque identity | PASS |
| Reality owns operational state | Derived per read, cleared by settlement or reversal; no ticket, no acknowledgement, and the invoice keeps its source lifecycle status only | PASS |
| Proven schema only | No schema change. The invoice date and the payment term already exist and are already read by the open-item derivation | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the queue and the read model call one application derivation, and no adapter derives a due date | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below, and the catalog entry names its executable evidence | PASS |
| Explainable web behavior | Explanation re-derives the current queue and returns causal values plus the shortest trace, identical to existing classes | PASS |
| Smallest coherent design | Consolidating the duplicated rule is smaller than adding a third copy; three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Write the due-date arithmetic a third time inside the exception derivation.** Smaller
  as a diff and rejected outright: it would make three places responsible for when money
  is due, and the queue's whole value is that it cannot disagree with the rest of the
  product.
- **Store a due date on the invoice.** Rejected by the proven-schema principle. The value
  is a function of two fields that already exist, and storing it would let it go stale
  when a payment term changes.
- **Cover payables in the same class.** Rejected in the spec: the condition is symmetric
  but dunning and paying are different decisions, and one entry maps to one decision.
- **Delete the two dead aging functions instead of consolidating them.** Tempting, and
  rejected: the rule they contain is the one this feature needs, and the read model is
  the shape a later aging view will use. Deleting would mean writing it a third time
  anyway.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py        # the one due-date rule, as_of-aware
packages/reality-core/src/reality/services/exceptions.py  # derivation, registry, order
packages/reality-core/src/reality/web/read_models.py      # delegates instead of computing
packages/reality-core/src/reality/catalogs.py             # class order
packages/reality-core/config/operational_exception_catalog.yaml  # closed product authority
packages/reality-core/tests/operational_exceptions/       # derivation, coverage, explanation proof
packages/reality-core/tests/                              # aging consolidation proof
docs/features/operational_exceptions.md                   # durable business contract
apps/docs/content/catalogs/exceptions.md (+ de/)          # generated, regenerated and formatted
docs/SPEC_COVERAGE_MATRIX.md                              # spec and evidence rows
```

**Files/layers affected**: services and catalog, plus one read model that loses arithmetic
it should not have had. Dependency direction unchanged. No `apps/web` change: the queue
row contract it reads is untouched, and no due-date column is added anywhere. No `domain/`
change: the rule needs session-bound records to reach a payment term, so it belongs in the
application layer, and the empty domain module stays empty.

## Design

### The one due-date rule

Two pure helpers plus one register, all in `services/core.py` beside the existing
`aging_register`:

- `effective_payment_term(document, party_payment_term_id, terms)` decides which term
  governs: the invoice's own, else its party's, else none. Both row builders carry the
  party's term id so this stays a pure decision over data the caller already has.
- `invoice_due_date(document, term)` returns the invoice date advanced by the governing
  term's due days, the invoice date itself when no term applies, and `None` when the
  recorded date cannot be read. The date is stored as a string, so the parse guard is part
  of the rule rather than of each caller.
- `invoice_days_overdue(due_date, as_of)` counts whole days from the due date to the
  evaluation instant, and `None` without a due date.
- `aging_register(session, tenant_id, *, as_of=None)` gains the evaluation instant,
  defaulting to now, and keeps returning the open-item rows enriched with `due_date` and
  `days_overdue`.

`web/read_models.py:aging_page` keeps its pagination and calls the two helpers instead of
recomputing them, which removes business arithmetic from the transport layer. It gains the
same optional evaluation instant as the register, because two consumers cannot be compared
at one point in time if one of them can only read the wall clock. Both aging
entry points had no caller, so this consolidation is observable only through the new
class — which is exactly why the class carries the proof for it.

### Reality flow

`overdue_receivable` walks the tenant's open items, keeps the sales invoices whose status
is open or partial with an outstanding amount above zero, derives the due date through the
shared rule, and reports those whose due date precedes the evaluation instant. Reversed
and fully settled invoices are already excluded by the open-item derivation, so the class
inherits that judgement rather than restating it — the same relationship
`reservation_exceeds_stock` has with the inventory derivation.

The authoritative record is the invoice `Document`; the identity is
`exc__overdue_receivable__{document_id}`. The entry sorts on its due date, so the
longest-overdue receivable surfaces first. `document` becomes the sixth record type, after
`commitment`, `import_job`, `movement`, `ledger_entry` and `item`; the explanation path
needs no change for it, because the `raw_source` branch is keyed on `import_job` and
already defaults to `None` otherwise.

### Service and adapter flow

The derivation is registered in `DERIVATION_REGISTRY` and the class id is placed seventh
in `CLASS_ORDER` and `OPERATIONAL_EXCEPTION_CLASS_ORDER`:

1. `overdue_outgoing_customer_commitment`
2. `outgoing_commitment_at_risk`
3. `overdue_incoming_supplier_commitment`
4. `reservation_exceeds_stock`
5. `source_interpretation_failure`
6. `unexplained_movement`
7. `overdue_receivable`
8. `unmatched_financial_event`

Money already lost ranks ahead of money that arrived and could not be matched, and both
stay at the end because they are the finance operator's queue rather than the warehouse's.
Every adapter keeps calling the same two entry points and needs no edit.

### Catalog activation

Atomic, as established in Spec 068: the validator requires the catalog ids to equal
`OPERATIONAL_EXCEPTION_CLASS_ORDER` exactly and the catalog derivations to equal the
`DERIVATION_REGISTRY` keys exactly, so the derivation, its registry entry, both order
constants and the catalog entry land in one step. No cause is added, so the closed cause
vocabulary and its gate are untouched — this feature does not need the relaxation Spec 068
made.

### Data and migration impact

None. No table, column, index, constraint, backfill, or migration. Rollback is a revert.

### Failure, security, and tenant behavior

Every query filters `tenant_id`, including the payment-term lookup. Explanation re-derives
the queue, so a malformed, unknown, settled, or foreign identity produces the existing
`NotFound` response with the same message. An unreadable invoice date yields no due date
and therefore no entry, rather than an error. Nothing here mutates, so no confirmation,
proposal, or idempotency key is involved.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_overdue_receivable` | class is not derived; queue is empty |
| FR-002 | story | `test_overdue_receivable_boundaries` | settled, undue, reversed and non-sales invoices are not yet distinguished |
| FR-003 | unit | `test_ledger.py::test_invoice_due_date_rule` | helper does not exist |
| FR-004 | story | `test_derivation.py::test_overdue_receivable_reports_the_outstanding_amount` | gross amount reported, or no entry at all |
| FR-005 | service | `test_derivation.py::test_overdue_receivable_entry_shape` | causal values and trace keys missing |
| FR-006 | story | `test_derivation.py::test_overdue_receivable_clears_through_settlement` | entry persists after allocation |
| FR-007 | service | `test_explanation.py::test_overdue_receivable_explanation_and_not_found_parity` | identity is unknown to explanation |
| FR-008 | service | `test_derivation.py::test_overdue_receivable_orders_before_unmatched_payment` | class order constant lacks the id |
| FR-009 | unit | `test_ledger.py::test_one_aging_rule_serves_every_consumer` | read model computes its own dates |
| FR-010 | unit | `test_coverage.py::test_production_operational_exception_catalog_has_closed_registry` | registry drift: class missing from catalog or code |
| FR-011 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_overdue_receivable` | adapters see fewer classes than the service |
| DR-001 | story | `test_overdue_receivable_clears_through_settlement` | nothing persists, so failure proves derivation is missing |
| DR-002 | service | `test_overdue_receivable_reports_the_outstanding_amount` | queue computes its own remainder |
| DR-003 | service | `test_derivation.py::test_overdue_receivable_entry_shape` | trace restates business fields |
| DR-004 | unit | `test_ledger.py::test_one_aging_rule_serves_every_consumer` | arithmetic still lives in the read model |
| DR-005 | story | `test_derivation.py::test_overdue_receivable_is_tenant_scoped` | cross-tenant rows leak |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged; guards that no cause was added |

Documentation evidence: `docs/features/operational_exceptions.md` gains the taxonomy row
with its clearing path and the due-date rule, and the generated catalog pages are
refreshed with the generator followed by `npm run format` in `apps/docs` — without the
formatting pass every catalog page shows a whitespace-only diff.

## Rollout and Rollback

No migration, so deployment order is irrelevant and rollback is a plain revert. One
operational consequence is expected: a tenant that imported invoices without payment terms
will see them as due on their invoice date, so an established receivables ledger can
produce a large number of entries on first deployment. This is the same shape as the
overdue-promise backlog measured for Spec 068 and is treated the same way — a true finding
whose remedy is correcting the terms at the source. The volume should be looked at on a
realistic tenant before merge rather than assumed.

## Review Risks

- **Inherited fallback.** An invoice without a payment term becomes due on its issue date.
  That rule comes from the existing derivation and is now visible for the first time,
  which means this feature will be blamed for it. It is recorded in the spec's
  clarifications so the decision is findable.
- **Consolidation without a consumer.** Both aging entry points were dead, so the
  refactor's only live proof is the new class plus the parity test. If either is weak the
  duplication can silently return.
- **Amount sign and reversal.** The outstanding amount comes from the ledger through
  `open_invoice_amount`, which returns zero for a reversed posting group. The class must
  rely on that rather than re-deriving a balance, or a reversed invoice will reappear.
- **String dates.** `document_date` is a string column with an empty default. The parse
  guard belongs to the shared rule; any caller that parses it again is a defect.
- **The party-level term is now consulted, and that decision was measured into being.**
  It was first left out as a scope widening. Measuring the volume showed 20 of 91 entries
  were late only because no invoice-level term applied, so the rule now cascades to the
  party. The residual risk moved with it: a party's term is resolved at read time, so
  changing a customer's terms moves the due dates of its open invoices. That is intended
  and stated in the assumptions, but it means the queue is not a snapshot and a reviewer
  should not expect one.
- **First-deployment volume.** Measured on 2026-09-04 and recorded in the quickstart. An
  imported ledger of 200 invoices produced 91 entries, of which 20 were late only because
  no payment term applies — the youngest issued the day before. The demo scenarios gained
  nothing. The fallback's cost is therefore a known 22% of that queue rather than a guess,
  and it is the strongest argument for the party-level term in T905.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
