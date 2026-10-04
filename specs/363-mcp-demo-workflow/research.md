# Research Decisions

- Reuse proposal review and confirmation: these already own privacy, policy, replay and
  stale-state checks. A second engine would violate service parity.
- Pending summaries use existing scoped cursors. Public default page, explicit legacy
  escape hatch, application default legacy; no internal consumer break is required.
- Company identity is a separate read. Open spec 362 forbids expanding its tenant object;
  use existing capability catalog for rights rather than duplicating authorization logic.
- Shipment objects and Movements answer different questions. Existing `order_explain`
  already returns held Movements; strengthen guidance, never invent an operational status.
- Add only exact document-line lookup to Finance navigation now. A universal invoice
  explanation needs a wider allocation/read audit and is not a clear bug restoration.
- Keep canonical profile unchanged; correct the contradicted authored purchase example.
- Claude scheduling and connector isolation remain outside Reality's ownership.

No unresolved design clarification exists in this clear slice. No extension hooks are
configured. Feature 363 is used because open PR #367 already claims feature 362.
