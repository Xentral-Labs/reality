# Research

Decision: preserve one new payment fully allocated to one selected invoice; allow partial payment.
Independent read-only research confirmed customer cash debit/AR credit and supplier AP debit/cash
credit, positive stated amount limited by current open amount, and atomic allocation.
Alternative arbitrary allocation of old unallocated payments is a distinct future workflow.

Decision: use the existing attributed document.recorded, ledger.posted and settlement.allocated
chain plus immutable original rows. These contain exact payment document snapshot, ordered
posting IDs/accounts/amounts and selected invoice-control linkage. Reconstruct the existing
ledger-only receipt; no new event is necessary. Explicit supplied time/source are checked;
execution-time defaults do not make tokens unstable. Later reversal leaves historical proof.

Decision: preserve optional payment source rather than inventing one or borrowing invoice source.
Source absence is exposed honestly. Require sales_invoice for customer payment in shared
validation, matching supplier type restriction. Shared mutation locking prevents stale competing
payment/allocation capacity. Existing refund and practice policies retain their semantics.
