# Tasks: Agent Email Handoffs

- [x] T001 Write source/file/version/partial-capture tests (US1; FR-001–003, DR-001–002).
- [x] T002 Write exact dispatch decision, actor, claim and retry tests (US2; FR-004–007, DR-004).
- [x] T003 Write report/reconciliation/deviation/history tests (US3; FR-008–010, DR-003–005).
- [x] T004 Write MCP/API/tenant/migration and discovery tests (US4; FR-011–012).
- [x] T005 Add closed domain schemas, dispatch model and migration.
- [x] T006 Implement shared capture/file/authorization/claim/report/history services.
- [x] T007 Bind application and MCP tools; expose shared API routes and review links.
- [x] T008 Publish canonical agent contract, labels and generated documentation.
- [x] T009 Run all required checks, review diff and record verification evidence.
- [x] T010 Create PR and resolve required CI/review findings until green.

## Analysis

No unresolved scope clarifications or critical design conflicts. Approval does not
mean dispatch occurred; capture/report permissions do not mean decision authority;
claim ownership is authenticated, never a caller-supplied agent name. Original
external metadata stays in payload. No provider-specific network execution is added.
Each FR/DR maps to the story/test tasks above and the specification traceability table.

## Review follow-up

- [x] T011 Preserve the FR-009 reconciliation guard for uncertain or conflicting reports with approval deviations; cover proposals and claims.
- [x] T012 Refresh FR-010 email history after approval and rejection without reopening the review; verify both browser journeys.
- [x] T013 Validate the review fixes locally and publish full-suite PR check links; the PR records the current head and final check status.

## Mandatory business context extension

- [x] T014 Add failing mandatory-context, supplier/object-history, tenant, version/dispatch and browser stories (FR-013–016; DR-006).
- [x] T015 Add closed reference envelopes, indexed tenant/source membership and protected migration (FR-013–014; DR-006).
- [x] T016 Implement validation, immutable memberships, approved context inheritance and paged object history in shared services (FR-013–015).
- [x] T017 Extend existing MCP/API history and Inspector/email review UI; verify object/source/file/decision navigation (FR-015–016).
- [x] T018 Update canonical contracts, discoverable examples, catalogs and verification; complete full PR checks on the final linear branch (FR-013–016).

## Local-test contract follow-up

- [x] T019 Prove shared approval attribution and explicit summary/detail handoffs with tenant-scoped regression tests (FR-017/018).
- [x] T020 Reuse shared attribution, expose next-read selectors and update workflow/schema/canonical documentation (FR-017/018).
- T021 Completion gate: regenerate catalogs, verify locally and pass full checks on the final rebased PR head (FR-017/018). The live PR verification section records the current head and the final completion evidence; a pending or failed run is not completion.

## Provider-independent follow-up

- [x] T022 Add evidence-label and explicit uncertain-retry actor/tenant/snapshot/concurrency regression tests (FR-019/020).
- [x] T023 Implement shared derived authorization labels, immutable risk acknowledgements and locked revalidation; show labels and risk in Inspector/review (FR-019/020).
- [x] T024 Publish provider-independent integration, linking, capture and retention guidance and draft external-grant spec 353 (FR-021).
- T025 Completion gate: local verification, generated catalogs and final current-head full-suite checks are recorded in the PR verification section. Pending checks are not completion.
