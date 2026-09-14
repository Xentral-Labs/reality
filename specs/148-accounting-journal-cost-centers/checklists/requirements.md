# Specification Quality Checklist: Operational Subledgers

**Created**: 2026-09-09  
**Feature**: [spec.md](../spec.md)

## Revised scope quality

- [x] Owner's accepted boundary is explicit: external software owns financial accounting.
- [x] Previous general-ledger, full financial chart, tax-engine, financial-statement, fiscal-close and opening-conversion requirements are removed.
- [x] Existing operational gross posting and settlement meanings remain intact.
- [x] Minimal subledger accounts define eligibility, stable roles, destinations, blocked-account reversal and optional external mappings.
- [x] Account setup/maintenance screens, additive historical adoption and individual planned proof are included.
- [x] Received net/tax detail and optional internal attribution are distinct from financial accounting authority.
- [x] Recording, preparation and external outcome are independent evidence-backed statements.
- [x] No live vendor connector or unnamed import compatibility is claimed.
- [x] Requested internal structure and screens are supplied as reviewable companion contracts.
- [x] English artifact language, mandatory sections, explicit scope assumptions and testable outcomes are present.
- [x] Every functional/domain requirement maps to individual planned proof.
- [x] Replay, corrections, tenant/target isolation, missing evidence and immutable revisions are covered.

## Readiness

- [x] Product direction accepted through the owner's confirmation of the subledger boundary and subsequent minimal-account-catalog addition.
- [x] Revised detail ready for review; no unresolved clarification placeholders.
- [ ] Technical plan, Constitution Check and schema/migration review complete.
- [ ] Implementation tasks and cross-artifact analysis complete.
- [ ] Runtime implementation and required acceptance checks pass.

## Notes

The feature directory retains its old slug to preserve links; its current contents supersede the earlier broad draft. The user explicitly requested internal data structure and views, so that detail is maintained in companion requirement contracts rather than omitted under the specify skill's general preference for business-only specifications.

No `.specify/extensions.yml` was present in the specification workflow; no before/after hooks apply. No feature branch or runtime implementation is created by this revision. Verification results are recorded below after checking the revised files.

## Revision verification

- Local links and placeholder checks passed across all five files.
- All 34 FR and seven DR identifiers have individual proof rows; no duplicate IDs were found.
- `make spec-check` remains red because the concurrent company/demo changes lack eight coverage-matrix entries: `test_company_setup.py`, `test_company_setup_api.py`, `test_company_setup_migration.py`, `test_demo_data.py`, `test_demo_data_intake.py`, `test_demo_data_security.py`, `test_demo_profile_history.py`, and `scenarios/test_international_demo.py`, all under `packages/reality-core/tests/`. This revision changes none of those tests or their shared coverage matrix.
- No runtime behavior was changed or claimed verified.

- Account-catalog revision rechecked: all five companion files and all 35 FR/DR proof mappings passed local-link/placeholder checks. The global spec gate was rerun and reports the same eight unrelated company/demo coverage gaps above. Account retirement, exact reversal, initial classification of unresolved legacy roles and deterministic defaults were reviewed together.

- [x] Owner-approved fixed transaction matrix and explicit extensible case/group mappings are included in posting-matrix.md and all companion requirements.
- [x] Unknown tax is not a no-tax case; country/rate inference is excluded and ambiguous mappings require review.

The matrix/case addition supersedes the earlier five-file/35-requirement check counts; the current package has six Markdown files and 41 FR/DR identifiers. Earlier verification entries describe their respective revisions.

## Latest verification — transaction matrix revision

- `make spec-check` passed on the current workspace; the previously reported concurrent coverage gaps no longer fail this gate.
- All six Markdown files passed local-link and placeholder checks; all 34 FR and seven DR identifiers have individual proof rows with no duplicate IDs.
- This remains specification work only; no runtime implementation or acceptance tests are claimed complete.

## Customer payment-difference scope addition

- [x] Explicit skonto acceptance is separated from merely explaining a residual.
- [x] Claimed withholding stays open; partial/full accepted reduction is evidenced and confirmed.
- [x] Actual overpayment remains reusable/refundable unallocated credit, without fake cash or credit notes.
- [x] Existing ledger/allocation primitives are reused; new action/evidence semantics and account role are bounded.
- [x] Corrections, tax-data boundaries, concurrent consumption and individual planned proof are specified.

This addition has seven Markdown files, 41 functional requirements and seven domain requirements. Earlier check counts describe earlier revisions.

