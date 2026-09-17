# Stable refresh feedback verification — 2026-09-17

Scope: owner-requested correction to FR-009. No service, scheduling or schema changes.

Pre-implementation review: FR-009 refinement maps to T032–T034; FR-007 translations
map to T033–T034. No uncovered refinement requirements, unresolved clarifications,
constitutional conflicts or critical findings. Existing feature 180 artifacts were
reviewed directly because the prerequisite helper selected current feature 220.

The updated browser test first failed on the previous changing button label
(`Updating…` instead of `Refresh`). It passes after implementation for delayed reads,
newer/unchanged results, repeated fast reads at 1440px and 390px, failed calculation
metadata, failed HTTP reads (both dropped and retained metadata), retry recovery,
and English/German/Dutch/Spanish. Button and notice bounding boxes stay identical
across repeated reads. Desktop/mobile screenshots were visually inspected.

Checks:
- Projection freshness browser regression: PASS.
- Frontend contract suite: 219 passed, zero failed.
- Production build (TypeScript and Vite): PASS; existing large-chunk advisory remains.
- i18n audit: all four languages PASS, 1897 entries each.
- Prettier for every changed frontend file: PASS.
- Spec policy: PASS via `python3 scripts/check_spec_policy.py`. The `make` wrapper
  cannot run on this machine until its Xcode license is accepted; the exact target
  command was executed directly.
- `git diff --check`: PASS.

Final review: guarded disabled state prevents duplicate refresh, immediate aria-busy
reports the read, and the initial implementation delayed checking text by 300 ms with timer cleanup
(superseded by the owner-requested spinner below). Fixed
button text and reserved localized feedback geometry prevent notice shifts. Errors
cannot be reported as successful unchanged/updated reads. Underlying calculation
failure is still reported truthfully; no background calculation is initiated.

## Owner-requested minimum spinner
FR-009 refinement maps to T035–T037; no new constitutional conflicts or unresolved
requirements. Small reserved indicator, immediate busy state, 1000 ms minimum
feedback, longer for slow reads, guarded disabled control and reduced-motion support.
No data response is artificially delayed. Timer cleanup runs on unmount.
The regression first failed because no spinner was visible. Browser checks then
passed minimum duration, stable desktop/mobile geometry and reduced motion.
Production build and frontend contracts passed. The temporarily reported localization
findings in concurrently edited ProjectionDataDialog.tsx were resolved externally;
the complete four-language audit is now green.

## Compact timestamp and action
The owner's follow-up removes visible outcome copy and places the timestamp beside
Refresh. FR-009 maps to T038, retaining T035–T037 spinner tests. Artifact review finds
no conflicting requirements or constitutional issues. No additional business scope.
The browser test first failed on the missing adjacent timestamp selector, then passed
with a 12px desktop gap, a screen-reader-only feedback element, stable repeated-read
geometry at 1440px/390px, minimum spinner duration, errors, retries and reduced motion.
Desktop and mobile screenshots were inspected. The failed-calculation state and
backlog remain visible; the extra unchanged/checking result line is absent.
Build, i18n audit, spec policy and changed-file formatting pass.

Final frontend contract rerun: 219 passed, zero failed. All required checks are green.

## Persistent refresh affordance
Owner-approved refinement keeps the icon visible in every state. FR-009 maps to
T039–T040; no new scope, unclear requirements or constitutional conflicts. Existing
read/confirmation/tenant semantics stay unchanged. The browser test first failed on
an invisible idle icon. Implementation uses the existing Lucide RefreshCw and shared
button styling; animation stops in idle and under reduced motion.

Final checks: browser PASS for visible idle/completed icon, busy rotation, keyboard
Enter activation, retained focus, rejected repeated Enter/programmatic clicks,
minimum one-second feedback, desktop/mobile geometry and reduced motion. The native
disabled button lost keyboard focus in the regression; aria-disabled plus the action
guard fixes this while preventing repeat reads. Production build, all four language
audits, 219 frontend contract tests, formatting, spec policy and diff checks PASS.
No schema/service changes or new dependencies.
