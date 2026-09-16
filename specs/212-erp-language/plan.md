# Implementation Plan: ERP language

## Summary and Technical Context
Use the existing React/TypeScript localization catalogs. Review effective (last-write) values and callers, then edit existing translations in place. Use a separate `Delivery progress` heading in the document preview so a business label does not rename the shared model-oriented `Operational Reality` heading elsewhere. Python presentation only; no business calculations change.

## Constitution Check
PASS for all eight principles: evidence/source content untouched; shared operational authority retained; no schema changes; tenant/service boundaries unchanged; spec and existing regression evidence required; clearer explainability; no dependencies; source-stated values unchanged.

## Verification
Review all three languages and all callers of each shared key. Update the existing document-preview heading assertion before the heading change and observe the failure. Run targeted preview PostgreSQL tests, all frontend contract/terminology/formatting tests, four-language audit, production build, Ruff and spec policy. No new snapshot tests for a wording-only change. Review before/after copy manually; avoid claiming native-speaker sign-off. Backend full suite need not repeat for a literal heading change.

## Risks and Rollback
A shared key may have a different meaning in another screen: use a context-specific heading where required, retain generic fulfillment labels, and protect canonical model nouns. Revert catalog/presentation changes to roll back; no data migration.

## Design
Language decisions and reviewed coverage are in research.md. Data model: unchanged. UI contract: contracts/ui.md. Existing test infrastructure only. No critical findings or unresolved product questions.
