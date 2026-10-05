# Verification evidence

Base: `main` at `b7a1f16e`; implementation: `feat/default-operational-cases`.
Specification and handoff imported from `feat/company-reference-simulator`.

- Test-first proof: ordinary default acceptance, no-owner discovery, rollout persistence
  and public internal-job refusal all failed before implementation (four failures).
- PostgreSQL case/guard/adapter/migration/tenant-isolation checks: 91 passed. Covers
  canonical acceptance, partial/closed history, raw Sources, rollback/retry, concurrent
  backfill/intake, old manual revisions/bindings/unknown execution, exact handback,
  missing migration, downgrade refusal, exhausted leases and revoked historical owner.
- Canonical-order compatibility checks: 2 passed; automatic serial reservations and
  Copilot approval still require supported order anchors and exact confirmed work.
  Manual orders without a Source have no interpreted Shopify refunds.
- Operational-cases Playwright proof passed: no enable control, incomplete rollout
  status, confirmation, takeover retry, provenance, exact handback and direct discovery.
- `make lint`, `make spec-check` (also against `origin/main`),
  `make business-annotations-check` passed (649 described functions, 115 described tests,
  zero missing root functions or approved tests).
- `make web-build` passed: formatting, executable contracts, localization audits,
  TypeScript and production build.
- `make docs-build` passed: 16 Python reference tests, 145 Node contracts, formatting,
  generated reference and production documentation build.
- `make docs-catalog-check` and `git diff --check` passed.

Full backend (6,490 collected tests), full fixture browser suite (87 scripts) and PR
CI are running. T011 and complete acceptance remain unchecked until assessed.
The local browser harness maps existing macOS `/private/tmp` screenshot paths to
`/tmp`; it changes only local artifact paths, not assertions or product code.

Simulator runtime remains on its separate branch. The imported integration regression
explicitly skips when `reality.services.live_company` is absent. External-runner and
multi-day capacity gates remain pending; no production rollout is claimed.
