# Research: Customer Exchange

Code reading on 2026-09-28 against `origin/main` (`78dcae55`). Paths are relative to
`packages/reality-core/`.

## R1. Where the exchange lives

**Decision**: A new table `customer_exchange`, linking one customer return (a return
`movement` or a `return_announcement`) to one replacement `commitment`.

**Rationale**:
- Constitution III: the exception derivations join and filter on it every evaluation
  (FR-005 to FR-007), and the credit, explanation and delivery reads join on it.
- Documents may not carry fulfilment or return state (hard rule 2), so no document field.
- A column on `commitment` or `movement` would need two nullable references (movement or
  announcement) plus a reason on a record read in dozens of places, and all three tables are
  reference-governed (`catalogs.py` `REFERENCE_GOVERNED_RECORDS`).
- `supply_assignment` (`db/core.py`, migration `0090_supply_assignments.py`) is the precedent:
  an append-only link between two commitments with a quantity check and an idempotent source
  record.

**Alternatives rejected**: a zero-price order document for the replacement (today's demo:
a separate order carries no link, and a document line makes the replacement billable, so
`shipped_not_billed` and the invoice delivery guard would need exchange exceptions);
a third `Commitment.type` (the `ReturnAnnouncement` docstring explains why 17 two-way
branches forbid it).

## R2. What the replacement is

**Decision**: A `customer_delivery` commitment with `amount=0`, no `document_id` and no
`document_line_id`, to the returned delivery's customer, from its company, at a stated
location (default: the returned delivery's location).

**Rationale**: `create_commitment` (`services/core.py`) already accepts no document, and
fulfilment readiness has a branch for it. `_order_line_promises`
(`services/exceptions.py`) inner-joins document lines, so a document-less promise is never
`shipped_not_billed` (FR-006 needs no change to that class) and never billable. The delivery
work list (`services/delivery_reads.py::_query`) outer-joins party, item and location only,
so the replacement appears for reservation and dispatch like any other promise.

## R3. Derivation changes

| Class | Change |
|---|---|
| `returned_not_credited` (`_return_exceptions`, customer side only) | `owed = min(returned, billed) - credited - exchanged_arrived` |
| `credited_not_returned` (same body) | `excess = credited - (returned - exchanged_arrived)` |
| `announced_return_not_arrived` | unchanged judgement; values and trace name the exchange and replacement (FR-007) |
| new `exchange_without_return` | an exchange whose announcement was withdrawn, whose replacement has shipped and against which nothing arrived (US2.4) |
| `shipped_not_billed` | none (R2) |

`exchanged_arrived` counts, per original commitment, the exchanges whose replacement is
not cancelled, capped by what has arrived: a movement-based exchange counts its quantity;
an announcement-based one counts up to `arrived_against_announcement`. A cancelled
replacement counts only what it shipped (FR-008), in the ratio of exchanged to replacement
quantity. The supplier branch of `_return_exceptions` stays unchanged.

Exchanges are read once per evaluation through a new cached input in
`services/exception_inputs.py` (spec 181: no per-commitment queries).

## R4. The credit guard

**Decision**: `uncredited_return_quantity` stays as it is. A credit after an exchange is
accepted and reported as `credited_not_returned` for the quantity settled twice (spec edge
case). Refusing it would contradict sources that state credits the company must record.

## R5. Review route

**Decision**: The state-bound delivery review used by `return_disposition`
(`services/return_disposition_actions.py`, `services/delivery_actions.py`): a
`_delivery_review` token bound to the returned delivery, the return or announcement and the
remaining exchangeable quantity; verification against the recorded effect. `return_announce`
is a plain proposal and does not satisfy FR-010.

## R6. Surfaces and gates

Precedent wiring for `return_disposition` and the gates a new tool, table and event hit:

- Tools: `tools/application.py` `TOOLS` and the `_action_id` set; `services/delivery_actions.py`
  (eligible, review, detail, unresolved guard, reconcile).
- MCP: `mcp/catalog.py` `ADDITIONAL_PROPOSAL_TOOLS` and a read `MCPToolDefinition`;
  `config/tool_catalog.json` `mcp_topics`; `config/command_catalog.yaml` (command,
  `agent_command_coverage`, `capability_guidance` for the read).
- CLI: `cli/app.py` read, propose and confirm commands.
- Web: `web/api.py` `DeliveryActionPrepare.tool`, a read endpoint and the sandbox read
  allowlist; `apps/web/src/unified` action discovery, card, Warehouse movement row action,
  `MovementExplanation` labels in four languages.
- Catalogs: `action_discovery.json`, `apps/web/scripts/fixtures/action-reference.json`,
  `resource_catalog.yaml` (`return` resource tables and German label),
  `service_refusals.json` and `refusal_ratchet.json`, `tenant_isolation_catalog.yaml`,
  `business_event_catalog.yaml`, `operational_exception_catalog.yaml`, `data_model.yaml`,
  `reporting_graph.yaml`, `services/interactions.py` stage pattern,
  `services/tenant_policy.py` practice operations, `business_locks.py` delivery writers,
  `catalogs.py` service and event-module lists, `services/projections.py`
  `TIMELINE_SILENT_SUBJECTS`.
- Pinned counts: command count, event count, tenant-isolation discovered operations
  (`tests/test_application_catalog.py`); schema index `later_tables`; reporting-graph coverage.
- Docs: `make docs-generate` output, including `config/product_advisor_knowledge.json`.

## R7. Existing behavior to replace

- `tests/scenarios/test_catalog_stock_and_returns.py::test_an_exchange_moves_no_money_but_reads_as_uncredited_and_unbilled`
  becomes the F07 proof.
- The demo exchange (`services/demo_profile.py`, SO-033/SO-034) records an unlinked return
  and a zero-price order. It stays unchanged in this feature: changing seeded demo data needs
  a profile version (company setup contract). A follow-up may move it to a recorded exchange.

## Implementation notes (T005–T013, 2026-09-28)

- The exchanges input uses the evaluation cache `_cached` in `services/exceptions.py`
  rather than a new `_ExceptionInputs` property; one read per evaluation either way.
- `customer_exchange` joins `supply_assignment` in the `operational_edge_workflows`
  reporting-graph deferral instead of becoming a graph node.
- A review whose state changed while the exchange stays valid is refused with the shared
  `review_delivery_changed`; one that became invalid is refused with the exchange's own code.
- The two tools and their tenant-isolation entries (and the pinned discovered-operation count,
  587 → 589) moved into T012 so no commit leaves the catalog gates red.
