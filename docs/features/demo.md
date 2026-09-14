# Feature: Demo

The guided demo is a 1–2 minute onboarding defined by `docs/DEMO_SPEC.md`. Every step
shows the business event, proposed application command, resulting primitive, and next
explanation link. Enter executes, edit changes the proposal, and quit leaves committed
history intact.

`demo --auto`, CLI interaction, and Web onboarding must call the same services and
produce equivalent domain state. A non-empty tenant is never reset implicitly; the UI
offers a fresh demo tenant. Tests compare the resulting Source, Evidence, Reality,
inventory, fulfillment, and trace IDs rather than terminal formatting.

The guided demo manifest is versioned as `guided-demo-v1`. It inventories every record
family produced by a real run and compares six authoritative sections: reference data,
Source, Evidence, Reality, derived outcomes, and explanation. Product Web keeps empty
company creation separate from an explicitly confirmed demo company. The demo has no
LedgerEntries or open items, so its financial expectation is explicitly empty.

A completed demo rerun is idempotent. A failure after confirmed company creation is
reported truthfully and may leave a partial tenant for explicit operator handling; it is
not described as safely retryable and is never deleted implicitly.
