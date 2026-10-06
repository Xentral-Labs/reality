# Essential intake completeness (spec 379)

An incoming source is evidence even when incomplete. Raw SourceRecord/SourceArtifact admission remains lossless; accepting business meaning is a separate step. Missing facts are never replaced by an apparent source statement.

## Shared rule matrix

| Value and path | New preparation/recording behavior | Allowed incomplete behavior |
|---|---|---|
| Currency on Shopify/file/synthetic orders and normalized invoice/payment sources | Require a nonblank source value; no implicit EUR | Direct human forms retain their visible currency default |
| Bank-file payment direction and booking instant | Require incoming/outgoing and effective_at; missing values refuse before posting | Raw remains available; received_at is never a booking substitute |
| Manual document unit price | Omission/blank remains unknown; explicit 0 stays 0 | Explicit-null direct manual validation remains unchanged; source-carried null stays unknown |
| Order document date | File profile preserves document_date; otherwise the stated ordered_at instant becomes the company-local day | Neither stated: retain unknown and expose review issue; never use today's date |
| Order time and delivery deadline | Preserve as stated and report absence in review | An order can legitimately have no agreed delivery date |
| Order total and line amount | Preserve exact source values and report absence | Unknown is not zero; do not multiply quantity by unit price to fill it |
| Known-item physical sales unit | Omitted unit uses the recorded item stock unit under the profile contract; explicit unsupported different unit refuses a promise | Unknown item lines remain evidence without a physical promise; existing purchase conversion remains separate |
| Automatic live simulator order | Author an explicit EUR 10 unit quotation, one order instant and its company-local document day | Manual composer amount without an explicit unit quotation remains unknown; no reverse price calculation |

Exported manual-order/document/free-supplier-invoice tool schemas accept omitted/blank unit prices and reject direct null; manual orders can omit the unit to inherit the recorded item stock unit. Agent schemas and shared recording services use the same absence meaning.

Order completeness observations use the shared domain policy and appear in retained intake reviews and manual-order previews. They are not persisted operational status. The existing unknown-item/missing-price exception and explicit billing amount paths remain in force. Missing essentials use stable field-specific localized refusals and existing preparation failure outcomes.

One coherent file order cannot state contradictory document_date or ordered_at header values across its rows. Compare parsed days/UTC instants, so equivalent timezone representations do not create a false conflict. Original row payloads remain unchanged. Dates with an explicit source document day keep that day even if the order instant belongs to another day. Company timezone state remains part of the exact review.

No schema, new queue, new confirmation cycle or agent authority is introduced. Existing approved reviews keep their original digest and exact accepted intent. Historical SourceRecords, orders and prices are never backfilled or rewritten by rollout. Existing undated simulator orders require separate reviewed remediation if the owner requests it.

## Verification

`tests/test_intake_completeness.py` covers essential omission/null/blank, zero versus unknown, original raw/no effects, explicit incoming/outgoing money, source/file/manual order observations, local-day/register date, conflicting headers and sales stock units. `tests/scenarios/test_live_company.py` covers automatic source/evidence/date/register/replay. Existing intake, financial, tenant, purchase, billing and source tests remain required, followed by complete PR CI. Measured results are retained in [spec 379 verification](../../specs/379-intake-completeness/verification.md).
