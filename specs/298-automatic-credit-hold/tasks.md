# Tasks: Automatic Credit Hold

**Input**: Design documents from `/specs/298-automatic-credit-hold/`

**Tests**: Tests precede each phase. Every "nothing held" or "not reported" assertion has a positive control; every refusal asserts its code. `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the owner's four decisions in `specs/298-automatic-credit-hold/spec.md`
- [x] T002 Record today's behaviour, the exposure, the check, the release and the finding in `research.md`, `data-model.md` and `contracts/credit-hold.md`
- [x] T003 Complete the Constitution Check and design in `plan.md`

## Phase 2: Exposure (FR-001, DR-002)

- [x] T004 [FR-001] Failing tests in `core/tests/test_credit_exposure.py`:
  - open invoices, open uninvoiced order lines (partly invoiced, cancelled, revised, unpriced) and available credits (credit note, unallocated payment) sum as specified;
  - overdue invoices are named apart from those not yet due;
  - payables of the same party are named, not subtracted;
  - another currency is named as not counted;
  - tenant scope;
  - an invoiced order counts once.
- [x] T005 [FR-001] `credit_exposure` in `core/src/reality/services/credit_exposure.py`.

## Phase 3: Hold at entry (FR-002, FR-003)

- [x] T006 [FR-002] [FR-003] Failing tests in `core/tests/test_credit_hold.py`:
  - an order over the limit is held with `credit_check` on each promise, with the note and a `commitment.held` event carrying the facts;
  - an order under the limit is not held (control);
  - no limit, no hold;
  - another currency, no hold;
  - a replayed intake holds once;
  - the same through `order_create`, the Shopify interpretation and the file import;
  - a credit hold is added beside an address hold;
  - an assigned line of a credit-held order is held;
  - a held promise cannot be reserved or shipped.
- [x] T007 [FR-002] `hold_if_over_credit_limit` and its calls in `create_manual_order`, the Shopify interpretation, the file `sales_order` import and `assign_line_item`.

## Phase 4: Release (FR-004)

- [x] T008 [FR-004] Failing tests in `core/tests/test_credit_hold.py`:
  - an owner releases with a reason and the event names it and the decision names the person;
  - the order then reserves and ships;
  - a blank reason is refused (`credit_hold_release_reason_missing`);
  - a member who is not an owner is refused (`company_owner_access_required`);
  - no credit hold is refused (`credit_hold_not_found`);
  - the generic release leaves credit holds and refuses with `credit_hold_owner_release_required` when only they are active;
  - a cancellation still releases every hold.
- [x] T009 [FR-004] The reviewed tool `credit_hold_release` in `core/src/reality/services/hold_actions.py`, `tools/application.py` and `services/credit_exposure.py`; `release_commitment_hold` reason codes; refusal codes with de/nl/es translations.

## Phase 5: Finding (FR-005)

- [x] T010 [FR-005] Failing tests: the finding reports the exposure the hold used for the same instant (SC-003) and names the overdue invoices; update the tests that pinned open-invoices-only on purpose.
- [x] T011 [FR-005] `_credit_limit_exceeded_exceptions` on `credit_exposure`, and the catalog description.

## Phase 6: Adapters and Web (FR-006)

- [x] T012 [FR-006] Failing adapter tests in `core/tests/test_credit_hold_adapters.py`:
  - MCP `credit_hold_release_propose` (strict schema, propose then confirm) and `credit_exposure`;
  - Web: delivery-action pass-through, the exposure endpoint, a foreign company refused;
  - CLI: propose, confirm and exposure.
- [x] T013 [FR-006] MCP, Web API and CLI wiring. Catalog gates:
  - command catalog, coverage and guidance;
  - action discovery and the web fixture;
  - resource labels (German);
  - tenant isolation catalog and counts;
  - MCP topic;
  - refusal ratchet.
- [x] T014 [FR-006] Web:
  - owner-only "Release credit hold" with a required reason on a held order;
  - hold note shown;
  - party exposure section;
  - de/nl/es translations;
  - `npm run test:i18n`, i18n audit, prettier and build.

## Phase 7: Stories and Guide (FR-007)

- [ ] T015 [US1] [US2] Business stories C07, C08 and R08 in `core/tests/scenarios/test_catalog_finance.py`.
- [ ] T016 [FR-007] Promote C07, C08 and R08 with story-first evidence and English and German keywords; check neighbouring questions. Update coverage, the roadmap and the coverage matrix, then run `make docs-generate`.

## Phase 8: Verification

- [ ] T017 Full backend suite from a clean worktree and the web checks
- [ ] T018 Manual check per `quickstart.md` on an isolated stack
- [ ] T019 Review of the diff; fix findings
