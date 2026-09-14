# Contract: Storyline HTTP surface

**Spec**: FR-001, FR-003 to FR-005, FR-009 to FR-013, FR-018, FR-021 | Router
`reality.web.storyline_api`. All routes require a signed-in account; tenant routes carry the
ordinary tenant surface dependency. Errors follow the Playground router: 404 not found,
409 conflict, 422 invalid, 429 quota with `{detail, code, quotas}`.

## Account scope: `/api/storyline`

| Method and path | Purpose | Body / query | Returns |
| --- | --- | --- | --- |
| `GET /api/storyline/library` | list built-in and imported packages | | `{items: [{key, version, title, author, chapters, origin: builtin|import, imported_at?, run?: {run_id, tenant_id, status, current_chapter}}], enabled}` |
| `GET /api/storyline/library/{key}/{version}` | one package document | | the document as JSON, `Content-Disposition` for `?download=yaml` |
| `POST /api/storyline/library?filename=` | import | raw body, `Content-Type: application/yaml` or `application/json`, ≤ 200 000 bytes | `201 {key, version, title, warnings}` or `422 {errors: [...]}`; `409 {code: "exists"}` unless `?replace=true` |
| `DELETE /api/storyline/library/{key}/{version}` | remove an import | | `204`; built-ins return `405` |
| `POST /api/storyline/runs` | start or resume a run for a package | `{key, version, request_key, confirmed}` | `{run_id, tenant_id, status, current_chapter}`; resumes the active run of that storyline key; starting another version while a run of the key is active returns `409 {code: "active_run"}` and the person restarts or archives first |
| `GET /api/storyline/runs/{run_id}/draft` | export the run as a draft package (FR-021) | `?format=yaml` | the draft document; a run the account does not own is `404` |

## Tenant scope: `/api/tenants/{tenant_id}/storyline`

| Method and path | Purpose | Body / query | Returns |
| --- | --- | --- | --- |
| `GET …/storyline` | run state for this company | | `{run_id, key, version, chapters: [{key, title, status: done|current|upcoming, step_id?, marker?, refused?}], current_chapter, branches}` (status derivation: plan §2; free play is a browser-only mode) |
| `GET …/storyline/chapters/{key}` | chapter texts, resolved inputs, view, branches, preconditions | | `{chapter, resolved_input, preconditions: [{kind: reference|finding_present|finding_absent, name, holds}], can_run}` |
| `POST …/storyline/chapters/{key}/prepare` | prepare the chapter's proposal | `{request_key}` | `200 {step_id, proposal_id, preview_revision, review}` for a prepared proposal; `200 {step_id, refused: {code, detail}}` when the system refuses the preparation (the step is kept, the trace has a `kind: error` entry); read chapters return `200 {step_id, results: [{tool, result}]}` |
| `POST …/storyline/chapters/{key}/confirm` | confirm | `{step_id, preview_revision, confirmed: true}` | the Playground step read (`receipt`, `observation`) |
| `POST …/storyline/chapters/{key}/reject` | reject | `{step_id, confirmed: true}` | the step read |
| `POST …/storyline/branches` | record a branch choice | `{chapter, branch}` | `{current_chapter}` |
| `POST …/storyline/restart` | fresh practice company for the same package | `{request_key, confirmed: true}` | `{run_id, tenant_id}` (new company) |
| `GET …/storyline/trace` | call trace | `?step_id=`, `?after_ordinal=&limit=` or `?free=true` (calls outside any chapter) | `{items: [{ordinal, step_id?, chapter?, kind, name, access, actor, proposal_id?, marker?, before_exceptions?, input, result, duration_ms, recorded_at}], has_more}` |
| `GET …/storyline/delta` | delta after a marker | `?after_sequence=&after_at=&record=<type:id>`, `?step_id=` or `?ordinal=` (the marker of one confirmation outside the story; `404` when that call has none) | see below |
| `GET …/storyline/tool-reference/{name}` | explanation of one tool or view (the single source for the protocol; `application-reference` is unchanged) | | `{key, kind, label: {en, de?}, description, access, parameters, projections, docs_url}` |

### Delta response

```json
{
  "range": {"after_sequence": 4830, "latest_sequence": 4835, "available": true},
  "events":     [{"sequence": 4831, "type": "payment.recorded", "subject_type": "payment", "subject_id": "pay_…", "title": "…", "action_id": "act_…"}],
  "facts":      [{"id": "fct_…", "subject_type": "payment", "subject_id": "pay_…", "predicate": "…", "value": "…", "recorded_at": "…"}],
  "records":    [{"record_type": "payment", "record_id": "pay_…", "label": "…"}],
  "exceptions": {
    "raised":  [{"id": "exc__unmatched_financial_event__pay_…", "class_id": "unmatched_financial_event", "label": "…", "title": "…", "clears_through": "…"}],
    "cleared": [{"id": "exc__party_hold_unreleased__pty_…", "class_id": "party_hold_unreleased", "label": "…"}]
  },
  "graph": {
    "record": {"record_type": "payment", "record_id": "pay_…"},
    "nodes": [{"record_type": "party", "record_id": "pty_…", "label": "…", "new": false}],
    "edges": [{"from": "payment:pay_…", "to": "document:doc_…", "relation": "settles", "new": true}]
  }
}
```

Every item carries what the web needs to open its ordinary surface: `record_type` and
`record_id` for the Inspector, `id` for the Facts register and the Exceptions page.

## Changes to existing routes

- `GET /api/tenants/{t}/timeline` gains `after_sequence` (forward, ascending, bounded by
  `limit`, mutually exclusive with `before_sequence`).
- `catalogs.load_catalog_labels()` exposes the resource catalog's per-language labels for
  commands, views, projections, exceptions and workspaces; `application-reference` is
  unchanged.
- The web app gains an HTTP middleware that records `GET` views of storyline companies (route
  template, parameters, status); the dispatcher records reads, proposals, confirmations and
  rejections itself. Both are inert for tenants without a storyline run.

## Non-changes

- `/api/playground/*` stays as it is; the storyline service calls the Playground services in
  process, not over HTTP.
- No SSE and no websocket; the web polls `activity-signal` and the trace at the HomePulse
  cadence.
