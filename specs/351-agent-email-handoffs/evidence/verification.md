# Verification: Agent Email Handoffs

## Local evidence

- Spec policy and Ruff passed.
- Source-authored business-description audit: zero missing root descriptions/bindings.
- Focused PostgreSQL integration/contract suite: 143 passed, including migration
  chain, policy, graph completeness, MCP read/permission and blueprint adapters.
- Final email-specific stories and migration checks: 18 passed.
- After both main integrations, email, migration, application/discovery catalogs
  and agent registry contracts: 77 passed.
- CI integration fixes (MCP schema shape, canonical frontend fixture and explicit
  Chat read/propose restriction): 49 passed, 2 unchanged skips.
- Product documentation: 145 JavaScript contracts, Python reference tests,
  formatting and production build passed.
- Web test suite: 462 passed. The sandbox initially refused Python fixture
  subprocesses (EPERM); the same suite passed with the approved test execution.
- All four-language i18n audits passed; web build passed.
- Browser acceptance: full outgoing text/BCC, safe HTML and original evidence/file
  navigation passed.
- Generated Tool Usage and Product Advisor knowledge refreshed.

## Full-suite execution

An initial local parallel run was stopped after 1,111 passing tests because its
migration workers exceeded the disposable PostgreSQL container's default lock
capacity. That interrupted run is not a full-suite pass. The container's
max_locks_per_transaction was raised to 1024; focused migration tests then passed.
The complete required suite passed on commit
`c80f845bc9a86fb3f93e121a5cdf16cd4975523c`:

- [Quality gates run 949](https://github.com/Xentral-Labs/reality/actions/runs/37147333752):
  all 22 jobs passed, including all four PostgreSQL shards (1,462 + 1,438 +
  1,801 + 1,316 = 6,017 passed; 10 existing skips), frontend, documentation,
  seven browser-script shards and six live-browser journeys.
- [Installer run 218](https://github.com/Xentral-Labs/reality/actions/runs/37147333749):
  script and end-to-end jobs passed.
- [PR #332](https://github.com/Xentral-Labs/reality/pull/332) records the live
  checks for the final pull-request head as well.

Merged main updates were incorporated, catalogs regenerated and the email
migration placed after the latest merged migration. The first CI
attempt found three registry/fixture contract mismatches; those were corrected,
verified locally and passed in the complete rerun. No unresolved review findings
were present at completion.

## Review

Original messages, files and reported outcomes remain Sources. Approval authorizes
an exact external instruction and does not imply successful sending or delivery.
Claims are authenticated and serialized; unresolved identical payloads cannot be
reproposed/claimed to bypass reconciliation. Outcome derivation uses only
executor-bound receipt links, not arbitrary caller-selected source labels.
New correspondence tables are explicitly deferred from graph analytics pending a
separate privacy/grain design; the operational evidence trail remains available.


## PR review corrections

The P1 reconciliation bypass and P2 stale decision history from review
5404048391 are corrected under FR-009 and FR-010. Execution uncertainty and
conflicting receipts are evaluated independently of approval deviations, so
identical proposals and claims remain blocked until the outcome is reconciled.
The mounted email history read observes proposal status changes.

Local validation: all 20 email integration tests pass, including unknown outcomes,
accepted/failed conflicts and conflicting provider identities with deviating
content, plus successful reconciliation. Browser acceptance verifies approval
and rejection refresh without reopening the dialog, alongside original evidence
navigation and safe HTML. Ruff, spec policy, business-description audit,
Prettier and the production web build pass. The current correction head and final full-suite status are recorded in the
[PR verification section](https://github.com/Xentral-Labs/reality/pull/332).


## Mandatory context extension verification

Owner scope approval on 2026-10-04 requires explicit correspondence links in this
same PR. Missing-context capture and missing object-history tests were observed
failing before shared-service implementation. No guessed historical backfill or
business Fact conversion is introduced.

Focused PostgreSQL email/context/migration/Inspector/graph suite: 43 passed.
Supplier, service supplier, item, purchase commitment and supplier invoice contexts
are queryable; foreign and duplicate references fail, generic imports cannot fake
memberships, context changes version original evidence, and actual reports inherit
approved context. Legacy evidence is preserved and populated-link downgrade refused.
Browser proof covers supplier object history, pagination, original files, Decisions
and decision-status refresh. Four-language audits and 145 documentation contracts
pass. The PR verification section records full-suite status for the final head.

Full extension baseline `efc7004c87a8c0a2ff050ef88f80f7c69dc7e5de` passed all
22 quality jobs ([run 1001](https://github.com/Xentral-Labs/reality/actions/runs/37176017182))
and installer2 ([run 236](https://github.com/Xentral-Labs/reality/actions/runs/37176017149)).
The four backend shards total 6,053 passed and 10 existing skips.
Final attachment-context refinement passes all 12 context integration tests: attachment
Sources inherit explicit memberships through their original email Sources. The complete
frontend contract suite passes 462 tests, and the refined correspondence browser journey
passes. Final current-head CI proof is maintained in the linked PR verification section.

## Local-test contract feedback (FR-017/018)

The owner approved the two local acceptance-test suggestions in PR comment
5976704162. Regression tests observed missing `decider` and `next_read` fields
before implementation. Shared attribution and email/context suite: 48 passed.
The final 18 context tests pass after extending source-to-decision selectors.
Person, token issuer distinction, Chat agent, pending/unknown attribution and
foreign-company follow-up reads are covered. Explicit summary selectors reach
the original message and separately reported execution without embedding bodies.
Documentation: all 145 contracts and formatting pass; specification policy, Ruff
and business-description audit pass. Catalogs are regenerated from executable
MCP descriptions and schema. The branch was rebased onto current main.
Catalog/MCP/optional-argument/context/migration integration suite: 82 passed.
The final source-to-related-decision next-read regression also passes.
T021 remains a live completion gate: the PR verification section records the final
current-head full-suite result; this local proof does not assert pending CI passed.

## Provider-independent integration follow-up (FR-019–021)

Owner approved common contracts for Atlas, Grok applications and other agents.
Initial regression tests observed absent authorization labels and retry snapshots.
Shared services derive labels from executor-bound receipt links, bind reviewed
uncertain-retry exceptions to immutable report-ID snapshots and serialize report,
authorization and claim validation through the shared delivery lock.
No outcome is fabricated or released by a timeout, and no new database table is added.

Email and decision-policy integration suite: 71 passed. Broader application/MCP/
optional-argument/context/migration/policy suite: 115 passed. Final context suite:
29 passed, including observed member attribution, token/Chat exclusion, foreign/
stale/forged acknowledgements, missing new attempts and competing approved claims.
Full frontend contracts: 462 passed. Browser journey passes original-file and
Decision navigation, external archive labels and reviewed duplicate-send warnings.
Four-language audits cover 2,728 strings; production web build passes. All 145
documentation contracts and formatting pass. Spec policy and business annotation
audit pass; generated catalogs reflect the published schema and workflow.

Spec 353 is explicitly a draft provider-independent external-grant contract; no
verified external grant or granular retention/deletion implementation is claimed.
T025 completion is recorded with current-head full-suite proof in PR #332; this
local acceptance evidence does not claim a pending CI run has passed.
