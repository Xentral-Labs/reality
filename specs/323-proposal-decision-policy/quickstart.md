# Validation Guide

Use the existing virtualenv and local test PostgreSQL on port 54329. Tests create
isolated temporary databases; never run against production.

1. Run `.venv/bin/pytest` from reality-core against test_proposal_decision_policy.py,
   test_proposal_review_parity.py, test_credit_hold_adapters.py and finance/test_owner_handoff.py.
2. Verify credit release advertises owner and refuses a member; a shipment permits
   a member; ordinary proposals retain existing paths; changed membership refuses.
3. Run Chat security/confirmation, MCP, attribution and full backend suites.
4. Run `make lint`, `make spec-check`, `make web-build` and proposal-review browser proof.
5. Run `make docs-generate`, docs build and check generated output reproducibility.
6. Review action/authority, tenant/replay and existing exception coverage against spec.
7. Run `.venv/bin/pytest -q tests/browser/unified_proposal_decisions.py` from
   reality-core for the disposable live-stack HTTP role proof.

## Verification evidence (2026-10-02)

- Test-first: the initial 17 policy tests failed with missing policy metadata and
  the credit-owner mismatch. Additional retired-replay and member-removal proofs
  were observed failing before their corrections. Specialized delivery metadata
  parity was observed failing before the shared detail wrapper was added.
- Final scoped backend run: **125 passed, 2 skipped** across decision policy,
  common review, credit adapters, unified delivery actions/holds, shipment actions/API,
  application tools, MCP and finance owner handoff.
- Frontend source/contract suite: **452 passed**. Four-language audit: **2497/2497**
  entries covered in each language, no missing or invalid translations.
- Proposal browser proof passed: old owner payload, new member/private-author/owner
  payloads, actual credit-release and shipment routes, exact review-token confirmation,
  verified executed credit reread and unresolved reread without confirmation.
- Documentation gates: **14 Python reference tests and 114 Node tests passed**;
  VitePress build passed. Final generated catalog output is reproducible: two complete
  generation passes have identical SHA-256 manifests.
- `make lint`, `make spec-check` and scoped `git diff --check` passed.
- Final Web and final generated-documentation builds passed.
- Complete PostgreSQL run (`pytest -q -n 4 --dist loadfile`): **5349 passed,
  10 skipped, 4 failed, 2 setup errors** in 3249.41 seconds. One failure exposed
  a catalog wording regression: the authenticated-principal requirement was retained
  explicitly in the new description and generated documentation was refreshed.
  Three failures were existing demo initialization job timeouts under load; two
  migration setup errors exhausted PostgreSQL shared lock memory.
- All five affected files were rerun without parallel workers after the wording fix:
  **69 passed** in 456.51 seconds, covering every failed/error case and their adjacent
  tests. No job timeout, database configuration or unrelated behavior was changed.
  The initial parallel run is not represented as an uninterrupted green run.

## Review evidence

Pre-implementation Spec Kit analysis covered all 8 FR and 2 DR requirements across
10 ordered tasks: 100% coverage, no unresolved clarification or CRITICAL finding.
The Constitution Check passed before and after design.

An independent read-only authority audit checked authorization phase ordering,
existing exceptions, rejection differences, retired execution replay and specialized
Web routing. Its concrete findings were corrected and covered by regression proofs:
owner-only member removal, reviewed membership before retired executed replay,
specialized delivery policy visibility, verified existing-credit success and loading
recovery. No new authority or schema was introduced.


## Final acceptance and commit review

- The live Web was inspected in Chrome against a disposable migrated PostgreSQL
  database and the real API, Vite, scheduler and worker processes. Credit release
  displayed owner approval, shipment dispatch displayed active-member approval,
  and the private report displayed original-author approval.
- Real authenticated HTTP calls refused member credit approval and another owner's
  private-report approval; allowed member shipment, owner credit and original-author
  report approval; and allowed separate member rejection of an owner-only proposal.
  A stale review token was refused before the proof fetched the current review as
  Web does. The reusable proof is `tests/browser/unified_proposal_decisions.py`.
  Its final isolated-snapshot run passed in 60.24 seconds. It verifies the exact
  owner refusal code and the existing private-author refusal message.
- Follow-up service proof: **43 passed**; expanded policy file: **21 passed**;
  existing fixture browser proof passed again.
- The isolated staged snapshot, excluding unrelated storage/account changes,
  passed **39 backend tests**, lint and spec policy. Catalog documentation was
  generated from that exact snapshot so its fingerprints do not include other work.

The checkout contains unrelated pre-existing work and uncommitted generated outputs.
`docs-catalog-check` compares against Git HEAD and therefore cannot serve as a clean-tree
staleness check here. Two-pass generation reproducibility checks the held outputs
without reverting other work. The owner subsequently authorized a feature-only
commit; shared files were staged by scope and generated outputs by isolated snapshot.

## Published Release Evidence — 2026-10-02

[PR #291](https://github.com/Xentral-Labs/reality/pull/291) released specs 323 and 325 together after all **22 hosted quality checks succeeded**. Rebase merge: `87a826015df786ae3b5324c72c6abf50379168a5`. [Deploy run](https://github.com/Xentral-Labs/reality/actions/runs/37022632660) and [GitOps receiver](https://github.com/Xentral-Labs/argocd/actions/runs/37022861405) succeeded. Logged-in native inspection identified a separate settings/runtime and membership-presentation defect, corrected by spec326 / PR292 without weakening this feature's approval or private-author boundaries. Spec326 records the subsequent release evidence and the remaining existing-session post-check limitation.
