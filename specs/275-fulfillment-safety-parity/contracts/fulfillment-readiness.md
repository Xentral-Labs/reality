# Contract: Fulfillment Readiness and Dispatch Review

## Read result

All identifiers are opaque and tenant-scoped. Decimal values are strings.

```json
{
  "document_id": "doc_…",
  "ship_ready": false,
  "currency": "EUR",
  "payment": {
    "policy": "prepayment",
    "required": "500.0000",
    "received": "0.0000",
    "remaining": "500.0000",
    "payment_term_id": "ptm_…",
    "invoice_ids": ["doc_…"],
    "allocation_ids": []
  },
  "blocking_reasons": ["prepayment_required"],
  "blockers": [
    {
      "code": "prepayment_required",
      "detail": "500.0000 EUR is required; 0.0000 EUR is allocated.",
      "links": [{"kind": "payment_term", "id": "ptm_…"}]
    }
  ],
  "lines": [],
  "basis": {},
  "links": []
}
```

Stable payment blocker codes:

- `prepayment_invoice_missing`: payment cannot be attributed because no posted order-backed
  receivable exists.
- `prepayment_attribution_ambiguous`: invoice evidence maps to more than one order and cannot be
  allocated to this order without a decision.
- `prepayment_required`: qualifying allocated money is below the stated order amount.

Existing stock, reservation, commitment, party-hold and commitment-hold codes remain canonical.

## Dispatch preparation

Preparation validates the complete current readiness for every customer-delivery movement. When
blocked it creates no proposal and returns the shared blocker result. When ready, the persisted
review includes:

```json
{
  "version": 2,
  "tool": "shipment_dispatch",
  "intent": {},
  "effect": {"shipment_action": "shipment_dispatch"},
  "state": {
    "counterparty": {},
    "movement_previews": [],
    "fulfillment_readiness": []
  },
  "token": "sha256(tenant, tool, intent, state)"
}
```

Confirmation recomputes the same state. A mismatch refuses as stale before effect. A current
readiness blocker refuses before effect even if a malformed legacy proposal lacks the version-2
state.

## Terminal proposal failure

A deterministic effect-free execution refusal returns the original business error to the caller
and persists:

```json
{
  "status": "failed",
  "receipt": {
    "business_effect": "none",
    "error": {"code": "…", "type": "InvalidOperation", "message": "…"},
    "safe_next_action": "correct_input_or_prepare_new_proposal"
  },
  "verification": "verified_no_effect"
}
```

Unexpected outcome uncertainty remains `executing` with `verification: unresolved`.
