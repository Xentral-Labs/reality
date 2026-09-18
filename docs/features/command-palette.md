# Global command palette

Status: implemented incrementally; release acceptance is pending. The authoritative
requirements and open work are [spec 237](../../specs/237-global-command-palette/spec.md),
[the task list](../../specs/237-global-command-palette/tasks.md) and
[verification evidence](../../specs/237-global-command-palette/verification.md).

## Entry and outcomes

The shared search button and Command/Ctrl+K open the same company-scoped palette.
Existing modal dialogs retain keyboard precedence. Selecting a destination opens it;
selecting an action opens its existing form and confirmation flow. Search never
executes a business mutation. Capabilities without a Web form open their explanation
in Tools. Calculated reports use their existing readers; private reports reopen the
owner-checked editor, and historical templates still require an explicit date.

## Retrieval and identity

Read-only POST `search/query` and `search/resolve` routes call the shared global search
service. Seven providers cover partners, items/locations, orders, finance, shipping,
Reality/evidence and private reports. Every table and joined alias remains tenant
scoped; report ownership and restricted lesson access are checked in the service.
Opaque physical keys deduplicate records, including payments represented by their
cash ledger entry and shipments with several matching packages. Human numbers are
searchable references, never identity. Source payloads are not scanned or altered.

Matching orders raw references, normalized exact matches, prefixes and single-edit
human words. Identifiers are never fuzzily corrected. Original display values are
preserved. Candidate matching precedes bounded ordering and keyset continuation.
Migration 0063 owns versioned SQL functions and supporting indexes; no runtime
startup installs search infrastructure or adds business fields.

The palette combines those providers with Actions, Pages, Help and Companies.
Preview limits are four entries per group and twelve overall. Group expansion has
a fifty-entry page limit. Failed providers are explicit and independently retryable.
Query/company changes abort requests and invalidate stale responses.

## Personal shortcuts and handoffs

Favorites and recent destinations are scoped to user and company. Browser storage
holds bounded target references, never labels or business snapshots. Protected
references are resolved again before display. Clearing history preserves favorites;
clearing shortcuts removes both. Logout/session expiry clears rendered shortcuts.

Overdue invoice destinations use the canonical aging observation before register
pagination. Blocked outbound work opens the existing fulfillment-blocker reader.
Chat handoff fills an editable draft; an optional selected record is reauthorized and
shown as removable context. It does not send a message.

## Verification boundary

Focused matching, migration, service, ownership, HTTP and browser proofs are recorded
in the linked verification document. The full suite initially had three integration
failures; their targeted fixes passed. Final full-suite rerun, broader interaction
coverage, sustained ten-user latency budgets and controlled cold-cache evidence are
still open. Do not describe this feature as release-ready from the smoke measurements.

Exact destination presentation: order/master results outside the loaded register
page use the shared selected-record preview, isolated from register toolbar styling.
Inline and off-page compact sections respond to their available container width;
loaded selected order/master details are brought into view. Existing evidence,
Reality links, actions and Inspector fallbacks remain unchanged. See spec 237's
verification log for the live family matrix and 390px visual checks.
