# Plan: Inbox decision badge

Add `apps/web/src/unified/pendingDecisions.ts` with a `usePendingDecisions(tenant)` hook that reads `api.changeProposals(tenant, "pending", 1, "", 1)` and returns `page.total`. It refreshes on tenant change, on `visibilitychange`, every 60 s while the document is visible and on a `reality:decisions-changed` window event. `api.ts` dispatches that event after approve, reject, review-token confirm and chat messages settle. `Shell.tsx` renders the count as a badge on the Inbox entry, describes it for assistive technology, and places the same count after the Decisions tab while another Inbox tab is open. `dailyWork.ts` holds the pure `decisionBadge` text rule.

## Constitution Check
PASS: no business rule, schema, service, tool, API or MCP change. The badge reads the existing shared count that the Decisions register already uses (Web UI invariant: operational pages use shared services). Tenant scope is enforced by the existing endpoint. No exceptions.

## Verification and rollback
New fixture-driven browser script covers zero, three, 99+, refresh after approval, company switch and collapsed rail in en/de. Run `npm run format:check`, `npm run build`, i18n audit, spec policy, and a live check against the local API. Revert the commit to roll back; no migration.
