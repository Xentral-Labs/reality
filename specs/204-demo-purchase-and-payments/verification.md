# Verification

## Completed checks

- The scenario tests failed first for the stated reason — `Counter({'open': 24})` for
  the settlement states and three purchase orders where six were expected — then passed.
- The permitted operations were found by probing, not by guessing, and the probe
  corrected two assumptions from the plan:
  - `post_customer_payment` is denied under the name `record_customer_payment`, which is
    what it calls internally, and both it and `post_supplier_payment` also need
    `allocate_settlement`.
  - `record_supplier_invoice` commits inside itself, which the profile scope rightly
    refuses ("Profile operation must commit atomically"). The supplier invoice is
    therefore built the way the sales invoice already is, with
    `create_manual_document_with_lines` and `post_supplier_invoice`, and that shared
    billing service is left untouched.
- A first draft measured the seeded outstanding with `account_balance` on the invoice,
  which reads the document's own ledger entries and therefore never sees a payment: the
  states all read "open". `open_invoice_amount` is the read Finance uses, and both the
  seed and the assertions use it now, so a credit note correctly reduces what a payment
  has to settle.
- Final distribution: 15 sales invoices settled, 4 carrying a residual, 5 untouched, 19
  customer payments; six purchase orders across three suppliers with payables settled,
  partly settled and untouched; received quantities 2, 0 and four times 5.
- Focused profile, company setup, execution fixture, demo data intake and free
  playground suites: 52 passed.
- Lint, format and spec coverage policy passed.

## Completion

Full PostgreSQL suite: 2570 passed, 9 skipped in 9:08.

Seed cost, measured on a quiet machine before and after: 2,83 s and 6.455 statements
become 3,6 s and 9.238 statements, for 27 more documents. That stays well inside the
worker's 30-second handler budget.

One measurement trap worth recording: the first readings were taken while a full suite
ran in the background and reported 10–20 s, which looked like a regression until the
unchanged baseline measured 25,9 s under the same load. Performance numbers here are
only meaningful on an otherwise idle machine.
