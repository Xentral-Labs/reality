# Tasks

- [x] T001 Specify and review user-approved scope; record Constitution PASS and read-guard audit (FR-001–005, DR-001–003).
- [x] T002 Add failing service and authenticated HTTP read/isolation regressions in tests/test_sandbox_read_parity.py and tests/test_playground_api.py; update the superseded reference-read expectation (FR-001–004).
- [x] T003 Replace read-only guards in services/reference_workspace.py, services/item_imports.py, web/warehouse_reads.py, web/source_reads.py and web/api.py using existing get_tenant (FR-001–004).
- [ ] T004 Run complete required gates; review every remaining purpose restriction and record evidence (FR-005, all DR).
- [x] T005 Deploy the scoped fix locally, verify actual demo reads and publish reviewable PR (SC-001–002).

Dependencies: T001 → analysis → T002 → T003 → T004 → T005. No unresolved clarifications or critical findings.

T004: all local gates and review passed. GitHub CI is blocked before execution by account billing/spending-limit status; completion awaits a successful hosted run.
