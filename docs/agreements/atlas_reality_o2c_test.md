# Atlas + Reality: First Order-to-Cash Integration Test

**Status:** Working agreement for the first joint test
**Scope:** One real (anonymised) Shopify or B2B order, first read-only and then through one governed Reality command
**Spec impact:** None. This document records a test agreement; it does not change product behaviour.

## Purpose

The first joint implementation must prove the boundary between Atlas and Reality with one real
order-to-cash slice. It runs in two phases: first a live read-only explanation through Reality's
existing authenticated MCP boundary, then one supervised governed reservation through the current
Reality proposal flow. Missing production guarantees are recorded by the test rather than blocking
it. It must not attempt to prove a general workflow platform or full O2C autonomy.

The test proves that:

1. Reality owns operational truth, operational context, and domain invariants.
2. Atlas owns organizational context, work, learning, authority, governed execution, and verification.
3. The integration uses projections and commands, never shared database tables.
4. A successful provider response is not considered verified until Atlas reads the changed Reality projection again.

## Recommended slice

Use one order for four units of one item, with ten units physically available. Phase 1 reads it
through Reality's existing `order_explain` and fulfilment tools. In Phase 2, Atlas's
provider-independent `ReserveInventory` capability maps to Reality's operation. Reality currently
exposes `reservation_propose` and `proposal_approve_and_execute` over MCP, backed by the internal
`reserve` operation. The prototype may use that sequence under mandatory human supervision; it
must make the duplicated confirmation visible rather than pretending it is the final authority
boundary. None of those provider names belongs in the Atlas capability.

```text
Order quantity:       4
Physical stock:      10
Existing reservation: 0
Expected reservation: 4
Expected shortage:    0
```

## Reality prerequisites (Bene)

For the read-only phase, Reality must provide a reachable test tenant and:

- an immutable, lossless Shopify/B2B `SourceRecord`;
- the resulting Party, Item, Location, Document/Line (if used), and open customer-delivery Commitment;
- its authenticated HTTP MCP endpoint with a revocable token restricted to the required read tools;
- the existing `order_explain`, `fulfillment_queue`, and `fulfillment_blockers` reads as needed by
  the agreed Atlas projection;
- authentication and tenant enforcement;
- a stable order identity through which Atlas can repeat the read.

The projection must include opaque IDs, the snapshot or revision used, source provenance, ordered
quantity, reserved quantity, available quantity, blocking reasons, and explicit omissions or
contradictions. Human-readable order numbers are display values only.

For the supervised prototype, Reality and Atlas document the selected operation's current input,
output, preconditions, refusal behavior, and returned identifiers. Caller-supplied idempotency,
cross-system correlation, stale-revision handling, durable receipts, and explicit unknown-outcome
semantics are hardening gaps to measure. They become requirements before automatic retry,
policy-backed execution, or unattended operation—not before the first controlled integration.

## Atlas prerequisites (Tobias)

For the read-only phase, Atlas must provide a test tenant mapped to the Reality tenant and:

- a Commerce Operator and a Matter for the order;
- a Reality projection adapter that retains an attributable observation, its digest or version,
  and the evidence needed by Atlas without copying Reality's complete operational document into
  the Atlas Kernel;
- a provider-independent order situation and explanation view that work without model scratchpads
  or hidden reasoning.

Before the mutating phase, Atlas must additionally provide:

- a Recommendation containing exactly one provider-independent capability and its arguments;
- an Authority Evaluation and an explicit human Decision (or a narrowly scoped test Policy);
- an Effect Attempt carrying the full correlation and idempotency context;
- a post-command Verification based on a fresh Reality read.

Atlas must retain this identity chain:

```text
matter_id -> atlas_command_id -> authority_evaluation_id
-> authority_basis(decision_id | policy_id)
-> effect_attempt_id -> reality_command_id/receipt_id -> projection_version
-> verification_id
```

Atlas must not write Reality tables, reimplement Reality inventory rules, or treat credentials as authority.

## Shared integration contract

The integration keeps four contexts distinct. Fields are required where their context exists; they
are not duplicated on every read and event.

```yaml
authenticated_transport:
  reality_tenant_id: bound by the Reality credential
  allowed_operations: bound by the Reality credential
  api_or_protocol_version: required

atlas_organizational_record:
  organization_id: required
  actor_id: required
  atlas_command_id: required for a governed action
  authority_evaluation_id: required for a governed action
  decision_id_or_policy_id: required for an allowed governed action
  correlation_id: required

mutation_request:
  atlas_command_id: required when Atlas initiates the action
  correlation_id: required
  idempotency_key: target before retry or unattended operation
  expected_projection_revision: target before snapshot-sensitive unattended operation

reality_receipt:
  reality_operation_id_or_receipt_id: use the strongest identifier currently returned
  affected_reality_ids: retain every identifier currently returned
  resulting_projection_revision: target before unattended verification
```

