# Plan
FR-013/T014: add shared timeline business counts/context and exact document-linked
sales/purchasing area predicates; retain old fields/defaults for other consumers.
No schema change. Translate presentation keys in a history helper, format received
quantities/amounts and deduplicate context; never parse English prose or derive state.
Replace technical default filter with business areas and keep event mode in disclosure.
History-only inspector mode renders business metrics/guidance and hides technical
trail/raw payload. Existing relationship traversal remains exact; no invented stages.
Tests first: shared area/count/context regression plus frontend/browser; targeted
backend event/API tests, frontend/build/audit/format/spec gates. Owner approved,
Constitution PASS; analysis finds no unresolved clarification or critical findings.
Rollback additive projection fields and history UI; no persisted data affected.
FR-002/003 refinement T013: replace count buttons with a semantic definition list,
small Data overview heading and native keyboard-operable info disclosures. Preserve
server totals and dropdown filtering; relocate grouping caveat beside Transactions.
Owner approved; Constitution PASS, no schema/service change or critical finding.
Test non-interactive totals, both disclosures and unchanged filtering; verify web
contracts, build, localization, format, spec and synthetic browser journey.
FR-012/T012: Remove redundant inventory captions and generic explainer. Review other
central registers; preserve their meaningful filter/partial-history information.
Owner approved; Constitution PASS, no unresolved clarification or critical finding.
Test absence before markup removal, run contracts/build/spec checks. UI-only rollback.
FR-011/T011: Introduce SearchField.tsx for OpenWork, OpenItems, Documents and
BusinessHistory. Scope icon, padding, 34px height, focus and wrapping CSS to the
cockpit. Preserve input callbacks and native history form submission. Add explicit
outlined settled toggle with check indicator. Test shared usage and browser geometry,
filter state/request semantics, search results and both themes. Owner approved;
Constitution PASS, no unresolved clarification or critical coverage finding. Rollback
is UI-only; verify contracts/build/audit/format/spec and browser before completion.
FR-010/T010: Presentation-only TableDetails component and scoped row-action CSS;
normalize inventory, master data, documents, open items and delivery tables. Keep
delivery native disclosure and all existing callbacks. Add regression assertions
for rightmost actions, matching Details styles and preserved inspection journeys.
Constitution PASS; user-approved scope, no unresolved questions or critical findings.
No schema/API changes. Rollback only component/markup/CSS. Web contracts, browser,
build, localization, formatting and spec policy required before completion.

FR-009/T009: Add Documents.tsx using existing api.documents and shared RegisterState.
Export the existing RecordRelations renderer with a narrow subject-reference prop,
retaining event evidence for history consumers. Document selection uses opaque ID,
not number. No backend/schema/business-rule changes; existing sandbox evidence route
is allowlisted. Use existing translated strings and compact register styles.
Tests first: source integration contract, then browser fixture search, pagination,
inspection/Back and zero writes. Run contracts/build/audit/format/spec checks.
Analysis: FR-009 maps to T009, scope approved, no unresolved questions or critical
findings. Constitution PASS. Rollback removes the additive tab/component export.

Extend shared timeline_activity with optional all-time (hours=0), subject filter,
before-sequence cursor, reference-name SQL search and tenant record counts. Defaults
for existing consumers stay unchanged. Tenant timeline adapter passes optional fields.
Frontend BusinessHistory uses that endpoint, merges pages by event identity and
displays server group identity. Adjacent detail uses existing api.inspector and
renders its authoritative trail/sections/links; local Back is presentation state only.
PlaygroundWorkspace changes only its journal panel, label and timeline highlighting.

## Constitution Check
PASS: read-only, tenant-scoped SQL, existing provenance/relationships, no schema or
business rules in UI, tests before implementation. No architectural exception.

## Tests and Review
FR-008: Shared RegisterState presentation component for central inventory, master
data, deliveries, finance and history. Existing strings and callbacks remain reused;
only read-filter reset is added. Browser no-match/reset and hidden-pagination proof,
contracts/build/i18n/format/spec checks. Constitution PASS; approved presentation
scope, no unresolved clarification or critical finding. No migration or writes.
FR-007: Reuse scoped cockpit CSS across secondary selectors and registers. Normalize
master selector pressed state and separate pagination classes; retain all callbacks.
Check selected styles, table headers and adjacent catalog placement in the browser,
then run contracts, build, formatting and spec gates. Constitution PASS: UI only,
no schema or service changes. Approved scope has no unresolved clarification or
critical consistency finding. Revert these presentation changes for rollback.
FR-006 refinement: scoped cockpit CSS only; no logic/API change. Add a browser height
assertion before styles, inspect desktop/mobile screenshots and run web gates.
Constitution PASS; approved scope and no critical findings. Revert scoped CSS to undo.
Shared service tests: cursor, filters, item search, counters; API existing timeline
tests and Playground boundary tests. Browser fixtures: groups, search, details,
timeline selection, empty/error, themes/mobile plus existing guided flow. Contracts,
localization, build, Ruff and spec policy. Rollback is additive API defaults plus UI
reversion; no migration. Analysis: FR-001–005 covered, no critical findings.
