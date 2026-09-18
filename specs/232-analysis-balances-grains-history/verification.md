# Verification and final review

## Evidence
- Complete backend run: 2,874 passed, nine skipped; two generic catalog probes failed
  because they did not supply the newly mandatory snapshot input. One pre-existing
  SQLAlchemy transaction warning remains. Log: `/tmp/reality-positions-full.log`.
- Corrected those probes to supply explicit date inputs from catalog metadata, without
  weakening runtime validation. All expansion coverage and final history regressions:
  **49 passed**, including every table node and structural edge in both directions.
  Log: `/tmp/reality-positions-final-coverage.log`.
- Final builder/history/declaration/traversal group: **116 passed** before the additional
  stock-compensation regression, which passed in the 49-test run above.
  Log: `/tmp/reality-positions-final-target.log`.
- Web contracts: **268 passed**; TypeScript/Vite production build, Prettier, and all four
  language audits passed. The existing bundle-size advisory remains unchanged.
- Ruff, specification policy and whitespace checks passed. Generated catalog reference
  is reproducible; all four reference-generator unit tests passed.
- Native Chrome: customer balance template returned 16 rows with separate EUR/USD
  currencies, unused credit and negative net values. Historical templates initially
  disabled adoption without a date. Calendar selection enabled adoption; historical
  stock returned 16 rows with the selected date visible in the sentence. The Cypher
  surface retained `snapshot_date = $value1`. No chat message, report save or business
  mutation was made during verification.

## Review
- No persisted derivation, schema migration or business-write path added.
- Canonical settlement cutoffs include posting time, allocation time, both allocation
  endpoints and reversal time. Current readers retain their default behavior.
- Native Decimal values, opaque position identities, backing anchors, currency/unit
  separation and ordinary fanout protection remain intact. Source families are bounded
  before materialization, including payment terms used by current aging.
- Exact null tracking buckets and shared movement-leg arithmetic conserve stock;
  retained compensations do not rewrite earlier physical-stock snapshots.
- Explicit end-of-UTC-day cutoffs survive templates, sentence editing, Cypher and chat
  validation. Pre-opening and unsupported histories are refused.
- Current names/units are not claimed as historical metadata. Historical reservations,
  availability, due/overdue terms and knowledge-time reconstruction remain unavailable.
- Final declaration: 64 objects, 189 relationships, 412 fields and 21 templates.
- No unresolved implementation or verification finding. No commit, push or deployment.
