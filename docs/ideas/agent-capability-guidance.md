# Idea: Governed agent use of Business Reality capabilities

**Status:** Proposed direction — not approved and not an implementation specification

## Problem

Reality already exposes shared application commands to people, Chat, and MCP agents.
Those boundaries prevent direct persistence and require confirmation for mutations,
but a schema alone does not tell an agent which business command is appropriate,
which apparently similar command is wrong, or how to prove the resulting business
state.

Without a common semantic contract, every agent must recreate this knowledge in its
prompt. Different agents can then interpret the same source differently, manufacture
Facts that mirror typed Reality, confuse a promise with a physical event, or trust a
successful command response without checking the resulting state.

The intended operating model is:

```text
immutable SourceRecord
        |
        v
interpretation outcome or explicit human intent
        |
        v
discover records -> describe capability -> propose command
        |
        v
confirmation or adopted policy -> shared application service
        |
        v
Fact / Commitment / Reservation / Movement / LedgerEntry
        |
        v
Business Event -> re-read declared projection -> verified outcome
```

Reality remains deliberately low-level. It owns valid storage transitions and their
traceability. Domain packs explain how a bounded business domain translates source
evidence into those transitions. Agents observe, reason, ask, and propose; model output
is neither business truth nor authority.

## Responsibility model

### Reality core

The core owns invariants that must be true regardless of agent or domain:

- tenant scope and opaque identity;
- lossless SourceRecord storage;
- valid typed relationships and values;
- registered commands and Fact predicates;
- idempotency where a command supports retry;
- confirmation and authorization boundaries;
- durable Business Events;
- projections that independently expose resulting Reality.

The core does not infer organization-specific procedures from conversations and does
not choose a business command on behalf of an agent.

### Capability contract

Every agent-eligible command needs one machine-readable description that answers:

- What business outcome does this command create?
- When should it be used?
- When must it not be used?
- Which records and opaque IDs must already exist?
- Which preconditions and authorization boundaries apply?
- Is a stable idempotency identity required?
- Which refusals can the caller handle?
- Which Business Events may follow?
- Which projections must be re-read to verify the outcome?
- What are one valid and one invalid usage example?

Chat, MCP, CLI, and future agents consume the same contract. Prompts may summarize the
contract but do not become its authoritative copy.

### Domain pack

A domain pack combines bounded interpretation guidance without moving business truth
into the agent runtime. A Commerce pack may select relevant Reality capabilities,
register domain-specific Fact predicates, define source interpretation rules, provide
examples, and declare verification and escalation guidance.

The pack is versioned. Interpretation records retain the pack and interpreter version
that produced their result. Learning may propose a new pack version, predicate, or
rule, but activation remains an explicit reviewed action.

### Agent

An agent follows a common loop:

1. discover relevant tenant-scoped records and opaque IDs;
2. inspect the candidate capability contract;
3. select a capability and explain why alternatives do not apply;
4. propose a typed command using the shared schema;
5. wait for confirmation or an explicit policy decision;
6. execute only through the shared application tool;
7. re-read the declared projection;
8. classify the outcome as verified, refused, unknown, or reconciliation-required.

## Fact decision rule

A Fact is a source-supported observation that does not replace an existing typed
business transition. `observe_fact` is the only core service that appends one. Agents
and interpreters call `fact_observe_propose`; they never write the Fact table directly.

| Input meaning | Correct Reality operation |
|---|---|
| A customer promises or requests a quantity by a date | Commitment command |
| Stock is allocated to that promise | Reservation command |
| Goods physically moved | Movement command |
| Money financially moved | Ledger or payment command |
| A source states an approved contextual predicate such as shipping priority | Fact proposal |
| An unknown upstream field has no proven operational use | Preserve only in SourceRecord |

If core logic repeatedly calculates, filters, joins, constrains, predicts, or acts on a
Fact predicate, that usage is evidence for a later typed-model proposal. It is not a
reason for an agent to expand schema or activate a predicate itself.

## Capability description example

```yaml
name: reserve
purpose: Allocate available stock to an existing commitment.
use_when:
  - An existing outgoing commitment needs a bounded stock allocation.
do_not_use_when:
  - Goods have already physically moved.
  - The source expresses only a customer preference.
required_context:
  - commitment
  - item
  - location
preconditions:
  - The commitment, item, and location belong to the selected tenant.
confirmation: required
idempotency: caller-stable identity before unattended retry
refusals:
  - insufficient_stock
  - commitment_closed
verification:
  projections:
    - inventory
    - commitment_register
```

This description is guidance, not a second implementation of domain rules. The
application service still enforces every invariant at execution time.

## Interpretation coverage

Durable intake guarantees that an input is not lost, but a completed job should also
state what interpretation concluded. Each accepted SourceRecord should eventually be
classifiable as:

- interpreted into named Evidence or Reality records;
- intentionally irrelevant to registered Reality;
- awaiting human review;
- unsupported by current capabilities or predicates;
- failed with an explainable retry or recovery path.

The outcome should reference produced records through typed opaque identities and list
unresolved observations without copying the source payload. Operators need a derived
queue for unprocessed, failed, unsupported, contradictory, or review-required inputs.
This is how Reality proves processing coverage without pretending an agent understood
everything.

## Learning and activation

Learning remains above the core:

```text
observations + corrections + repeated human decisions
        |
        v
learning candidate with provenance
        |
        v
review, simulation, and shadow comparison
        |
        v
new versioned domain rule or capability guidance
        |
        v
explicit activation with bounded scope
```

A conversation, model completion, repeated pattern, or successful prior action never
activates a policy or Fact predicate by itself.

## Proposed delivery sequence

### Slice 1 — Describe and verify core capabilities

- enrich the canonical command catalog with use, non-use, precondition, refusal,
  idempotency, event, and verification guidance;
- expose one read-only capability-description path to Chat and MCP;
- prove complete guidance for `observe_fact`, `create_manual_order`, `reserve`, and
  `record_movement`;
- extend conformance checks so every agent-exposed mutation remains confirmation-bound
  and all declared projections and examples resolve.

### Slice 2 — Interpretation coverage

- retain one explicit interpretation outcome per source processing attempt;
- reference produced records and unresolved observations;
- expose review, unsupported, and failed queues;
- measure accepted sources that do not yet have a terminal interpretation outcome.

### Slice 3 — First Commerce domain pack

- package Shopify order interpretation, selected Commerce Facts, relevant commands,
  examples, and verification rules;
- persist pack and interpreter versions with interpretation outcomes;
- emit proposals for uncertain observations rather than direct writes.

### Slice 4 — Closed governed agent loop

- run discover, describe, propose, authorize, execute, re-read, and verify as one
  explainable operation;
- preserve unknown outcomes and reconciliation needs instead of assuming success;
- evaluate planted command-selection defects and source omissions.

## Non-goals

- No generic workflow engine before a second proven domain requires it.
- No autonomous policy adoption from model output or observed repetition.
- No direct ORM or database access for agents.
- No Fact mirrors of Commitments, Reservations, Movements, or Ledger entries.
- No universal mapping language that attempts to replace registered interpreters.
- No claim that capability guidance can replace service-side validation.

## Open design questions for later slices

1. Whether interpretation outcomes need a dedicated durable record or can initially be
   an immutable extension of ImportJob results.
2. Whether domain packs remain versioned configuration or later require a separately
   installable package boundary.
3. Which narrow deterministic interpretation rules may execute under an adopted
   policy without per-record human confirmation.
4. How provider reconciliation proves that push- and pull-observed inputs are complete.

