# Verification

## Local source and adapter evidence

- 336 isolated PostgreSQL native/legacy/shared-intake/catalogue/action-reference
  tests passed, with12 existing SQLAlchemy deprecation warnings. This includes68
  dedicated acceptance tests, all using owned disposable synthetic databases.
- Positive paths cover BOTH exact external human and current finite standing
  authority, canonical sales-order Document/Line and delivery Commitment creation,
  atomic original-proof receipt, unchanged original SourceRecord/ImportJob.input,
  completed import and zero Movement/LedgerEntry/payment/fulfillment effects.
- Meaningful reviewer regression RED: same standing ID revised EUR->USD wrongly
  applied an otherwise eligible second order. GREEN after refusing any different
  OR missing prior receipt currency BEFORE aggregation. All same-ID revisions
  retain cumulative exposure; no nominal FX sum, filtering or budget reset.
- Real two-session tests cover same-order competing proposals, same-proposal lost
  response retry, and a DIFFERENT reader token waiting for the original in-flight
  acceptance transaction (pg_blocking_pids proves the row-lock wait).
- Lost response AFTER commit reconciles the same original receipt with no resend.
  Fault after canonical writes and host policy revocation after the effect boundary
  roll back all business records AND approval evidence. Wrong source/plan/issuer/
  subject/purpose/proof expiry, token/policy/ref/calendar changes, quota exhaustion,
  incompatible currency revision and unresolved source/credit/calendar evidence
  cannot apply. Generic confirmed execution is refused.
- Positive source cases use realistic provider-documented null fee/duty evidence
  with complete empty lists, without manufacturing zero. Rounding/unrepresentable
  Numeric(18,4), ancillary charges, partial/edited quantities and missing selected
  evidence stay held. Midnight/offset processedAt dates use the actual instant,
  not the legacy midnight-stated-day sentinel. Newly posted debt is evaluated at
  current time, not hidden behind a frozen review-time query cutoff.
- Actual authenticated current MCP ASGI tests negotiated EXACT2025-03-26 and
  2025-06-18. Prepare/review/accept/status each returned200, unauthenticated401,
  ungranted generic confirmation denied. Original tokens/signing secrets/proofs
  are absent from repository evidence. Actual SDK schemas/annotations and
  redacted synthetic examples are in contracts/.

## Quality and review

Full Ruff, specification policy and business annotations passed.483 Web contract
tests, shared four-language i18n audit, Web formatting and TypeScript/Vite build
passed. Generated docs preserve maintained formatting;145 docs tests, formatting
and VitePress build passed. No new form/layout exists and these checks do not
claim visual, native Desktop or real-model acceptance.

Coordinating reviewer independently inspected source/profile/storage guards,
current token/delivery/finance/source/reference/calendar locks, closed canonical
effects, original-proof replay/status and immutable-source semantics. The mixed
currency finding was corrected with the observed RED/GREEN proof above. No
remaining inspected source blocker was reported, subject to final checks.

Full hosted CI for the exact commit remains a separate required gate; do not infer
it from the local focused336 tests. The earlier391 PR412 exact b55d41c7 passed
all26 hosted jobs; that is not a392 CI claim.

## Rollout limits

NO existing company database, provider/model call, old99 application, migration,
pilot installation, native grant, global worker or public deployment was used.
This is current native implementation plus isolated evidence, not full Tuesday
Main/Operator execution or production/autonomous O2C acceptance.

An unchanged upstream version previously captured with narrower v1 fields remains
a canonical conflict when recaptured with a different richer payload. The guard
is explicitly tested and unchanged. First acceptance walk must use a genuinely
new/current source first captured with v2, or a future separately reviewed
profile/enrichment transition. Never edit Shopify or invent updatedAt to force
eligibility; existing#1004 is not silently promoted.

Supported scope is simple same-currency undiscounted source-backed order meaning,
explicit not_promised delivery terms, current configured calendar and complete
positive-limit credit. Unsupported commercial/reference meanings remain typed
holds for Now. Native392 default-deny issuer policy and separately granted tools
must be configured later; old99 and previous buyer/proposal contracts remain
unchanged. Payment, stock, fulfillment and settlement require separate authority.
