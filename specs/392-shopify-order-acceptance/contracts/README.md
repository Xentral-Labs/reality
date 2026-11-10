# Exact successor wire contract

The four methods are frozen for the Tuesday connector:

- shopify_source_order_acceptance_prepare(propose): prepare-input -> review-response.
- shopify_source_order_acceptance_review(read): review-input -> review-response.
- shopify_source_order_acceptance_accept(confirm): accept-input -> receipt.
- shopify_source_order_acceptance_status(read): status-input -> status-response.

One human/standing review boundary only. Preparing391 first is NOT required;
391 contracts and stored digests remain unchanged and never become executable.

Native schemas are *.schema.json. Examples are actual synthetic isolated native
HTTP results; accept-input.example.json deliberately contains a REDACTED invalid
proof placeholder, never an executable grant. No bearer token, signing private
key or original compact proof is included.

actual-sdk-initialize.json records a REAL authenticated current-runtime request
and response negotiating2025-03-26. Actual HTTP tools/list advertisement including
annotations is in actual-sdk-advertisement.json; extracted input schemas are in
actual-sdk-input-schemas.json. The same actual prepare/review/accept/status test
also passed negotiated2025-06-18. Native server validation remains strict even
where SDK advertisement loses top-level constraints. Match exact known schemas;
do not normalize arbitrary provider schemas or remove generic restrictions.

## Exact approval claims

Host-only Ed25519 key signs header algEdDSA, typ
`tuesday-shopify-order-acceptance+jwt`, configuredkid. Claims are closed in
approval-claims.schema.json: issuer/audience/subject/time/UUIDjti/purpose,
tenant/proposal/review/source-binding/mapping-bundle/full-plan digests plus exact
human or current standing mandate identity/revision. Five-minute proof lifetime.
The model never receives private key, bearer token or authority to sign.

Canonical digest: UTF-8 JSON, sorted object keys, no whitespace, Unicode retained
(not ASCII-escaped), no NaN. source_binding_digest is the digest of returned
source_binding; mapping_bundle_digest is the digest of returned mapping_bundle.
Use the returned opaque review_digest and plan_digest. The full plan includes
unchanged raw original line payloads; the public review_projection omits ONLY
those source-evidence duplicates and is NOT the full-plan digest input. ALL
prospective business-effect arguments remain visible. Do not recompute plan_digest
from that trimmed projection or accept model-supplied replacement digests.

Human proof cannot claim mandate fields. Standing proof must name the current
configured mandate ID/revision/subject/profile/not_promised/currency and obey
order/amount/unit cumulative caps. source_created_after is strictly exclusive
against ORIGINAL createdAt, never processedAt/proof time. Historical backlog or
exact-boundary order requires a separate explicit scope/human decision.

## Meaning and limits

See source-v2.md for complete selected evidence, typed not-applicable nulls and
source comparisons. No amount override, date default, approximate discounted
price, fake local Principal or generic confirmation. Current explicit timezone
source and exact provider processedAt instant determine the interpreted date;
the legacy midnight-as-stated-day sentinel does not apply to a known instant.
Canonical complete positive-limit credit is queried at CURRENT time, never a
permanently frozen review-time cutoff. Original source and ImportJob.input stay
unchanged; accepted intake completes the job and retains canonical outcome.

Successor buyer/readiness data is explicitly historical review evidence, not
legacy389 overall intake status. Dedicated successor status validates original
proof identity at acceptance time, waits an in-flight acceptance row, performs
no dispatch and never renews expiry. Unknown/lost response reconciles that SAME
proposal/receipt. A different proof cannot alias a completed intent.

Default-deny separate private process-owner-only policy file:
REALITY_SHOPIFY_ORDER_ACCEPTANCE_POLICY_FILE. issuer-policy.schema.json describes
its exact scope and caps. No old99 application adapter, existing pilot install,
new live grant, provider operation, global worker, payment, inventory movement,
fulfillment or settlement is supplied by this native packet.
