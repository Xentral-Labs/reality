# Tasks: Explain MCP Use

**Input**: Design documents from `/specs/101-explain-mcp-use/`

## Phase 1: Contract Proof

- [x] T001 [P] [US1] Add failing landing MCP value, safety, authentication, and guide-link assertions in `provider-site/scripts/site-contract.test.mjs`
- [x] T002 [P] [US2] Add failing bilingual guide, navigation, setup-step, and limitation assertions in `apps/docs/scripts/docs-contract.test.mjs`

## Phase 2: User Story 1 — Understand MCP Value

- [x] T003 [US1] Add concrete MCP jobs, governance copy, implemented authentication wording, and guide CTA in `provider-site/src/LandingPage.tsx`
- [x] T004 [US1] Add responsive styles using existing landing tokens in `provider-site/src/landing.css`
- [x] T005 [US1] Add complete German, Dutch, and Spanish public-site translations in `provider-site/src/localization.tsx`

## Phase 3: User Story 2 — Connect an MCP Client

- [x] T006 [P] [US2] Write the canonical setup guide in `apps/docs/content/api-tools/connect-mcp.md`
- [x] T007 [P] [US2] Write the matching German setup guide in `apps/docs/content/de/api-tools/connect-mcp.md`
- [x] T008 [US2] Add both guide routes to `apps/docs/.vitepress/config.mts` and link the API & Tools overview in `apps/docs/content/api-tools/index.md` and `apps/docs/content/de/api-tools/index.md`

## Phase 4: Verification

- [x] T009 Run Site contract, localization, formatting, and build checks from `provider-site/package.json`
- [x] T010 Run Docs contract, formatting, and build checks from `apps/docs/package.json`
- [x] T011 Run `make spec-check`, review claims against the MCP implementation, and mark completed tasks in `specs/101-explain-mcp-use/tasks.md`

## Phase 5: Compact Landing Bridge

- [x] T012 [US1] Update the landing content contract to require one compact MCP bridge and reject the capability grid in `provider-site/scripts/site-contract.test.mjs`
- [x] T013 [US1] Replace the five-card MCP panel with a compact connection bridge in `provider-site/src/LandingPage.tsx`
- [x] T014 [US1] Give the bridge explicit readable colors and responsive layout in `provider-site/src/landing.css`
- [x] T015 [US1] Replace panel copy with complete German, Dutch, and Spanish bridge translations in `provider-site/src/localization.tsx`
- [x] T016 Run Site tests, formatting, build, and `make spec-check`, then review the rendered hierarchy

## Dependencies

- T001 and T002 are independent failing proofs and precede implementation.
- T003 → T004 → T005 complete US1.
- T006 and T007 may run in parallel; T008 follows them.
- T009–T011 follow both stories.
- T012 precedes T013–T015; T016 verifies the compact-bridge amendment.

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| FR-001–FR-004, FR-007, FR-009 | T001, T003–T005, T009 |
| FR-005–FR-009 | T002, T006–T010 |
| FR-001–FR-004, FR-007, FR-009 compact-bridge amendment | T012–T016 |

## Implementation Strategy

The landing capability panel is the MVP. The guide completes the customer journey without changing protocol behavior.