Latest payment-difference revision: `make spec-check` passed. All seven files passed local-link/placeholder checks and all 48 FR/DR identifiers have individual proof rows without duplicates. No runtime implementation was changed or claimed verified.

## Customer/supplier symmetry and available-credit addition

- [x] Supplier payment differences mirror customer flows with explicit opposite control/cash directions.
- [x] Supplier liability reductions require recorded entitlement/agreement; unaccepted withholdings stay payable.
- [x] V09 includes both Customers and Suppliers, payment and credit-note origins, allocation/refund detail and no automatic cross-role netting.
- [x] Supplier action/mapping/reversal/catalog and UI proof are specified, including concurrency and no-open-invoice credit discoverability.

Current requirement count is 43 FR plus seven DR across seven Markdown files; prior check counts describe earlier revisions.

Latest symmetric revision: `make spec-check` passed; seven files and all 50 FR/DR mappings passed local-link, placeholder and proof-coverage checks. Runtime implementation remains pending.

## Opening subledger positions addition

- [x] All four customer/supplier debt/credit directions have explicit control and neutral counterpart semantics.
- [x] Stated residuals, source/cutover identity, optional original dates and labelled summary mode are specified.
- [x] Replay, changed snapshots, original-document reimport and summary/detail overlap cannot silently duplicate balances.
- [x] Existing settlement/refund/reversal and V09 are extended, with V10 and individual proof requirements.

Current package: eight Markdown files, 48 FR and seven DR. Prior counts refer to prior revisions.

Latest opening-item revision: `make spec-check` passed. Eight Markdown files and all 55 FR/DR mappings passed local-link, placeholder and individual-proof coverage checks. No runtime implementation is claimed.

## Systematic trade-finance gap closure

- [x] Provider captures, stated fees, reserves/disputes and bank payout legs are distinct and source-backed.
- [x] Advance purpose and payable holds constrain actions without inventing cash or changing debt.
- [x] Same-account allocation is preserved through explicit conservative cross-account reclassification.
- [x] Existing goods/billing/return controls distinguish unknown migration coverage from proved absence.
- [x] Structured agent explanations, Fact authority and post-action verification are explicitly defined.
- [x] All additions map to scenarios and individual planned proof; V11–V13 and integration dependencies are recorded.

Current scope has ten Markdown files, 58 FR and seven DR. This closes the reviewed requirements gaps; physical plan/tasks and runtime proof remain pending.

Latest trade-finance revision: `make spec-check` passed; ten Markdown files and all 65 FR/DR identifiers passed local-link, placeholder and individual-proof mapping checks. Self-review aligned invoice-account precedence with the new reclassification rule and distinguished transfer-leg identities from duplicate imports. No runtime implementation or formal plan/tasks/analyze completion is claimed.

## Technical planning revision — 2026-09-09

- [x] Prepared plan.md, research.md, data-model.md, contracts/commands.md, contracts/views.md, quickstart.md and test-plan.md.
- [x] Recorded existing allocation/atomicity/partial-billing gaps and root-worktree integration constraints.
- [x] Evaluated all eight Constitution design rows as PASS without exceptions.
- [x] Checked 17 Markdown files, all local links and exactly 65 individual FR/DR test mappings; no missing, extra or duplicate identifiers.
- [x] `make spec-check` passed; no unresolved template markers; extension configuration absent, so no plan hooks apply.
- [ ] Complete human schema/technical review, task generation and cross-artifact analysis before implementation.
- [ ] Implement and run required runtime, migration, concurrency, adapter and browser verification.

These checks establish documentation consistency only. No feature behavior, database migration, UI rendering or automated posting has been implemented or verified by this planning revision.

## Authorized analysis remediation — 2026-09-09

The owner authorized corrections to the three reported design findings. Source classification now has target-independent typed revision storage and commands; money-account detail no longer imposes a single currency; target-dependent account mapping tasks follow target/profile schema. Tests cover source scope/revision collisions and preserved multi-currency legacy account identity. Tasks remain unimplemented. The subsequent consistency check is separate from schema approval or runtime verification.

## Owner-approved local cutover simplification — 2026-09-09

The owner confirmed being the sole local tester with no real existing account population. FR-022, FR-028 and SC-004 now specify clean initialization instead of legacy adoption. Earlier checked legacy-migration items above are superseded. Plan/model/contracts/tasks/proof were updated to remove account-string backfill, unresolved roles, compatibility columns, rollout stages and old-binary recovery. External opening-item imports and new-model immutable history remain required. No database reset or code implementation was executed.
