# Read contracts

GET `/api/tenants/{tenant}/data-sources/systems`: q/page/size; items id,code,name,description,is_active,record_count and page. Count means retained source versions for that tenant/system code.

GET `/api/tenants/{tenant}/data-sources/records`: q/source_system/page/size; metadata id,source_system,source_type,external_id,version,received_at,supersedes_source_record_id,job_status and page. No payload/hash/job-input/error. Order received_at descending, opaque ID descending. Exact system and metadata search before count/page. Missing job null, not interpreted success.

Existing GET evidence-documents adds optional source_record_id, composed with other existing filters before paging. Foreign source filters reveal no documents. Clients remain backward compatible.

`/app/data-sources` URL fields: data_view systems/records/documents, source_system, source_record, evidence_type, entry; existing tenant/q/page. Default systems. Initial Inspector kind source_record or document from tab. Tab switches clear entry/q/page; selecting a source's evidence clears incompatible type/search. Company switching clears system/source/type/entry. Invalid tab falls back to systems. No POSTs.
