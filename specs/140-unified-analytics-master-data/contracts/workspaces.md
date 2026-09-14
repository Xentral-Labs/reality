# Workspace contracts

All routes below are under `/api/tenants/{tenant_id}` and require existing authenticated ordinary-company authorization.

- `GET /analytics?days=7|30|90`: `{position,series,window,observed_at,definitions,coverage}`. Position: open, fully_reserved, needs_reservation, overdue, coverage_percent (null with no open commitments), unknown_due. Series: date, created, shipped counts. Window uses UTC today minus days-1 through observed_at.
- `GET /analytics/contributors?metric=open|fully_reserved|needs_reservation|overdue|unknown_due|created|shipped&days=...&day=YYYY-MM-DD&page=...`: bounded `{items,page,scope}`; optional day applies only to activity metrics and must lie in the window. Items identify actual Commitment or Movement with business labels and timestamp.
- `GET /master-data?family=customer|supplier|item|location&q=&page=1&include_inactive=false`: bounded register with server total and stable label/ID order.
- `GET /master-data/{family}/{id}`: scoped snapshot, expected_revision, active flag, display fields and source link.
- `POST /master-data/prepare`: `{family,operation:create|update,request_id,record}`. Basic fields only. Update requires id and expected_revision from detail. No business write. Same request/intent returns original proposal; changed intent conflicts.
- `GET /master-data/proposals/{id}`: canonical input and status; pending output contains the original field-change preview, executed output contains the authoritative receipt and record links. Recorded input remains available after execution. Only the six reference tools are admitted.
- `POST /master-data/proposals/{id}/confirm`: `{confirmed:true}`. Fresh principal check and existing canonical executor. No new intent accepted. Existing rejection endpoint is reused. Executing remains explicit, with no automatic mutation retry.

Frontend routes `/app/analytics` and `/app/master-data` add bounded days, metric/day, family, record and active state to the URL selection allowlist. Company changes clear selected records/proposals and filters. Master proposal review can be reopened from Decisions and Chat using its persisted ID.

## Metric definitions

All current-position metrics count customer-delivery Commitments in the selected
company whose status is open and whose correction-aware remaining quantity is
positive. Effective quantity and due date use the shared latest-revision reads;
remaining quantity and active reservations use the existing delivery expressions.

| Metric | Question and unit | Time and contributor predicate |
| --- | --- | --- |
| open | How many delivery commitments still have work? Count of Commitments | Current position, independent of chart period |
| fully_reserved | How many have their full remaining quantity reserved? Count of Commitments | Active reserved quantity >= remaining quantity |
| needs_reservation | How many lack full reservation coverage? Count of Commitments | Active reserved quantity < remaining quantity |
| overdue | How many open commitments have passed their stated due time? Count of Commitments | Effective due time < observed_at |
| unknown_due | How many have no stated due time? Count of Commitments | Effective due time is null; not silently overdue |
| coverage_percent | What share of open commitments is fully reserved? Percentage | fully_reserved / open × 100; null when open is zero |
| created | How many customer-delivery commitments were recorded? Count of Commitments | created_at in each UTC day and selected window; includes retained commitments regardless of current status |
| shipped | How many effective positive shipment movements occurred? Count of Movements | occurred_at in each UTC day/window; excludes originals and compensations referenced by MovementCorrection; an uncorrected replacement counts at its own occurrence time |

Coverage uses the fully-reserved and open contributor lists, not loaded-row totals.
It describes reservation coverage, not shipment readiness: holds or other blockers
remain visible in the delivery case. Quantities across units are never added.
Historical counts describe the records currently retained, with corrections applied;
this is not an as-of reconstruction of what the system knew on a past date.
