# Verification evidence

## Scope and review
Owner approved finance measures and calendar dates as the next step. No migration,
new business authority, write action or external deployment. Earlier spec228/229 work
is preserved on main. Review confirms canonical aging/settlement services supply all
remaining amounts; graph SQL only joins and aggregates ephemeral typed results.

Finance balances are explicitly current customer/supplier debt positions. Unused
credits and net party balances are not substituted. Existing ambiguous party measure
continues to refuse. The service adapter has a 20,000-document refusal boundary,
exact numeric JSON strings, tenant-scoped identity joins and measured read counts.

## Automated results
- New finance/date regressions: 8 passed, including partial payment, payment/invoice
  reversal, original opening due dates, currencies, tenant isolation, derivation bound,
  signed ledger amounts, malformed/leap dates and chat validation.
- Reporting, builder and relevant finance regression run: 246 passed before the last
  four additional finance tests; full suite final evidence follows below.
- Web contracts: 266 passed after final preview formatting change.
- Calendar/builder tests under America/Los_Angeles: 30 passed.
- Web production build, format check, four-language audit, Ruff, spec policy and
  whitespace checks passed. Existing Vite large-chunk advisory remains.
- Catalog reference generation completed through the underlying Python command
  (make is unavailable because this machine has not accepted the Xcode license).

## Chrome inspection
Native Chrome showed 57 objects / 182 relationships. Customer financial positions
loaded five real preview records, including EUR and USD, then opened in Analysis.
Document and due dates display as calendar days without the prior 02:00 suffix.
The existing question frame, shared controls and canonical dates remained visible.
No report was saved and no chat message or business mutation was sent.

## Final suite
Complete backend suite: **2,847 passed, 9 skipped**, 709.70 seconds.
One pre-existing SQLAlchemy transaction-cleanup warning in storyline API tests.
Log: `/tmp/reality-finance-full-backend.log`.

Final review: all FR-001–005 acceptance families are green. No schema changes, no
second settlement computation, no persisted derivation, no tenant/currency bypass.
All implementation tasks complete locally on main. Nothing committed or pushed.
