# Idea: Deterministic external-system simulator

**Status:** Brainstorming — not approved, not an implementation specification

## Problem

Reality needs repeatable end-to-end tests for orders, payments, refunds, fulfillment,
master data, webhook delivery, polling, retries, and failure handling. Building test
shortcuts that insert rows directly would prove a different system from production and
would bypass Source → Evidence → Reality, authentication, mapping, jobs, events,
projections, and operation traceability.

Create a small external-system simulator that behaves like selected providers at the
integration boundary. It generates realistic provider-shaped objects and sends or
serves them through exactly the same transports used by real integrations.

```text
scenario manifest
       |
       v
external-system simulator
       +-- sends signed webhook ------+
       +-- exposes pull API ----------+--> normal connector/ingestion path
       +-- emits import file ---------+
                                       |
                                       v
                      SourceRecord -> ImportJob -> interpreter
                                       |
                                       v
                         Facts / Evidence / Reality
```

The simulator is outside the Reality domain boundary. It must not call Reality
repositories, ORM models, internal interpreter functions, or projection builders.

## Two complementary layers

### Provider simulator

Imitates the observable edge of one external system:

- provider-shaped order, customer, product, payment, refund, payout, dispute, and
  fulfillment payloads;
- webhook signatures and delivery IDs;
- pull endpoints with pagination, cursors, updated-since filters, and rate limits;
- provider object IDs, versions, timestamps, and lifecycle transitions;
- configurable retry, duplicate, reordering, delay, timeout, and malformed responses.

Start with a deliberately small subset of a provider contract. Do not claim complete
Shopify, Stripe, or PayPal compatibility.

### Scenario runner

Orchestrates deterministic business stories across one or more provider simulators:

```text
customer created
  -> Shopify order created
  -> payment authorized/captured
  -> fulfillment created
  -> optional refund or dispute
```

The runner controls seed and virtual time, invokes only public integration paths, waits
for asynchronous processing, and then queries public Reality read services to compare
observable outcomes.

## Reuse instead of parallel test behavior

The simulator should reuse contracts and fixtures, but not production domain code:

- Connector catalog selects which provider/capability profiles exist.
- MappingContract and interpreter contracts define what Reality accepts.
- The simulator owns representative upstream payload builders and transport behavior.
- Contract fixtures can be consumed by unit tests, validation dry runs, simulator
  scenarios, and documentation examples.
- Reality receives every simulated delivery through WebhookBinding, PullBinding, file
  intake, or another public adapter exactly as production would.
- Assertions use public queries and trace services, never direct database mutation.

Sharing literal parsing or domain-conversion functions between simulator and Reality
would hide incompatibilities. Share schemas and golden examples where appropriate;
keep independently implemented producer and consumer behavior.

## Initial scenario catalog

| Scenario | Simulated source activity | Reality path to prove |
|---|---|---|
| Paid Shopify order | Customer, product, order, payment capture | Source -> Document/Lines -> Commitment plus payment Evidence |
| Order before payment | Order first, delayed capture | Independent arrival and later correlation |
| Partial fulfillment | One order, multiple fulfillment events | Movements and remaining Commitment state |
| Refund | Capture followed by partial/full refund | Immutable correction and financial trace |
| Duplicate webhook | Same delivery sent repeatedly | No duplicate Source version or Facts/Reality |
| Changed order | Same external object with a newer version | SourceStream versioning and controlled reinterpretation |
| Out-of-order delivery | Newer event arrives before older event | Stale/conflict handling |
| Missing mapping | Unknown SKU, Party, or predicate | Safe failed/unmapped job, no invented identity |
| Invalid signature | Correct payload with bad authentication | Rejection without trusted Source evidence |
| Webhook gap repaired by pull | Event omitted from push, later returned by API | Same identity and idempotent reconciliation |
| Payment dispute | Capture then dispute event | Traceable exception without premature accounting assumptions |
| Cross-system operation | Enterprise agent initiates order/payment flow | Shared OperationContext across known participants |

PayPal should be added to the connector catalog only when its first concrete capability
and contract are selected. Until then, a generic payment-provider simulator can prove
the payment lifecycle without falsely claiming PayPal compatibility.

