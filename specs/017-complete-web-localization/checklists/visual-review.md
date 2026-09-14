# Visual Review Checklist: Complete Web Localization

**Purpose**: Verify representative selected-language states at desktop and mobile sizes
**Created**: 2026-08-31
**Status**: PASS — owner-reviewed desktop/mobile representative states

## Public and Authentication

- [x] English landing and authentication states pass at desktop and mobile widths
- [x] German landing and authentication states pass at desktop and mobile widths
- [x] Dutch landing and authentication states pass at desktop and mobile widths
- [x] Spanish landing and authentication states pass at desktop and mobile widths

## Product States

- [x] English operational and configuration states pass at desktop and mobile widths
- [x] German operational and configuration states pass at desktop and mobile widths
- [x] Dutch operational and configuration states pass at desktop and mobile widths
- [x] Spanish operational and configuration states pass at desktop and mobile widths

## Cross-Language States

- [x] Loading, empty, error, and confirmation states contain no avoidable English fallback
- [x] Critical actions, navigation, and labels are not clipped or made unusable by text length
- [x] Accessibility labels use the selected language or an approved invariant
- [x] Source, Evidence, document, ID, user-entered, and diagnostic content remains unchanged

## Evidence

- Automated audit: PASS — 775/775 discovered strings covered for `en`, `de`, `nl`, and `es`
- Focused localization tests: PASS — 8/8
- Frontend production build: PASS
- Browser review attempt: no controllable browser was available to the agent.
- Owner-supplied evidence: Spanish public landing state reviewed at desktop width.
- Defect found: the four-option segmented language control was atypical for a modern
  landing page.
- Corrected paths: `frontend/src/LandingPage.tsx`, `frontend/src/landing.css`.
- Corrected behavior: globe plus active language code opens a compact language popover;
  the active language is visibly checked and the native language names are preserved.
- Owner decision: corrected landing result accepted and continued evidence work
  approved on 2026-08-31; final baseline closure remains pending.
- Follow-up defect found during evidence review: public authentication rendered outside
  the localization boundary and dropped the selected landing language.
- Follow-up correction: `frontend/src/Auth.tsx`, `frontend/src/LandingPage.tsx`, and
  `frontend/src/localization-core.ts` now preserve a supported public language from the
  URL/stored choice and localize authentication through the shared provider. The new
  regression in `frontend/scripts/localization-contract.test.mjs` passes.
- Owner follow-up review: authentication language continuity and mobile presentation
  accepted on 2026-08-31.
- Owner final review: representative authenticated operational and configuration states
  in all advertised languages accepted on 2026-08-31.
