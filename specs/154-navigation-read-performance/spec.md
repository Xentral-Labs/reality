# Feature Specification: Navigation read performance

**Language**: English
**Status**: Approved scope — user requested continuation after the spec 153 optimization and authorized the remaining Orders/browser and Finance investigation.

## Context and Intent

### Problem
The delivery list receives its data in about 114 ms but the browser spends about 935 ms executing JavaScript before displaying it. The localization boundary repeatedly scans all dictionaries for each text node. Finance Payments takes about 4.2 seconds after intake because its totals trigger an unrelated full projection build. Journal reads directly but shares the expensive localization path.

### Scope
Preserve existing presentation and business results while eliminating repeated dictionary scans and unrelated payment projection refresh work.

### Non-Goals
No layout or label redesign, new business rules, schema, persistent cache, timer, stale-result window, journal backend rewrite or general capacity claim.

## User Scenarios & Testing

### US1 — See register results promptly (Priority: P1)
An operator sees the same labels, dates, original business text and actions with less browser delay.
**Independent test**: Compare every current translated dictionary value and unknown input against the previous first-match lookup; prove repeat lookups do not rescan dictionaries.
**Acceptance scenarios**:
1. Given every supported language, shared translations and missing text, when source text is resolved, then exact prior lookup semantics remain intact.
2. Given catalog additions during module initialization and repeated business values, when the page renders, then all catalog additions are visible and work/memory do not grow with repeated unknown values.

### US2 — Open payment history promptly (Priority: P1)
An operator sees current payment rows and complete filtered totals after intake or reversal without rebuilding unrelated views.
**Independent test**: Compare payment projection output with canonical payment rows and prove unrelated checkpoints are not refreshed.
**Acceptance scenarios**:
1. Given new events, when payment totals refresh, then only the payment projection refreshes; page bounds, filters, currency grouping and reversal behavior stay unchanged.
2. Given no payments or another tenant, when read, then totals and rows remain empty/scoped without foreign effects.

### Edge Cases
Duplicate translated values across keys/languages, blank strings, untranslated business values, language switching, late module-initialization additions, empty payments, partial allocations, reversal, missing tenant and cold/warm cache.

## Requirements

- **FR-001**: Source-text resolution MUST preserve the prior first-match dictionary/key order, unknown-value fallback and all supported-language outputs while avoiding dictionary rescans after initial lookup.
- **FR-002**: Optimization MUST preserve the original-content DOM boundary and dynamic/language-change behavior; retained lookup data MUST be bounded by catalog entries, not business values.
- **FR-003**: Payment projection refresh MUST use canonical payment derivation and event invalidation while leaving unrelated checkpoints untouched and retaining explicit full-refresh compatibility.
- **FR-004**: Payment rows, filters, complete currency-separated totals, reversal semantics and tenant isolation MUST remain unchanged.
- **FR-005**: Tests MUST prove lookup parity/bounded scans and payment freshness/isolation/parity; repeat local browser measurements MUST report primary-response and frame timing separately.

## Success Criteria

- **SC-001**: Local delivery-list response-to-frame delay falls at least 50% from the observed 977 ms baseline in two repeat navigations; this is a local observation, not an SLA.
- **SC-002**: Local payment primary-response time after intake falls at least 50% from 4,190 ms; empty and populated payment fixtures retain equal results.
- **SC-003**: Required backend/frontend and specification gates pass with no intended business or presentation difference.

## Assumptions and Dependencies

Depends on spec 153 selective refresh and existing immutable-at-runtime localization catalogs. Catalog assignments complete before the first rendered lookup. No new localization source or runtime catalog-editing feature is introduced. The local live-demo stack stays active and its unrelated changes are preserved. The user accepted this bounded follow-up; no unresolved product clarification remains.

## Requirement Traceability

| Requirement | Scenario | Proof |
|---|---|---|
| FR-001–002 | US1.1–2 | localization-contract.test.mjs; T002–003 |
| FR-003–004 | US2.1–2 | test_payment_projection_performance.py; T004–005 |
| FR-005, SC-001–003 | Both stories | full gates and local timing in quickstart.md; T006–007 |
