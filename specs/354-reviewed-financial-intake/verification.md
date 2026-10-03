# Verification checkpoint: explicit financial statement profiles

Implemented explicit customer-payment, supplier-payment and sales-invoice plans.
Bank-file and legacy automatic/demo interpreter cutover remain pending.

Preparation retains source-stated amounts, dates, currency, account identities,
order-line billing links and canonical defaults without financial writes. Exact
approval requires a current owner and applies evidence/postings/allocation through
the canonical services in the shared atomic intake transaction.

Observed PostgreSQL evidence:

- Initial failure-first proofs exposed unrelated-sibling staleness, substituted
  cash accounts and substituted document dates. They pass after binding relevant
  invoice/account/company-currency state and exact nested calls.
- Both independently reviewed payments settle through one actual queue run.
  Unrelated postings preserve a matched payment review; selected-invoice
  allocation changes refuse its complete combined unit without a new posting.
- Substituted posting document IDs refuse; retained receipts replay unchanged.
- A sales invoice prepares without evidence/postings, bills exact order lines,
  posts once and replays. An outgoing statement records the stated supplier
  payment without sending funds or executing a bank transfer.
- A failure-first default-visibility check passes after canonical business defaults
  are retained at preparation across shared intake effect kinds.
- Final shared admission subset: 49 passed in 14.50 seconds, with the already
  verified 500-order volume test deselected. The financial profile suite passed
  before the default addition; final catalog/profile verification follows.
- Existing finance regression block: 94 passed in 72.53 seconds, including payment
  intake, foreign currency, company currency, atomicity, accounts and reversals.

All remaining feature tasks and global PR gates stay open until verified.

Final catalog/refusal/file-admission block: 61 passed in 47.46 seconds.
