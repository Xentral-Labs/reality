# Tasks: Fee Open Receivables

- [x] T001 Record owner-approved fee policy and review specification.
- [x] T002 Review plan against the Constitution: existing evidence/control entries, no schema, shared services, tenant scope, confirmation and read-time derivation.
- [x] T003 Analyze requirement coverage and consistency: FR-001–FR-006 mapped below; no unresolved clarification or critical/high finding.
- [x] T004 [FR-001–FR-005] Add failing fee-register, aging, exposure, payment/reversal, history and exclusion tests in `tests/finance/test_fee_open_receivables.py`.
- [x] T005 [FR-001, FR-003–FR-005] Share fee claim vocabulary; extend canonical OP/aging/exposure and Web reads; keep dunning and noncash reductions excluded.
- [x] T006 [FR-002, FR-006] Enable existing confirmed cash/credit allocation service for fee claims without changing adjustment eligibility; test tenant/currency/over-allocation and confirmation guards.
- [x] T007 [FR-001, FR-003, FR-006] Update projection version/catalog, adapter evidence, feature documentation and generated references; link resolved prior limitations.
- [ ] T008 Verify focused finance/story/adapter tests, full backend, lint/spec, Web/docs gates and final review; record evidence before completion.

T001 → T002 → T003 → T004 → T005/T006 → T007 → T008. No migration or historical rebooking.

| Requirement | Test task | Implementation task |
|---|---|---|
| FR-001 | T004 | T005, T007 |
| FR-002 | T004, T006 | T006 |
| FR-003 | T004 | T005, T007 |
| FR-004 | T004 | T005, T006 |
| FR-005 | T004 | T005 |
| FR-006 | T006, T007 | T006, T007 |
