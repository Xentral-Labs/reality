# Research

- Exceptions profile: each of three commitment derivators repeats approximately 2,082 queries; return/billing classes also repeat movement and evidence reads. Decision: batch retained input facts once per evaluation and retain canonical rules. Reject persistent memoization because it would make freshness and invalidation new behavior.
- Finance profile: open-items entry triggers _build_operational_rows for all 13 projection families, causing about 20,000 queries after a new event. Decision: rebuild only the requested financial projection using the existing builder, version and event checkpoint. Keep explicit full refresh compatible. Reject background refresh or TTL because neither is needed to remove unrelated work.
- No external research or new technology is needed; repository code and local measurements establish the cause.
