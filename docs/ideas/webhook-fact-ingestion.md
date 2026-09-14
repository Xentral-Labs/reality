# Idea: Validated webhook ingestion into source-supported Facts

**Status:** Brainstorming — not approved, not an implementation specification

## Problem

Reality has a tenant-scoped registry of external systems and their declared
capabilities, but that registry does not yet represent live connectivity. An
enterprise agent or another external system should be able to deliver webhook events
without bypassing Reality's evidence model. Operators also need a direct way to test
from the integration list whether endpoint authentication, payload identity, mapping,
and Fact creation would actually work.

The tempting shortcut is `webhook JSON -> Fact`. That would lose the original request,
make retries and mapping changes hard to explain, and create operational truth from an
unvalidated network payload. The smallest coherent flow is instead:

```text
webhook request
      |
      v
authenticated webhook delivery
      |
      v
immutable SourceRecord + ImportJob
      |
      v
versioned, validated mapping
      |
      +-- unmapped / rejected / quarantined
      |
      v
source-supported Fact(s) + Business Event(s)
```

This preserves the core invariant:

```text
Source -> Evidence -> Reality
```

A Fact created from a webhook always links to the immutable SourceRecord that supports
it. The original payload remains available losslessly even when no Fact can be created.

## Proposed product concept

Extend a configured **SourceCapability** with an optional **WebhookBinding**. The
binding describes how one authenticated endpoint accepts a declared upstream event
type and which versioned mapping contract may interpret it.

From the Integrations list an operator can:

1. select a source system and one declared capability;
2. configure its webhook authentication and routing contract;
3. copy the tenant-specific endpoint URL;
4. send or paste a representative test delivery;
5. run **Validate webhook** without creating live Facts;
6. inspect transport, authentication, identity, schema, and mapping results;
7. explicitly activate the validated binding;
8. monitor received, duplicate, unmapped, quarantined, failed, and interpreted
   deliveries.

Creating or activating a binding is a confirmed mutation. Receiving a delivery through
an already activated contract is automated source ingestion and does not require a new
human confirmation for every event.

## Relationship to the existing integration list

The existing SourceSystem and SourceCapability registry remains the starting point.
It must not claim connectivity merely because a capability was declared.

Each capability should expose a derived readiness state:

| State | Meaning |
|---|---|
| `declared` | Source and intended target are known; no live webhook exists |
| `configured` | Endpoint/authentication and mapping draft exist |
| `validated` | A test delivery passed the current contract version |
| `active` | Live deliveries may be interpreted automatically |
| `degraded` | Recent live delivery or mapping checks are failing |
| `disabled` | New deliveries are rejected or retained without interpretation according to policy |

Readiness is not a manually editable status field. It is derived from binding
configuration, validation evidence, activation, and recent delivery outcomes.

The Integrations list should show per capability:

- declared `source_type -> target_type`;
- whether a webhook binding exists;
- authentication mode and secret rotation state, never the secret;
- mapping contract version;
- last validation result and time;
- last delivery and interpretation outcome;
- a **Validate** action and links to recent deliveries and their SourceRecords.

### Concrete capability target map

The mechanism should eventually support the capabilities already named in the
connector catalog, plus explicitly approved additions. Concrete examples make the
intended breadth visible without claiming that all mappings already exist:

| Source example | Upstream event/object | Intended Reality target | Likely first transport |
|---|---|---|---|
| Shopify | order created/updated | sales-order Source/Evidence, then Commitments | Webhook plus reconciliation pull |
| Shopify | product/customer updated | Item or Party Evidence | Webhook or pull |
| Shopify | fulfillment/refund | fulfillment or sales-refund Evidence/Reality | Webhook |
| Stripe | payment intent/charge/refund | payment or refund Evidence, then financial Reality | Webhook plus reconciliation pull |
| Shopify Payments | transaction/payout/dispute | payment, payout, or dispute Evidence | Webhook plus reconciliation pull |
| PayPal, after catalog approval | payment capture/refund/dispute | payment, refund, or dispute Evidence | Webhook plus reconciliation pull |
| ERP such as Xentral/Odoo/weclapp | order, purchase order, item, party, payment | matching registered target type | Provider-dependent webhook or pull |
| CRM such as Salesforce/HubSpot | account/contact/deal change | Party or opportunity Evidence | Webhook or pull |
| PIM such as Akeneo/Pimcore | product change | Item Evidence | Webhook or pull |

