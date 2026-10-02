# Data Model

Reuse `Document` (`dunning_fee_charge`, `payment_return_fee_charge`), `SourceRecord`, existing receivable `LedgerEntry`, `SettlementAllocation` and reversal records. No new tables, columns or authoritative derived balances.

Fee open-item origin is `fee`; source and control posting identities remain unchanged. Due date is only the fee document's stated maturity, with no inherited discount or payment term. Amount/status are effective read-time settlement observations.
