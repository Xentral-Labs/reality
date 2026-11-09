# Common wire response contract

All wire fields are snake_case. Source hashes and customer digests are returned
by Reality; the caller must not replace them with a different JSON hash algorithm.

source_binding = {source_record_id,import_job_id,source_hash,source_version:positive_integer,external_id,order_id,order_label,shop,query_digest}.
customer = {party_id,label,digest}.

Candidates: {purpose:"shopify_source_buyer_mapping_only/1",source_binding,
observed_at,items:[customer],has_more:boolean,coverage:"bounded_matching_existing_customers",existing_mapping:null|verified_mapping}.
No cursor in the first bounded slice; refine query when has_more. No email/address.

Prepare/status proposed: {purpose,review_id,review_digest,expires_at,
state:"proposed"|"expired",source_binding,customer,
business_effects_accepted:false,original_source_unchanged:true,
import_job_input_unchanged:true,sales_order_created:false}.

Commit/status recorded: same frozen fields with state:"mapping_recorded",
approval_source_record_id,approval_source_hash,recorded_at,approval:{kind:"issuer_signed_main_human_review",
issuer,subject,jti,proof_digest},business_effects_accepted:false,original_source_unchanged:true,
import_job_input_unchanged:true,sales_order_created:false,
remaining_review:"full_intake_review_not_prepared",current_basis:{source_current,customer_current}.
proof_digest is SHA256 of the original compact JWS ASCII bytes. jti is the exact
Main human approval UUID. Status preserves both; reconciliation must match its
retained human proof, not merely issuer and person.

verified_mapping = {mapping_state:"applied_to_source",customer,approval_source_record_id,
review_id,review_digest,current_basis,remaining_review:"full_intake_review_not_prepared"}.

An exact repeat of an already recorded review/proof returns the original receipt.
A different proof or changed customer/source basis is not a fresh approval. A
second mapping for this original source is refused in this first slice; remapping
requires its own future reviewed contract. No proposal is silently refreshed.

The original source job remains review_required. Its next immutable needs_review
outcome has reason buyer_mapping_recorded_intake_pending, explicitly separating
recorded buyer choice from a full interpreted/accepted order. No job.input update.
