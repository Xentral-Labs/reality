# Interpretation Coverage

## Idea

Every accepted `SourceRecord` should end in an explicit, explainable interpretation
outcome. A successful import must name the Reality records it produced; a source that
cannot safely produce Reality must say why it is unsupported, needs review, is stale,
conflicts, or failed. Silence is not an outcome.

This closes the gap between lossless intake and agent operation. An agent can then ask
which sources are understood, which require a person, and which exact records came
from a specific interpretation attempt without inferring that from mutable job state.

## Smallest proof

The first slice covers the existing Shopify order interpreter and generic unmapped and
failed imports. It adds one append-only outcome per completed processing attempt, a
tenant-scoped coverage read available through the shared application-tool boundary,
and tests for success, retry, unsupported input, and tenant isolation.

The outcome is operational audit metadata, not a new business fact. Documents,
Commitments, and other Reality records remain authoritative for business state.

## Later

- richer field-level observations and review resolution;
- coverage metrics by connector and interpreter version;
- Atlas/Operator attention routing;
- learned mappings proposed from repeated unresolved observations.

