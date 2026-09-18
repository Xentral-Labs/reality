# Home activity and readiness

Authority: [spec 149](../../specs/149-home-live-status/spec.md).

Home reads the existing tenant timeline with `hours=0&limit=20`, newest recorded
sequence first. Timestamps are recording times, not claims about when an upstream
business event occurred. Every row opens the existing event Inspector. Full history
uses the Activity drawer. Visible Home polls every ten seconds; stale events remain
visible with a notice. Refresh does not authorize any business mutation.

`GET /api/tenants/{tenant_id}/readiness` requires normal company admission and calls
`services.system_readiness.readiness`. A scoped tenant read proves API/database
connectivity. Background roles are independently verified through configured private
HTTP probes. Results are `ready`, `unknown` (not configured), or `unavailable`.
Only three positive results produce the combined ready status. This is availability,
not proof that every business action or external integration succeeded.

Continuous scheduler and worker commands optionally start an in-memory health server
when `REALITY_BACKGROUND_HEALTH_PORT` is set. `/healthz` returns role, status and age
of the last successful sweep. Idle successful sweeps count; starting, failed, stopped
or more than 90 seconds old do not. Reads never execute jobs or persist health facts.
One-shot commands do not start a server. No migration is needed.

Compose enables private port 8081 for each background container and configures API
`REALITY_SCHEDULER_HEALTH_URL=http://scheduler:8081/healthz` and
`REALITY_WORKER_HEALTH_URL=http://worker:8081/healthz`. No host port is published.
For Railway or another container host, use the deployed services' private DNS names
and the same port. IPv6 dual-stack binding is used when supported. These URLs are
operator configuration, never user input; probes have a 0.75-second socket timeout,
4096-byte payload limit, no redirects and no ambient proxy. Never expose credentials
or health URLs in browser responses. Without background configuration Home reports
unknown. Rollback: remove health-port/URL environment variables and revert Home UI;
existing scheduling and stored data are unaffected.

Implementation: `jobs/health.py`, `jobs/runtime.py`, `services/system_readiness.py`,
`web/api.py`, `HomePulse.tsx`. Tests: `test_home_readiness.py` and
`apps/web/scripts/home-live-browser.mjs`.

Home aborts pending activity/readiness reads after eight seconds and on unmount.
A stalled request therefore marks the last activity stale and clears positive readiness;
it cannot indefinitely block subsequent refreshes.

## Rolling activity graph (FR-008–011)

The Home graph supersedes the default recent-event list. It displays a rolling
24-hour,7-day or30-day window (default30days), refreshing every10seconds. Source
buckets are UTC-aligned30-minute intervals. The display sums adjacent buckets when
needed for its width (at most24hours per displayed bar), and labels the actual
resolution. The right edge tracks time even when there is no new activity.

`GET /api/tenants/{tenant_id}/activity-volume?days=30` calls
`services.activity_volume.volume`; supported days are1,7,30. Complete SQL aggregates
count first recorded occurrences of distinct subject identities in four categories:
`document.recorded` for sales/purchase orders, other recorded documents,
`reservation.created` and `movement.recorded`. Source/processing/commitment events
are excluded, so an imported order is not multiplied by its processing steps.
Deduplication precedes time filtering so a repeated event cannot reappear in a
later range or drilldown. These are counts of recorded entities, not quantities,
revenue, shipments, successful jobs or third-party completeness claims.

Coverage starts at the company's creation; pre-company time is hatched. The current
bucket is partial. On failure the last graph remains, marked stale; time after the
last successful observation is unknown, never automatically filled with zeros.
Newly imported historical documents produce recording activity at import time;
business dates are not substituted for recording timestamps.

`GET /api/tenants/{tenant_id}/activity-volume/events?start=...&end=...` uses the same
classification and deduplication for an explicitly zoned half-open interval of at
most one day. It returns latest50 matching event identities, total and has_more.
Each opens the existing event Inspector. Full history remains in Activity. Both
reads retain normal tenant admission, require no schema or writes and expose no
new mutation permissions. Tests: `test_activity_volume.py`, `home-live-browser.mjs`.

## Inbox Welcome placement (spec 225 FR-017–018)

The former Home surface now lives in Inbox's first tab, Welcome, at the same /app
landing URL. Company activity is its first content, followed by the three existing
operational queue counts. The activity implementation and its loading, polling,
readiness, period preferences and inspector links are unchanged. There is no separate
Home sidebar entry.
