# Implementation Plan: Browser-free MCP Demo Workflow

## Technical Context

Python 3.12, SQLAlchemy 2/PostgreSQL and existing application/MCP tools; React/TypeScript
for two presentation defects. Reuse shared read cursor/metadata and proposal review
services. No dependency or migration. The user's latest message accepts implementation
of the unambiguous slice; the original checkout and running installation stay untouched.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Existing retained documents/lines/movements/reviews; received values unchanged |
| Operational authority / shortest links | PASS | No document status or duplicated relationship |
| Proven schema | PASS | No schema changes |
| Tenant/shared services | PASS | Every SQL read scoped; adapters call shared services |
| Spec and test evidence | PASS | Owner authorization; tests before implementation; tasks and analysis below |
| Explainable Web | PASS | Labels distinguish current and proposed effects; shared review retained |
| Storage discipline | PASS | PostgreSQL, read-only observations, bounded pages |
| Received values | PASS | No financial recomputation or inferred source amount |

## Design and Paths

1. `services/proposal_reviews.py`: expose a safe exact MCP review using existing
   `proposal_review`. Explicitly return only a retained delivery review's fingerprint
   needed by the existing confirmation tool; never expose credential/private carriers.
   Preserve lifecycle, authority/staleness enforcement and no read writes.
2. `services/read_contracts.py`: scoped keyset pending summary page using existing
   page helpers, stable opaque ID order, exact tool filter, no input/preview payload.
   Existing application no-argument callers remain legacy; public MCP defaults to page
   and permits explicit legacy mode for migration. Details come from exact review.
3. `services/capability_catalog.py`: a separate company-context read for stored ID/name/
   purpose plus existing credential metadata, with a principal/tenant mismatch refused.
   Rights remain discoverable through the existing topic catalog; no duplicate grant logic.
4. `services/core.py`: discover document lines and optional exact document scope through
   existing discovery; page scope includes that filter. Closed families in MCP schemas.
5. `tools/application.py`, `mcp/catalog.py`: register read-only context/review, bounded
   proposal inputs, precise inventory/family enums and movement-vs-shipment guidance.
   `resource_catalog.yaml`: business home and German labels for new reads.
6. `services/product_advisor.py`: prefer actual company referents for operational
   prompts even when they mention Reality; preserve hypothetical/product questions.
7. `apps/web/src/Auth.tsx`, `unified/ActionCard.tsx`: preserve locale on signup links;
   reservation preview says Reserved after confirming. No browser business rules.
8. EN/DE demo/connect-agent/guidance docs: existing confirmation tool, optional link,
   explicit admission, canonical purchase example, external schedule/permission limits,
   source-grounded support and shipping coverage. Regenerate executable tool references.

## Tests Before Implementation

`tests/test_demo_mcp_workflow.py`: company scope, bounded/payload-free traversal and
cursor scope, exact review privacy, browser-free decision/receipt/replay/refusal story,
document-line discovery, movement-only order evidence, closed schema choices.
`tests/test_chat_tools.py`: exact mission and genuine product-query routing.
`apps/web/scripts/demo-workflow-contract.test.mjs`: locale and proposed-effect labels.
Retain existing proposal, MCP read, privacy and demo/documentation regressions.

## Verification and Rollback

Run focused failing proofs, then relevant and full backend tests, Ruff, spec policy,
web contract/build/i18n, docs generation/catalog/build and every GitHub required check.
CI's isolated PostgreSQL shards are the full-suite gate. Record actual head and results.
Revert code/catalog/docs commit to roll back; legacy application list reads remain
compatible. No data or deployed configuration rollback is needed.

## Explicit Remaining Work

Full allocation explanation (FR-007 beyond document/line navigation), optional human
review URL, and enforcement/qualification inside third-party agent systems are not
silently implemented or marked complete. Do not broaden access, merge or deploy.
