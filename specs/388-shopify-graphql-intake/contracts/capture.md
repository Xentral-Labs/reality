# Capture contract

MCP shopify_order_graphql_capture, access propose, tenant from authenticated principal only. Strict outer input: order (unmodified original data.order object), optional company_party_id/customer_party_id/location_id, optional acquisition {shop,api_version,query_digest,observed_at,coverage:complete-selected-order}. Derive source identity/timestamp from order.id/updatedAt; hardcode source system/type. Return source_record_id/import_job_id/status/business_effects_accepted:false. No apply/accept/grant or general source_type parameter.
