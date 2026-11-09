# Implementation Plan

## Technical Context
Python3.12/SQLAlchemy/Pydantic2/Ed25519. Current and old99 common Source/Action/outcome models only. No migration or background infrastructure. Four exact MCP contracts are in contracts/.

## Constitution Check
All PASS: original source immutable; mapping-only decision is separate from business Reality; no typed schema expansion; tenant-scoped shared services; human approval independently verified; no source-value recomputation; test-first and explicit limits. No exceptions.

## Layers
1. Pure strict proof/schema/canonical digest helpers; no provider SDK.
2. Shared services/shopify_buyer_mapping.py uses old99 common models and canonical store_source_record/outcome retention. Prepare retains dedicated proposed Action. Commit rechecks locked exact source/job/customer and trusted issuer proof; adds approval Source keyed by original source identity, updates only mapping Action and named review outcome, never source/job input or operational records.
3. Narrow tools adapter and MCP definitions: candidates read, prepare propose, commit confirm (privileged submission of proof only), status read. No generic executor registration for mapping Action type.
4. Current runtime default-deny host policy file. Version-pinned old99 overlay copies the same shared module and registers tools before normal API/MCP imports; no migrations/worker startup.

## Locking and Idempotency
Canonical tenant/delivery lock before source streams, original source/job, customer/roles, review Action and approval Source stream. Authenticated manual submitter token is validated/locked consistently with transport authority. Re-read policy and live clock after locks. Original SourceStream selection and source/job hash/version are CAS preconditions. Unique approval SourceStream for original source prevents a second mapping. Stable request nonce identifies Action; exact signed-proof retry returns original receipt.

## Verification
Candidates eligibility/privacy/isolation; frozen nonce replay; source/job/hash/version/role changes; correct/invalid/expired/wrong-key/subject/audience/purpose proof; duplicate JSON/header algorithm refusal; approval replay/concurrent/second mapping; no generic execute; immutable original source/job input and unchanged operational counts. Prove shared module against exact old image metadata without migrations. Current full checks and independent review remain required before completion.

## Rollback and Risks
Disable host policy/issuer or narrow token to stop new writes; retained sources/decisions remain. No schema removal. Mapping is not full intake or accepted business order. External proof attribution is not a local Reality human identity. Manual tokens grant submission only. No Shopify customer permission expansion. Existing customer identity/role/name digest changes require a new review; no silent alias/remap.
