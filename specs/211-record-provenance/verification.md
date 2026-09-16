# Verification

## Pre-implementation review
Scope approved in conversation on 2026-09-16, including the explicit decision to place the external base address on `SourceSystem`. Fourteen requirements map to acceptance scenarios, tests and implementation tasks with no unmapped task. The Constitution Check passes all eight principles pre-design. The one schema decision requiring product-scope approval (FR-007, `connector_code`) was approved on 2026-09-16 after the existing association defect was demonstrated: with the present catalog, an instance installed from `shopify_payments` satisfies the description-prefix test for both `shopify_payments` and `shopify`, so `connector_shells` already lists it under two connectors. The requirements checklist is complete at 8/8.

No implementation has started. Post-design Constitution Check, failing-test evidence and gate results are recorded here as the phases complete.
