
Historical contribution graph: `contribution_cost_context: {action_id, mode:
"historical"}` selects one confirmed joint contribution action. The standalone
`contribution_valuation` node compiles fixed contribution sources with coverage through
the shared SQL kernel. Response `cost_basis.kind = "contribution"` includes pinned
generation IDs, retained review IDs and loaded position counts. These counts are not
DB2 completeness; the corresponding covered/required measures express that separately.
`graph.contribution_reviews.list` accepts limit 1–50 and an opaque continuation action;
the HTTP route is `GET /analytics/graph/contribution-reviews`. Neither discovery nor
report reads create approvals or cache records. The existing visual selector preserves
this context through save/reopen and refuses text-editor conversion that would drop it.

Contribution context additionally accepts `mode: "current"`. This means unchanged
knowledge since confirmation for the selected fixed cutoff. Service snapshots expose
freshness (state, processed_event_sequence, target_event_sequence) and suppress stale
rows/groups. Graph execution performs the same cursor check after aggregate SQL and
returns `cost_basis_pending` without numeric rows if new data arrived. Current reads
require READ COMMITTED. Historical mode remains the default and does not read the live
cursor. Browser selection and saved questions preserve the optional requirement.
