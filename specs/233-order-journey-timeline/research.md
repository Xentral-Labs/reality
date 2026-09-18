# Research

- Decision: reuse `timeline_activity` serialization with a private SQL subject criterion. Rationale: existing titles, values, cursors and tenant enforcement stay consistent; filtering after pagination would lose relevant history. Alternative: duplicating event serialization rejected.
- Decision: use typed, tenant-scoped membership subqueries through document/line, commitment, reservation and movement. Facts match exact typed subjects and ledger entries attach directly to the root document. Rationale: shared item/customer/source do not establish process identity. Unbounded graph traversal rejected.
- Decision: source/evidence events are terminal context; plotted business events occupy five lanes. Rationale: preserve provenance without confusing evidence with facts.
- Decision: preserve recording time and make range controls local viewport choices. Existing timeline `hours` filters occurred time and must not be silently reused for a recorded-time chart.
- Decision: current record FKs define explicit relationship lines; current links are not represented as event causation or a historical snapshot.
- Decision: no first-release invoice traversal or order status headline. Canonical operational summaries can be added separately without implying completeness from this loaded history.

Repository research inspected services/core.py (document_detail, timeline_activity), db/core.py, existing Inspector and recorder helpers. A read-only research agent independently confirmed membership paths and the absence of an existing exact order filter.
