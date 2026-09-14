# Research: Auditable Ledger Reversals

## Decision 1: Reverse the complete posting group

**Decision**: The existing opaque posting-group identity is the reversal unit.

**Rationale**: Balance is guaranteed only for the complete group; partial reversal would
introduce a second posting editor and ambiguous balance behavior.

**Alternatives considered**: Entry-level reversal was rejected as unsafe; arbitrary
replacement in one transaction was rejected because normal posting already handles the
intended corrected transaction.

## Decision 2: Add one explicit reversal relation

**Decision**: Persist one tenant-scoped relation between original and inverse group with
reason, time, actor context, and fingerprint.

**Rationale**: Uniqueness, retry, allocation filtering, role display, event explanation,
and audit all repeatedly act on this meaning; inference from matching amounts is unsafe.

**Alternatives considered**: Entry flags would mutate/duplicate state. A new PostingGroup
parent with full historical backfill adds broad schema churn without new behavior.

## Decision 3: Do not copy original Evidence

**Decision**: LedgerReversal is direct durable correction Evidence. Inverse entries reach
original Document/SourceRecord business Evidence through the relation and original group.

**Rationale**: The original Evidence supports the original claim, not the later human
correction decision. The reason/actor/time relation is direct reversal evidence.

**Alternatives considered**: Copying provenance was rejected as a false direct claim.
Creating a correction Document was rejected because LedgerReversal already captures the
proven correction decision used by retry, audit, role, and derivation logic.

## Decision 4: Preserve allocation rows but derive inactivity

**Decision**: An allocation is active only if neither linked group's original role is
reversed.

**Rationale**: This retains the historical matching decision while releasing the
unaffected invoice/payment side and preventing contradictory settlement.

**Alternatives considered**: Deleting allocations violates append-only history. Negative
allocation rows require a new allocation-correction model. Blocking settled reversals
would not close the general reversal gap.

## Decision 5: Disallow reversal of reversal

**Decision**: Each group can participate in only one role; inverse groups cannot reverse.

**Rationale**: A single two-group chain is deterministic and explainable. A mistaken
business event can be posted correctly through normal posting after reversal.

**Alternatives considered**: Arbitrary reversal chains require parity-based activation,
allocation reactivation, and much more complex concurrency semantics.

## Decision 6: Fingerprint semantic intent, not actor metadata

**Decision**: Fingerprint tenant, original group, and normalized reason; exclude actor.

**Rationale**: Retrying the same approved intent across Web/CLI/tool must replay safely,
while the actor context from the accepted first execution remains immutable audit data.

**Alternatives considered**: Including actor context creates duplicate-intent conflicts.
Reason-free keys would incorrectly merge different correction decisions.

## Decision 7: One transactional event boundary

**Decision**: Exact inverses, relation, and `ledger.reversed` event commit together.

**Rationale**: Append-only correctness cannot tolerate entries without correction meaning
or consumers missing invalidation.

**Alternatives considered**: Calling the currently committing public posting function
would permit partial state; post-commit event publication would break atomic audit.

## Decision 8: Server-derived preview and existing confirmation policy

**Decision**: Preview uses the same normalization/derivation as execute; execute locks and
revalidates revision/fingerprint. Web/CLI confirm; Chat/MCP propose for approval.

**Rationale**: Financial effects and affected allocations must not be calculated by an
adapter, and stale previews must fail safely.

**Alternatives considered**: Client-side preview risks semantic drift. Direct agent
mutation violates the Constitution and existing tool contract.
