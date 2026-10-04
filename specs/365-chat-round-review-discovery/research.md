# Research Decisions

- Decision: Fix the actual movement selector first. The live page claimed query
  shipment while returning opening_stock, receipt and return; the shared builder
  configured no searchable Movement column. A small prompt-only test hid the defect.
- Rationale: Existing typed Movement.type is the shortest true filter. Both paged and
  legacy adapters already share the builder; no new search API or authority is needed.
- Alternatives: A longer prompt, regex prose rewrite or second model judge cannot
  prove consistency. A typed deterministic daily report is a material additional
  product contract and is deferred unless the corrected live mission still fails.
- Decision: Explicit standalone generic confirmation presentation; retain existing
  intake tool bindings. Existing mcp_topics already says review, but represented tools
  never reach the fallback standalone entry.
- Rationale: Catalog metadata can expose the general boundary without changing any
  application command, decision policy or grant.
- Decision: External recurring qualification records support/gaps. The shared
  scheduling contract exposes no generic MCP provider-routine controls. Never infer
  a next run from an unpersisted timetable or treat manual runs as scheduled.

Read-only research under speckit-plan reviewed both provider loops and stream behavior.
If a future typed finalization is designed, raw streaming must also be guarded; a
post-hoc saved-answer fix alone cannot guarantee what users see.

## Actual daily mission argument failure

The isolated source API selected the corrected shipment evidence, then its provider
called shipments_list(limit=...). That input is absent from the declared schema and
raised TypeError at the handler. Canonical schema-based name refusal is preferable
to swallowing TypeError (which can hide bugs) or adding a fake service alias.
