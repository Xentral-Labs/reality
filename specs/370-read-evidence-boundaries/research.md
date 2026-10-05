# Research

Decision: reuse metadata.decision_coverage in the summary; its detached location allows the generic count to be overstated. Qualify the first sentence and preserve pagination semantics.

Decision: expose a transient order inventory interpretation limit rather than adding inventory history queries or causal calculations. order_explain includes current stock and commitment-linked movements only.

Existing evidence readers: movement_explanation takes exact movement_id and reads authoritative source/commitment/correction/reason links. inventory_read filters item/location but is current stock. Movement discovery has no item/document filter; query matches type. Reading exact provenance does not prove complete stock history.

Alternatives rejected: new report/tool, persistent derived history status, provider-specific output rewriting and automatically reading every item movement. None is necessary to correct the ambiguous contract.
