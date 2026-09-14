# Feature: Explain

`reality explain commitment ID` returns a structured, tenant-scoped trace containing:

- promise, direction, parties, item, location, quantity, due date, and state;
- active/released/consumed reservations;
- linked fulfillment movements and derived fulfilled/open quantity;
- DocumentLine → Document → SourceRecord evidence when present;
- original raw source payload;
- relevant incoming commitments and computed risk/shortage.

The trace traverses opaque foreign keys, never document numbers. A commitment without
document evidence remains explainable and explicitly reports that no source chain is
present. Cross-tenant IDs return not found.
