# Research and review

Decision: reuse declarative model, retain old invoice keys, add explicit subtype nodes.
Rationale: saved queries must not silently change type coverage. Alternatives rejected:
narrow old invoice node; UI-only names without executable nodes; create new business tables.

Compiler audit found Node.of is not applied; fix with parent EXISTS before new line
nodes. Same-table reverse joins must use edge multiplicity/direction, not table equality.
Observed vocabularies must apply the same scope. All required fields already exist.
Document dates stored as text remain text; do not silently cast malformed external dates.
Events are historical observations; expose supersession links instead of a new status.

No unresolved clarification. Owner approved scope and main; no extension hooks present.
Derived inventory/aging, financial mapping histories and polymorphic raw evidence remain
outside this bounded catalog expansion, explicitly documented rather than implied.

## Final relationship review
Read-only independent review found two missing supported routes: customer credit lines
can credit invoice lines (not just order lines), and purchasing needs explicit routes
to commitments. Both routes were added with populated PostgreSQL regression fixtures;
the tests failed as unknown_edge before the declarations and pass afterward. Reverse
same-table target filters also receive a populated movement-return regression.
