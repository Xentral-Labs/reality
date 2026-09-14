# Glossary

## SourceRecord

Immutable, lossless accepted input from an upstream source. Changed input creates a version or
event.

## Document and DocumentLine

Structured business evidence derived from source input. They do not own operational or financial
state.

## Fact

An immutable observation explicitly supported by a same-tenant SourceRecord and attached to an
existing opaque Reality subject through a reviewed predicate. It is not a model guess or a copy of
typed operational state. See
[Facts: source-supported observations](/concepts/business-reality-guide/06-facts-and-open-questions#facts).

## Commitment

An obligation to deliver, receive, pay, or collect.

## Reservation

An allocation of stock or capacity directly to a Commitment.

## Movement

A quantity moving between locations or inventory positions. Corrections preserve the original
movement and create an explicit audit trail.

## LedgerEntry

A debit or credit posting in balanced financial reality. Reversals are explicit rather than edits.

## Evidence

The structured support connecting an operational or financial conclusion to accepted source input.

## Reality

The tenant-scoped operational and financial records that own the current position and support
action.

## Shortest true links

Relationships connect directly to the record that owns their meaning and avoid duplicate foreign
keys to indirect evidence or source records.

## Tenant

The isolation boundary for every business table, repository query, and application request.

## Opaque ID

A system identity with no business meaning. Human numbers remain searchable but are never identity.