Not every target should become a generic Fact. Facts are suitable for
source-supported observations that do not yet justify a wider typed model. A Shopify
order or PayPal payment normally needs a registered typed interpreter once its
business story is proven. The transport and validation pipeline stays the same:

```text
delivery -> SourceRecord -> ImportJob -> registered interpreter
                                      +-> Fact(s), or
                                      +-> Evidence and typed Reality
```

The capability list must distinguish `declared`, `transport available`, `mapping
available`, and `end-to-end validated`. Listing `PayPal -> payment`, for example,
would not by itself claim that authentication, webhook receipt, or payment posting is
implemented.

## Providers without webhooks

Webhook is one inbound transport, not the integration domain model. A provider that
offers no webhook should use a separate **PullBinding** or file binding attached to the
same SourceCapability. It should reuse:

- SourceSystem and SourceCapability identity;
- credential vault and authorization rules;
- versioned MappingContract or registered interpreter;
- SourceRecord, SourceStream, ImportJob, and Business Events;
- OperationContext, validation results, readiness states, and trace UI.

A PullBinding additionally needs cursor/checkpoint, schedule, pagination, rate-limit,
backfill window, and overlap/reconciliation semantics. Those concerns do not belong in
WebhookBinding. They should be specified as a sibling transport feature rather than
making one universal binding full of nullable webhook and polling fields.

Even providers with webhooks often need reconciliation pulls because webhook delivery
is not guaranteed to be complete forever. Push provides low latency; pull verifies
completeness and repairs gaps. Both paths must converge on the same source identity and
idempotent ingestion service so receiving and later polling the same object does not
duplicate Reality.

## Smallest domain split

Investigate these concepts without committing to their exact tables yet:

### WebhookBinding

Tenant-scoped configuration attached to exactly one SourceCapability:

- opaque binding ID and an unguessable public route token;
- source system and capability references;
- allowed HTTP method and content type;
- authentication verifier reference stored through the existing secret vault;
- explicit event-type routing rules;
- external identity and source-version extraction rules;
- active MappingContract version;
- activation and lifecycle metadata.

The public route must not expose tenant IDs or use a human code as authorization.

### WebhookDelivery

Immutable receipt/audit information for one HTTP attempt:

- tenant and binding identity resolved by the route;
- receipt timestamp, bounded safe headers, body hash, exact byte size, and media type;
- upstream delivery/event ID when supplied;
- authentication and parsing outcome;
- effective enterprise OperationContext when supplied or generated;
- resulting SourceRecord and ImportJob references when accepted;
- safe rejection/quarantine reason.

Large bodies should use immutable artifact storage rather than unbounded database or
log fields. Secrets, authorization headers, cookies, and signatures are never copied
into logs or general payload metadata.

### MappingContract

A versioned, immutable contract approved for one capability. It defines:

- supported upstream event/schema version;
- deterministic paths for `source_type`, `external_id`, and optional
  `source_version_at`;
- an optional stable upstream delivery ID for transport deduplication;
- one or more explicit Fact mappings;
- required values, accepted types, conversions, defaults, and bounded enumerations;
- target subject resolution rules;
- behavior for missing, null, malformed, or unknown fields.

Changing a mapping creates a new version. Existing SourceRecords and Facts retain the
contract version that interpreted them. A new contract does not silently rewrite
historical Facts; replay or correction requires a separate explicit workflow.

## Fact mapping contract

The first slice maps only to the existing generic Fact concept:

