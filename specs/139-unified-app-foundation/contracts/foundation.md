# Foundation interface contracts

All paths below are under the existing authenticated `/api/tenants/{tenant_id}` boundary. Normal tenant membership and ordinary-company policy are required. Foreign IDs and unauthorized related records do not disclose data. These additive contracts are implemented behind the opt-in frontend rollout.

## Delivery reads

`GET /delivery-work?page=1&size=50&q=&status=open`

- Customer-delivery commitments only; cap size at 100.
- Effective quantity/date and correction-aware fulfillment determine filters and counts before paging.
- Return `{items, page, scope, observed_at}`. Rows carry opaque commitment/document/line/reference IDs, display labels, unit, effective quantity/due date, fulfilled/open/reserved decimal strings and authoritative blockers.
- No page-local aggregation as a tenant total. Stable effective-date/ID ordering.

`GET /delivery-work/{commitment_id}`

- Return `{case, inventory, links, history, observation}`.
- Case remains readable after fulfillment. Inventory is explicitly item/location scoped.
- Links have `{kind,id,label}` for actual shortest relationships, including DocumentLine where relevant.
- History is a bounded related-event read with `has_more` and an opaque next cursor; a separate cursor request retrieves the next page without widening company scope.
- Missing evidence/reference/coverage is explicit. No invented status, due date or shortage.

Existing commitment inspector delegates to the same service semantics. Existing dashboard responses gain sample-scope/completeness metadata where needed, preserving current fields.

## Proposal preparation and review

`POST /delivery-actions/prepare`

Body: `{request_id, tool, arguments, session_id?}`. `tool` is `reserve` or `movement_create` with `movement_type=shipment` only. Validate the existing tool's required reference/tracking fields. Reject reserved internal metadata and unknown fields. Session, if provided, must belong to the current tenant.

Response: `{id, tool, status, review, receipt, verification, links, observation, observation_error}` including stable proposal ID, normalized intent, labels, effect, expected quantities, review token and recorded review-time scope. Preparation performs no business mutation. Same tenant/actor/request identity and same intent returns the same result; changed intent conflicts. The request token is not a credential and is never a substitute for authorization.

`GET /delivery-actions/{proposal_id}`

Return original review, exact intended arguments, current proposal state, correlated recorded effect and separately fresh/failed current observation. This direct lookup is the reload/recovery path; do not scan a pending page for an executing result.

`POST /delivery-actions/{proposal_id}/review`

For eligible old unversioned pending proposals, obtain a state-bound review without executing. Existing reviewed proposals return their immutable review or stale indication; a materially changed intent/state needs rejection/replacement and fresh confirmation. Competing tabs cannot obtain conflicting approvals for the same intent.

Existing `POST /change-proposals/{id}/approve` gains `review_token` and explicit `confirmed: true` for reviewed delivery proposals, retaining optional `session_id`. It enforces token/state under the shared guard and canonical proposal executor. Raw new business arguments are never accepted at confirmation. Every supported adapter must enforce the same rule. Existing rejection endpoint remains the rejection path. CLI direct commands continue through the guarded shared services; there is no CLI proposal-approval command to upgrade.

Old pending proposals remain readable; legacy UI and MCP obtain a review token before deciding these actions. Other command families are unchanged. Executed replay rechecks access and returns stored effect; optional chat notification must not duplicate on replay or turn a recorded business success into an apparent execution failure.

## Recovery

Existing proposal status tool and new detail endpoint expose consistent recorded/verified/unknown semantics. Immutable action-correlated events verify reserve and shipment. A later consumed Reservation or corrected Movement does not erase evidence of original execution; current observation explains subsequent changes.

No handler reexecution is permitted as a recovery technique. Relevant unresolved activity must be exposed and block a dependent new mutation whose preconditions cannot be established. Verification can settle an executing proposal only from sufficient matching evidence under the same guard.

## Chat context

Existing message body `{message}` gains optional `{context:{kind:'commitment',id}}`. Validate context before provider calls. Persist a server-created versioned context annotation with the message for visible historical context; legacy plain messages remain unchanged. Do not trust annotations supplied in ordinary user text. Model-proposed supported actions go through the same review preparation path.

## UI state

- Routes: Home, Chat, Work and Decisions. Company/commitment/proposal/session URL selection is encoded, allowlisted and authorization-checked.
- Company changes cancel outstanding reads and invalidate old response generations. Never display another company's cached case/draft.
- Shared action card states: editing, preparing, review, confirming, rejected, stale, result, unresolved and observation-unavailable. Map to existing backend authority; do not store a parallel execution state.
- Dirty intent clears its review capability. Prepared proposal IDs survive navigation/reload through URL and persisted server state.
- Closing a panel is not rejection. Cancellation and explicit Reject are distinguished.
- Launcher has business descriptions and prerequisites, bounded reference search, and no unsupported command execution.
- Source HTML/scripts are not rendered; use safe existing Markdown and escaped payload inspection.


## Reference selection and reconciliation

`GET /delivery-references?family=lot&commitment_id=...&q=...` accepts `lot`,
`serial_unit` and `handling_unit`. It returns at most 50 actual tenant-scoped
choices and `has_more`; lot/serial choices are item-scoped. Selection IDs remain
opaque and are revalidated by the shared domain validation at review and execution.

`POST /delivery-actions/{proposal_id}/reconcile` settles only a sufficiently
verified, already-recorded effect. Missing evidence remains unknown. Existing
Inspector reads additionally accept `document_line`, `source_record` and
`business_event` and preserve escaped lossless payloads.

The contextual Chat provider receives the same bounded delivery service snapshot
as the selected case. Existing tool definitions stay canonical; no duplicate
read-model authority or unrestricted command gateway is introduced.
