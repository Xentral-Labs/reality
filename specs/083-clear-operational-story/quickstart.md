# Validation

## Closing agent-context chapter

Added chapter 11 in both locales, linked from the sidebar, overview and preceding chapter.
Read the inventory, finance, changes, lifecycle, views and approvals chapters and the current
timeline service before drafting. Inventory reconciles as 20 + 22 - 12 - 30 = 0;
the financial example leaves 1,470 - 500 - 100 = 870. Assigning that invoice to Huber is
explicitly an illustrative evidence-link assumption, not an inferred production relationship.
Alternative cases are excluded from base totals. The page is not a live tool response or
an as-of reconstruction claim. The new contract failed before implementation; after updates,
all 42 docs tests, the VitePress build, spec policy and whitespace checks passed.
No browser visual acceptance is claimed; T012 remains pending.

## Inventory walkthrough write boundaries

Clarified sections 13–19 in both editions against create_manual_order, reserve,
_consume_reservations and movement recording. Explicit reservation writes, automatic
shipment consumption/remainder creation and derived balances are distinguished.
Receipts and subsequent allocation are separate actions; shortages do not create purchases.
The bilingual regression failed before edits. All 41 docs tests and the production build
passed; spec policy and diff whitespace passed. No backend behavior changed; no visual
browser review is claimed.

## Original documentation learning path restored

Owner requested restoring the original docs narrative with light clarification only.
Restored home, first product journey and first trace from baseline 658090d in English and
German. The 15/30/60-minute model/operator/integration progression is back; 60 minutes now
prepares a pilot rather than promising a working ERP connection. Original technical
positioning and navigation remain. Lamp example, source readiness and action boundaries
are supporting clarifications; other domain/rule corrections remain untouched.
The timed-path regression failed before restoration. All 40 docs tests and the VitePress
build passed. No visual browser verification is claimed; T012 remains open.

## Glossary clarification verification

Copy-only refinement under FR-005, FR-006 and FR-008; eight existing terms and layout retained.
The focused glossary contract failed on the missing SourceRecord explanation before edits.
After updating English and all three translations: 52 site tests passed, 433/433 strings
covered in every locale, production build and spec policy passed; diff whitespace clean.
No backend, documentation routes or business behavior changed. Visual browser acceptance
remains pending under T012; these checks do not claim a rendered layout review.

## Owner revision verification

The original technology-led landing and explanatory pages are restored with targeted copy and
domain-label improvements. CoreMap, system brands, context graph, capability progression and
finance graph remain. The simplified OperationalStory component and its layout CSS were removed;
they are recoverable from the first PR commit. The improved documentation remains unchanged.

- Site: 51 tests pass, including original-presentation preservation and refined-example checks.
- All 435 discovered interface strings are covered in en/de/nl/es; formatting and production build pass.
- Docs: full quality/build gate passes (39 tests, formatting, links and production build).
- Spec policy, Ruff and diff whitespace checks pass.
- Desktop/mobile visual acceptance is still pending; no new browser verification is claimed.
- The first-iteration evidence below is historical and does not describe the restored layout.

Run npm test, npm run i18n:audit and npm run build in provider-site.
Run npm test and npm run build in apps/docs. Run make spec-check and make lint at root.
Read / and /why-reality, follow the example to /getting-started/ and /getting-started/first-trace.
Confirm consistent lamp quantities, visible readiness and unknown-data boundaries. Inspect
desktop/mobile layouts and all language selections where a browser is available.

## Verification evidence — 2026-09-05

- Initial new contract checks failed before implementation: missing shared story, entry paths,
  missing-information guide and readiness wording.
- Site: 51 tests passed; format check passed; all 179 discovered interface strings covered in
  en/de/nl/es; TypeScript and Vite production build passed.
- Docs: 39 tests passed, including translated inventory/table parity and relative links;
  format check passed; VitePress production build and dead-link validation passed.
- Repository: make spec-check, make lint and git diff --check passed.
- Final review retained all published section anchors and verified configured-origin documentation
  routing (German edition; English fallback for Dutch/Spanish). No price, account or backend behavior changes.
- No connected browser is available (discovery returned an empty list). Desktop/mobile visual
  acceptance is still pending, not a passing check. Responsive grid and existing appearance
  contracts were checked in source/tests only.
- At implementation handoff, no deployment, commit, push or PR had been performed. Existing .claude/worktrees/ was untouched.
# Open-source closing-note revision

FR-010: the new contract failed on end-of-page placement before implementation.
Replaced the banner with a plain paragraph after the final CTA, before the shared footer.
Removed obsolete banner styles and translated the new sentence in German, Dutch and Spanish.
Site: 51 tests passed; all 433 strings covered in every locale; formatting and build passed.
Spec policy, Ruff and diff whitespace checks passed. No docs content or backend changes.
Source review confirms inline links and preserved core-technology sections. Desktop/mobile
visual acceptance remains pending under T012; no connected browser was available.
