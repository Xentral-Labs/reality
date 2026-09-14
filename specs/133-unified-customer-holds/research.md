# Research
Read-only delegated audit plus local inspection completed before implementation.
- Decision: reuse existing customer shipment gating. Rationale: PartyHold blocks linked customer shipment only; new and existing reservations remain allowed, incoming receipts unaffected. Alternative rejected: redefine a party hold as an inventory freeze.
- Decision: snapshot customer identity and full active hold set, no affected count. Rationale: future shipments are also covered; a current count is not complete scope and needlessly broadens stale-state checks.
- Decision: optional core action ID plus exact event payload for proof; no schema. Existing events lacked proposal attribution. State alone cannot prove which command executed; repeated raw place returns an existing hold and release may return empty, so reviewed no-ops reject.
- Decision: customer role checked through existing reference_detail, preserving multiple-party-role semantics. Raw CLI/MCP party tools stay broader and compatible.
- Decision: block unresolved same-party hold work and linked shipment/correction work; leave reservation permission intact. Existing delivery review includes party hold blockers and revalidates stale shipments.
- Decision: shared card and existing prepare/review/confirm/detail/reconcile routes; one dedicated read-only context endpoint. All unknowns resolved. No extension hooks registered.
