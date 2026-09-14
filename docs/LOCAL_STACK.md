# Local application stack

The local app on port 8080 is built from
`.claude/worktrees/invoice-lines-research`, based on `acab690`, with the reviewed
company-setup/demo/scheduler changes and the company-card clarity refinement.
The root checkout retains the earlier implementation and unrelated work; it is
not the build context for the combined running application.

From the root repository, use:

```sh
cd .claude/worktrees/invoice-lines-research
docker compose --env-file $(pwd)/.env -p reality -f compose.yml --profile background build api migrate web mcp invitation-worker scheduler worker
```

The selected database migration head is `0047_merge_demo_lot_expiry`. It joins
`0045_lot_expiry` and the additive scheduled-jobs/company-setup branch without
rewriting either migration or existing business facts. Apply migrations once using
the matching `migrate` image; neither scheduler nor worker migrates on startup.
After successful migration, the selected runtime services are `api`, `web`, `mcp`,
`invitation-worker`, `scheduler` and `worker`. Do not restart or recreate PostgreSQL
or object-storage volumes merely to update application code.

The `background` profile is required for the scheduler and worker. A live demo starts
only after explicit company-creation consent or source Start. Manual connection alone
remains stopped. Keep all services on the matching combined core.

A private local PostgreSQL backup was taken before rollout. A restored-database
rehearsal verified all existing rows in 62 tables, including 38 tenants, unchanged;
only four infrastructure tables were added. Final results are recorded in spec 146's
quickstart in the active worktree. No remote system is part of this deployment.

## Verified local rollout — 2026-09-09

The additive migration and runtime update completed locally. The pre/post migration
comparison preserved every existing row in 62 tables and all 38 tenants. The active
revision is `0047_merge_demo_lot_expiry`. API and MCP report healthy; web, invitation
worker, scheduler and worker are running with zero restarts. Both background loops
report successful idle sweeps. No demo company or job was created by deployment.

Port 8080 serves `index-Dtjnimpw.js` and `index-DuoEnMnM.css`, matching the combined
web build. API health returns 200; unauthenticated setup-options access returns 401
and the deployed creation schema includes live simulation.

To update the same services after a successful matching migration:

```sh
docker compose --env-file $(pwd)/.env -p reality -f compose.yml --profile background up -d --no-deps api mcp invitation-worker scheduler worker web
```

FR-023 subsequently updated the local web build with one goal-based creation choice (own company, empty Sandbox, demo data) and demo-only live simulation. The asset hashes above describe the preceding rollout; the current web build supersedes them. Backend/migration/process configuration is unchanged. See active spec 146 quickstart for verification.

The subsequent FR-026–029 rollout adds read-only Sandbox Reports, chronological live
import snapshots and the standalone `/app/demo-data` page. Demo Data appears below
Companies for demo/source-enabled companies. The wide Sandbox banner is replaced
by a header badge. Matching local API/MCP/background/web images were updated without
a schema migration; the existing live source continued. Verification is recorded in
the active spec 146 quickstart. Earlier asset hashes are historical.

Spec149 Home activity/readiness is now verified and running in the active worktree
stack on port8080. Home polls real activity and private process health every ten
seconds. See active `docs/features/home-live-status.md` and
`specs/149-home-live-status/quickstart.md` for configuration and evidence.
No schema migration or data reset was needed for this update.

Spec149 FR-008–011 now replaces the Home event list with the rolling activity graph
(24hours/7days/30days,30-minute source buckets, responsive aggregation and event
drilldown). Read `docs/features/home-live-status.md` in the active worktree for
count/coverage semantics. Local8080 verification is in spec149 quickstart.


2026-09-09 hover-summary web update: local web uses `reality-web:hover-summary-20260909`, built from the isolated `/private/tmp/reality-hover-release` source copy and deployed with its `compose.hover.json` override. Verified 8080 assets: `index-BHh9axz-.js`, `index-BBt5dvwI.css`. API, scheduler, worker and data were not changed. The image passed all 16 hover-height browser combinations.

2026-09-09 activity range update: web now uses `reality-web:activity-range-20260909` with `/private/tmp/reality-range-release/compose.range.json`. Port 8080 verified assets: `index-BoeiTI5R.js`, `index-BBt5dvwI.css`. Default 24 hours; range remembered per user in the browser. API/background/data unchanged.
