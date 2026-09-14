# Research
Read-only research delegated under the plan skill to order_research; findings consolidated before implementation.
- Decision: Extend the existing payment review/proof engine with an explicit refund variant. Rationale: identical two-entry receipt and document.recorded/ledger.posted/settlement.allocated evidence. Alternative: independent copied backend would duplicate recovery rules.
- Decision: Preview canonical credit_note_id/refund_number through a normalized internal settlement descriptor, preserving public tool arguments. Rationale: compatibility with PlaygroundRefundInput and existing CLI/API. Alternative: renaming public fields breaks existing callers.
- Decision: Lock before refund reads and snapshot allocations on either endpoint. Rationale: credit-to-invoice netting consumes the same credit as refunds and may use its payment endpoint. Alternative: only invoice-side allocations miss state identity changes.
- Decision: Keep optional original source absent when none supplied, consistent with payment recording; confirmed action and emitted immutable evidence preserve operator intent. No invented upstream payload.
- Decision: Separate refund form wording from payment direction while sharing proposal/recovery services. Existing reversal effects already show the reopened credit; no invented transfer state.
All technical unknowns resolved; no schema or constitutional exception.
