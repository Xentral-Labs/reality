# Walkthrough findings and preparation review

**Date**: 2026-10-04
**Language**: English
**Scope**: Static code/contract triage plus recorded synthetic walkthrough observations.
This is not a reproduction on the newly fetched main and not a release verification.

## Decision correction

MCP already exposes `proposal_approve_and_execute` and `proposal_reject`, both mode
`confirm`, in `packages/reality-core/src/reality/mcp/catalog.py`. The tested read/propose
token excluded them. The original report's implication that a browser link was the
primary missing capability is superseded: the primary proof is exact review and
explicit human confirmation through MCP. An optional URL helps a human, not the agent.

`services/proposal_reviews.py::proposal_review` already produces safe input, preview,
receipt, confirmability and next steps for Web. First inspect reuse and the existing
review-token requirements in `tools/application.py::approve_and_execute_proposal`.
Do not add another decision engine or weaken token/actor attribution.

## Complete disposition of the owner's list

| # / requirement | Finding / confidence | Disposition |
|---|---|---|
| 1 / FR-001 | Execution tool exists; browser-free confirmation untested | Prove existing execution; expose reusable exact review if needed; link optional |
| 2 / FR-002 | Criteria spread across readiness, stock and retained review | Consolidate safe current decision context through existing services |
| 3 / FR-003 | Tested context lacked company name; purpose work already open | Coordinate PR #367/spec 362; review identity extension separately |
| 4 / FR-004 | Agent reported no shipping from empty Shipment list despite Movement | Reproduce retained movement/object split; truthful coverage and operational read |
| 5 / FR-005 | Pending list unbounded and full plans | Bounded summary/detail contract; preserve internal consumers and migrate public clients |
| 6 / FR-006 | Pending intake proposals do not create accepted orders | Intended spec 356 admission, clarify docs/status; no auto-approval |
| 7 / FR-007 | Agent failed invoice-line/allocation navigation; direct read found gross amount | Audit all existing read paths before adding a scoped invoice explanation |
| 8 / FR-008 | Fresh PO-006 returned 5 received and 5 billed contrary to guide | Verify canonical profile then correct guide/fixture together |
| 9 / FR-009 | Exact mission routed to Product Advisor fallback | Routing regression against exact prompt; retain genuine product questions |
| 10 / FR-010 | Agent draft added guarantee and future message | Source-grounding guidance and external-agent evaluation, no transport feature |
| 11 / FR-011 | Chat claimed no scheduling; Cowork had it | Concrete supported-mode instructions, avoid runtime claim beyond tested mode |
| 12 / FR-012 | Other Claude connectors technically attached | Explain external technical isolation; Reality does not administer Claude |
| 13 / FR-013 | Routine Berlin, company UTC unstated; next-run offset | Explicit distinction and actual next-run/pause/device guidance, no new scheduler |
| 14 / FR-014 | Review said Reserved 2 before actual reservation | Current/proposed labels plus named context; retain shared authoritative review |
| 15 / FR-015 | Login → signup drops locale, mixed labels | Signup route and localized guide terminology regressions |
| 16 / FR-016 | Generic string choices / projection names hinder follow-ups | Exact schemas and callable follow-ups; generated reference parity |

## Static evidence checked on main

- `services/product_advisor.py::is_product_advisor_question` only excludes possessive
  company requests when the prompt does not contain "reality". The exact demo mission
  contains Reality and operational instructions. `services/core.py` runs
  `business_journey_guide` when this classifier returns true, before operational AI.
  This is a concrete suspect, not proof that a one-line classifier change is sufficient.
- `tools/application.py::proposals_awaiting_approval` selects every proposed tenant
  record; `mcp/catalog.py` declares no inputs for this public read.
- `apps/web/src/Auth.tsx` contains literal `/signup` hrefs while other auth paths use
  `languageHref`. Cover both actual signup entry points, not only one text string.
- `apps/docs/content/de/getting-started/demo-company.md` still says PO-006 is received
  without an invoice. Match both locales to the current canonical profile before fixing.
- Spec 145 FR-005 already requires movements and source evidence in retained order
  explanations. Empty Shipment objects alone are not complete shipping evidence.
- Open PR #367 explicitly adds only `tenant.purpose` and forbids other keys in that
  object. Do not silently expand its accepted requirement to satisfy identity discovery.
- Spec 356 preserves exact reviewed external admission. Pending live inputs are expected.

## Recorded manual evidence and limits

The external test explained an order with 5 promised / 3 shipment-Movement quantity /
2 open. A concretely approved two-unit reservation changed stock from 0 to 2 reserved
and made the remaining order ship-ready. Confirmation was in Web; MCP verified it.
Both a saved manual task and a timer task used the test MCP connector. The timer was
scheduled for 17:33 Berlin, started 17:33:35 and completed 17:35:06; it repeated the
shipping inference error. The task was restored to its weekday plan and paused.
No real email, shipment, bank transfer or optional purchase was performed.

Large MCP answers caused reads/searches of retained tool-result files; one earlier
Claude turn used shell despite the instruction. This is an external-agent deviation,
not evidence that Reality wrote business data through shell or leaked personal files.
The first support draft's unsupported guarantees were corrected. No general claim
that every invoice navigation tool is missing is justified by that failed path.

## Implementation sequencing after scope acceptance

1. Prove review → explicit confirmation → execution → reconciliation, company context
   and bounded decision reads. Run permission/staleness/replay cases first.
2. Correct operational routing and evidence completeness for shipping and Finance.
3. Align profile examples, locale, review wording and external-agent setup guidance.

This is prioritization for review, not an approved technical plan or implementation
task list. No plan/tasks/analyze artifacts are manufactured before the human scope gate.
If the implementation diff becomes too broad, keep this common acceptance specification
and split the reviewable implementation slices; do not silently drop listed requirements.

## Required gates for later implementation

After scope acceptance: plan with Constitution PASS → tasks with exact test paths →
Spec Kit analyze with no critical findings → test-first implementation → backend,
frontend, migration (if applicable), spec and generated-documentation gates → final review.
Any affected command/tool/schema requires `make docs-generate` and
`make docs-catalog-check`. Business services remain the authority; transport-only
patches cannot implement stock, settlement or confirmation rules.
