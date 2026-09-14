# Research Decisions

- Decision: Use a new feature 145 on current main. Reason: 144 is already claimed by integrations; preserve unrelated detached-checkout work and the broader Atlas draft.
- Decision: Public MCP pages by default, explicit legacy escape hatch, internal list default. Reason: avoid silent truncation for agents while retaining Playground list consumers. Alternative: all callers changed to envelopes would force unrelated frontend changes. Research agent identified the exact consumers in playground.py and application/tenant tests.
- Decision: Live keyset cursor bound to tenant/tool/filter. Reason: no new state or snapshot promise. Alternative: persistent snapshots add unapproved infrastructure; full content hashing for every discovery page adds unnecessary scans.
- Decision: Reuse existing builder for direct operational diagnostics and delivery_case/document_detail for retained explanation. Reason: no competing business rules. Alternative: cached paging writes during a diagnostic and does not guarantee coherence across requests.
- Decision: Source freshness unknown; observed event sequence is local context only. Reason: not every upstream change is known to Reality.

All design questions resolved within accepted scope. No new technology choice requires external research.