Source evidence identifiers and causation identifiers are carried where the relevant Reality
record or event has them; their absence from an unrelated read is not filled with an invented ID.

The projection contract must define its name, version, tenant, subject IDs, `as_of` or snapshot
revision, provenance, omissions or contradictions, and change or ETag semantics.

## Test procedure

### Phase 1 — live read-only integration

#### 1. Capture and interpret

Reality stores the original payload unchanged and derives the minimum Evidence and Reality needed for the order. No Reservation exists yet.

**Pass:** the payload is recoverable byte-for-byte; the Commitment is traceable to its evidence and source; unknown upstream fields remain available.

#### 2. Observe and understand

Atlas reads the Reality projection and explains the order, provenance, uncertainty, and next required action. Any missing organisational rule is recorded as a claim or question, not as a Policy.

**Pass:** Atlas can explain why reservation is proposed using the selected projection snapshot.

### Phase 2 — governed reservation

Phase 2 is a supervised prototype. It requires a person to approve the exact action and permits one
dispatch attempt. It does not wait for every production guarantee, but it must not silently replace
a missing guarantee with an Atlas claim.

#### 3. Govern the action

Atlas proposes exactly one `ReserveInventory` command. Authority is evaluated before any effect. A
person confirms the exact Commitment, quantity, and capability, or an applicable Atlas policy is
the recorded authority basis. The Reality adapter maps that consequence to the agreed provider
operation without leaking the provider name into the Atlas command.

**Pass:** no Reality mutation occurs without the Decision/Policy required by the test.

#### 4. Execute once

Atlas sends one authenticated command once. Reality applies its own invariants and returns its
current proposal output and affected identifiers. Atlas records those identifiers against the
Effect Attempt without calling them a durable receipt if Reality does not provide one.

**Pass:** exactly one Reservation is created for the Commitment and Atlas retains the strongest
Reality identifiers returned by the operation.

#### 5. Test retry only when safe

If the current Reality boundary accepts a caller-provided idempotency key, Atlas repeats the
identical request and proves replay behavior. Otherwise, do not manufacture this test by issuing a
second effect that may duplicate the reservation. Record idempotency as an observed hardening gap.

**Prototype pass:** Atlas never retries an ambiguous effect automatically. **Hardening pass:** no
second Reservation is created, the original outcome is returned, and reusing the key with different
semantic arguments is rejected as an idempotency conflict.

#### 6. Re-read and verify

Atlas reads the affected Reality projection again and compares it with the receipt.

**Pass:** the new projection proves the expected Reality (`reserved_quantity = 4`, no shortage, and the corresponding readiness change). Only then may Atlas mark the outcome `verified`.

## Required negative tests

The joint run must also show:

1. **No approval:** Atlas cannot dispatch the mutating command.
2. **Stale projection:** Atlas requires a fresh read and a person while Reality has no
   snapshot-sensitive precondition; once supported, Reality refuses a stale expected revision.
3. **Insufficient stock:** the agreed partial-reservation or atomic-refusal semantics are observed and explained.
4. **Wrong tenant:** cross-tenant reads and writes behave as not found or are refused without data disclosure.
5. **Unknown outcome:** a timeout after dispatch becomes an unresolved Matter for a person. Atlas
   does not retry or mark success until idempotency or operation identity can reconcile it.

## Evidence of completion

Phase 1 is green when both teams can present this read-only chain:

```text
Reality SourceRecord
 -> Evidence / DocumentLine
 -> Commitment
 -> Reality Projection
 -> Atlas Matter
 -> Atlas provider-independent order situation
 -> Atlas explanation with provenance, freshness, and bounds
```

Phase 2 is green only when both teams can extend it with this complete governed-effect chain:

```text
Atlas Command
 -> Authority Evaluation
 -> Decision or Policy basis
 -> Effect Attempt
 -> Reality Receipt
 -> Reservation
 -> New Reality Projection
 -> Atlas Verification
```

The result must be explainable from persisted records and projections alone. Model output may propose an action, but it is not evidence, authority, or business truth.

## Known implementation checkpoint

Reality's current authenticated MCP boundary, tenant-bound tool tokens, and read tools are enough to
start Phase 1 once Atlas has a reachable test tenant, restricted token, and stable order. This phase
should be attempted before requesting a new Reality transport or Atlas-shaped response.

Phase 2 may use Reality's current proposal and confirmation flow for one controlled action. While
caller-provided idempotency, Atlas operation correlation, stale-revision handling, a durable
receipt, explicit unknown-outcome semantics, or a projection version are missing, Atlas requires a
person, dispatches once, never retries an ambiguous result, re-reads Reality after a successful
response, and reports the limitations explicitly.

Those gaps must close before automatic retry, policy-backed execution, or unattended operation.
The prototype exists to expose and prioritize them; it must not wait for a production-complete
contract before testing the real boundary.
