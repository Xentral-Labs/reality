# Creation Contract
POST /api/playground/runs adds sandbox_kind (temporary default or practice)
and company_name (required, trimmed 1–120 for practice; omitted for temporary).
Confirmation, quotas, session and owner locks unchanged. Reusing a key with different
preset/kind/name conflicts. Summaries add sandbox_kind/company_name. Restart accepts
only temporary sources and creates temporary targets. No production tenant selector.

Active practice companies owned by an active verified account are additionally
returned by App bootstrap/company management with purpose=playground and
sandbox_run_id. No purpose conversion is performed. The App's tenant URL parameter
is only a selection hint validated against bootstrap. Supported local business
operations use normal shared services; unknown/egress/sharing/lifecycle operations
remain denied. Temporary runs retain the narrower Playground route policy.
