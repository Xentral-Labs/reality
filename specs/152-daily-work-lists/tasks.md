# Tasks
- [x] T001 [FR-001–006] Add queue service and routing regression proofs before implementation; add browser proof during UI integration.
- [x] T002 [FR-004/006] Extend shared pending proposal read/count and API with tool filter and oldest-first order.
- [x] T003 [FR-001/002/005/006] Implement shared incremental list and side dialog plus open-only customer/supplier CommitmentsPage and navigation.
- [x] T004 [FR-001/003/004/005/006] Refactor exceptions and decisions into compact localized work lists with on-demand detail.
- [x] T005 [FR-001–006] Run backend/frontend/browser/spec verification, review, update durable docs and local stack.

- [x] T006 [FR-002] Replace the misleading circle with the existing package icon; verify frontend/build/spec and update local web.

- [x] Refine shared tab underline spacing and place daily-work totals beside the introduction title; verify frontend and browser fixtures.

Verification: frontend build and 61 contracts passed; spec policy passed. Daily-work browser fixtures passed all three queues across English/German, desktop/mobile and light/dark, including title counter ancestry, pagination, filters, drawers and no writes. Screenshots reviewed. Local web rebuilt on port 8080.

Tab regression: the higher-specificity selected-tab background shorthand reset the underline size to auto. Restore size, position and repeat at the same specificity; verify selected computed style and screenshots before deploying. Restores the specified thin underline without changing hit targets.

Tab regression verification passed: TypeScript/Vite build; 32 desktop/mobile routes and 3 translations with computed 2px background size and no-repeat; 8 populated Inspector layouts and visual review.
