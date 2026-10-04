# Implementation Tasks

## Foundation

- [x] T001 Record authorized slice and Constitution PASS in `specs/363-mcp-demo-workflow/spec.md` and `plan.md`.
- [x] T002 Add failing MCP read/decision/navigation regressions in `packages/reality-core/tests/test_demo_mcp_workflow.py`.
- [x] T003 Add failing operational routing scenarios in `packages/reality-core/tests/test_chat_tools.py` and browser UI regressions in `apps/web/scripts/unified-delivery-browser.mjs`.

## US1 — Browser-free decision cycle

- [x] T004 [US1] Reuse safe review in `services/proposal_reviews.py` and scoped pending pages in `services/read_contracts.py` (FR-001/002/005, DR-001/002).
- [x] T005 [US1] Add separate company context in `services/capability_catalog.py` and shared adapters in `tools/application.py` (FR-003).
- [x] T006 [US1] Register reads, schemas and public page defaults in `mcp/catalog.py`; label/group in `config/resource_catalog.yaml` (FR-001/003/005/016).

## US2 — Correct operational evidence

- [x] T007 [US2] Fix company-question routing in `services/product_advisor.py` (FR-009).
- [x] T008 [US2] Add exact document/line navigation in `services/core.py`, `services/read_contracts.py`, `mcp/catalog.py` (FR-007/016 clear slice).
- [x] T009 [US2] Clarify shipping evidence in `mcp/catalog.py` and source-grounded support in public guides (FR-004/010).

## US3 — Truthful entry and review

- [x] T010 [US3] Preserve signup language in `apps/web/src/Auth.tsx`; proposed-effect label in `unified/ActionCard.tsx` (FR-014/015).
- [x] T011 [US3] Correct EN/DE demo/connect-agent docs for intake, profile, MCP confirmation, schedules and permissions (FR-006/008/011/012/013/015).

## Verify and review

- [x] T012 Generate tool docs via `make docs-generate`; run focused/full backend, frontend, docs and policy gates; record evidence in `verification.md` (all scoped requirements).
- [x] T013 Review privacy/tenant/confirmation/compatibility, update PR scope and verify final-head GitHub checks; leave wider FR-007 follow-up explicit.

Dependencies: T001 → T002/T003 → T004–T011 → T012 → T013. No delegated execution.
Acceptance is independent by story; no task is complete until its corresponding proof passes.
