# Connector Contract

## Responsibilities

A connector authenticates to its upstream source, selects authorized records, captures them
losslessly, and submits them with tenant and source identity through Reality's application boundary.
It does not write domain tables, infer operational status in transport code, or bypass confirmation.

## Lossless payloads

Store the original record and relevant envelope metadata. Do not drop unknown fields. Binary source
files belong in private object storage and are referenced by opaque keys; business identity and
metadata remain in PostgreSQL.

## Idempotency and versioning

Repeated delivery of the same upstream version must not manufacture duplicate business events. A
changed upstream record creates a new SourceRecord version or event so history remains explainable.
Human document numbers are not idempotency keys unless an explicit source contract proves their
scope and version behavior.

## Typing criteria

Promote a source field into the typed model only when core logic repeatedly:

- calculates with it;
- filters or joins on it;
- constrains or validates it;
- predicts from it; or
- acts on it.

## Error model

Classify connection/authentication errors, invalid envelopes, unsupported interpretation, and
downstream service failures separately. Preserve accepted source input, expose a safe operator
message, log diagnostic context without secrets, and make retry behavior explicit.

## Traceability outcome

Where applicable, a reader can traverse SourceRecord → Document/DocumentLine → Fact, Commitment,
Reservation, Movement, or LedgerEntry. When a stage does not apply, the connector does not invent
it.

> **Normative invariant:** Connectors call shared services/tools. They never perform direct ORM
> writes or implement a second set of business rules.
