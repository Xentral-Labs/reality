# Tasks: Choose how the first company starts

1. Service tests first: both starts, receipt content, replay, conflicting retry,
   eligibility, and a Demo Data connection after an empty start.
2. Extend `free_playground.enter` with the closed `content` choice and its company
   name and live-simulation rule.
3. Extend the account-scoped playground adapter body with the same closed literal.
4. Replace the automatic request in `unified/FreePlayground.tsx` with the two-card
   start screen; keep progress, failure, retry and handover behaviour.
5. Add the card strings to all four languages; extend the free playground browser
   script to cover both starts and a narrow viewport.
6. Run the focused suites, the web checks and the full PostgreSQL pytest run; record
   verification.
