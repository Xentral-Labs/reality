# Analytics design research

Date: 2026-09-13. Product scope approved. Research is repository analysis and design, not implementation evidence.

## R1 — Structured requests rather than generated SQL

Decision: Pydantic discriminated models describe cataloged dimensions, measures, typed predicates and existence predicates. SQLAlchemy compiles admitted order requests; model-authored SQL, column expressions, functions and join strings are not accepted.

Rationale: The user wants freedom to combine business concepts. One schema and catalog can support new combinations while preserving tenant predicates, measure grain and traceability. SQL itself is not the missing capability.

Alternatives: fixed report functions repeat the current limitation; arbitrary SQL requires a materially larger authority/validation surface; a graph copy does not resolve business meaning or missing relationships.

Evidence: `mcp/catalog.py` currently exposes focused schemas; `tools/application.py:2102` dispatches read tools. `company_insights.py` is deliberately fixed. No new database dependency is justified by the 30 questions.

## R2 — Grain-specific perspectives and canonical operational adapters

Decision: Expose order lines, order headers, customer purchase history and product pairs as distinct discoverable perspectives. Add current commitments, inventory, order billing, invoice open items and payments through existing canonical service calculations. Aggregation/filtering is shared; each dataset owns its fixed relationship/measure definition.

Rationale: A header total cannot be summed after line fan-out; first purchase must be computed before applying a first-purchase filter. Product co-occurrence is a distinct unordered item pair per order. These meanings are not safely expressed as arbitrary joins.

Reuse: `delivery_reads.effective_value/fulfillment_expressions`, `core._order_line_billing`, `core.financial_open_items/aging_register`, `read_contracts.location_inventory_rows`, non-persisting `projections.derive_projection_rows`, finance credits/payment services and effective movement correction rules. Any extracted SQL helper requires parity tests for all existing consumers before analytics uses it.

Alternatives: browser/agent aggregation and independent operational formulas rejected because they drift from canonical meaning and incomplete pages.

## R3 — Order evidence eligibility and missing values

Decision: Orders are counted through interpreted Document identities, not raw SourceRecord versions or stream heads. Replayed interpretation cannot add a second count. Per-intake provenance/eligibility adapters report newer pending or reviewed/unapplied versions. Conflicting evidence that cannot be reconciled is excluded with an explicit count/reason rather than guessed current authority.

Rationale: The Shopify interpreter returns an existing document for the same source and raises `ShopifyUpdateNeedsReview` for later versions; a global latest-source filter would erase retained valid orders. Manual corrections and other interpreters need their own existing authority rules traced in tests.

For quantities/prices/amounts, adapters must establish whether a received value exists. ORM numeric defaults alone are insufficient proof of a source-stated zero. Where presence cannot be established, the value is null/unknown in analytics with coverage rather than a new authority. No schema backfill is authorized by this design.

## R4 — Execution consistency, limits and cancellation

Decision: Each run owns a fresh READ ONLY, REPEATABLE READ session. Initial rows, totals, comparisons and coverage share that transaction. Subsequent pages/contributors/export are fresh observations, clearly labelled; a definition fingerprint is not a reusable database snapshot. No report-result database cache is added.

A 30-second monotonic deadline covers execution. Each SQL statement gets the remaining deadline as a local statement timeout; preflight admission and cooperative checks bound canonical Python derivations. Web disconnect/cancel and protocol cancellation propagate to the owned psycopg connection and computation context. Connections are rolled back/discarded before reuse; no arbitrary backend PID is accepted from clients. A timeout never returns partial totals.

Database statement timeout is per statement, not a whole request; it cannot alone satisfy the deadline. Driver cancellation can race with completion, so cancellation invalidates the response generation even if computation just finished. Existing storyline tracing writes outside the analytical read transaction and is disclosed in persistence metadata. It must not commit the owned analytical session.

Sources: [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [statement timeout](https://www.postgresql.org/docs/current/runtime-config-client.html), [psycopg connection cancellation](https://www.psycopg.org/psycopg3/docs/api/connections.html). Check installed driver support during implementation; use its supported cancellation API rather than requiring an upgrade. Fresh-session precedent: `services/finance/target_mappings.py` and `jobs/runner.py`.

## R5 — Trusted identity and private definitions

Decision: Add an optional trusted execution context outside model/tool arguments. Web and authenticated Web chat supply current Principal. Tenant MCP tokens and the existing local tenant-only CLI execute analytics reads and unsaved definitions, but cannot list or mutate private definitions without an authenticated user principal. They receive `user_context_required`; no `owner_id` argument grants identity. No new token delegation or token owner inference is introduced.

Current generic `run_read_tool` and MCP dispatch carry no principal. Propagate context through Web chat and both dispatch loops in `agent/mcp_chat.py`. Keep legacy handlers compatible. At save/approval, bind original author, current membership, definition hash and expected revision. Generic company owners cannot approve a mutation to another person's private report. Do not widen unrelated command authorization.

Alternatives: assigning a company token to the last logged-in owner, trusting a provided user ID, or treating all company members' reports as visible would violate approved privacy semantics. Extending MCP authentication is a separate feature.

## R6 — One saved-definition table

Decision: One additive table `analytics_report` stores a user/company-owned versioned definition and presentation, revision, timestamps, creation retry identity and last mutation identity/hash. A retained deletion tombstone prevents old create retries from resurrecting a removed report. No separate result, scheduling, sharing or receipt table.

Create retries with the same key and creation payload find the same identity and return its current state explicitly as a replay. Current mutation retries return the stored matching revision outcome. Older mutations after another revision fail as stale; they never overwrite it. All mutation requests bind expected revision and payload fingerprint; key reuse with a changed payload is a conflict. Existing agent proposal receipts retain exact historical action results. Direct Web retry recovery can read the current report state, including a delete receipt, through a narrowly scoped recovery operation.

Reason: US3 proves persistence across visits, author isolation, concurrent edits and uncertain saves. Browser storage would not satisfy cross-session report ownership/recovery. Existing SourceArtifact and Facts are not configuration storage. The concrete table/ownership design is subject to the repository architecture/schema review.

## R7 — Explorer state and existing chat

Decision: Keep `AnalyticsPreview` and legacy metric URLs. Add an Analytics workspace wrapper and separate explorer modules. `useRead` is suitable for catalog/list discovery, not query execution: it auto-runs dependencies and clears failed data. A dedicated hook retains draft, executed definition/result, running generation, error and cancellation state.

Use small accessible SVG charts and native tables; no chart/grid dependency is required. Decimal text is formatted through existing helpers, with numeric conversion limited to drawing coordinates. Service computes pivots/non-additive totals.

Typed analytics context extends the existing commitment-only chat annotation and message API. Explicit Discuss attaches visible context to the existing composer. Agent output uses a validated bounded definition handoff; opening never saves it. Revalidate all external/handoff definitions and scope before executing. Do not send result data in URLs.

Evidence: `unified/routing.ts`, `Shell.tsx`, `ChatPage.tsx`, `context.ts`, `useCompanyContext.ts`, `web/api.py` CopilotContext and `services/core.py` send_chat_message. Existing chat only intercepts selected work links; a new URL without the renderer/parser work is not a functioning handoff.

## R8 — Research process and remaining gates

Two bounded research agents independently inspected backend and frontend while the primary agent examined the schema, workflow and execution design. No code was changed by researchers. Their concrete findings are incorporated above. Extension configuration is absent; no pre/post hooks applied.

No unresolved technology question remains. Product scope is approved. Technical ownership/schema review and the reviewer-owned requirements checklist are separate gates; test execution and performance measurements remain future implementation work.
