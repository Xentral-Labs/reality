# Data Model: External Agent Audit Closure

## Model decision

No new business table, column, foreign key or migration is planned. This feature changes
public contracts, adds one atomic composition of existing records and derives additional
guidance from current tenant-scoped state.

## Existing authoritative entities

### ChangeProposal

- Holds the exact prepared tool identity, normalized input, preview, lifecycle and receipt.
- Remains the single handoff from agent preparation to authenticated human decision.
- States remain `proposed`, `executing`, `executed` and `rejected`; terminal `failed` records a
  deterministic, rolled-back refusal with no business effect. `executing` remains reserved for an
  outcome whose commit state is genuinely indeterminate.
- Only `proposed` may transition to `executing` through confirmation or to `rejected` through
  explicit rejection. `executing` may transition to `executed` after a committed effect or to
  `failed` only after the attempted transaction rolled back and reconciliation proves that no
  business record, event or ledger effect exists for the action identity. Executed, failed or
  indeterminate execution is never rewritten as rejected.

### SourceRecord

- Immutable lossless statement behind free supplier invoices, payments, credits, dunning and
  cost evidence where a source applies.
- Unknown upstream labels remain payload values and do not become typed operational document
  values without a proven mapping.

### Document and DocumentLine

- Evidence for invoices, credit notes, payments and dunning artifacts.
- A free supplier invoice uses the existing supplier-invoice type and supported lines without
  inventing a purchase order or commitment.
- An invoice-linked credit line retains the existing direct link to the credited invoice line,
  which in turn retains its order evidence relationship.
- Documents do not gain reservation, fulfilment, return, payment or cost status.

### LedgerEntry and SettlementAllocation

- Existing financial authority for receivables/payables, actual cash, bounded invoice
  allocation, reductions and reusable credit.
- Overpayment remains the unallocated part of an actual payment; it is not a fabricated credit
  note.

### DunningNotice and DunningNoticeInvoice

- Existing dated, levelled notice and immutable membership of overdue customer invoices.
- Optional fee retains its existing separate financial evidence and posting semantics.

### Commitment, Reservation and BusinessEvent

- Commitment supplies the exact item and location scope for reservation.
- Reservation is created only for applied quantity above zero.
- `none`, `partial` and `complete` are receipt observations derived from requested/applied/
  shortage and are not stored lifecycle fields.
- BusinessEvent remains correlated proof when an operational effect occurs.

### Movement and return disposition evidence

- The arrived customer-return Movement is the physical subject of disposition.
- Resolving movements retain the applicable location, lot, serial and handling-unit identity
  and their existing direct resolution link.
- Credit evidence remains separate and does not create or resolve a physical movement.

### Cost evidence, basis, review and generation records

- Existing cost records retain admitted components, ownership/method/completeness decisions,
  inventory/commercial/contribution reviews and published results.
- Cost guidance is derived at read time from their presence, state and gaps.
- Actual acquisition cost, inventory value, DB1 and DB2 remain unavailable until their own
  required evidence and review are complete.
- A receipt review's freshness is the equality of its retained canonical evidence fingerprint,
  not equality with the tenant's latest unrelated event sequence.
- An internal transfer consumes and recreates location-scoped quantity while preserving the
  original acquisition layer, owner and receipt trace.

### Received invoice finance detail

- Existing `DocumentLine.payload.reality_finance_v1` retains only source-stated `net`, `tax`,
  `gross`, currency and source codes.
- Absent net or tax remains absent. Gross and ledger postings are not used to manufacture it.
- Contribution reads use stated net evidence and name `received_net_missing` otherwise.

## Derived read contracts

### Proposal next step

- Proposal identity and current lifecycle.
- Whether a current server review is required.
- Canonical review read and Web handoff.
- Required principal and explicit confirmation rule.
- Named verification/reconciliation read.

### Reservation effect

- `none`: applied is zero and no Reservation/event is claimed.
- `partial`: applied is positive and shortage is positive.
- `complete`: requested equals applied and shortage is zero.
- Remaining work equals shortage at execution; current state is re-read separately.

### Invoice credit context

- One tenant-owned posted customer invoice.
- Eligible invoice lines with opaque identity, billed/credited/remaining quantity and amount
  capacity.
- Invoice open amount and explicit blockers.
- Read-only; it grants no credit authority.

### Cost guidance

- Bounded tenant/scope identity and freshness.
- Completed and missing stages.
- Exact missing basis/review reason.
- Next permitted owner-reviewed action and explanation links.
- Read-only; it is not persisted as workflow state.

## Validation invariants

- Every opaque relationship resolves inside the selected tenant or behaves as not found.
- Closed operational types are accepted only from the canonical shared vocabulary.
- Free supplier-invoice header and lines reconcile to the source-stated total under existing
  invoice rules; all evidence and posting effects commit atomically.
- A credit position belongs to the selected invoice and does not exceed remaining capacity.
- A return disposition cannot exceed unresolved arrived quantity or change unrelated tracked
  stock.
- Owner-governed finance/cost effects require an active authenticated owner at confirmation.
- Derived guidance and effect classifications perform no writes.
- An unrelated tenant event does not change a receipt evidence fingerprint; a related component,
  attribution, correction, receipt or category decision does.
- A deterministic failed proposal has no retained domain record, event or ledger effect for its
  action identity and exposes a redacted failure receipt.

## Migration and rollback

No migration or backfill. Rollback removes code-level contracts while leaving every existing
record valid. A later proposal for persistence must return to Constitution/schema review.
