# Plan: Home activity and readiness

Reuse timeline(limit=20,hours=0), existing event titles/context and Inspector/Activity drawer. Add a Home pulse component; visibility-aware single-flight polling independently settles timeline/readiness. Plain-language component statuses; failed readiness clears green presentation. Existing dashboard business calculations are unchanged.

Add jobs/health.py: in-memory loop freshness plus optional small HTTP health server, dual-stack where supported; only /healthz, sanitized role/status/age. ProcessLoop.run starts it only for continuous mode with REALITY_BACKGROUND_HEALTH_PORT, marks successful/failed sweeps, shuts it down on exit. Default90-second freshness safely exceeds bounded25-second sweep plus30-second child timeout and max30-second poll. No migration/job execution from probe.

services/system_readiness.py combines scoped tenant existence/database read with two configured private probes (0.75s each, max4096 bytes, no redirects/proxy). No probes for missing configuration; state unknown. HTTP role and freshness must match. Web /api/tenants/{tenant_id}/readiness uses existing tenant admission. Add API_URLs in Compose and health-port environment in scheduler/worker; no host port or Docker socket needed. Document Railway private DNS overrides. Runtime probe is opt-in, preserving CLI/container defaults.

## Constitution Check
All principles PASS: no new business persistence, source facts unchanged, tenant admission retained, shared read services, no mutations or new scheduling authority, pure readiness observations and proportional executable proof.

## Tests and rollback
Unit clock/failure/role/config/redaction tests; actual optional HTTP probe and scoped API tests; existing runtime and complete backend suite. Browser advancing event fixtures, stale health, hidden tab, company change, details links and localized responsive screenshots. Build all matching roles; verify running private endpoints and Home API without stopping user work. Rollback disables probe env vars/URLs and restores web/API images; no migration.

Home requests use an eight-second abort deadline and abort on unmount, so a stalled
network cannot indefinitely preserve an old positive status or block future polls.

## Graph refinement plan and review
Domain meaning: four explicitly named recorded-entity categories. Shared
`services/activity_volume.py` derives canonical classification from existing events
and same-tenant Document.type. SQL deduplicates category/subject identity at first
recording within the window and aggregates30-minute UTC buckets, bounded to1441.
Coverage begins at Tenant.created_at; no new tables. Detail reads use the same query
and return at most50 matching event identities plus truncation. HTTP adapters keep
the normal company admission dependency. No new mutation authority.
Frontend replaces the Home list with an SVG time chart, responsive grouping,
keyboard/pointer interval selection and event Inspector; readiness is compact.
Time axis follows clock; fetched coverage ends at observation time. Unknown gaps
are visually distinct from measured zero. Existing8second request deadline retained.
Tests before service: category exclusion/deduplication, bucket boundaries, ranges,
foreign tenant, gap coverage and detail identity. Browser: range switching, live
advance, outages, old-company responses, width/theme/language, no writes and drilldown.
Constitution Check: PASS throughout; no schema, scope or business-authority expansion.
Approved scope is unambiguous; no critical analysis finding. Existing ignore files
already cover build, credentials and dependencies. Rollback restores previous images.

Hover stability: overlay hint and detail in one CSS grid cell, retaining inactive
layout space with visibility:hidden and aria-hidden. Reserve the maximum current
category values for stable wrapping. No API/counting changes. Browser asserts box
height at rest, first/last hover and leave in all16 presentation combinations.
Constitution PASS; no open clarification or critical finding for this UI correction.


Range preference plan: pass authenticated opaque user ID from UnifiedApp through HomePage to HomePulse. Lazy-load a validated localStorage preference keyed by user; write only on explicit range selection, catching unavailable storage. Reset on user identity change. No API/schema/business changes. Browser regression proves new-user 24h, reload and company persistence, user isolation, invalid storage and blocked storage; retain existing graph checks. Constitution Check PASS. Scope reviewed against user instruction; FR-008/012 and task T010 are consistent, no unresolved or critical analysis findings. Rollback restores web image.


## Naming refinement (FR-013–014)
Adapter-only change: shared daily-work category/selection definitions used by Shell
and HomePage; add commitments below Home, localized labels and an open qualifier.
Keep existing dashboard totals and customer-delivery scope. Use the same selection
for link href and click; distinguish the commitments shortcut's active state from
the general workspace. Update localization and durable Web contract.
Constitution Check: all principles PASS; no domain/service/tool/schema changes.
Verification: existing frontend contract suite, build, localization audit, spec gate;
review shared selections for stale filters and tenant preservation. No new tests for
this reversible presentation change; existing route tests cover selection serialization.
Rollback: revert these adapter changes and rebuild the local web image only.

FR-015 Constitution PASS: remove the alternate Home loading tree. Render stable cards with shared ReadLine placeholders; keep HomePulse mounted and show dashboard errors after it. Test a deliberately delayed dashboard and assert activity vertical position stays unchanged. Verify frontend build/contracts and browser checks. Analysis: requirements resolved, no critical findings.
