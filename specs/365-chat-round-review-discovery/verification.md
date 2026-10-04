# Verification

**Language**: English

## Deterministic regressions

The original padded selection, both-provider context, standalone confirmation and
configuration validation regressions failed before implementation (9 failures).
The live-discovered undeclared-argument tests then failed before the additional
boundary correction (3 failures; genuine handler-error control passed).

Initial focused run: **101 passed** across test_mcp_read_contract,
test_chat_scope_security, test_capability_catalog, test_tool_catalog and
test_demo_mcp_workflow. Lint passes. Specification policy passes. Tool Usage was
regenerated from the executable contracts. Final full Quality checks are pending.

Full CI then exposed two existing Playground admission-precedence regressions:
unknown-field validation intercepted a prohibited item_create_propose before the
Sandbox refusal. The guard was narrowed to reads; proposal/confirmation admission
remains unchanged. The reviewed regression run including all six focused/security
files passed: **710 passed, 1 existing skip**. No assertion or gate was weakened.

The complete local suite uses disposable PostgreSQL with
max_locks_per_transaction=1024, matching CI. An earlier root-directory invocation
failed relative Alembic/fixture resolution and was stopped; the corrected run uses
packages/reality-core. No deployed database settings were changed. The four-worker local replay benchmark
exceeded its 60-second threshold under load (70.4 seconds); its isolated repeat
passed in 36.68 seconds. The superseded two-worker full run was stopped after
1,370 passed and four existing skips to validate the final compatibility correction.

## Actual daily mission

Test company: Reality MCP PR370 Retest 2026-10-04, ten_f5328569e6. Its source is
paused; the retained synthetic evidence and existing reservation were preserved.
A temporary loopback-only API loaded this worktree's source/configuration while
the existing local stack continued running the merged release. No migration,
additional reservation, shipment, approval or company-setting change was performed.

The exact published German daily mission was submitted through the authenticated
copilot API, using the real managed provider. The initial attempt exposed the
provider's shipments_list(limit=...) call. Its undeclared argument escaped as
TypeError and aborted the turn. After the closed flat-schema argument boundary
was restored for reads, the mission completed and pending proposal IDs were unchanged.

Independent shared-tool reads confirmed:

- Shipment query: five records, all type shipment, **has_more=true**. The earlier
  sample included opening_stock, receipt and return, proving the original filter bug.
- SO-006: the retained commitment com_c9f2b45910 and Movement mov_74048f6524 still
  represent 5 promised, 3 shipped and 2 remaining; the pre-existing reservation
  res_f039236c52 remains. No consignment/tracking was fabricated.
- Return query: seven records, **four return and three supplier_return**, with
  has_more=false.
- The public capability_catalog(topic=review) independently exposes
  proposal_approve_and_execute. Principal tests establish the actual grant reasons.

The daily response now recognizes retained shipment Movements separately from
consignments. This is an improvement, **not a general model-prose correctness proof**.
Remaining observed response problems:

1. It reports the five-record shipping sample without making has_more visible;
   readers could mistake the bounded sample for a company count.
2. It reverses the return category count (three customer/four supplier versus the
   actual four customer/three supplier).
3. It states an unproven outbound-delivery conversion cause for an unshipped order.
4. It describes a hypothetical future automatic routine without verified client
   controls, next run or pause evidence; the mission was a manual current round.

These are follow-up findings. No regex prose rewrite or second model judge was
added; deterministic evidence-linked stage output requires its own reviewed design.

## External repeated-agent qualification

**Outcome: blocked, not scheduled.** Native Claude control reported the Mac locked
when attempting to inspect actual scheduled-task state. No automatic unlock was
attempted. The existing tasks/connections were not modified. No new temporary
credential or recurring task was created for this feature, so no new credential
needed revocation. Previously revoked test credentials remain revoked.

The current round is manual. Actual clock access, saved mission/checkpoint reuse,
a second autonomous MCP round, time zone/workdays, next run and pause remain
unverified. No next-run time, enabled routine or Reality-owned timer is claimed.

## Evidence retention and cleanup

Local raw synthetic results are retained under
/Users/benediktsauter/GitHub/reality/.local/reports/pr371-live-evidence
and /private/tmp/reality365-live (daily-mission.json, retained-evidence.json,
proposals-before.json and proposals-after.json). No credential values are present
in these artifacts. Temporary runtime cleanup follows completed validation.