## Scenario manifest

A versioned, reviewable manifest describes intent rather than implementation details:

- scenario name, seed, virtual start time, and tenant test identity;
- provider instances and enabled capabilities;
- ordered actions and controlled time advances;
- transport choice per action: webhook, pull-visible object, or file;
- deliberate fault injections;
- expected public business outcomes and trace relationships;
- completion timeout and asynchronous checkpoints.

Generated IDs and timestamps must be deterministic for the same seed. Secrets used by
the simulator are test-only and provisioned through the same binding setup APIs, not
hard-coded into production configuration.

## Control plane versus data plane

Keep simulator control separate from simulated provider traffic:

- **Control plane:** reset isolated simulator state, choose scenario, advance virtual
  time, inject faults, and inspect what the simulated provider sent.
- **Data plane:** signed webhooks, pull API responses, and files that look like normal
  provider traffic to Reality.

Reality must never accept a control-plane command as a shortcut to create business
state. A scenario can ask the simulator to create an order; only the resulting public
delivery may affect Reality.

## Validation uses

The simulator should support three levels without creating three implementations:

1. **Contract validation:** send one representative payload through the Integrations
   page's dry-run Validate action.
2. **Transport validation:** prove signature, endpoint, retry, pull cursor, and
   reconciliation behavior against a running Reality instance.
3. **Business-story validation:** run a complete order/payment/fulfillment scenario and
   inspect Source, Evidence, Reality, Business Events, projections, and operation trace.

The scenario report should link each external object and delivery to the returned
operation reference, SourceRecord, ImportJob, interpreted records, and final public
outcomes. It should clearly distinguish simulator assertions from facts observed in
Reality.

## Safety and environment boundaries

- Simulator endpoints and controls are disabled by default and cannot be enabled in a
  production deployment accidentally.
- Use explicit test tenant allowlists and visibly synthetic provider identities.
- Reset only simulator-owned state and dedicated test tenants; never provide a broad
  database reset operation.
- Never reuse production credentials, webhook secrets, callback URLs, or customer
  payloads.
- Apply realistic request limits so tests also exercise bounded ingestion.
- Fault injection is explicit in the scenario report and cannot leak into normal
  connector operation.
- Generated data is marked synthetic at the source/integration boundary without adding
  fake semantics to every domain table.

## Smallest useful slice

1. Implement one minimal Shopify-shaped simulator profile for customer, product, and
   order objects.
2. Implement one generic payment-provider profile for authorization/capture, leaving
   PayPal branding until its real contract is selected.
3. Send signed webhooks through the planned WebhookBinding and expose one reconciliation
   pull endpoint.
4. Run a deterministic paid-order scenario with one shared OperationContext.
5. Exercise the real SourceRecord, ImportJob, registered interpreter, Business Event,
   and projection paths.
6. Assert outcomes only through public application/read services.
7. Add duplicate, invalid-signature, unknown-SKU, and webhook-gap fault variants.
8. Produce one trace report comparing emitted external actions with observed Reality
   participation.

Out of scope for the first slice: a universal mock server, complete vendor API
emulation, performance/load testing, a visual scenario editor, production demo data,
direct database seeding, and implementing every connector in the catalog.

## Questions to resolve before specification

1. Which exact Shopify event/schema version is the first supported contract?
2. Should the first payment profile target Stripe, Shopify Payments, PayPal, or remain
   intentionally generic until one real provider is selected?
3. Does the simulator run as a separate local process/container or as a test-only
   package with an HTTP boundary?
4. Which public query defines completion for asynchronous scenarios?
5. Which fixtures may be shared with MappingContract validation without coupling the
   simulator producer to the Reality consumer?
6. How is virtual time propagated when Reality itself uses UTC wall-clock behavior?
7. Which minimum pull/reconciliation behavior is needed in the first slice?

## Promotion trigger

Move this idea into a numbered Spec Kit feature after selecting one exact order
contract, one payment contract, the first webhook authentication method, and the public
outcomes of the paid-order story. The plan must keep the simulator outside the domain
and route all generated activity through production-equivalent application boundaries.
