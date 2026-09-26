# Data Model: Fulfillment Safety Parity

## PaymentTerm change

Add one field to the existing tenant-scoped `PaymentTerm`:

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `requires_prepayment` | boolean | yes | false | The stated agreement requires qualifying payment before customer dispatch. |

Validation and lifecycle:

- Creation and update accept an explicit boolean.
- Existing rows migrate to false; no code/name inference occurs.
- Activation/deactivation behavior is unchanged.
- Orders continue to reference the term by opaque tenant-scoped ID.
- Changing a term affects future/current readiness reads for orders that reference it and therefore
  retires any dispatch review whose readiness basis changes.

## FulfillmentReadiness observation

This is a read-time value object, not a table.

| Field | Meaning |
|---|---|
| `document_id` | Customer order being evaluated. |
| `commitment_ids` | Exact customer-delivery commitments covered. |
| `ship_ready` | True only when no blocker remains. |
| `blockers` | Stable coded blocker objects with business explanation and evidence links. |
| `required_amount` | Stated order gross required by the prepayment agreement, or null when not applicable. |
| `received_amount` | Qualifying active customer-payment allocations attributable to the order. |
| `remaining_amount` | `max(required - received, 0)` as a read-time comparison. |
| `currency` | Order currency for all payment comparisons. |
| `line_readiness` | Open, reserved, short and physically available quantities per commitment. |
| `basis` | Canonical IDs/revisions/active states used for explanation and review hashing. |
| `links` | Opaque links to term, order, commitments, reservations, holds, invoices, ledger entries and allocations. |

`remaining_amount` is not a new authority: it is an observation comparing the order's received
stated amount with recorded qualifying allocations.

## Qualifying allocation relationship

```text
sales order Document
  → order DocumentLine
  ← sales invoice DocumentLine.billed_document_line_id
  → sales invoice Document
  → receivable LedgerEntry
  ← active SettlementAllocation
  → customer-payment LedgerEntry
  → payment Document
```

An allocation qualifies only when every record is in the same tenant, invoice and payment are for
the same customer and currency as the order, the invoice is posted, the allocation is active, and
the billed-line set maps unambiguously to this order. Ambiguous consolidated evidence creates a
blocker and contributes zero automatically.

## Proposal lifecycle

No schema change is required. Existing `ChangeProposal.status = failed` and `output` hold the
terminal classification:

```json
{
  "business_effect": "none",
  "error": {
    "code": "<stable-code>",
    "type": "<domain-type>",
    "message": "<business refusal>"
  },
  "safe_next_action": "correct_input_or_prepare_new_proposal"
}
```

Transitions in scope:

```text
proposed → executing → executed
                    ↘ failed        deterministic refusal / known rollback
                    ↘ executing     genuinely unknown effect, reconciliation required
```

Failed proposals are terminal. Pre-handler stale-review refusal remains proposed because execution
was never attempted and a fresh review is the intended recovery.
