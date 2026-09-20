# Specification Quality Checklist: Evidenced inventory cost and contribution

**Purpose**: Review the concept before product/domain acceptance and technical planning.
**Created**: 2026-09-18
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] Specification describes business behavior; architectural proposals are separate in research.md.
- [x] Focused on user value and understandable cost/margin distinctions.
- [x] Mandatory specification sections completed in English.
- [x] Existing capability is distinguished from proposed scope and deferred industries.

## Requirement Completeness

- [x] No unresolved requirement placeholders; proposed defaults are explicit.
- [x] Requirements are testable and have scenario/fixture traceability.
- [x] Success criteria are measurable and independent of implementation technology.
- [x] Primary flows, edge cases, dependencies and non-goals are identified.
- [x] Missing costs, partial scope and historical changes cannot masquerade as complete values.
- [x] HGB carrying value is distinct from commercial contribution and historical cost.
- [x] Received amounts and explicit decisions remain distinct from derived observations.

## Feature Readiness

- [x] All functional/domain requirements map to planned proof in verification.md.
- [x] Arithmetic fixtures independently reviewed for conservation and margin definitions.
- [ ] Product/domain owner has accepted the proposed scope, DB profile and valuation approach.
- [ ] Technical plan has passed its Constitution Check and schema review.
- [ ] Tasks and cross-artifact analysis are complete.
- [ ] Implementation and executable verification are complete.

## Review Notes

This checklist records specification review only. Numeric fixtures are design evidence,
not passing runtime tests. The user's request authorized a concept; implementation is
outside this delivery. No claim is made that HGB policy suitability has been approved.
The first method is explicitly proposed FIFO/specific identification; other required
company methods must be separately supported, never silently replaced.

## Validation Performed

- `python3 scripts/check_spec_policy.py`: passed.
- `git diff --check`: passed for tracked changes; new Markdown files were separately
  reviewed through their content and local-link checks.
- Local document-link and requirement mapping check: passed, all 32 FR/DR identifiers
  are present in the traceability table.
- Independent Decimal checks of the main cost, FIFO and return examples: passed.
- `make spec-check`: could not start because the local Apple tooling requires Xcode
  license acceptance. Its exact underlying Python policy check passed when run directly.
- No application tests were run: this delivery changes specifications only.
- No `.specify/extensions.yml` exists; before/after specification hooks do not apply.


## Review Follow-up

- [x] FR-018 and fixture J define scale, response, refresh and reconstruction budgets;
  a pre-architecture experiment must establish feasibility before implementation planning.
- [x] FR-019 explicitly reuses owner-only approval and member reads, without inventing roles.
- [x] FR-020–FR-022 and fixture K cover tax, customs duty, cash discounts and precision.
- [x] FR-023 defines canonical bilingual product labels; surrounding repository prose is English.
- [x] FR-024 chooses existing reporting/builder integration; FR-025 reuses Exceptions/Rules.
- [x] FR-026 and fixture M require the canonical complete/incomplete demo and setup boundaries.
- [x] SC-002, SC-006 and SC-007 add usability, performance and observable coverage outcomes.
- [x] Research follows the repository filename convention; baseline catalog paths are explicit.
- [x] Verification includes tenant-isolation catalog classification/count gates.
- [x] Open Questions lists concrete owner decisions without claiming acceptance.
- [x] Feature branch starts at origin/main; unrelated Inbox commit is excluded.

## Second review round

- [x] FR-025 and fixture L use the existing catalog contract: one of the four existing
  severity values, catalog-style accountable areas, existing `record_type` subjects,
  contiguous class ranks and the pinned class count raised from 35 to 39. Verified
  against `services/exceptions.py`, the catalog and `tests/test_reference_integrity.py`.
- [x] FR-018 and fixture J now budget the Exceptions/attention queue and chat/MCP cost
  answers, the surfaces the new derivation actually loads, and report the queue delta.
- [x] FR-027 requires every new cost record reference on inspector, web, CLI and MCP with
  resource vocabulary and generated Tool Usage pages; fixture I proves it.
- [x] Fixture J reuses spec 033's harness and reduced-profile convention. Its earlier
  scale restriction is superseded by the explicitly accepted historical-volume profile below.
- [x] The delivery table maps every requirement and fixture to a slice, with a slice 0
  costing spike as the architecture gate.
- [x] User Story 5 (authorization) is P1 and separate from User Story 6 (scale and
  integration, P2); the traceability table follows the renumbering.
- [x] Existing Contracts names specs 033, 146, 178 and 228; the benchmark path is exact;
  FR-023 settles what happens in Dutch and Spanish.

Validation of this revision: spec policy, local links, requirement coverage, whitespace
and Decimal examples pass. Performance, permission enforcement, usability and demo runtime
proofs remain planned acceptance tests, not claims about the current application.


## Owner-approved four-point revision

The owner explicitly accepted all four proposed changes; other product scope choices
and implementation approval remain as recorded in spec.md.

- [x] US5.3 and FR-019 permit agent assistance with explicit owner confirmation and
  execution-time revalidation; fixture I tests both authorized and refused paths.
- [x] FR-005 specifies original-cost return layers at return time; fixture C2 tests
  FIFO ordering and the distinct specific-identification result.
- [x] FR-022 defines cumulative consumption rounding before filtering; fixture K2 tests
  exact conservation, filtered reporting, returns and late cost corrections.
- [x] Fixture J fixes test-day and historical orders, items, movements, components,
  attribution and matching cardinalities without claiming daily ingestion capacity.

Specification policy, links, requirement mapping and the new Decimal examples were
checked for this revision. Runtime/benchmark tests remain unexecuted: changes are
specification-only.


## Phase 0 planning progression

- [x] Owner continuation recorded with the accepted four decisions preserved.
- [x] plan.md defines the bounded qualification experiment and its Constitution Check.
- [x] data-model.md distinguishes disposable experiment inputs from unapproved product schema.
- [x] contracts/spike-contract.md and quickstart.md define response/measurement and validation targets.
- [x] Research identifies service-measure refusal, input limits and whole-projection replacement.
- [ ] Fixture J executed on the reference envelope and architecture qualified.
- [ ] Production Phase 1 schema/service design finalized after qualification.

The plan skill's Phase 1 production design is not marked complete: spec 242 requires
fixture J before architecture approval. Current artifacts fully describe Phase 0;
commands naming future costing tests/runner are explicitly marked as not implemented.
No application changes or active database operations were made during planning.
