# Feature: Payment intake and matching

**Status: customer side implemented by [feature 168](../../specs/168-demo-order-to-cash/spec.md) in `services/payment_intake.py`; supplier side proposed.** This contract accompanies the idea
[Demo Data pays its orders](../ideas/demo-order-to-cash.md) and becomes binding only through a
numbered specification. It describes how money that arrives from a bank, a payment provider
or a synthetic source is recorded, allocated and, where Reality cannot decide, proposed.

Before feature 168 Reality recorded payments (`record_customer_payment`, the bank-statement CSV
profile) and allocated them on explicit human command (`post_customer_payment`,
`allocate_settlement`); nothing matched a payment to an invoice automatically. The shared core
now lives in `services/payment_intake.py`; the synthetic Demo Data source is its first
normaliser, and the bank-statement CSV profile still records without allocating. See [the ledger](./ledger.md) for the
posting and allocation invariants this contract builds on and never weakens.

## Three tiers

Every incoming customer payment passes the same three tiers, whatever its source. The
user-facing definition, with preconditions, outcomes and the reference rules, lives in the docs
site's finance chapter (`apps/docs/content/concepts/business-reality-guide/05-finance.md`); this
file is the developer contract behind it.

| Tier | Who acts | What happens | What it may never do |
|---|---|---|---|
| 1 Record | Reality, always | Payment document plus balanced cash/receivable posting, linked to the SourceRecord | Interpret, allocate, refuse money |
| 2 Allocate | Reality, deterministic | Allocate `min(amount, open)` to exactly one posted invoice the source names | Guess, over-allocate, write off, accept a discount, invent an invoice |
| 3 Propose | Reality computes, a person or agent confirms | Read-time candidates with reasons; confirmation runs the existing propose-and-execute tools | Persist candidates, allocate without confirmation |

Tier 1 is the existing standalone recording. Tier 2 is new and applies only when the link is
**stated by the source** (constitution rule 11). Tier 3 is new and produces observations only
(spec 148: suggestions are read-time observations that require confirmation).

## Stated references and their resolution

A source states zero or more typed references. The normaliser of each source extracts them
verbatim; the shared core resolves them. Human numbers are used to look up, never stored as
the link (constitution rule 6). The allocation remains an opaque `SettlementAllocation`
between two ledger entries.

| Reference type | Looked up in | Path to the invoice |
|---|---|---|
| Invoice number | `Document.number` of the party's posted sales invoices | direct |
| Shop id | `SourceRecord.external_id` of the order in the matching source system | order, then `billed_document_line_id` to the invoice |
| Shop order number | `Document.number` of the party's sales orders | order, then invoice |
| Customer reference / PO | `Document.customer_reference` of the party's sales orders | order, then invoice |
| Customer number | party (`party_accounting_code`) | none; narrows tier-3 candidates only |

Tier 2 allocates only when the resolution yields exactly one posted invoice of the same tenant,
party and currency. Partial billing (two invoices for one order) and consolidated billing (one
invoice for several orders) yield candidates, not an allocation. A provider transaction id
identifies the payment itself and is the payment SourceRecord's `external_id`; it never
resolves to an invoice.

## Outcomes of tier 2

| Amount versus open | Allocation | Visible result | Follow-up decision |
|---|---|---|---|
| equal | full | invoice `paid` | none |
| lower | full amount | invoice `partial`, residual open; `overdue_receivable` after the due date; `early_payment_discount_taken` tag when the invoice's term explains the residual | leave open, explain a deduction, accept a stated reduction (spec 148) |
| higher | open amount | invoice `paid`, remainder as unallocated customer credit; `unmatched_financial_event` for the remainder | allocate credit to another invoice or record an evidenced refund (spec 148) |

No tolerance closes a small residual silently. Every reduction of a receivable is a separate,
confirmed, evidenced posting, never part of matching.

## Tier 3 candidates

Candidates are computed at read time for a payment with unallocated amount and no stated,
unambiguous reference. Sources of candidates, each carrying its reason:

- same party and currency, open amount of exactly one invoice equals the unallocated amount;
- an invoice number of the party appears as a substring of the remittance text;
- a stated reference resolved to more than one invoice (partial or consolidated billing).

Candidates are shown in Payments and over MCP. They are never stored, never ranked as
authority, and never change any balance. Confirming one runs `allocate_settlement` through the
existing proposal flow with the same bounds as tier 2.

## Who confirms

A person or an authorised agent. Chat and MCP call the same tools as CLI and Web; every
mutating action needs confirmation. An agent receives the same candidates and difference
facts a person sees and owns no matching logic of its own. Where a tenant explicitly allows it
for a class of cases, the agent may confirm; the allocation still carries actor, reason and the
evidence it was based on. An agent never recomputes amounts, accepts a discount without the
tenant's explicit rule, or invents an invoice for a payment.

## Invariants

- A payment is recorded exactly once per source identity; replay returns the existing records.
- Recording never fails because matching fails. Tier 1 succeeds or the whole intake rolls back.
- Tier 2 never allocates more than the payment's unallocated amount or the invoice's open amount.
- Tier 2 never allocates across parties, currencies or tenants, and never to an unposted invoice.
- Tier 3 writes nothing. Reading candidates twice yields the same candidates for the same state.
- The remittance text and every stated reference are retained verbatim in the payload.
- Reversal of a payment releases its allocations operationally (spec 024); a confirmed tier-3
  allocation reverses like any other.

## Source normalisers

Each source contributes a thin normaliser that maps its payload to the shared normalised
payment: payer party, amount, currency, effective time, external payment identity, money path
and the list of typed references. The first normalisers are the synthetic Demo Data bank line
and provider capture. Stripe, PayPal and Shopify Payments normalisers register later under
their own `(source_system, source_type)` and change nothing in the core.

## Non-goals

Fuzzy or probabilistic matching in tier 2, amount-tolerance write-offs, automatic discount
acceptance, dunning, provider money paths (fees, payouts) beyond what spec 148 defines, and
matching supplier payments, which mirror this contract in a later extension.

## Party balances (feature 170)

`services/finance/balances.py::party_balances` sums, per party and currency, the open items of
one side from `aging_register` (open amount; overdue where `due_date < as_of.date()` and status
open or partial, the condition of `overdue_receivable` and `overdue_payable`) and the unused credit
from `available_credit_rows` (the unpaged core of the credit register). It stores nothing and
derives no new amount. Surfaces: the open items endpoint with `flow=customer-balances` or
`supplier-balances` (plus `credit_only`, and `party_id` on the open items and credit flows for the
drill-down), the App view Finance → Balances, and the read tool `finance.party_balances.list`
(`finance_party_balances` over MCP).
