# Frozen read contract v1

Tool: shopify_source_intake_preflight (read). Input and response are exact strict
snake_case JSON schemas in this directory. Tenant derives from transport, never
from caller input. At most100 lines; report serialization at most24000 UTF-8 bytes
(initial conservative bound). Larger reports refuse unavailable, never silently
truncate semantic fields. Semantic output_digest is SHA256 of canonical sorted
JSON excluding observed_at and output_digest. No received monetary values are
recomputed. Null source_unit is an interpretation/selection unknown, not an
upstream absence claim. No ready boolean exists. Unavailable/stale requested
basis is a refusal, not a successful report with stale data.