```text
Fact(
  subject_type,
  subject_id,
  predicate,
  value,
  observed_at,
  source_record_id
)
```

Every emitted Fact mapping must answer:

1. Which existing tenant-scoped subject does this observation describe?
2. Which stable predicate is being observed?
3. Which JSON value is retained and which deterministic conversion is applied?
4. When was it observed, and what is the fallback if upstream supplies no time?
5. Which immutable SourceRecord proves the observation?

Subject resolution must use an explicit, tenant-scoped lookup contract. It must not
guess by display name or treat a human number as internal identity. If the subject is
missing or ambiguous, interpretation fails safely and creates no Fact.

Unknown webhook fields remain losslessly available in the SourceRecord payload. They
do not automatically become predicates. A predicate becomes configured only for a
proven query, rule, explanation, or later operational use. Mapping directly to
Commitments, Movements, LedgerEntries, or other typed Reality is out of scope for the
first slice and requires its own registered interpreter and business story.

## Validation from the integration list

**Validate webhook** runs the same parser, identity extractor, mapper, subject
resolver, and repository constraints used by live processing, but inside a dry-run
boundary that rolls back all candidate business writes.

Validation has explicit stages:

| Stage | Proves | Example failure |
|---|---|---|
| Route | Binding resolves to the intended tenant capability | Unknown/disabled route |
| Transport | Method, content type, encoding, and size are accepted | Body too large |
| Authentication | Real verifier succeeds with test credentials/signature | Invalid HMAC |
| Envelope | Payload parses losslessly and event type is allowed | Invalid JSON |
| Identity | Stable source type, external ID, and version can be extracted | Missing object ID |
| Idempotency | Delivery and source-version duplicate behavior is deterministic | Conflicting same version |
| Mapping | Required Fact paths, types, and conversions succeed | Invalid decimal/date |
| Subject | Every Fact target resolves exactly once inside the tenant | Unknown or ambiguous item |
| Dry run | Candidate SourceRecord, ImportJob, Facts, and events satisfy normal rules | Repository constraint failure |
| Trace | Operation, SourceRecord, mapping version, and candidate Facts form a complete explanation | Missing source link |

The result should show:

- pass, warning, or failure per stage;
- sanitized extracted identity and schema/event version;
- candidate Facts with subject, predicate, value, and observation time;
- ignored fields and why they remain untyped;
- whether replay would be new, duplicate, stale, or conflicting;
- no secrets and no unbounded payload echo;
- an opaque validation-run ID for support and logs.

A successful validation is evidence about one payload and one MappingContract version,
not proof that every future vendor payload will work. Activation records which test
run and contract version were approved.

## Live delivery behavior

1. Resolve the opaque route to one active tenant-scoped binding.
2. Enforce request size, method, content type, rate limit, and authentication before
   interpretation.
3. Retain the accepted payload losslessly as immutable Source evidence.
4. Derive stable source identity only through the active MappingContract.
5. Use the existing enqueue/ImportJob path rather than a webhook-specific ORM write.
6. A worker loads the exact contract version, resolves subjects, and creates all
   candidate Facts transactionally.
7. Emit normal Business Events with source, mapping, and OperationContext trace.
8. Return quickly after durable acceptance; slow interpretation is asynchronous.

HTTP acceptance and business interpretation are different outcomes. A `2xx` may mean
the delivery was durably accepted, not that Facts already exist. The product and API
must expose the later ImportJob result.

If authentication succeeds but mapping is unknown or invalid, retain the SourceRecord
and mark the ImportJob `unmapped` or `failed` as appropriate. If authentication fails,
do not create trusted Source evidence; retain only bounded security audit metadata
according to policy.

## Delivery identity, source identity, and idempotency

Keep three identities separate:

- **delivery ID** identifies an upstream HTTP delivery attempt and helps detect
  transport retries;
- **source identity** `(source_system, source_type, external_id)` identifies the
  external business object or observation stream;
- **operation identity** connects this receipt to the wider enterprise-agent or
  cross-system execution.

