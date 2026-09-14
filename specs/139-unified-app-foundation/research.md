# Research: Unified App Foundation

Scope approved 2026-09-07. Research is a read-only source inspection; no runtime or concurrency proof is claimed. Two bounded research agents inspected proposal lifecycle and delivery reads while the primary agent inspected routing, authentication, styles and Chat.

## R1 — New presentation, existing authentication and service authority

**Decision:** Create `apps/web/src/unified/` and route four foundation surfaces through it behind `VITE_UNIFIED_APP`. Keep existing company/support routes and `/playground` available; no permanent public old/new selector. Preserve AuthGate's pending-account and practice routing before attempting company bootstrap.

**Evidence:** `App.tsx` selects ProductApp versus PlaygroundPage. `Auth.tsx` grants practice admission to verified pending accounts only on playground paths; normal ProductApp bootstrap is not a replacement for that policy.

**Alternative rejected:** Mounting the new UI inside the legacy ProductApp retains old navigation and global CSS. A separate frontend deployment duplicates authentication, routing and maintenance.

## R2 — Isolate legacy styles and reuse narrowly

**Decision:** Keep App as a small authenticated dispatcher. Move the old ProductApp module to `apps/web/src/legacy/LegacyProductApp.tsx` with behavior unchanged and load it only for legacy routes. Move its import-relative assets correctly. New pages use `tailwind.css` and shared br-* controls; extract genuinely reusable formatting/reference components, not old screens.

A legacy-to-new entry uses full document navigation during transition so previously loaded legacy global CSS does not persist. New-to-new routes use normal history handling. No whole-App rewrite or new router dependency is needed.

**Alternative rejected:** Importing both style stacks globally makes new appearance depend on legacy cascade order. Copying mockup CSS into the product violates shared UI conventions.

## R3 — Authoritative delivery reads need correction

**Evidence:** `web/read_models.py::_fulfillment_expressions` uses original commitment quantity/date, whereas `services/core.py` has revision-aware `commitment_quantity`, `commitment_due_at`, `fulfilled_quantity`, `open_quantity`. `web/api.py::commitment_inspector` additionally sums shipments without subtracting corrections. Existing dashboard lists are bounded samples, not totals.

**Decision:** Add `services/delivery_reads.py` for paginated delivery work and case composition, reuse existing authorities, and fix effective-value SQL before pagination in `web/read_models.py`. Delegate the existing commitment inspector to these semantics. Preserve item/location/unit scope, linked identities and explicit history/sample completeness.

**Alternatives rejected:** Summing visible rows; browser arithmetic; fetching one page then applying revision-aware filtering; copying the inconsistent inspector into a new page.

## R4 — Reuse proposals, strengthen exact review

**Evidence:** `tools/application.py::create_change_proposal` stores input and a generic preview; `approve_and_execute_proposal` atomically claims proposed→executing and injects `_action_id`. Executed requests replay their stored output. Review currently lacks stock-bound reservation/shipment revision. The output is replaced on execution.

**Decision:** Add bounded preparation and review helpers in `services/delivery_actions.py`, called by the shared application-tool proposal path for ordinary-company reserve and shipment-only movement_create. Preserve immutable reviewed input/preview metadata in a versioned reserved proposal-input envelope and strip it before passing business arguments to a handler. Preserve existing top-level receipt fields and add review/verification metadata. Bind a new review token to exact normalized intent and authoritative relevant state. No new table or column is required.

Preparation retries use a stable opaque request ID, scoped to company and authenticated actor, to derive an opaque proposal identity. A matching replay returns the same proposal; changed intent for the same request ID conflicts. A conflict cannot expose another scope. Provider-created proposals receive server-side request identity; deterministic form requests retain their request ID until answered.

New reviewed proposals require the review token from all adapters, not just the new UI. Existing pending legacy proposals remain readable; first review upgrades them under their existing identity before confirmation. Update CLI/MCP/legacy review adapters to carry the token for these actions. Do not silently execute a new reviewed proposal through an older bypass.

**Alternative rejected:** A second action table or browser-only revision. Reusing Playground policy would broaden sandbox admission unintentionally.

## R5 — Keep allocation semantics and serialize shared mutation

`services/core.py::reserve` caps allocation to availability and remaining unreserved demand. The new preview must disclose requested/applied/shortage, including zero; do not redefine it as all-or-nothing.

Same-proposal CAS does not protect different proposals competing for stock. Implementation review found a smaller design than the originally proposed cross-commit session lock: claim the proposal first, then acquire the existing tenant row lock and perform the final review validation in the same transaction as the domain mutation. Every relevant direct writer acquires that tenant lock before authoritative capacity reads through the shared core mutation boundary. Core commits release the guard only after effects are recorded.

A stale or invalid review discovered after claim but before invoking the handler returns the proposal to proposed with no business effect. A handler exception remains unresolved; this distinction is explicit in tests. Preliminary review/token checks still run before claim. No other adapter may bypass final validation. Outer operations that acquire source/document/run locks are audited for lock order; PostgreSQL deadlock failures never imply safe replay after execution claim.

**Alternative rejected after implementation inspection:** A session advisory lock would require pinning every ordinary caller's SQLAlchemy connection across commits and changing unrelated transaction ownership. The existing tenant row lock plus final validation immediately before the handler provides the needed atomic check/effect boundary without that new infrastructure. No new database table, session class or schema is needed.

## R6 — Verify history using immutable events

**Evidence:** `_proposal_execution_status` has reservation verification and opening-stock recovery, but shipment lacks equivalent verification. Reservation quantity is mutable under consumption/splitting; it cannot independently prove the quantity originally allocated.

**Decision:** Extend verification against immutable `BusinessEvent.action_id` evidence and exact reviewed intent, plus actual Movement links. Report historical recorded effect separately from the current observation. An executing proposal with no observable event remains unresolved; absence is not proof of no mutation. A recorded effect with unavailable refreshed observations is not a failed action.

## R7 — Chat and case context

**Decision:** Reuse company chat sessions/messages and provider dispatch in `services/core.py` and `agent/`. Add optional typed context to message submission. Validate a context kind/ID in the active tenant before constructing provider context. UI shows the context attached to each sent question; editing selection cannot rewrite old messages. Store the context annotation in existing message content with a versioned structured prefix handled by presentation (no new column); legacy plain messages continue to render unchanged. System authority never comes from user-supplied annotations.

Persisted context is explanatory history, not authorization: each send resolves context again server-side. Reuse messages for normal conversation, not for storing action authority; cards reference ChangeProposal IDs. Preserve retained questions and avoid duplicate successful sends on a manual retry by checking the existing recorded question/result where identifiable; no automatic mutation retry.

## R8 — Tests and review

Use current pytest/PostgreSQL, frontend Node contract tests, React/Vite build and existing browser harness conventions. Add actual fixture-backed browser journeys plus PostgreSQL API stories; text-only assertions cannot establish interactive correctness. No new browser-test dependency is prescribed until the existing harness environment is checked.

Browser automation was unavailable earlier in this conversation; implementation visual acceptance therefore remains an explicit gate. No alternative browser-control method or screenshot success is implied.

All research questions needed to write this plan are resolved. Runtime proofs, shared-lock coverage and visual acceptance are implementation tasks, not completed findings.
