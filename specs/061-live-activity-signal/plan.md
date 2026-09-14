# Implementation Plan: Live Activity Signal

## Summary

Add one tenant-scoped aggregate read over durable BusinessEvents and a small React polling hook. Use the existing timeline for detail and refresh it when the cursor advances.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Signal references existing immutable events only. | PASS |
| Reality authority | No document state or alternate event authority. | PASS |
| Proven schema | No migration or new field. | PASS |
| Tenant/service boundaries | Service query and tenant API router enforce scope. | PASS |
| Test evidence | Service/API/frontend proofs precede implementation. | PASS |
| Explainable Web | Activity remains the traceable detail surface. | PASS |
| Smallest design | Polling reuses sequence and avoids push infrastructure. | PASS |

## Technical Approach

- Add `activity_signal(session, tenant_id, after_sequence)` beside timeline services.
- Return only `latest_sequence`, `new_events`, and `attention_events`.
- Poll every 10 seconds in Product Web while `document.visibilityState === "visible"`.
- Establish a baseline before displaying unread state; reset it on tenant change and Activity entry.
- Pass the cursor to Timeline as a refresh dependency and render one `aria-live="polite"` attention toast.

No schema, migration, command, catalog, or persistence changes. Rollback removes the endpoint and presentation state.

## Test Strategy

Service/API tests prove cursor semantics, attention counts, empty tenants, isolation, and tenant-isolation catalog classification. Frontend structural contracts prove interval, visibility pause, baseline, badge/pulse, Activity reset/refresh, localized attention-only live region, and the unchanged canonical Activity boundary. Run focused tests, format, build, strict localization audit, spec check, and diff review.