The same delivery may be retried, one source object may produce many immutable
versions, and one enterprise operation may deliver several source objects. None of
these IDs should silently substitute for another.

Canonical payload hashing and source version rules remain authoritative for
SourceRecord idempotency. A repeated delivery must not create duplicate Facts. A
changed payload creates a new source version and new source-supported observations
according to explicit Fact correction/supersession semantics defined by the future
specification.

## Security and operational invariants

- Every binding, delivery, mapping, validation run, SourceRecord, ImportJob, and Fact
  is tenant-scoped; every repository query enforces the scope.
- Support HMAC or another explicit verifier first. Provider-specific signature
  algorithms are adapters, not branches inside domain services.
- Secrets live in the existing encrypted vault and support rotation with an overlap
  window where the provider requires it.
- Compare signatures safely and verify against the exact raw bytes before JSON
  normalization.
- Apply bounded body size, timeout, concurrency, and rate limits before expensive
  parsing or mapping.
- Prevent replay according to provider guarantees without confusing replay protection
  with SourceRecord idempotency.
- Never let payload fields choose tenant, model/table name, arbitrary predicate, ORM
  class, storage key, callback URL, or executable expression.
- Mapping paths and conversions come from an allowlisted contract language, not
  arbitrary Python, templates, SQL, or user-provided code.
- Failed deliveries are observable without leaking payloads or secrets into logs.
- Disabling a source or capability stops new interpretation consistently; the exact
  retain-or-reject behavior must be explicit.
- Webhook actions use the same application services as file intake, API, CLI, chat,
  and MCP. No direct ORM writes occur in the adapter.

## Smallest useful slice

1. Select one existing SourceSystem capability whose intended target is `fact`.
2. Configure one HMAC-authenticated JSON webhook binding and one immutable mapping
   version.
3. Map one known upstream event to one or more Facts about an existing Party or Item.
4. Provide **Validate webhook** from the Integrations capability detail using a real
   signed sample request and a rollback-only dry run.
5. Activate the exact validated mapping version through a confirmed application
   command.
6. Accept a live delivery into SourceRecord plus ImportJob and process it
   asynchronously through shared services.
7. Show delivery, immutable payload, mapping version, generated Facts, Business Events,
   and OperationContext as one trace.
8. Prove duplicate delivery safety, changed-payload versioning, invalid signatures,
   missing subjects, mapping failure, retry, and cross-tenant isolation.

Out of scope for the first slice: arbitrary visual transformation programming,
outbound webhooks, polling connectors, vendor-wide connector frameworks, mapping
directly into every domain table, synchronous Fact creation inside the HTTP request,
and claiming that one successful sample validates all possible upstream payloads.

## Questions to resolve before specification

1. Which concrete source system, event type, and Fact predicate prove the first slice?
2. Does the upstream provider supply a stable delivery ID and source version/time?
3. Is HMAC sufficient for the first provider, and what exact canonical signing input
   does it require?
4. Should authenticated but unmappable deliveries always become SourceRecords, or are
   there payload classes that policy requires quarantining before evidence storage?
5. What are the Fact supersession/correction semantics when the same external object
   sends a changed observation?
6. Which subject identity can be resolved deterministically without using a human
   display name as identity?
7. Must validation support a captured real delivery, a manually pasted payload, a
   provider challenge request, or all three?
8. What retention and redaction rules apply to WebhookDelivery metadata and validation
   samples?
9. Which readiness failures should mark the integration `degraded`, and which merely
   create one failed delivery?

## Promotion trigger

Move this idea into a numbered Spec Kit feature after choosing one real provider
event, its authentication contract, its stable source identity, the first useful Fact
predicate, and deterministic subject resolution. The specification should define the
operator setup, validation, activation, live receipt, failure, and trace stories. The
plan should reuse SourceRecord, ImportJob, Business Events, OperationContext, secret
vault, and shared application services before proposing new infrastructure.
